from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from agents.phase3_orchestrator import diagnose_snapshot
from collectors.k8s_events_collector import K8sEventsCollector
from collectors.loki_collector import LokiCollector
from collectors.prometheus_collector import PrometheusCollector
from collectors.tempo_collector import TempoCollector
from config import settings
from db import get_db
from incident.incident_assembler import IncidentAssembler
from incident.store import INCIDENTS


MONITORED_SCENARIO_IDS = {
    "oom-kill-001",
    "cpu-spike-001",
    "crash-loop-001",
    "db-latency-001",
}


class LiveMonitorAgent:
    """Background monitor loop that detects anomalies and opens incidents."""

    def __init__(self, poll_interval_seconds: int | None = None) -> None:
        self.poll_interval_seconds = poll_interval_seconds or settings.monitor_poll_interval_seconds
        self.prometheus = PrometheusCollector()
        self.loki = LokiCollector()
        self.tempo = TempoCollector()
        self.k8s_events = K8sEventsCollector()
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop(), name="live-monitor-agent")

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def run_cycle_once(self) -> None:
        scenarios = self._load_scenarios()
        for scenario in scenarios:
            try:
                await self._evaluate_scenario(scenario)
            except Exception as exc:
                print(f"WARN: monitor cycle failed for {scenario.get('scenario_id')}: {exc}")

    async def _run_loop(self) -> None:
        while True:
            try:
                await self.run_cycle_once()
            except Exception as exc:
                print(f"WARN: monitor loop cycle failed: {exc}")
            await asyncio.sleep(max(1, self.poll_interval_seconds))

    def _load_scenarios(self) -> list[dict[str, Any]]:
        db = get_db()
        try:
            rows = db.execute("SELECT scenario_json FROM scenarios").fetchall()
        finally:
            db.close()

        scenarios: list[dict[str, Any]] = []
        for row in rows:
            try:
                scenario = json.loads(row["scenario_json"])
            except Exception:
                continue
            if scenario.get("scenario_id") in MONITORED_SCENARIO_IDS:
                scenarios.append(scenario)
        return scenarios

    async def _evaluate_scenario(self, scenario: dict[str, Any]) -> None:
        scenario_id = str(scenario.get("scenario_id", ""))
        namespace = str(scenario.get("namespace", "default"))
        deployment = str(scenario.get("deployment", "unknown"))
        service = str(scenario.get("service", deployment))
        pod = await self._resolve_pod_name(namespace, deployment)

        metrics = await self.prometheus.get_incident_metrics(namespace=namespace, pod=pod)
        baseline = await self.prometheus.get_baseline_samples(namespace=namespace, pod=pod, samples=10)
        logs = await self.loki.get_log_lines(namespace=namespace, service=service)
        events = self.k8s_events.get_deployment_events(namespace=namespace, deployment=deployment, window_minutes=5)

        baseline_last = baseline[-1] if baseline else {}
        if not self._is_anomaly_for_scenario(
            scenario_id=scenario_id,
            metrics=metrics,
            baseline=baseline_last,
            logs=logs,
            events=events,
        ):
            return

        traces = await self._collect_traces_if_needed(service, metrics, baseline_last, logs)
        started_at = datetime.now(timezone.utc).isoformat()

        incident = IncidentAssembler.assemble(
            injection_event={
                "scenario_id": scenario_id,
                "service": service,
                "namespace": namespace,
                "pod": pod,
                "deployment": deployment,
                "started_at": started_at,
            },
            collected_signals={
                "metrics": metrics,
                "logs": logs,
                "traces": traces,
                "events": events,
            },
            context={
                "baseline_values": baseline_last,
                "dependency_graph_summary": f"{service} -> dependencies",
            },
        )

        snapshot = incident["snapshot"]
        failure_class = str(snapshot.get("failure_class", "unknown"))
        if self._is_duplicate_incident(namespace=namespace, service=service, failure_class=failure_class):
            return

        diagnosis = diagnose_snapshot(self._to_diagnosis_snapshot(incident))
        self._create_incident_record(incident=incident, diagnosis=diagnosis)

    async def _resolve_pod_name(self, namespace: str, deployment: str) -> str:
        if self.k8s_events.v1 is None:
            return f"{deployment}-unknown"

        try:
            pods = self.k8s_events.v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={deployment}",
            )
            if pods.items:
                return str(pods.items[0].metadata.name)
        except Exception:
            pass
        return f"{deployment}-unknown"

    @staticmethod
    def _is_anomaly_for_scenario(
        *,
        scenario_id: str,
        metrics: dict[str, Any],
        baseline: dict[str, Any],
        logs: list[str],
        events: list[dict[str, Any]],
    ) -> bool:
        memory = float(metrics.get("memory_usage_percent", 0.0))
        cpu = float(metrics.get("cpu_usage_percent", 0.0))
        restarts = float(metrics.get("restart_count", 0.0))
        latency = float(metrics.get("latency_p95_seconds", 0.0))
        baseline_latency = max(float(baseline.get("latency_p95_seconds", 0.001)), 0.001)
        latency_delta = latency / baseline_latency

        event_reasons = {str(event.get("reason", "")) for event in events}
        logs_blob = " ".join(logs).lower()

        if scenario_id == "oom-kill-001":
            return memory >= 85 or "OOMKilled" in event_reasons or "Evicted" in event_reasons

        if scenario_id == "cpu-spike-001":
            return cpu >= 80 or (latency_delta >= 2.0 and "timeout" in logs_blob)

        if scenario_id == "crash-loop-001":
            return (
                "CrashLoopBackOff" in event_reasons
                or "BackOff" in event_reasons
                or "ImagePullBackOff" in event_reasons
                or "ErrImagePull" in event_reasons
                or restarts >= 3
            )

        if scenario_id == "db-latency-001":
            return (
                latency_delta >= 2.0
                or "Unhealthy" in event_reasons
                or "timeout" in logs_blob
                or "connection" in logs_blob
            )

        return False

    async def _collect_traces_if_needed(
        self,
        service: str,
        metrics: dict[str, Any],
        baseline: dict[str, Any],
        logs: list[str],
    ) -> list[dict[str, Any]]:
        baseline_latency = max(float(baseline.get("latency_p95_seconds", 0.001)), 0.001)
        latency_delta = float(metrics.get("latency_p95_seconds", 0.0)) / baseline_latency
        timeout_count = sum(1 for line in logs if "timeout" in str(line).lower())

        if not self.tempo.should_query(
            latency_delta_x=latency_delta,
            timeout_log_count=timeout_count,
            cross_service_suspected=False,
            rule_confidence=0.0,
            failure_class="unknown",
        ):
            return []

        end = datetime.now(timezone.utc)
        start = end - timedelta(minutes=5)
        try:
            traces = await self.tempo.search_traces(service, start, end)
            if not traces:
                return []
            trace_id = traces[0].get("traceID")
            if not trace_id:
                return []
            trace = await self.tempo.get_trace(trace_id)
            return [trace] if trace else []
        except Exception:
            return []

    def _is_duplicate_incident(self, *, namespace: str, service: str, failure_class: str) -> bool:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        for incident in INCIDENTS:
            if incident.get("service") != service:
                continue

            scope = incident.get("scope") or incident.get("snapshot", {}).get("scope") or {}
            if scope.get("namespace") != namespace:
                continue

            if incident.get("failure_class") != failure_class:
                continue

            if incident.get("status") in {"resolved", "failed"}:
                continue

            created_at = str(incident.get("created_at", ""))
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                continue
            if created >= cutoff:
                return True
        return False

    @staticmethod
    def _to_diagnosis_snapshot(incident: dict[str, Any]) -> dict[str, Any]:
        snapshot = incident.get("snapshot", {})
        metrics = snapshot.get("metrics", {})
        return {
            "metrics": {
                "memory_pct": float(str(metrics.get("memory", "0")).rstrip("%") or 0),
                "cpu_pct": float(str(metrics.get("cpu", "0")).rstrip("%") or 0),
                "restart_count": float(metrics.get("restarts", 0)),
                "latency_delta": float(str(metrics.get("latency_delta", "1")).rstrip("x") or 1),
            },
            "events": snapshot.get("events", []),
            "logs_summary": snapshot.get("logs_summary", []),
            "trace": snapshot.get("trace_summary") or {},
        }

    def _create_incident_record(self, *, incident: dict[str, Any], diagnosis: dict[str, Any]) -> None:
        snapshot = incident["snapshot"]
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "incident_id": incident["incident_id"],
            "service": incident.get("service", "unknown"),
            "status": "open",
            "failure_class": snapshot.get("failure_class", "unknown"),
            "severity": incident.get("severity", "medium"),
            "monitor_confidence": float(snapshot.get("monitor_confidence", 0.0)),
            "created_at": incident.get("started_at", now),
            "updated_at": now,
            "scope": snapshot.get("scope", {}),
            "namespace": incident.get("namespace", "default"),
            "pod": snapshot.get("pod", "unknown"),
            "scenario_id": incident.get("scenario_id"),
            "snapshot": snapshot,
            "diagnosis": diagnosis,
            "plan": None,
            "execution": None,
            "verification": None,
            "token_summary": None,
            "resolved_at": None,
            "dependency_graph_summary": snapshot.get("dependency_graph_summary", ""),
            "summary": snapshot.get("alert", "monitor detected anomaly"),
        }

        INCIDENTS.insert(0, record)

        db = get_db()
        try:
            db.execute(
                """INSERT OR REPLACE INTO incidents (incident_id, service, status, failure_class, summary, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    record["incident_id"],
                    record["service"],
                    record["status"],
                    record["failure_class"],
                    record["summary"],
                    record["created_at"],
                ),
            )
            db.commit()
        finally:
            db.close()


LIVE_MONITOR_AGENT = LiveMonitorAgent()

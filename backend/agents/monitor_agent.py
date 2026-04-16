from collectors.k8s_events_collector import K8sEventsCollector
from collectors.loki_collector import LokiCollector
from collectors.prometheus_collector import PrometheusCollector
from collectors.tempo_collector import TempoCollector


class MonitorAgent:
    def __init__(self) -> None:
        self.prom = PrometheusCollector()
        self.loki = LokiCollector()
        self.tempo = TempoCollector()
        self.events = K8sEventsCollector()

    def collect_snapshot(self) -> dict:
        return {
            "memory_pct": self.prom.query_instant("memory_usage_percent").get("value", 0.0),
            "event_reason": self.events.list_recent_events().get("events", []),
            "log_signatures": self.loki.query_logs("{app=\"payment-api\"} |= \"error\"").get("signatures", []),
            "trace": self.tempo.get_trace_summary("trace-stub"),
        }

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from agents.phase3_orchestrator import collect_monitor_snapshot, diagnose_snapshot
from planner.plan_simulator import simulate_action
from planner.planner_agent import PlannerAgent

router = APIRouter(prefix="/incidents", tags=["incidents"])
planner_agent = PlannerAgent()

INCIDENTS: list[dict] = [
    {
        "incident_id": "inc-001",
        "service": "payment-api",
        "status": "open",
        "failure_class": "resource",
        "scope": {"namespace": "default", "deployment": "payment-api"},
        "dependency_graph_summary": "frontend -> payment-api -> db",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]


def _find_incident(incident_id: str) -> dict[str, Any]:
    for incident in INCIDENTS:
        if incident["incident_id"] == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")


@router.get("")
def list_incidents() -> list[dict]:
    return INCIDENTS


@router.get("/{incident_id}")
def get_incident(incident_id: str) -> dict:
    return _find_incident(incident_id)


@router.post("/{incident_id}/plan")
def plan_incident(incident_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    incident = _find_incident(incident_id)
    body = payload or {}

    context = dict(incident.get("scope", {}))
    context.update(body.get("context", {}))
    context["dependency_graph_summary"] = body.get(
        "dependency_graph_summary",
        incident.get("dependency_graph_summary", ""),
    )
    context["has_rollback_revision"] = body.get("has_rollback_revision", True)

    snapshot = body.get("snapshot") or collect_monitor_snapshot()
    diagnosis = body.get("diagnosis") or diagnose_snapshot(snapshot)

    plan_output = planner_agent.run(
        diagnosis=diagnosis,
        snapshot={
            "dependency_graph_summary": context["dependency_graph_summary"],
            "has_rollback_revision": context["has_rollback_revision"],
        },
        context=context,
    )

    actions = [action.model_dump() for action in plan_output.actions]
    incident["diagnosis"] = diagnosis
    incident["plan_json"] = {"actions": actions}
    incident["planned_at"] = datetime.now(timezone.utc).isoformat()

    if any(action["approval_required"] for action in actions):
        incident["status"] = "pending_approval"
    else:
        incident["status"] = "planned"

    return {
        "incident_id": incident_id,
        "status": incident["status"],
        "plan": incident["plan_json"],
    }


@router.post("/{incident_id}/simulate")
def simulate_incident_action(incident_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    incident = _find_incident(incident_id)
    if "plan_json" not in incident or not incident["plan_json"].get("actions"):
        raise HTTPException(status_code=400, detail="No plan available. Run /plan first.")

    body = payload or {}
    action_index = int(body.get("action_index", 0))
    actions = incident["plan_json"]["actions"]

    if action_index < 0 or action_index >= len(actions):
        raise HTTPException(status_code=400, detail="Invalid action_index")

    action = actions[action_index]
    simulated = simulate_action(
        {
            "command": action["action"],
            "risk": action["risk_level"],
            "approval_required": action["approval_required"],
        },
        {
            "dependency_graph_summary": incident.get("dependency_graph_summary", ""),
            "has_rollback_revision": bool(body.get("has_rollback_revision", True)),
        },
    )
    action["simulation_result"] = simulated.model_dump()

    return {
        "incident_id": incident_id,
        "action_index": action_index,
        "simulation_result": action["simulation_result"],
    }


@router.post("/{incident_id}/approve")
def approve_incident_action(incident_id: str) -> dict:
    incident = _find_incident(incident_id)

    if incident.get("status") == "failed":
        raise HTTPException(status_code=400, detail="Incident already closed as failed")

    incident["status"] = "approved"
    return {
        "incident_id": incident_id,
        "status": incident["status"],
        "message": "Approval accepted. Executor integration is next.",
    }

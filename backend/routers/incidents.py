from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/incidents", tags=["incidents"])

INCIDENTS: list[dict] = [
    {
        "incident_id": "inc-001",
        "service": "payment-api",
        "status": "open",
        "failure_class": "resource",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
]


@router.get("")
def list_incidents() -> list[dict]:
    return INCIDENTS


@router.get("/{incident_id}")
def get_incident(incident_id: str) -> dict:
    for incident in INCIDENTS:
        if incident["incident_id"] == incident_id:
            return incident
    raise HTTPException(status_code=404, detail="Incident not found")


@router.post("/{incident_id}/approve")
def approve_incident_action(incident_id: str) -> dict:
    return {
        "incident_id": incident_id,
        "status": "approved",
        "message": "Approval stub accepted. Wire executor next.",
    }

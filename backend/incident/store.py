from __future__ import annotations

from datetime import datetime, timezone


# Shared in-memory incident store for demo API and monitor loop.
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

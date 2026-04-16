from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from collectors.k8s_events_collector import K8sEventsCollector
from collectors.loki_collector import LokiCollector
from collectors.prometheus_collector import PrometheusCollector
from collectors.tempo_collector import TempoCollector
from db import get_db
from fault_injection.fault_injector import FaultInjector
from models.schemas import FaultInjectionRequest, FaultInjectionResponse

router = APIRouter(tags=["fault-injection"])


@router.post("/inject-fault")
async def inject_fault(body: FaultInjectionRequest) -> FaultInjectionResponse:
    db = get_db()
    try:
        row = db.execute(
            "SELECT scenario_json FROM scenarios WHERE scenario_id = ?",
            (body.scenario_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"error": "scenario_not_found"})

        scenario = json.loads(row["scenario_json"])
    finally:
        db.close()

    injector = FaultInjector([scenario])
    injector.apply_fault(body.scenario_id)
    snapshot_id = f"obs-{uuid4().hex[:8]}"

    snapshot = await injector.collect_snapshot(
        scenario_id=body.scenario_id,
        snapshot_id=snapshot_id,
        prometheus=PrometheusCollector(),
        loki=LokiCollector(),
        k8s_events=K8sEventsCollector(),
        tempo=TempoCollector(),
    )

    return FaultInjectionResponse(
        scenario_id=body.scenario_id,
        snapshot=snapshot,
        message="Snapshot collected from metrics, logs, events, and traces",
    )

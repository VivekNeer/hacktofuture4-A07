from fastapi import APIRouter

router = APIRouter(tags=["agents"])


@router.post("/diagnose")
def diagnose() -> dict:
    return {"status": "stub", "agent": "diagnose"}


@router.post("/plan")
def plan() -> dict:
    return {"status": "stub", "agent": "planner"}


@router.post("/execute")
def execute() -> dict:
    return {"status": "stub", "agent": "executor"}


@router.post("/verify")
def verify() -> dict:
    return {"status": "stub", "agent": "verifier"}

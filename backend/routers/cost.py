from fastapi import APIRouter

router = APIRouter(tags=["cost"])


@router.get("/cost-report")
def cost_report() -> dict:
    return {"total_estimated_cost_usd": 0.0, "calls": 0}

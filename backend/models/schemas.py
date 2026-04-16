from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import IncidentStatus, RiskLevel


class IncidentListItem(BaseModel):
    incident_id: str
    service: str
    status: IncidentStatus
    failure_class: str | None = None
    created_at: datetime


class DiagnosisPayload(BaseModel):
    root_cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class PlannerAction(BaseModel):
    action_id: str
    command: str
    risk: RiskLevel
    approval_required: bool = True

from __future__ import annotations

from typing import Any

from models.enums import DependencyImpact
from models.schemas import SimulationResult


def compute_blast_radius(action: dict[str, Any], dependency_summary: str) -> float:
    command = str(action.get("command", "")).lower()
    score = 0.0

    if "rollout restart" in command:
        score += 0.3
    if "rollout undo" in command:
        score += 0.5
    if "set image" in command or "set resources" in command:
        score += 0.2
    if "scale" in command:
        score += 0.1

    if "high error rate" in dependency_summary.lower():
        score += 0.15

    return min(round(score, 2), 1.0)


def check_rollback_ready(action: dict[str, Any], snapshot: dict[str, Any]) -> bool:
    command = str(action.get("command", "")).lower()
    if "rollout undo" not in command:
        return True

    # For demo/runtime predictability, use snapshot hint instead of shelling out.
    return bool(snapshot.get("has_rollback_revision", True))


def assess_dependency_impact(action: dict[str, Any], dependency_summary: str) -> DependencyImpact:
    command = str(action.get("command", "")).lower()
    if ("rollout undo" in command or "set image" in command) and "high error rate" in dependency_summary.lower():
        return DependencyImpact.BROAD
    if "rollout restart" in command:
        return DependencyImpact.LIMITED
    if "scale" in command or "set resources" in command:
        return DependencyImpact.NONE
    return DependencyImpact.LIMITED


def simulate_action(action: dict[str, Any], snapshot: dict[str, Any]) -> SimulationResult:
    dependency_summary = str(snapshot.get("dependency_graph_summary", ""))
    blast_radius = compute_blast_radius(action, dependency_summary)
    rollback_ready = check_rollback_ready(action, snapshot)
    dependency_impact = assess_dependency_impact(action, dependency_summary)

    violations: list[str] = []
    risk_level = str(action.get("risk", "medium")).lower()

    if not rollback_ready and risk_level == "high":
        violations.append("no_rollback_available_for_high_risk_action")

    if dependency_impact == DependencyImpact.BROAD and not bool(action.get("approval_required", False)):
        violations.append("broad_dependency_impact_requires_approval")

    return SimulationResult(
        blast_radius_score=blast_radius,
        rollback_ready=rollback_ready,
        dependency_impact=dependency_impact,
        policy_violations=violations,
    )

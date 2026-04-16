from typing import Any


POLICIES = {
    "FP-001": [
        {
            "action_id": "act-restart",
            "command": "kubectl rollout restart deploy/payment-api",
            "risk": "medium",
            "approval_required": True,
        }
    ]
}


def rank_actions(fingerprint_id: str, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    _ = context or {}
    return POLICIES.get(
        fingerprint_id,
        [
            {
                "action_id": "act-investigate",
                "command": "kubectl describe pod <pod-name>",
                "risk": "low",
                "approval_required": False,
            }
        ],
    )

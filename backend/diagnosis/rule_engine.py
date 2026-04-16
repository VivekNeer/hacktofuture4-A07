from typing import Any


FINGERPRINTS = {
    "FP-001": "memory_exhaustion_oom",
    "FP-002": "crash_loop_application_error",
    "FP-003": "image_pull_failure",
}


def match_fingerprint(snapshot: dict[str, Any]) -> dict[str, Any]:
    memory_pct = float(snapshot.get("memory_pct", 0))
    event = str(snapshot.get("event_reason", "")).lower()

    if memory_pct >= 90 and "oom" in event:
        return {
            "fingerprint_id": "FP-001",
            "root_cause": FINGERPRINTS["FP-001"],
            "confidence": 0.92,
        }

    if "imagepullbackoff" in event:
        return {
            "fingerprint_id": "FP-003",
            "root_cause": FINGERPRINTS["FP-003"],
            "confidence": 0.9,
        }

    return {
        "fingerprint_id": "FP-UNKNOWN",
        "root_cause": "unknown",
        "confidence": 0.4,
    }

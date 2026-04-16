"""
LLM-based fallback diagnosis when rule-based fingerprinting confidence is low.
Handles AI API calls with JSON parsing, graceful error handling, and token budgeting.
"""

import json
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


class LLMFallbackError(Exception):
    """Exception for LLM fallback processing errors."""
    pass


def call_llm_api(
    incident_snapshot: Dict[str, Any],
    model: str = "custom-api",
    api_url: str = "https://www.aiversusme.com/api/chat",
    timeout_seconds: int = 30,
) -> Optional[Dict[str, Any]]:
    """
    Call LLM API to diagnose incident when rule-based confidence is low.
    
    Args:
        incident_snapshot: IncidentSnapshot dict with metrics, events, logs
        model: Model identifier (for tracking/logging)
        api_url: LLM API endpoint
        timeout_seconds: Request timeout
    
    Returns:
        Parsed diagnosis dict with fields: {root_cause, confidence, reasoning, actions}
        Returns None if API fails or parsing fails (graceful degradation)
    
    Raises:
        LLMFallbackError: If API communication fails unexpectedly
    """
    
    # Construct prompt for LLM
    prompt = _construct_diagnosis_prompt(incident_snapshot)
    
    try:
        # Call LLM API
        response = requests.post(
            api_url,
            json={"message": prompt},
            timeout=timeout_seconds,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Extract diagnosis from LLM response
        diagnosis = _parse_llm_response(response_data, incident_snapshot)
        
        logger.info(f"LLM fallback diagnosis: {diagnosis['root_cause']} (confidence: {diagnosis['confidence']})")
        return diagnosis
        
    except requests.exceptions.Timeout:
        logger.warning(f"LLM API timeout after {timeout_seconds}s - falling back to rule-only")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"LLM API connection failed - falling back to rule-only: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"LLM API HTTP error - falling back to rule-only: {e}")
        return None
    except (ValueError, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse LLM response - falling back to rule-only: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected LLM fallback error: {e}")
        raise LLMFallbackError(f"LLM fallback failed unexpectedly: {e}")


def _construct_diagnosis_prompt(snapshot: Dict[str, Any]) -> str:
    """
    Construct a diagnosis prompt for the LLM based on incident snapshot.
    
    Args:
        snapshot: IncidentSnapshot with metrics, events, logs
    
    Returns:
        Formatted prompt for LLM API
    """
    
    metrics = snapshot.get("metrics", {})
    events = snapshot.get("events", [])
    logs_summary = snapshot.get("logs_summary", [])
    
    prompt = f"""Analyze this Kubernetes incident and provide diagnosis:

**Current Metrics:**
- Memory: {metrics.get('memory_pct', 'unknown')}%
- CPU: {metrics.get('cpu_pct', 'unknown')}%
- Restart Count: {metrics.get('restart_count', 'unknown')}

**Events:**
{chr(10).join(f"- {e}" for e in events[:5]) if events else "- None"}

**Log Signatures (top 5):**
{chr(10).join(f"- {l}" for l in logs_summary[:5]) if logs_summary else "- None"}

**Task:** Identify the most likely root cause. Respond with JSON:
{{
    "root_cause": "brief root cause description",
    "confidence": 0.0-1.0,
    "reasoning": "explanation",
    "suggested_actions": ["action1", "action2"]
}}

Respond with ONLY valid JSON, no extra text."""
    
    return prompt


def _parse_llm_response(response_data: Dict[str, Any], snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse LLM API response and extract diagnosis.
    
    Args:
        response_data: Raw response from LLM API
        snapshot: Original incident snapshot (fallback data source)
    
    Returns:
        Normalized diagnosis dict: {root_cause, confidence, reasoning, actions}
    
    Raises:
        ValueError: If response format is invalid
    """
    
    # Extract message field from response
    message = response_data.get("message", "")
    if not message:
        raise ValueError("No message in LLM response")
    
    # Try to parse JSON from message
    try:
        # Sometimes LLM wraps JSON in markdown or extra text
        # Try direct parse first
        diagnosis = json.loads(message)
    except json.JSONDecodeError:
        # Try extracting JSON from text (e.g., ```json ... ```)
        try:
            import re
            json_match = re.search(r'\{.*\}', message, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            diagnosis = json.loads(json_match.group(0))
        except (json.JSONDecodeError, AttributeError) as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {e}")
    
    # Validate required fields
    required_fields = ["root_cause", "confidence"]
    for field in required_fields:
        if field not in diagnosis:
            raise ValueError(f"Missing required field: {field}")
    
    # Ensure confidence is between 0 and 1
    confidence = diagnosis.get("confidence", 0)
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        logger.warning(f"Invalid confidence value: {confidence}, clamping to valid range")
        confidence = max(0, min(1, float(confidence)))
    
    # Normalize response
    return {
        "root_cause": str(diagnosis["root_cause"]),
        "confidence": float(confidence),
        "reasoning": str(diagnosis.get("reasoning", "AI diagnosed based on incident signals")),
        "suggested_actions": diagnosis.get("suggested_actions", []),
        "source": "llm_fallback",
    }


def should_use_llm_fallback(rule_confidence: float, budget_allows: bool) -> bool:
    """
    Determine if LLM fallback should be used.
    
    Args:
        rule_confidence: Confidence score from rule-based matching (0-1)
        budget_allows: Whether token budget allows another AI call
    
    Returns:
        True if LLM should be called, False otherwise
    """
    # Use LLM if rule confidence is low AND budget permits
    confidence_threshold = 0.75
    return rule_confidence < confidence_threshold and budget_allows

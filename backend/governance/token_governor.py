from dataclasses import dataclass


@dataclass
class TokenBudget:
    max_calls_per_incident: int = 2
    max_estimated_cost_usd: float = 0.15


class TokenGovernor:
    def __init__(self, budget: TokenBudget | None = None) -> None:
        self.budget = budget or TokenBudget()

    def estimate_tokens(self, text: str) -> int:
        # Basic approximation stub for day-1 integration.
        return max(1, len(text) // 4)

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return round((input_tokens + output_tokens) * 0.0000015, 6)

    def allow_ai_call(self, calls_so_far: int, estimated_total_cost: float) -> bool:
        if calls_so_far >= self.budget.max_calls_per_incident:
            return False
        if estimated_total_cost > self.budget.max_estimated_cost_usd:
            return False
        return True

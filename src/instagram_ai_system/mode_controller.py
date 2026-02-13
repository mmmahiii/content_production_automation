from __future__ import annotations

from dataclasses import dataclass


Mode = str


@dataclass(slots=True)
class ModeInputs:
    hit_rate_7d: float
    novelty_fatigue: float
    account_volatility: float
    confidence_trend: float
    monetization_drift: float
    plateau_cycles: int
    hours_since_mode_change: int
    drawdown_24h: float
    risk_budget: float


@dataclass(slots=True)
class ModeDecision:
    mode: Mode
    explore_coef: float
    rationale: list[str]


class ModeController:
    """Rule-based controller implementing docs/strategy/mode-controller.md transitions."""

    def decide(self, *, current_mode: Mode, explore_coef: float, inputs: ModeInputs) -> ModeDecision:
        mode = current_mode
        rationale: list[str] = []

        if inputs.hours_since_mode_change < 6:
            rationale.append("cooldown_active")
        else:
            if current_mode == "exploit" and inputs.novelty_fatigue >= 0.65:
                mode = "explore"
                rationale.append("exploit_to_explore_due_to_fatigue")
            elif current_mode == "explore" and inputs.hit_rate_7d >= 0.6 and inputs.confidence_trend > 0:
                mode = "mutation"
                rationale.append("explore_to_mutation_due_to_repeated_wins")
            elif inputs.plateau_cycles >= 3 and inputs.risk_budget >= 0.6 and inputs.hours_since_mode_change >= 12:
                mode = "chaos"
                rationale.append("plateau_triggered_chaos")
            elif current_mode == "chaos" and inputs.hit_rate_7d < 0.5:
                mode = "exploit"
                rationale.append("chaos_back_to_exploit")

        adjusted = explore_coef + (0.2 - inputs.drawdown_24h) * 0.1 + (inputs.monetization_drift * 0.05)
        adjusted = min(0.8, max(0.05, adjusted))
        return ModeDecision(mode=mode, explore_coef=round(adjusted, 4), rationale=rationale or ["stay"])

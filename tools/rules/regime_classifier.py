"""
Regime classification (rule-based, no LLM).

States:
  Normal          — no active stress signals
  Slowdown        — FTSE drawdown 10–15%
  Recession Risk  — FTSE drawdown > 15% AND yield curve inverted
  Inflation Shock — commodity spike AND bond yield shock

Reads live signals from the rule modules.
"""

from tools.rules.market_stress import compute_drawdown
from tools.rules.macro_check import check_yield_curve_inversion, check_commodity_spike, check_bond_yield_shock

REGIMES = ["Normal", "Slowdown", "Recession Risk", "Inflation Shock"]


def classify_regime(
    drawdown: float,
    yield_inverted: bool,
    commodity_spike: bool,
    bond_shock: bool,
) -> str:
    if commodity_spike and bond_shock:
        return "Inflation Shock"
    if drawdown > 0.15 and yield_inverted:
        return "Recession Risk"
    if 0.10 <= drawdown <= 0.15:
        return "Slowdown"
    return "Normal"


def run() -> dict:
    """Evaluate all signals and return the current regime state."""
    dd_result = compute_drawdown()
    drawdown = dd_result["drawdown"] if dd_result else 0.0

    yield_inverted = check_yield_curve_inversion() is not None
    commodity_spike = check_commodity_spike() is not None
    bond_shock = check_bond_yield_shock() is not None

    regime = classify_regime(drawdown, yield_inverted, commodity_spike, bond_shock)

    return {
        "regime": regime,
        "drawdown": drawdown,
        "yield_inverted": yield_inverted,
        "commodity_spike": commodity_spike,
        "bond_shock": bond_shock,
    }


if __name__ == "__main__":
    from tools.db import init_db
    init_db()
    result = run()
    print(f"Current regime: {result['regime']}")
    print(result)

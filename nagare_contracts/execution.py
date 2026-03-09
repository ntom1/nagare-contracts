"""Execution configuration constants — single source of truth.

All execution-related constants MUST be imported from this module.

Model Roles:
  - Backtest: SLIPPAGE_PCT used as flat cost deduction from net PnL
  - Paper trade: fills at raw open price; LIQUIDITY_TIERS for diagnostics
  - DB signals: expected_fill_price = signal_price * (1 + SLIPPAGE_PCT)
  - Governance: displays these constants as the active execution assumptions

See docs/execution_assumptions.md for the authoritative specification.
"""

# --- Cost Model (Backtest & DB expected_fill_price) ---
SLIPPAGE_PCT = 0.001  # 0.1% per side, 0.2% round trip
COMMISSION_PER_TRADE = 0  # SBI/Rakuten free tier

# --- Fill Realism Model (Paper Trade diagnostics) ---
FILL_MODEL_VERSION = "v1.0-liquidity-tier"

# (min_avg_vol, max_avg_vol): (expected_slippage_bps, partial_fill_risk, label)
LIQUIDITY_TIERS = {
    (0, 100_000):        (30, 0.20, "Very Low"),
    (100_000, 300_000):  (15, 0.10, "Low"),
    (300_000, 1_000_000): (8, 0.03, "Medium"),
    (1_000_000, 5_000_000): (5, 0.01, "High"),
    (5_000_000, float("inf")): (3, 0.005, "Very High"),
}

GAP_WARNING_PCT = 3.0    # Warn if open deviates > 3% from signal price
STALE_SIGNAL_DAYS = 3    # Warn if signal is > 3 days old

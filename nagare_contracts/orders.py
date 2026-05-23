"""Signal, order, and execution contracts for cross-repo integration.

SignalRequest: nagare/ronin → ronin (strategy signal generation input)
SignalOutput: ronin → DB/nagare (strategy signal generation output)
OrderIntent: ronin → DB → torii (approved order to execute)
ExecutionReport: torii → DB → nagare/ronin (execution result)
"""

from dataclasses import dataclass, field
from nagare_contracts.broker import BrokerError


@dataclass
class SignalRequest:
    """Input contract for ronin-owned signal generation."""

    date: str
    strategy_version: str
    config_hash: str
    capital: float
    current_positions: list[str] = field(default_factory=list)
    max_positions: int = 2


@dataclass
class SignalOutput:
    """Output contract from ronin's signal generator.

    signal_id is assigned by the persistence layer, so it may be empty before
    the signal is written to DB.
    """

    ticker: str
    side: str
    intended_price: float
    qty: int
    strategy_version: str
    config_hash: str
    score: float = 0.0
    filters_applied: dict = field(default_factory=dict)
    signal_id: str | None = None


@dataclass
class SignalDecision:
    """Per-candidate decision trace from ronin's signal generator.

    This lets dashboards and observers consume the strategy owner's own
    acceptance/rejection result instead of re-running a mirror filter chain.
    """

    ticker: str
    decision: str                     # accepted | rejected
    side: str = "BUY"
    rejection_reason_code: str | None = None
    filter_stage: int | None = None
    candidate_rank: int | None = None
    score: float = 0.0
    blocked_by_cap: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class OrderIntent:
    """Approved order intent from ronin, consumed by torii.

    ronin writes to DB, torii polls and executes.

    Fix E-1 (broker逆指値 paired stop):
        stop_loss_pct を指定するとgateway が entry fill 後に paired STOP 注文を
        broker に提出し、当日ザラ場で SL を発火可能にする。
        - BUY entry の場合: STOP SELL @ fill_price * (1 - stop_loss_pct)
        - SELL entry (信用空売り) の場合: STOP BUY @ fill_price * (1 + stop_loss_pct)

        None なら stop は emit されない (既存の MARKET-only 動作)。

        take_profit_pct は同様に paired LIMIT (利確) を emit する場合に使う。
        STOP / TP のいずれか一方のみ、両方、なし、を選べる。

    paired_intent_id (出力時、gateway が記入):
        STOP/TP として emit された intent は、entry intent の intent_id を
        ここに保持する。ExecutionReport で entry/stop の対応を辿るための
        link。ronin 側で OrderIntent を直接 STOP として書く場合は手動で設定。
    """
    intent_id: str
    signal_id: str
    ticker: str
    side: str            # BUY | SELL
    qty: int
    intended_price: float
    strategy_version: str
    config_hash: str
    max_slippage_bps: float = 30.0
    urgency: str = "normal"   # "normal" | "immediate"
    approved_at: str = ""     # ISO 8601
    # Fix E-1: paired stop / take-profit instructions
    order_type: str = "MARKET"   # MARKET | LIMIT | STOP | STOP_LIMIT
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    trigger_price: float | None = None        # for explicit STOP / STOP_LIMIT
    trigger_above: bool | None = None         # True: 以上 / False: 以下
    paired_intent_id: str | None = None       # parent intent_id (stop が紐付く entry)


@dataclass
class ExecutionReport:
    """Execution result from torii, recorded to DB.

    torii writes after broker interaction. nagare reads for dashboards,
    ronin reads for gate evaluation.
    """
    order_id: str
    intent_id: str
    signal_id: str
    broker: str              # "kabustation" | "rakuten" | "paper"
    broker_order_id: str | None
    status: str              # one of EXECUTION_STATUSES
    fill_price: float | None = None
    fill_qty: int | None = None
    slippage_bps: float | None = None
    fill_time: str | None = None
    error: BrokerError | None = None


# Valid ExecutionReport statuses
EXECUTION_STATUSES = [
    "PENDING", "SUBMITTED", "PARTIAL", "FILLED",
    "CANCELLED", "REJECTED", "ERROR",
]

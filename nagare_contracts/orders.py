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

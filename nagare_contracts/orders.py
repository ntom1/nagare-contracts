"""OrderIntent and ExecutionReport — cross-repo integration contracts.

OrderIntent: ronin → DB → torii (approved order to execute)
ExecutionReport: torii → DB → nagare/ronin (execution result)
"""

from dataclasses import dataclass, field
from nagare_contracts.broker import BrokerError


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

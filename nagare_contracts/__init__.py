"""nagare-contracts — shared contracts for jcdd/nagare/ronin/torii.

Zero-dependency package. Only uses Python stdlib.
All 4 repos install this via `pip install -e ../nagare-contracts`.
"""

from nagare_contracts.broker import (  # noqa: F401
    Broker,
    BrokerError,
    OrderRequest,
    OrderResult,
    Quote,
    Position,
    ReconciliationResult,
    AccountSummary,
    CashMarginStatus,
)
from nagare_contracts.orders import (  # noqa: F401
    OrderIntent,
    ExecutionReport,
    EXECUTION_STATUSES,
)
from nagare_contracts.heartbeat import (  # noqa: F401
    Heartbeat,
    HEARTBEAT_STATUSES,
)
from nagare_contracts.states import (  # noqa: F401
    ORDER_STATES,
    SIGNAL_STATES,
    PROPOSAL_TRANSITIONS,
    APPROVAL_REASON_CODES,
)
from nagare_contracts.execution import (  # noqa: F401
    SLIPPAGE_PCT,
    COMMISSION_PER_TRADE,
    FILL_MODEL_VERSION,
    LIQUIDITY_TIERS,
    GAP_WARNING_PCT,
    STALE_SIGNAL_DAYS,
)

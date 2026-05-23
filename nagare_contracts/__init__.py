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
    SignalRequest,
    SignalOutput,
    SignalDecision,
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
    StatusChangeEvent,
    STATUS_CHANGE_FIELDS,
    LIFECYCLE_STAGES,
    GATE_STATUSES,
    READINESS_STATUSES,
    STATUS_CHANGE_FIELD_ALLOWED_VALUES,
    STATUS_CHANGE_REASON_CODES,
    STATUS_CHANGE_ACTORS,
    STATUS_CHANGE_COMPONENTS,
)
from nagare_contracts.validation import (  # noqa: F401
    ValidationError,
    validate_order_request,
    validate_status_change,
)
from nagare_contracts.execution import (  # noqa: F401
    SLIPPAGE_PCT,
    COMMISSION_PER_TRADE,
    FILL_MODEL_VERSION,
    LIQUIDITY_TIERS,
    GAP_WARNING_PCT,
    STALE_SIGNAL_DAYS,
)
from nagare_contracts.ops_shared import (  # noqa: F401
    configure_connection_provider,
    db_read,
    db_write,
    get_connection_provider,
    make_id,
    now_jst,
    record_halt,
    record_halt_restart,
    record_heartbeat,
    record_override,
)

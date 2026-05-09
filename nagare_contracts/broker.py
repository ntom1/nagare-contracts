"""Broker Protocol and dataclasses — shared across all repos.

Any class implementing the Broker Protocol methods is a valid broker.
No explicit inheritance required (structural subtyping via typing.Protocol).
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class BrokerError:
    """Normalized broker error for rejection/cancellation."""
    source: str          # "broker" | "exchange" | "approval" | "system"
    code: str            # broker-specific error code
    reason: str          # human-readable
    retryable: bool      # whether the order can be retried


@dataclass
class OrderRequest:
    """Outbound order request from signal pipeline to broker.

    Fix E-1 (broker逆指値): order_type に STOP / STOP_LIMIT を追加。
    既存呼び出し (MARKET / LIMIT) は新フィールドを未指定のままで動作する。

    order_type:
        - MARKET: 成行
        - LIMIT: 指値 (intended_price で約定)
        - STOP: 逆指値成行 (trigger_price 到達で MARKET 約定)
        - STOP_LIMIT: 逆指値指値 (trigger_price 到達で LIMIT 約定 at intended_price)

    trigger_price / trigger_above は STOP / STOP_LIMIT で必須。
    trigger_above=False で「現在値が trigger_price 以下に到達したら発火」
    (= long position の保護用 SELL stop)、True で「以上に到達したら発火」
    (= short カバー用 BUY stop)。
    """
    signal_id: str
    ticker: str
    side: str       # BUY | SELL
    qty: int
    intended_price: float
    order_type: str  # MARKET | LIMIT | STOP | STOP_LIMIT
    trigger_price: float | None = None
    trigger_above: bool | None = None


@dataclass
class OrderResult:
    """Broker response after order submission or status query."""
    order_id: str
    broker_order_id: str | None
    status: str       # one of ORDER_STATES
    fill_price: float | None
    fill_qty: int | None
    slippage_bps: float | None
    fill_time: str | None
    reject_reason: str | None    # DEPRECATED: use error field
    error: BrokerError | None = None


@dataclass
class Quote:
    """Real-time quote for a ticker."""
    ticker: str
    bid: float | None
    ask: float | None
    last: float
    volume: int
    timestamp: str  # ISO format


@dataclass
class Position:
    """Single position held by the broker account."""
    ticker: str
    qty: int
    avg_cost: float
    unrealized_pnl: float


@dataclass
class ReconciliationResult:
    """Result of comparing expected positions with actual broker positions."""
    matches: list[str]
    mismatches: list[dict]  # {"ticker": str, "expected_qty": int, "actual_qty": int}
    orphans: list[str]
    missing: list[str]


@dataclass
class AccountSummary:
    """Broker account summary."""
    cash: float
    buying_power: float
    total_equity: float
    unrealized_pnl: float


@dataclass
class CashMarginStatus:
    """Cash and margin account status."""
    cash: float
    margin_buying_power: float
    margin_maintenance_rate: float | None
    margin_used: float


class Broker(Protocol):
    """Broker-agnostic interface for order routing and position management."""

    def submit_order(self, order: OrderRequest) -> OrderResult: ...
    def cancel_order(self, order_id: str) -> bool: ...
    def get_order_status(self, order_id: str) -> OrderResult: ...
    def get_positions(self) -> list[Position]: ...
    def get_account_summary(self) -> AccountSummary: ...
    def get_cash_margin_status(self) -> CashMarginStatus: ...
    def heartbeat(self) -> bool: ...
    def cancel_all(self) -> int: ...
    def get_quote(self, ticker: str) -> Quote: ...
    def reconcile_positions(self, expected: list[Position]) -> ReconciliationResult: ...
    def emergency_flatten(self) -> list[OrderResult]: ...

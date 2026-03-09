"""Heartbeat contract — all components report liveness to shared DB.

Naming convention: {repo}_{process}
  e.g., torii_order_router, nagare_monitor, ronin_gate, jcdd_loader
"""

from dataclasses import dataclass, field


@dataclass
class Heartbeat:
    """Periodic liveness report written to system_heartbeats table."""
    component: str      # e.g., "torii_order_router"
    status: str         # one of HEARTBEAT_STATUSES
    last_action: str    # e.g., "Filled ORD-2026-03-10-001"
    checked_at: str     # ISO 8601
    details: dict = field(default_factory=dict)


HEARTBEAT_STATUSES = ["OK", "ALERT", "CRITICAL"]

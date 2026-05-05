"""State constants and transition rules — shared across all repos.

Single source of truth for order states, signal states, proposal
transitions, and approval reason codes.
"""

from dataclasses import dataclass

# Normalized order states (broker-agnostic)
ORDER_STATES = ["PENDING", "SENT", "PARTIAL_FILL", "FILLED", "REJECTED", "CANCELLED"]

# Signal lifecycle states
SIGNAL_STATES = ["GENERATED", "FILLED", "SKIPPED", "CANCELLED"]

# Valid proposal status transitions (from_status, to_status)
PROPOSAL_TRANSITIONS = {
    ("PROPOSED", "APPROVED"),
    ("PROPOSED", "REJECTED"),
    ("APPROVED", "DEPLOYED"),
    ("APPROVED", "REJECTED"),
    ("DEPLOYED", "ROLLED_BACK"),
}

# Approval gate reason codes (machine-readable)
APPROVAL_REASON_CODES = [
    "ROBUSTNESS_LOW_WF",     # WF pass rate below threshold
    "ROBUSTNESS_MISSING",    # No robustness evidence found
    "SESSION_FAILED",        # Session quality check failed
    "SESSION_MISSING",       # No session review found
    "EVIDENCE_OLD",          # Evidence older than threshold
    "EVIDENCE_STALE",        # Evidence missing or unparseable
]

# ---------------------------------------------------------------------------
# Status Change Event — enums, schema, allowed values
# ---------------------------------------------------------------------------

# Fields that can be changed via StatusChangeEvent
STATUS_CHANGE_FIELDS = ["lifecycle_stage", "gate_status", "readiness_status"]

# Allowed values per field
LIFECYCLE_STAGES = [
    "Paper Trading", "Gate Passed", "Ready for Incubation",
    "Incubation", "Production Ready", "Production",
]

GATE_STATUSES = [
    "NOT_YET (30+ trades蓄積待ち)",
    "IN_PROGRESS",
    "PASS",
    "FAIL",
]

READINESS_STATUSES = [
    "NOT READY",
    "PARTIALLY READY",
    "READY",
]

STATUS_CHANGE_FIELD_ALLOWED_VALUES = {
    "lifecycle_stage": LIFECYCLE_STAGES,
    "gate_status": GATE_STATUSES,
    "readiness_status": READINESS_STATUSES,
}


@dataclass
class StatusChangeEvent:
    """Canonical schema for auditable status changes."""
    field: str
    from_value: str
    to_value: str
    reason_code: str
    evidence: str
    timestamp: str
    actor: str
    source_component: str
    event_id: str | None = None

    def to_validation_dict(self) -> dict:
        """Return the wire shape consumed by validate_status_change()."""
        event = {
            "field": self.field,
            "from": self.from_value,
            "to": self.to_value,
            "reason_code": self.reason_code,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "source_component": self.source_component,
        }
        if self.event_id is not None:
            event["event_id"] = self.event_id
        return event


# reason_code for status changes
STATUS_CHANGE_REASON_CODES = [
    "gate-review",           # Gate evaluation passed
    "readiness-evidence",    # Production Readiness item PASS/FAIL change
    "phase-transition",      # Migration phase progression
    "manual-override",       # Manual status correction
    "rollback",              # Revert to previous status
]

# Known actors (human + automated)
STATUS_CHANGE_ACTORS = [
    "jarvis",                # Human operator
    "ronin_gate",            # Automated gate evaluation
    "torii_failsafe",        # Automated failsafe trigger
    "nagare_monitor",        # Automated anomaly detection
    "ci-bot",                # CI/CD automation
]

# Source components (4 repos + manual)
STATUS_CHANGE_COMPONENTS = ["ronin", "torii", "nagare", "jcdd", "manual"]

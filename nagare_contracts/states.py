"""State constants and transition rules — shared across all repos.

Single source of truth for order states, signal states, proposal
transitions, and approval reason codes.
"""

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

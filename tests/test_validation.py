"""Unit tests for validate_status_change() — tier-based precedence rules.

5 mandatory patterns from migration_plan.md:
1. same field, multiple violations → lowest tier only
2. different fields, multiple violations → all returned
3. same tier, different fields → both returned
4. field_value_mismatch (Tier D)
5. valid event → empty errors
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nagare_contracts.validation import ValidationError, validate_status_change


def _valid_event() -> dict:
    """Minimal valid StatusChangeEvent."""
    return {
        "field": "lifecycle_stage",
        "from": "Paper Trading",
        "to": "Gate Passed",
        "reason_code": "gate-review",
        "evidence": "30+ trades, 6/6 criteria PASS",
        "timestamp": "2026-04-15T10:00:00+09:00",
        "actor": "ronin_gate",
        "source_component": "ronin",
    }


def _error_codes(errors: list[ValidationError]) -> list[str]:
    return [e.code for e in errors]


def _error_fields(errors: list[ValidationError]) -> list[str]:
    return [e.field for e in errors]


# -----------------------------------------------------------------------
# Pattern 1: same field, multiple violations → lowest tier only
# -----------------------------------------------------------------------

def test_same_field_lowest_tier_only():
    """timestamp missing (Tier A) should suppress Tier B checks."""
    event = _valid_event()
    del event["timestamp"]
    errors = validate_status_change(event)

    ts_errors = [e for e in errors if e.field == "timestamp"]
    assert len(ts_errors) == 1
    assert ts_errors[0].code == "missing_required_field"


def test_timestamp_timezone_missing_suppresses_format_check():
    """Tier B-2 (timezone_missing) should suppress Tier B-3 (format)."""
    event = _valid_event()
    event["timestamp"] = "2026-04-15T10:00:00"  # no timezone
    errors = validate_status_change(event)

    ts_errors = [e for e in errors if e.field == "timestamp"]
    assert len(ts_errors) == 1
    assert ts_errors[0].code == "timestamp_timezone_missing"


# -----------------------------------------------------------------------
# Pattern 2: different fields, multiple violations → all returned
# -----------------------------------------------------------------------

def test_different_fields_all_returned():
    """timestamp missing + reason_code invalid → both errors returned."""
    event = _valid_event()
    del event["timestamp"]
    event["reason_code"] = "misc"
    errors = validate_status_change(event)

    codes = _error_codes(errors)
    fields = _error_fields(errors)
    assert "missing_required_field" in codes
    assert "invalid_reason_code" in codes
    assert "timestamp" in fields
    assert "reason_code" in fields


# -----------------------------------------------------------------------
# Pattern 3: same tier, different fields → both returned
# -----------------------------------------------------------------------

def test_same_tier_different_fields():
    """source_component and actor both invalid (Tier B-enum) → both returned."""
    event = _valid_event()
    event["source_component"] = "kubernetes"
    event["actor"] = "admin"
    errors = validate_status_change(event)

    codes = _error_codes(errors)
    fields = _error_fields(errors)
    assert "invalid_source_component" in codes
    assert "invalid_actor" in codes
    assert "source_component" in fields
    assert "actor" in fields


# -----------------------------------------------------------------------
# Pattern 4: field_value_mismatch (Tier D)
# -----------------------------------------------------------------------

def test_field_value_mismatch():
    """FILLED is valid in ORDER_STATES but not in lifecycle_stage → Tier D."""
    event = _valid_event()
    event["from"] = "FILLED"  # valid enum, wrong field
    errors = validate_status_change(event)

    from_errors = [e for e in errors if e.field == "from"]
    assert len(from_errors) == 1
    assert from_errors[0].code == "field_value_mismatch"


def test_invalid_enum_value_not_mismatch():
    """'foo' is not in any enum → invalid_enum_value, not field_value_mismatch."""
    event = _valid_event()
    event["from"] = "foo"
    errors = validate_status_change(event)

    from_errors = [e for e in errors if e.field == "from"]
    assert len(from_errors) == 1
    assert from_errors[0].code == "invalid_enum_value"


# -----------------------------------------------------------------------
# Pattern 5: valid event → empty errors
# -----------------------------------------------------------------------

def test_valid_event_empty_errors():
    """Fully valid event produces no errors."""
    event = _valid_event()
    errors = validate_status_change(event)
    assert errors == []


# -----------------------------------------------------------------------
# Additional coverage: edge cases
# -----------------------------------------------------------------------

def test_invalid_field_value():
    """field value not in STATUS_CHANGE_FIELDS → invalid_enum_value."""
    event = _valid_event()
    event["field"] = "nonexistent_field"
    errors = validate_status_change(event)

    field_errors = [e for e in errors if e.field == "field"]
    assert len(field_errors) == 1
    assert field_errors[0].code == "invalid_enum_value"


def test_utc_timestamp_rejected():
    """UTC (Z) is not allowed — JST only."""
    event = _valid_event()
    event["timestamp"] = "2026-04-15T01:00:00Z"
    errors = validate_status_change(event)

    ts_errors = [e for e in errors if e.field == "timestamp"]
    assert len(ts_errors) == 1
    assert ts_errors[0].code == "invalid_timestamp_format"


def test_empty_string_is_missing():
    """Empty string for required field → missing_required_field."""
    event = _valid_event()
    event["evidence"] = ""
    errors = validate_status_change(event)

    ev_errors = [e for e in errors if e.field == "evidence"]
    assert len(ev_errors) == 1
    assert ev_errors[0].code == "missing_required_field"


def test_multiple_missing_fields():
    """Multiple missing fields all reported."""
    event = _valid_event()
    del event["field"]
    del event["reason_code"]
    del event["actor"]
    errors = validate_status_change(event)

    missing = [e for e in errors if e.code == "missing_required_field"]
    missing_fields = {e.field for e in missing}
    assert {"field", "reason_code", "actor"} <= missing_fields


def test_all_reason_codes_accepted():
    """All defined reason codes are valid."""
    from nagare_contracts.states import STATUS_CHANGE_REASON_CODES
    for rc in STATUS_CHANGE_REASON_CODES:
        event = _valid_event()
        event["reason_code"] = rc
        errors = validate_status_change(event)
        assert errors == [], f"reason_code '{rc}' should be valid but got {errors}"


def test_all_lifecycle_stages_accepted():
    """All defined lifecycle stages are valid for from/to."""
    from nagare_contracts.states import LIFECYCLE_STAGES
    for stage in LIFECYCLE_STAGES:
        event = _valid_event()
        event["from"] = stage
        event["to"] = stage  # same is fine for validation
        errors = validate_status_change(event)
        assert errors == [], f"lifecycle_stage '{stage}' should be valid but got {errors}"


def test_deterministic_output():
    """Same input always produces same error codes in same order."""
    event = _valid_event()
    event["source_component"] = "k8s"
    event["actor"] = "unknown_bot"
    del event["evidence"]

    results = [validate_status_change(event) for _ in range(10)]
    first_codes = [(e.code, e.field) for e in results[0]]
    for r in results[1:]:
        assert [(e.code, e.field) for e in r] == first_codes

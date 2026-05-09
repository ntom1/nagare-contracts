"""Status change event validation — field-level precedence, deterministic errors.

Implements the validator spec from docs/migration_plan.md:
- Precedence is applied per-field (not per-event)
- Same field, multiple tiers → lowest tier only
- Different fields → all errors returned
- Deterministic: same input always produces same error set
"""

import re
from dataclasses import dataclass

from nagare_contracts.states import (
    LIFECYCLE_STAGES,
    ORDER_STATES,
    SIGNAL_STATES,
    STATUS_CHANGE_ACTORS,
    STATUS_CHANGE_COMPONENTS,
    STATUS_CHANGE_FIELD_ALLOWED_VALUES,
    STATUS_CHANGE_FIELDS,
    STATUS_CHANGE_REASON_CODES,
)


@dataclass
class ValidationError:
    """Machine-readable validation failure."""
    code: str
    field: str
    message: str


# All known enum values across all domains (for invalid_enum_value vs field_value_mismatch)
_ALL_KNOWN_VALUES: set[str] = set(
    LIFECYCLE_STAGES + ORDER_STATES + SIGNAL_STATES
    + STATUS_CHANGE_FIELDS + STATUS_CHANGE_REASON_CODES
    + STATUS_CHANGE_ACTORS + STATUS_CHANGE_COMPONENTS
    + [
        value
        for allowed_values in STATUS_CHANGE_FIELD_ALLOWED_VALUES.values()
        for value in allowed_values
    ]
)

# Field-specific allowed values for from/to (keyed by the `field` value)
_FIELD_ALLOWED_VALUES: dict[str, list[str]] = STATUS_CHANGE_FIELD_ALLOWED_VALUES

# Required fields for a StatusChangeEvent
_REQUIRED_FIELDS = [
    "field", "from", "to", "reason_code", "evidence",
    "timestamp", "actor", "source_component",
]

# ISO 8601 with mandatory JST timezone offset (+09:00)
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$"
)

# Timezone offset pattern (any offset, including Z)
_HAS_TIMEZONE_RE = re.compile(
    r"[+-]\d{2}:\d{2}$|Z$"
)


def validate_status_change(event: dict) -> list[ValidationError]:
    """Validate a StatusChangeEvent dict. Returns errors (empty = valid).

    Precedence tiers (per-field):
      A (1): missing_required_field
      B-timestamp (2-3): timestamp_timezone_missing → invalid_timestamp_format
      B-enum (4): invalid_source_component, invalid_reason_code, invalid_actor
      C (5): invalid_enum_value
      D (6): field_value_mismatch
    """
    errors: list[ValidationError] = []
    # Track which fields already have an error (for per-field precedence)
    errored_fields: set[str] = set()

    # --- Tier A: missing_required_field ---
    for f in _REQUIRED_FIELDS:
        if f not in event or event[f] is None or event[f] == "":
            errors.append(ValidationError(
                code="missing_required_field",
                field=f,
                message=f"Required field '{f}' is missing or empty",
            ))
            errored_fields.add(f)

    # --- Tier B-timestamp (2-3): only if timestamp passed Tier A ---
    if "timestamp" not in errored_fields:
        ts = event["timestamp"]
        if not _HAS_TIMEZONE_RE.search(str(ts)):
            errors.append(ValidationError(
                code="timestamp_timezone_missing",
                field="timestamp",
                message=f"Timestamp '{ts}' has no timezone offset. JST (+09:00) required",
            ))
            errored_fields.add("timestamp")
        elif not _TIMESTAMP_RE.match(str(ts)):
            errors.append(ValidationError(
                code="invalid_timestamp_format",
                field="timestamp",
                message=f"Timestamp '{ts}' is not ISO 8601 JST format (YYYY-MM-DDTHH:MM:SS+09:00)",
            ))
            errored_fields.add("timestamp")

    # --- Tier B-enum (4): specialized enum checks ---
    if "source_component" not in errored_fields:
        if event["source_component"] not in STATUS_CHANGE_COMPONENTS:
            errors.append(ValidationError(
                code="invalid_source_component",
                field="source_component",
                message=f"'{event['source_component']}' not in allowed components: {STATUS_CHANGE_COMPONENTS}",
            ))
            errored_fields.add("source_component")

    if "reason_code" not in errored_fields:
        if event["reason_code"] not in STATUS_CHANGE_REASON_CODES:
            errors.append(ValidationError(
                code="invalid_reason_code",
                field="reason_code",
                message=f"'{event['reason_code']}' not in allowed reason codes: {STATUS_CHANGE_REASON_CODES}",
            ))
            errored_fields.add("reason_code")

    if "actor" not in errored_fields:
        if event["actor"] not in STATUS_CHANGE_ACTORS:
            errors.append(ValidationError(
                code="invalid_actor",
                field="actor",
                message=f"'{event['actor']}' not in allowed actors: {STATUS_CHANGE_ACTORS}",
            ))
            errored_fields.add("actor")

    # --- Tier C (5): generic enum check for `field` ---
    if "field" not in errored_fields:
        if event["field"] not in STATUS_CHANGE_FIELDS:
            errors.append(ValidationError(
                code="invalid_enum_value",
                field="field",
                message=f"'{event['field']}' not in allowed fields: {STATUS_CHANGE_FIELDS}",
            ))
            errored_fields.add("field")

    # --- Tier D (6): field_value_mismatch for from/to ---
    target_field = event.get("field")
    if target_field and target_field in _FIELD_ALLOWED_VALUES:
        allowed = _FIELD_ALLOWED_VALUES[target_field]
        for key in ("from", "to"):
            if key not in errored_fields:
                val = event.get(key)
                if val is not None and val not in allowed:
                    if val in _ALL_KNOWN_VALUES:
                        errors.append(ValidationError(
                            code="field_value_mismatch",
                            field=key,
                            message=f"'{val}' is a valid enum value but not allowed for {target_field}. Allowed: {allowed}",
                        ))
                    else:
                        errors.append(ValidationError(
                            code="invalid_enum_value",
                            field=key,
                            message=f"'{val}' is not a known enum value for {target_field}. Allowed: {allowed}",
                        ))
                    errored_fields.add(key)

    return errors


# ---------------------------------------------------------------------------
# Fix E-1: OrderRequest validation
# ---------------------------------------------------------------------------

_ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT", "STOP", "STOP_LIMIT"}


def validate_order_request(order) -> list[ValidationError]:
    """Validate an OrderRequest dataclass instance.

    Returns empty list if valid. Each error follows the same shape as
    validate_status_change for consistency.

    Rules:
    - order_type must be one of MARKET / LIMIT / STOP / STOP_LIMIT
    - STOP / STOP_LIMIT require trigger_price > 0 and trigger_above is bool
    - MARKET / LIMIT must NOT have trigger_price (precaution against accidental
      dual-trigger orders)
    - qty > 0
    - intended_price >= 0 (MARKET allows 0)
    """
    errors: list[ValidationError] = []
    order_type = str(getattr(order, "order_type", "") or "").upper()
    qty = getattr(order, "qty", None)
    intended = getattr(order, "intended_price", None)
    trigger = getattr(order, "trigger_price", None)
    trigger_above = getattr(order, "trigger_above", None)

    if order_type not in _ALLOWED_ORDER_TYPES:
        errors.append(ValidationError(
            code="invalid_order_type",
            field="order_type",
            message=f"'{order_type}' not in {sorted(_ALLOWED_ORDER_TYPES)}",
        ))
        return errors  # 後続の判定は order_type 依存なので fail-fast

    if not isinstance(qty, int) or qty <= 0:
        errors.append(ValidationError(
            code="invalid_qty",
            field="qty",
            message=f"qty must be positive int, got {qty!r}",
        ))

    if intended is None or float(intended) < 0:
        errors.append(ValidationError(
            code="invalid_intended_price",
            field="intended_price",
            message=f"intended_price must be >= 0, got {intended!r}",
        ))

    requires_trigger = order_type in {"STOP", "STOP_LIMIT"}
    if requires_trigger:
        if trigger is None or float(trigger) <= 0:
            errors.append(ValidationError(
                code="missing_trigger_price",
                field="trigger_price",
                message=f"{order_type} requires trigger_price > 0, got {trigger!r}",
            ))
        if not isinstance(trigger_above, bool):
            errors.append(ValidationError(
                code="missing_trigger_above",
                field="trigger_above",
                message=f"{order_type} requires trigger_above bool, got {trigger_above!r}",
            ))
    else:
        if trigger is not None:
            errors.append(ValidationError(
                code="unexpected_trigger_price",
                field="trigger_price",
                message=f"{order_type} must not set trigger_price, got {trigger!r}",
            ))

    return errors

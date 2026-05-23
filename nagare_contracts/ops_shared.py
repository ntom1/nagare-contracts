"""Shared operational DB write helpers.

The functions in this module are shared by jcdd/nagare/ronin/torii without
owning a concrete database driver. Each application configures a connection
provider, keeping this package dependency-free.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import sys
import uuid
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("nagare_contracts.ops_shared")

_JST = dt.timezone(dt.timedelta(hours=9))
_connection_provider: Callable[[], Any] | None = None


def configure_connection_provider(provider: Callable[[], Any] | None) -> None:
    """Configure the DB connection provider used by shared ops writes."""
    global _connection_provider
    _connection_provider = provider


def get_connection_provider() -> Callable[[], Any] | None:
    """Return the configured DB connection provider, if any."""
    return _connection_provider


def _resolve_provider(provider: Callable[[], Any] | None = None) -> Callable[[], Any]:
    resolved = provider or _connection_provider
    if resolved is None:
        raise RuntimeError("ops_shared connection provider is not configured")
    return resolved


def now_jst():
    return dt.datetime.now(_JST)


def make_id(prefix, date_str, seq=1):
    suffix = uuid.uuid4().hex[:8]
    return f"{prefix}-{date_str}-{seq:03d}-{suffix}"


def db_write(fn_name, severity, operation, *, connection_provider=None):
    """Execute a DB write operation with rollback and severity-aware logging."""
    conn = None
    try:
        conn = _resolve_provider(connection_provider)()
        result = operation(conn)
        conn.commit()
        return result
    except Exception as exc:
        log_fn = getattr(logger, severity, logger.error)
        log_fn("[ops_shared] %s failed: %s", fn_name, exc)
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def db_read(fn_name, operation, *, connection_provider=None):
    """Execute a DB read operation with graceful failure."""
    conn = None
    try:
        conn = _resolve_provider(connection_provider)()
        return operation(conn)
    except Exception as exc:
        logger.warning("[ops_shared] %s failed: %s", fn_name, exc)
        return None
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def record_heartbeat(component, status, last_action, details=None, *, connection_provider=None):
    """Record a system heartbeat. Returns True on success, False on failure."""
    def _op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_heartbeats (component, status, last_action, details, recorded_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    component,
                    status,
                    last_action,
                    json.dumps(details) if details else None,
                    now_jst(),
                ),
            )
        return True

    result = db_write(
        "record_heartbeat",
        "warning",
        _op,
        connection_provider=connection_provider,
    )
    return result is not None


def record_halt(
    reason,
    trigger_layer,
    trigger_value=None,
    threshold_value=None,
    *,
    connection_provider=None,
):
    """Record a halt event. Returns halt_id on success, None on failure."""
    now = now_jst()
    halt_id = f"HALT-{now.strftime('%Y%m%d-%H%M%S-%f')}-{uuid.uuid4().hex[:6]}"

    def _op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO halts (halt_id, halt_time, halt_reason, trigger_layer,
                    trigger_value, threshold_value)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (halt_id) DO NOTHING
                """,
                (halt_id, now, reason, trigger_layer, trigger_value, threshold_value),
            )
        return halt_id

    result = db_write(
        "record_halt",
        "critical",
        _op,
        connection_provider=connection_provider,
    )
    if result is None:
        print(
            f"CRITICAL: halt record failed - reason={reason}, layer={trigger_layer}",
            file=sys.stderr,
        )
    return result


def record_halt_restart(
    halt_id,
    restarted_by="system",
    conditions=None,
    *,
    connection_provider=None,
):
    """Record restart of a halt. Returns True on success, False on failure."""
    def _op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE halts SET restart_time = %s, restarted_by = %s,
                    restart_conditions = %s
                WHERE halt_id = %s
                """,
                (now_jst(), restarted_by, conditions, halt_id),
            )
            return cur.rowcount == 1

    result = db_write(
        "record_halt_restart",
        "error",
        _op,
        connection_provider=connection_provider,
    )
    if result is False:
        logger.error("[ops_shared] record_halt_restart found no matching halt: %s", halt_id)
    return result is True


def record_override(
    action,
    reason,
    overridden_by,
    related_halt_id=None,
    notes=None,
    *,
    connection_provider=None,
):
    """Record a manual override action. Returns override_id on success."""
    now = now_jst()
    override_id = f"OVR-{now.strftime('%Y%m%d-%H%M%S-%f')}-{uuid.uuid4().hex[:6]}"

    def _op(conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO overrides (override_id, override_time, action, reason,
                    overridden_by, related_halt_id, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (override_id) DO NOTHING
                """,
                (override_id, now, action, reason, overridden_by, related_halt_id, notes),
            )
        return override_id

    return db_write(
        "record_override",
        "error",
        _op,
        connection_provider=connection_provider,
    )


__all__ = [
    "configure_connection_provider",
    "db_read",
    "db_write",
    "get_connection_provider",
    "make_id",
    "now_jst",
    "record_halt",
    "record_halt_restart",
    "record_heartbeat",
    "record_override",
]

"""Fix E-1 OrderRequest validation tests.

新しい order_type (STOP / STOP_LIMIT) と trigger_price / trigger_above の
組み合わせ検証。MARKET / LIMIT の後方互換も確認する。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from nagare_contracts import OrderRequest
from nagare_contracts.validation import validate_order_request


def _req(**overrides):
    base = dict(
        signal_id="SIG-1", ticker="1234", side="BUY",
        qty=100, intended_price=1000.0, order_type="MARKET",
    )
    base.update(overrides)
    return OrderRequest(**base)


# --- Backward compatibility (MARKET / LIMIT 既存) ---

def test_market_order_valid():
    errs = validate_order_request(_req(order_type="MARKET"))
    assert errs == []


def test_limit_order_valid():
    errs = validate_order_request(_req(order_type="LIMIT", intended_price=1000.0))
    assert errs == []


def test_market_with_trigger_price_rejected():
    """MARKET で trigger_price を誤って付けたら reject。"""
    errs = validate_order_request(_req(order_type="MARKET", trigger_price=900.0))
    codes = [e.code for e in errs]
    assert "unexpected_trigger_price" in codes


# --- STOP order ---

def test_stop_order_valid():
    errs = validate_order_request(_req(
        order_type="STOP", trigger_price=970.0, trigger_above=False,
    ))
    assert errs == []


def test_stop_order_missing_trigger_price():
    errs = validate_order_request(_req(order_type="STOP", trigger_above=False))
    codes = [e.code for e in errs]
    assert "missing_trigger_price" in codes


def test_stop_order_missing_trigger_above():
    errs = validate_order_request(_req(order_type="STOP", trigger_price=970.0))
    codes = [e.code for e in errs]
    assert "missing_trigger_above" in codes


def test_stop_order_zero_trigger_price():
    errs = validate_order_request(_req(
        order_type="STOP", trigger_price=0, trigger_above=False,
    ))
    codes = [e.code for e in errs]
    assert "missing_trigger_price" in codes


def test_stop_order_non_bool_trigger_above():
    errs = validate_order_request(_req(
        order_type="STOP", trigger_price=970.0, trigger_above=1,
    ))
    codes = [e.code for e in errs]
    assert "missing_trigger_above" in codes


# --- STOP_LIMIT order ---

def test_stop_limit_order_valid():
    errs = validate_order_request(_req(
        order_type="STOP_LIMIT", intended_price=965.0,
        trigger_price=970.0, trigger_above=False,
    ))
    assert errs == []


# --- Other ---

def test_invalid_order_type_rejected():
    errs = validate_order_request(_req(order_type="OCO"))
    codes = [e.code for e in errs]
    assert "invalid_order_type" in codes


def test_zero_qty_rejected():
    errs = validate_order_request(_req(qty=0))
    codes = [e.code for e in errs]
    assert "invalid_qty" in codes


def test_negative_intended_price_rejected():
    errs = validate_order_request(_req(intended_price=-1.0))
    codes = [e.code for e in errs]
    assert "invalid_intended_price" in codes


def test_market_zero_intended_price_allowed():
    """MARKET で intended_price=0 は kabu の運用上 OK (Price=0 は成行)。"""
    errs = validate_order_request(_req(order_type="MARKET", intended_price=0))
    assert errs == []

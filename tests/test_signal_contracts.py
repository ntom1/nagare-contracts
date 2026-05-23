from dataclasses import asdict

from nagare_contracts import SignalDecision, SignalOutput, SignalRequest
from nagare_contracts import ops_shared


def test_signal_request_contract_is_serializable():
    request = SignalRequest(
        date="2026-05-20",
        strategy_version="BT-010",
        config_hash="bt010-hypc-sl3-pos2-vol300k",
        capital=506100,
        current_positions=["3382"],
        max_positions=2,
    )

    payload = asdict(request)

    assert payload == {
        "date": "2026-05-20",
        "strategy_version": "BT-010",
        "config_hash": "bt010-hypc-sl3-pos2-vol300k",
        "capital": 506100,
        "current_positions": ["3382"],
        "max_positions": 2,
    }


def test_signal_output_allows_pre_persistence_signal_id():
    output = SignalOutput(
        ticker="1568",
        side="BUY",
        intended_price=845.2,
        qty=100,
        strategy_version="BT-010",
        config_hash="bt010-hypc-sl3-pos2-vol300k",
        score=1.0,
        filters_applied={"entry_quality": True},
    )

    assert output.signal_id is None
    assert asdict(output)["filters_applied"] == {"entry_quality": True}


def test_signal_decision_contract_is_serializable():
    decision = SignalDecision(
        ticker="1568",
        decision="rejected",
        side="BUY",
        rejection_reason_code="position_cap",
        filter_stage=30,
        candidate_rank=3,
        score=0.42,
        blocked_by_cap=True,
        metadata={"source": "ronin.signal"},
    )

    assert asdict(decision) == {
        "ticker": "1568",
        "decision": "rejected",
        "side": "BUY",
        "rejection_reason_code": "position_cap",
        "filter_stage": 30,
        "candidate_rank": 3,
        "score": 0.42,
        "blocked_by_cap": True,
        "metadata": {"source": "ronin.signal"},
    }


class _Cursor:
    rowcount = 1

    def __init__(self):
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params):
        self.calls.append((sql, params))


class _Conn:
    def __init__(self):
        self.cursor_obj = _Cursor()
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_ops_shared_uses_configured_connection_provider():
    conn = _Conn()
    ops_shared.configure_connection_provider(lambda: conn)

    assert ops_shared.record_heartbeat("unit", "OK", "checked", {"x": 1}) is True

    assert conn.committed is True
    assert conn.closed is True
    sql, params = conn.cursor_obj.calls[0]
    assert "INSERT INTO system_heartbeats" in sql
    assert params[:4] == ("unit", "OK", "checked", '{"x": 1}')

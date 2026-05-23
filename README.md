# nagare-contracts

`nagare-contracts` は、Nagare 系システムの各リポジトリで共有する Python 契約パッケージです。

対象コンポーネント:

- `jcdd`: 市場データ・企業データ基盤
- `nagare`: 監視、ダッシュボード、ガバナンス、ペーパートレード
- `ronin`: 戦略、シグナル生成、承認ゲート、注文意図生成
- `torii`: ブローカー接続、注文実行、リコンシリエーション、フェイルセーフ

このリポジトリは実行アプリケーションではありません。DB 接続、ブローカー API 呼び出し、ダッシュボード表示、バッチ実行は各利用側リポジトリの責務です。

## 目的

各リポジトリ間で共有する型、状態定数、実行前提、バリデーションを一箇所に集約し、契約 drift を防ぎます。

主な契約:

- `SignalRequest`: `ronin` のシグナル生成へ渡す入力条件
- `SignalOutput`: `ronin` が生成し、DB / `nagare` 側の保存処理へ渡すシグナル出力
- `OrderIntent`: `ronin` から `torii` へ渡す承認済み注文意図
- `ExecutionReport`: `torii` から DB 経由で `nagare` / `ronin` へ戻す実行結果
- `Broker`: broker-agnostic な注文・口座・建玉操作 Protocol
- `Heartbeat`: 各コンポーネントの liveness 報告
- `StatusChangeEvent`: lifecycle / gate / readiness の監査可能な状態変更イベント
- `validate_status_change()`: 状態変更イベントの deterministic validation
- `ops_shared`: heartbeat / halt / override の共有 DB write helper
- execution constants: `SLIPPAGE_PCT`, `LIQUIDITY_TIERS` などの実行前提

## インストール

ローカル開発では、各リポジトリから editable install します。

```bash
pip install -e ../nagare-contracts
```

Python は `3.11` 以上を前提にしています。外部依存はありません。

## モジュール構成

| ファイル | 内容 |
| --- | --- |
| `nagare_contracts/broker.py` | `Broker` Protocol、`OrderRequest`、`OrderResult`、`Quote`、`Position`、口座・照合系 dataclass |
| `nagare_contracts/orders.py` | `SignalRequest`、`SignalOutput`、`OrderIntent`、`ExecutionReport`、`EXECUTION_STATUSES` |
| `nagare_contracts/heartbeat.py` | `Heartbeat`、`HEARTBEAT_STATUSES` |
| `nagare_contracts/states.py` | order / signal / proposal / status-change の状態定数と `StatusChangeEvent` |
| `nagare_contracts/validation.py` | `validate_status_change()` と `ValidationError` |
| `nagare_contracts/execution.py` | slippage、commission、liquidity tier などの実行前提定数 |
| `nagare_contracts/ops_shared.py` | heartbeat / halt / override の共有 DB write helper。DB connection provider は利用側が設定 |
| `nagare_contracts/__init__.py` | 利用側向け re-export |

## 使用例

### SignalRequest / SignalOutput

```python
from nagare_contracts import SignalOutput, SignalRequest

request = SignalRequest(
    date="2026-05-20",
    strategy_version="BT-010",
    config_hash="bt010-hypc-sl3-pos2-vol300k",
    capital=506100,
    current_positions=[],
    max_positions=2,
)

output = SignalOutput(
    ticker="1568",
    side="BUY",
    intended_price=845.2,
    qty=100,
    strategy_version=request.strategy_version,
    config_hash=request.config_hash,
)
```

### OrderIntent

```python
from nagare_contracts import OrderIntent

intent = OrderIntent(
    intent_id="INT-2026-03-10-001",
    signal_id="SIG-2026-03-10-001",
    ticker="1301",
    side="BUY",
    qty=100,
    intended_price=1500.0,
    strategy_version="BT-010",
    config_hash="bt010-hypc-sl3-pos2-vol300k",
)
```

### StatusChangeEvent validation

```python
from nagare_contracts import StatusChangeEvent, validate_status_change

event = StatusChangeEvent(
    field="lifecycle_stage",
    from_value="Paper Trading",
    to_value="Gate Passed",
    reason_code="gate-review",
    evidence="30+ trades, 6/6 criteria PASS",
    timestamp="2026-04-15T10:00:00+09:00",
    actor="ronin_gate",
    source_component="ronin",
)

errors = validate_status_change(event.to_validation_dict())
assert errors == []
```

## StatusChangeEvent のルール

`validate_status_change()` は、同じ入力に対して常に同じ error set を返します。

必須フィールド:

- `field`
- `from`
- `to`
- `reason_code`
- `evidence`
- `timestamp`
- `actor`
- `source_component`

`timestamp` は JST 固定の ISO 8601 形式です。

```text
YYYY-MM-DDTHH:MM:SS+09:00
```

`unknown`、`other`、`N/A`、空文字のような逃げ値は allowed values に入れません。未定義の値が必要になった場合は、利用前に `states.py` の enum を拡張し、テストを追加します。

## 開発・検証

```bash
pytest -q
```

現在のテストは主に `validate_status_change()` の precedence と allowed values を検証します。

CI でも `pytest -q` を実行します。共有契約を変更する場合は、利用側リポジトリの contract smoke test も合わせて確認してください。

## 変更時の注意

- 公開 API を削除・リネームする場合は、`nagare` / `ronin` / `torii` / `jcdd` の利用状況を先に確認すること
- 状態定数を追加する場合は、validator とテストも同時に更新すること
- `OrderResult.reject_reason` は後方互換のため残しています。新規実装では `error: BrokerError | None` を優先すること
- broker 固有の実装、DB 書き込み、UI 表示はこのリポジトリに置かないこと

<!--
このテンプレートは ~/Development/agent-rules/templates/PULL_REQUEST_TEMPLATE.md
が正本。各 repo の .github/PULL_REQUEST_TEMPLATE.md は install-repo-rule-files.sh が
このファイルからコピーする (差分は repo 側で持たない)。
-->

## Summary

<!-- 何を / なぜ。1〜3 文 + 必要なら箇条書き。 -->

## Test plan

<!-- 動作確認の TODO。チェックして merge。 -->

- [ ] `npm run typecheck` (該当 repo のコマンドで読み替え)
- [ ] `npm run lint` (該当 repo のコマンドで読み替え)
- [ ] `npm test` (該当 repo のコマンドで読み替え)
- [ ] ローカルで動作確認した

## Docs sync (Definition of Done)

<!--
コードを変えたらドキュメントも揃えるのがこの repo の運用ルール。
当てはまるものは更新済みにチェック、当てはまらなければ「N/A」と書く。
-->

- [ ] `README.md` の該当箇所を更新した
- [ ] `.env.example` / `.env.production.example` を更新した (env 追加・変更時)
- [ ] HOSTING / DEPLOY / RUNBOOK 系 docs を更新した (本番影響時)
- [ ] `tests/` を追加・更新した (parser / pure logic / API 変更時)
- [ ] `AGENTS.md` / `CLAUDE.md` に repo 固有の運用変更があれば反映した

## 影響範囲 / 注意

<!-- breaking change / migration / 新規 env / 外部サービス変更 など。なければ削除可。 -->

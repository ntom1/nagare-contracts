# nagare-contracts エージェント運用ルール

<!-- agent-rules:shared-rule-start -->
## 上位ルール参照

このrepoでは、まず上位の共通ルールを必ず適用する。
共通ルールは長く複製せず、作業内容に応じて必要な詳細だけ参照すること。

- Codex向け共通ルール: `~/Development/AGENTS.md`
- Claude Code向け共通ルール: `~/Development/CLAUDE.md`
- Skill原本管理: `~/Development/agent-skills/`

共通ルールとこのrepo固有ルールが矛盾する場合は、より上位の共通ルールを優先すること。
このファイルには、共通ルールを複製せず、このrepo固有の差分だけを書くこと。

Skillを作成・更新する場合は、`~/.agents/skills/` や `~/.claude/skills/` を直接編集せず、必ず `~/Development/agent-skills/skills-src/<skill-name>/SKILL.md` を原本とすること。
Markdownは、ユーザーから明示的な指定がない限り日本語で作成・更新すること。
<!-- agent-rules:shared-rule-end -->

## このrepo固有ルール

- 目的: TODO: このrepoの目的を確認する。
- 起動方法: TODO: 起動コマンドを確認する。
- 検証コマンド: TODO: テスト・lint・typecheckなどの確認コマンドを確認する。
- 触ってはいけないファイル/ディレクトリ: TODO: 予約領域や生成物を確認する。
- GitHubへpushする前の確認事項: TODO: このrepo固有の確認事項を確認する。

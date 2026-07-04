# nagare-contracts Claude Code 運用ルール

<!-- agent-rules:shared-rule-start -->
## 上位ルール参照

Claude Codeでこのrepoを扱う場合も、Codexと同じ共通ルールを必ず適用する。
共通ルールは長く複製せず、作業内容に応じて必要な詳細だけ参照すること。

- Claude Code向け共通ルール: `~/Development/CLAUDE.md`
- Codex向け共通ルール: `~/Development/AGENTS.md`
- このrepoのCodex向け固有ルール: `AGENTS.md`
- Skill原本管理: `~/Development/agent-skills/`

このファイルはClaude Code向けの入口として扱う。
repo固有の詳細ルールは原則として `AGENTS.md` に集約し、このファイルでは重複コピーしないこと。

Skillを作成・更新する場合は、`~/.agents/skills/` や `~/.claude/skills/` を直接編集せず、必ず `~/Development/agent-skills/skills-src/<skill-name>/SKILL.md` を原本とすること。
Markdownは、ユーザーから明示的な指定がない限り日本語で作成・更新すること。
<!-- agent-rules:shared-rule-end -->


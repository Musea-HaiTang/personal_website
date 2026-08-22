# AGENTS.md

## Agent skills

### Issue tracker

Issues and specs for this repo live as GitHub issues; use the `gh` CLI for all operations. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: read `CONTEXT.md` at the repo root and `docs/adr/` when exploring; proceed silently if absent. See `docs/agents/domain.md`.

## 工程工作流

新功能 / 修复按标准工作流执行，完整流程、技能清单与审查纪律见 `docs/agents/workflow.md`。

- 流程技能默认不自动触发（`grill-me`、`to-spec`、`to-tickets`、`setup-matt-pocock-skills` 需显式点名）；`code-review` 在用户要求 review 时自动使用。
- 审查只读：Standards / Spec 子代理只返回报告，禁止修改文件、git/gh 操作与派生子代理。
- AI 提交必须过隐私检查：禁止默认 `git add .` / `git add -A`；commit/push 前先核对暂存文件，扫描 `.env`、`backend/data/`、API key/token/私钥、个人数据等，发现可疑项立即停止并报告。检查细则见 `docs/agents/workflow.md`。
- 收尾（plan.md 同步、提交、关闭 issue）只由主代理执行。
- 新对话里直接说「处理 #n」或「按工作流做 #n」即可，agent 按本流程执行并调用对应技能。

# AGENTS.md

## Agent skills

### Issue tracker

Issues and specs for this repo live as GitHub issues; use the `gh` CLI for all operations. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: read `CONTEXT.md` at the repo root and `docs/adr/` when exploring; proceed silently if absent. See `docs/agents/domain.md`.

## 工程工作流

新功能 / 修复按 `plan.md` 第 7 节执行。流程技能需要显式点名才会运行（`grill-me`、`to-spec`、`to-tickets`、`setup-matt-pocock-skills` 均禁用了自动触发）；`code-review` 在用户要求 review 时自动使用。

- 需求未定：先 `grill-me` 访谈；UI 需求先 `prototype` 出 `design-mockups/` 原型，定稿后回写 plan.md / SPEC。
- 需求定稿：`to-spec` 发布 SPEC（GitHub issue），`to-tickets` 拆纵向切片 ticket（标注 Blocked by）。
- 实现：按 frontier 顺序，一个 issue 一个 commit（commit 消息引用 issue 号）。
- 收尾：`code-review` 双轴审查，通过后关闭 issue，并同步更新 plan.md。

新对话里直接说「处理 #n」或「按工作流做 #n」即可，agent 按本流程执行并调用对应技能。

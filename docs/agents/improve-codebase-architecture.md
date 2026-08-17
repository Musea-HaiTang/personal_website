# 技能记录：/improve-codebase-architecture（架构体检与深化）

> 记录日期：2026-08-17。本文件只记录技能事实与拟接入方案；是否安装、何时执行由用户决定。

## 来源

- 上游仓库：`mattpocock/skills`，路径 `skills/engineering/improve-codebase-architecture/`
- 拟锁定 commit：`068b6e0c62393147daf03530149cdce209c93da8`
- 触发方式：仅用户显式点名（SKILL.md 声明 `disable-model-invocation: true`，agent 不会自动跑）

## 用途（业务语言）

把代码库拆成一个个"盒子"，找出"接口和实现一样复杂"的浅盒子（shallow module），
给出把浅盒子变深盒子的改造候选，配可视化 HTML 报告，然后和用户逐项确认怎么改。
目标是让代码更好测试、更好被 agent 导航。作者建议每个项目每隔几天跑一次，作为"体检"而非"救援"。

## 依赖技能（需一并安装才能完整运行）

| 技能 | 角色 |
| --- | --- |
| `codebase-design` | 架构词汇：module / interface / depth / seam / adapter / leverage / locality，deep module 设计纪律 |
| `domain-modeling` | 边讨论边维护 `CONTEXT.md` 与 `docs/adr/`，术语模糊时创建/更新 |
| `grilling` | 决策树访谈原语，用户选中候选后走访谈 |

## 工作方式

1. **Explore**：先定范围再扫描（YAGNI）——用户点名方向就用方向，否则看最近 ~20 条 commit 找热点；派一个只读子代理逛代码库，记录摩擦点。
2. **HTML 报告**：写进系统临时目录（`%TEMP%/architecture-review-<时间戳>.html`），不落仓库；Tailwind/Mermaid CDN 排版；每个候选有文件、问题、方案、收益、前后对比图、推荐强度徽章；结尾给 Top 推荐。
3. **Grilling 循环**：用户选候选后逐项确认约束/依赖/模块形态/测试存活；过程中命名了新领域概念就更新 `CONTEXT.md`，用户以长期有效理由否掉候选时提议记 ADR。

## 拟接入流程（待用户确认后执行）

| 触发场景 | 流程 |
| --- | --- |
| 架构改进 / 重构需求 | `/improve-codebase-architecture` → CONTEXT/ADR 固化 → `/to-spec` → `/to-tickets` → 实现 → `/code-review` |
| 可选：每完成一批功能后体检 | 范围受限扫描（近期热点），候选进 issue 队列，不必当场全改 |

定位：标准工作流第 1 步"访谈"的架构变体，产物直接接现有 to-spec / to-tickets 管线。

## 纪律对齐（本仓库特有约束）

- 子代理只读探索、只回报发现；HTML 报告与 CONTEXT/ADR 写入只由主代理执行（遵守"子代理永远不是执行者"）。
- 报告只进 `%TEMP%`，不进仓库。
- 候选被否且理由有长期价值时提议记 ADR（与 `docs/agents/domain.md` 的 ADR 冲突提示约定一致）。
- 现实注意：报告依赖 Tailwind/Mermaid CDN，国内网络可能加载慢，必要时降级为内联样式；一次体检限一个方向以控制 token。

## 决策待定

- [ ] 安装方式：直接复制（锁 commit） vs `npx skills add`（跟最新）
- [ ] 是否同步安装依赖三件套（codebase-design / domain-modeling / grilling）
- [ ] 是否把 `docs/agents/workflow.md` 技能表与标准流程接入点补上
- [ ] `CONTEXT.md` / `docs/adr/` 按约定由该技能首次运行时惰性创建，不预先建

## 关联候选技能（2026-08-17 盘点，待选）

见工作流讨论结论；核心候选：`grill-with-docs`、`implement`、`tdd`、`diagnosing-bugs`、`ask-matt`。

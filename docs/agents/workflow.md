# 工程工作流（可复用模板）

> 一套从需求到落地的标准流程，适用于新项目/新功能。复制本文件到新仓库的 `docs/agents/workflow.md`（或项目约定位置），按仓库实际情况调整后启用。
>
> 配套文档：`docs/agents/issue-tracker.md`（issue 操作约定）、`docs/agents/domain.md`（领域上下文约定）、`docs/agents/improve-codebase-architecture.md`（架构体检技能记录）、根目录 `AGENTS.md`（agent 行为规则）。

## 0. 总原则

1. 需求未定先访谈（仓库内用 `/grill-with-docs`，边谈边沉淀 `CONTEXT.md` / ADR），UI 类需求先出原型，需求定稿后才拆票实现。
2. 一个 issue 一个 commit，commit 消息引用 issue 号；docs 类同步单独 commit。
3. 审查是只读阶段；收尾动作只由主代理执行；子代理永远不是执行者。
4. 每阶段完成并验证后再进入下一阶段；plan.md / SPEC / CONTEXT.md 与代码保持同步。
5. 阶段完成后用业务语言说明该阶段的作用与收益。

## 1. 技能清单

| 技能 | 用途 | 触发方式 |
| --- | --- | --- |
| `/setup-matt-pocock-skills` | 初始化仓库配置（issue tracker、domain docs 布局） | 配置缺失时由 agent 自动补跑（无需用户手动执行） |
| `/ask-matt` | 技能路由器：按当前情况选择流程路径 | 不确定走哪条流时显式调用 |
| `/grill-with-docs` | 需求访谈 + 同步沉淀 `CONTEXT.md` / ADR（仓库内首选） | 需求未定时显式调用 |
| `/grill-me` | 无仓库场景的纯访谈（不落文档） | 不在工作目录时显式调用 |
| `/prototype` | UI 原型（`design-mockups/`） | UI 类需求显式调用 |
| `/to-spec` | 发布 SPEC issue，打 `ready-for-agent` 标签 | 需求定稿后显式调用 |
| `/to-tickets` | 拆纵向切片 ticket，标注 `Blocked by` | SPEC 发布后显式调用 |
| `/implement` | 按 SPEC / ticket 实现：内部驱动 `/tdd`，收尾 `/code-review` 后提交 | 实现阶段按 ticket 显式调用 |
| `/tdd` | 红-绿-重构测试驱动开发 | 模型自动触发；`/implement` 内部使用 |
| `/diagnosing-bugs` | 硬 bug / 性能回退纪律排查：先造可复现回路再假设 | 模型自动触发；硬 bug 建议显式点名 |
| `/improve-codebase-architecture` | 架构体检：扫深化机会出 HTML 报告，再访谈选定候选 | 架构/重构需求显式调用；可选定期体检 |
| `/code-review` | 双轴审查（Standards / Spec） | 用户要求 review 或进入收尾时自动使用 |
| `/codebase-design` | 深模块设计词汇（module / interface / depth / seam / adapter / leverage / locality） | 模型自动触发（词汇层，被上层技能调用） |
| `/domain-modeling` | 维护 `CONTEXT.md` 术语与 ADR | 模型自动触发（词汇层，被访谈/架构技能调用） |
| `/grilling` | 决策树访谈原语 | 模型自动触发（被 grill-with-docs / improve-codebase-architecture 等调用） |

技能默认不自动触发（除非仓库 AGENTS.md 另有规定）；user-invoked 技能需显式点名，model-invoked 技能在任务匹配时自动可用。

## 2. 标准流程

1. **访谈** `/grill-with-docs`：把想法问清楚、确定方案，边谈边把术语写进 `CONTEXT.md`、把难决策写成 ADR；多方案时呈现取舍，不静默选择。不在仓库内的场景（纯写作/计划）用 `/grill-me`。
2. **原型** `/prototype`：UI 类需求先做可丢弃的 HTML 原型变体（放 `design-mockups/`）供选择与迭代；定稿后把决策固化进 plan.md / SPEC。
3. **规格** `/to-spec`：把已确认需求写成 SPEC，发布为 GitHub issue，打 `ready-for-agent` 标签。
4. **拆票** `/to-tickets`：把 SPEC 拆成 tracer-bullet 纵向切片 issue，每个 issue 写明 `Blocked by` 依赖。
5. **实现**：按 frontier 顺序用 `/implement` 逐个处理没有未完成阻塞依赖的 issue——内部驱动 `/tdd`（在约定接缝处红-绿-重构）、经常跑类型检查与单测、结束前跑全量测试，再 `/code-review` 通过后提交；一个 issue 一个 commit（消息引用 issue 号）。实现后自验：接口/页面冒烟，并清理冒烟数据。
6. **审查** `/code-review`（只读阶段）：
   - Standards 与 Spec 两个并行子代理各返回报告；审查固定点为实现 commit 的父提交，范围 `git diff <fixed-point>...HEAD`。
   - 子代理只读：禁止修改文件、禁止 git/gh 操作、禁止派生子代理、禁止执行任何收尾步骤，只返回报告。
   - 子代理上下文最小化（优先 `fork_turns="none"`）；派发后先确认收到任务正文；未确认、越权或递归派生立即中断，降级为主代理直接执行该轴并在报告中注明。
   - **降级规则（按观测触发，不绑定机器）**：子代理可用性随运行环境而异；同一阶段内连续两次失败（任务正文未送达、无响应/无确认、越权写入、递归派生等）即停止重试，默认降级为主代理直审——两轴由主代理分别执行并分开报告，报告中注明降级原因；更换环境（如另一台电脑）后可重新尝试子代理。
   - 主代理汇总两轴报告；问题先修复并补测试，再重新审查或说明不修理由。
7. **收尾**（仅主代理执行）：
   - 审查通过后同步 plan.md（阶段记录、验收清单、当前进度）。
   - docs commit（引用 issue 号）→ 推送 → 关闭 issue，附验收评论（实现内容、验证结果、审查结论）。
8. **整体验收**：按验收清单完整跑一遍，确认 plan.md 为最终交付状态。

**Bug / 性能问题**：小 bug（一眼能定位、改一行就好的）直接修，跑相关测试/冒烟确认即可，不走完整循环。只有硬 bug（反复修不好、偶发 flake、版本间回归、原因藏在多层调用链里）才走 `/diagnosing-bugs` 完整纪律循环——先造能复现该 bug 的最小反馈回路（测试/脚本/抓包，回路不红不进入假设阶段）→ 复现并最小化 → 列出 3-5 个可证伪假设 → 逐个验证 → 修复并补回归测试 → 清理临时产物。若发现"没有合适接缝能锁住这个 bug"，把该发现作为候选交给 `/improve-codebase-architecture`。

**架构改进 / 重构需求**：先跑 `/improve-codebase-architecture`：扫描（用户点名方向优先，否则聚焦近期热点）→ 生成 HTML 报告（临时目录，不入仓库）→ 用户选候选 → 决策树访谈 → 边谈边更新 `CONTEXT.md` / ADR。选定方向后再进入上面的标准流程（to-spec → to-tickets → implement）。可选：每完成一批功能后做一次范围受限体检。

**上下文卫生**：访谈 → 规格 → 拆票尽量在同一上下文窗口内连续完成，避免中途压缩丢思考；每个 `/implement` 可从 ticket 开新上下文，ticket 自包含即可。

## 3. 纪律

- 子代理永远不是执行者：所有写入（代码、plan.md、git、gh）只由主代理在用户授权范围内执行；`improve-codebase-architecture` 的探索子代理只读汇报，HTML 报告与 CONTEXT/ADR 写入由主代理完成。
- 审查与收尾分离：收尾动作不得发生在审查通过之前，也不得由审查者代做。
- 验收证据留痕：测试项数、构建结果、冒烟流程与数据清理情况写入 issue 评论与 plan.md。
- 冒烟数据必须清理：只删除本次创建的测试数据，不触碰真实数据。
- 遇阻及时上报：步骤长时间无进展（反复重试失败、疑似死循环、超时）立即停止并报告，不绕道假装完成。
- tdd 只在约定接缝按切片使用，不强制处处红-绿-重构；诊断必须先有"能复现该 bug"的回路再谈假设，禁止直接读码猜。
- 配置缺失自动补齐：仓库缺少 AGENTS.md / docs/agents 指引时，agent 先自动运行 `/setup-matt-pocock-skills` 再继续流程，无需用户手动操作。

## 4. 审查子代理任务模板

主代理派发审查子代理时固定携带：

```text
你是 {Standards|Spec} 轴审查员。只读任务：
1. 不得修改文件，不得执行 git/gh 操作，不得派生子代理；
2. 审查范围：git diff <fixed-point>...HEAD（commit 列表见下）；
3. spec 源：issue #N（正文见下）；
4. 输出：按报告要求逐条列出，<400 字；
5. 先回复确认已收到任务正文；未收到请直接说明，不要猜测。
```

## 5. 新项目落地清单

1. 复制本文件到新仓库 `docs/agents/workflow.md`。
2. 若发现仓库配置缺失（AGENTS.md / docs/agents 指引），agent 按工作流执行时自动补跑 `/setup-matt-pocock-skills`，无需用户手动操作。
3. 在根目录 `AGENTS.md` 引用本文件（「# Agent skills」或工作流小节）。
4. plan.md（若有）第 7 节指向本文件，不重复维护全文。
5. 按实际仓库调整：issue 编号、SPEC 文件、技能名称、测试/构建命令。
6. `CONTEXT.md` / `docs/adr/` 由 `/grill-with-docs`、`/domain-modeling` 等技能惰性创建，无需预先建。

落地示例（本仓库 personal_website）：

| 模板项 | 本仓库落地 |
| --- | --- |
| SPEC | SPEC.md + issue #1 |
| 切片 issue | #2–#8 |
| 流程文档 | docs/agents/workflow.md（本文件） |
| plan.md | 第 7 节引用本文件 |

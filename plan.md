# 个人网站开发计划

> 单用户个人网站，Vue 3 + FastAPI，本机免登录一键启动（`start.bat`）。
> 当前状态：**P0 五个核心模块已完成并通过验收（2026-08-16）**；**P1 学习模块已精简为笔记导入 + 只读 Markdown 阅读（2026-08-18）**；**P2 计划页增强（过往周浏览 + 统计 + 周总结）已完成（2026-08-28）**；**#26/#27 阅读弹窗大纲样式调整已完成（2026-08-29）**；**#34 笔记导入标题去重已完成（2026-08-29）**；**#35 阅读弹窗大纲恢复 H1 顶层项已完成（2026-08-29）**；**#36 笔记列表/阅读管线重构（列表不带正文、服务端搜索）已完成（2026-08-31）**；**#37/#38/#39 笔记阅读弹窗拆分为 render + outline、大纲改基于解析树已完成（2026-08-31）**；**#40/#41/#42 计划模块给「一周」建聚合模块、统一完成率口径已完成（2026-09-04）**。

## 1. 项目概述

一个日常自用的个人网站：任务计划、日记闪念、番茄专注、书签导航、笔记导入与阅读。结构化数据存 SQLite，日记/笔记正文落盘为 Markdown 文件；架构为后续桌宠、爬虫、小说阅读和公网登录预留扩展点。

## 2. 技术栈

- 前端：Vue 3.5 + Vite + Tailwind + Pinia + Vue Router + Axios，Markdown 预览用 markdown-it。
- 后端：FastAPI + SQLAlchemy 2.0 + SQLite + Pydantic v2。
- 测试：pytest + TestClient，只测 HTTP API 外部行为。
- Markdown 阅读：前端用 `markdown-it` 做只读渲染，不引入编辑器内核。

## 3. 架构设计

### 3.1 目录结构（当前）

```text
personal_website/
├── plan.md / SPEC.md / README.md / AGENTS.md
├── start.bat / setup.bat          # 一键启动 / 首次初始化
├── docs/agents/                   # 工作流、issue 约定、领域文档、架构体检记录
├── design-mockups/                # UI 原型（diary/learn/nav/pomodoro/plans）
├── backend/
│   ├── app/
│   │   ├── main.py / config.py / database.py
│   │   ├── models/                # tasks / diary / flash / notes / nav / pomodoro
│   │   ├── schemas/               # Pydantic 请求/响应模型
│   │   ├── routers/               # HTTP 层：参数与响应模型
│   │   └── services/              # 业务规则 / 文件仓库 / 搜索（tasks/diary/notes/favicon/tags/markdown_store/search/dashboard）
│   ├── tests/                     # pytest，独立 SQLite
│   ├── data/                      # SQLite + 日记/笔记 Markdown + favicon 缓存
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/ router/ stores/ utils/
    │   ├── views/                 # 六个页面（Home/Plans/Diary/Pomodoro/Notes/Nav）
    │   └── components/            # BaseModal / FloatingTimer + diary/nav/notes/plans 弹窗
    └── package.json / vite.config.js / tailwind.config.js
```

### 3.2 数据模型

| 表 | 用途 | 关键字段 |
| --- | --- | --- |
| `weekly_plans` | 本周计划 | 标题、重要度、备注、周起始日 |
| `subtasks` | 子任务 | 所属计划、名字、备注、重要度、完成状态、完成时间 |
| `tasks` | 今日任务 | 标题、日期、重要度、备注、完成状态、可关联计划与子任务、复盘原因 |
| `week_summaries` | 周总结 | 周起始日（唯一）、收获与反思、下周重点、更新时间 |
| `diary_entries` | 日记元数据 | 日期（唯一）、标题、标签、正文文件路径 |
| `flash_notes` | 闪念 | 内容、创建时间（按日聚合） |
| `notes` | 学习笔记 | 文件夹、标题、标签、文件路径、更新时间 |
| `note_folders` | 笔记分类 | 分类名、创建时间；允许先建空分类再导入 |
| `pomodoro_sessions` | 番茄记录 | 开始/结束时间、专注时长、可选绑定任务 |
| `nav_categories` / `nav_links` | 导航 | 名称、URL、描述、分类、置顶、排序 |

历史 SQLite 表 `note_chunks` / `note_index_jobs` / `questions` 保留但不迁移、不删除；所有当前表预留可空 `user_id` 字段，为未来公网登录留扩展点。

### 3.3 API 概览

| 模块 | 路由 | 说明 |
| --- | --- | --- |
| 健康检查 | `/api/health` | 前后端连通性 |
| 聚合首页 | `/api/dashboard` | 今日任务、今日专注统计、最近日记、置顶导航 |
| 计划 | `/api/plans`、`/api/subtasks`、`/api/tasks` | CRUD；按日期/周筛选；关联完成；顺延；周导出；近12周统计（`/api/plans/stats`）；周总结（`/api/plans/{week_start}/summary`） |
| 日记 | `/api/diary` | CRUD；按日期、标签、关键词搜索 |
| 闪念 | `/api/flash` | 新增/删除；按日期、关键词过滤 |
| 笔记 | `/api/notes` | 列表（含关键词搜索，只回元信息）/文件夹/新建/导入/删除；单篇读取返回全文 |
| 番茄钟 | `/api/pomodoro/sessions` | 创建会话、按日统计、可选绑定任务 |
| 导航 | `/api/nav/categories`、`/api/nav/links`、`/api/nav/favicons` | CRUD、置顶排序、favicon 本地缓存 |

### 3.4 前端 CSS 三层架构（约定）

- **第 0 层 令牌**：`frontend/src/style.css` 的 `:root` 一次性定义全部主题变量（纸色/墨绿/琥珀/字体），与 `tailwind.config.js` 同值，两处需同步维护。
- **第 1 层 公共组件类**：`@layer components` 统一维护 `.page`、`.card`/`.paper`、`.btn` 系列、`.tag`/`.tag-chip`、错误提示、弹窗遮罩、弹窗外壳、日记信纸头 `.head`；改样式只动这一处。
- **第 2 层 页面专属样式**：scoped `<style>` 只放页面独有视觉（信纸横线、便利贴、热力图、番茄圆环、导航磁贴等）。
- 新页面写法：Tailwind 工具类管布局 + 公共类管组件 + 小段 scoped 管装饰；颜色一律用主题变量，不写硬编码色值。

### 3.5 后端分层约定

- Router 只做 HTTP 参数与响应模型；业务规则（任务联动、顺延、周导出、笔记导入、聚合）收进各自 service。
- 文件读写统一走 `MarkdownStore`（`services/markdown_store.py`，日记/笔记各一个实例）；关键词搜索收在 `services/search.py` 接缝，调用方与具体实现解耦。
- 前端数据流：视图编排、Pinia store 管数据；弹窗拆独立组件，共享 `BaseModal` 与 `utils/highlight.js`。

## 4. 功能现状

### P0 核心模块（已完成）

| 模块 | issue | 完成时间 | 关键功能 |
| --- | --- | --- | --- |
| 项目骨架 | #2 | 2026-08-14/15 | FastAPI + SQLAlchemy + SQLite；Vite + Vue3 + Tailwind + Pinia；start.bat/setup.bat |
| 导航 | #3 | 2026-08-14/16 | 分类/链接 CRUD、置顶排序、即时搜索、书签墙改版、favicon 本地缓存 |
| 计划任务 | #4 | 2026-08-15 | 本周计划/子任务/今日任务、关联完成、复盘顺延、周导出、列宽拖拽 |
| 日记 | #5 | 2026-08-14/15 | Markdown 日记、标签/日期/关键词搜索、便利贴闪念、信纸弹窗、热力图与统计 |
| 番茄钟 | #6 | 2026-08-14/15 | 专注/休息双模式、时长编辑、全局小窗、绑定任务、今日统计 |
| 聚合首页 | #7 | 2026-08-16 | `/api/dashboard` 四块数据（任务/专注/日记/导航） |
| 整体验收 | #8 | 2026-08-16 | 一键启动、全流程冒烟、pytest 37 项、P0 交付完成 |

### P1 学习模块（已精简）

- **#18/#19 笔记精简（已完成）**：笔记只保留导入、列表和只读 Markdown 阅读；删除编辑、标签管理、问答、答题与向量索引入口；`markdown-it` 渲染 Typora 风格文章页。
- **#20–#25 笔记阅读弹窗 Typora Github 主题重构（已完成）**：阅读弹窗改为 Typora Github 主题（1440px 宽、白底、无衬线、蓝链、语法高亮、任务列表、GitHub 式表格）；左侧「大纲 / 文件」侧栏——大纲含标题项、可折叠、点击平滑跳转，文件页签同分类快速切换；26px 圆形侧栏开关（‹ / › 旋转 180°，0.3s 平滑过渡，收起后窗口尺寸不变）；阅读弹窗内删除键移除，删除入口移到列表页卡片。
- **#28 阅读弹窗 Typora 主题对齐（已完成）**：引用块渲染前归一化换行（CRLF→LF），避免 md 里连在一起的连续 `>` 行被 markdown-it 拆成多个独立引用块；大纲改为按 h1~h6 级别用栈建树（h1 顶层、h2 缩进、h3 更缩进）并支持任意深度折叠，与 Typora 大纲一致。
- 历史票：#12 笔记模块、#13 题库管理、#14 分块与向量索引已实现后被 #18/#19 精简取代；#15 RAG 问答、#16 答题判分、#17 答题统计不再进入 frontier。

### P2 计划页增强（已完成）

- **#31 过往周浏览（已完成）**：计划页页头加「‹ 上一周 / 下一周 ›」+ 周标签 +「回到本周」，默认本周；整个计划页（今日/本周计划/已完成/复盘）跟随所选周；过往周只读（隐藏新增/编辑/删除/顺延，标「历史周 · 只读」）；「已完成」页签跟随所选周。
- **#32 统计页签（已完成）**：新增 `GET /api/plans/stats?weeks=12`（近 12 周完成率/计划数/子任务数/任务数/每日完成计数）；`StatsPanel` 自绘 SVG 折线（完成率趋势）/ 分组柱（计划/子任务/今日任务）/ 热力图（列=周、行=周一~日，x 轴每周标日期）；「统计」页签为全局视图，不跟随周切换。
- **#33 周总结页签（已完成）**：新增 `week_summaries` 表 + `GET/PUT /api/plans/{week_start}/summary`；「周总结」页签跟随所选周，本周完成/未完成为自动派生只读清单，收获与反思/下周重点手动编辑按周落库，任何一周都能回顾并修改。

## 5. 验收清单

### P0（全部通过）

- [x] 一键启动后前后端同时可用。
- [x] 计划页：本周计划/子任务/今日任务、复盘顺延、周导出。
- [x] 日记页：Markdown 写、预览、搜索、编辑、删除；闪念便利贴。
- [x] 番茄钟：专注/休息计时、今日统计、绑定任务。
- [x] 导航页：分类/链接 CRUD、置顶、搜索、编辑、删除。
- [x] 聚合首页四块数据与各模块同步。
- [x] 后端 API 冒烟测试通过（pytest 全量通过）。
- [x] `npm run build` 通过。

### P1 学习模块（已精简）

- [x] #18/#19 笔记只保留导入 + 列表 + 只读 Markdown 阅读。
- [x] 编辑、问答、答题、向量索引入口已移除，历史表保留。
- [x] #20–#25 阅读弹窗 Github 主题、大纲/文件侧栏、收起沉浸阅读、列表页删除，均通过 `npm run build` 与 Edge 端到端冒烟。
- [x] #28 引用块连排、大纲按标题层级缩进，`npm run build` 通过。
- [x] 阅读弹窗样式微调：大纲默认折叠到章/去文件名、引用块合并连排、代码块行号与多语言高亮、笔记换行归一化，`npm run build` 通过。
- [x] #26/#27 阅读弹窗大纲样式调整：h1 保留加粗、h2/h3 正常，14/13/13px + 颜色分级，14px 步进缩进（h2=14px、h3=28px），`npm run build` 通过。
- [x] pytest 47 项通过，`npm run build` 通过，Edge 冒烟通过。

### P2 计划页增强

- [x] 计划页可翻到过去任意周；过往周只读（无新增/编辑/删除/顺延，标「历史周 · 只读」），本周可编辑。
- [x] 「已完成」「复盘」「今日执行」跟随所选周。
- [x] 统计页签：近 12 周完成率折线、每周任务数量分组柱、每日完成热力图正常渲染，x 轴每周标日期。
- [x] 周总结页签：本周完成/未完成自动派生只读清单；收获与反思/下周重点手动编辑且按周保存；历史周也能修改。
- [x] pytest 53 项通过；`npm run build` 通过；隐私检查通过。

## 6. 后续规划

- P2：网页版桌宠（纯前端）。
- P3：爬虫与小说阅读，只处理用户自有或已授权内容，遵守 robots 和限速。
- 公网阶段：Docker、nginx、HTTPS、单密码或完整账号体系，开启 `AUTH_ENABLED`。

## 7. 实施约定

- 代码改动后同步更新本文件，阶段完成后用业务语言说明作用。
- 时间统一按 `Asia/Shanghai` 存储和展示。
- 测试使用独立 SQLite 文件或临时目录，不污染真实数据。
- 每个阶段完成并验证后再进入下一阶段。
- 全站 UI 采用「纸感」主题：米色纸底、暖白卡片、细线边框、墨绿主色、衬线大标题；色板与字体按 3.4 节三层架构维护。
- 验证以最小必要为准：代码改动后至少 `npm run build` / pytest 全量通过，重要改动做冒烟并清理测试数据。

## 8. 工程工作流

标准流程、技能清单与审查纪律见 [docs/agents/workflow.md](docs/agents/workflow.md)。新功能/修复按该文档执行；架构重构需求先出方案并经确认后再实施。

## 9. 迭代记录

### 2026-09-04：#40/#41/#42 计划模块给「一周」建聚合模块（week.py）

- 背景：源自 2026-08-29 架构体检第 3 项。`tasks.py` 里对「一周」存在三套理解——`weekly_stats`（子任务+独立任务）、`_week_items`/`get_week_summary`（列计划子任务与当日任务）、`export_week_markdown`（只算子任务，完成率与统计不一致）；周范围计算被硬编码在多处（`current_week_start` / `_week_start_of` / 各处 `+6 天`），改「周」定义要动多处；导出还走 `plan.subtasks` 懒加载（N+1）。
- 改动：
  - 新增 `backend/app/services/week.py`：`week_start_of`（某日所在周一）+ `WeekAggregate`（dataclass，含 plans/subtasks/独立任务 + 派生 plan_count/subtask_count/task_count/done/total/completion_rate/daily_counts）+ `fetch_week`（批量取齐、按批取子任务，去 N+1）。
  - `tasks.py`：`weekly_stats` 逐周 `fetch_week` 组装 `WeeklyStatsOut`；`get_week_summary` / `export_week_markdown` 改为从 `fetch_week` 取数；移除 `current_week_start` / `_week_start_of` / `_week_items`。
  - 口径统一（已确认）：「一周」= 当周计划 + 计划子任务 + 独立任务（`subtask_id` 为空），子任务关联的当日任务由子任务代表不重复计；完成率 = (子任务完成+独立任务完成)/(子任务+独立任务)，统计/总结/导出一致。
  - CONTEXT.md 新增「计划与周（Tasks）」领域词条。
- 验证：后端 pytest 全量 **61 项通过**（新增 `test_week.py` 4 项 + `test_export_rate_consistent_with_stats` 回归）；隐私检查通过；双轴 review（Standards / Spec）由主代理直审（子代理空跑后中断，按流程回退），清理 import 位置与超长行后复查。
- 业务作用：周统计 / 周总结 / 周导出现在共用同一套取数与完成率，不再各算各的；周完成率口径一致（导出与统计不再打架）、导出不再 N+1、改「周」定义只需动一个模块，为后续加功能降低维护成本。

### 2026-08-31：#36 笔记列表/阅读管线重构（收拢搜索，列表不带正文）

- 背景：源自架构体检第 1 项。此前关键词匹配存在三处（后端 `search.matches` 服务笔记/日记 + 前端 `stores/notes.js` 的 `filtered` 重复实现）；`list_notes` 对每篇笔记读两遍文件（先匹配再组装）；列表接口把每篇完整正文返给前端，仅为喂给阅读弹窗。
- 改动：
  - 后端 `schemas/notes.py`：拆出 `NoteListItem`（id/folder/title/tags/updated_at，无正文）与 `NoteDetail`（含正文）；`ImportResult.created` 改用列表项。
  - `services/notes.py`：`list_notes` 只在有关键词时读文件做正文匹配，其余回元信息（零文件读取）；新增 `note_to_list_item`；`get_note`/`create_note` 返回 `NoteDetail`。
  - `routers/notes.py`：`GET /api/notes` 返回 `list[NoteListItem]`，`GET/POST /api/notes/{id}` 返回 `NoteDetail`。
  - 前端 `stores/notes.js`：删除 `filtered` 里的 substring 重复匹配，改为分类本地筛 + 关键词交给后端（`/notes?q=`），新增 `fetchNote(id)`。
  - `views/NotesView.vue`：列表卡片只显示标题（去掉摘要行）；点开时 `fetchNote(id)` 取详情传给弹窗；关键词输入加 300ms 防抖；分类页签仍为本地即时切换。
  - `components/notes/NoteReaderModal.vue`：`switchNote` 改为按 id 取详情全文再渲染。
- 验证：后端 pytest 全量 56 项通过；`npm run build` 通过；隐私检查通过（仅暂存 7 个目标文件，未含 `.env`/`backend/data/`/`dist`）。
- 业务作用：搜索规则只留服务端一份、改一处即生效；列表浏览不再触发文件读取、也不再传输整篇正文，点开阅读才按 id 取全文；列表更轻、更快。
- 状态：实现完成，待 code-review。

### 2026-08-31：#37/#38/#39 笔记阅读弹窗拆分为 render + outline、大纲改基于解析树

- 背景：源自架构体检第 2 项。阅读弹窗 `NoteReaderModal.vue`（763 行）一个 SFC 同时承担渲染（markdown-it）、13 语言高亮、行号、引用合并、大纲构建、h1→h2 降级、文件页/侧栏七种职责；大纲用 `querySelectorAll` 从已渲染 DOM 反查，导致大纲结构与导入/渲染逻辑隐形耦合（#34 改导入曾静默弄坏大纲 #35）。
- 改动：
  - 抽出 `frontend/src/components/notes/noteRender.js`：markdown-it 配置（13 语言高亮、行号、引用合并、taskLists）、标题 id 注入（slugify + 去重）、内容 h1→h2 降级；导出 `renderNote(content) → { html, headings }`，`headings` 从 token 解析树提取、不依赖 DOM。
  - 新增 `frontend/src/components/notes/noteOutline.js`：纯函数 `buildOutlineTree(title, headings) → 大纲树`，从解析树建层级。
  - `NoteReaderModal.vue` 退化为薄组合：删除 `buildOutline()` / `slugify` / `watch+nextTick+DOM` 重建；保留折叠/展开/跳转/扁平化；大纲、跳转锚点、h1→h2 降级同源一致。
- 验证：`npm run build` 通过；用 node 核验解析树提取（标题文本、id 去重、h1→h2 不影响大纲 level）与 `buildOutlineTree` 嵌套；双轴 code-review 通过（Standards 1 条判断项已加固；Spec 2 条小备注接受，浏览器冒烟保留人工验证）。隐私检查通过（仅暂存 notes 目录 3 个目标文件）。
- 业务作用：大纲不再依赖渲染 DOM，以后改导入/渲染逻辑不会静默弄坏大纲；大纲可脱离浏览器单测（为后续测试基建留缝）；弹窗大幅瘦身，渲染与大纲各归一位，阅读更稳、更好定位。

### 2026-08-29：#35 阅读弹窗大纲恢复 H1 顶层项

- 背景：#34 把正文首行 H1 提升为笔记标题并从正文移除后，阅读弹窗大纲里没有 H1 顶层项了，章节全部平铺、不再嵌套在文档标题下。
- 根因：`NoteReaderModal.vue` 的 `buildOutline()` 用 `h1:not(.note-title)` 收集正文标题，刻意排除 `.note-title`。以前文档标题是正文里的 `# H1` 会被收进大纲；#34 后标题只存在于 `note-title` 元素、被排除，于是大纲丢失顶层 H1。
- 改动：`buildOutline()` 把 `h1.note-title` 作为最顶层 H1 加进大纲（保留其固定 id），让后续 `##` 章节正确嵌套在它下面，并保持正文 h1 降级、折叠与跳转行为不变。
- 验证：`npm run build` 通过；用真实笔记内容模拟大纲建树确认 H1 顶层项与章节嵌套正确。
- 业务作用：大纲恢复“文档标题最顶 + 章节其下”的层级，长文定位更清晰。

### 2026-08-29：#34 导入时以正文 H1 为标题并去重

- 背景：笔记阅读弹窗顶部出现两个相同大标题（如 `python基础知识梳理`）。用户写笔记习惯用 H1 当文件名，后端导入又以文件名做标题、正文保留首行 H1，阅读页标题重复。
- 改动（`backend/app/services/notes.py`）：
  - 新增 `extract_note_title()`：取正文首行 H1 作为标题，并从正文移除该行与紧随的空行；首行不是 H1 时回退标题到文件名、正文保持不变。
  - `import_notes()`：标题改为来自正文 H1（不再派生自文件名），文件名沿用原上传文件名、仅在重名时自动改名；写入的正文已去掉重复 H1。
- 验证：pytest 全量 55 项通过（新增导入 H1 去重回归测试 + 无 H1 回退测试，并按新语义更新自动改名测试）；隐私检查通过。
- 业务作用：阅读页只显示一次标题（正文 H1），列表标题也更准确（H1 带副标题时展示完整标题）；导入的笔记不再出现"标题显示两次"。

### 2026-08-29：#26/#27 阅读弹窗大纲样式调整

- 背景：阅读弹窗左侧大纲此前层级偏重、不够清爽，希望更接近 Typora 的简洁大纲。
- 改动（`frontend/src/components/notes/NoteReaderModal.vue`）：
  - 大纲层级用字号 + 颜色分级：h1 14px `--gh-strong`（保留加粗，用于强调章级）、h2 13px `--gh-muted`、h3 13px `--gh-muted-2`；h2/h3 不加粗。
  - 缩进按层级 14px 步进：`.ol-row` 内联 `padding-left: (level-1)*14px`，h1 0 / h2 14px / h3 28px，箭头随层级缩进。
  - 保留折叠、点击跳转、hover 高亮行为。
- 验证：`npm run build` 通过；浏览器冒烟确认大纲视觉（层级字号/颜色、缩进、箭头、跳转）。
- 业务作用：大纲层级更清爽——章级用加粗 + 深色突出，小节靠字号与颜色递减，缩进随层级递增，长文定位更直观。

### 2026-08-28：计划页过往周浏览 + 统计页签 + 周总结

- 背景：计划页此前只展示本周，无法回看历史；缺少跨周统计；每周结束缺少可回顾/修改的总结。
- 改动：
  - 计划页页头加「‹ 上一周 / 下一周 ›」+ 周标签 +「回到本周」，整个计划页跟随所选周；过往周只读（隐藏新增/编辑/删除/顺延/重新打开，勾选不可点，标「历史周 · 只读」）；「已完成」页签跟随所选周（#31）。
  - 新增 `GET /api/plans/stats?weeks=12`（近 12 周完成率/计划数/子任务数/任务数/每日完成计数）；`StatsPanel` 自绘 SVG 折线/分组柱/热力图（无图表库，x 轴每周标日期）；新增「统计」页签（全局视图）（#32）。
  - 新增 `week_summaries` 表 + `GET/PUT /api/plans/{week_start}/summary`；`SummaryPanel` 周总结页签——本周完成/未完成自动派生只读清单，收获与反思/下周重点手动编辑按周落库，任何一周可回顾并修改（#33）。
- 验证：后端 pytest 全量 53 项通过（新增 stats + week_summaries 用例）；`npm run build` 通过；隐私检查通过；原型 `design-mockups/plans/plans-history.html` 定稿（gitignore，不入 main）。
- 业务作用：计划页现在能回看历史周、看到近 12 周的节奏（完成率/任务量/热力图），并可在每周写一份总结（完成/未完成自动带出，反思与下周重点自己写），过去任何一周都能再打开修改。

### 2026-08-24：阅读弹窗大纲折叠/引用连排、代码块行号与多语言高亮

- 背景：笔记正文用 `#`（章）/`##`（练习）书写，大纲默认全展开显得很长、且顶层带文件名根节点；md 中相邻 `>` 引用行之间的空行会被 markdown-it 拆成多个独立引用块；导入的 md 是 `\r\r\n`（Windows 下 `write_text` 对已含 `\r\n` 的内容二次转义造成），读回变成 `\n\n`，导致代码块/引用块每行之间多出空行、代码块也没有行号。
- 改动：
  - `NoteReaderModal.vue`：大纲根节点改为虚拟容器（不再渲染文件名），默认只展开 h1/h2、更深层级收起；渲染层把相邻 `<blockquote>` 合并成一整块；代码块按行拆分为 `.code-line` 并用 CSS 计数器显示行号（空行占号、结尾不多出空行号）；新增 `vue`(映射到 xml)、`powershell`、`markdown`、`yaml`、`scss` 高亮注册。
  - `markdown_store.py`：写入与读取统一规整换行（`\r\r\n`/`\r\n`/`\r` → `\n`），根因修复代码块/引用块被空行撑开。
- 验证：pytest 49 项通过（新增换行归一化回归测试：写入落盘 + 导入路径，#29）；`npm run build` 通过；行号与高亮渲染核验通过。
- 业务作用：大纲默认呈现「书名 + 章」的简洁目录、可逐层展开；连续引用与代码块不再被空行断开；代码带行号并支持常用语言高亮，阅读更贴近 Typora。

### 2026-08-22：#28 阅读弹窗 Typora 主题对齐

- 背景：笔记 md 为 CRLF，markdown-it 会把连续 `>` 引用行拆成多个独立引用块，视觉上"连接内容被断开"；大纲把正文 h1（章节）与 h2 压到同一层，章节层级丢失。
- 改动：`NoteReaderModal.vue`——渲染前归一化换行（CRLF→LF）保证引用块连排；大纲改为按 h1~h6 级别用栈建树 + 按层级缩进（h1 顶层、h2 缩进、h3 更缩进），大纲改为扁平列表 + 任意层级折叠；引用块 CSS 微调（区块内段落 margin/padding）。
- 验证：`npm run build` 通过；before/after 复刻确认引用块由"拆成多块"变为"合并连排"、大纲缩进与 Typora 一致；双轴 review（Standards/Spec 子代理派发触发递归后按降级规则由主代理直审）。
- 业务作用：阅读体验更贴近 Typora——md 里连在一起的引用不再被拆断，长文大纲按章节层级缩进、可折叠，跳转更清晰。

### 2026-08-19：#20–#25 笔记阅读弹窗 Typora Github 主题重构

- 原型 7 轮迭代定稿（`design-mockups/learn/reader-typora.html` C 变体 v7）：只改阅读弹窗；Github 主题；大纲可收起且窗口尺寸不变；标题作为大纲第一项；无子级标题不显示箭头；单枚圆形按钮 ‹ / › 旋转切换；列表页加删除、弹窗内删除移除；收起态不做文件切换入口。
- SPEC #20 定稿后拆 5 张票：#21 弹窗结构/Typora 排版、#22 大纲侧栏与侧栏开关、#23 语法高亮与任务列表、#24 文件页签同分类切换、#25 列表页删除入口。
- 实现：`NoteReaderModal.vue` 重写为 Typora Github 主题（Github 色板收敛为组件内 `--gh-*` 局部令牌，不污染全局主题）；大纲渲染后从 DOM 提取，正文 h1 与标题重复则去掉、其余降级为 h2 纳入大纲；highlight.js 按需注册 9 种常用语言；markdown-it-task-lists 任务列表；文件切换后停留在文件页签；列表卡片删除带二次确认。
- 验证：`npm run build` 通过；Edge 端到端冒烟（1440px 弹窗、大纲跳转/折叠、文件切换、收起展开、列表删除）通过，冒烟笔记已清理；pytest 46 项通过。双轴 review：Standards / Spec 子代理派发失败后由主代理直审（见 issue #20 评论），发现并修复"正文自带 h1 与标题重复"问题。
- 业务作用：笔记阅读从"小信纸弹窗"升级为接近 Typora 的宽屏阅读体验，长文有目录可跳转、同类笔记可快速切换，删除操作移到列表页更符合只读定位。

### 2026-08-18：#14 分块与向量索引

- 新增 `note_chunks` / `note_index_jobs` 与 `GET /api/notes/index/progress`；`chunker.py` 按 Markdown 标题和段落切块，长文本按 600 字切分并保留 50 字重叠；`embeddings.py` 用 zai-sdk 调 embedding-3（测试用 mock）。
- 创建/更新笔记后同步重建索引，删除时清理分块与状态；批量导入由后台 worker 排队建索引，进度接口返回 `total / done / chunk_count / pending / failed / running`；失败重试耗尽后标记 failed，笔记仍可正常浏览。
- 业务作用：笔记保存后自动变成可语义检索的知识块，后续问答可以直接按向量命中相关内容，不用每次全文扫描；批量导入时页面不会被索引过程卡住。
- 验证：pytest 61 项通过，`npm run build` 通过；真实 embedding-3 冒烟返回 2048 维向量；双轴 review 通过（Standards 硬违规已修复，Spec 通过）。

### 2026-08-18：#18/#19 笔记模块精简为导入 + 只读阅读

- 新增 `note_folders` 表与 `POST /api/notes/folders`，空分类会持久化；文件夹列表合并已有笔记分类和空分类。
- 导入弹窗展示已选文件名、支持拖拽；导入成功后自动关闭弹窗，并在笔记页显示导入结果。
- 笔记弹窗放大到最大 1024px，打开即只读 Markdown 文章，用 `markdown-it` 渲染 Typora 风格排版。
- 移除笔记编辑、标签管理、问答、答题、向量索引入口；历史 SQLite 表保留但不迁移、不删除。
- 验证：pytest 46 项通过，`npm run build` 通过，Edge 端到端冒烟通过，冒烟数据已清理。

### 2026-08-17：P1 学习模块启动 + 架构整理

- SPEC #11 定稿，票 #12–#17 入 frontier；#12 笔记模块、#13 题库管理已完成并通过双轴 review（pytest 53 项全量通过）。
- 架构整理 A：后端业务下沉 service（tags/tasks/diary/notes/quiz/dashboard），router 只留 HTTP 层。
- 架构整理 B：前端视图拆分——新增 `BaseModal` 与 `utils/highlight.js`，Plans/Nav/Diary/Notes 弹窗全部拆成独立组件，API 调用下沉 Pinia store。
- 架构整理 C：CSS 三层架构——全局主题令牌 + `@layer components` 公共类 + 页面专属 scoped；删除 7 个文件局部变量，把约 2,300 行自定义样式中重复的公共类收进全局层，番茄钟/计划页硬编码色值统一换变量（见 3.4 节）。
- 后端架构整理（C/D/E）：`MarkdownStore` 合并日记/笔记两套文件读写（删除 diary_files/note_files，消除重复）；新增 `services/search.py` 搜索接缝，日记/笔记列表检索改走 `matches()`，P1 向量检索在此替换；聚合去重复核完成（dashboard 复用 `task_to_out` 与 `tags.to_list`，无残留重复转换）。验证：pytest 53 项通过。

### 2026-08-16：P0 收尾

- 聚合首页 #7（`/api/dashboard` + HomeView 四张卡片）、导航页书签墙改版与 favicon 本地缓存（#3 收尾）、日记/导航 Pinia 缓存、往日记录详情与删除（#9/#10）、整体验收 #8（番茄绑定任务、一键启动、全流程冒烟），P0 交付完成。

### 2026-08-15：核心页面与视觉改版

- 计划页 #4、日记页改版 #5（便利贴闪念 + 信纸日记 + 图表）、番茄钟改版 #6（藤蔓圆环 + 全局小窗）、导航页改版 #3 定稿；浏览器批注迭代（信纸排版、番茄时长输入框、`ring-wrap` 类名修复）。

### 2026-08-14：骨架与后端

- 项目骨架 #2、后端数据层与五模块 API（#3–#6 后端部分）、四页初版（#3–#6）。

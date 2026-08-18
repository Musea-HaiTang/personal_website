# 个人网站开发计划

> 单用户个人网站，Vue 3 + FastAPI，本机免登录一键启动（`start.bat`）。
> 当前状态：**P0 五个核心模块已完成并通过验收（2026-08-16）**；**P1 学习模块已精简为笔记导入 + 只读 Markdown 阅读（2026-08-18）**。

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
| 计划 | `/api/plans`、`/api/subtasks`、`/api/tasks` | CRUD；按日期/周筛选；关联完成；顺延；周导出 |
| 日记 | `/api/diary` | CRUD；按日期、标签、关键词搜索 |
| 闪念 | `/api/flash` | 新增/删除；按日期、关键词过滤 |
| 笔记 | `/api/notes` | 列表/文件夹/新建/导入/删除；单篇读取 |
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
- 历史票：#12 笔记模块、#13 题库管理、#14 分块与向量索引已实现后被 #18/#19 精简取代；#15 RAG 问答、#16 答题判分、#17 答题统计不再进入 frontier。

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
- [x] pytest 46 项通过，`npm run build` 通过，Edge 冒烟通过。

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

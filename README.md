# 个人网站 Personal Website

单用户个人网站，把计划任务、Markdown 日记、番茄钟和网站导航集中到一个本地工具里，配一个聚合首页一屏掌握当天状态。P0 已交付完成，本机免登录、一键启动。

## 功能

- **聚合首页**：今日未完成任务、今日专注次数/时长、最近日记、置顶导航四块卡片，各模块改动后首页自动同步。
- **计划页**：本周计划 → 子任务 → 今日任务三层结构；重要度标注、任务与子任务完成联动、复盘顺延、本周计划 Markdown 导出。
- **日记页**：Markdown 写作与即时预览、标签管理、日期/标签/关键词搜索；便利贴闪念、写作热力图、每月字数、连续记录、去年今天回顾。
- **番茄钟**：专注/休息双模式、时长可调、暂停/继续/重置；可绑定计划任务，计时中右下角全局小窗显示，专注结束自动记录并更新今日统计。
- **导航页**：分类书签墙、置顶常用、即时搜索；favicon 由后端抓取一次并本地缓存，刷新快且不依赖第三方服务。
- **笔记页**：导入本地 Markdown 笔记，按文件夹和关键词查找，点开以 Typora 风格只读渲染正文。

## 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3.5、Vite、Tailwind CSS、Pinia、Vue Router、Axios、markdown-it |
| 后端 | FastAPI、SQLAlchemy 2.0、SQLite、Pydantic v2 |
| 测试 | pytest + TestClient（只测 HTTP API 外部行为） |

## 快速开始

环境要求：Python 3.12+、Node.js 18+（Windows）。

首次运行初始化依赖：

```bat
setup.bat
```

一键启动前后端：

```bat
start.bat
```

启动后会自动打开浏览器：

- 前端：http://localhost:5173
- 后端健康检查：http://127.0.0.1:8000/api/health

## 目录结构

```text
personal_website/
├── plan.md                  # 开发计划与进度
├── SPEC.md                  # P0 规格说明
├── AGENTS.md                # 仓库级 agent 指令
├── start.bat                # 一键启动前后端
├── setup.bat                # 首次初始化依赖
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置（时区、AUTH_ENABLED）
│   │   ├── database.py      # SQLite 初始化
│   │   ├── models/          # SQLAlchemy 模型
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── routers/         # API 路由
│   │   └── services/        # 业务逻辑（日记文件、favicon 缓存）
│   ├── tests/               # pytest 冒烟测试
│   ├── data/                # SQLite、Markdown 日记、favicon 缓存
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api/             # Axios 封装
    │   ├── router/          # 六个页面路由
    │   ├── stores/          # Pinia
    │   ├── views/           # 六个页面
    │   └── components/      # 全局小窗计时器等
    ├── package.json
    └── vite.config.js       # /api 代理到后端
```

## 数据存储

- 结构化数据：SQLite 数据库 `backend/data/app.db`。
- 日记正文：按日期命名的 Markdown 文件 `backend/data/diary/YYYY-MM-DD.md`，不依赖数据库，可直接查看和迁移。
- 导航图标：后端抓取一次后缓存到 `backend/data/favicons/`，TTL 7 天刷新。

数据表：`weekly_plans`（本周计划）、`subtasks`（子任务）、`tasks`（今日任务）、`diary_entries`（日记元数据）、`flash_notes`（闪念）、`notes`（笔记元数据）、`note_folders`（笔记分类）、`pomodoro_sessions`（番茄记录）、`nav_categories`（导航分类）、`nav_links`（导航链接）。所有当前表预留可空 `user_id` 字段，为未来公网登录留扩展点。

## API 概览

| 模块 | 路由 | 说明 |
| --- | --- | --- |
| 健康检查 | `GET /api/health` | 前后端连通性 |
| 聚合首页 | `GET /api/dashboard` | 今日任务、今日专注、最近日记、置顶导航 |
| 计划 | `/api/plans`、`/api/subtasks`、`/api/tasks` | 计划/子任务/今日任务 CRUD、按日筛选、顺延、周导出 |
| 日记 | `/api/diary` | CRUD、日期/标签/关键词搜索 |
| 闪念 | `/api/flash` | 新增、列表（可按日期/关键词过滤）、删除 |
| 笔记 | `/api/notes` | 列表/文件夹/新建/导入/删除、单篇读取 |
| 番茄钟 | `/api/pomodoro/sessions` | 创建会话记录（可选绑定任务）、按日统计 |
| 导航 | `/api/nav/categories`、`/api/nav/links`、`/api/nav/favicons` | 分类/链接 CRUD、favicon 缓存获取 |

## 测试与验证

```bat
cd backend
.venv\Scripts\python -m pytest
```

```bat
cd frontend
npm run build
```

P0 验收结果：后端全量 pytest 37 项通过，前端 `npm run build` 通过；一键启动、全流程冒烟（新建任务 → 绑定番茄 → 写日记 → 新增导航 → 首页四块同步）均验证通过。

## 设计与开发文档

- [SPEC.md](SPEC.md)：P0 规格说明（用户故事、实现决策、验收口径）。
- [plan.md](plan.md)：开发计划、阶段进度与迭代记录。
- [docs/agents/workflow.md](docs/agents/workflow.md)：工程工作流与审查纪律。

规格与实施拆解通过 GitHub issue 跟踪（仓库 `Musea-HaiTang/personal_website`）：SPEC 为 #1，实施 issue #2–#8 均已关闭并推送 `main`。

## 后续规划

- **P1**：笔记导入与只读 Markdown 阅读（已完成）。
- **P2**：网页版桌宠（纯前端）。
- **P3**：爬虫与小说阅读，只处理用户自有或已授权内容，遵守 robots 与限速。
- **公网阶段**：Docker、nginx、HTTPS、单密码或完整账号体系，开启 `AUTH_ENABLED`。

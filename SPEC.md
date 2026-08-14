# 个人网站 P0 规格说明

## Problem Statement

我目前没有一个统一的地方管理日常的个人信息：计划任务、日记、专注记录和常用网站收藏分散在各处，查找和统计都很麻烦。我还希望这个网站以后能扩展出学习笔记查询、技术答题、网页桌宠、爬虫和小说阅读等能力，所以需要一个可以长期演进、先在本机使用、以后能安全发布到公网的个人网站。

## Solution

用 Vue 3 + FastAPI 搭建一个单用户个人网站。第一版（P0）提供聚合首页、计划任务、Markdown 日记、番茄钟、网站导航五个页面；结构化数据存入 SQLite，日记正文以 Markdown 文件保存；本机免登录一键启动，架构上为后续模块和未来公网登录预留扩展点。

## User Stories

1. As 网站主人, I want 打开网站先看到聚合首页, so that 一眼看到今日任务、今日专注时长、最近日记和常用导航
2. As 网站主人, I want 在聚合首页看到今天未完成的任务, so that 不打开计划页也能知道今天要做什么
3. As 网站主人, I want 在聚合首页看到今日番茄钟次数和总时长, so that 快速了解今天的专注情况
4. As 网站主人, I want 在聚合首页看到最近几篇日记, so that 方便回顾和续写
5. As 网站主人, I want 在聚合首页看到置顶导航链接, so that 常用网站一键直达
6. As 网站主人, I want 新增计划任务时填写标题、日期、优先级和备注, so that 任务信息完整可检索
7. As 网站主人, I want 计划页按日期分组展示任务, so that 我能按天安排和查看
8. As 网站主人, I want 编辑已有任务, so that 日期或优先级变化时能及时修正
9. As 网站主人, I want 一键把任务标记为完成或重新打开, so that 状态维护成本最低
10. As 网站主人, I want 删除不再需要的任务, so that 列表保持干净
11. As 网站主人, I want 按日期筛选任务, so that 只看某一天的计划
12. As 网站主人, I want 为某一天创建日记, so that 每天的记录都归档在同一位置
13. As 网站主人, I want 用 Markdown 写日记并即时预览, so that 排版和内容编辑体验好
14. As 网站主人, I want 给日记添加一个或多个标签, so that 之后能按主题归类查找
15. As 网站主人, I want 按日期、标签和关键词搜索日记, so that 快速找回过去的记录
16. As 网站主人, I want 编辑和删除已有日记, so that 记录可以持续维护
17. As 网站主人, I want 日记正文以 YYYY-MM-DD.md 文件保存在本地, so that 内容不依赖数据库、可直接查看和迁移
18. As 网站主人, I want 一键开始番茄钟，默认专注 25 分钟, so that 进入专注不需要额外设置
19. As 网站主人, I want 调整专注和休息时长, so that 适应不同的工作节奏
20. As 网站主人, I want 暂停、继续、重置计时器, so that 临时打断也能正确处理
21. As 网站主人, I want 完成一个番茄后记录专注时长, so that 有历史数据可统计
22. As 网站主人, I want 番茄记录可选绑定一个计划任务, so that 能看到每个任务投入的时间
23. As 网站主人, I want 当天看到专注次数和总时长, so that 每天结束能复盘
24. As 网站主人, I want 创建和管理导航分类, so that 收藏按主题组织
25. As 网站主人, I want 添加导航链接并填写标题、URL、描述和分类, so that 常用网站有完整入口
26. As 网站主人, I want 编辑和删除导航链接与分类, so that 收藏随时保持准确
27. As 网站主人, I want 置顶最常用的导航链接, so that 高频网站排在最前
28. As 网站主人, I want 在导航页按关键词即时搜索, so that 收藏很多时也能快速找到
29. As 网站主人, I want 一键启动前后端服务, so that 本机使用不需要手动配置环境
30. As 网站主人, I want 后续导入学习笔记并全文检索, so that 学习资料能集中查询
31. As 网站主人, I want 后续对学习笔记提问并获得基于笔记的回答, so that 结合 DeepSeek 做知识问答
32. As 网站主人, I want 后续做技术学习答题并获得判分, so that 检验学习效果
33. As 网站主人, I want 后续有一个网页版桌宠, so that 使用网站时更有陪伴感
34. As 网站主人, I want 后续能阅读本地或已授权导入的小说, so that 阅读记录也能集中管理
35. As 网站主人, I want 后续把网站发布到公网时加上登录, so that 私人内容不会被别人看到

## Implementation Decisions

- 技术栈：前端 Vue 3.5 + Vite + Tailwind + Pinia + Vue Router + Axios，无第三方 UI 组件库，界面自绘；后端 FastAPI + SQLAlchemy 2.0 + SQLite + Pydantic v2；前端 Markdown 预览使用 markdown-it。
- 项目形态：单一 monorepo，前端和后端分目录，后端按 routers / services / schemas 分层，沿用既有 Novel2YAML 项目的组织风格。
- 页面与路由：聚合首页、计划页、日记页、番茄钟页、导航页，侧边栏导航，中文界面，桌面优先并做基础响应式。
- 数据库表：tasks（计划任务）、diary_entries（日记元数据）、pomodoro_sessions（番茄记录）、nav_categories（导航分类）、nav_links（导航链接）；所有表预留可空 user_id 字段。
- 日记存储：正文写为按日期命名的 Markdown 文件，日期、标题、标签等元数据写入 SQLite；关键词搜索在个人数据量级下直接扫描正文。
- API 合同：计划、日记、番茄钟、导航各提供独立的 CRUD 路由；番茄钟提供按日统计；提供聚合首页接口，返回今日任务、今日专注统计、最近日记和置顶导航。
- 模块联动：番茄记录可选绑定计划任务；日记按日期归档；导航模块独立；不做日历、目标拆解和完整统计报表。
- 鉴权：P0 免登录，保留 AUTH_ENABLED 配置开关；未来上公网时先加单密码或完整账号体系。
- 时间处理：统一按本地时区 Asia/Shanghai 存储和展示。
- 运行方式：提供一键启动脚本，同时启动后端 uvicorn 和前端 Vite 开发服务器；Docker、nginx、HTTPS 留到公网阶段。
- 后续阶段：P1 学习笔记查询与技术答题（复用 Markdown 存储和 DeepSeek，JSON mode）；P2 网页版桌宠（纯前端）；P3 爬虫与小说阅读（仅用户自有或已授权内容，遵守 robots 与限速，不抓取付费内容）。

## Testing Decisions

- 单一测试接缝：FastAPI HTTP API（pytest + TestClient）。只测外部行为（请求与响应），不测内部实现细节；前端验证以 `npm run build` 通过加手动冒烟为准。
- 被测模块：计划任务 CRUD、日记保存/加载/搜索、番茄会话创建与日统计、导航分类和链接 CRUD、聚合首页数据正确性。
- 先例：本仓库是绿地项目，没有可复用的既有测试；本规格将建立第一套后端 API 冒烟测试，测试数据库使用独立 SQLite 文件或临时目录，避免污染真实数据。
- 手工验收场景：一键启动后完成一条任务、写一篇日记、记一次番茄、加一个导航链接，确认聚合首页四块数据同步更新。

## Out of Scope

- 登录、多用户、公网部署、HTTPS、Docker/nginx（P0 不做）。
- AI 能力：DeepSeek、笔记问答、自动判分、日记摘要（P1 起）。
- 网页桌宠、爬虫、小说阅读（后续阶段）。
- 浏览器书签导入、日历视图、目标拆解、周/月统计报表。
- 独立移动端应用或移动端优先设计。

## Further Notes

- 实现前先编写并持续同步 plan.md；每个阶段完成后用业务语言说明该阶段的作用和收益。
- 测试接缝默认采用后端 API 单接缝；如果后续希望增加前端组件测试，再在对应模块补 Vitest 用例。
- 本规格暂存于仓库内；当前环境未配置 issue tracker（无远程仓库、无 GitHub CLI、无相关连接器），待配置后按 to-spec 流程发布到项目 issue tracker 并打上 ready-for-agent 标签。

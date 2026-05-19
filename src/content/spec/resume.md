## 招聘官快速判断

- **目标岗位**：Go 后端工程师 / AI 应用工程师 / AI Agent 平台工程师 / Vue 全栈工程师。
- **主线能力**：能把认证权限、队列调度、WebSocket 实时通信、AI Agent、工具调用、知识库、运行监控、浏览器插件和前端管理台做成一套真实可运行、可验证、可部署、可公开追溯的系统。
- **最大卖点**：我不是只会写页面或单表 CRUD 的候选人，而是能用 Go/Vue/AI 把复杂后台主线从架构、开发、测试、部署到公开作品集完整打穿。

## 基本信息

- **姓名**：左光明
- **学历**：本科 · 武汉文理学院 · 计算机科学与技术 · 2026届
- **电话**：15671628271
- **邮箱**：2093146753@qq.com
- **地点**：武汉 / 全国 / 远程均可
- **期望薪资**：面议，优先看岗位挑战和成长空间
- **GitHub**：[github.com/zgm2003](https://github.com/zgm2003)
- **在线系统**：[zgm2003.cn](https://zgm2003.cn)
- **个人博客**：[blog.zgm2003.cn](https://blog.zgm2003.cn)
- **技术社区**：[Linux.do 三级用户](https://linux.do/u/zgm2003/summary)

---

## 求职主线

我当前最核心的简历项目，是把一套已有企业级 Admin 系统从 PHP/Webman 迁到 **Go + Gin modular monolith**，同时维护配套 **Vue 3 + TypeScript** 管理前端。这个项目已经覆盖后台核心能力和 AI 应用平台能力：登录会话、RBAC、用户/角色/权限、操作日志、系统配置、队列任务、定时调度、WebSocket、通知推送、AI Provider、Agent、Chat、Run Monitor、Tool Calling、Knowledge RAG 等。

这个项目不是 CRUD demo。它有后端 API 进程、Worker 进程、MySQL/Redis 状态、Asynq 队列、DB-backed scheduler、WebSocket realtime、Docker 部署、宝塔/Nginx 反代、前后端契约文档、单元测试、Vitest、vue-tsc 和 smoke 脚本。对应的 root / backend / frontend 仓库都已经公开到 GitHub，可以被直接审阅。

---

## 招聘官担心点，我直接给反证

| 担心点 | 我的反证 |
| --- | --- |
| “应届生项目是不是玩具？” | 主项目不是孤立 demo，而是 Go API + Worker + MySQL + Redis + WebSocket + Asynq + Vue 管理台 + Docker/Nginx 部署的组合系统。 |
| “是不是只会套 AI 接口？” | AI 链路覆盖 Provider、Agent、Conversation、Message、Run Monitor、Tool Calling、Knowledge RAG、流式事件和运行记录。 |
| “是不是只会前端或只会后端？” | 后端负责认证、权限、队列、实时通信、AI 调用链；前端负责 typed API、动态菜单、AI Chat、Run Monitor、Knowledge/Tool 页面。 |
| “简历写得很满，能不能追问？” | GitHub 仓库、在线系统、技术博客、测试文件、部署文档和 smoke 脚本都能作为追问入口。 |

---

## 核心竞争力

### 1. Go 后端：能搭复杂后台系统，不只是写接口

- 使用 **Go / Gin / GORM / MySQL / Redis / Asynq / gocron/v2 / gorilla/websocket / slog** 构建 Admin 后端，进程拆成 `admin-api` 和 `admin-worker`。
- 后端采用 **modular monolith**，顶层按 `cmd -> bootstrap -> server -> module -> platform` 装配，模块内部按 `route -> handler -> service -> repository -> model` 收口，避免 Java 式过度抽象。
- 已落地 **30+ 后端模块**：auth、session、captcha、user、permission、role、operationlog、notification、notificationtask、crontask、exporttask、systemlog、systemsetting、uploadconfig、uploadtoken、realtime、queuemonitor、clientversion、payment、AI provider / agent / chat / conversation / message / run / tool / knowledge 等。
- 熟悉认证会话和权限系统：Access / Refresh Token、Token Hash + Pepper、Redis token cache、MySQL session fallback、平台策略、设备/IP 策略、单端登录、refresh rotation、logout revoke、滑块验证码、RBAC 动态菜单、按钮权限码、fail-closed API 权限检查。
- 能把横切能力做清楚：`Recovery -> RequestID -> AccessLog -> CORS -> AuthToken -> PermissionCheck -> OperationLog -> Handler`，权限检查和操作审计都走显式 route metadata，不靠反射和 handler 名称猜测。

### 2. AI 工程化：不只是调模型，而是做 AI 平台闭环

- 设计并实现后台 AI 管理链路：**Provider -> Agent -> Conversation -> Message -> Run -> Tool -> Knowledge**，前后端都有明确 REST 契约和页面入口。
- Provider 配置支持 OpenAI-compatible 接入，API Key 服务端加密保存，列表/详情不返回明文或密文字段，避免密钥泄露。
- Agent 配置按场景管理模型、系统提示词、头像、状态，并支持绑定工具和知识库；Chat 页面只消费启用的 chat 场景 Agent。
- AI Chat 使用 `ai_conversations` + `ai_messages` 持久化会话和消息，模型回复通过共享 WebSocket 输出 `ai.response.start/delta/completed/failed.v1` 版本化事件。
- Run Monitor 记录一次 AI 调用的生命周期、耗时、token、错误、消息关联、工具调用和知识检索明细，避免 AI 调用变成不可排查的黑盒。
- Tool Calling 支持从 Agent 绑定的工具生成 OpenAI function tools，执行工具调用并把结果回传模型，同时落库 `ai_tool_calls` 供运行监控查看。
- Knowledge RAG 使用本地知识库、文档、chunk、检索配置和命中记录，把检索内容只注入当前模型输入，并记录 `ai_knowledge_retrievals` / hits 审计链路。
- 流式治理不是只开一个超时：区分在线回复最大时长、上游 stream idle timeout、stale run 清理任务，避免慢模型、断流和后台清理互相污染。

### 3. WebSocket / 队列 / 调度：能处理真实运行时问题

- WebSocket 后端基于 gorilla/websocket，实现 cookie path-scoped upgrade 认证、bounded send queue、read/write pump、heartbeat、identity topic 白名单、断开清理。
- Realtime Publisher 支持 `local / noop / redis`，多 API 进程下通过 Redis Pub/Sub fan-out，把通知和 AI 回复投递给当前在线 session。
- 队列采用 Asynq，任务类型版本化，例如 `export:run:v1`、`notification:dispatch-due:v1`、`notification:send-task:v1`、`ai:conversation-reply:v1`、`ai:run-timeout:v1`、`payment:close-expired-order:v1`。
- Worker 负责导出、通知、登录日志、AI run timeout、支付定时任务等后台处理；Scheduler 从数据库 `cron_task` 注册任务，并用 Redis lock 降低多 worker 重复执行风险。
- 导出任务不是假按钮：提交后创建 `export_tasks` pending 行，Worker 生成 xlsx、上传 COS、更新状态，并通过通知任务提醒用户。

### 4. Vue / TypeScript 前端：能把复杂后台能力交付成可用页面

- 前端使用 **Vue 3.5 / TypeScript / Vite / Element Plus / Pinia / Vue Router / Vue I18n / Vitest**，不是简单页面拼装。
- 已把大量旧 PHP legacy 调用切到 Go REST typed client，API 层按资源拆分：`src/api/ai/*`、`src/api/user/*`、`src/api/permission/*`、`src/api/system/*`、`src/api/payment/*`。
- 动态菜单和按钮权限来自后端 `users/init`，前端用 permission map 和 button codes 驱动路由、菜单和操作按钮，不在页面里硬编码权限逻辑。
- AI 前端已经形成产品化页面：Provider 配置、模型同步、Agent 配置、工具绑定、知识库/文档/chunk/检索测试、Run Monitor、AI Chat 会话页。
- AI Chat 前端不是一个 textarea：包含 Agent 列表、会话抽屉、消息列表、WebSocket 增量回复、会话切换缓存、未完成回复保护、取消生成、图片附件、语音输入、emoji、运行参数面板。
- WebSocket client 封装共享连接、自动重连、identity topic 订阅、message bus 分发，并处理本地开发 `localhost/127.0.0.1` cookie host 隔离问题。
- 前端质量有测试兜底：AI API contract、message session visibility、stream chat session、router guards、permission UI、payment views、notification runtime、realtime client、useTable/useCrudTable 等都有 Vitest 覆盖。

### 5. 工程验证与部署：不是“本地能跑”就结束

- 后端当前规模：**536 个 Go 文件、161 个 Go 测试文件、849 个测试函数、约 72,600 行 Go 代码**。
- 前端当前规模：**285 个 TS/Vue 源码文件、74 个 Vitest 测试文件、约 43,900 行前端源码**。
- 建立文档和验证闭环：`current-status.md`、`admin-api-v1.md`、`admin-realtime-v1.md`、smoke matrix、backend architecture、README、Docker 部署文档。
- 部署链路包含 Docker Compose、`admin-api` / `admin-worker`、MySQL、Redis、宝塔 Nginx 反代、HTTPS、前端 GitHub Actions 自动打包上传 dist。
- 排障时优先看运行时事实：日志、真实路由、网络请求、WebSocket 认证、Nginx 反代、Redis key、MySQL 表结构和 smoke 结果，而不是靠猜。

---

## 可投岗位关键词

> Go 后端工程师 / 后端开发工程师 / AI 应用开发工程师 / AI Agent 工程师 / 全栈开发工程师 / Vue + Go 全栈 / 平台型后台系统 / 工程化与部署

我更适合的团队画像：

- 正在做企业级后台、SaaS、AI 平台、内部工具、数据/内容生产系统的团队。
- 需要一个能同时理解后端架构、前端交付、AI 工作流和部署排障的人。
- 愿意看作品集和 GitHub，而不是只看“几年经验”的团队。

---

## GitHub 公开项目证据

我的 GitHub 不是只放学习 demo，而是按“能被面试官追问”的方式沉淀项目。下面这些仓库分别证明后端架构、前端工程、AI Agent、可靠性设计、浏览器扩展和个人技术表达能力。

| 仓库 | 类型 | 能证明什么 |
| --- | --- | --- |
| [admin_go](https://github.com/zgm2003/admin_go) | Go/Vue 总控仓库 | 架构文档、契约文档、smoke/governance、Codex hooks、agent 工作流和工程事实源管理 |
| [admin_back_go](https://github.com/zgm2003/admin_back_go) | Go 后端 | Gin modular monolith、认证/RBAC、AI 平台、WebSocket、Asynq、scheduler、COS、支付、测试和部署 |
| [admin_front_ts](https://github.com/zgm2003/admin_front_ts) | Vue 管理前端 | Vue 3 + TypeScript 后台、动态路由、按钮权限、AI Chat、Run Monitor、Knowledge/Tool 管理、Vitest |
| [personal_blog](https://github.com/zgm2003/personal_blog) | 个人站点 / 简历 / 技术文章 | Astro 技术博客、在线简历、项目复盘和工程思考沉淀 |
| [rc_zuoguangming](https://github.com/zgm2003/rc_zuoguangming) | Python / FastAPI 可靠通知服务 | 持久化通知意图、异步投递、失败重试、attempt 记录、SSRF 防护和 at-least-once 语义 |
| [spider_media](https://github.com/zgm2003/spider_media) | Chrome / Edge MV3 扩展 | `webRequest` 监听、页面主世界桥接、DOM 观察、blob 抓取、HLS/DASH 轻量分析和 ffmpeg 命令生成 |
| [cine-make](https://github.com/zgm2003/cine-make) | AI Agent 工具链 | Codex skill、本地 CLI、短剧预生产、storyboard、分镜连续性、AI 视频工具 prompt pack |
| [chatgpt2api](https://github.com/zgm2003/chatgpt2api) | Python / React 研究型 fork | OpenAI-compatible API、图片生成/编辑、账号池、Docker 自托管、前后端联动和复杂项目二次维护能力 |

这组仓库能形成一条清楚主线：

> 企业级后台系统 -> AI Agent 平台 -> 实时通信/队列/调度 -> 浏览器采集/自动化 -> 可靠性小系统 -> 技术博客与公开表达

---

## 代表项目

### 智澜 Admin Go / Vue 企业级 AI 管理系统重构

- **角色**：个人主导 / Go 主后端架构与实现 / Vue 前端适配 / 线上部署
- **在线地址**：[https://zgm2003.cn](https://zgm2003.cn)
- **GitHub**：[admin_go](https://github.com/zgm2003/admin_go) / [admin_back_go](https://github.com/zgm2003/admin_back_go) / [admin_front_ts](https://github.com/zgm2003/admin_front_ts)
- **技术栈**：Go、Gin、GORM、MySQL、Redis、Asynq、gocron/v2、gorilla/websocket、slog、Docker Compose、Vue 3、TypeScript、Vite、Element Plus、Pinia、Vitest、腾讯云 COS、OpenAI-compatible API。
- **相关复盘**：[Go Admin Core Foundation：从 PHP 迁移到 Gin Modular Monolith](/posts/go-admin-architecture-design/)

#### 项目价值

这是一套面向后台管理和 AI 应用配置的全栈系统重构。核心难点不是“写几个接口”，而是在不破坏既有前端和业务使用路径的前提下，把认证权限、用户体系、系统配置、日志审计、队列调度、WebSocket 实时通信和 AI 平台能力迁到 Go，并让前端同步切到新 REST 契约。

#### 我负责的关键工作

**后端架构与权限核心**
- 搭建 Gin modular monolith，固定 API 进程和 Worker 进程边界，所有模块通过 bootstrap 统一装配依赖。
- 实现登录、验证码、Token refresh、logout revoke、session fallback、用户资料、用户会话、用户管理、角色授权、权限树、动态菜单、按钮权限码。
- 设计显式 middleware 链和 route metadata，做到认证、权限、审计三者职责分离。

**AI 平台能力**
- 实现 AI Provider 配置、OpenAI 模型同步、密钥加密存储和响应脱敏。
- 实现 Agent 配置、Chat 会话、消息持久化、WebSocket 增量回复、取消生成、运行监控、token/耗时统计。
- 实现工具调用闭环：Agent 绑定工具 -> Provider function tools -> 工具执行 -> 结果回传模型 -> `ai_tool_calls` 落库。
- 实现本地 Knowledge RAG MVP：知识库、文档、chunk、检索测试、Agent 绑定、运行时检索注入、命中审计。

**实时通信与异步任务**
- 实现 WebSocket realtime：认证 upgrade、心跳、订阅白名单、慢客户端保护、Redis Pub/Sub fan-out。
- 实现通知任务发布/调度/发送，支持 `notification.created.v1` 事件推送到在线用户。
- 实现 Asynq 队列和 DB-backed cron task，Worker 统一消费导出、通知、AI timeout、支付定时任务。

**前端管理台**
- 用 Vue 3 + TypeScript 适配 Go REST API，沉淀 typed API client，逐步删除 legacy client 和旧 PHP 路径。
- 实现 AI Provider / Agent / Tools / Knowledge / Runs / Chat 页面，覆盖配置、绑定、检索、运行明细和实时会话。
- 封装共享 WebSocket client 和 message bus，AI Chat 按 `conversation_id + request_id` 分发增量回复，切换会话不丢未完成输出。
- 动态菜单、动态路由、按钮权限全部由后端返回，前端只负责渲染和交互，不再自造权限事实。

**部署与验证**
- 编写 Docker Compose 部署，`admin-api` 和 `admin-worker` 分进程运行，Nginx/宝塔负责 HTTPS 和反向代理。
- 配置前端 GitHub Actions，push 后自动构建 dist 并上传服务器。
- 使用 Go test、Vitest、vue-tsc、contract check、basic/full smoke 脚本验证核心链路。

#### 项目亮点

- **复杂度真实**：不是单表 CRUD，而是认证、RBAC、WebSocket、队列、AI、RAG、运行监控、部署的组合系统。
- **边界清楚**：Go 后端不写成 Java，前端不靠 `any` 和空兜底吞错误，契约漂移通过测试和 smoke 暴露。
- **AI 能力可观测**：每次 AI 调用都有 conversation/message/run/event/tool/retrieval 记录，不把模型调用当黑盒。
- **运行时可部署**：有 Docker、Nginx、域名、HTTPS、MySQL、Redis、日志、健康检查和 CI/CD，不停在本地 demo。

### Python + AI 电商内容自动化流水线

- **角色**：个人项目 / Python 自动化与 AI 内容生成链路设计
- **相关仓库**：[spider_media](https://github.com/zgm2003/spider_media)；商品采集扩展当前保留在 Gitee/local 工作区
- **技术栈**：Python、浏览器插件、OCR、AI Agent、TTS、SRT、Redis Queue、MySQL、COS。

围绕电商商品构建 **商品采集 -> 图片/OCR -> AI 卖点与口播生成 -> TTS 合成 -> SRT 字幕下载** 的内容生产流水线。重点不是“调用一次模型”，而是把运营重复劳动拆成可采集、可清洗、可排队、可追踪、可重试、可审核的任务链。

- 浏览器插件采集商品标题、价格、销量、品牌、店铺、规格、评论、详情图等结构化信息。
- Python 负责数据清洗、图片/文件处理、接口回放、AI 工具链验证和批处理脚本。
- 后台负责状态管理、人工审核、任务排队和结果持久化，Python/AI 层负责重复处理和生成能力。
- 适合作为我 Python 方向的证明：Python 放在 AI 自动化和数据处理上，而不是硬包装成普通 CRUD 后端。

### Cine Make / AI Agent 本地生产力工具链

- **角色**：个人工具 / Codex Skill / 本地 Agent 工作流设计
- **GitHub**：[cine-make](https://github.com/zgm2003/cine-make)
- **技术栈**：Node.js、JavaScript ESM、Codex Skill、Prompt Engineering、AI Image/Video Prompt、自动化测试。

Cine Make 是一个本地 AI 短剧预生产工具，目标不是渲染 MP4，而是把小说、脚本、广告 brief 或故事片段拆成可交给 AI 视频工具的交付包：故事流、分镜、关键帧提示词、角色/场景参考、连续性备注和 video-tool feed pack。

- 支持 draft / visual 两种模式，先确认故事节奏，再进入图片和视频工具交付。
- 将 30 秒短剧拆成连续的 15 秒卡片，复用上一段尾帧作为下一段起帧，解决 AI 视频常见的连续性问题。
- 将内部调试产物和用户交付产物分离，正常输出只暴露 `deliverable.md` 和 `storyboard-images/`。
- 这个项目体现的是我对 AI Agent 的判断：AI 不只是聊天框，而应该被产品流程、交付物、验证脚本和边界约束成稳定工具。

### Reliable HTTP Notification Service

- **角色**：课程/作品项目 / Python 后端可靠性设计
- **GitHub**：[rc_zuoguangming](https://github.com/zgm2003/rc_zuoguangming)
- **技术栈**：Python、FastAPI、SQLite、HTTPX、Docker Compose、pytest。

这是一个面向内部系统的可靠 HTTP 通知投递服务。业务系统只提交“通知意图”，服务负责持久化、异步投递、失败重试和最终失败记录。

- 采用 `POST /notifications -> persist first -> worker claim -> HTTP dispatch -> attempts` 的可靠投递链路。
- 明确选择 **at-least-once delivery**，不伪造 HTTP exactly-once；通过 `idempotency_key` 和 attempt 记录降低重复投递风险。
- 对 loopback、link-local、metadata 等目标做 SSRF/open relay 防护，避免通知服务变成内网探测器。
- 这个项目适合面试时讲可靠性语义、边界设计、重试策略和工程取舍。

---

## 技术文章 / 证明材料

- [Go Admin Core Foundation：从 PHP 迁移到 Gin Modular Monolith](/posts/go-admin-architecture-design/)
- [从调 API 到 Agent 工程化：把 AI 能力做成可治理系统](/posts/ai-agent-engineering-practice/)
- [Agent 工程学习路线：从 LLM 到可上线智能体系统](/posts/understanding-ai-ecosystem/)
- [电商 AI 口播生成系统：OCR、Agent、TTS 与队列闭环](/posts/ecommerce-ai-script-generation/)
- [WebSocket 实时通信架构：从连接管理到业务事件分发](/posts/websocket-realtime-architecture/)
- [Go 语言基本学习路线：从变量到项目入门](/posts/go-beginner-learning-route/)
- [个人 GitHub 仓库](https://github.com/zgm2003)

---

## 教育经历

### 武汉文理学院 · 计算机科学与技术 · 本科

**毕业时间**：2026.06

---

## 我的优势

- **能做复杂系统主线**：Go 后端、Vue 前端、AI 平台、队列、WebSocket、部署都在同一个真实项目里串起来了。
- **不是只会写页面或单表 CRUD**：我能处理认证、权限、审计、异步任务、实时通信、AI 调用链、运行监控和线上部署。
- **有工程洁癖**：反感 `any`、空兜底、静默 catch、字段乱猜和假兼容；更倾向契约清楚、边界清楚、测试能证明。
- **能把 AI 做成产品能力**：Provider、Agent、Tool、Knowledge、Chat、Run Monitor 都有后台管理和运行记录，不是孤立的 Prompt Demo。
- **学习和迁移能力强**：能从旧 PHP 系统抽业务事实，用 Go 重建运行边界，并让前端逐步切到新契约。

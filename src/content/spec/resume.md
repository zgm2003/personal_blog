# 左光明 - AI Agent / Web 全栈工程师

> 目标不是“会一点前后端”，而是能把 AI、权限、支付、实时通信、异步任务和部署链路收束成一个可运行、可维护、可扩展的企业级系统。

## 基本信息

- **姓名**：左光明
- **学历**：本科 · 武汉文理学院 · 计算机科学与技术 · 2026届
- **电话**：15671628271
- **邮箱**：2093146753@qq.com
- **方向**：AI Agent 工程师 / Web 全栈工程师 / 企业级后台系统开发
- **地点**：武汉 / 全国 / 远程均可
- **期望薪资**：8K 起
- **在线系统**：[zgm2003.cn](https://zgm2003.cn)
- **技术社区**：[Linux.do 三级用户](https://linux.do/u/zgm2003/summary)

---

## 个人定位

我不是按“前端、后端、某一种语言”来定义自己的开发者。我更关注的是：**一个系统的边界是否清楚、数据流是否可信、异步任务是否可恢复、权限模型是否可演进、AI Agent 是否能被观测和治理、部署后是否真的能稳定跑起来**。

目前我最核心的证明，是独立设计并上线了一套企业级 AI Admin 系统：前端、后端、数据库、权限、Agent、SSE、WebSocket、支付、队列、桌面端更新和线上部署都由我自己完成。

---

## 技术能力

### AI Agent / LLM 工程化

- 能把大模型能力落成可管理的工程系统，而不是只停留在“调 API / 写 Prompt”。
- 设计过 Agent、Model、Tool、Prompt、Conversation、Message、Run、Run Step 等运行模型。
- 熟悉 SSE 流式对话、运行取消、超时治理、历史消息拼装、步骤审计和错误暴露。
- 关注 Tool Calling 的安全边界：内部工具、HTTPS 白名单工具、只读 SQL 工具、SSRF 防护、SQL 写操作拦截、结果截断。
- 理解 RAG 的检索、召回、重排、上下文拼装链路；当前项目已预留 RAG 模式和 Step 类型，后续可继续扩展。

### 前端 / 客户端工程

- Vue 3.5、TypeScript 5.9、Vite 8、Element Plus、Pinia、Vue Router、Vue I18n。
- 熟悉后台前端工程化：统一请求封装、ApiEnvelope 解包、401 刷新队列、动态路由、按钮权限、SSE 严格解析、WebSocket 单例连接。
- 能拆分前端基础设施边界：HTTP、Auth Session、Stream、Realtime、Router、Tauri Runtime、Table / CRUD composable。
- 使用 Tauri 2 封装线上 Admin，处理窗口能力、版本检测、更新清单、NSIS 打包和 CSP 安全策略。

### 后端 / 系统架构

- PHP 8.1+、Webman / Workerman、Eloquent、MySQL 8.4、Redis、Redis Queue、GatewayWorker、Crontab、PHPUnit。
- 坚持 Controller -> Module -> Dep -> Model 分层：Controller 只转发，Module 只编排，Dep 负责数据访问，Model 只做表映射。
- 熟悉认证权限：Access / Refresh Token、Token Hash + Pepper、Redis Session、单端登录、平台/设备/IP 绑定、RBAC 菜单/路由/按钮权限。
- 熟悉异步与后台任务：Redis Queue、定时任务、AI 超时检测、通知调度、支付关单/同步/履约/对账任务。

### 部署 / 交付

- 独立完成域名、HTTPS、Nginx 反代、Webman 多端口服务、MySQL、Redis、COS 静态资源与更新清单配置。
- 能区分 API、SSE、WebSocket 不同服务形态，并按运行时特性做端口与反代隔离。
- 关注契约测试和工程约束，不靠前端兜底掩盖后端错误。

---

## 工作经历

### 小药药医药科技有限公司 · 前端开发

**时间**：2025.10.27 - 至今

- 负责公司前端业务开发与日常需求维护，参与页面实现、交互联调、接口对接和需求迭代。
- 公司项目内容后续可按真实模块继续补充；当前简历不虚构未确认的业务成果。

---

## 项目经历

### 智澜·TS 企业级 AI Admin 系统

**角色**：个人项目 / 独立设计与开发 / 已上线  
**在线地址**：[https://zgm2003.cn](https://zgm2003.cn)  
**技术栈**：Vue 3.5、TypeScript、Vite 8、Element Plus、Pinia、Vue Router、Vue I18n、Tauri 2、PHP 8.1+、Webman / Workerman、Eloquent、MySQL 8.4、Redis、Redis Queue、GatewayWorker、NeuronAI、Yansongda Pay、腾讯云 COS / TTS、阿里云 AIGC / TTS。

#### 项目概述

智澜·TS 是一套面向企业后台管理与 AI 能力集成的全栈 Admin 系统。它不是单纯的 CRUD Demo，而是一个包含 **认证权限、动态菜单、AI Agent、流式对话、IM 聊天、支付钱包、订单履约、上传存储、通知任务、导出任务、系统日志、Tauri 桌面端更新** 的完整工程。

这个项目真正体现的是我的工程能力：我能把复杂系统拆成可维护边界，把 AI 能力接入业务系统，把异步任务、实时通信、权限模型和部署链路做成闭环。

#### 1. AI Agent 运行系统

- 设计 Agent / Model / Tool / Prompt / Conversation / Message / Run / Step 数据模型，让一次 AI 调用从“黑盒请求”变成可追踪、可审计、可取消、可超时治理的运行过程。
- 支持多模型 Provider 和 OpenAI-compatible 接口，面向不同 Agent 绑定模型、系统提示词和工具能力。
- 后端通过独立 SSE 服务输出 `conversation`、`run`、`content`、`tool_call`、`tool_result`、`done`、`error`、`canceled` 等事件；前端按事件驱动更新 UI，而不是拼接假状态。
- 前端对 SSE 做严格解析：malformed payload、缺失终止事件、运行失败都会直接暴露，避免“看起来完成了，实际状态坏了”的假成功。

#### 2. Agent Tool 安全治理

- 实现 Internal Tool、HTTPS 白名单 Tool、只读 SQL Tool 三类工具执行器。
- HTTPS 工具执行前做域名/IP 检查，拒绝 IP 直连和内网地址访问，降低 SSRF 风险。
- SQL 工具限制只允许 SELECT，拒绝 INSERT / UPDATE / DELETE / DROP 等写关键字，并自动追加 LIMIT，避免 Agent 直接变成数据库破坏入口。
- 工具调用链路保留执行记录和结果截断，兼顾可观测性与安全边界。

#### 3. 企业级后台架构

- 后端坚持 Controller -> Module -> Dep -> Model 分层，避免接口、业务、查询、表映射混在一起。
- Controller 只做路由入口，Module 负责编排验证、事务和业务流程，Dep 负责 Eloquent 查询与缓存读写，Model 只保留表映射和 casts。
- Service 承载跨模块能力，Lib 封装第三方 SDK，保证 AI、支付、上传、TTS 等外部能力不会污染业务层。
- 当前后端规模：**43 个 Controller、48 个 Module、46 个 Dep、47 个 Model、21 个 Service、10 个 Redis Queue 消费者**。

#### 4. 认证、权限与动态路由

- 实现 Access / Refresh Token 机制，Token 明文不落库，仅存 Hash；结合 Pepper、Redis Session、过期校验和降级 DB 查询。
- 支持单端登录指针、平台/设备/IP 绑定策略，降低 Token 被复用后的风险。
- RBAC 权限按平台输出菜单树、动态路由和按钮权限码，前端通过 `userStore.can(code)` 控制按钮级权限。
- 动态路由只接收后端 `view_key`，前端通过 `import.meta.glob` 精确解析视图组件，不做路径猜测和历史字段兜底。

#### 5. 前端基础设施与强契约

- 封装 Axios 客户端，统一处理 ApiEnvelope 解包、错误提示、认证 Header 和 401 刷新队列。
- 拆分 `useTable` 与 `useCrudTable`：前者只管列表与分页，后者才处理搜索、删除、批量删除、状态切换等 CRUD 编排。
- WebSocket 客户端封装为单例连接，支持绑定用户、自动重连、ping/pong 和消息总线分发。
- 对前后端契约采取“后端错就暴露”的策略，不用空数组、空对象、静默 catch 去掩盖接口问题。

#### 6. 支付、钱包与订单闭环

- 接入 Yansongda Pay，完成微信/支付宝支付相关能力封装。
- 实现充值订单、支付流水、钱包入账、订单履约、支付回调、对账任务和定时补偿。
- 使用 RedisLock 控制重复提交和回调并发，避免支付链路重复入账或重复履约。
- 将履约、关单、同步、对账放入后台任务，减少主请求链路阻塞。

#### 7. 商品 AI 工作台

- 围绕电商商品构建 OCR -> AI 口播生成 -> TTS 合成 -> SRT 下载的异步流水线。
- 支持商品采集、图片选择、OCR 识别、Agent 生成卖点/口播词、语音合成和字幕文件下载。
- 使用 Redis Queue 承载 OCR、AI、TTS 等耗时任务，让用户操作链路保持即时响应。

#### 8. 桌面端与线上部署

- 使用 Tauri 2 封装线上 Admin，配置窗口能力、进程退出、版本检测、NSIS 打包、COS 更新清单和 CSP。
- 独立完成服务器部署、域名解析、HTTPS、Nginx 反代、MySQL / Redis 配置和前端发布。
- 线上服务拆分为 API `8787`、SSE `8788`、WebSocket `7272`，按协议特性分别反代。

---

## 教育经历

### 武汉文理学院 · 计算机科学与技术 · 本科

**毕业时间**：2026.06

---

## 我的优势

- **不是只会写页面**：能从页面走到接口、数据库、队列、权限、Agent、部署和桌面端。
- **不是只会调模型**：能把 LLM 接成 Agent 运行系统，考虑工具安全、运行审计、超时、取消和前端流式体验。
- **不是只会堆功能**：更关注模块边界、前后端契约、数据一致性和系统长期维护成本。
- **不被语言栈限制**：PHP、TypeScript、JavaScript、Python 都只是工具，真正重要的是架构、边界和交付。

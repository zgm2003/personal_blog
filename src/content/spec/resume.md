# 左光明 - Python / AI Agent / Web 全栈工程师

> 求职主线：**Python AI 应用开发 / AI Agent 工程化 / 后端系统开发 / Web 全栈交付**。我想表达的不是“会很多栈”，而是能把 AI、数据处理、权限、队列、实时通信和部署链路收束成一个真实可运行的系统。

## 基本信息

- **姓名**：左光明
- **学历**：本科 · 武汉文理学院 · 计算机科学与技术 · 2026届
- **电话**：15671628271
- **邮箱**：2093146753@qq.com
- **地点**：武汉 / 全国 / 远程均可
- **期望薪资**：8K 起
- **在线系统**：[zgm2003.cn](https://zgm2003.cn)
- **技术社区**：[Linux.do 三级用户](https://linux.do/u/zgm2003/summary)

---

## 个人定位

我不是只按“前端 / PHP / 某一种语言”定义自己。我的核心能力是：**把业务问题拆成清楚的数据流、任务流、权限边界和交付链路**。

目前最能证明这一点的是我独立设计并上线的企业级 AI Admin 系统：前端、后端、数据库、权限、Agent、SSE、WebSocket、支付、Redis Queue、桌面端更新和线上部署都由我完成。这个项目让我更适合投递 **Python AI 应用、AI Agent 工程化、后端全栈、企业后台系统开发** 这类岗位，而不是只把自己包装成普通前端或普通 PHP 开发。

---

## 核心能力

### AI Agent / LLM 工程化

- 能把 LLM 调用落成可管理的工程系统：模型接入、Agent 配置、Prompt 管理、工具调用、流式输出、运行审计、超时取消和错误暴露。
- 设计过 Agent、Model、Tool、Prompt、Conversation、Message、Run、Run Step 等运行模型，把一次 AI 调用从“黑盒请求”拆成可观测状态机。
- 熟悉 OpenAI-compatible 接口、SSE 流式对话、历史消息拼装、工具执行记录、结果截断、失败恢复和取消机制。
- 关注 Tool Calling 安全边界：HTTPS 白名单、SSRF 防护、只读 SQL、写操作拦截、自动 LIMIT、敏感结果控制。
- 理解 RAG、工具调用、工作流、HITL、Guardrails、Tracing 和 Evals 在生产 Agent 系统中的位置，不把 Agent 简化成一句 Prompt。

### Python / 自动化 / 数据处理

- 能用 Python 做批量数据处理、接口调试、文件/素材处理、运营数据清洗和 AI 工具链辅助，不把重复脏活留给人工。
- 理解 Python 在 AI 应用里的真实价值：不是换个语言写 CRUD，而是承担采集、清洗、任务编排、模型调用、评估脚本和自动化流程。
- 有电商商品数据、图片/OCR、AI 口播生成、TTS 合成这类业务流水线经验，后续可自然演进为 Python 数据处理服务或 FastAPI AI 应用服务。
- 能把 Python 自动化与已有 Web 后台结合：前台负责操作入口，后端负责状态与权限，Python/脚本层负责重复处理和 AI 工具链。

### 后端 / 数据 / 异步任务

- PHP 8.1+、Laravel 8、Webman / Workerman、Eloquent、MySQL、Redis、Redis Queue、GatewayWorker、Crontab、PHPUnit。
- 坚持 Controller -> Module -> Dep -> Model 分层：Controller 只转发，Module 只编排，Dep 负责数据访问，Model 只做表映射。
- 熟悉认证权限：Access / Refresh Token、Sanctum、Token Hash + Pepper、Redis Session、单端登录、平台/设备/IP 绑定、RBAC 菜单/路由/按钮权限。
- 熟悉异步与后台任务：Redis Queue、Laravel Job、定时任务、AI 超时检测、通知调度、支付关单/同步/履约/对账任务。
- 能处理支付、钱包、上传存储、系统通知、导出任务、日志审计、实时通信等后台系统常见复杂链路。

### 前端 / 客户端工程

- Vue 3 / React、TypeScript、Vite、Element Plus、Ant Design、Pinia、Zustand、Vue Router、React Router、Vue I18n、Vant、uni-app。
- 熟悉后台前端工程化：统一请求封装、ApiEnvelope 解包、401 刷新队列、动态路由、按钮权限、SSE 严格解析、WebSocket 单例连接。
- 能拆分前端基础设施边界：HTTP、Auth Session、Stream、Realtime、Router、Table / CRUD composable、权限快照和 i18n 文案边界。
- 有 Electron / Tauri 桌面端经验，处理窗口能力、IPC / Bridge、Preload、版本检测、更新清单、安装包构建和 CSP 安全策略。

### 部署 / 交付

- 独立完成域名、HTTPS、Nginx 反代、Webman 多端口服务、MySQL、Redis、COS 静态资源与桌面端更新清单配置。
- 能区分 API、SSE、WebSocket、桌面端本地能力和外部渠道回调的运行形态，并按协议特性做隔离。
- 关注契约测试、接口边界和工程约束，不靠前端空数组、空对象、静默 catch 掩盖后端错误。

---

## 工作经历

### 小药药医药科技有限公司 · 前端开发

**时间**：2025.10.27 - 至今

- 从 0 搭建公司 SaaS 商家端前端工程，覆盖 Web 独立运行与 Electron Desktop 打包运行两条链路。
- 负责登录、租户/门店选择、总部/门店工作区切换、权限菜单、会话恢复、统一请求和 CRUD 基础设施等核心工程能力。
- 参与荷叶问诊后台、移动端 APP、问诊内核 H5 三端迭代，覆盖远程审方、视频问诊、合理用药审查、长处方/慢病规则、移动推送与跨端跳转等医疗问诊核心链路。
- 在 Figma Make 生成代码质量不稳定、UI 基础组件边界不清的约束下，逐步收口页面结构、组件边界和交互规范，避免设计稿代码直接污染业务层。

### 江苏麦影网络科技有限公司 · 全栈开发

**时间**：2024.06 - 2025.06

- 参与麦小图 VCMS 内容管理 / 发布系统迭代，覆盖视频发布、内容管理、达人运营、内容运营、后期运营、素材中心、数据中心和运营任务等核心模块。
- 参与 Electron + Vue 3 桌面端建设，通过 IPC、BrowserWindow / BrowserView、Preload 和本地存储能力承载多平台授权、内容发布、账号检测和运营辅助流程。
- 对接淘宝、京东、小红书、B 站、支付宝、得物、快手、拼多多等内容/电商渠道，处理 OAuth、Cookie 注入、渠道发布回调、账号池和平台数据同步等复杂链路。
- 参与 AI 内容生产与视频任务流转能力，覆盖商品/素材管理、AIGC 文案生成、视频混剪、字幕/语音/封面、审核状态和队列任务处理。
- 支撑运营后台高频能力：团队/角色/权限、批量编辑、Excel 导入导出、数据统计、内容审核和任务状态流转，提升内容运营批处理效率。

---

## 项目经历

### 智澜·TS 企业级 AI Admin 系统

**角色**：个人项目 / 独立设计与开发 / 已上线
**在线地址**：[https://zgm2003.cn](https://zgm2003.cn)
**技术栈**：Vue 3.5、TypeScript、Vite、Element Plus、Pinia、Vue Router、Vue I18n、Tauri 2、PHP 8.1+、Webman / Workerman、Eloquent、MySQL 8.4、Redis、Redis Queue、GatewayWorker、NeuronAI、Yansongda Pay、腾讯云 COS / TTS、阿里云 AIGC / TTS。
**相关复盘**：[AI Agent 工程化](/posts/ai-agent-engineering-practice/) / [SSE 流式对话](/posts/sse-streaming-chat/) / [Webman 分层架构](/posts/webman-layered-architecture/) / [WebSocket 实时通信](/posts/websocket-realtime-architecture/)

#### 项目概述

智澜·TS 是一套面向企业后台管理与 AI 能力集成的全栈 Admin 系统。它不是单纯的 CRUD Demo，而是一个包含 **认证权限、动态菜单、AI Agent、流式对话、IM 聊天、支付钱包、订单履约、上传存储、通知任务、导出任务、系统日志、Tauri 桌面端更新** 的完整工程。

#### 核心贡献

- **AI Agent 运行系统**：设计 Agent / Model / Tool / Prompt / Conversation / Message / Run / Step 数据模型，让一次 AI 调用从“黑盒请求”变成可追踪、可审计、可取消、可超时治理的运行过程。
- **流式对话协议**：后端通过独立 SSE 服务输出 `conversation`、`run`、`content`、`tool_call`、`tool_result`、`done`、`error`、`canceled` 等事件；前端按事件驱动更新 UI，不拼假状态。
- **Tool 安全治理**：实现 Internal Tool、HTTPS 白名单 Tool、只读 SQL Tool 三类工具执行器；SQL 只允许 SELECT，拒绝写操作，并自动追加 LIMIT。
- **企业级后台分层**：后端坚持 Controller -> Module -> Dep -> Model 分层，Service 承载跨模块能力，Lib 封装第三方 SDK，避免业务、查询、表映射混在一起。
- **认证权限体系**：实现 Access / Refresh Token、Token Hash + Pepper、Redis Session、单端登录、平台/设备/IP 绑定、RBAC 菜单/动态路由/按钮权限码。
- **支付与订单闭环**：接入 Yansongda Pay，完成充值订单、支付流水、钱包入账、订单履约、支付回调、对账任务和定时补偿；使用 RedisLock 控制重复提交和回调并发。
- **实时通信与异步任务**：封装 WebSocket 单例连接、GatewayWorker 推送、Redis Queue 消费者、AI 超时检测、通知调度、支付关单/同步/履约/对账任务。
- **线上部署**：独立完成服务器部署、域名解析、HTTPS、Nginx 反代、MySQL / Redis 配置；线上服务拆分为 API `8787`、SSE `8788`、WebSocket `7272`。

#### 可量化信息

- 后端规模：**43 个 Controller、48 个 Module、46 个 Dep、47 个 Model、21 个 Service、10 个 Redis Queue 消费者**。
- 运行边界：API、SSE、WebSocket、队列消费者、定时任务、Tauri 桌面端更新链路均已形成闭环。
- 工程原则：前后端强契约，后端错就暴露，不靠前端空对象、空数组、静默 catch 掩盖协议问题。

### 电商 AI 口播生成流水线

**角色**：个人项目 / AI 业务落地 / 商品 AI 工作台能力
**技术栈**：Chrome Extension、OCR、AI Agent、TTS、Redis Queue、PHP / Webman、MySQL、COS、Python 自动化脚本。
**相关复盘**：[电商 AI 口播生成系统](/posts/ecommerce-ai-script-generation/)

#### 项目概述

该项目围绕电商商品构建 **商品采集 -> 图片/OCR -> AI 卖点与口播生成 -> TTS 合成 -> SRT 下载** 的异步流水线。它的价值不是“做了一个 AI 按钮”，而是把内容运营中的重复劳动拆成可排队、可追踪、可重试、可审核的任务链路。

#### 核心工作

- 浏览器插件负责采集商品标题、价格、销量、品牌、店铺、规格、描述、评论、详情图等结构化信息。
- 后端承接商品入库、图片选择、OCR 识别、Agent 生成卖点/口播词、TTS 合成和字幕文件下载。
- 使用 Redis Queue 承载 OCR、AI、TTS 等耗时任务，让用户操作链路保持即时响应。
- 为不同阶段设计状态流转，避免任务失败后只留下一个模糊的“生成失败”。
- 用 Python 自动化脚本辅助批量数据处理、文件处理、接口调试和 AI 工具链验证，为后续拆出 Python 数据处理服务打基础。

#### 求职价值

这个项目适合作为 Python / AI 应用方向的核心包装材料：它天然包含数据采集、清洗、图片/OCR、模型调用、任务队列、状态机和人工审核闭环。Python 在这里不是硬贴标签，而是最适合承接采集清洗、AI 工作流和自动化处理的工程语言。

### SaaS 商家端 Web / Desktop 一体化前端

**角色**：公司项目 / 前端架构与核心开发 / 从 0 搭建
**技术栈**：React 19、TypeScript、Vite、Electron、Ant Design、TanStack React Query、Zustand、React Router、Axios、Zod、Tailwind CSS、Electron Builder。
**相关复盘**：[SaaS 商家端 Web / Desktop 一体化前端工程复盘](/posts/saas-seller-web-desktop-frontend/)

#### 项目概述

该项目是面向药店/商家的 SaaS 管理端，既支持浏览器 Web 运行，也支持 Electron 桌面端本地运行和打包发布。我负责从工程初始化到核心链路落地：运行时识别、接口基址配置、登录恢复、门店/总部工作区、权限菜单、统一请求、状态管理和通用 CRUD 页面能力。

#### 核心工作

- 搭建 Web / Desktop 双运行链路：Web 端使用 Vite 独立构建，桌面端通过 Electron 承载本地运行、后端 ready bridge、窗口能力和安装包构建。
- 设计运行时初始化与接口客户端配置，区分 Web、Desktop、本地后端、业务 API 等不同基础地址，避免页面代码到处判断运行环境。
- 落地登录、Token 恢复、门店选择/申请、总部/门店工作区切换、权限菜单和动态路由入口，让用户会话和业务工作区状态可恢复、可切换。
- 封装 Zustand session/users 状态、Axios 请求客户端、统一错误处理、权限快照和 i18n 文案边界，减少页面层重复状态和重复判断。
- 在 Figma Make 生成代码质量不稳定的现实约束下，把页面代码逐步收口到 Ant Design 与 `components/ui` 基础组件，沉淀 Dialog、Search、Table、Column Settings、CRUD Hook 等可复用能力。
- 坚持强契约开发：前端不靠猜字段、空兜底和静默 catch 掩盖接口问题，优先让协议错误暴露出来，再按真实契约修正。

### 荷叶问诊医药 SaaS 三端协同系统

**角色**：公司项目 / 核心前端开发
**技术栈**：Vue 3、TypeScript、Vite、Element Plus、Vant、uni-app、Pinia、Axios / luch-request、腾讯云 IM / TRTC、阿里云移动推送、Aegis。
**相关复盘**：[医疗问诊 SaaS 三端协同](/posts/medical-inquiry-saas-three-clients/)

#### 项目概述

该项目覆盖 PC 管理后台、跨端移动 APP 和问诊内核 H5。核心业务不是普通页面 CRUD，而是围绕互联网医院与药店问诊场景，把患者、医生、药师、商家、处方、审方、视频通话、移动推送和合规规则串成可用链路。

#### 核心亮点

- 后台端承接远程审方、药师工作台、处方记录、问诊数据、GSP 商品资料和合理用药规则配置，处理动态路由、租户 `tenant-id`、Token 刷新队列和全局错误提示。
- 移动端基于 uni-app 支持 H5、Android、iOS、微信小程序和鸿蒙配置，接入阿里云推送、腾讯 IM / TRTC，处理处方待审、视频来电、订单通知、权限申请和跨端页面跳转。
- 问诊内核 H5 使用 Vue 3 + Vant 承载患者问诊、医生接诊、药师审方、第三方问诊流转、商品提交、套餐购买和消息中心等移动端业务。
- 在第三方问诊链路中梳理详情拉取、合理用药审查、药品/诊断归一化、审查弹窗拦截和后续流转，避免把医疗规则判断散落在页面事件里。
- 排查过长处方/慢病仍提示超量的问题，定位到“慢病病情选择”和“后台慢病目录药品配置”是两层不同规则，问题根因不在前端状态，而在规则目录匹配。

### AI Make 本地 UIUX Patch Compiler

**角色**：个人项目 / 产品设计与独立开发 / Codex Skill + npm CLI
**技术栈**：Node.js、JavaScript ESM、Codex Skill、Prompt Engineering、React、TypeScript、Tailwind CSS、Multi-Agent Workflow。

#### 项目概述

AI Make 是我围绕 Figma Make 工作流沉淀的本地开发者 UI 生成 Skill。它不是网页 IDE，也不直接调用模型 API，而是把一句 UI 需求编译成 **visual brief、page composition blueprint、ui-spec、prompt-pack、agent handoff、任务拆分和 review gates**，再交给 Codex / Claude Code / Cursor 等本地编码 Agent 在现有项目里生成可审查、可验证、可合并的前端 patch。

#### 核心工作

- 设计从自然语言 UI 需求到本地代码 patch 的编译链路：先确定视觉方向和首屏结构，再生成规格、提示词包、Agent 交接文档和验证要求。
- 实现 `ai-make` CLI 与 Codex Skill 入口，支持读取目标项目上下文、生成运行目录、拆分任务、输出单任务 Agent prompt，并记录本轮 patch 的 review gate。
- 把视觉质量放在代码质量之前：通过 `visual-brief` 和 `page composition blueprint` 约束首屏框架、hero、指标节奏、证据区、行动区和细节层，避免生成“能跑但像模板”的页面。
- 强约束生成边界：不猜后端字段、不添加 fallback 字段、不绕过项目架构、不擅自引入新 UI 库、不生成巨大单文件页面。
- 支持本地多 Agent 协作思路，通过任务依赖和 write set 限定每个 Agent 的编辑范围，降低并行开发时的冲突和风格漂移。

---

## 技术文章 / 证明材料

- [从调 API 到 Agent 工程化：把 AI 能力做成可治理系统](/posts/ai-agent-engineering-practice/)
- [Agent 工程学习路线：从 LLM 到可上线智能体系统](/posts/understanding-ai-ecosystem/)
- [电商 AI 口播生成系统：OCR、Agent、TTS 与队列闭环](/posts/ecommerce-ai-script-generation/)
- [Webman 分层架构：Controller 到 Model 的边界治理](/posts/webman-layered-architecture/)
- [SSE 流式对话系统：AI 实时输出的生产级实现](/posts/sse-streaming-chat/)
- [医疗问诊 SaaS 三端协同：后台、移动端与问诊内核怎么串起来](/posts/medical-inquiry-saas-three-clients/)

---

## 教育经历

### 武汉文理学院 · 计算机科学与技术 · 本科

**毕业时间**：2026.06

---

## 我的优势

- **不是只会写页面**：能从页面走到接口、数据库、队列、权限、Agent、部署和桌面端。
- **不是只会调模型**：能把 LLM 接成 Agent 运行系统，考虑工具安全、运行审计、超时、取消和前端流式体验。
- **不是只会堆功能**：更关注模块边界、前后端契约、数据一致性和系统长期维护成本。
- **不是硬蹭 Python**：Python 在我的简历里承担的是 AI 应用、数据处理、自动化和工具链方向；PHP / TypeScript 是已验证的系统交付证据。

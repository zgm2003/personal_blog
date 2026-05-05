---
title: "Go Admin Core Foundation：从 PHP 系统迁移到 Gin Modular Monolith"
published: 2026-05-03T10:00:00Z
draft: false
tags: [置顶, Go, Gin, 架构, 后端, RBAC, WebSocket, Queue]
description: "复盘一个企业级 Admin 系统从 PHP/Webman 迁移到 Go/Gin 的真实落地过程：认证会话、RBAC、用户管理、操作日志、队列、上传、WebSocket、smoke 和测试体系如何一步步收口。"
category: 后端技术
---

> 这是一份 Go Admin core foundation 的落地复盘：一个已有企业级 Admin 系统在迁移到 Go/Gin 时，认证、会话、RBAC、用户管理、操作日志、队列、上传、WebSocket、测试和 smoke 如何形成一条可验证的工程链路。

# 写在前面：Go 不是魔法，是主后端工程能力

很多人谈 Go，喜欢先谈高并发、微服务、Kubernetes、gRPC。听起来热闹，但我这个项目遇到的真问题不是这些。我的真问题很具体：已经有一套 PHP / Webman 写出来并上线过的企业级 Admin 系统，里面有登录、Access / Refresh Token、Redis Session、动态菜单、按钮权限、AI Agent、SSE、WebSocket、支付、队列、通知、上传、审计日志、桌面端更新和线上部署。现在我要把它迁到 Go 主后端，但不能把已有前端、登录路径、菜单权限和业务使用方式砸烂。

这件事的重点不是 Go 语法。语法不难，难的是边界：哪些东西进 Go 主后端，哪些东西留给 Python AI 自动化，哪些只是 PHP 旧系统里的业务事实，哪些历史包袱不能带进新架构。更难的是节奏：如果一上来重做数据库、重做 RBAC、重做前端权限、重做 UI、重做接口命名，那不是重构，是把一个能跑的系统拆成半成品。

所以我给这个项目定了三条硬问题：

```text
1. 这是个真问题吗？
2. 有更简单的做法吗？
3. 会破坏已有前端、登录、菜单和权限吗？
```

答案很清楚：真问题是后台系统边界变重，旧 PHP 继续堆功能会越来越难维护；更简单的做法不是微服务，而是 Gin modular monolith；不能破坏用户空间，所以旧接口和旧前端路径必须被显式 adapter 保护，而不是被新架构“教育”。

# 为什么主后端选 Go，Python 和 PHP 放在正确位置

PHP / Webman / Workerman 在旧系统里已经承接过接口、队列、SSE、WebSocket、支付回调、存储和后台任务，也提供了完整的业务语义来源。问题是长期维护不能继续被旧项目的历史风格牵着走：路由风格、命名习惯、历史兼容和分层包袱都会越来越重。

Python 也很重要，但它的位置不是拿来替代整个 Admin 主后端。Python 的强项在 AI 应用、RAG、OCR、TTS、embedding、批量数据处理、自动化脚本、模型评估和内容流水线。把 Python 当 AI sidecar / automation layer 是合理的；让 Python 去承接整个 Admin 的认证、会话、RBAC、菜单、审计、支付和长期 HTTP 服务，不是当前最优解。

Go 的位置最清楚：它适合长期运行的后台服务。单二进制部署干净；标准库对 HTTP、context、并发和测试支持强；类型系统能让接口契约更早暴露问题；goroutine 适合队列、WebSocket、后台任务和并发 I/O；简单语法逼你少搞抽象。真正写 Go 项目，不是把 Java 设计模式搬过来，而是把调用链收短，把错误显式返回，把资源生命周期讲清楚。

因此我的技术分工是：

```text
Go      -> Admin 主后端：REST API / auth / session / RBAC / queue / upload / realtime
Python  -> AI 应用与自动化：采集 / 清洗 / OCR / TTS / 模型调用 / 评估 / 脚本流水线
PHP     -> 已上线业务事实：存量系统、迁移参考、业务语义来源
前端    -> 强交付层：Vue / React / uni-app / Electron / Tauri / 权限菜单 / UI 工程
```

关键不是把所有技术混在一起，而是让每个技术栈只承担它最适合的职责。

# 当前项目状态：已经不是 skeleton

当前 Go 项目已经进入 **Admin core foundation** 阶段，不是刚起一个 Gin skeleton。

当前 Go 后端已经落地的模块包括：

```text
auth
session
authplatform
captcha
user
permission
role
operationlog
queuemonitor
systemsetting
systemlog
uploadconfig
uploadtoken
realtime
```

当前已经形成闭环的能力包括：

```text
health / ready
登录配置
滑块验证码
密码 / 验证码登录
Access / Refresh Token
Token Hash + Pepper
Redis token cache
MySQL session fallback
平台认证策略
设备 / IP / 单端登录策略
Users/init RBAC bootstrap
permission definitions REST
role grant / restore
用户管理 REST
个人资料 / 账号安全
系统日志
操作日志
Asynq queue monitor
系统设置
上传配置
COS 上传 token
WebSocket baseline
basic-admin-smoke
full-admin-smoke
```

当前代码规模已经能反映工程密度：本地仓库约 `229` 个 Go 文件、`70` 个测试文件、`365` 个测试函数；`go test ./...`、`go vet -p=1 ./...`、`git diff --check` 已经通过。这些数字只说明一件事：这套 Go 后端已经进入“能被验证、能继续迁移”的状态。

# 架构选择：Gin Modular Monolith，而不是微服务

我采用的顶层结构是：

```text
cmd -> bootstrap -> server -> module -> platform
```

模块内部默认是：

```text
route -> handler -> service -> repository -> model
```

这个结构不新奇，但它解决实际问题。`cmd/admin-api` 只启动 HTTP API；`cmd/admin-worker` 只跑队列消费和 scheduler；`bootstrap` 装配 config、logger、resources、service、middleware 和 router；`server` 负责 Gin engine、全局 middleware 和路由挂载；`internal/module` 放业务模块；`internal/platform` 放数据库、Redis、队列、调度、存储、WebSocket 等外部资源边界。

为什么不一开始微服务？因为当前真问题是迁移 Admin 核心链路，不是给每个模块单独起进程。微服务不是架构成熟的象征，它是组织、部署、监控、网络、数据一致性和故障隔离都准备好之后的结果。现在先用 modular monolith 把 auth、RBAC、operationlog、queue、storage、realtime、AI workflow 的边界写清楚，未来要拆也有路可走。

好架构不是层数多，而是特殊情况少。没有数据库的模块不硬造 repository；没有表的模块不硬造 model；没有两个真实实现的地方不硬造 interface；没有业务任务时不写 fake cron。少一层是一层，少一个特殊情况就是进步。

# 认证会话：不是套一个 JWT middleware 就完事

这个系统不是纯 JWT stateless auth。旧系统已经有 token hash、Redis session、MySQL session、平台策略、设备绑定、IP 绑定、单端登录和 refresh token 语义。Go 迁移不能把这些事实抹掉。

当前 session/auth 链路做了这些事：

```text
access token / refresh token 生成
sha256(token + pepper) hash
Redis token cache
MySQL user_sessions fallback
session.platform 作为可信 platform
access_ttl / refresh_ttl 从 auth_platforms 读取
refresh rotation
logout revoke
single_session / max_sessions
bind_platform / bind_device / bind_ip
登录日志 task
```

`AuthToken` middleware 只做认证边界：解析 `Authorization: Bearer <token>`，读取 platform / device-id / client-ip，调用 authenticator，拿到 `AuthIdentity` 后挂到 Gin context。它不生成 token，不查业务权限，不判断 RBAC，不处理验证码。这些东西都在 service 层，不能塞进 middleware。

这里有个细节：浏览器 WebSocket 和队列监控 iframe 这类入口不能稳定附加 `Authorization` header，所以我做了 **path-scoped cookie token**。只允许 `GET/HEAD /api/admin/v1/queue-monitor-ui/*` 和 `GET /api/admin/v1/realtime/ws` 从 `access_token` cookie 取 token；普通 JSON API 不允许 cookie fallback，POST/PUT/PATCH/DELETE 也不允许。这是显式边界，不是全局兜底。

# RBAC：Admin 系统的硬骨头

RBAC 是 Admin 的核心，不是三张表那么简单。它同时影响菜单、路由、按钮、接口权限、缓存、前端动态路由和审计。

当前 Go 版本保留旧系统已经验证过的语义：

```text
users.role_id 单角色模型
permissions: DIR / PAGE / BUTTON
role_permissions: PAGE / BUTTON 授权
BUTTON 授权隐含父 PAGE
Users/init 返回 permissions + router + buttonCodes + quick_entry
show_menu 只控制菜单显示，不代表无页面权限
button cache 只做性能加速，不做权限真相源
PermissionCheck fail-closed
权限/角色变更后清理受影响用户 button grant cache
```

为什么第一阶段不做多角色？因为多角色不是免费的。它会改变授权合并、冲突处理、审计解释、前端展示和缓存失效逻辑。当前业务事实是单角色，那就先把单角色迁稳。以后要做多角色，应该在边界清楚后演进，而不是迁移第一阶段顺手改语义。

`PermissionCheck` 不靠反射、注解或 handler 名字猜权限码。只有显式 route metadata 配了规则，才检查。用户不存在、角色不存在、权限数据异常，全部 fail-closed。缓存 miss 或 Redis error 必须回源计算，不能把缓存当成权限真相源。

这才是 RBAC 的重点：菜单是菜单，页面权限是页面权限，按钮权限是按钮权限，接口权限是接口权限，缓存是缓存，数据库事实是数据库事实。混在一起就会烂。

# 用户管理、个人资料和账号安全：别把业务塞错模块

用户管理不是简单列表。当前 Go REST 已经覆盖：

```text
GET    /api/admin/v1/users/page-init
GET    /api/admin/v1/users
PUT    /api/admin/v1/users/:id
PATCH  /api/admin/v1/users/:id/status
PATCH  /api/admin/v1/users
DELETE /api/admin/v1/users/:id
DELETE /api/admin/v1/users
```

个人资料和账号安全没有另起一个空模块，而是归在 `user` 模块，因为表事实就是 `users` 和 `user_profiles`：

```text
GET /api/admin/v1/profile
GET /api/admin/v1/users/:id/profile
PUT /api/admin/v1/profile
PUT /api/admin/v1/profile/security/password
PUT /api/admin/v1/profile/security/email
PUT /api/admin/v1/profile/security/phone
```

这里的边界很重要：用户编辑自己的资料，不应该挂用户管理按钮权限；它只需要登录态，并记录 `profile.update_profile` 操作日志。账号安全写操作复用验证码 store，但不让 handler 或 repository 直接碰 Redis。GET profile 不偷偷创建缺失 profile 行，读接口不能暗中写库。

这些细节看起来小，但能看出代码品味。坏代码喜欢为了“方便”新开模块、偷偷写库、顺手兜底字段。好代码先问：这个业务事实到底归谁？读路径能不能保持只读？权限是不是刚好够用？

# 操作日志：显式 metadata，不靠猜

操作日志不是 access log。access log 记录 HTTP 横切信息；operation log 记录后台用户做了什么业务操作。

当前 Go 版本用显式 route metadata 维护操作日志规则：

```text
method + route pattern -> module / action / title
```

比如新增权限、编辑角色、删除操作日志、编辑个人资料、修改登录密码、签发上传凭证等，都通过显式规则记录。middleware 在 handler 执行后拿到 status、success、latency、request_id、user_id、session_id、platform、client_ip，再写入 repository。

敏感字段必须被 sanitizer 遮蔽，验证码坐标、密码、token、secret 不允许进审计日志。日志记录失败不应该打断普通业务主流程，但高风险操作如果未来要求强审计，那应该作为单独业务规则设计，而不是在通用 middleware 里偷偷改变语义。

# 队列和 worker：API 不消费任务，scheduler 不直接跑业务

Go 后端当前采用单体多进程，而不是微服务：

```text
cmd/admin-api     # HTTP API
cmd/admin-worker  # queue consumer + scheduler
```

队列使用 Asynq，scheduler 使用 gocron/v2，但业务模块不直接到处 import asynq/gocron。底层封装在：

```text
internal/platform/taskqueue
internal/platform/scheduler
internal/jobs
```

队列 lane 分为：

```text
critical
default
low
```

这不是按目录建 `fast/slow`。快慢是运行时策略，不是业务所有权。登录日志、权限缓存刷新这类短任务走 critical；普通业务走 default；慢任务、批量任务、AI 后处理以后走 low。scheduler 只能投递 queue task，不直接执行业务。worker handler 必须幂等，因为队列语义是 at-least-once。

当前已经有 `auth:login-log:v1` 和 `system:no-op:v1` 这样的版本化 task，queue monitor 采用 Asynq 官方 `asynqmon` 只读挂载，而不是重新手写一个半吊子 dashboard。这个取舍很现实：能用成熟生态就用，但要包在项目自己的边界里。

# 上传：配置是配置，运行时 token 是运行时 token

上传是很容易写烂的地方。很多系统会先做一个“上传中心”，然后倒推各种 scene，最后一堆无主文件记录没人知道归谁。我这里反过来：上传 token 只签发临时凭证，不定义业务；真正业务模块自己保存 object key/url、状态、权限和操作日志。

当前 Go 版本拆成两块：

```text
uploadconfig  -> 管理 upload drivers / rules / settings
uploadtoken   -> 读取 enabled setting，签发 COS 临时凭证
```

配置管理支持 cos/oss 记录，是因为存量数据可能有两种配置；但运行时默认只实现 COS-first token。OSS runtime 没实现就显式报错，不静默 fallback。

关键规则包括：

```text
driver secret 使用 VAULT_KEY + AES-GCM secretbox 加密
secret 永不返回明文或密文，只返回 hint
setting 启用互斥在 repository transaction 内完成
folder/file_name/file_size/file_kind 双层校验
object key 服务端生成
rule.max_size_mb / image_exts / file_exts 是上传限制真相
COS_STS_ENABLED=false 时显式报未启用
```

这比“调个 SDK 上传文件”更重要。上传不是 SDK 问题，是权限、配置、密钥、规则、业务归属和安全边界问题。

# WebSocket baseline：先把连接生命周期打稳

Realtime 当前只做基建，不假装业务通知和 AI streaming 已经完成。当前已经实现：

```text
GET /api/admin/v1/realtime/ws
Authorization bearer 优先
浏览器 path-scoped cookie auth
local connection manager
bounded send queue
read pump / write pump
server ping control frame
client ping -> server pong envelope
connected event
topic subscribe 白名单骨架
local / noop Publisher
REALTIME_ENABLED=false 明确 503
unknown publisher 明确 down，不假装 Redis fan-out
```

这里最重要的是生命周期。WebSocket 不能让业务代码直接拿 conn 到处写。当前 `Session` 拥有一个 bounded send queue，所有输出都经过队列串行化；队列满了说明 slow client，直接关闭连接，不能让内存无限涨。read pump / write pump 通过 context 和 done channel 退出，App shutdown 会关闭本机 manager 下的连接。

AI streaming 未来可以走 WebSocket，但现在不写假实现。Redis Pub/Sub / Redis Streams fan-out 也还没实现，所以配置成 redis publisher 时 readiness 必须 down。没做就是没做，别把 planned 写成 implemented。

# 前端边界：迁移不能只看后端

这个 Go 项目不是后端单边改造。迁移能成功，前端工程也必须跟上。现有前端要处理登录恢复、权限菜单、动态路由、按钮权限、请求封装、401 刷新队列、WebSocket URL 切换、iframe queue monitor、上传 client、个人资料和账号安全页面适配。

前端侧涉及的技术和交付边界包括：

```text
Vue 3 / React / TypeScript / Vite
Element Plus / Ant Design / Vant / Tailwind
Pinia / Zustand / React Query
动态路由 / 权限菜单 / 按钮权限
uni-app 移动端 / H5 / 小程序 / Android / iOS / 鸿蒙配置
腾讯 IM / TRTC / 移动推送
Electron / Tauri 桌面端
Capacitor 跨端壳层思路
Figma Make / AI UI 生成代码收口
```

后端迁移如果不了解前端真实消费顺序，很容易把接口改得“理论正确、实际不可用”。权限状态怎么恢复、接口契约在哪里会炸、哪些 fallback 会掩盖后端错误，这些都必须在迁移时一起处理。前端不是附属品，它是验证 Go 后端契约是否稳定的第一现场。

# Python 边界：AI 自动化和内容流水线

Python 不抢 Go 主后端的位置，但在 AI 应用和自动化链路里非常关键。

例如电商 AI 内容流水线：

```text
商品采集
图片 / OCR
商品数据清洗
卖点提取
AI 口播生成
TTS 合成
SRT 字幕
批量文件处理
接口调试与回放
AI 工具链验证
```

这些任务天然适合 Python。Web 后台负责权限、状态、任务流和人工审核；Go/PHP 后端负责主业务和持久化；Python 负责自动化、数据处理和模型生态。硬把 Python 写成一个普通 CRUD 服务没有意义；把 Python 放进 AI 工作流和自动化链路里，价值更明确。

# 测试和 smoke：没有验证，不叫完成

迁移项目最怕“看起来能跑”。所以我给 Go 项目建立了测试和 smoke 门禁。

单元测试覆盖 handler、service、middleware、platform wrapper 和核心业务规则。service 层用 fake repository 做 table-driven tests；handler 层用 `httptest` 验证 HTTP 契约；middleware 验证 AuthToken / PermissionCheck / OperationLog 的 fail-closed 和执行顺序；platform 层验证 taskqueue / scheduler / realtime / secretbox / COS signer 边界。

smoke 分两层：

```text
basic-admin-smoke.ps1
full-admin-smoke.ps1
```

basic smoke 证明基础 admin 链路没断：`/ready`、login config、captcha、login、users/me、users/init、users page-init/list、permission + role RBAC loop、logout、WebSocket connect/ping/pong。

full smoke 在 basic 基础上探测 operation log、queue monitor、system logs、system settings、upload config、upload token shape、profile/account security 等更慢模块。写库 smoke 必须用临时数据，成功后清理，失败保留 `.tmp` 日志。

当前我已经验证过：

```powershell
go test ./...
go vet -p=1 ./...
git diff --check
```

这才是迁移项目该有的态度：没有验证证据，不准说完成。

# 当前边界：已经落地的和还没落地的

到目前为止，这个 Go 后端已经完成的是 Admin core foundation，而不是完整业务迁移。这个边界必须说清楚。

已经落地的部分，是认证、会话、RBAC、用户管理、系统设置、系统日志、操作日志、队列监控、上传配置、COS 上传 token 和 WebSocket baseline。这些能力共同构成后台系统继续迁移的地基。

还没有落地的部分，也不能假装完成。真实业务模块还没有批量迁移，短信/邮件发送器还只是 dev-mode 边界，AI streaming 还没有接入 WebSocket，Redis fan-out 也还没有实现。上传现在是 COS-first runtime token，不是完整文件管理系统，也不是 OSS runtime。

这个阶段的目标不是“把所有功能一次写完”，而是先把系统最容易出事故的基础链路固定住：登录不能乱，权限不能乱，缓存不能变成真相源，队列不能和 API 进程搅在一起，上传密钥不能明文暴露，WebSocket 不能无边界写连接，测试和 smoke 不能缺席。

# 结尾：真正的升级，是边界变清楚

Go 项目最容易写成两种垃圾：一种是披着 Go 外衣的 Java 项目，目录复杂、interface 泛滥、ServiceImpl 到处飞；另一种是脚本式 Go，所有逻辑塞 handler，数据库、权限、缓存、响应混在一起。前者假装专业，后者假装快速，最后都会难维护。

我想要的是第三种：少层级、少抽象、先跑通、再提炼。先保护已有用户路径，再替换内部实现；先把认证和 RBAC 打稳，再迁业务模块；先用 tests 和 smoke 证明契约，再谈优化；先保持 modular monolith，再决定未来是否拆服务。

这就是我对 Go 主后端的理解：Go 的强项不是让你写更多框架，而是逼你把事情说清楚。一个好的 Admin 后端，不应该靠魔法、兜底和猜测运行。它应该让每个请求从进入系统到返回结果都能被解释，让每个权限判断都有来源，让每个错误都能暴露，让每个迁移步骤都能验证。做到这些，Go 才不是口号，而是真正能承接业务系统的工程能力。

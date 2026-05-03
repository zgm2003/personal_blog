---
title: "Go 语言与 Admin 架构设计：从 PHP 系统迁移到 Gin Modular Monolith"
published: 2026-05-03T10:00:00Z
draft: false
tags: [置顶, Go, Gin, 架构, 后端, RBAC]
description: "复盘一个企业级 Admin 系统从 PHP/Webman 迁移到 Go/Gin 的架构取舍：为什么先做 modular monolith，如何设计模块边界、认证会话、RBAC、中间件、legacy adapter 和渐进迁移路径。"
category: 后端技术
---

> **本文价值**：这篇文章不是“Go 语法学习笔记”，也不是为了显得高级而硬写微服务。它记录的是一个已有 Admin 系统迁移到 Go 时，怎样把技术选择、模块边界、认证会话、RBAC、接口契约、中间件、缓存和测试放到同一条可落地的工程链路里。

# 写在前面：Go 不是魔法，架构也不是 PPT

很多人谈 Go，喜欢先谈高并发、云原生、微服务、Kubernetes、gRPC。听起来很热闹，但这不是我这个项目真正遇到的问题。我的真实问题很朴素：已经有一套 PHP / Webman 写出来的企业级 Admin 系统，里面有用户登录、Access / Refresh Token、Redis Session、动态菜单、按钮权限、AI Agent、SSE、WebSocket、支付、队列、通知、上传存储、审计日志、桌面端更新和线上部署。现在我要把它迁移到 Go 后端，但不能把已有前端、已有登录路径、已有权限语义和已有业务使用方式砸烂。

这件事的核心不是“会不会写 Go 语法”。语法一周就能上手，难的是边界：什么东西应该进入 Go 主后端，什么东西应该留给 Python AI sidecar，什么东西只是旧 PHP 的业务事实，什么东西不能带进新架构。更难的是迁移节奏：如果一上来就重做数据库、重做 RBAC、重做前端权限、重做 UI、重做接口命名，那不是架构升级，是把一个能跑的系统拆成一堆半成品。

所以我做这个 Go 项目时，先给自己定了三条问题。第一，这是不是一个真实问题？如果只是为了简历好看而重写，那就是浪费时间。第二，有没有更简单的做法？能用一个 Gin modular monolith 解决，就不要上来拆十个服务。第三，会破坏什么？如果一个新后端让现有前端登录不了、菜单不显示、按钮权限错乱，那这个 Go 项目再“理论正确”也是垃圾。

# 为什么主后端选 Go，而不是继续 PHP 或全换 Python

PHP 在这个系统里不是废物。旧系统能上线，说明 PHP / Webman / Workerman 这一套已经证明过业务价值。它承接过接口、队列、SSE、WebSocket、支付回调、存储和后台任务。问题在于，随着系统边界变大，PHP 项目里积累的历史兼容、路由风格、命名习惯和业务分层会越来越重。继续在旧项目里叠代码，短期最快，长期会把所有迁移成本都藏到未来。

Python 也不是不能做后端，但在这个项目里，Python 的强项不是拿来重写 Admin 主后端。Python 更适合 AI 工具链、RAG、embedding、模型适配、批量数据处理、自动化脚本和评估流程。把 Python 当成 AI sidecar 是合理的；把 Python 拿来承接整个 Admin 权限、会话、菜单、审计、支付、队列和长期 HTTP 服务，不是不能做，而是对这个项目没有最强性价比。

Go 的位置更清楚：它适合长期运行的后台服务。它编译成单二进制，部署干净；标准库对 HTTP、context、并发和测试支持很好；类型系统比动态语言更容易让接口契约暴露问题；goroutine 和 channel 适合处理 SSE、队列消费者、后台任务、超时取消和并发 I/O；同时 Go 的简单语法逼迫你少搞抽象。真正写 Go 项目时，最重要的不是把所有设计模式搬进来，而是把调用链收短，把错误显式返回，把资源生命周期讲清楚。

因此我的技术分工是：Go 做主 Admin 后端，负责 REST API、认证会话、RBAC、审计日志、队列入口、SSE / WebSocket 边界和长期运行服务；Python 只在模型生态、数据处理和 AI 工具链更强的地方出现；旧 PHP 只提供业务事实和迁移参考，不再决定新架构的目录、命名和接口风格。

# 真问题：这不是 CRUD Demo，而是已有 Admin 的迁移

一个新项目最容易犯的错，是把真实系统当成 CRUD Demo。CRUD Demo 只需要用户表、角色表、权限表，然后随便生成一套页面。真实 Admin 系统不是这样。真实系统的登录会涉及平台、设备、IP、单端登录、Refresh Token、会话过期、Redis 状态、数据库状态和前端恢复。真实权限会涉及菜单树、路由、按钮权限码、角色授权、缓存、缓存失效、超级管理员、隐藏菜单和页面访问权限之间的区别。真实迁移还要考虑旧接口是否仍被前端调用、旧返回结构是否要兼容、新接口是否要保持 RESTful、错误响应是否会被前端吞掉。

所以这个 Go 项目第一步不是写代码，而是明确迁移边界。旧 PHP 的路由风格不能直接搬进 Go。旧系统里的业务语义要保留，比如单角色模型、`DIR / PAGE / BUTTON` 三类权限、`Users/init` 返回的 router / permissions / buttonCodes、按钮缓存 key 的语义、`show_menu` 只控制菜单显示而不代表无页面权限。保留这些语义，是为了不破坏用户空间；但新 Go 模块内部不能继续被旧的 POST 动词接口污染。

这就是迁移项目和新项目的差别。新项目可以拍脑袋定接口，迁移项目不行。迁移项目必须承认用户已经存在，前端已经存在，接口调用顺序已经存在，权限数据已经存在。新后端的职责不是教育前端“你应该按我的新标准改”，而是在保证旧路径不被破坏的前提下，把内部实现逐步换成更清楚、更少特殊情况的结构。

# 架构选择：Gin Modular Monolith，而不是微服务

我最终采用的形态是 Gin modular monolith。顶层调用链是：

```text
cmd -> bootstrap -> server -> module -> platform
```

业务模块内部默认是：

```text
route -> handler -> service -> repository -> model
```

这个结构看起来普通，但它解决的是实际问题。`cmd/admin-api/main.go` 只负责读取配置、创建 logger、装配应用并启动进程。`bootstrap` 负责把 config、database、redis、service、middleware 和 router 装起来。`server` 负责 Gin engine、全局 middleware 和路由挂载。`internal/module` 放业务模块，比如 auth、session、authplatform、user、permission、role、operationlog、system。`internal/platform` 放外部资源，比如 MySQL、Redis、队列、存储、AI client。这样切开以后，谁负责什么非常明确。

为什么不一开始微服务？因为微服务不是架构成熟的象征，微服务是组织、部署、监控、网络、数据一致性和故障隔离都准备好之后的结果。当前这个系统最真实的问题是迁移 Admin 核心链路，不是给每个模块单独起进程。把 auth、RBAC、operationlog、AI workflow、notification、storage 未来可拆的边界先设计出来就够了。等某个边界真的有独立扩缩容、独立团队、独立数据或独立故障域需求，再拆。现在把它们硬拆出去，只会制造跨服务调用、分布式事务、链路追踪和部署复杂度。

这个决策的好处是简单。一个 Go 进程，一个 Gin HTTP API，一套清楚的模块边界，一套可测试的契约。模块边界按未来可拆服务设计，但运行形态先保持单体。这样既不阻碍未来演进，也不为今天不存在的问题付账。

# 目录不是摆设：每一层都必须有真实职责

很多项目的目录看起来很专业，实际全是噪音：controller、service、serviceImpl、manager、factory、bo、vo、converter、assembler，一层又一层，最后一个字段改名要穿十几个文件。这种东西不是架构，是 Java 味垃圾。Go 项目尤其不能这样写。

我的规则很硬：模块内部最多保留这些文件：`route.go`、`handler.go`、`service.go`、`repository.go`、`model.go`、`dto.go`、`errors.go`。但这不是要求每个模块必须有七个文件。没有数据库就没有 repository，没有表就没有 model，没有复杂请求结构就不需要 dto。少一层是一层。目录存在的前提，是它能消掉特殊情况，而不是制造仪式感。

`route.go` 只注册路由，只绑定 handler。它不应该决定业务，不应该查库，不应该拼响应。`handler.go` 只处理 HTTP 边界：解析请求、取 path/query/body/header、调用 service、把 app error 映射成 response。`service.go` 承载业务规则，但不能依赖 `gin.Context`。一旦 service 引入 `gin.Context`，这个 service 就被 HTTP 框架绑死，测试、复用和未来拆分都会变差。`repository.go` 做数据访问，不写业务分支。`model.go` 只放数据库映射，不写业务方法。这个边界简单粗暴，但很有效。

例如登录链路里，handler 可以读取请求体和 header，但真正判断平台策略、会话有效期、Token hash、单端登录、refresh rotation 的逻辑必须进入 service。repository 只知道怎么查 `users`、`sessions`、`auth_platforms`，不应该知道“是否允许登录”这种业务结论。这样做的价值不是为了好看，而是当登录规则变化时，我知道该改哪里；当数据库字段变化时，我知道不会污染 HTTP 层；当前端接口有问题时，我知道不会到处搜一堆散落逻辑。

# 接口契约：新世界 RESTful，旧世界显式 adapter

迁移项目里最容易产生坏味道的地方就是接口。为了省事，很多人会让后端同时接受 `id`、`ids`、`permission_id`、`permissionIds`，返回时也同时给 `user_id`、`userId`、`id`，前端再用 `?? []`、`?? {}`、`as any` 一路吞掉。短期看是兼容，长期看是把错误数据放进系统，让每个调用方都猜字段。

我在 Go 项目里把规则定死：新接口统一走 `/api/v1/<resource>`，方法语义固定。查询用 GET，创建用 POST，整体更新用 PUT，局部状态变化用 PATCH，删除用 DELETE。不要继续写 `/api/admin/Permission/list` 这种全 POST 动词接口，也不要把 `/add`、`/edit`、`/del` 塞进 URL。接口不是页面按钮的翻译，接口是资源和状态变化的契约。

但是迁移期不能装瞎。旧前端可能还在调 `/api/Users/init`、`/api/Users/login`、`/api/Users/refresh`、`/api/admin/Permission/list`。这些路径可以保留，但必须叫 legacy adapter。它们的调用链应该是：

```text
legacy route adapter -> module service -> repository
```

adapter 只负责把旧请求翻译成内部服务需要的输入，把内部服务输出翻译成旧前端仍能识别的响应。它不能污染 service，也不能让新模块内部继续按旧接口命名。这样迁移期就有两条清晰路线：旧路径不破坏，新路径按 RESTful 演进。

统一响应也要固定：

```json
{
  "code": 0,
  "data": {},
  "msg": "ok"
}
```

这不是说所有错误都返回 200。HTTP status 和业务 code 都要明确。handler 不应该随手拼错误文本，service 应该返回结构化 app error，response 层负责映射。真正的契约不是“前端能凑合显示”，而是成功、失败、未登录、无权限、参数错误、系统错误都有稳定表达。

# RBAC：保留业务语义，不照搬旧实现

RBAC 是 Admin 系统的核心，也是最容易被写烂的地方。看起来只是用户、角色、权限三张表，实际涉及菜单、路由、按钮、接口、缓存、前端动态路由和审计日志。我的 Go 项目第一阶段不追求“最完美 RBAC”，而是保留当前系统已经验证过的语义，再把实现边界理顺。

当前基线是单角色模型：`users.role_id`。第一阶段不改多角色。为什么？因为多角色不是免费的。它会改变授权合并、冲突处理、前端展示、审计解释和缓存失效逻辑。如果当前业务没有真实多角色需求，就不要为了显得完整把系统复杂度翻倍。以后要做多角色，可以在边界清楚后演进，但不应该在迁移第一阶段顺手改语义。

权限类型保留 `DIR / PAGE / BUTTON`。`DIR` 是目录，`PAGE` 是页面，`BUTTON` 是按钮。角色授权时，`DIR` 不直接授权，`PAGE` 授权，`BUTTON` 授权并隐含父 PAGE。`Users/init` 必须继续返回前端需要的 `permissions`、`router`、`buttonCodes`、`quick_entry`。`show_menu` 只控制菜单显示，不代表没有页面权限。这个细节很关键：一个页面可以不在菜单出现，但仍然可以通过路由进入；如果把菜单显示和页面访问混在一起，前端路由和权限判断就会错。

权限检查必须 fail-closed。用户不存在、角色不存在、权限数据异常时，默认拒绝，不允许绕过。缓存也不能成为权限真相源。按钮授权 cache 只做性能加速，cache miss 或 Redis error 时必须回源计算。角色或权限变更后，要清理受影响用户的 button grant cache。否则权限看起来改了，实际用户还拿着旧授权，这就是安全和业务一致性问题。

这里的重点不是“我设计了一个多复杂的权限系统”，而是我没有让特殊情况散落在代码里。菜单是菜单，页面权限是页面权限，按钮权限是按钮权限，API 权限是 API 权限，缓存是缓存，数据库事实是数据库事实。边界越清楚，bug 越少。

# Middleware 顺序：不要让认证、权限和审计互相踩脚

Gin 的 middleware 看起来简单，但顺序错了，系统就会出现很隐蔽的问题。我的目标顺序是：

```text
Recovery
RequestID
AccessLog
CORS
AuthToken
PermissionCheck
OperationLog
Handler
```

`Recovery` 放最前面，保证 panic 不会直接打爆进程。`RequestID` 尽早生成，让后续日志都能串起来。`AccessLog` 记录请求基本信息。`CORS` 在认证之前处理跨域和 OPTIONS，避免预检请求被鉴权拦掉。`AuthToken` 负责解析 Bearer Token，读取 platform、device-id、client IP，校验 session，并把 `AuthIdentity` 放进 context。`PermissionCheck` 在有身份之后执行，按显式 route rule 判断需要哪个权限码。`OperationLog` 包住 handler，等 handler 执行完后记录状态、耗时、用户、平台、模块和动作。

这里有两个细节必须坚持。第一，PermissionCheck 不靠反射、注解或 handler 名字猜权限码。只有显式 route metadata 配置了规则，才检查。没有规则就不拦截，不记录。这不是放松安全，而是避免“猜测式权限”。权限规则必须明确写出来，才能被审查、测试和迁移。第二，OperationLog 不应该影响主流程。审计记录失败可以打 warning，但不能让一个已经成功的业务操作因为日志写入失败变成失败。当然，如果某些高风险操作要求审计强一致，那要作为业务规则单独设计，而不是在通用 middleware 里偷偷改变语义。

这套顺序的价值在于可推理。一个请求从进来到出去，身份在哪里生成，权限在哪里检查，日志在哪里记录，错误在哪里映射，都能说清楚。架构不是画图，架构是线上出问题时你能不能立刻知道该看哪一层。

# 配置和资源：bootstrap 负责装配，不让业务到处初始化

Go 项目里另一个常见坏味道，是业务代码到处读取环境变量、到处打开数据库、到处创建 Redis client。短期方便，长期必烂。我的做法是把资源装配收口到 bootstrap 和 platform。

`config` 负责读取环境变量和默认值。HTTP 地址、read header timeout、MySQL DSN、连接池大小、Redis 地址、CORS 配置都应该在配置层明确。`platform/database` 负责打开 GORM 和底层 `sql.DB`，设置最大连接数、空闲连接数和连接生命周期，并提供 `Ping(ctx)` 和 `Close()`。`platform/redis` 同理，负责创建 client、ping、close。业务模块拿到的是已经装配好的 repository 或 service，不应该自己知道 DSN 从哪里来。

`bootstrap.New` 的职责是装配依赖：打开资源，创建 session authenticator，创建 authplatform service，创建 auth service，创建 permission service，创建 role service，创建 operation recorder，最后把这些交给 `server.NewRouter`。这就是 Go 项目的依赖注入。它不需要上复杂 DI 框架，也不需要反射容器。显式 new，显式传参，出错就显式处理。Go 的好处就在这里：简单代码比“高级框架”更容易审查。

优雅关闭也不能忘。HTTP server shutdown 需要 context timeout，资源关闭需要合并错误。后台任务、队列消费者、SSE 连接以后接入时，也必须挂在 context 生命周期下。Go 的并发能力强，但前提是每个 goroutine 都有退出路径。没有生命周期管理的 goroutine 不是并发，是泄漏。

# 错误处理：不要用空对象掩盖问题

我很讨厌一种写法：后端错了，前端拿 `?? []` 兜底；接口缺字段，前端补默认值；数据库查询失败，后端返回空列表；权限数据异常，后端当作没权限或者干脆放过。这种代码短期让页面“不报错”，长期会让系统失去真相。

Go 里错误必须显式处理。repository 返回底层 error，service 把它包装成 app error，handler 映射成 HTTP response。包装错误时要保留原始错误，比如 `fmt.Errorf("query user: %w", err)` 这种模式。这样日志里既有业务语义，也有底层原因。不能在 service 里直接 `c.JSON`，也不能在 repository 里返回 HTTP 状态码。每一层只做自己的事。

统一 app error 的好处是，业务错误和系统错误不混。参数错误是 400，未登录是 401，无权限是 403，资源不存在是 404，系统异常是 500。前端看到错误时，不需要猜是网络错、业务错还是权限错。更重要的是，错误不会被静默吞掉。迁移期最怕的不是报错，最怕的是错误被兜底吞掉，最后数据错了还没人知道。

这也是我在前端适配里坚持的原则：API 层可以做契约翻译，但不能做字段猜测层。旧接口适配可以有，但必须有名字、有边界、有删除计划。无边界 fallback 就是垃圾代码。

# Go 的 interface：少用，但用在刀刃上

Go 新手容易走两个极端。一个极端是完全不用 interface，所有依赖都写死，测试和替换困难。另一个极端是每个 struct 都配一个 interface，再来一套 ServiceImpl，这就变成 Java。我的规则是：真实有多个实现，或者需要隔离外部系统时，才定义 interface。

例如 permission service 依赖 repository，这是合理的，因为 repository 隔离了数据库。auth service 依赖 session authenticator，也是合理的，因为认证逻辑可以在测试里替换。operationlog middleware 依赖 OperationRecorder，也是合理的，因为日志记录是外部副作用，失败策略需要隔离。但如果一个模块只有一个 service，没有替代实现，也没有跨边界需求，就不要为了“规范”硬造 interface。

Go 更推荐小接口。不要定义一个包含二十个方法的 `UserServiceInterface`。调用方需要什么，就接受什么。例如某个 handler 只需要 `Login` 和 `Refresh`，那它的依赖接口就只放这两个方法。这样测试替身简单，真实实现也不会被无关方法污染。

`accept interfaces, return structs` 这条经验很有用。构造函数返回具体结构体，调用方依赖最小接口。这样既保留实现能力，也降低耦合。接口不是为了“抽象看起来高级”，接口是为了让依赖方向更干净，让外部系统更容易替换，让测试更容易写。

# 并发设计：不要到处 goroutine，先定义生命周期

Go 的 goroutine 很便宜，但不是免费。很多人一写 Go 就到处 `go func()`，最后没有 cancel、没有 wait、没有错误传播、没有 panic recovery。这样的并发代码上线后很难查。我的原则是：只有真实异步需求才用 goroutine，而且每个 goroutine 必须知道什么时候退出，错误怎么返回，资源怎么关闭。

在 Admin 系统里，真实需要并发的地方很多，但不是每个 HTTP handler 都需要并发。SSE 流式输出需要处理客户端断开、模型输出、工具执行、超时取消。队列消费者需要 worker pool、重试、死信或失败状态。支付同步、通知调度、AI 超时检测需要定时任务和锁。WebSocket 推送需要连接管理和心跳。这些地方适合 Go，但都必须围绕 context 设计。

一个健康的 worker 形态应该是：输入 channel 有边界，worker 数量有上限，context 取消后能退出，错误能返回或记录，shutdown 时能 wait。不要把无限 goroutine 当成性能优化。性能优化的第一步不是增加并发，而是知道瓶颈在哪里。数据库连接池、Redis 连接、外部 API 限流、用户请求超时，这些才是真正决定系统表现的地方。

对这个 Go Admin 项目来说，当前阶段先把 HTTP、认证、RBAC 和资源生命周期打稳，比提前写复杂 worker pool 更重要。架构要给未来异步任务留边界，但不能在还没真实需求时堆并发框架。

# 测试：先证明契约，再谈覆盖率数字

测试不是为了凑覆盖率。迁移项目里的测试首先要证明契约没有被破坏。比如 health endpoint 是否可访问，login config 是否兼容旧前端，refresh/logout 是否按预期返回，PermissionCheck 在没有规则时是否放行、有规则且无身份时是否拒绝、有身份但无权限时是否 fail-closed，Users/init 是否返回 router / permissions / buttonCodes，角色授权是否正确包含 PAGE 和 BUTTON，权限变更是否清缓存。

Go 的 table-driven tests 很适合这种场景。一个函数的不同输入、不同角色、不同平台、不同权限组合，可以放在一张测试表里，每个 case 用 `t.Run` 表达。handler 层可以用 `httptest` 验证 HTTP 契约，service 层可以用 fake repository 验证业务规则，repository 层再单独用数据库集成测试。不要为了测试去改业务结构，也不要为了 mock 一切而制造一堆无意义接口。

Race detector 也很重要，尤其是以后接入 SSE、队列、WebSocket 和缓存时。并发 bug 很少在本地稳定复现，`go test -race ./...` 是底线。性能问题则要用 benchmark 和 pprof 说话，而不是凭感觉说“Go 很快”。Go 给了工具，但工具不会自动替你做好工程纪律。

测试还有一个价值：防止迁移过程中偷偷破坏用户空间。每迁一条旧接口，就应该有旧响应结构的测试；每加一个新 REST 接口，就应该有新契约测试；每改一个权限规则，就应该有 fail-closed 和 cache invalidation 测试。没有测试的迁移就是赌博。

# 前端适配：不重做 UI，只换 API 契约

这个 Go 项目不是前端重做项目。现有 `admin_front_ts` 已经有页面、菜单、权限、登录、请求封装和业务状态。Go 后端迁移阶段，前端的任务应该是适配 API 契约，而不是借机重做 UI。否则你永远分不清问题来自后端迁移，还是前端重构。

前端适配要分两层。第一层是 legacy client，继续请求旧 PHP 或 Go 提供的 legacy adapter。第二层是 go client，请求 `/api/v1/...`。迁移一个模块时，先固定 OpenAPI 或至少固定 DTO，再让前端 API 层做明确翻译。页面层不应该知道后端是 PHP 还是 Go，也不应该到处写 `if (res.xxx ?? res.yyy)`。

动态菜单和按钮权限尤其要谨慎。后端返回 router、permissions、buttonCodes，前端负责渲染和判断，但不能反向定义权限模型。前端可以发现契约问题，但不能用 `any` 和 fallback 把问题吞掉。TypeScript 的价值就在这里：让接口漂移暴露出来，而不是让所有响应都变成 `Record<string, any>`。

这条路线看起来慢，但实际最快。一次只迁移一个模块，一条链路一条链路验证。登录没稳，就别迁角色管理；RBAC 没稳，就别迁业务模块；Go skeleton 没稳，就别上队列和 AI。阶段边界越硬，返工越少。

# 渐进迁移路线：从骨架到 RBAC，再到业务模块

我把迁移拆成几个阶段。第一阶段是最小 Go skeleton：`cmd/admin-api/main.go`、config、logger、Gin router、health、ping、基础测试。这个阶段只证明 Go 服务能跑，不写业务。第二阶段是数据库和配置基线：MySQL、Redis、readiness、连接池、env、graceful shutdown。第三阶段是认证和会话：login config、login、refresh、logout、token hash、session lookup、auth platform policy。第四阶段是 RBAC read path：CheckToken、CheckPermission、Users/init、router、buttonCodes。第五阶段是 RBAC write path：permission、role、授权、缓存失效、operation log。最后才是业务模块迁移。

这个顺序不是为了显得严谨，而是为了减少交叉污染。认证没稳时写业务模块，后面会返工。RBAC 没定时写菜单页面，后面会返工。接口契约没定时改前端，后面会返工。迁移项目最怕同时动前端、后端、数据库、权限和 UI；出了问题根本不知道是哪一层坏。

每个阶段都要能单独解释、单独验证、单独回滚。比如 health 阶段可以用 HTTP smoke 验证；session 阶段可以用 token 测试和 refresh/logout 测试验证；RBAC 阶段可以用固定用户、角色、权限数据验证 Users/init 和 PermissionCheck；前端适配阶段可以用登录、菜单、按钮权限和一个管理页面验证。没有验证，不准说完成。

# 从 PHP 分层到 Go 分层：保留经验，丢掉包袱

我之前在 PHP / Webman 项目里坚持 Controller -> Module -> Dep -> Model。这个经验不是废的。它训练的是边界意识：Controller 不写业务，Module 编排业务，Dep 数据访问，Model 表映射。迁移到 Go 后，这个思想可以保留，但名字和实现要变成 Go 味。Go 里对应的是 route -> handler -> service -> repository -> model。

区别在于 Go 不需要那么多运行时魔法。PHP 项目里可能有 BaseModule、BaseDep、trait、helper 和动态调用；Go 里应该尽量显式。依赖用构造函数传入，错误用返回值表达，context 从 HTTP request 往下传，数据库操作在 repository，业务规则在 service。少用继承式思路，多用组合和小接口。

旧 PHP 的价值是业务事实，不是新架构规则。比如旧接口名、旧 controller 命名、旧 POST 风格、旧历史兼容字段，都不能自动成为 Go 的规则。但旧系统里已经验证过的业务语义，比如单角色、按钮权限、登录平台策略、Redis Session、队列任务状态，这些必须认真迁移。迁移不是照搬代码，迁移是提取事实，然后用更干净的结构重新表达。

# 架构设计的好坏，最后看能不能少出特殊情况

我判断一个架构好不好，不看图画得多复杂，不看用了多少框架，也不看目录有多“企业级”。我看三件事。第一，特殊情况有没有减少。好的设计会把旧接口兼容收口到 adapter，把权限判断收口到 middleware，把数据库访问收口到 repository，把错误映射收口到 response。坏设计会让每个页面、每个 handler、每个 service 都知道一堆例外。

第二，修改路径是否短。改一个权限规则，应该知道去 permission service 或 route rule；改一个登录策略，应该去 authplatform 或 session service；改一个响应格式，应该去 response；改一个数据库查询，应该去 repository。要是一个需求要从 handler 改到前端页面、再改到缓存、再改到 model 方法，还要猜哪个 fallback 生效，那这个系统已经开始腐烂。

第三，是否保护用户空间。后端重构不能让用户登录路径断掉，不能让菜单突然消失，不能让按钮权限错乱，不能让旧业务页面无声失败。技术升级的意义是让系统更可靠，不是让用户为你的架构洁癖买单。

# 这篇文章对应的简历价值

如果把这件事写到简历里，我不会写“熟悉 Go 高并发”这种空话。我会写：用 Go / Gin / GORM / Redis 设计并推进企业级 Admin 后端重构；采用 modular monolith，明确 `cmd -> bootstrap -> server -> module -> platform` 和 `route -> handler -> service -> repository -> model` 边界；迁移认证会话、RBAC、动态菜单、按钮权限、legacy adapter、统一响应、中间件和审计日志；坚持 context 生命周期、错误显式返回、table-driven tests 和 fail-closed 权限策略。

这比“我学过 Go”有用得多。招聘方真正关心的不是你背过多少语法，而是你能不能把一个复杂后台系统拆清楚，能不能在不破坏现有业务的前提下重构，能不能写出别人接手不痛苦的代码。Go 只是工具，架构品味才是关键。

对 PHP 岗位，这个项目说明我不是只会维护旧代码，而是能从旧系统里提取业务事实并做渐进重构。对 Go 岗位，它说明我理解 Gin、GORM、Redis、middleware、context、错误处理、RBAC 和测试，不是只写过 demo。对 Python / AI 应用岗位，它说明我知道 Python 应该放在 AI 工具链和数据处理位置，而不是盲目替代主后端。对前端/全栈岗位，它说明我尊重前后端契约，不会让后端迁移把用户路径炸掉。

# 结尾：少点花活，多点可验证的边界

Go 项目最容易写成两种坏东西：一种是披着 Go 外衣的 Java 项目，目录复杂、接口泛滥、抽象过度；另一种是脚本式 Go 项目，所有逻辑塞 handler，数据库、权限、响应、缓存混在一起。前者假装专业，后者假装快速，最后都会难维护。

我想要的是第三种：少层级、少抽象、先跑通、再提炼。先把真实问题讲清楚，再选最小可行架构；先保护已有用户路径，再逐步替换内部实现；先用 tests 和 smoke 证明契约，再谈优化；先保持单体模块边界清楚，再决定未来是否拆服务。

这就是我对 Go 语言和架构设计的理解：Go 的强项不是让你写更多框架，而是逼你把事情说清楚。一个好的 Admin 后端，不应该靠魔法、兜底和猜测运行。它应该让每个请求从进入系统到返回结果都能被解释，让每个权限判断都有来源，让每个错误都能暴露，让每个迁移步骤都能验证。能做到这些，Go 才不是简历上的一个关键词，而是真正能承接业务系统的工程能力。

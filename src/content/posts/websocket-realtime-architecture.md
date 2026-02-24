---
title: WebSocket 实时通信架构
published: 2026-01-19T18:00:00Z
description: 基于 Webman + GatewayWorker 搭建 WebSocket 基础设施，实现实时通知推送
tags: [后端, WebSocket, 架构]
category: 后端技术
draft: false
---

# 需求背景

Admin 系统需要实时推送能力：
- 异步任务完成通知（如导出 Excel）
- 系统公告广播
- 用户强制下线

项目基于 Webman，天然支持 GatewayWorker，搭建 WebSocket 水到渠成。

## 架构设计

**核心原则**：Gateway 只做消息转发，业务逻辑通过 HTTP 接口处理。

```
┌─────────────────────────────────────────────────────────────┐
│  Events.php (Gateway 事件)                                  │
│  - onConnect: 发送 client_id                                │
│  - onMessage: 空（不处理业务）                               │
│  - onClose: 空                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  HTTP 接口 + GatewayClient                                  │
│  - /WebSocket/bind: 绑定用户                                │
│  - /WebSocket/pushToUser: 推送给指定用户                    │
│  - /WebSocket/broadcast: 广播                               │
└─────────────────────────────────────────────────────────────┘
```

## 后端实现

### Events.php（极简）

```php
<?php
namespace plugin\webman\gateway;

use GatewayWorker\Lib\Gateway;

class Events
{
    public static function onWorkerStart($worker) {}

    public static function onConnect($client_id)
    {
        // 只发送 client_id，让前端通过 HTTP 绑定
        Gateway::sendToClient($client_id, json_encode([
            'type'      => 'init',
            'client_id' => $client_id
        ]));
    }

    public static function onWebSocketConnect($client_id, $data) {}
    public static function onMessage($client_id, $message) {}
    public static function onClose($client_id) {}
}
```

### WebSocketModule.php（业务逻辑）

```php
<?php
namespace app\module\System;

use app\module\BaseModule;
use app\validate\System\WebSocketValidate;
use GatewayWorker\Lib\Gateway;

class WebSocketModule extends BaseModule
{
    public function __construct()
    {
        Gateway::$registerAddress = '127.0.0.1:1236';
    }

    public function bind($request): array
    {
        $param = $this->validate($request, WebSocketValidate::bind());
        $userId = $request->userId;

        Gateway::bindUid($param['client_id'], $userId);
        Gateway::sendToClient($param['client_id'], json_encode([
            'type' => 'bind_success',
            'data' => ['uid' => $userId]
        ]));

        \support\Log::info("[WebSocket] 用户上线: uid={$userId}");
        return self::success(['bound' => true]);
    }

    public function pushToUser($request): array
    {
        $param = $this->validate($request, WebSocketValidate::pushToUser());

        Gateway::sendToUid($param['uid'], json_encode([
            'type' => $param['type'] ?? 'notification',
            'data' => $param['data'] ?? []
        ]));

        return self::success(['sent' => true]);
    }
}
```

## 前端实现

### useWebSocket Hook

```typescript
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const ws = ref<WebSocket | null>(null)
  const isConnected = ref(false)
  const isBound = ref(false)
  const clientId = ref('')

  function connect() {
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('[WebSocket] 连接成功')
      isConnected.value = true
    }

    ws.value.onmessage = (event) => {
      const message = JSON.parse(event.data)
      handleMessage(message)
    }
  }

  function handleMessage(message: WsMessage) {
    switch (message.type) {
      case 'init':
        clientId.value = message.client_id
        bindUser()  // 通过 HTTP 接口绑定
        break
      case 'bind_success':
        console.log('[WebSocket] 绑定成功')
        isBound.value = true
        break
    }
  }

  async function bindUser() {
    await request.post('/api/admin/WebSocket/bind', { 
      client_id: clientId.value 
    })
  }

  onMounted(() => connect())
  onUnmounted(() => disconnect())

  return { isConnected, isBound, send }
}
```

### 消息监听（组件内订阅）

`onWsMessage` 是订阅函数，各组件按需调用：

```typescript
// NotificationCenter.vue - 通知组件内监听
import { onWsMessage } from '@/hooks/useWebSocket'

let unsubscribe: (() => void) | null = null

onMounted(() => {
  unsubscribe = onWsMessage('notification', ({ data }) => {
    unreadCount.value++
    if (data.level === 'urgent') {
      ElNotification({ title: data.title, message: data.content, type: data.notification_type })
    }
  })
})

onUnmounted(() => unsubscribe?.())
```

**职责分离**：
- `useWebSocket()` 只负责建立连接（在 Layout 调用）
- `onWsMessage()` 是订阅函数，各组件按需调用
- 必须在 `onUnmounted` 取消订阅，避免监听器累积

## 实战：异步导出 + 通知系统

现在导出完成后通过 `NotificationService` 统一发送通知：

```php
use app\service\System\NotificationService;

class ExportTask implements Consumer
{
    public $queue = 'export_task';

    public function consume($data)
    {
        $result = (new ExportService())->export($data['headers'], $data['data'], $data['prefix']);
        (new ExportTaskDep())->updateSuccess($data['task_id'], $result);
        
        // 通过通知服务发送（写库 + WebSocket 推送）
        NotificationService::sendUrgent($data['user_id'], $data['title'] . ' - 导出完成', '点击查看并下载导出文件', [
            'type' => NotificationService::TYPE_SUCCESS,
            'link' => '/devTools/exportTask'
        ]);
    }
}
```

> 详见《通知管理系统设计与实现》

## 连接生命周期

```
登录 → 进入 Layout → WebSocketProvider 挂载
    → useWebSocket onMounted → connect()
    → 收到 init → HTTP 绑定 → 收到 bind_success
    → 可以接收推送了

退出 → 路由跳转 → Layout 卸载
    → useWebSocket onUnmounted → disconnect()
    → WebSocket 断开
```

登录页不使用 Layout，所以不会连接 WebSocket。

## 总结

| 组件 | 职责 |
|------|------|
| Events.php | 只发 client_id，不处理业务 |
| WebSocketModule | 绑定、推送等业务逻辑 |
| useWebSocket | 连接管理、消息分发 |
| onWsMessage | 订阅函数，组件内按需调用 |
| NotificationService | 写库 + WebSocket 推送 |

**核心思想**：Gateway 只是通道，业务逻辑走 HTTP，职责分离，架构清晰。

## 心跳保活机制

WebSocket 连接不是永久的。网络波动、NAT 超时、代理服务器都可能导致连接静默断开。必须有心跳机制来检测和恢复连接。

### 前端心跳

```typescript
const HEARTBEAT_INTERVAL = 30000 // 30秒
const HEARTBEAT_TIMEOUT = 10000  // 10秒无响应视为断开

let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let heartbeatTimeoutTimer: ReturnType<typeof setTimeout> | null = null

function startHeartbeat() {
  heartbeatTimer = setInterval(() => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      ws.value.send(JSON.stringify({ type: 'ping' }))

      // 设置超时检测
      heartbeatTimeoutTimer = setTimeout(() => {
        console.warn('[WebSocket] 心跳超时，准备重连')
        ws.value?.close()
        reconnect()
      }, HEARTBEAT_TIMEOUT)
    }
  }, HEARTBEAT_INTERVAL)
}

// 收到 pong 时清除超时计时器
function handlePong() {
  if (heartbeatTimeoutTimer) {
    clearTimeout(heartbeatTimeoutTimer)
    heartbeatTimeoutTimer = null
  }
}
```

### 后端心跳响应

GatewayWorker 内置了心跳检测，但我们也在 Events 里处理前端发来的 ping：

```php
public static function onMessage($client_id, $message)
{
    $data = json_decode($message, true);
    if ($data['type'] === 'ping') {
        Gateway::sendToClient($client_id, json_encode(['type' => 'pong']));
    }
}
```

### GatewayWorker 配置

```php
// config/plugin/webman/gateway/process.php
return [
    'gateway' => [
        'handler' => Gateway::class,
        'listen' => 'websocket://0.0.0.0:7272',
        'context' => [],
        'constructor' => ['0.0.0.0', 7272, [
            'pingInterval' => 55,      // 55秒检测一次
            'pingNotResponseLimit' => 1, // 1次无响应就断开
            'pingData' => '',           // 服务端主动 ping 的数据
        ]],
    ],
];
```

为什么是 55 秒？因为很多 Nginx 反向代理的默认超时是 60 秒，55 秒发一次心跳刚好在超时之前。

## 断线重连策略

网络不稳定时，WebSocket 会频繁断开。重连策略需要考虑：

1. 不能立即重连（可能是服务器宕机，立即重连只会加重负担）
2. 不能无限重连（避免资源浪费）
3. 重连间隔要递增（指数退避）

```typescript
const MAX_RECONNECT_ATTEMPTS = 10
const BASE_RECONNECT_DELAY = 1000 // 1秒

let reconnectAttempts = 0
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function reconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error('[WebSocket] 重连次数已达上限')
    ElNotification.error({ message: '实时连接已断开，请刷新页面' })
    return
  }

  // 指数退避 + 随机抖动
  const delay = Math.min(
    BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttempts) + Math.random() * 1000,
    30000 // 最大 30 秒
  )

  console.log(`[WebSocket] ${delay}ms 后第 ${reconnectAttempts + 1} 次重连`)

  reconnectTimer = setTimeout(() => {
    reconnectAttempts++
    connect()
  }, delay)
}

// 连接成功后重置计数器
function onConnected() {
  reconnectAttempts = 0
  isConnected.value = true
  console.log('[WebSocket] 连接成功')
}
```

随机抖动（jitter）很重要。如果服务器重启，所有客户端同时重连会造成"惊群效应"，加上随机延迟可以分散重连请求。

## 通知系统集成

WebSocket 最大的应用场景是实时通知。我设计了一个 `NotificationService` 来统一管理通知的发送：

```php
class NotificationService
{
    const TYPE_INFO = 'info';
    const TYPE_SUCCESS = 'success';
    const TYPE_WARNING = 'warning';
    const TYPE_ERROR = 'error';

    /**
     * 发送紧急通知（写库 + WebSocket 推送 + 可选系统通知）
     */
    public static function sendUrgent(
        int $userId,
        string $title,
        string $content,
        array $extra = []
    ): void {
        // 1. 写入通知表（持久化）
        $notification = (new NotificationDep())->add([
            'user_id' => $userId,
            'title' => $title,
            'content' => $content,
            'level' => 'urgent',
            'notification_type' => $extra['type'] ?? self::TYPE_INFO,
            'link' => $extra['link'] ?? '',
            'is_read' => CommonEnum::NO,
        ]);

        // 2. WebSocket 实时推送
        try {
            Gateway::$registerAddress = '127.0.0.1:1236';
            Gateway::sendToUid($userId, json_encode([
                'type' => 'notification',
                'data' => [
                    'id' => $notification->id,
                    'title' => $title,
                    'content' => $content,
                    'level' => 'urgent',
                    'notification_type' => $extra['type'] ?? self::TYPE_INFO,
                    'link' => $extra['link'] ?? '',
                    'created_at' => date('Y-m-d H:i:s'),
                ],
            ]));
        } catch (\Throwable $e) {
            // WebSocket 推送失败不影响通知写入
            Log::warning("[Notification] WebSocket 推送失败: {$e->getMessage()}");
        }
    }

    /**
     * 发送普通通知（只写库，不推送）
     */
    public static function send(int $userId, string $title, string $content, array $extra = []): void
    {
        (new NotificationDep())->add([
            'user_id' => $userId,
            'title' => $title,
            'content' => $content,
            'level' => 'normal',
            'notification_type' => $extra['type'] ?? self::TYPE_INFO,
            'link' => $extra['link'] ?? '',
            'is_read' => CommonEnum::NO,
        ]);
    }
}
```

关键设计：WebSocket 推送失败不能影响通知写入。用户下次打开页面时，可以通过 HTTP 接口拉取未读通知。WebSocket 只是"锦上添花"的实时推送，不是通知的唯一通道。

## 安全考虑

### 认证

WebSocket 连接本身不携带 Token。我的方案是：连接建立后，通过 HTTP 接口绑定用户身份。

```
WebSocket 连接 → 获得 client_id → HTTP POST /bind (带 Token) → 服务端验证 Token → 绑定 uid
```

为什么不在 WebSocket 握手时验证？因为 GatewayWorker 的 Events 运行在独立进程，不方便访问业务层的 Token 验证逻辑。通过 HTTP 接口绑定，可以复用已有的中间件链（CheckToken → CheckPermission）。

### 消息校验

推送消息时要校验目标用户是否有权限接收：

```php
public function pushToUser($request): array
{
    $param = $this->validate($request, WebSocketValidate::pushToUser());

    // 只允许推送给自己或下级用户
    $currentUserId = $request->userId;
    $targetUserId = $param['uid'];

    if ($currentUserId !== $targetUserId) {
        $hasPermission = $this->dep(UsersDep::class)
            ->isSubordinate($currentUserId, $targetUserId);
        self::throwUnless($hasPermission, '无权向该用户推送消息');
    }

    Gateway::sendToUid($targetUserId, json_encode([
        'type' => $param['type'] ?? 'notification',
        'data' => $param['data'] ?? [],
    ]));

    return self::success(['sent' => true]);
}
```

## Nginx 反向代理配置

生产环境通常有 Nginx 在前面，需要正确配置 WebSocket 代理：

```nginx
# WebSocket 代理
location /ws {
    proxy_pass http://127.0.0.1:7272;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # 超时设置要比心跳间隔长
    proxy_read_timeout 120s;
    proxy_send_timeout 120s;
}
```

`proxy_read_timeout` 必须大于心跳间隔，否则 Nginx 会在心跳之前就断开连接。

## 总结

| 组件 | 职责 |
|------|------|
| Events.php | 只发 client_id，不处理业务 |
| WebSocketModule | 绑定、推送等业务逻辑 |
| useWebSocket | 连接管理、心跳、重连 |
| onWsMessage | 订阅函数，组件内按需调用 |
| NotificationService | 写库 + WebSocket 推送 |
| Nginx | 反向代理 + 超时控制 |

WebSocket 实时通信看起来简单，但要做到生产可用，心跳保活、断线重连、安全认证、Nginx 配置每一个环节都不能少。核心思想始终是：Gateway 只是通道，业务逻辑走 HTTP，职责分离，架构清晰。

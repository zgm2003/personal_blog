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

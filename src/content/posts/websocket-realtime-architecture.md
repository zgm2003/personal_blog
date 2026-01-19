---
title: WebSocket 实时通信架构
published: 2026-01-19T18:00:00Z
description: 基于 Webman + GatewayWorker 搭建 WebSocket 基础设施，实现异步导出通知
tags: [后端, WebSocket, 架构]
category: 智澜管理系统
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

### WebSocketProvider（职责分离）

```vue
<script setup lang="ts">
import { h } from 'vue'
import { useWebSocket, onWsMessage } from '@/hooks/useWebSocket'
import { ElNotification } from 'element-plus'

useWebSocket()

// 监听通知
onWsMessage('notification', (msg) => {
  ElNotification({
    title: msg.data?.title || '通知',
    message: msg.data?.content || '',
    type: msg.data?.type || 'info',
  })
})

// 监听导出完成
onWsMessage('export_complete', (msg) => {
  ElNotification({
    title: msg.data?.title || '导出完成',
    message: h('a', { href: msg.data?.url, target: '_blank' }, '下载文件'),
    type: 'success',
    duration: 10000,
  })
})
</script>

<template>
  <slot />
</template>
```

Layout 只需引入 Provider：

```vue
<template>
  <WebSocketProvider>
    <el-container>...</el-container>
  </WebSocketProvider>
</template>
```

## 实战：异步导出 + WebSocket 通知

### 改造导出接口

```php
// 原来：同步导出，阻塞请求
$url = $exportService->export($headers, $data);
return self::success(['url' => $url]);

// 现在：丢队列，立即返回
RedisQueue::send('export-task', [
    'user_id' => $request->userId,
    'headers' => $headers,
    'data' => $data,
    'title' => '用户列表导出',
]);
return self::success(['message' => '导出任务已提交']);
```

### 队列消费者

```php
class ExportTask implements Consumer
{
    public $queue = 'export-task';

    public function consume($data)
    {
        $url = (new ExportService())->export(
            $data['headers'], 
            $data['data'], 
            $data['prefix']
        );

        // 推送完成通知
        Gateway::$registerAddress = '127.0.0.1:1236';
        Gateway::sendToUid($data['user_id'], json_encode([
            'type' => 'export_complete',
            'data' => [
                'title' => $data['title'],
                'url' => $url,
                'message' => '导出完成，点击下载'
            ]
        ]));
    }
}
```

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
| WebSocketProvider | 全局消息监听、通知弹窗 |
| ExportTask | 异步导出 + 完成推送 |

**核心思想**：Gateway 只是通道，业务逻辑走 HTTP，职责分离，架构清晰。

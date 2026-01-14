---
title: Redis 异步队列
published: 2026-01-13T15:00:00Z
description: 使用 Redis Queue 实现异步任务，AI 标题生成优化实践
tags: [后端, Redis, 异步]
category: AI对话
draft: false
---

# 问题背景

AI 对话完成后，需要自动生成会话标题。原来的做法：

```php
// 同步生成标题
$title = $this->chatService->generateTitle($client, $userMessage);
$this->conversationsDep->updateTitle($conversationId, $title);
```

问题：生成标题需要调用 AI 接口，耗时 2-3 秒，用户要干等。

## 解决方案：异步队列

把标题生成放到后台队列处理，接口立即返回。

```php
// 异步生成标题
RedisQueue::send('generate_conversation_title', [
    'conversation_id' => $conversationId,
    'agent_id' => $agentId,
    'user_message' => $userMessage,
    'user_id' => $userId,
]);
```

## 队列消费者

```php
<?php
namespace app\queue\redis\slow;

use Webman\RedisQueue\Consumer;

class GenerateConversationTitle implements Consumer
{
    public $queue = 'generate_conversation_title';
    public $connection = 'default';

    public function consume($data): void
    {
        $conversationId = $data['conversation_id'];
        $userMessage = $data['user_message'];
        
        // 检查会话是否已有标题
        $conversation = $this->conversationsDep->get($conversationId);
        if (!empty($conversation->title)) {
            return;  // 已有标题，跳过
        }
        
        // 获取智能体和模型
        $agent = $this->agentsDep->get($data['agent_id']);
        $model = $this->modelsDep->get($agent->model_id);
        
        // 创建 AI 客户端
        [$client, $config] = $this->chatService->createClient($model);
        
        // 生成标题
        $title = $this->chatService->generateTitle($client, $userMessage);
        
        // 更新会话标题
        if ($title) {
            $this->conversationsDep->updateTitle($conversationId, $title);
        }
    }
}
```

## 配置 Redis Queue

`config/plugin/webman/redis-queue/redis.php`:

```php
return [
    'default' => [
        'host' => 'redis://127.0.0.1:6379',
        'options' => [
            'max_attempts' => 3,      // 最大重试次数
            'retry_seconds' => 5,     // 重试间隔
        ]
    ]
];
```

## 队列分组

不同任务放不同队列，避免慢任务阻塞快任务：

```
app/queue/redis/
├── fast/           # 快速任务（< 1s）
│   └── SendNotification.php
├── slow/           # 慢任务（1-10s）
│   └── GenerateConversationTitle.php
└── heavy/          # 重任务（> 10s）
    └── ExportReport.php
```

## 启动队列进程

```bash
php webman queue:work
```

或者在 `process.php` 中配置：

```php
return [
    'redis-queue' => [
        'handler' => Webman\RedisQueue\Process\Consumer::class,
        'count' => 4,  // 4 个消费进程
    ]
];
```

## 效果对比

| 指标 | 同步 | 异步 |
|------|------|------|
| 接口响应时间 | 3-5s | 200ms |
| 用户体验 | 卡顿 | 流畅 |
| 标题生成 | 立即可见 | 延迟 2-3s |

用户发完消息立即能继续操作，标题稍后自动出现，体验好很多。

## 适用场景

- 发送邮件/短信
- 生成报表
- 图片处理
- AI 调用
- 数据同步

只要不需要立即返回结果的任务，都可以异步化。

## 注意事项

1. **幂等性**：任务可能重试，确保多次执行结果一致
2. **超时处理**：设置合理的超时时间
3. **错误处理**：记录失败日志，方便排查
4. **监控**：监控队列积压情况

异步队列是提升接口性能的利器，用好了事半功倍。

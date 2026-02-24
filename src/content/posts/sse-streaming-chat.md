---
title: SSE 流式对话系统：从协议原理到生产实践
published: 2026-02-10T10:00:00Z
description: 深入解析 SSE 协议在 AI 对话场景的应用，包含流式输出、中断机制、异常处理的完整实现
tags: [SSE, AI, 前端, 后端]
category: 前端技术
draft: false
---

# 为什么需要流式输出？

用过 ChatGPT 的人都知道，AI 的回答是逐字"打"出来的，而不是等全部生成完再一次性显示。这不是花哨的动画效果，而是实实在在的技术需求。

GPT-4 生成一段 500 字的回答可能需要 10-15 秒。如果等全部生成完再返回，用户要盯着空白页面等 15 秒。但如果用流式输出，用户在第 1 秒就能看到第一个字，体验完全不同。

这就是 SSE（Server-Sent Events）的用武之地。

## SSE vs WebSocket：为什么选 SSE？

很多人第一反应是用 WebSocket。但对于 AI 对话这个场景，SSE 更合适：

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| 方向 | 服务端 → 客户端（单向） | 双向 |
| 协议 | HTTP | 独立协议 |
| 重连 | 浏览器自动重连 | 需要手动实现 |
| 兼容性 | 所有现代浏览器 | 所有现代浏览器 |
| 复杂度 | 低 | 高 |

AI 对话的数据流是单向的：服务端生成内容，推送给客户端。不需要客户端实时往服务端发数据。SSE 天然适合这个场景，而且基于 HTTP 协议，不需要额外的握手和连接管理。

## 后端实现：Webman + SSE

Webman 是常驻内存的 PHP 框架，天然支持长连接。实现 SSE 的关键是正确设置响应头和数据格式。

```php
class AiChatController extends Controller
{
    public function stream(Request $request)
    {
        $param = $this->validate($request, ChatValidate::stream());

        // 设置 SSE 响应头
        $connection = $request->connection;
        $connection->send(new Response(200, [
            'Content-Type' => 'text/event-stream',
            'Cache-Control' => 'no-cache',
            'Connection' => 'keep-alive',
            'X-Accel-Buffering' => 'no', // 告诉 Nginx 不要缓冲
        ]));

        // 获取智能体和模型
        $agent = AiAgents::find($param['agent_id']);
        $model = AiModels::find($agent->model_id);

        // 构建消息上下文
        $messages = $this->buildMessages($agent, $param);

        // 流式调用大模型
        $fullContent = '';
        $this->aiService->streamChat($messages, $model, function ($chunk) use ($connection, &$fullContent) {
            $fullContent .= $chunk;

            // SSE 数据格式：data: {json}\n\n
            $connection->send("data: " . json_encode([
                'type' => 'content',
                'content' => $chunk,
            ]) . "\n\n");
        });

        // 发送结束信号
        $connection->send("data: " . json_encode([
            'type' => 'done',
            'content' => $fullContent,
        ]) . "\n\n");

        // 异步保存对话记录（不阻塞响应）
        $this->asyncSaveMessage($param, $fullContent);
    }
}
```

几个关键细节：

1. `X-Accel-Buffering: no`：如果前面有 Nginx 反向代理，必须加这个头，否则 Nginx 会缓冲 SSE 数据，用户看到的就不是逐字输出
2. 每条 SSE 消息以 `\n\n` 结尾，这是协议规定的分隔符
3. 对话记录异步保存，不影响流式输出的实时性

## 前端实现：封装 streamPost

浏览器原生的 `EventSource` API 只支持 GET 请求，但 AI 对话需要 POST（因为要传消息体）。所以我们用 `fetch` + `ReadableStream` 来实现。

```typescript
interface StreamOptions {
  url: string
  data: Record<string, any>
  onMessage: (chunk: string) => void
  onDone?: (fullContent: string) => void
  onError?: (error: Error) => void
}

export function streamPost(options: StreamOptions): AbortController {
  const controller = new AbortController()

  fetch(options.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`,
    },
    body: JSON.stringify(options.data),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // 按 SSE 协议解析：以 \n\n 分割消息
      const messages = buffer.split('\n\n')
      buffer = messages.pop() || '' // 最后一个可能是不完整的

      for (const msg of messages) {
        if (!msg.startsWith('data: ')) continue
        const jsonStr = msg.slice(6)

        try {
          const data = JSON.parse(jsonStr)
          if (data.type === 'content') {
            options.onMessage(data.content)
          } else if (data.type === 'done') {
            options.onDone?.(data.content)
          }
        } catch {
          // 忽略解析失败的消息
        }
      }
    }
  }).catch((err) => {
    if (err.name === 'AbortError') return // 用户主动中断，不算错误
    options.onError?.(err)
  })

  return controller // 返回 controller，用于中断
}
```

使用方式非常简洁：

```typescript
const controller = streamPost({
  url: '/api/ai/chat/stream',
  data: { agent_id: 1, messages: [...] },
  onMessage(chunk) {
    // 逐字追加到界面
    currentMessage.value += chunk
  },
  onDone(fullContent) {
    // 完成后刷新对话列表
    refreshMessages()
  },
  onError(err) {
    ElNotification.error({ message: '对话失败：' + err.message })
  },
})

// 用户点击"停止生成"
stopButton.onclick = () => controller.abort()
```

## 中断机制：用户说停就停

这是一个容易被忽略但非常重要的功能。用户可能在 AI 生成到一半时发现方向不对，需要立即停止。

前端通过 `AbortController.abort()` 中断 fetch 请求。但后端怎么知道客户端断开了？

在 Webman 中，当客户端断开连接时，`$connection` 的 `onClose` 回调会被触发。我们利用这个机制来停止模型调用：

```php
$stopped = false;

$connection->onClose = function () use (&$stopped) {
    $stopped = true;
};

$this->aiService->streamChat($messages, $model, function ($chunk) use ($connection, &$stopped, &$fullContent) {
    if ($stopped) {
        throw new StreamInterruptedException();
    }

    $fullContent .= $chunk;
    $connection->send("data: " . json_encode([
        'type' => 'content',
        'content' => $chunk,
    ]) . "\n\n");
});
```

关键点：即使用户中断了，已经生成的内容也要保存。不能因为中断就丢弃前面的输出。

```php
try {
    // 流式输出...
} catch (StreamInterruptedException $e) {
    // 中断不是错误，保存已生成的内容
} finally {
    if ($fullContent) {
        $this->saveMessage($param, $fullContent, $stopped ? 'interrupted' : 'completed');
    }
}
```

## 异步标题生成：不阻塞主流程

对话完成后，需要给这轮对话生成一个标题（就像 ChatGPT 那样，左侧栏显示对话标题）。

标题生成本身也是一次 AI 调用，如果同步执行，用户要多等 2-3 秒。所以我们把它丢到 Redis 队列里异步处理：

```php
// 对话完成后，异步生成标题
if ($isFirstMessage) {
    Redis::send('chat-queue', [
        'action' => 'generate_title',
        'conversation_id' => $param['conversation_id'],
        'first_message' => $param['messages'][0]['content'],
    ]);
}
```

消费者用一个轻量级的模型（比如 GPT-3.5）来生成标题，成本低、速度快：

```php
private function generateTitle(array $data): void
{
    $result = $this->aiService->chat([
        ['role' => 'system', 'content' => '用10个字以内概括以下对话的主题，直接输出标题，不要解释'],
        ['role' => 'user', 'content' => $data['first_message']],
    ], $this->getLightModel());

    Conversation::where('id', $data['conversation_id'])
        ->update(['title' => $result->content]);
}
```

这个优化让对话接口的响应时间从 3 秒降到了 200ms（不算流式输出时间）。

## 错误处理：优雅降级

AI 服务不是 100% 可靠的。网络波动、服务降级、Token 超限都可能导致调用失败。我们的错误处理策略：

```php
// 1. 超时控制
$this->aiService->streamChat($messages, $model, $callback, [
    'timeout' => 120, // 最长等待 2 分钟
]);

// 2. 重试机制（仅对可重试的错误）
$retryableErrors = [429, 500, 502, 503];
$maxRetries = 2;

for ($i = 0; $i <= $maxRetries; $i++) {
    try {
        return $this->callModel($messages, $model);
    } catch (ApiException $e) {
        if (!in_array($e->getCode(), $retryableErrors) || $i === $maxRetries) {
            throw $e;
        }
        sleep(pow(2, $i)); // 指数退避：1s, 2s, 4s
    }
}

// 3. 前端友好提示
// 不要把原始错误信息暴露给用户
$userMessage = match (true) {
    $e->getCode() === 429 => '当前使用人数较多，请稍后再试',
    $e->getCode() >= 500 => 'AI 服务暂时不可用，请稍后再试',
    default => '对话失败，请重试',
};
```

## 性能优化总结

| 优化项 | 优化前 | 优化后 |
|--------|--------|--------|
| 首字响应 | 3-5s | < 500ms |
| 标题生成 | 同步 3s | 异步 0ms |
| 接口调用 | 4 个 | 1 个 |
| 中断响应 | 不支持 | 即时 |

## 写在最后

SSE 流式对话看起来简单，但要做到生产可用，需要考虑很多细节：Nginx 缓冲、中断机制、错误重试、异步优化。每一个细节都可能影响用户体验。

技术选型上，SSE 比 WebSocket 更适合 AI 对话场景。不要为了"看起来高级"而选择更复杂的方案，合适的才是最好的。

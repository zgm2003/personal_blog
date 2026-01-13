---
title: SSE 流式输出实战：从 0 到 1 实现 AI 对话
published: 2026-01-13T12:00:00Z
description: 基于 Server-Sent Events 实现类 ChatGPT 的流式对话体验
tags: [SSE, AI, Vue3, PHP]
category: 技术
draft: false
---

# 为什么要流式输出？

普通 HTTP 请求：等 AI 生成完所有内容 → 一次性返回 → 用户干等 10 秒

流式输出：AI 边生成边返回 → 用户实时看到内容 → 体验丝滑

ChatGPT 就是这么做的。

## 技术选型

| 方案 | 优点 | 缺点 |
|------|------|------|
| WebSocket | 双向通信 | 复杂，需要维护连接 |
| SSE | 简单，原生支持 | 单向，只能服务端推送 |
| 长轮询 | 兼容性好 | 效率低 |

AI 对话场景是典型的"服务端推送"，SSE 最合适。

## 后端实现（PHP/Webman）

```php
public function sendStream(array $param, int $userId, callable $onChunk): array
{
    // 准备上下文
    $ctx = $this->prepareChat($param, $userId);
    
    // 创建 Run 记录
    $runId = $this->createRun($requestId, $userId, $ctx);
    $onChunk('run', ['run_id' => $runId]);
    
    // 调用 AI 服务，流式输出
    $result = $this->chatService->chatStream(
        $ctx['client'], 
        $ctx['payload'],
        function ($delta) use ($onChunk) {
            // 每收到一段内容，推送给前端
            $onChunk('content', ['delta' => $delta]);
        },
        function () use ($runId) {
            // 检查是否被取消
            $run = $this->runsDep->find($runId);
            return $run->run_status === AiEnum::RUN_STATUS_CANCELED;
        }
    );
    
    $onChunk('done', ['conversation_id' => $ctx['conversationId']]);
    return self::success();
}
```

Controller 层发送 SSE：

```php
public function stream(Request $request)
{
    return response()->withHeaders([
        'Content-Type' => 'text/event-stream',
        'Cache-Control' => 'no-cache',
        'Connection' => 'keep-alive',
    ])->withBody(new StreamBody(function ($write) use ($request) {
        $module = new AiChatModule();
        $module->sendStream($param, $userId, function ($event, $data) use ($write) {
            $write("event: {$event}\n");
            $write("data: " . json_encode($data) . "\n\n");
        });
    }));
}
```

## 前端实现（Vue3 + TypeScript）

封装 streamPost 函数：

```typescript
export async function streamPost(url: string, data: any, callbacks: SSECallbacks) {
  const response = await fetch(url, {
    method: 'POST',
    headers: getCommonHeaders(),
    body: JSON.stringify(data),
  })

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    
    // 解析 SSE 格式
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentEvent = ''
    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        const data = JSON.parse(line.slice(5).trim())
        callbacks.onEvent?.(currentEvent, data)
      }
    }
  }
}
```

使用 Composable 封装业务逻辑：

```typescript
export function useStreamChat(options: StreamChatOptions) {
  const sending = ref(false)
  const isStreaming = ref(false)
  
  const send = async (content: string) => {
    sending.value = true
    isStreaming.value = true
    
    // 添加用户消息
    messages.value.push({ role: 'user', content })
    
    // 添加 AI 占位消息
    messages.value.push({ role: 'assistant', content: '', isStreaming: true })
    
    await AiChatApi.stream({ content }, {
      onContent: (delta) => {
        // 实时更新 AI 消息内容
        const lastMsg = messages.value[messages.value.length - 1]
        lastMsg.content += delta
      },
      onDone: () => {
        isStreaming.value = false
      }
    })
  }
  
  return { sending, isStreaming, send }
}
```

## 取消机制

用户切换会话或点击停止时，需要取消正在进行的流式输出：

```typescript
const cancelOnSwitch = async () => {
  if (!isStreaming.value || !currentRunId.value) return
  
  // 立即重置状态
  isStreaming.value = false
  
  // 后台取消请求
  AiChatApi.cancel(currentRunId.value)
}
```

后端检测到取消后，保存已生成的部分内容：

```php
if (!empty($result['canceled'])) {
    // 保存已生成的内容
    $this->saveAssistantMessage($conversationId, $result['content']);
    $onChunk('canceled', []);
    return;
}
```

## 效果

- 首字响应时间 < 500ms
- 用户可以随时停止生成
- 切换会话不会丢失已生成内容
- 体验接近 ChatGPT

流式输出是 AI 应用的标配，掌握 SSE 很有必要。

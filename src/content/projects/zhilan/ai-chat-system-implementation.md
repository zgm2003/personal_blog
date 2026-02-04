---
title: AI 对话系统完整实现
published: 2026-02-04T20:20:00Z
description: 深度剖析 AI 对话系统的完整实现，涵盖 8 种 AI 驱动统一封装、SSE 流式输出、渲染节流优化、防串话机制、Run/Step 追踪
tags: [AI, SSE, 架构, 性能优化]
project: 智澜管理系统
order: 100
draft: false
---

# 前言

在开发智澜管理系统的 AI 对话模块时，我遇到了一系列挑战：

- 如何统一接入 OpenAI、Claude、通义千问等 8 种 AI 驱动？
- SSE 流式输出时，如何避免高频 DOM 更新导致的卡顿？
- 用户切换会话时，如何防止消息串话？
- 如何追踪每次 AI 调用的完整过程？

本文将深度剖析这些问题的解决方案，分享一套完整的 AI 对话系统实现。

---

# 一、多驱动架构设计

## 1.1 设计目标

**核心诉求**：
- 支持多种 AI 服务商（OpenAI、通义千问、DeepSeek、Moonshot、智谱、混元等）
- 统一的调用接口，业务层无需关心底层驱动差异
- 易于扩展，新增驱动只需实现接口

**架构分层**：

```
业务层 (AiChatModule)
    
服务层 (AiChatService)
    
客户端工厂 (AiClientFactory)
    
驱动实现 (OpenAiCompatClient, WenxinClient...)
```

## 1.2 接口定义

所有 AI 客户端必须实现统一接口：

```php
interface AiClientInterface
{
    /**
     * 非流式调用
     * @return array ['content' => string, 'usage' => array, 'raw' => array]
     */
    public function chatCompletions(array \, array \): array;

    /**
     * 流式调用
     * @param callable \ function(string \, array \)
     * @param callable|null \ function(): bool
     * @return array ['content' => string, 'usage' => array, 'canceled' => bool]
     */
    public function chatCompletionsStream(
        array \, 
        array \, 
        callable \, 
        ?callable \ = null
    ): array;
}
```

**关键设计**：
- \ 回调：支持中途取消，用于会话切换场景
- 统一返回格式：content + usage，屏蔽各家 API 差异

## 1.3 工厂模式实现

```php
class AiClientFactory
{
    private static array \ = [
        AiEnum::DRIVER_QWEN => OpenAiCompatClient::class,
        AiEnum::DRIVER_DEEPSEEK => OpenAiCompatClient::class,
        AiEnum::DRIVER_MOONSHOT => OpenAiCompatClient::class,
        AiEnum::DRIVER_ZHIPU => OpenAiCompatClient::class,
        AiEnum::DRIVER_OPENAI => OpenAiCompatClient::class,
        AiEnum::DRIVER_HUNYUAN => OpenAiCompatClient::class,
        // 未来扩展：
        // AiEnum::DRIVER_WENXIN => WenxinClient::class,
        // AiEnum::DRIVER_CLAUDE => ClaudeClient::class,
    ];

    private static array \ = [
        AiEnum::DRIVER_QWEN => 'https://dashscope.aliyuncs.com/compatible-mode/v1',
        AiEnum::DRIVER_DEEPSEEK => 'https://api.deepseek.com/v1',
        AiEnum::DRIVER_MOONSHOT => 'https://api.moonshot.cn/v1',
        AiEnum::DRIVER_ZHIPU => 'https://open.bigmodel.cn/api/paas/v4',
        AiEnum::DRIVER_OPENAI => 'https://api.openai.com/v1',
    ];

    public static function create(string \): AiClientInterface
    {
        if (!isset(self::\[\])) {
            throw new RuntimeException(\"不支持的 AI 驱动: {\}\");
        }

        \ = self::\[\];
        \ = self::\[\] ?? '';

        return new \(\);
    }
}
```

**优势**：
- 新增驱动只需在 \ 注册
- OpenAI 兼容接口共用一个客户端实现
- 支持自定义 endpoint（私有部署场景）

---

# 二、OpenAI 兼容客户端实现

## 2.1 为什么 6 种驱动共用一个客户端？

通义千问、DeepSeek、Moonshot、智谱、OpenAI、混元都支持 OpenAI 兼容接口，只是 baseUrl 不同。

**统一格式**：

```http
POST {baseUrl}/chat/completions
Authorization: Bearer {apiKey}
Content-Type: application/json

{
  \"model\": \"qwen-plus\",
  \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}],
  \"stream\": true
}
```

## 2.2 流式调用核心实现

```php
public function chatCompletionsStream(
    array \, 
    array \, 
    callable \, 
    ?callable \ = null
): array {
    \ = \['endpoint'] ?? \->defaultBaseUrl;
    \ = \['apiKey'];
    
    \['stream'] = true;
    \['stream_options'] = ['include_usage' => true];  // 请求返回 token 统计

    \ = '';
    \ = [];
    \ = false;

    \ = curl_init();
    curl_setopt_array(\, [
        CURLOPT_URL => \ . '/chat/completions',
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(\),
        CURLOPT_RETURNTRANSFER => false,
        CURLOPT_TIMEOUT => 300,
        CURLOPT_HTTPHEADER => [
            'Content-Type: application/json',
            'Authorization: Bearer ' . \,
            'Accept: text/event-stream',
        ],
        CURLOPT_WRITEFUNCTION => function (\, \) use (
            &\, &\, &\, \, \
        ) {
            // 检查是否应该停止
            if (\ && \()) {
                \ = true;
                return 0;  // 返回 0 中断 curl
            }
            
            // 解析 SSE 数据
            \ = explode(\"\\n\", \);
            foreach (\ as \) {
                \ = trim(\);
                if (empty(\) || str_starts_with(\, ':')) continue;
                
                if (str_starts_with(\, 'data:')) {
                    \ = trim(substr(\, 5));
                    if (\ === '[DONE]') continue;
                    
                    \ = json_decode(\, true);
                    if (!\) continue;
                    
                    // 提取内容
                    if (isset(\['choices'][0]['delta']['content'])) {
                        \ = \['choices'][0]['delta']['content'];
                        \ .= \;
                        \(\, \);  // 回调通知前端
                    }
                    
                    // 提取 usage（最后一个 chunk）
                    if (isset(\['usage'])) {
                        \ = \['usage'];
                    }
                }
            }
            return strlen(\);
        },
    ]);

    curl_exec(\);
    curl_close(\);

    return [
        'content' => \,
        'usage' => \,
        'canceled' => \,
    ];
}
```

**关键点**：
1. **CURLOPT_WRITEFUNCTION**：逐块接收数据，实时解析
2. **\ 回调**：每次接收数据前检查，支持中途取消
3. **返回 0 中断**：curl 收到 0 会立即停止请求
4. **usage 统计**：通过 stream_options 请求，在最后一个 chunk 返回

---

# 三、SSE 渲染优化

## 3.1 问题分析

AI 模型每输出一个 token 就触发一次 onmessage，高频更新导致：
- 大量 DOM 操作，页面卡顿
- 滚动跳跃，用户体验差

**测试数据**：
- 优化前：~100 次/秒 DOM 更新
- 优化后：~20 次/秒 DOM 更新

## 3.2 双重节流方案

### 方案 1：内容缓冲 + 定时刷新

```typescript
const FLUSH_INTERVAL = 50  // 50ms flush 一次，约 20fps

let deltaBuffer = ''
let flushTimer: ReturnType<typeof setTimeout> | null = null

const flushBuffer = () => {
  if (!deltaBuffer) return
  
  streamingContent.value += deltaBuffer
  const lastMsg = messages.value[messages.value.length - 1]
  if (lastMsg) lastMsg.content = streamingContent.value
  
  deltaBuffer = ''
  throttledScroll()
}

const onContent = (delta: string) => {
  // 不直接更新 UI，先存入缓冲区
  deltaBuffer += delta
  
  if (!flushTimer) {
    flushTimer = setTimeout(() => {
      flushBuffer()
      flushTimer = null
    }, FLUSH_INTERVAL)
  }
}
```

### 方案 2：滚动节流

```typescript
const SCROLL_THROTTLE = 100  // 100ms

let lastScrollTime = 0

const throttledScroll = () => {
  const now = Date.now()
  if (now - lastScrollTime >= SCROLL_THROTTLE) {
    lastScrollTime = now
    requestAnimationFrame(() => scrollToBottom())
  }
}
```

**效果对比**：

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| DOM 更新频率 | ~100次/秒 | ~20次/秒 |
| 滚动频率 | ~100次/秒 | ~10次/秒 |
| 页面流畅度 | 明显卡顿 | 丝滑 |

---

# 四、防串话机制

## 4.1 问题场景

1. 用户在会话 A 发起 AI 对话
2. 流正在进行中，用户切换到会话 B
3. 流结束时，内容被写入了会话 B

**根因**：切换会话时，缓冲区内容未清空。

## 4.2 解决方案

```typescript
const createCallbacks = (requestConversationId: number | null) => {
  return {
    onContent: (delta) => {
      // 会话已切换，忽略
      if (currentConversationId.value !== requestConversationId) return
      deltaBuffer += delta
      startFlushTimer()
    },
    onDone: (data) => {
      //  先检查，切换了就丢弃 buffer
      if (currentConversationId.value !== requestConversationId) {
        deltaBuffer = ''
        clearTimers()
        return
      }
      
      flushBuffer()  // 确认是当前会话才 flush
    }
  }
}
```

**关键**：
- 每次发送消息时记录 
equestConversationId
- 回调中对比当前会话 ID，不匹配则丢弃数据
- onDone 时先检查再 flush，防止最后一刻串话

---

# 五、Run/Step 追踪系统

## 5.1 为什么需要追踪？

AI 调用是黑盒，出问题时难以排查：
- 用户反馈"AI 没回复"，是超时？还是 API 错误？
- 某次对话耗时 30 秒，瓶颈在哪？

**解决方案**：记录每次 AI 调用的完整过程。

## 5.2 数据库设计

```sql
-- AI 运行记录
CREATE TABLE ai_runs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    request_id VARCHAR(50) UNIQUE,
    user_id INT,
    conversation_id INT,
    agent_id INT,
    model_id INT,
    run_status TINYINT,  -- 1运行中 2成功 3失败 4已取消
    error_msg TEXT,
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT,
    duration_ms INT,
    created_at DATETIME,
    updated_at DATETIME
);

-- AI 运行步骤
CREATE TABLE ai_run_steps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    run_id INT,
    step_type TINYINT,  -- 1提示词构建 2RAG检索 3LLM调用 4工具调用 5工具返回 6最终化
    step_data JSON,
    duration_ms INT,
    created_at DATETIME
);
```

## 5.3 业务流程

```php
// 1. 创建 Run 记录
\ = \->runsDep->add([
    'request_id' => \,
    'user_id' => \,
    'conversation_id' => \,
    'agent_id' => \,
    'model_id' => \->id,
    'run_status' => AiEnum::RUN_STATUS_RUNNING,
]);

// 2. 记录 Step：提示词构建
\->stepsDep->add([
    'run_id' => \,
    'step_type' => AiEnum::STEP_TYPE_PROMPT,
    'step_data' => ['messages' => \],
]);

// 3. 记录 Step：LLM 调用
\ = microtime(true);
\ = \->chatService->chatStream(...);
\ = (int)((microtime(true) - \) * 1000);

\->stepsDep->add([
    'run_id' => \,
    'step_type' => AiEnum::STEP_TYPE_LLM,
    'step_data' => ['model' => \->model_code],
    'duration_ms' => \,
]);

// 4. 更新 Run 状态
\->runsDep->markSuccess(\, [
    'prompt_tokens' => \['usage']['prompt_tokens'],
    'completion_tokens' => \['usage']['completion_tokens'],
    'total_tokens' => \['usage']['total_tokens'],
    'duration_ms' => \,
]);
```

**价值**：
- 完整的调用链路追踪
- 性能瓶颈分析
- 错误排查依据
- Token 消耗统计

---

# 六、完整流程图

```
用户发送消息
    
前端：添加用户消息 + AI 占位消息
    
后端：创建 Run 记录（状态：运行中）
    
后端：记录 Step（提示词构建）
    
后端：调用 AiClientFactory.create(driver)
    
后端：调用 client.chatCompletionsStream()
    
后端：逐 chunk 推送给前端（SSE）
    
前端：delta 加入缓冲区
    
前端：50ms 定时 flush 到 UI
    
前端：100ms 节流滚动
    
后端：流结束，记录 Step（LLM 调用）
    
后端：更新 Run 状态（成功 + usage）
    
后端：保存 AI 消息到数据库
    
后端：异步队列生成会话标题
    
前端：收到 done 事件，flush 剩余内容
    
完成 
```

---

# 七、关键设计决策

## 7.1 为什么用工厂模式而不是策略模式？

**工厂模式**：根据驱动类型创建不同的客户端实例
**策略模式**：运行时切换不同的调用策略

AI 驱动在模型配置时就确定了，不需要运行时切换，工厂模式更简洁。

## 7.2 为什么不用 WebSocket 而用 SSE？

| 方案 | 优点 | 缺点 |
|------|------|------|
| WebSocket | 双向通信 | 复杂，需要维护连接 |
| SSE | 简单，原生支持 | 单向，只能服务端推送 |

AI 对话是典型的"服务端推送"场景，SSE 足够且更简单。

## 7.3 为什么缓冲区用 50ms 而不是 100ms？

- 50ms  20fps，人眼感知流畅
- 100ms  10fps，会有轻微卡顿感
- 30ms  33fps，收益不明显且增加 CPU 负担

## 7.4 为什么 Run/Step 不用 MongoDB？

- MySQL 足够应对（单表百万级数据）
- JSON 字段存储灵活数据
- 无需引入新技术栈

---

# 八、性能数据

| 指标 | 数值 |
|------|------|
| 首字响应时间 | < 500ms |
| 流式输出帧率 | ~20fps |
| DOM 更新频率 | ~20次/秒 |
| 滚动节流频率 | ~10次/秒 |
| 会话切换响应 | < 100ms |
| Run 记录查询 | < 50ms |

---

# 九、未来优化方向

1. **多模态支持**：语音输入、文件上传
2. **RAG 检索**：接入向量数据库
3. **工具调用**：Function Calling
4. **分支对话**：同一消息多次重新生成
5. **流式 Token 统计**：实时显示消耗

---

# 十、总结

构建一个生产级的 AI 对话系统，需要考虑：

1. **架构设计**：工厂模式统一多驱动接入
2. **性能优化**：缓冲 + 节流解决高频渲染
3. **用户体验**：防串话、可取消、流畅滚动
4. **可观测性**：Run/Step 追踪完整调用链路

这套方案已在智澜管理系统稳定运行，支撑了数千次 AI 对话。

**核心代码**：
- 后端：dmin_back/app/service/Ai/AiChatService.php
- 客户端：dmin_back/app/lib/Ai/Clients/OpenAiCompatClient.php
- 前端：dmin_front_ts/src/views/Main/ai/chat/composables/useStreamChat.ts

希望这篇文章能帮助你构建自己的 AI 对话系统。

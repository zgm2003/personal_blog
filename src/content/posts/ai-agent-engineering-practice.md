---
title: 从调 API 到 Agent 工程化：我的 AI 落地实践之路
published: 2026-02-20T10:00:00Z
description: 从最初的 API 调用到反向代理、号池管理、Agent 编排，分享 AI 工程化落地的完整实践
tags: [AI, 架构, 后端]
category: 后端技术
draft: false
---

# 写在前面

很多人觉得"会用 AI"就是会写 Prompt。但真正把 AI 落地到生产环境，你会发现 Prompt 只是冰山一角。网络怎么通？Key 怎么管？并发怎么扛？失败怎么重试？成本怎么控？这些才是 AI 工程化的核心问题。

这篇文章记录我从"调 API 玩玩"到"搭建完整 AI 基础设施"的过程，踩过的坑和总结的方法论。

## 第一阶段：直连 API 的天真时代

最开始接触大模型 API，思路很简单：拿到 Key，curl 一下，拿到结果。

```php
$response = Http::post('https://api.openai.com/v1/chat/completions', [
    'model' => 'gpt-4',
    'messages' => [['role' => 'user', 'content' => $prompt]],
]);
```

很快就遇到了现实问题：

1. 国内网络不稳定，直连经常超时
2. 单个 Key 有 RPM/TPM 限制，并发一上来就 429
3. Key 硬编码在代码里，泄露风险大
4. 不同场景想用不同模型，但切换很麻烦

这些问题逼着我开始思考：怎么把 AI 调用从"写死的代码"变成"可管理的基础设施"。

## 第二阶段：反向代理 — 解决网络问题

第一个要解决的是网络问题。方案很直接：在海外服务器上搭一层反向代理。

```nginx
server {
    listen 443 ssl;
    server_name ai-proxy.example.com;

    location /v1/ {
        proxy_pass https://api.openai.com/v1/;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header Content-Type $http_content_type;
        proxy_buffering off;  # SSE 流式输出必须关闭缓冲
        proxy_read_timeout 300s;
    }
}
```

关键细节：

- `proxy_buffering off` 是必须的，不然 SSE 流式输出会被 Nginx 缓冲，用户看到的就不是逐字输出而是一坨一坨的
- `proxy_read_timeout` 要设长一点，大模型生成长文本可能需要几十秒
- SSL 证书要配好，API 调用走 HTTPS 是基本要求

这一层代理不仅解决了网络问题，还带来了一个额外好处：所有 AI 请求都经过我的服务器，可以做日志记录、流量统计、异常监控。

但很快又遇到新问题：代理服务器的带宽和连接数也是有限的。当多个用户同时发起长对话，代理服务器的连接数会飙升。

解决方案是引入连接池和请求队列：

```php
// 使用 Guzzle 连接池，复用 TCP 连接
$client = new Client([
    'base_uri' => 'https://ai-proxy.example.com',
    'timeout' => 120,
    'connect_timeout' => 5,
    'http_errors' => false,
    'curl' => [
        CURLOPT_TCP_KEEPALIVE => 1,
        CURLOPT_TCP_KEEPIDLE => 30,
    ],
]);
```

## 第三阶段：号池管理 — 解决并发和成本问题

单个 API Key 的限制是硬伤。OpenAI 的 Tier 1 账号 RPM 只有 500，GPT-4 更低。业务量一上来，429 错误满天飞。

我的方案是搭建一个 Key 号池系统：

```php
class AiKeyPool
{
    /**
     * 从号池中获取可用的 Key
     * 策略：轮询 + 权重 + 冷却
     */
    public function getAvailableKey(string $model): ?AiKeyEntity
    {
        $keys = $this->getActiveKeys($model);

        foreach ($keys as $key) {
            // 检查是否在冷却期（被 429 后冷却 60s）
            if ($this->isInCooldown($key->id)) {
                continue;
            }

            // 检查当前分钟的请求数是否超限
            $currentRpm = $this->getCurrentRpm($key->id);
            if ($currentRpm >= $key->rpm_limit) {
                continue;
            }

            // 记录使用次数
            $this->incrementUsage($key->id);
            return $key;
        }

        return null; // 所有 Key 都不可用
    }

    /**
     * Key 被限流后进入冷却期
     */
    public function markCooldown(int $keyId, int $seconds = 60): void
    {
        Redis::setex("ai_key_cooldown:{$keyId}", $seconds, 1);
    }

    /**
     * 记录每个 Key 的使用量，用于监控和计费
     */
    private function incrementUsage(int $keyId): void
    {
        $minuteKey = "ai_key_rpm:{$keyId}:" . date('YmdHi');
        $dayKey = "ai_key_daily:{$keyId}:" . date('Ymd');

        Redis::incr($minuteKey);
        Redis::expire($minuteKey, 120);

        Redis::incr($dayKey);
        Redis::expire($dayKey, 86400 * 2);
    }
}
```

号池的核心设计思路：

1. 轮询分发：请求均匀分配到不同 Key，避免单点压力
2. 冷却机制：某个 Key 被 429 后自动冷却，不再分配请求
3. 用量统计：每个 Key 的 RPM、日用量都有记录，方便监控成本
4. 动态权重：可以给不同 Key 设置权重，比如付费 Key 权重高、免费 Key 权重低

这套号池系统上线后，429 错误率从 15% 降到了 0.3%。

### 多供应商统一接入

号池不仅管理同一个供应商的多个 Key，还要管理不同供应商的 Key。OpenAI、DeepSeek、Qwen、GLM 的 API 格式大同小异，但有细微差别。

我设计了一个模型管理表来抽象这些差异：

```sql
CREATE TABLE ai_models (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL COMMENT '模型名称',
    provider VARCHAR(30) NOT NULL COMMENT '供应商: openai/deepseek/qwen/glm',
    model_name VARCHAR(50) NOT NULL COMMENT 'API 模型标识',
    base_url VARCHAR(200) NOT NULL COMMENT 'API 地址',
    api_key TEXT NOT NULL COMMENT 'API Key（加密存储）',
    rpm_limit INT DEFAULT 500 COMMENT 'RPM 限制',
    tpm_limit INT DEFAULT 100000 COMMENT 'TPM 限制',
    input_price DECIMAL(10,6) COMMENT '输入价格 $/1K tokens',
    output_price DECIMAL(10,6) COMMENT '输出价格 $/1K tokens',
    status TINYINT DEFAULT 1,
    created_at DATETIME
);
```

关键设计：`base_url` 字段让每个模型可以指向不同的 API 地址。OpenAI 走反向代理，DeepSeek 直连国内 API，Qwen 走阿里云。这样切换模型只需要改数据库配置，不需要改代码。

```php
class AiChatService
{
    public function chat(array $messages, AiModels $model): ChatResult
    {
        $client = new Client([
            'base_uri' => $model->base_url,
            'timeout' => 120,
        ]);

        // 所有供应商都兼容 OpenAI 格式
        $response = $client->post('/v1/chat/completions', [
            'headers' => [
                'Authorization' => 'Bearer ' . decrypt($model->api_key),
                'Content-Type' => 'application/json',
            ],
            'json' => [
                'model' => $model->model_name,
                'messages' => $messages,
                'temperature' => $model->temperature ?? 0.7,
                'max_tokens' => $model->max_tokens ?? 4096,
            ],
        ]);

        return ChatResult::fromResponse(json_decode($response->getBody(), true));
    }
}
```

为什么所有供应商都用 OpenAI 格式？因为 DeepSeek、Qwen、GLM 都兼容 OpenAI 的 API 格式。这是行业事实标准，一套代码接入所有模型。

### 成本控制：预算告警

号池不仅管理并发，还管理成本。每个 Key 都有日预算限制：

```php
public function checkBudget(int $keyId): bool
{
    $key = $this->getKey($keyId);
    $todayUsage = $this->getTodayUsage($keyId);

    // 计算今日花费
    $cost = ($todayUsage['input_tokens'] / 1000) * $key->input_price
          + ($todayUsage['output_tokens'] / 1000) * $key->output_price;

    if ($cost >= $key->daily_budget) {
        Log::warning("Key {$keyId} 已达日预算上限: \${$cost}");
        return false;
    }

    // 80% 预警
    if ($cost >= $key->daily_budget * 0.8) {
        $this->sendBudgetAlert($keyId, $cost, $key->daily_budget);
    }

    return true;
}
```

这套预算系统避免了一个真实发生过的事故：某次 Prompt 写错导致死循环调用，如果没有预算限制，一晚上能烧掉几百美元。

## 第四阶段：智能体系统 — 从 API 调用到 Agent 编排

解决了基础设施问题后，下一步是让 AI 调用变得更灵活。不同业务场景需要不同的 Prompt、不同的模型、不同的参数。

我设计了一套智能体（Agent）管理系统：

```sql
CREATE TABLE ai_agents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '智能体名称',
    system_prompt TEXT COMMENT '系统提示词',
    model_id INT NOT NULL COMMENT '关联的模型',
    scene VARCHAR(30) NOT NULL DEFAULT 'chat' COMMENT '使用场景',
    mode VARCHAR(20) NOT NULL DEFAULT 'chat' COMMENT '对话模式',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INT DEFAULT 4096,
    status TINYINT DEFAULT 1,
    created_at DATETIME
);
```

`scene` 字段是关键设计。同一个智能体系统，通过 `scene` 区分不同的使用场景：

- `chat`：日常对话，温度高一点，回答更有创意
- `goods_script`：电商口播词生成，温度低一点，输出更稳定

```php
class AiAgentsDep extends BaseDep
{
    /**
     * 根据场景获取激活的智能体
     */
    public function getActiveByScene(string $scene): ?Model
    {
        return $this->model
            ->where('scene', $scene)
            ->where('status', CommonEnum::STATUS_ACTIVE)
            ->orderBy('id', 'desc')
            ->first();
    }
}
```

智能体 + 模型的组合让 AI 调用变得非常灵活。运营人员可以在后台直接调整 Prompt 和参数，不需要改代码、不需要发版。

## 第五阶段：AI 运行监控 — 让每次调用都可追溯

AI 调用不像普通接口，它有不确定性。同样的输入可能产生不同的输出，而且成本不低（GPT-4 一次调用可能几毛钱）。所以必须有完善的监控。

我设计了两张表来记录每次 AI 调用：

```
ai_runs（运行记录）
├── agent_id     → 用了哪个智能体
├── model_id     → 用了哪个模型
├── input_tokens → 输入 Token 数
├── output_tokens → 输出 Token 数
├── duration_ms  → 耗时
├── status       → 成功/失败
└── ai_run_steps（运行步骤）
    ├── step: PROMPT    → 构建提示词
    ├── step: LLM       → 模型调用
    └── step: FINALIZE  → 结果处理
```

每次 AI 调用都会记录完整的链路：用了什么 Prompt、调了什么模型、花了多少 Token、耗时多久。这些数据不仅用于排查问题，还能用于成本分析和效果优化。

```php
// 记录一次完整的 AI 调用
$run = AiRun::create([
    'agent_id' => $agent->id,
    'model_id' => $agent->model_id,
    'scene' => 'goods_script',
    'status' => 'running',
]);

// Step 1: 构建 Prompt
AiRunStep::create([
    'run_id' => $run->id,
    'step' => 'PROMPT',
    'input' => json_encode($messages),
    'started_at' => now(),
]);

// Step 2: 调用模型
$result = $aiChatService->chat($messages, $model);

// Step 3: 记录结果
AiRunStep::create([
    'run_id' => $run->id,
    'step' => 'LLM',
    'output' => $result->content,
    'tokens_in' => $result->usage->prompt_tokens,
    'tokens_out' => $result->usage->completion_tokens,
]);
```

有了这套监控，我可以清楚地知道：

- 每天花了多少钱在 AI 上
- 哪个智能体的效果最好
- 哪些调用失败了，失败原因是什么
- 平均响应时间是多少，有没有变慢的趋势

### 监控面板数据示例

```
┌─────────────────────────────────────────────────┐
│  AI 调用监控面板                                  │
├─────────────────────────────────────────────────┤
│  今日调用次数：347                                │
│  成功率：98.6%                                   │
│  平均响应时间：3.2s                               │
│  今日 Token 消耗：1,247,832                      │
│  今日费用：$4.73                                  │
├─────────────────────────────────────────────────┤
│  按场景统计：                                     │
│  chat:          218 次  $2.89  avg 2.8s          │
│  goods_script:  129 次  $1.84  avg 3.9s          │
├─────────────────────────────────────────────────┤
│  按模型统计：                                     │
│  deepseek-v4:   201 次  $0.42  avg 2.1s          │
│  gpt-5.3:        89 次  $3.15  avg 4.7s          │
│  qwen-3.5:       57 次  $1.16  avg 3.4s          │
└─────────────────────────────────────────────────┘
```

这些数据直接驱动了模型选择的决策。比如发现 DeepSeek V4 在口播词生成场景的效果和 GPT-5.3 差不多，但成本只有 1/7，于是把 `goods_script` 场景的默认模型从 GPT 切到了 DeepSeek。

## 第六阶段：错误处理与优雅降级

AI 服务不是 100% 可靠的。网络波动、服务降级、Token 超限都可能导致调用失败。一个生产级的 AI 系统必须有完善的错误处理。

### 重试策略

```php
class AiRetryHandler
{
    private const RETRYABLE_CODES = [429, 500, 502, 503, 504];
    private const MAX_RETRIES = 3;

    public function callWithRetry(callable $fn): mixed
    {
        $lastException = null;

        for ($attempt = 0; $attempt <= self::MAX_RETRIES; $attempt++) {
            try {
                return $fn();
            } catch (AiApiException $e) {
                $lastException = $e;

                if (!in_array($e->getCode(), self::RETRYABLE_CODES)) {
                    throw $e; // 不可重试的错误直接抛出
                }

                if ($attempt === self::MAX_RETRIES) {
                    throw $e; // 重试次数用完
                }

                // 指数退避：1s, 2s, 4s
                $delay = pow(2, $attempt);

                // 429 特殊处理：读取 Retry-After 头
                if ($e->getCode() === 429 && $e->retryAfter) {
                    $delay = max($delay, $e->retryAfter);
                }

                Log::info("AI 调用重试 #{$attempt}, 等待 {$delay}s", [
                    'error' => $e->getMessage(),
                ]);

                sleep($delay);
            }
        }

        throw $lastException;
    }
}
```

### 模型降级

当主模型不可用时，自动切换到备用模型：

```php
public function chatWithFallback(array $messages, string $scene): ChatResult
{
    // 获取场景对应的智能体（可能有多个，按优先级排序）
    $agents = $this->dep(AiAgentsDep::class)->getActiveByScene($scene);

    foreach ($agents as $agent) {
        $model = AiModels::find($agent->model_id);

        try {
            return $this->retryHandler->callWithRetry(
                fn() => $this->aiChatService->chat($messages, $model)
            );
        } catch (AiApiException $e) {
            Log::warning("模型 {$model->name} 不可用，尝试降级", [
                'error' => $e->getMessage(),
            ]);
            continue; // 尝试下一个模型
        }
    }

    throw new BusinessException('所有 AI 模型均不可用，请稍后再试');
}
```

这套降级机制在实际运行中救过好几次。有一次 OpenAI 服务降级了 2 小时，系统自动切到 DeepSeek，用户完全无感知。

## 总结：AI 工程化的核心能力

回顾这段经历，我觉得 AI 工程化的核心不是"会写 Prompt"，而是：

1. 基础设施能力：网络代理、Key 管理、连接池
2. 系统设计能力：智能体抽象、场景隔离、配置化管理
3. 可观测性：调用链路追踪、成本监控、效果评估
4. 工程化思维：异步队列、错误重试、优雅降级

AI 只是一个能力，怎么把这个能力稳定、高效、可控地集成到业务系统中，才是 Agent 工程师真正要解决的问题。

在我看来，未来不会有"前端工程师"和"后端工程师"的严格区分，而是"能不能用最合适的技术解决问题"。语言和框架只是工具，选择合适的工具、设计合理的架构、让 AI 真正产生业务价值，这才是核心竞争力。

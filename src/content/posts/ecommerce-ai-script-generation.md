---
title: "电商 AI 口播生成系统：OCR、Agent、TTS 与队列闭环"
published: 2026-02-18T10:00:00Z
draft: false
tags: [置顶, AI, Agent, Redis, 异步, 后端]
description: "基于 OCR、Redis 异步队列、Agent 编排和 TTS 合成的电商口播自动生成系统，展示 AI 落地到业务流水线的能力。"
category: AI 技术
---

> **本文价值**：这篇文章保留的是业务落地能力：从商品信息到 OCR、Agent 生成、TTS 合成和异步队列闭环。

# 业务背景

做电商直播的朋友都知道，每个商品都需要一段口播词。主播拿到商品后，要提炼卖点、组织话术、录制音频。一个品可能要花 30 分钟到 1 小时。

如果一天要上 50 个品呢？纯人工根本扛不住。

我们的目标是：把这个流程自动化。选品 → OCR 识别商品信息 → AI 生成口播词 → TTS 合成语音，全链路打通，人只需要做最终审核。

## 系统架构

```
浏览器插件（选品）
    ↓
后台管理系统（商品管理）
    ↓
Redis 异步队列
    ├── OCR 识别（图片 → 文字）
    ├── AI 生成（文字 → 口播词）
    └── TTS 合成（口播词 → 音频）
```

整个系统分为三个核心环节，每个环节都是异步的，通过状态机驱动流转。

## 状态机设计

这是整个系统的骨架。一个商品从录入到完成，经历 7 个状态：

```
待处理(1) → OCR中(2) → 已识别(3) → 生成中(4) → 已生成(5) → TTS中(6) → 已完成(7)
                                                                          ↘ 失败(8)
```

```php
class GoodsEnum
{
    // 状态流转定义
    public static array $statusFlow = [
        1 => [2],      // 待处理 → OCR中
        2 => [3, 8],   // OCR中 → 已识别 / 失败
        3 => [4],      // 已识别 → 生成中
        4 => [5, 8],   // 生成中 → 已生成 / 失败
        5 => [6],      // 已生成 → TTS中
        6 => [7, 8],   // TTS中 → 已完成 / 失败
    ];

    /**
     * 校验状态流转是否合法
     */
    public static function canTransit(int $from, int $to): bool
    {
        return in_array($to, self::$statusFlow[$from] ?? []);
    }
}
```

为什么要用状态机而不是简单的标记？因为并发场景下，如果不校验状态流转，可能出现：

- 用户点了两次 OCR，同一个商品被识别两次
- OCR 还没完成，用户就点了生成，导致用空数据去生成
- 失败的商品被重新触发，但状态没有正确回退

状态机保证了每次操作都是合法的，避免了这些边界问题。

## 异步队列：为什么不能同步？

OCR、AI 生成、TTS 这三个操作有一个共同特点：慢。

- OCR 识别一张图片：2-5 秒
- AI 生成一段口播词：5-15 秒
- TTS 合成一段音频：3-8 秒

如果同步处理，用户点一下按钮要等 10-30 秒才能得到响应。而且这些操作都依赖外部 API，网络波动、服务降级都可能导致超时。

所以必须异步。用户点击后立即返回"任务已提交"，后台通过 Redis 队列慢慢处理。

```php
class GoodsModule extends BaseModule
{
    public function ocr($request): array
    {
        $param = $this->validate($request, GoodsValidate::ocr());

        // 1. 校验状态：只有"待处理"和"已识别"可以触发 OCR
        $goods = $this->dep(GoodsDep::class)->getById($param['id']);
        if (!in_array($goods->status, [1, 3])) {
            return [null, 400, '当前状态不允许执行 OCR'];
        }

        // 2. 更新状态为"OCR中"
        $this->dep(GoodsDep::class)->transitStatus($param['id'], 2);

        // 3. 投递到异步队列
        Redis::send('goods-slow-queue', [
            'action' => 'ocr',
            'goods_id' => $param['id'],
            'image_list' => $param['image_list_success'],
        ]);

        return [null, 0, 'OCR 任务已提交'];
    }
}
```

注意这里的设计：先改状态，再投队列。这样即使队列投递失败，状态也已经变成了"OCR中"，前端能看到正确的状态。如果队列消费失败，消费者会把状态改为"失败"。

## 队列消费者设计

消费者是整个系统最核心的部分。它需要处理三种任务，每种任务的逻辑不同，但错误处理模式是统一的。

```php
class GoodsProcess implements Consumer
{
    public string $queue = 'goods-slow-queue';

    public function consume($data): void
    {
        try {
            match ($data['action']) {
                'ocr' => $this->handleOcr($data),
                'generate' => $this->handleGenerate($data),
                'tts' => $this->handleTts($data),
            };
        } catch (\Throwable $e) {
            // 统一错误处理：更新状态为失败，记录错误信息
            $this->markFailed($data['goods_id'], $e->getMessage());
            Log::error("Goods queue failed", [
                'action' => $data['action'],
                'goods_id' => $data['goods_id'],
                'error' => $e->getMessage(),
            ]);
        }
    }
}
```

### OCR 处理

OCR 的核心是把商品详情图片里的文字提取出来。电商商品图片通常包含大量信息：规格参数、卖点描述、促销信息等。

```php
private function handleOcr(array $data): void
{
    $goods = Goods::find($data['goods_id']);
    $images = $data['image_list'];

    // 逐张识别，合并结果
    $ocrResults = [];
    foreach ($images as $imageUrl) {
        $result = $this->ocrService->recognize($imageUrl);
        if ($result) {
            $ocrResults[] = $result;
        }
    }

    $ocrText = implode("\n\n", $ocrResults);

    // 更新商品数据
    $goods->update([
        'ocr' => $ocrText,
        'image_list_success' => json_encode($images),
        'status' => 3, // 已识别
    ]);
}
```

### AI 生成：智能体 + 模型的组合

这是最有意思的部分。AI 生成不是简单地把 OCR 文本丢给大模型，而是通过智能体系统来编排。

```php
private function handleGenerate(array $data): void
{
    $goods = Goods::find($data['goods_id']);

    // 获取指定的智能体（前端选择的）
    $agent = AiAgents::find($data['agent_id']);
    if (!$agent) {
        // 降级：使用默认的口播词生成智能体
        $agent = $this->dep(AiAgentsDep::class)
            ->getActiveByScene('goods_script');
    }

    $model = AiModels::find($agent->model_id);

    // 构建消息
    $messages = [
        ['role' => 'system', 'content' => $agent->system_prompt],
        ['role' => 'user', 'content' => $this->buildUserPrompt($goods)],
    ];

    // 记录 AI 运行日志
    $run = $this->createRun($agent, 'goods_script');
    $this->createStep($run, 'PROMPT', json_encode($messages));

    // 调用模型
    $result = $this->aiChatService->chat($messages, $model);

    $this->createStep($run, 'LLM', $result->content, [
        'tokens_in' => $result->usage->prompt_tokens,
        'tokens_out' => $result->usage->completion_tokens,
    ]);

    // 解析结果：提取卖点和口播词
    [$point, $scriptText] = $this->parseGenerateResult($result->content);

    $goods->update([
        'point' => $point,
        'script_text' => $scriptText,
        'model_origin' => $model->name,
        'status' => 5, // 已生成
    ]);

    $this->finalizeRun($run, 'success');
}
```

`buildUserPrompt` 方法会把商品的标题、OCR 文本、用户自定义提示词组合成一个结构化的 Prompt：

```php
private function buildUserPrompt(Goods $goods): string
{
    $parts = ["商品标题：{$goods->title}"];

    if ($goods->ocr) {
        $parts[] = "商品详情（OCR 识别结果）：\n{$goods->ocr}";
    }

    if ($goods->tips) {
        $parts[] = "额外要求：{$goods->tips}";
    }

    $parts[] = "请根据以上信息，生成商品卖点和口播词。";

    return implode("\n\n", $parts);
}
```

这里有一个设计决策：为什么让用户选择智能体而不是固定一个？

因为不同品类的商品需要不同的话术风格。美妆产品需要精致优雅的表达，数码产品需要参数对比和性价比分析，食品需要突出口感和新鲜度。通过不同的智能体（不同的 System Prompt），可以让 AI 输出更贴合品类特点的口播词。

## 前端工作台设计

前端采用全屏工作台的设计，把商品编辑变成一个沉浸式的工作流程。

```
┌─────────────────────────────────────────────────────┐
│ 编辑商品  [已生成]                              [×] │
├─────────────────────────────────────────────────────┤
│ 详情图片（点击选择需要识别的图片）                    │
│ [☑ img1] [☑ img2] [☐ img3] [☑ img4] ...           │
│ [OCR识别（3张已选）]                                 │
├────────────┬───────────┬───────────┬────────────────┤
│ 商品信息   │ AI提示词  │ 卖点      │ 口播词         │
│            │           │           │                │
│ 标题: xxx  │ 智能体:   │ (textarea)│ (textarea)     │
│ 链接: xxx  │ [选择▾]   │           │                │
│ OCR结果:   │ 提示词:   │           │                │
│ (readonly) │ (textarea)│           │                │
│            │ [生成]    │           │                │
├────────────┴───────────┴───────────┴────────────────┤
│                              [取消]  [确认]          │
└─────────────────────────────────────────────────────┘
```

四列布局的设计思路：

1. 商品信息：基础数据和 OCR 结果，只读参考
2. AI 提示词工程：选择智能体、填写额外提示、触发生成
3. 卖点：AI 生成的卖点，可以手动编辑调整
4. 口播词：最终的口播词，可以手动润色

这个布局让用户能同时看到输入（左边）和输出（右边），方便对比和调整。操作完 OCR 或生成后，弹窗自动关闭并刷新列表，用户可以看到状态变化。

## 浏览器插件：选品入口

选品是整个流程的起点。我们开发了一个 Chrome 扩展，用户在电商平台浏览商品时，一键就能把商品信息抓取到系统里。

插件采用 Manifest V3，支持淘宝、京东、天猫、拼多多等主流平台。每个平台有独立的 scraper，因为不同平台的页面结构差异很大。

```javascript
// 平台识别 + 对应 scraper 调用
const scrapers = {
    'taobao.com': scrapeTaobao,
    'jd.com': scrapeJD,
    'tmall.com': scrapeTmall,
    'pinduoduo.com': scrapePDD,
};

function detectPlatform(url) {
    for (const [domain, scraper] of Object.entries(scrapers)) {
        if (url.includes(domain)) return { platform: domain, scraper };
    }
    return null;
}
```

抓取的数据包括：商品标题、主图、详情图列表、价格、链接。这些数据通过 API 提交到后台，自动创建一条商品记录，状态为"待处理"。

## 性能数据

系统上线后的实际数据：

| 指标 | 人工处理 | 系统处理 | 提升 |
|------|---------|---------|------|
| 单品处理时间 | 30-60 分钟 | 20-40 秒 | 60-90x |
| 日处理量 | 10-20 品 | 200+ 品 | 10-20x |
| 口播词质量 | 依赖个人水平 | 稳定中上 | 一致性更好 |

当然，AI 生成的口播词不是完美的，有时候需要人工润色。但它把 80% 的重复劳动自动化了，人只需要做最后 20% 的创意调整。

## 踩过的坑

1. OCR 图片顺序很重要：电商详情图是有逻辑顺序的，打乱顺序会导致 OCR 结果混乱，AI 生成的口播词也会逻辑不通
2. Prompt 要结构化：直接把 OCR 文本丢给 AI 效果很差，需要用结构化的 Prompt 引导 AI 分步骤输出
3. 异步队列要有超时机制：外部 API 可能无限等待，消费者必须设置超时，否则会阻塞整个队列
4. 状态机要有"重试"入口：失败的商品需要能重新触发，但要回退到正确的前置状态

## 写在最后

这个系统的核心价值不是"用了 AI"，而是把一个复杂的业务流程拆解成了可自动化的步骤，然后用合适的技术（异步队列、状态机、智能体编排）把它们串起来。

AI 是其中的一个环节，但不是全部。工程化的能力才是让 AI 真正产生业务价值的关键。

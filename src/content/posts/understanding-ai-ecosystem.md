---
title: 从 LLM 到 Agent：一个开发者视角的 AI 全景认知图谱
published: 2026-02-22T10:00:00Z
description: 从底层的大语言模型到上层的 Agent 编排，系统梳理 LLM、Prompt Engineering、Function Calling、RAG、MCP、Skill、Agent 等核心概念，构建完整的 AI 认知体系
tags: [置顶, AI, LLM, Agent, MCP]
category: AI 技术
draft: false
---

# 写在前面

过去一年，AI 领域的概念像井喷一样涌出来：LLM、Prompt Engineering、RAG、Function Calling、Agent、MCP、Skill、Tool Use、Chain of Thought……每隔几周就有新名词冒出来，搞得很多开发者一头雾水。

我自己也经历了从"这都是什么"到"原来是这么回事"的过程。这篇文章不是学术论文，而是一个工程师的理解笔记。我会用尽量直白的语言，把这些概念之间的关系讲清楚，帮你建立一个完整的认知框架。

先放一张全景图，后面逐层展开：

```
┌─────────────────────────────────────────────────────────┐
│                      应用层                              │
│   Agent（智能体）= LLM + Memory + Tools + Planning      │
├─────────────────────────────────────────────────────────┤
│                      协议层                              │
│   MCP（模型上下文协议）= 标准化的工具接入方式              │
├─────────────────────────────────────────────────────────┤
│                      能力层                              │
│   Function Calling / Tool Use / RAG / Skill             │
├─────────────────────────────────────────────────────────┤
│                      交互层                              │
│   Prompt Engineering / Chain of Thought / Few-shot      │
├─────────────────────────────────────────────────────────┤
│                      模型层                              │
│   LLM（大语言模型）= GPT / Claude / DeepSeek / Qwen     │
└─────────────────────────────────────────────────────────┘
```

理解 AI，从最底层开始。

## 第一层：LLM — 一切的基石

LLM，Large Language Model，大语言模型。这是整个 AI 浪潮的核心引擎。

### LLM 到底是什么？

用最简单的话说：LLM 是一个超大规模的"文字接龙"程序。你给它一段文字，它预测下一个最可能出现的词，然后把这个词加到文字后面，再预测下一个……如此循环，就生成了一段完整的回答。

```
输入：今天天气
预测：真 → 不 → 错 → ， → 适 → 合 → 出 → 去 → 走 → 走
输出：今天天气真不错，适合出去走走
```

但这个"接龙"不是随机的。LLM 在训练阶段读了互联网上几乎所有的公开文本——维基百科、书籍、论文、代码、论坛帖子。它从这些海量数据中学到了语言的规律、知识的关联、逻辑的推理方式。

所以 LLM 不只是在"接龙"，它是在基于对世界知识的理解来"接龙"。

### 2026 年主流 LLM 格局

AI 模型的迭代速度快得离谱。2024 年大家还在聊 GPT-4，现在已经是 GPT-5.3 和 Claude Opus 4.6 的时代了。作为开发者，你需要了解当前的主流模型：

| 模型 | 厂商 | 特点 | 适用场景 |
|------|------|------|---------|
| GPT-5.3 Codex | OpenAI | 推理能力顶级，编码极强 | 复杂推理，代码生成 |
| Claude Opus 4.6 | Anthropic | 100 万 Token 上下文，推理 benchmark 领先 | 长文档处理，深度分析 |
| Gemini 3 Pro | Google | 原生多模态，超大上下文 | 多模态任务，信息检索 |
| DeepSeek V4 | DeepSeek | Engram 记忆技术，100 万上下文，成本极低 | 代码场景，成本敏感业务 |
| Qwen 3.5 | 阿里 | 397B 参数 MoE 架构，Apache 2.0 开源，支持 201 种语言 | 私有化部署，Agentic AI |
| Grok 4.1 | xAI | 200 万 Token 上下文 | 超长文档，实时信息 |
| GLM-5 | 智谱 | 745B MoE 开源，成本约 $0.11/MTok | 国内业务，极致性价比 |

2026 年的模型竞争格局和两年前完全不同。几个关键变化：

1. 上下文窗口爆炸式增长：从 128K 到 100 万甚至 200 万 Token，长文档处理不再是瓶颈
2. 价格断崖式下降：GPT-5.3 Codex 约 $1.75/MTok，GLM-5 低至 $0.11/MTok，AI 调用成本已经不是主要顾虑
3. 开源模型崛起：Qwen 3.5、DeepSeek V4、GLM-5 都是开源或半开源，私有化部署成为现实选择
4. Agentic 能力成为标配：Qwen 3.5 原生支持 Visual Agent，能自主操作桌面和移动端应用

选模型不是选"最强的"，而是选"最合适的"。一个简单的文本分类任务，用 Claude Opus 4.6 是杀鸡用牛刀，用 DeepSeek 的轻量模型就够了，成本可能差 50 倍。

### Temperature：控制创造力的旋钮

LLM 有一个关键参数叫 `temperature`（温度），它决定了模型输出的"创造力"：

```
temperature = 0：确定性输出，每次结果几乎一样
temperature = 0.7：平衡模式，有一定随机性
temperature = 1.0：高创造力，输出更多样
temperature > 1.0：非常随机，可能出现胡言乱语
```

实际应用中：
- 代码生成：temperature 0-0.3（要准确）
- 日常对话：temperature 0.7（要自然）
- 创意写作：temperature 0.9-1.0（要有想象力）
- 电商口播词：temperature 0.5-0.7（要稳定但不死板）

这不是玄学，是概率分布的数学控制。temperature 越低，模型越倾向于选择概率最高的词；越高，低概率的词也有机会被选中。

### Token：LLM 的计量单位

LLM 不是按"字"来处理文本的，而是按 Token。一个 Token 大约是 3/4 个英文单词，或者半个到一个中文字。

```
"Hello world" → 2 tokens
"你好世界" → 2-4 tokens（取决于分词器）
```

为什么要关心 Token？因为：

1. 计费按 Token 算：Claude Opus 4.6 约 $5/MTok，GPT-5.3 Codex 约 $1.75/MTok，GLM-5 低至 $0.11/MTok
2. 上下文窗口虽然已经到了百万级别，但输入越长，成本越高，速度越慢
3. 长上下文不等于"什么都往里塞"——模型对中间位置信息的注意力仍然偏弱（Lost in the Middle 问题）

所以在工程实践中，Prompt 的长度控制非常重要。不是给模型的信息越多越好，而是要给"精准的"信息。

## 第二层：Prompt Engineering — 和 AI 对话的艺术

有了 LLM，下一个问题是：怎么让它按你的意思输出？

这就是 Prompt Engineering（提示词工程）。听起来很高大上，本质就是"怎么跟 AI 说话，它才能听懂你要什么"。

### System Prompt vs User Prompt

大模型的消息格式通常分三种角色：

```json
[
  { "role": "system", "content": "你是一个专业的电商口播词撰写专家..." },
  { "role": "user", "content": "帮我写一段关于这款蓝牙耳机的口播词" },
  { "role": "assistant", "content": "家人们看过来！这款蓝牙耳机..." }
]
```

- `system`：设定 AI 的身份、行为规则、输出格式。这是"人设"
- `user`：用户的输入
- `assistant`：AI 的回复

System Prompt 是 Prompt Engineering 的核心。一个好的 System Prompt 能让同一个模型表现出完全不同的能力。

### 几种关键的 Prompt 技巧

**Zero-shot（零样本）**：直接告诉模型要做什么，不给例子。

```
请将以下文本分类为"正面"或"负面"：
"这个产品质量太差了，用了一天就坏了"
```

**Few-shot（少样本）**：给几个例子，让模型学会模式。

```
文本："这个手机拍照效果很好" → 正面
文本："物流太慢了等了一周" → 负面
文本："包装精美，送人很合适" → ?
```

**Chain of Thought（思维链）**：让模型一步步推理，而不是直接给答案。

```
请一步步分析这个商品的卖点：
1. 首先，识别商品的核心功能
2. 然后，找出与竞品的差异化优势
3. 接着，提炼出 3-5 个关键卖点
4. 最后，用口语化的方式组织成口播词
```

Chain of Thought 对复杂任务特别有效。研究表明，加上"Let's think step by step"这句话，GPT-4 在数学推理任务上的准确率能提升 20% 以上。

**结构化输出**：要求模型按特定格式输出，方便程序解析。

```
请按以下 JSON 格式输出：
{
  "selling_points": ["卖点1", "卖点2", "卖点3"],
  "script": "口播词正文...",
  "duration_estimate": "预计时长（秒）"
}
```

### Prompt 工程的本质

很多人觉得 Prompt Engineering 就是"调咒语"，试来试去找到一个好用的 Prompt。这是初级阶段。

高级阶段是理解 LLM 的工作原理，然后有针对性地设计 Prompt：

- LLM 是基于上下文预测的 → 所以给它足够的上下文信息
- LLM 容易"幻觉"（编造事实）→ 所以要求它"只基于提供的信息回答"
- LLM 对格式敏感 → 所以用清晰的结构化 Prompt
- LLM 的注意力有偏向 → 重要信息放在开头和结尾，中间容易被忽略

在我的电商口播词系统中，System Prompt 是这样设计的：

```
你是一位资深的电商直播口播词撰写专家。

## 输出要求
1. 先输出 3-5 个核心卖点（每个不超过 15 字）
2. 再输出完整的口播词（200-400 字）
3. 口播词要口语化，适合主播直接朗读
4. 用"---"分隔卖点和口播词

## 风格要求
- 语气亲切自然，像朋友推荐
- 突出性价比和使用场景
- 避免虚假宣传和绝对化用语
```

这个 Prompt 不是拍脑袋写的，是经过几十次迭代调优的结果。每次调整都基于实际输出的质量反馈。

## 第三层：Function Calling & Tool Use — 让 LLM 长出"手脚"

LLM 有一个致命的局限：它只能处理文本。它不能查数据库、不能调 API、不能读文件、不能执行代码。它就像一个知识渊博但被关在房间里的人——什么都知道，但什么都做不了。

Function Calling（函数调用）就是给 LLM 开了一扇门。

### 工作原理

Function Calling 的核心思路是：告诉 LLM 有哪些工具可以用，让它自己决定什么时候用、怎么用。

```
你（开发者）→ 告诉 LLM：你可以用这些工具
  - search_database(query): 搜索数据库
  - get_weather(city): 查天气
  - send_email(to, subject, body): 发邮件

用户 → "帮我查一下北京今天的天气，然后发邮件告诉张三"

LLM → 思考后决定：
  1. 先调用 get_weather("北京")
  2. 拿到结果后，调用 send_email("zhangsan@example.com", "北京天气", "...")
```

LLM 并不是真的在"执行"这些函数。它只是输出一个结构化的调用请求，由你的程序去实际执行，然后把结果返回给 LLM，LLM 再基于结果继续生成回答。

```
完整流程：
用户输入 → LLM 分析 → 输出函数调用请求 → 你的程序执行函数 → 结果返回给 LLM → LLM 生成最终回答
```

### 代码示例

以 OpenAI 的 API 为例：

```php
$response = $client->chat()->create([
    'model' => 'gpt-4o',
    'messages' => $messages,
    'tools' => [
        [
            'type' => 'function',
            'function' => [
                'name' => 'search_goods',
                'description' => '根据关键词搜索商品数据库',
                'parameters' => [
                    'type' => 'object',
                    'properties' => [
                        'keyword' => [
                            'type' => 'string',
                            'description' => '搜索关键词',
                        ],
                        'platform' => [
                            'type' => 'string',
                            'enum' => ['taobao', 'jd', 'pdd'],
                            'description' => '电商平台',
                        ],
                    ],
                    'required' => ['keyword'],
                ],
            ],
        ],
    ],
]);

// LLM 可能返回一个函数调用请求
if ($response->choices[0]->message->tool_calls) {
    $toolCall = $response->choices[0]->message->tool_calls[0];
    $args = json_decode($toolCall->function->arguments, true);
    
    // 你来执行实际的函数
    $result = $this->searchGoods($args['keyword'], $args['platform'] ?? null);
    
    // 把结果返回给 LLM
    $messages[] = [
        'role' => 'tool',
        'tool_call_id' => $toolCall->id,
        'content' => json_encode($result),
    ];
    
    // LLM 基于结果生成最终回答
    $finalResponse = $client->chat()->create([
        'model' => 'gpt-4o',
        'messages' => $messages,
    ]);
}
```

Function Calling 是 LLM 从"聊天机器人"进化为"能干活的助手"的关键一步。没有它，LLM 就只能纸上谈兵。

### Tool Use 的边界

需要注意的是，LLM 调用工具不是万能的。它有几个限制：

1. LLM 可能"幻觉"出不存在的函数名或参数
2. LLM 可能在不需要调用工具的时候强行调用
3. 复杂的多步骤工具调用，LLM 可能搞错顺序

所以在工程实践中，你需要：
- 对 LLM 返回的函数调用做严格校验
- 设置白名单，只允许调用预定义的函数
- 对敏感操作（删除、支付）加二次确认

## 第四层：RAG — 给 LLM 装上"外部记忆"

LLM 的知识有一个截止日期。GPT-4 的训练数据截止到 2024 年初，它不知道 2024 年之后发生的事。而且它不知道你公司的内部文档、你的产品手册、你的客户数据。

RAG（Retrieval-Augmented Generation，检索增强生成）就是解决这个问题的。

### 原理

RAG 的思路很直接：在让 LLM 回答之前，先从你的知识库里检索相关信息，然后把这些信息塞到 Prompt 里，让 LLM 基于这些信息来回答。

```
用户问题："我们公司的退货政策是什么？"

传统 LLM → "一般来说，退货政策包括..." （瞎编的）

RAG 流程：
1. 把问题转成向量（Embedding）
2. 在向量数据库中检索最相关的文档片段
3. 找到：《客服手册》第3章 - 退货政策：7天无理由退货...
4. 把检索到的内容 + 用户问题一起发给 LLM
5. LLM 基于真实文档回答："根据我们的政策，支持7天无理由退货..."
```

### 向量检索是怎么工作的？

这里涉及一个关键技术：Embedding（向量嵌入）。

简单说，Embedding 就是把文本转成一组数字（向量）。语义相近的文本，向量也相近。

```
"苹果手机" → [0.23, 0.87, 0.12, ...]
"iPhone"   → [0.25, 0.85, 0.14, ...]  ← 很接近
"今天天气" → [0.91, 0.03, 0.67, ...]  ← 很远
```

通过计算向量之间的距离（余弦相似度），就能找到语义最相关的文档片段。这比传统的关键词搜索强大得多——用户搜"手机"也能匹配到包含"iPhone"的文档。

### RAG vs 微调

很多人会问：为什么不直接微调（Fine-tune）模型，让它学会你的知识？

| 维度 | RAG | 微调 |
|------|-----|------|
| 成本 | 低（只需要向量数据库） | 高（需要 GPU 训练） |
| 更新 | 实时（改文档即生效） | 慢（需要重新训练） |
| 准确性 | 高（基于真实文档） | 可能幻觉 |
| 适用场景 | 知识问答、文档检索 | 风格迁移、特定任务 |

大多数企业场景，RAG 是更实用的选择。微调更适合需要改变模型"行为模式"的场景，比如让模型学会特定的写作风格。

## 第五层：MCP — 工具接入的"USB 接口"

MCP，Model Context Protocol，模型上下文协议。这是 Anthropic 在 2024 年底提出的开放协议，2025 年 12 月捐赠给了 Linux 基金会的 Agentic AI Foundation。目前 OpenAI、Google、Microsoft 都已支持 MCP，它已经成为 AI 工具接入的行业标准。截至 2025 年底，GitHub 上已经有超过 13000 个 MCP Server。

### 为什么需要 MCP？

在 MCP 出现之前，每个 AI 应用要接入外部工具，都需要自己写一套集成代码。

比如你想让 AI 助手能查数据库、读文件、调 API，你需要：
- 为每个工具写 Function Calling 的定义
- 写工具的执行逻辑
- 处理认证、错误、超时
- 如果换一个 AI 平台，所有代码重写

这就像早期的手机充电器，每个品牌一个接口，出门要带一堆线。

MCP 就是 AI 领域的"USB-C"。它定义了一套标准协议，让任何 AI 应用都能用统一的方式接入任何工具。

### MCP 的架构

```
┌──────────────┐     MCP 协议     ┌──────────────┐
│  MCP Client  │ ←──────────────→ │  MCP Server  │
│  (AI 应用)   │                  │  (工具提供方) │
│              │  JSON-RPC 2.0    │              │
│  Kiro/Cursor │  stdio/SSE      │  数据库/API  │
│  Claude App  │                  │  文件系统    │
└──────────────┘                  └──────────────┘
```

- MCP Client：AI 应用端（比如 Kiro、Cursor、Claude Desktop、VS Code）
- MCP Server：工具提供端（比如数据库查询服务、文件操作服务）
- 通信协议：基于 JSON-RPC 2.0，支持 stdio（本地进程）和 Streamable HTTP（远程服务，已取代早期的 SSE 传输方式）

### MCP Server 提供什么？

一个 MCP Server 可以暴露三种能力：

**1. Tools（工具）**：可执行的操作

```json
{
  "name": "query_database",
  "description": "执行 SQL 查询",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": { "type": "string", "description": "SQL 语句" }
    },
    "required": ["sql"]
  }
}
```

**2. Resources（资源）**：可读取的数据源

```json
{
  "uri": "file:///project/src/main.ts",
  "name": "主入口文件",
  "mimeType": "text/typescript"
}
```

**3. Prompts（提示词模板）**：预定义的交互模板

```json
{
  "name": "code_review",
  "description": "代码审查模板",
  "arguments": [
    { "name": "code", "description": "要审查的代码", "required": true }
  ]
}
```

### 实际配置

在 Kiro 中配置一个 MCP Server 非常简单，只需要一个 JSON 文件：

```json
{
  "mcpServers": {
    "aws-docs": {
      "command": "uvx",
      "args": ["awslabs.aws-documentation-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

配置好之后，AI 助手就能直接搜索 AWS 文档了。不需要写任何代码，不需要处理 API 认证，MCP 协议帮你搞定了一切。

### MCP 的意义

MCP 的真正价值不在于技术本身，而在于它创造了一个生态：

- 工具开发者只需要实现一次 MCP Server，所有 AI 应用都能用
- AI 应用开发者只需要实现一次 MCP Client，所有工具都能接入
- 用户只需要配置一下，就能给 AI 助手"装插件"

这和 Web 的发展路径很像：HTTP 协议统一了浏览器和服务器的通信方式，才有了今天的互联网生态。MCP 正在做同样的事情，统一 AI 和工具的通信方式。

## 第六层：Skill — 可复用的能力包

Skill（技能）是 Agent 生态中一个越来越重要的概念。如果说 Tool 是一个具体的操作（查数据库、读文件），那 Skill 就是一组操作 + 知识 + 流程的打包。

### Skill vs Tool

```
Tool（工具）：一个具体的动作
  → search_database("SELECT * FROM users")
  → read_file("/src/main.ts")

Skill（技能）：一套完整的能力
  → "代码审查"技能 = 读代码 + 分析架构 + 检查规范 + 输出报告
  → "UI 设计"技能 = 理解需求 + 设计规范 + 组件选择 + 响应式适配
```

Skill 通常包含：
1. 知识文档：这个技能需要的背景知识（比如代码规范、设计原则）
2. 工作流程：执行步骤的定义（先做什么、后做什么）
3. 工具集合：完成任务需要用到的工具
4. 提示词模板：针对特定任务优化的 Prompt

### 在 Kiro 中的 Skill

以 Kiro 为例，一个 Skill 的结构是这样的：

```
skills/
  ui-ux-pro-max/
    SKILL.md          ← 技能说明文档
    data/             ← 知识数据（设计规范、参考案例等）
    scripts/          ← 自动化脚本
```

`SKILL.md` 定义了这个技能的能力边界和工作方式。当你激活这个 Skill 时，AI 助手就"学会"了这个技能，能够按照预定义的流程和规范来工作。

这个设计的精妙之处在于：Skill 是可分享的。一个团队的资深工程师可以把自己的经验封装成 Skill，新人激活后就能获得同样水平的 AI 辅助。

### Skill 的工程价值

在实际开发中，Skill 解决了一个核心问题：AI 助手的输出质量不稳定。

同样是"帮我写一个列表页"，不同的 Prompt 可能产出完全不同质量的代码。但如果你有一个"前端开发"Skill，里面包含了：
- 团队的代码规范
- 组件库的使用方式
- 项目的架构约定
- 常见模式的最佳实践

那 AI 的输出就会稳定在一个较高的水平。这就是 Skill 的价值——把个人经验变成可复用的团队能力。

## 第七层：Agent — 把一切串起来

终于到了最顶层：Agent（智能体）。

Agent 是目前 AI 领域最热的概念，也是最容易被误解的概念。很多人以为 Agent 就是"更聪明的聊天机器人"，但实际上 Agent 是一个完整的系统架构。

### Agent 的四要素

一个完整的 Agent 包含四个核心组件：

```
Agent = LLM（大脑）+ Memory（记忆）+ Tools（工具）+ Planning（规划）
```

**LLM（大脑）**：负责理解、推理、决策。这是 Agent 的核心引擎。

**Memory（记忆）**：
- 短期记忆：当前对话的上下文（消息历史）
- 长期记忆：跨对话的持久化信息（用户偏好、历史决策）

**Tools（工具）**：Agent 能调用的外部能力。通过 Function Calling 或 MCP 接入。

**Planning（规划）**：面对复杂任务时，Agent 能把大任务拆解成小步骤，然后逐步执行。

### Agent 的工作循环

Agent 不是一次性回答问题，而是一个循环：

```
感知（Perceive）→ 思考（Think）→ 行动（Act）→ 观察（Observe）→ 再思考...

具体流程：
1. 接收用户指令："帮我分析这个项目的性能瓶颈"
2. 规划步骤：
   - 先读取项目结构
   - 找到关键的性能相关代码
   - 分析数据库查询
   - 检查缓存使用情况
   - 生成分析报告
3. 执行第一步：调用 read_directory 工具
4. 观察结果：发现项目用了 Webman + MySQL + Redis
5. 调整计划：重点检查 MySQL 慢查询和 Redis 缓存命中率
6. 继续执行...
7. 最终输出分析报告
```

这个"思考-行动-观察"的循环叫做 ReAct（Reasoning + Acting）模式，是目前最主流的 Agent 架构。

### 单 Agent vs 多 Agent：Swarm 与 Handoff

简单任务用单个 Agent 就够了。但复杂任务可能需要多个 Agent 协作。这就是 Multi-Agent 系统。

OpenAI 在 2024 年推出了实验性的 Swarm 框架，2025 年 3 月进化为正式的 Agents SDK。Swarm 的核心理念非常优雅——只有三个概念：

1. Agent：一个有特定职责的智能体（System Prompt + Tools）
2. Handoff（交接）：一个 Agent 发现任务超出自己能力范围时，把对话"交接"给另一个专业 Agent
3. Routine（流程）：预定义的工作步骤，引导 Agent 按流程执行

```
用户："帮我开发一个用户管理模块"

协调者 Agent
  ├── 判断任务类型 → 交接给架构师 Agent
  │
架构师 Agent
  ├── 设计数据库表结构和 API 接口
  ├── 完成后 Handoff → 后端 Agent
  │
后端 Agent
  ├── 实现 Controller、Module、Dep
  ├── 完成后 Handoff → 前端 Agent
  │
前端 Agent
  ├── 实现 Vue 页面和 API 调用
  ├── 完成后 Handoff → 代码审查 Agent
  │
代码审查 Agent
  └── 审查所有代码质量 → 输出最终结果
```

Swarm 的精妙之处在于：每个 Agent 只需要关心自己擅长的事，不需要了解整个系统。就像一个接力赛，每个选手跑自己最擅长的那一棒，通过 Handoff 把接力棒传给下一个人。

这种模式比让一个"全能 Agent"处理所有事情要可靠得多。因为：
- 每个 Agent 的 System Prompt 更聚焦，输出质量更高
- 单个 Agent 的上下文更短，不容易"迷失"
- 出了问题容易定位是哪个 Agent 的责任
- 可以给不同 Agent 分配不同的模型（简单任务用便宜模型，关键任务用强模型）

### 我的 Agent 实践

在我的项目中，Agent 系统是这样设计的：

```sql
ai_agents 表
├── name: 智能体名称
├── system_prompt: 系统提示词（定义人设和能力）
├── model_id: 关联的模型（GPT-4 / DeepSeek / Qwen）
├── scene: 使用场景（chat / goods_script）
├── temperature: 温度参数
└── max_tokens: 最大输出长度
```

不同场景使用不同的 Agent：
- `chat` 场景：通用对话，temperature 0.7，用 Claude Opus 4.6 或 GPT-5.3
- `goods_script` 场景：口播词生成，temperature 0.5，用 DeepSeek V4（性价比极高，代码和中文能力都很强）

Agent 的配置完全在后台管理，运营人员可以随时调整 Prompt 和参数，不需要改代码。这就是 Agent 工程化的价值——把 AI 能力变成可配置、可管理、可监控的系统。

## 第八层：Steering & Hooks — AI 辅助开发的工程化

除了上面这些"AI 本身"的概念，还有一些是"AI 辅助开发"领域的重要概念。

### Steering（引导文件）

Steering 是一种给 AI 编码助手提供项目上下文的机制。你可以把团队的编码规范、架构约定、技术栈信息写成 Steering 文件，AI 助手在工作时会自动参考这些信息。

```markdown
# 项目开发规范

## 架构
- 后端采用 CMVD 分层：Controller → Module → Validate → Dep
- Controller 只做路由转发，不写业务逻辑
- Module 返回 [$data, $code, $msg] 三元组

## 技术栈
- 后端：Webman + PHP 8.1
- 前端：Vue3 + TypeScript + Element Plus
- 数据库：MySQL 8.0 + Redis 7.0

## 代码规范
- 软删除使用 is_del 字段（YES=1, NO=2）
- 所有字典数据通过 DictService 链式方法初始化
- 外部 API 调用必须走 Redis 异步队列
```

有了 Steering，AI 助手生成的代码就会自动遵循你的项目规范。不需要每次都在 Prompt 里重复说明。

### Hooks（钩子）

Hooks 是 AI 辅助开发中的自动化机制。你可以定义"当某个事件发生时，自动执行某个操作"。

```json
{
  "name": "Lint on Save",
  "version": "1.0.0",
  "when": {
    "type": "fileEdited",
    "patterns": ["*.ts", "*.tsx"]
  },
  "then": {
    "type": "runCommand",
    "command": "npm run lint"
  }
}
```

这个 Hook 的意思是：当 TypeScript 文件被编辑保存时，自动运行 lint 检查。

更高级的用法：

```json
{
  "name": "Review Write Operations",
  "version": "1.0.0",
  "when": {
    "type": "preToolUse",
    "toolTypes": ["write"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "在写入文件之前，请检查代码是否符合项目规范"
  }
}
```

这个 Hook 会在 AI 助手每次写入文件之前，自动触发一次代码规范检查。相当于给 AI 加了一个"代码审查员"。

Steering + Hooks 的组合，让 AI 辅助开发从"随机输出"变成了"规范化、可控的工程实践"。

## 概念关系总结

最后，用一张图把所有概念的关系串起来：

```
用户需求
  ↓
Agent（智能体）
  ├── 大脑：LLM（大语言模型）
  │     ├── 交互方式：Prompt Engineering
  │     ├── 推理增强：Chain of Thought
  │     └── 参数控制：Temperature / Max Tokens
  ├── 记忆：Memory
  │     ├── 短期：对话上下文
  │     └── 长期：向量数据库（RAG）
  ├── 工具：Tools
  │     ├── 调用方式：Function Calling
  │     ├── 接入协议：MCP（已成为行业标准）
  │     └── 能力打包：Skill
  └── 规划：Planning
        ├── 任务拆解
        ├── ReAct 循环
        └── 多 Agent 协作（Swarm / Handoff）
```

## 我的理解

写到这里，我想分享一个自己的认知转变。

刚接触 AI 的时候，我觉得"会用 AI"就是会写 Prompt、会调 API。后来发现，这只是最表层的东西。

真正的 AI 工程能力是：

1. 理解 LLM 的能力边界——知道它能做什么、不能做什么
2. 设计合理的系统架构——Agent、Tool、Memory 怎么组合
3. 搭建可靠的基础设施——反向代理、号池、监控、异步队列
4. 建立工程化的工作流——Steering、Hooks、Skill 让 AI 输出可控

AI 不是魔法，它是一种新的计算范式。就像数据库、消息队列、缓存一样，它是你工具箱里的一个工具。关键不在于工具本身有多强，而在于你怎么把它集成到你的系统中，让它真正产生价值。

在我看来，未来的开发者不会被 AI 替代，但不会用 AI 的开发者会被会用 AI 的开发者替代。这不是危言耸听，而是正在发生的事实。

掌握这些概念不是为了面试时能侃侃而谈，而是为了在实际工作中，能够做出正确的技术决策。当老板说"我们要接入 AI"的时候，你能清楚地知道：用什么模型、怎么接入、成本多少、风险在哪。

这才是一个 AI 时代的工程师应该具备的能力。

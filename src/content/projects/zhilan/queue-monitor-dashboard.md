---
title: Redis 队列监控仪表盘
published: 2026-01-20T10:00:00Z
description: 基于 webman/redis-queue 实现队列监控，支持实时查看、失败重试、队列清空
tags: [后端, Redis, 运维]
project: 智澜管理系统
order: 70
draft: false
---

# 需求背景

系统用了很多异步队列（操作日志、邮件发送、AI 标题生成、导出任务等），需要一个监控面板：

- 实时查看各队列的等待/延迟/失败数量
- 查看失败任务详情和错误信息
- 支持失败任务重试
- 支持清空队列

## webman/redis-queue 的 Key 结构

先搞清楚 redis-queue 的数据存储格式：

```
{redis-queue}-waiting + 队列名    # List，等待中的任务
{redis-queue}-delayed             # ZSet，所有队列共用，按时间戳排序
{redis-queue}-failed              # List，所有队列共用，通过 queue 字段区分
```

关键点：`delayed` 和 `failed` 是所有队列共用的，需要遍历解析 `queue` 字段来统计。

## 后端实现

### 队列配置（改为系统设置 JSON）

- **系统设置 key**：`devtools_queue_monitor_queues`
- **类型**：JSON（系统设置类型 4）
- **示例值**：

```json
[
  {"group": "fast", "name": "operation_log", "label": "操作日志"},
  {"group": "fast", "name": "user_login_log", "label": "登录日志"},
  {"group": "slow", "name": "email_send", "label": "邮件发送"},
  {"group": "slow", "name": "export_task", "label": "导出任务"},
  {"group": "slow", "name": "generate_conversation_title", "label": "AI标题生成"}
]
```

实现要点：
1) 运行时优先读取系统设置 JSON；解析失败或未配置时，自动回退到内置默认列表，避免页面空白。  
2) 校验：`name` 必填且去重；`group` 仅支持 `fast/slow`（非法值降级为 `slow`）；`label` 为空时用 `name`。  
3) 这样新增/改名/隐藏队列不需要发版，运维直接改系统设置即可生效。

### 获取队列状态（Pipeline 优化）

```php
public function list($request): array
{
    // 批量获取 waiting 队列长度（Pipeline 减少 RTT）
    $pipe = Redis::pipeline();
    foreach ($this->queues as $queue) {
        $pipe->lLen(self::WAITING_PREFIX . $queue['name']);
    }
    $waitingResults = $pipe->exec();

    // 统计失败数和延迟数（需要遍历解析）
    $failedCounts = $this->countFailedByQueue();
    $delayedCounts = $this->countDelayedByQueue();

    $list = [];
    foreach ($this->queues as $i => $queue) {
        $list[] = [
            'name' => $queue['name'],
            'label' => $queue['label'],
            'group' => $queue['group'],
            'waiting' => (int)($waitingResults[$i] ?? 0),
            'delayed' => $delayedCounts[$queue['name']] ?? 0,
            'failed' => $failedCounts[$queue['name']] ?? 0,
        ];
    }

    return self::success($list);
}
```

### 统计失败任务

```php
private function countFailedByQueue(): array
{
    $counts = [];
    $items = Redis::lRange(self::FAILED_KEY, 0, -1);
    foreach ($items as $item) {
        $data = json_decode($item, true);
        $queue = $data['queue'] ?? 'unknown';
        $counts[$queue] = ($counts[$queue] ?? 0) + 1;
    }
    return $counts;
}
```

### 失败任务重试

```php
public function retry($request): array
{
    $queueName = $param['queue'];
    $index = $param['index'];
    
    // 获取指定位置的任务
    $item = Redis::lIndex(self::FAILED_KEY, (int)$index);
    $data = json_decode($item, true);
    
    // 重置重试次数，重新入队
    $data['attempts'] = 0;
    unset($data['error']);
    
    $waitingKey = self::WAITING_PREFIX . $queueName;
    
    Redis::multi();
    Redis::lRem(self::FAILED_KEY, 1, $item);
    Redis::rPush($waitingKey, json_encode($data, JSON_UNESCAPED_UNICODE));
    Redis::exec();
    
    return self::success([], '已重新入队');
}
```

## 前端实现

### 队列列表

```vue
<el-table :data="queueList" v-loading="loading">
  <el-table-column prop="label" label="队列名称" />
  <el-table-column prop="group" label="分组">
    <template #default="{row}">
      <el-tag :type="row.group === 'fast' ? 'success' : 'warning'" size="small">
        {{ row.group }}
      </el-tag>
    </template>
  </el-table-column>
  <el-table-column prop="waiting" label="等待中" />
  <el-table-column prop="delayed" label="延迟中" />
  <el-table-column prop="failed" label="失败">
    <template #default="{row}">
      <span :class="{'text-danger': row.failed > 0}">{{ row.failed }}</span>
    </template>
  </el-table-column>
  <el-table-column label="操作">
    <template #default="{row}">
      <el-button text @click="viewFailed(row)" :disabled="row.failed === 0">
        查看失败
      </el-button>
      <el-button text type="danger" @click="clearWaiting(row)" :disabled="row.waiting === 0">
        清空等待
      </el-button>
    </template>
  </el-table-column>
</el-table>
```

### 自动刷新

```typescript
const autoRefresh = ref(false)
let timer: number | null = null

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    timer = setInterval(() => getList(), 3000)
  } else {
    timer && clearInterval(timer)
  }
}

onUnmounted(() => timer && clearInterval(timer))
```

## 数据结构说明

失败任务的数据结构：

```json
{
  "queue": "export_task",
  "data": {
    "task_id": 123,
    "user_id": 1,
    "headers": {...},
    "data": [...]
  },
  "max_attempts": 3,
  "attempts": 3,
  "error": "Connection timeout"
}
```

延迟任务存在 ZSet 中，score 是执行时间戳。

## 效果展示

| 队列名称 | 分组 | 等待中 | 延迟中 | 失败 | 操作 |
|---------|------|-------|-------|------|------|
| 操作日志 | fast | 0 | 0 | 0 | - |
| 导出任务 | slow | 2 | 1 | 3 | 查看失败 / 清空 |

## 注意事项

1. **性能**：`delayed` 和 `failed` 是共用的，任务量大时遍历会慢，可以考虑定时统计缓存
2. **安全**：清空和重试操作要加权限控制
3. **队列命名**：统一使用下划线分隔，保持规范

队列监控是运维的眼睛，出问题能第一时间发现和处理。

---
title: 异步导出 + WebSocket 实时通知
published: 2026-01-20T11:00:00Z
description: 完整的异步导出方案：队列处理 + COS 存储 + WebSocket 推送 + 导出管理页面
tags: [后端, WebSocket, 异步]
category: 后端技术
draft: false
---

# 需求背景

导出 Excel 是常见功能，但数据量大时会很慢：

- 同步导出：用户干等，接口超时
- 异步导出：立即返回，完成后怎么通知用户？

方案：**异步队列 + WebSocket 实时推送 + 导出管理页面**

## 整体架构

```
用户点击导出
    │
    ▼
┌─────────────────────────────┐
│  Module: 创建任务记录 + 入队  │
└─────────────────────────────┘
    │
    ▼ Redis Queue
┌─────────────────────────────┐
│  Consumer: 生成 Excel        │
│  → 上传 COS                  │
│  → 更新任务状态              │
│  → WebSocket 推送通知        │
└─────────────────────────────┘
    │
    ▼
┌─────────────────────────────┐
│  前端: 收到推送，弹窗提示下载  │
└─────────────────────────────┘
```

## 数据库设计

```sql
CREATE TABLE export_task (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    file_name VARCHAR(200),
    file_url VARCHAR(500),
    file_size INT,
    row_count INT,
    status TINYINT DEFAULT 1,  -- 1处理中 2成功 3失败
    error_msg VARCHAR(500),
    expire_at DATETIME,        -- 7天后过期
    is_del TINYINT DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME
);
```

## 后端实现

### 提交导出任务

```php
// ExportTaskDep.php
public function submit(int $userId, string $title, array $headers, array $data, string $prefix = 'export'): int
{
    // 1. 创建任务记录
    $taskId = $this->add([
        'user_id' => $userId,
        'title' => $title,
        'status' => ExportTaskEnum::STATUS_PENDING,
        'expire_at' => date('Y-m-d H:i:s', strtotime('+7 days')),
    ]);

    // 2. 入队
    RedisQueue::send('export_task', [
        'task_id' => $taskId,
        'user_id' => $userId,
        'headers' => $headers,
        'data' => $data,
        'title' => $title,
        'prefix' => $prefix,
    ]);

    return $taskId;
}
```

### 业务层调用

```php
// UsersListModule.php
public function export($request)
{
    $users = $this->usersDep->getMap($param['ids'])->values();
    
    $headers = [
        'id' => '用户ID',
        'username' => '用户名',
        'email' => '邮箱',
    ];
    
    $data = $users->map(fn($item) => [
        'id' => $item->id,
        'username' => $item->username,
        'email' => $item->email,
    ])->toArray();

    $this->exportTaskDep->submit($request->userId, '用户列表导出', $headers, $data, 'users_export');

    return self::success(['message' => '导出任务已提交，完成后将通知您']);
}
```

### 队列消费者

Webman 自动 ack，不需要手动 try-catch：

```php
use app\service\System\NotificationService;

class ExportTask implements Consumer
{
    public $queue = 'export_task';

    public function consume($data)
    {
        $taskId = $data['task_id'];
        $userId = $data['user_id'];
        $title = $data['title'] ?? '数据导出';

        $result = (new ExportService())->export($data['headers'], $data['data'], $data['prefix'] ?? 'export');
        (new ExportTaskDep())->updateSuccess($taskId, $result);
        
        // 通过通知服务发送（写库 + WebSocket 推送）
        NotificationService::sendUrgent($userId, $title . ' - 导出完成', '点击查看并下载导出文件', [
            'type' => NotificationService::TYPE_SUCCESS,
            'link' => '/devTools/exportTask'
        ]);
    }

    public function onConsumeFailure(\Throwable $e, $package)
    {
        $data = $package['data'] ?? [];
        if ($data['task_id'] ?? null) {
            (new ExportTaskDep())->updateFailed($data['task_id'], $e->getMessage());
        }
        if ($data['user_id'] ?? null) {
            NotificationService::sendUrgent($data['user_id'], ($data['title'] ?? '导出') . ' - 失败', '导出失败，已重试多次仍无法完成', [
                'type' => NotificationService::TYPE_ERROR,
                'link' => '/devTools/exportTask'
            ]);
        }
    }
}
```

> 注意：Webman 队列自动 ack，不需要手动 try-catch。异常会触发 `onConsumeFailure`。

## 前端实现

### WebSocket 监听

现在通知监听在 `NotificationCenter` 组件内完成：

```typescript
// NotificationCenter.vue
import { onWsMessage } from '@/hooks/useWebSocket'
import { shouldUseNative } from '@/store/tauri'

let unsubscribe: (() => void) | null = null

onMounted(() => {
  unsubscribe = onWsMessage('notification', async ({ data }) => {
    unreadCount.value++
    prepend(data)  // 列表头部插入新通知
    
    if (data.level === 'urgent') {
      // Tauri 系统通知（窗口不可见时）
      if (await shouldUseNative()) {
        const { invoke } = await import('@tauri-apps/api/core')
        invoke('send_notification', { title: data.title, body: data.content })
      }
      // Web Toast 通知
      ElNotification({
        title: data.title,
        message: data.content,
        type: data.notification_type || 'info',
        duration: 5000,
        onClick: () => router.push(data.link)
      })
    }
  })
})

onUnmounted(() => unsubscribe?.())
```

**双端通知策略**：
- Web 端：始终用 `ElNotification`
- Tauri 端：窗口可见用 `ElNotification`，不可见用系统通知

> 详见《[通知管理系统设计与实现](/projects/zhilan/notification-system/)》

### 导出管理页面

使用 el-tabs 按状态筛选 + Search 组件搜索：

```vue
<Search v-model="searchForm" :fields="searchFields" @query="handleSearch" @reset="handleSearch" />

<el-tabs v-model="searchForm.status" @tab-change="handleChangeStatus">
  <el-tab-pane v-for="item in statusArr" :key="item.value" :name="item.value">
    <template #label>{{ item.label }} ({{ item.num }})</template>
  </el-tab-pane>
</el-tabs>

<AppTable :columns="columns" :data="listData">
  <template #cell-actions="{row}">
    <el-button text @click="handleDownload(row)" :disabled="row.status !== 2">
      下载
    </el-button>
    <el-button text type="danger" @click="confirmDel(row)">删除</el-button>
  </template>
</AppTable>
```

搜索配置：

```typescript
const searchFields = computed<SearchField[]>(() => [
  {key: 'title', type: 'input', label: '任务名称', placeholder: '任务名称', width: 180},
  {key: 'file_name', type: 'input', label: '文件名', placeholder: '文件名', width: 180}
])

const handleSearch = () => {
  getList()
  refreshStatusCount()  // 搜索条件同步给状态统计
}
```

### 状态统计接口（支持搜索条件）

```php
public function statusCount($request): array
{
    $param = $request->all();
    $param['user_id'] = $request->userId;
    $counts = $this->exportTaskDep->countByStatus($param);
    $list = [];
    foreach (ExportTaskEnum::$statusArr as $val => $label) {
        $list[] = ['label' => $label, 'value' => $val, 'num' => $counts[$val] ?? 0];
    }
    return self::success($list);
}
```

### 模糊搜索（左对齐保证索引）

```php
// ExportTaskDep.php
public function list(array $param)
{
    return $this->model
        ->where('user_id', $param['user_id'])
        ->where('is_del', CommonEnum::NO)
        ->when(isset($param['status']) && $param['status'] !== '', fn($q) => $q->where('status', (int)$param['status']))
        // 左对齐 LIKE 'xxx%' 可以用上索引
        ->when(!empty($param['title']), fn($q) => $q->where('title', 'like', $param['title'] . '%'))
        ->when(!empty($param['file_name']), fn($q) => $q->where('file_name', 'like', $param['file_name'] . '%'))
        ->orderBy('id', 'desc')
        ->paginate($param['page_size'], ['*'], 'page', $param['current_page']);
}

public function countByStatus(array $param): array
{
    return $this->query()
        ->where('user_id', $param['user_id'])
        ->where('is_del', CommonEnum::NO)
        // 搜索条件同步给状态统计，保证数量和列表一致
        ->when(!empty($param['title']), fn($q) => $q->where('title', 'like', $param['title'] . '%'))
        ->when(!empty($param['file_name']), fn($q) => $q->where('file_name', 'like', $param['file_name'] . '%'))
        ->selectRaw('status, COUNT(*) as num')
        ->groupBy('status')
        ->pluck('num', 'status')
        ->toArray();
}
```

> 注意：模糊搜索只做左对齐 `LIKE 'xxx%'`，不用 `%xxx%`，这样能用上索引。

## 用户体验流程

```
1. 用户点击「导出」按钮
2. 接口立即返回「导出任务已提交」
3. 后台队列处理，生成 Excel，上传 COS
4. 完成后 WebSocket 推送通知
5. 前端弹窗「导出完成，点击下载」
6. 用户也可以去「导出管理」页面查看历史记录
```

## 定时清理过期文件

```php
// CleanExportTask.php (定时进程)
public function onWorkerStart()
{
    Timer::add(3600, function () {
        $dep = new ExportTaskDep();
        $count = $dep->cleanExpired();
        if ($count > 0) {
            Log::info("[CleanExportTask] 清理过期任务: {$count} 条");
        }
    });
}
```

## 效果对比

| 方案 | 响应时间 | 用户体验 | 可追溯 |
|------|---------|---------|-------|
| 同步导出 | 10-30s | 卡顿 | 无 |
| 异步+轮询 | 立即 | 一般 | 有 |
| 异步+WebSocket | 立即 | 流畅 | 有 |

## 总结

完整方案包含：

1. **任务记录**：数据库存储，可追溯
2. **异步处理**：队列消费，不阻塞接口
3. **实时通知**：WebSocket 推送，体验好
4. **管理页面**：查看历史，重新下载
5. **搜索筛选**：任务名称/文件名模糊搜索，左对齐保证索引
6. **定时清理**：7天过期，节省存储

异步 + 实时通知是大文件导出的标准解法。

---
title: 通知任务管理：批量发布与定时调度
published: 2026-01-25T19:00:00Z
description: 实现管理员批量发布通知的完整方案：任务表设计、定时调度、队列消费、前端管理
tags: [后端, 队列, 定时任务, 架构]
category: 智澜管理系统
draft: false
---

# 需求背景

之前实现了通知系统（`NotificationService`），支持代码层面发送通知。现在需要让**管理员**也能在后台发布通知：

- 支持发送给：全体用户 / 指定用户 / 指定角色
- 支持立即发送 / 定时发送
- 任务状态追踪：待发送 → 发送中 → 已完成/失败
- 发送进度可视化

## 整体架构

```
管理员发布通知
    │
    ▼
┌─────────────────────────────────────┐
│  NotificationTaskModule              │
│  - 创建任务记录                       │
│  - 立即发送：直接入队                 │
│  - 定时发送：等待调度器               │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  NotificationTaskScheduler (定时)    │
│  - 每分钟扫描待发送的定时任务         │
│  - 更新状态为「发送中」               │
│  - 将任务入队                        │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  NotificationTask (队列消费者)        │
│  - 获取目标用户列表                   │
│  - 分批调用 NotificationService       │
│  - 更新发送进度                       │
└─────────────────────────────────────┘
```

---

# 数据库设计

## notification_tasks 表

```sql
CREATE TABLE notification_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL COMMENT '通知标题',
    content TEXT COMMENT '通知内容',
    type TINYINT DEFAULT 1 COMMENT '类型：1info 2success 3warning 4error',
    level TINYINT DEFAULT 1 COMMENT '级别：1普通 2紧急',
    link VARCHAR(500) DEFAULT '' COMMENT '跳转链接',
    target_type TINYINT NOT NULL COMMENT '目标：1全体 2指定用户 3指定角色',
    target_ids JSON COMMENT '目标ID数组',
    status TINYINT DEFAULT 1 COMMENT '状态：1待发送 2发送中 3已完成 4失败',
    total_count INT DEFAULT 0 COMMENT '目标用户数',
    sent_count INT DEFAULT 0 COMMENT '已发送数',
    send_at DATETIME COMMENT '定时发送时间（空=立即）',
    error_msg VARCHAR(500) COMMENT '错误信息',
    created_by INT NOT NULL COMMENT '创建人',
    is_del TINYINT DEFAULT 2,
    created_at DATETIME,
    updated_at DATETIME,
    INDEX idx_status_send_at (status, send_at)
);
```

**设计要点**：
- `target_type + target_ids`：灵活的目标定义
- `total_count / sent_count`：实时进度追踪
- `send_at`：空表示立即发送，有值表示定时
- `error_msg`：失败时记录原因

---

# 后端实现

## 1. 创建任务（NotificationTaskModule）

```php
public function add($request): array
{
    $param = $this->validate($request, NotificationTaskValidate::add());

    // 计算目标用户数
    $totalCount = $this->calculateTotalCount($param['target_type'], $param['target_ids'] ?? []);

    $taskId = $this->notificationTaskDep->submit([
        'title' => $param['title'],
        'content' => $param['content'] ?? '',
        'type' => $param['type'] ?? NotificationEnum::TYPE_INFO,
        'level' => $param['level'] ?? NotificationEnum::LEVEL_NORMAL,
        'link' => $param['link'] ?? '',
        'target_type' => $param['target_type'],
        'target_ids' => json_encode($param['target_ids'] ?? []),
        'status' => NotificationEnum::STATUS_PENDING,
        'total_count' => $totalCount,
        'send_at' => $param['send_at'] ?: null,  // 注意用 ?: 不是 ??
        'created_by' => $request->userId,
    ]);

    return self::success(['id' => $taskId]);
}

private function calculateTotalCount(int $targetType, array $targetIds): int
{
    return match ($targetType) {
        NotificationEnum::TARGET_ALL => $this->usersDep->countAll(),
        NotificationEnum::TARGET_USERS => count($targetIds),
        NotificationEnum::TARGET_ROLES => $this->usersDep->getIdsByRoleIds($targetIds)->count(),
        default => 0,
    };
}
```

## 2. 任务入队（NotificationTaskDep）

```php
public function submit(array $data, bool $immediate = true): int
{
    $taskId = $this->add($data);

    // 无 send_at = 立即发送，直接入队
    if ($immediate && empty($data['send_at'])) {
        RedisQueue::send('notification_task', ['task_id' => $taskId]);
    }

    return $taskId;
}
```

## 3. 定时调度器（NotificationTaskScheduler）

```php
class NotificationTaskScheduler extends BaseCronTask
{
    protected function getTaskName(): string
    {
        return 'notification_task_scheduler';
    }

    protected function handle(): ?string
    {
        $notificationTaskDep = new NotificationTaskDep();
        $tasks = $notificationTaskDep->getPendingTasks();

        if (empty($tasks)) {
            return '无待发送任务';
        }

        $count = 0;
        foreach ($tasks as $task) {
            // 先更新状态为「发送中」，防止重复入队
            $notificationTaskDep->updateStatus($task['id'], NotificationEnum::STATUS_SENDING);
            RedisQueue::send('notification_task', ['task_id' => $task['id']]);
            $count++;
        }

        return "已将 {$count} 个任务加入队列";
    }
}
```

**关键点**：入队前先更新状态！否则下次调度会重复入队。

查询待发送任务：

```php
public function getPendingTasks(): array
{
    return $this->query()
        ->where('status', NotificationEnum::STATUS_PENDING)
        ->where('is_del', CommonEnum::NO)
        ->whereNotNull('send_at')
        ->where('send_at', '<=', date('Y-m-d H:i:s'))
        ->get()
        ->toArray();
}
```

## 4. 队列消费者（NotificationTask）

```php
class NotificationTask implements Consumer
{
    public $queue = 'notification_task';
    private const BATCH_SIZE = 100;

    public function consume($data)
    {
        $taskId = $data['task_id'];
        $notificationTaskDep = new NotificationTaskDep();

        $task = $notificationTaskDep->get($taskId);
        if (!$task) {
            $this->log('任务不存在', ['task_id' => $taskId]);
            return;
        }

        // 更新状态为发送中
        $notificationTaskDep->updateStatus($taskId, NotificationEnum::STATUS_SENDING);

        // 获取目标用户
        $userIds = $this->getTargetUserIds($task);
        $notificationTaskDep->updateStatus($taskId, NotificationEnum::STATUS_SENDING, count($userIds));

        // 分批发送
        $sentCount = 0;
        foreach (array_chunk($userIds, self::BATCH_SIZE) as $chunk) {
            foreach ($chunk as $userId) {
                NotificationService::send($userId, $task->title, $task->content ?? '', [
                    'type' => NotificationEnum::getTypeStr($task->type),
                    'level' => NotificationEnum::getLevelStr($task->level),
                    'link' => $task->link ?? '',
                ]);
                $sentCount++;
            }
            // 更新进度
            $notificationTaskDep->update($taskId, ['sent_count' => $sentCount]);
        }

        // 完成
        $notificationTaskDep->updateStatus($taskId, NotificationEnum::STATUS_SUCCESS);
    }

    public function onConsumeFailure(\Throwable $e, $package)
    {
        $taskId = $package['data']['task_id'] ?? null;
        if ($taskId) {
            (new NotificationTaskDep())->updateStatus(
                $taskId,
                NotificationEnum::STATUS_FAILED,
                null,
                '重试次数耗尽: ' . $e->getMessage()
            );
        }
    }

    private function getTargetUserIds($task): array
    {
        $usersDep = new UsersDep();
        return match ((int)$task->target_type) {
            NotificationEnum::TARGET_ALL => $usersDep->all()->pluck('id')->toArray(),
            NotificationEnum::TARGET_USERS => json_decode($task->target_ids, true) ?? [],
            NotificationEnum::TARGET_ROLES => $usersDep->getIdsByRoleIds(json_decode($task->target_ids, true) ?? [])->toArray(),
            default => [],
        };
    }
}
```

---

# 前端实现

## 任务列表页

```vue
<template>
  <div class="box">
    <!-- Tab 状态统计 -->
    <el-tabs v-model="searchForm.status" @tab-change="handleChangeStatus">
      <el-tab-pane v-for="item in statusArr" :key="item.value" :name="item.value">
        <template #label>{{ item.label }} ({{ item.num }})</template>
      </el-tab-pane>
    </el-tabs>

    <AppTable :columns="columns" :data="listData" :loading="listLoading">
      <!-- 进度列 -->
      <template #cell-progress="{row}">
        <span>{{ row.sent_count }} / {{ row.total_count }}</span>
      </template>
      
      <!-- 状态列 -->
      <template #cell-status="{row}">
        <el-tag :type="getStatusType(row.status)" size="small">{{ row.status_text }}</el-tag>
      </template>
      
      <!-- 错误信息列（独立展示 + 复制按钮） -->
      <template #cell-error_msg="{row}">
        <div v-if="row.error_msg" class="cell-error">
          <span class="error-text">{{ row.error_msg }}</span>
          <el-button :icon="DocumentCopy" link size="small" @click="copy(row.error_msg)" />
        </div>
        <span v-else class="text-secondary">-</span>
      </template>
      
      <!-- 定时发送时间 -->
      <template #cell-send_at="{row}">
        <span v-if="row.send_at">{{ row.send_at }}</span>
        <span v-else class="text-secondary">{{ t('notificationTask.immediate') }}</span>
      </template>
    </AppTable>
  </div>
</template>
```

## 发布弹窗

```vue
<el-dialog v-model="dialogVisible">
  <el-form :model="form" ref="formRef" label-width="100px">
    <el-form-item :label="t('notificationTask.title')" prop="title" :rules="[{required: true}]">
      <el-input v-model="form.title" maxlength="100" show-word-limit />
    </el-form-item>
    
    <!-- 级别选择 -->
    <el-form-item :label="t('notificationTask.level')">
      <el-radio-group v-model="form.level">
        <el-radio v-for="item in levelArr" :key="item.value" :value="item.value">{{ item.label }}</el-radio>
      </el-radio-group>
    </el-form-item>
    <!-- 级别帮助提示 -->
    <el-form-item>
      <el-alert :title="t('notificationTask.levelHelp')" type="primary" :closable="false" show-icon />
    </el-form-item>
    
    <!-- 目标类型 -->
    <el-form-item :label="t('notificationTask.targetType')">
      <el-radio-group v-model="form.target_type" @change="form.target_ids = []">
        <el-radio v-for="item in targetTypeArr" :key="item.value" :value="item.value">{{ item.label }}</el-radio>
      </el-radio-group>
    </el-form-item>
    
    <!-- 指定用户（远程搜索 + 滚动加载） -->
    <el-form-item v-if="form.target_type === 2">
      <RemoteSelect v-model="form.target_ids" multiple :fetch-method="UsersListApi.list"
                    :label-field="(item: any) => item.username" value-field="id" width="100%" />
    </el-form-item>
    
    <!-- 定时发送 -->
    <el-form-item :label="t('notificationTask.sendAt')">
      <el-date-picker v-model="form.send_at" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" />
    </el-form-item>
  </el-form>
</el-dialog>
```

---

# 踩坑记录

## 1. 定时任务重复入队

**问题**：调度器每分钟扫描，入队后状态没变，下次又扫到同一个任务。

**修复前**：
```php
foreach ($tasks as $task) {
    RedisQueue::send('notification_task', ['task_id' => $task['id']]);
    // 状态还是 PENDING！
}
```

**修复后**：
```php
foreach ($tasks as $task) {
    $notificationTaskDep->updateStatus($task['id'], NotificationEnum::STATUS_SENDING);  // 先改状态！
    RedisQueue::send('notification_task', ['task_id' => $task['id']]);
}
```

## 2. send_at 空字符串导致 SQL 错误

**问题**：前端传空字符串 `""`，后端 `$param['send_at'] ?? null` 不生效。

**原因**：`??` 只判断 null，空字符串不是 null。

**修复**：改用 `?:` 运算符：
```php
'send_at' => $param['send_at'] ?: null
```

## 3. Workerman Crontab 用 6 位表达式

**问题**：标准 cron 是 5 位，Workerman 用 6 位（多一个秒）。

**错误**：`* * * * *`（5 位，不执行）
**正确**：`0 * * * * *`（6 位，每分钟第 0 秒执行）

## 4. 定时任务不生效的排查

依赖链：
1. `cron_task` 表有对应记录
2. `status = 1`（启用）
3. `is_del = 2`（未删除，注意项目里 NO=2）
4. `cron` 表达式正确（6 位）
5. 服务已重启（Crontab 在 Worker 启动时注册）

---

# 总结

| 层级 | 组件 | 职责 |
|------|------|------|
| Module | NotificationTaskModule | 创建任务、计算目标用户数 |
| Dep | NotificationTaskDep | 数据访问、入队、状态更新 |
| Process | NotificationTaskScheduler | 定时扫描待发送任务 |
| Queue | NotificationTask | 分批发送、进度追踪 |
| 前端 | notificationTask/index.vue | 任务列表、发布弹窗 |

**核心设计**：
- **双表分离**：任务表（一）+ 通知表（多），解耦管理和触达
- **状态先行**：入队前先改状态，防止重复入队
- **分批发送**：BATCH_SIZE=100，避免内存爆炸
- **失败记录**：`onConsumeFailure` 记录错误信息，便于排查

---
title: 定时任务管理模块
published: 2026-01-21T10:00:00Z
description: 基于 Webman Crontab 实现定时任务动态管理，支持 CRUD、软禁用、执行日志
tags: [后端, Crontab, 运维]
category: 智澜管理系统
draft: false
---

# 需求背景

系统有多个定时任务：

- `CleanExportTask`：每天凌晨 1 点清理过期导出文件
- `AiRunTimeoutTask`：每分钟检测 AI 运行超时

之前是硬编码 cron 表达式，修改周期需要改代码重新部署。现在需要：

- 在后台界面动态修改执行周期
- 支持启用/禁用任务（软禁用）
- 记录每次执行的日志（时长、状态、错误信息）

## 数据库设计

### 任务表 `cron_task`

```sql
CREATE TABLE cron_task (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(50) NOT NULL UNIQUE COMMENT '任务标识',
  title VARCHAR(100) NOT NULL COMMENT '任务名称',
  description VARCHAR(255) DEFAULT '' COMMENT '任务描述',
  cron VARCHAR(50) NOT NULL COMMENT 'Cron 表达式',
  cron_readable VARCHAR(50) DEFAULT '' COMMENT '可读描述',
  handler VARCHAR(255) NOT NULL COMMENT '处理器类名',
  status TINYINT DEFAULT 1 COMMENT '状态：1启用 0禁用',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 执行日志表 `cron_task_log`

```sql
CREATE TABLE cron_task_log (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id INT NOT NULL,
  task_name VARCHAR(50) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME,
  duration_ms INT DEFAULT 0 COMMENT '执行时长(毫秒)',
  status TINYINT DEFAULT 3 COMMENT '1成功 2失败 3运行中',
  result TEXT COMMENT '执行结果',
  error_msg TEXT COMMENT '错误信息',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_task_id (task_id),
  INDEX idx_start_time (start_time)
);
```

## 后端实现

### BaseCronTask 基类

核心设计：基类统一处理调度注册和日志记录，子类只需实现业务逻辑。

```php
abstract class BaseCronTask
{
    protected CronTaskDep $cronTaskDep;
    protected CronTaskLogDep $cronTaskLogDep;

    public function __construct()
    {
        $this->cronTaskDep = new CronTaskDep();
        $this->cronTaskLogDep = new CronTaskLogDep();
    }

    // 子类必须实现：返回任务标识
    abstract public function getTaskName(): string;

    // 子类必须实现：业务逻辑
    abstract public function handle(): void;

    // 统一的 Worker 启动入口
    public function onWorkerStart(): void
    {
        $task = $this->cronTaskDep->findByName($this->getTaskName());
        
        // 任务不存在或被禁用，不注册调度
        if (!$task || $task->status != 1 || empty($task->cron)) {
            return;
        }

        new Crontab($task->cron, fn() => $this->runWithLog());
    }

    // 带日志的执行
    protected function runWithLog(): void
    {
        $task = $this->cronTaskDep->findByName($this->getTaskName());
        if (!$task) return;

        $logId = $this->cronTaskLogDep->startLog($task->id, $task->name);
        $startTime = microtime(true);

        try {
            $this->handle();
            $durationMs = (int)((microtime(true) - $startTime) * 1000);
            $this->cronTaskLogDep->endLog($logId, 1, $durationMs, 'OK');
        } catch (\Throwable $e) {
            $durationMs = (int)((microtime(true) - $startTime) * 1000);
            $this->cronTaskLogDep->endLog($logId, 2, $durationMs, null, $e->getMessage());
        }
    }
}
```

### 子类实现

子类变得非常简洁：

```php
class CleanExportTask extends BaseCronTask
{
    public function getTaskName(): string
    {
        return 'clean_export';
    }

    public function handle(): void
    {
        // 清理 7 天前的导出文件
        $expireTime = Carbon::now()->subDays(7);
        ExportTaskModel::where('created_at', '<', $expireTime)->delete();
    }
}
```

### Cron 预设枚举

常用的 cron 表达式做成枚举，方便前端快捷选择：

```php
class CronEnum
{
    const EVERY_MINUTE = '0 * * * * *';
    const EVERY_5_MINUTES = '0 */5 * * * *';
    const EVERY_HOUR = '0 0 * * * *';
    const DAILY_0AM = '0 0 0 * * *';
    const DAILY_1AM = '0 0 1 * * *';
    const WEEKLY_MONDAY = '0 0 0 * * 1';
    const MONTHLY_1ST = '0 0 0 1 * *';

    public static array $presetArr = [
        self::EVERY_MINUTE => '每分钟',
        self::EVERY_5_MINUTES => '每5分钟',
        self::EVERY_HOUR => '每小时',
        self::DAILY_0AM => '每天0点',
        self::DAILY_1AM => '每天凌晨1点',
        self::WEEKLY_MONDAY => '每周一0点',
        self::MONTHLY_1ST => '每月1号0点',
    ];
}
```

### DictService 集成

```php
public function setCronPresetArr()
{
    $this->dict['cron_preset_arr'] = $this->enumToDict(CronEnum::$presetArr);
    return $this;
}
```

## 前端实现

### Cron 快捷选择

使用 `el-select-v2` 实现快捷选择，选中后自动填充表达式和可读描述：

```vue
<el-form-item :label="t('cronTask.form.cronPreset')">
  <el-select-v2 
    v-model="form.cron" 
    :options="cronPresets" 
    clearable 
    @change="onPresetChange" 
  />
</el-form-item>

<el-form-item :label="t('cronTask.form.cron')" prop="cron" required>
  <el-input v-model="form.cron" placeholder="0 0 1 * * *" />
</el-form-item>
```

```typescript
const onPresetChange = (val: string) => {
  if (!val) return
  const preset = cronPresets.value.find((p: any) => p.value === val)
  if (preset) {
    form.value.cron = preset.value
    form.value.cron_readable = preset.label
  }
}
```

### 执行日志弹窗

```vue
<el-dialog v-model="logVisible" title="执行日志" width="900px">
  <Search v-model="logSearchForm" :fields="logSearchFields" @query="onLogSearch" />
  <AppTable 
    :columns="logColumns" 
    :data="logData" 
    :loading="logLoading"
    :tableProps="{ height: 400 }"
    :fixedFooter="false"
  >
    <template #cell-status="{ row }">
      <el-tag :type="LOG_STATUS_TYPE[row.status]" size="small">
        {{ row.status_name }}
      </el-tag>
    </template>
  </AppTable>
</el-dialog>
```

## 软禁用实现

任务的启用/禁用是"软禁用"，通过 `status` 字段控制：

- `status = 1`：启用，Worker 启动时注册 Crontab
- `status = 0`：禁用，Worker 启动时跳过

```php
public function onWorkerStart(): void
{
    $task = $this->cronTaskDep->findByName($this->getTaskName());
    
    // 禁用状态不注册
    if (!$task || $task->status != 1) {
        return;
    }
    
    new Crontab($task->cron, fn() => $this->runWithLog());
}
```

## 注意事项

### 修改后需重启

Crontab 是在 Worker 启动时注册的，修改数据库后不会立即生效。前端需要提示：

```vue
<el-alert type="warning" :closable="false">
  修改后需重启服务才能生效
</el-alert>
```

### 任务标识唯一

`name` 字段是任务的唯一标识，用于关联代码中的处理器类。新增任务时需要校验：

```php
self::throwIf($this->cronTaskDep->nameExists($param['name']), '任务标识已存在');
```

### 日志时间筛选

日志查询支持时间范围筛选，后端使用 Carbon 处理：

```php
if (!empty($param['date'])) {
    $query->where('start_time', '>=', Carbon::parse($param['date'][0])->startOfDay())
          ->where('start_time', '<=', Carbon::parse($param['date'][1])->endOfDay());
}
```

## 效果展示

| 任务名称 | Cron 表达式 | 下次执行 | 状态 | 操作 |
|---------|------------|---------|------|------|
| AI超时检测 | 每分钟 | 2026-01-21 10:01:00 | 启用 | 编辑 / 禁用 / 日志 |
| 清理导出文件 | 每天凌晨1点 | 2026-01-22 01:00:00 | 启用 | 编辑 / 禁用 / 日志 |

## 总结

这套方案的核心思路：

1. **基类抽象**：`BaseCronTask` 统一处理调度和日志，子类专注业务
2. **配置外置**：cron 表达式存数据库，运维可视化修改
3. **软禁用**：不删代码就能暂停任务
4. **可追溯**：每次执行都有日志，出问题能快速定位

定时任务是系统的"后台劳动者"，有了这套管理机制，运维再也不用改代码重启了。

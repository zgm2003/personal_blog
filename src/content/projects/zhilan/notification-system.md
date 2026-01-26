---
title: 通知管理系统设计与实现
published: 2026-01-25T12:00:00Z
description: 完整的站内通知方案：数据库存储 + WebSocket 实时推送 + Tauri 系统通知 + 游标分页
tags: [后端, WebSocket, Tauri, 架构]
project: 智澜管理系统
order: 50
draft: false
---

# 需求背景

管理系统需要一套完整的通知机制：

- 异步任务完成后通知用户（如导出完成）
- 支持不同级别：普通（静默更新角标）、紧急（弹 Toast）
- 数据持久化，用户可查看历史
- Tauri 桌面端支持系统级通知

## 整体架构

```
业务代码（如导出任务完成）
    │
    ▼
┌─────────────────────────────────────┐
│  NotificationService                 │
│  - 写入数据库                        │
│  - WebSocket 推送                   │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  前端 NotificationCenter             │
│  - 监听 WebSocket                    │
│  - 更新角标                          │
│  - urgent 级别：弹 Toast + 系统通知  │
└─────────────────────────────────────┘
```

## 数据库设计

```sql
CREATE TABLE notification (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT,
    type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
    level ENUM('normal', 'urgent') DEFAULT 'normal',
    link VARCHAR(500),           -- 点击跳转链接
    is_read TINYINT DEFAULT 2,   -- 1已读 2未读
    is_del TINYINT DEFAULT 2,
    created_at DATETIME,
    updated_at DATETIME,
    INDEX idx_user_read (user_id, is_read, is_del)
);
```

**字段说明**：
- `type`：通知类型，对应 Toast 颜色
- `level`：`normal` 静默更新角标，`urgent` 弹 Toast
- `link`：点击通知跳转的路由或外链

---

# 后端实现

## NotificationService（核心服务）

统一的通知发送入口，一次调用完成「写库 + 推送」：

```php
<?php
namespace app\service\System;

use app\dep\System\NotificationDep;
use GatewayWorker\Lib\Gateway;

class NotificationService
{
    const TYPE_INFO = 'info';
    const TYPE_SUCCESS = 'success';
    const TYPE_WARNING = 'warning';
    const TYPE_ERROR = 'error';
    
    const LEVEL_NORMAL = 'normal';   // 静默
    const LEVEL_URGENT = 'urgent';   // 弹 Toast

    public static function send(int $userId, string $title, string $content = '', array $options = []): int
    {
        Gateway::$registerAddress = '127.0.0.1:1236';
        
        $type = $options['type'] ?? self::TYPE_INFO;
        $level = $options['level'] ?? self::LEVEL_NORMAL;
        $link = $options['link'] ?? '';

        // 1. 写入数据库
        $notificationId = (new NotificationDep())->add([
            'user_id' => $userId,
            'title' => $title,
            'content' => $content,
            'type' => $type,
            'level' => $level,
            'link' => $link,
            'is_read' => 2,
            'is_del' => 2,
        ]);

        // 2. WebSocket 推送
        try {
            Gateway::sendToUid($userId, json_encode([
                'type' => 'notification',
                'data' => [
                    'id' => $notificationId,
                    'title' => $title,
                    'content' => $content,
                    'notification_type' => $type,
                    'level' => $level,
                    'link' => $link,
                    'created_at' => date('Y-m-d H:i:s'),
                ]
            ]));
        } catch (\Throwable $e) {
            \support\Log::warning("[NotificationService] WebSocket 推送失败: " . $e->getMessage());
        }

        return $notificationId;
    }

    /** 发送紧急通知（弹 Toast） */
    public static function sendUrgent(int $userId, string $title, string $content = '', array $options = []): int
    {
        return self::send($userId, $title, $content, ['level' => self::LEVEL_URGENT] + $options);
    }
}
```

## 业务调用示例

```php
// ExportTask.php - 导出完成后发送通知
public function consume($data)
{
    $result = (new ExportService())->export($data['headers'], $data['data'], $data['prefix']);
    (new ExportTaskDep())->updateSuccess($data['task_id'], $result);
    
    NotificationService::sendUrgent($data['user_id'], $data['title'] . ' - 导出完成', '点击查看并下载导出文件', [
        'type' => NotificationService::TYPE_SUCCESS,
        'link' => '/devTools/exportTask'
    ]);
}
```

## 通知列表接口（游标分页）

大量通知场景下，传统分页有深翻页性能问题，改用游标分页：

```php
// NotificationDep.php
public function list(array $param)
{
    $query = $this->model
        ->where('user_id', $param['user_id'])
        ->where('is_del', CommonEnum::NO)
        ->orderBy('id', 'desc');

    // 游标分页：cursor 是上一页最后一条的 ID
    if (!empty($param['cursor'])) {
        $query->where('id', '<', $param['cursor']);
    }

    return $query->limit($param['page_size'] ?? 20)->get();
}
```

**前端复用 LogStream Hook**：

```typescript
const { list, loading, hasMore, loadInitial, loadMore, prepend } = useLogStream<NotificationItem>({
  api: NotificationApi,
  pageSize: 20
})
```

---

# 前端实现

## NotificationCenter 组件

**核心职责**：
1. 显示铃铛图标 + 未读角标
2. 展开面板显示通知列表
3. 监听 WebSocket 消息
4. urgent 级别触发 Toast + Tauri 系统通知

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { onWsMessage } from '@/hooks/useWebSocket'
import { shouldUseNative } from '@/store/tauri'
import { useLogStream } from '@/components/LogStream/src/useLogStream'

const UNREAD = 2
const unreadCount = ref(0)
const { list, loadInitial, loadMore, prepend } = useLogStream<NotificationItem>({ api: NotificationApi, pageSize: 20 })

// WebSocket 监听
let unsubscribe: (() => void) | null = null

onMounted(async () => {
  // 获取初始未读数
  const res = await NotificationApi.unreadCount().catch(() => null)
  unreadCount.value = res?.count || 0
  
  // 监听新通知
  unsubscribe = onWsMessage('notification', async ({ data = {} }) => {
    unreadCount.value++
    prepend({ id: data.id, title: data.title, content: data.content, ... })
    
    if (data.level === 'urgent') {
      // Tauri 系统通知（窗口不可见时）
      if (await shouldUseNative()) {
        const { invoke } = await import('@tauri-apps/api/core')
        invoke('send_notification', { title: data.title, body: data.content })
      }
      // Web Toast 通知
      ElNotification({ title: data.title, message: data.content, type: data.notification_type || 'info', duration: 5000 })
    }
  })
})

onUnmounted(() => unsubscribe?.())
</script>
```

## Tauri 窗口可见性判断

```typescript
// store/tauri.ts
export const isTauri = () => !!(window as any).__TAURI__

export async function shouldUseNative(): Promise<boolean> {
  if (!isTauri()) return false
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    const win = getCurrentWindow()
    const [minimized, focused, visible] = await Promise.all([
      win.isMinimized(), 
      win.isFocused(), 
      win.isVisible()
    ])
    return minimized || !focused || !visible
  } catch {
    return false
  }
}
```

**逻辑**：
- Web 端：始终用 `ElNotification`
- Tauri 端：窗口可见用 `ElNotification`，不可见用系统通知

---

# 用户体验流程

```
1. 用户触发异步任务（如导出）
2. 后台处理完成，调用 NotificationService.sendUrgent()
3. 数据写入 notification 表
4. WebSocket 推送给前端
5. 前端收到消息：
   - 角标 +1
   - 列表头部插入新通知
   - urgent 级别：弹 Toast
   - Tauri 窗口不可见：触发系统通知
6. 用户点击通知，跳转到对应页面
7. 标记已读，角标 -1
```

---

# 关键设计决策

## 1. 为什么不用 WebSocketProvider？

之前的设计是在 `WebSocketProvider` 全局组件里监听通知，但存在问题：
- 职责不单一：连接管理 + 消息处理混在一起
- HMR 热更新时监听器丢失

**现在的设计**：
- `useWebSocket()` 只负责建立连接（在 Layout 调用）
- `onWsMessage()` 是订阅函数，各组件按需调用
- `NotificationCenter` 负责通知相关的所有逻辑

## 2. 为什么用游标分页？

传统分页 `LIMIT 1000, 20` 需要扫描前 1000 条，深翻页很慢。

游标分页 `WHERE id < cursor LIMIT 20` 直接走索引，性能恒定。

## 3. 为什么 Tauri 通知不支持点击回调？

测试发现 Windows 下 `notify-rust` 的 `wait_for_action` 不生效。最终方案：
- 通知只做提醒，不是交互入口
- 托盘是唯一可靠的唤醒入口
- 通知文案引导用户点击托盘

---

# 总结

| 层级 | 组件 | 职责 |
|------|------|------|
| 后端 | NotificationService | 写库 + WebSocket 推送 |
| 后端 | NotificationDep | 数据访问（游标分页） |
| 前端 | useWebSocket | 连接管理 |
| 前端 | NotificationCenter | 角标 + 列表 + Toast + 系统通知 |
| 前端 | store/tauri.ts | Tauri 环境检测 + 窗口状态判断 |

**核心原则**：
- 一次调用完成「写库 + 推送」
- 游标分页解决深翻页性能问题
- 组件就近注册原则
- Web/Tauri 双端兼容

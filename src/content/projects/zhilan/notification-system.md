---
title: 通知管理系统设计与实现：从数据库到 WebSocket 的完整方案
published: 2026-02-04T20:00:00Z
description: 设计并实现一个完整的通知系统，涵盖数据库设计、游标分页、WebSocket 推送、前端组件封装等全流程
tags: [后端, WebSocket, 架构, 通知系统]
category: 后端技术
draft: false
---

# 需求背景

后台管理系统需要一个完善的通知功能：

- 异步任务完成通知（导出、AI 生成等）
- 系统公告广播
- 审批流程提醒
- 实时推送 + 历史记录

之前的做法是各个模块自己推送 WebSocket 消息，没有统一管理，导致：
- 消息格式不统一
- 无法查看历史通知
- 未读数量无法统计
- 推送逻辑重复

是时候做一个统一的通知系统了。

---

# 一、数据库设计

## 表结构

```sql
CREATE TABLE `notifications` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '接收用户ID',
  `title` varchar(100) NOT NULL COMMENT '通知标题',
  `content` varchar(500) NOT NULL COMMENT '通知内容',
  `notification_type` varchar(20) DEFAULT 'info' COMMENT '通知类型：success/warning/error/info',
  `level` varchar(20) DEFAULT 'normal' COMMENT '通知等级：normal/urgent',
  `link` varchar(200) DEFAULT NULL COMMENT '跳转链接',
  `extra_data` json DEFAULT NULL COMMENT '额外数据',
  `is_read` tinyint DEFAULT 0 COMMENT '是否已读：0未读 1已读',
  `read_at` datetime DEFAULT NULL COMMENT '已读时间',
  `is_del` tinyint DEFAULT 0 COMMENT '是否删除：0否 1是',
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user_created` (`user_id`, `created_at`),
  KEY `idx_user_read` (`user_id`, `is_read`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='通知表';
```

### 设计要点

**通知等级**

- `normal`：普通通知，只写库，不弹窗
- `urgent`：紧急通知，写库 + WebSocket 推送 + 前端弹窗

**通知类型**

对应 Element Plus 的通知类型：
- `success`：成功（绿色）
- `warning`：警告（黄色）
- `error`：错误（红色）
- `info`：信息（蓝色）

**索引设计**

- `idx_user_created`：用户 + 创建时间，支持游标分页
- `idx_user_read`：用户 + 已读状态，支持未读数量统计

---

# 二、后端实现

## NotificationService 统一服务

所有通知发送都通过这个服务：

```php
<?php
namespace app\service\System;

use app\dep\System\NotificationDep;
use GatewayWorker\Lib\Gateway;
use support\Log;

class NotificationService
{
    const TYPE_SUCCESS = 'success';
    const TYPE_WARNING = 'warning';
    const TYPE_ERROR = 'error';
    const TYPE_INFO = 'info';

    const LEVEL_NORMAL = 'normal';
    const LEVEL_URGENT = 'urgent';

    /**
     * 发送普通通知（只写库）
     */
    public static function send(
        int $userId,
        string $title,
        string $content,
        array $options = []
    ): int {
        $dep = new NotificationDep();
        return $dep->add([
            'user_id' => $userId,
            'title' => $title,
            'content' => $content,
            'notification_type' => $options['type'] ?? self::TYPE_INFO,
            'level' => self::LEVEL_NORMAL,
            'link' => $options['link'] ?? null,
            'extra_data' => isset($options['extra']) ? json_encode($options['extra']) : null,
        ]);
    }

    /**
     * 发送紧急通知（写库 + WebSocket 推送）
     */
    public static function sendUrgent(
        int $userId,
        string $title,
        string $content,
        array $options = []
    ): int {
        $dep = new NotificationDep();
        
        // 1. 写入数据库
        $id = $dep->add([
            'user_id' => $userId,
            'title' => $title,
            'content' => $content,
            'notification_type' => $options['type'] ?? self::TYPE_INFO,
            'level' => self::LEVEL_URGENT,
   
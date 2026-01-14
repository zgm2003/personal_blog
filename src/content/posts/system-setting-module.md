---
title: 系统设置模块
published: 2026-01-14T21:00:00Z
description: 基于数据库的动态配置管理，支持多类型值、缓存机制，告别硬编码配置文件
tags: [系统, 配置, 缓存, 动态配置]
category: 智澜管理系统
draft: false
---

# 模块概述

系统设置模块将原本散落在 `config/*.php` 中的配置项迁移到数据库，实现：

- 运行时动态修改配置，无需重启服务
- 后台可视化管理，非技术人员也能操作
- 支持多种值类型（字符串、数字、布尔、JSON）
- Redis 缓存加速，避免频繁查库
- 基于注解的权限控制

---

## 数据表设计

```sql
CREATE TABLE `system_settings` (
  `id` bigint UNSIGNED NOT NULL AUTO_INCREMENT,
  `setting_key` varchar(100) NOT NULL COMMENT '配置键',
  `setting_value` text NOT NULL COMMENT '配置值',
  `value_type` tinyint NOT NULL DEFAULT 1 COMMENT '1=string 2=number 3=bool 4=json',
  `remark` varchar(255) NOT NULL DEFAULT '' COMMENT '备注',
  `status` tinyint NOT NULL DEFAULT 1 COMMENT '1启用 2禁用',
  `is_del` tinyint NOT NULL DEFAULT 2 COMMENT '2正常 1软删',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统设置';
```

---

## 配置项命名规范

采用**点分层级命名**：`模块.功能.子项`

| Key | 类型 | 说明 |
|-----|------|------|
| `user.default_avatar` | string | 新用户默认头像 |
| `user.register_enabled` | bool | 是否开放注册 |
| `auth.access_ttl` | number | Access Token 有效期（秒） |
| `auth.refresh_ttl` | number | Refresh Token 有效期（秒） |
| `auth.policy.admin` | json | 后台登录策略 |
| `auth.policy.h5` | json | H5 端登录策略 |
| `auth.policy.app` | json | APP 端登录策略 |
| `auth.policy.mini` | json | 小程序端登录策略 |
| `auth.default_policy` | json | 默认登录策略 |

---

## 后端实现

### 目录结构

```
app/service/System/SettingService.php    # 统一配置读取
app/dep/System/SystemSettingDep.php      # 数据访问（带缓存）
app/module/System/SystemSettingModule.php # CRUD 业务逻辑
app/controller/System/SystemSettingController.php # HTTP 接口
```

### SettingService

```php
use app\service\System\SettingService;

// 获取默认头像
SettingService::getDefaultAvatar();

// 检查是否开放注册
SettingService::isRegisterEnabled();

// 获取 Token 有效期
SettingService::getAccessTtl();
SettingService::getRefreshTtl();

// 获取登录策略
SettingService::getAuthPolicy('admin');
```

### 缓存机制

- 读取时优先查 Redis，未命中再查库并缓存 24 小时
- 写入/更新/删除时自动清除对应缓存
- 缓存 Key 格式：`sys_setting_user_default_avatar`

---

## 权限控制

### 后端注解

```php
/**
 * @OperationLog("系统设置新增")
 * @Permission("systemSetting.add")
 */
public function add(Request $request) { ... }

/**
 * @OperationLog("系统设置编辑")
 * @Permission("systemSetting.edit")
 */
public function edit(Request $request) { ... }

/**
 * @OperationLog("系统设置删除")
 * @Permission("systemSetting.del")
 */
public function del(Request $request) { ... }

/**
 * @OperationLog("系统设置状态变更")
 * @Permission("systemSetting.status")
 */
public function status(Request $request) { ... }
```

### 前端权限

```vue
<el-button v-if="userStore.can('systemSetting.add')" @click="add">新增</el-button>
<el-button v-if="userStore.can('systemSetting.del')" @click="batchDel">批量删除</el-button>
<el-button v-if="userStore.can('systemSetting.edit')" @click="edit(row)">编辑</el-button>
<el-button v-if="userStore.can('systemSetting.status')" @click="toggleStatus(row)">启用/禁用</el-button>
```

### 权限标识

| 标识 | 说明 |
|------|------|
| `systemSetting.add` | 新增配置 |
| `systemSetting.edit` | 编辑配置 |
| `systemSetting.del` | 删除配置（含批量） |
| `systemSetting.status` | 启用/禁用 |

---

## 登录策略 JSON

```json
{
  "bind_platform": true,
  "bind_device": true,
  "bind_ip": true,
  "single_session_per_platform": true
}
```

| 字段 | 说明 |
|------|------|
| `bind_platform` | 校验请求平台与登录平台一致 |
| `bind_device` | 校验设备 ID 一致 |
| `bind_ip` | 校验 IP 地址一致 |
| `single_session_per_platform` | 同平台单会话（互踢） |

---

## API 接口

| 接口 | 权限 | 说明 |
|------|------|------|
| `POST /SystemSetting/init` | - | 获取字典 |
| `POST /SystemSetting/list` | - | 分页列表 |
| `POST /SystemSetting/add` | systemSetting.add | 新增 |
| `POST /SystemSetting/edit` | systemSetting.edit | 编辑 |
| `POST /SystemSetting/del` | systemSetting.del | 删除 |
| `POST /SystemSetting/status` | systemSetting.status | 状态变更 |

---

## 不该放数据库的配置

安全敏感的密钥应保留在 `.env`：

- `TOKEN_PEPPER` - Token 哈希盐值
- `VAULT_KEY` - 敏感数据加密密钥
- 数据库/Redis 连接信息
- 第三方 API 密钥

原因：数据库被拖库或后台权限泄露时，密钥不会暴露。

---

## 总结

适合放数据库：业务开关、可调参数、策略配置

不适合放数据库：安全密钥、连接信息、不变的常量

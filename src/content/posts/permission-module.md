---
title: 权限管理模块
published: 2026-01-14T12:00:00Z
description: RBAC 权限模型、菜单/页面/按钮三级权限、动态路由生成
tags: [用户, 权限, RBAC]
category: 智澜管理系统
draft: false
---

# 模块概述

权限管理是后台系统的核心功能，本实现采用 RBAC（基于角色的访问控制）模型：

- 三级权限类型：目录、页面、按钮
- 角色绑定权限，用户绑定角色
- 前端动态路由生成
- 按钮级权限控制

## 权限模型

```
用户 → 角色 → 权限（目录/页面/按钮）
```

---

## 后端实现

### 权限类型

```php
class PermissionEnum
{
    const TYPE_DIR = 1;     // 目录（菜单分组）
    const TYPE_PAGE = 2;    // 页面（路由）
    const TYPE_BUTTON = 3;  // 按钮（操作权限）
}
```

### 权限表结构

```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,           -- 权限名称
    parent_id INT DEFAULT -1,            -- 父级ID，-1为顶级
    type TINYINT NOT NULL,               -- 类型：1目录 2页面 3按钮
    path VARCHAR(100),                   -- 路由路径（页面）
    component VARCHAR(100),              -- 组件路径（页面）
    icon VARCHAR(50),                    -- 图标（目录/页面）
    code VARCHAR(50),                    -- 权限标识（按钮）
    i18n_key VARCHAR(50),                -- 国际化 key
    sort INT DEFAULT 0,                  -- 排序
    show_menu TINYINT DEFAULT 1,         -- 是否显示在菜单
    status TINYINT DEFAULT 1,            -- 状态
    INDEX idx_parent (parent_id),
    INDEX idx_type (type)
);
```

### 新增权限

```php
public function add($request)
{
    $param = $this->validate($request, PermissionValidate::add());

    // 根据类型校验必填字段
    if ($param['type'] == PermissionEnum::TYPE_DIR) {
        // 目录：需要 i18n_key, show_menu
        $data = [
            'name' => $param['name'],
            'parent_id' => $param['parent_id'] ?? -1,
            'icon' => $param['icon'],
            'type' => $param['type'],
            'i18n_key' => $param['i18n_key'],
            'sort' => $param['sort'],
            'show_menu' => $param['show_menu'],
        ];
    } elseif ($param['type'] == PermissionEnum::TYPE_PAGE) {
        // 页面：需要 path, component, i18n_key
        $data = [
            'name' => $param['name'],
            'parent_id' => $param['parent_id'] ?? -1,
            'path' => $param['path'],
            'component' => $param['component'],
            'type' => $param['type'],
            'icon' => $param['icon'],
            'i18n_key' => $param['i18n_key'],
            'sort' => $param['sort'],
            'show_menu' => $param['show_menu'],
        ];
    } elseif ($param['type'] == PermissionEnum::TYPE_BUTTON) {
        // 按钮：需要 parent_id, code
        $data = [
            'name' => $param['name'],
            'parent_id' => $param['parent_id'],
            'code' => $param['code'],
            'type' => $param['type'],
            'sort' => $param['sort'],
        ];
    }

    $this->permissionDep->add($data);
    
    // 清除缓存
    PermissionDep::clearCache();
    DictService::clearPermissionCache();
    
    return self::success();
}
```

### 权限树查询

```php
public function list($request)
{
    $resList = $this->permissionDep->list($param);

    $data['list'] = $resList->map(function ($item) {
        return [
            'id' => $item->id,
            'name' => $item->name,
            'path' => $item->path,
            'parent_id' => $item->parent_id,
            'icon' => $item->icon,
            'component' => $item->component,
            'type' => $item->type,
            'type_name' => PermissionEnum::$typeArr[$item->type],
            'code' => $item->code,
            'i18n_key' => $item->i18n_key,
            'sort' => $item->sort,
            'show_menu' => $item->show_menu,
        ];
    });

    // 转换为树形结构
    $data['menu_tree'] = listToTree($data['list']->toArray(), -1);

    return self::success($data['menu_tree']);
}
```

---

## 角色管理

### 角色表结构

```sql
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    permission_id JSON,                  -- 权限ID数组
    is_default TINYINT DEFAULT 0,        -- 是否默认角色
    is_del TINYINT DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### 角色绑定权限

```php
public function add($request)
{
    $param = $this->validate($request, RoleValidate::add());
    
    // 检查角色名唯一
    self::throwIf($this->roleDep->findByName($param['name']), '角色名已存在');
    
    $data = [
        'name' => $param['name'],
        'permission_id' => json_encode($param['permission_id']),  // 权限ID数组
    ];
    $this->roleDep->add($data);
    
    return self::success();
}
```

### 设置默认角色

新用户自动注册时使用默认角色：

```php
public function setDefault($request)
{
    $param = $this->validate($request, RoleValidate::setDefault());
    $id = (int)$param['id'];

    // 事务：清除旧默认 + 设置新默认
    $this->withTransaction(function () use ($id) {
        $this->roleDep->clearDefault();
        $this->roleDep->update($id, ['is_default' => CommonEnum::YES]);
    });

    return self::success();
}
```

### 角色删除时清除缓存

```php
public function del($request)
{
    $ids = is_array($param['id']) ? $param['id'] : [$param['id']];
    
    // 默认角色不能删除
    self::throwIf($this->roleDep->hasDefaultIn($ids), '默认角色不能删除');
    
    $this->roleDep->delete($ids);

    // 清除该角色下所有用户的权限缓存
    $usersDep = new UsersDep();
    $userIds = $usersDep->getIdsByRoleIds($ids);
    foreach ($userIds as $uid) {
        Cache::delete('auth_perm_uid_' . $uid);
    }

    return self::success();
}
```

---

## 前端实现

### 动态路由生成

```typescript
// router/permission.ts
export async function generateRoutes(): Promise<RouteRecordRaw[]> {
  const { data } = await UserApi.getPermissions()
  
  const routes = filterAsyncRoutes(data.permissions)
  return routes
}

function filterAsyncRoutes(permissions: Permission[]): RouteRecordRaw[] {
  const routes: RouteRecordRaw[] = []
  
  permissions.forEach(permission => {
    if (permission.type === PermissionType.DIR) {
      // 目录：创建父路由
      const route: RouteRecordRaw = {
        path: '/' + permission.path,
        component: Layout,
        meta: {
          title: permission.i18n_key,
          icon: permission.icon,
        },
        children: permission.children 
          ? filterAsyncRoutes(permission.children) 
          : []
      }
      routes.push(route)
    } else if (permission.type === PermissionType.PAGE) {
      // 页面：动态导入组件
      const route: RouteRecordRaw = {
        path: permission.path,
        component: () => import(`@/views/${permission.component}.vue`),
        meta: {
          title: permission.i18n_key,
          icon: permission.icon,
        }
      }
      routes.push(route)
    }
  })
  
  return routes
}
```

### 按钮权限指令

```typescript
// directives/permission.ts
export const permission: Directive = {
  mounted(el: HTMLElement, binding) {
    const { value } = binding
    const permissions = useUserStore().permissions
    
    if (value && !permissions.includes(value)) {
      el.parentNode?.removeChild(el)
    }
  }
}

// 使用
<el-button v-permission="'user:add'">新增用户</el-button>
<el-button v-permission="'user:delete'">删除用户</el-button>
```

### 权限 Hook

```typescript
// composables/usePermission.ts
export function usePermission() {
  const userStore = useUserStore()
  
  const hasPermission = (code: string | string[]): boolean => {
    const codes = Array.isArray(code) ? code : [code]
    return codes.some(c => userStore.permissions.includes(c))
  }
  
  return { hasPermission }
}

// 使用
const { hasPermission } = usePermission()

if (hasPermission('user:edit')) {
  // 显示编辑按钮
}
```

---

## 权限缓存策略

### 后端缓存

```php
// 用户权限缓存
$cacheKey = 'auth_perm_uid_' . $userId;
$permissions = Cache::get($cacheKey);

if (!$permissions) {
    $user = $this->usersDep->find($userId);
    $role = $this->roleDep->find($user->role_id);
    $permissionIds = json_decode($role->permission_id, true);
    $permissions = $this->permissionDep->getByIds($permissionIds);
    
    Cache::set($cacheKey, $permissions, 3600);  // 1小时
}
```

### 缓存失效时机

- 角色权限变更 → 清除该角色所有用户缓存
- 用户角色变更 → 清除该用户缓存
- 权限变更 → 清除全局权限缓存

---

## 数据示例

### 权限树

```json
[
  {
    "id": 1,
    "name": "系统管理",
    "type": 1,
    "icon": "setting",
    "children": [
      {
        "id": 2,
        "name": "用户管理",
        "type": 2,
        "path": "/system/user",
        "component": "system/user/index",
        "children": [
          { "id": 3, "name": "新增", "type": 3, "code": "user:add" },
          { "id": 4, "name": "编辑", "type": 3, "code": "user:edit" },
          { "id": 5, "name": "删除", "type": 3, "code": "user:delete" }
        ]
      }
    ]
  }
]
```

### 角色

```json
{
  "id": 1,
  "name": "管理员",
  "permission_id": [1, 2, 3, 4, 5, 6, 7, 8],
  "is_default": 0
}
```

---

## 扩展方向

- 数据权限（部门/创建人过滤）
- 权限继承（子角色继承父角色）
- 临时权限（时效性授权）
- 权限审计日志

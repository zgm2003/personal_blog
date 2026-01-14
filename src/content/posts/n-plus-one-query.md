---
title: N+1 查询优化
published: 2026-01-13T13:00:00Z
description: 批量预加载 + keyBy 解决 N+1 查询问题
tags: [后端, 性能, 数据库]
category: 智澜管理系统
draft: false
---

# 什么是 N+1 问题？

假设要查询 20 个用户及其角色名称：

```php
// ❌ 错误写法
$users = $userDep->list($param);  // 1 次查询

foreach ($users as $user) {
    $role = $roleDep->first($user->role_id);  // 每次循环查 1 次
    $user->role_name = $role->name;
}
// 总共：1 + 20 = 21 次数据库查询！
```

20 条数据查 21 次，200 条就是 201 次。Webman 常驻内存的优势全被浪费了。

## 解决方案：批量预加载 + keyBy

```php
// ✅ 正确写法
$users = $userDep->list($param);  // 1 次查询

// Step 1: 提取所有 role_id
$roleIds = $users->pluck('role_id')->unique()->toArray();

// Step 2: 批量查询，keyBy 转成 Map
$roleMap = $roleDep->getMapActive($roleIds);  // 1 次查询

// Step 3: O(1) 关联
$users->map(function ($user) use ($roleMap) {
    $role = $roleMap->get($user->role_id);
    $user->role_name = $role?->name ?? '';
});
// 总共：2 次数据库查询！
```

从 21 次降到 2 次，性能提升 10 倍。

## BaseDep 封装

在 `BaseDep` 基类中封装批量查询方法：

```php
abstract class BaseDep
{
    /**
     * 批量查询，返回 id => model 的 Collection
     */
    public function getMap(array $ids)
    {
        if (empty($ids)) {
            return collect();
        }
        return $this->model
            ->whereIn('id', array_unique($ids))
            ->get()
            ->keyBy('id');
    }

    /**
     * 批量查询（只查未删除的）
     */
    public function getMapActive(array $ids)
    {
        if (empty($ids)) {
            return collect();
        }
        return $this->model
            ->whereIn('id', array_unique($ids))
            ->where('is_del', CommonEnum::NO)
            ->get()
            ->keyBy('id');
    }
}
```

## Laravel Collection 常用方法

| 方法 | 作用 | 示例 |
|------|------|------|
| `pluck('field')` | 提取某字段 | `$users->pluck('id')` |
| `->unique()` | 去重 | `->pluck('role_id')->unique()` |
| `->toArray()` | 转数组 | `->unique()->toArray()` |
| `->keyBy('id')` | 转 Map | `->get()->keyBy('id')` |
| `->get($key)` | O(1) 取值 | `$roleMap->get(5)` |

## 实际案例：用户列表

```php
public function list($request): array
{
    $param = $request->all();
    $users = $this->usersDep->list($param);
    
    // 批量获取关联数据
    $roleIds = $users->pluck('role_id')->unique()->toArray();
    $deptIds = $users->pluck('dept_id')->unique()->toArray();
    
    $roleMap = $this->rolesDep->getMapActive($roleIds);
    $deptMap = $this->deptsDep->getMapActive($deptIds);
    
    // O(1) 关联
    $users->map(function ($user) use ($roleMap, $deptMap) {
        $user->role_name = $roleMap->get($user->role_id)?->name ?? '';
        $user->dept_name = $deptMap->get($user->dept_id)?->name ?? '';
    });
    
    return self::paginate($users, [...]);
}
```

## 性能对比

| 数据量 | N+1 查询次数 | 优化后查询次数 |
|--------|-------------|---------------|
| 20 条 | 21 次 | 3 次 |
| 100 条 | 101 次 | 3 次 |
| 1000 条 | 1001 次 | 3 次 |

## Checklist

开发新功能时，检查：

- [ ] 列表接口是否有循环内查询？
- [ ] 导出接口是否有循环内查询？
- [ ] 是否使用了 `getMap` / `getMapActive`？

N+1 问题是后端性能优化的基础，务必重视。

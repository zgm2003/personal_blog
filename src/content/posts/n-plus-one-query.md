---
title: N+1 查询优化
published: 2026-01-13T13:00:00Z
description: 批量预加载 + keyBy 解决 N+1 查询问题
tags: [后端, 性能, 数据库]
category: 数据库
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

## 进阶：多层级关联的 N+1

实际业务中，关联关系往往不止一层。比如：用户列表需要显示角色名、部门名、创建人名。

```php
public function list($request): array
{
    $param = $this->validate($request, UserValidate::list());
    $res = $this->dep(UsersDep::class)->list($param);
    $users = $res->items();

    // 收集所有需要关联的 ID
    $roleIds = collect($users)->pluck('role_id')->unique()->filter()->toArray();
    $deptIds = collect($users)->pluck('dept_id')->unique()->filter()->toArray();
    $creatorIds = collect($users)->pluck('created_by')->unique()->filter()->toArray();

    // 批量查询（3 次查询搞定所有关联）
    $roleMap = $this->dep(RolesDep::class)->getMapActive($roleIds);
    $deptMap = $this->dep(DeptsDep::class)->getMapActive($deptIds);
    $creatorMap = $this->dep(UsersDep::class)->getMap($creatorIds);

    // O(1) 关联赋值
    collect($users)->each(function ($user) use ($roleMap, $deptMap, $creatorMap) {
        $user->role_name = $roleMap->get($user->role_id)?->name ?? '';
        $user->dept_name = $deptMap->get($user->dept_id)?->name ?? '';
        $user->creator_name = $creatorMap->get($user->created_by)?->nickname ?? '';
    });

    return self::paginate($users, [
        'current_page' => $res->currentPage(),
        'page_size' => $res->perPage(),
        'total' => $res->total(),
    ]);
}
```

关键点：`->filter()` 过滤掉 null 和 0 值，避免无效查询。

## 进阶：导出场景的 N+1 陷阱

导出功能是 N+1 的重灾区。因为导出通常是全量数据，如果有 N+1 问题，几千条数据能产生几千次查询，直接把数据库打爆。

```php
// ❌ 导出时的 N+1 灾难
public function export($request): array
{
    $list = $this->dep(OrdersDep::class)->getAll(); // 5000 条

    foreach ($list as $order) {
        // 每条订单查一次用户 → 5000 次查询
        $user = $this->dep(UsersDep::class)->getById($order->user_id);
        $order->user_name = $user?->nickname ?? '';

        // 每条订单查一次商品 → 又 5000 次查询
        $goods = $this->dep(GoodsDep::class)->getById($order->goods_id);
        $order->goods_title = $goods?->title ?? '';
    }
    // 总计：1 + 5000 + 5000 = 10001 次查询！
}
```

正确做法：

```php
// ✅ 导出时的批量预加载
public function export($request): array
{
    $list = $this->dep(OrdersDep::class)->getAll();

    $userIds = $list->pluck('user_id')->unique()->filter()->toArray();
    $goodsIds = $list->pluck('goods_id')->unique()->filter()->toArray();

    $userMap = $this->dep(UsersDep::class)->getMap($userIds);
    $goodsMap = $this->dep(GoodsDep::class)->getMap($goodsIds);

    $list->each(function ($order) use ($userMap, $goodsMap) {
        $order->user_name = $userMap->get($order->user_id)?->nickname ?? '';
        $order->goods_title = $goodsMap->get($order->goods_id)?->title ?? '';
    });
    // 总计：3 次查询！
}
```

5000 条数据，从 10001 次查询降到 3 次。这不是优化，这是救命。

## 进阶：when 条件查询的封装

在 Dep 层，经常需要根据搜索条件动态拼接查询。Eloquent 的 `when` 方法非常适合这个场景：

```php
public function list(array $param)
{
    return $this->model
        ->where('is_del', CommonEnum::NO)
        ->when($param['title'] ?? null, fn($q, $v) =>
            $q->where('title', 'like', "%{$v}%"))
        ->when($param['status'] ?? null, fn($q, $v) =>
            $q->where('status', $v))
        ->when($param['start_date'] ?? null, fn($q, $v) =>
            $q->where('created_at', '>=', $v))
        ->when($param['end_date'] ?? null, fn($q, $v) =>
            $q->where('created_at', '<=', $v . ' 23:59:59'))
        ->orderBy('id', 'desc')
        ->paginate($param['page_size'] ?? 20);
}
```

`when($value, $callback)` 的语义是：当 `$value` 为真值时才执行 `$callback`。这比一堆 `if` 判断优雅得多，而且链式调用不会断。

## 性能监控：怎么发现 N+1？

光靠代码审查很难发现所有 N+1 问题。我的做法是在开发环境开启查询日志：

```php
// 在 bootstrap.php 中
if (config('app.debug')) {
    \Illuminate\Database\Capsule\Manager::connection()
        ->enableQueryLog();

    // 请求结束后输出查询次数
    register_shutdown_function(function () {
        $queries = \Illuminate\Database\Capsule\Manager::connection()
            ->getQueryLog();
        $count = count($queries);

        if ($count > 10) {
            Log::warning("High query count: {$count}", [
                'uri' => request()->uri(),
                'queries' => array_slice($queries, 0, 20),
            ]);
        }
    });
}
```

当一个请求的查询次数超过 10 次时，自动记录警告日志。这样就能在开发阶段及时发现 N+1 问题。

## 总结

| 场景 | 错误做法 | 正确做法 |
|------|---------|---------|
| 列表关联 | 循环内 getById | pluck + getMap |
| 导出关联 | 循环内查询 | 批量预加载 |
| 多层关联 | 嵌套循环查询 | 多次 getMap |
| 条件查询 | if 拼接 SQL | when 链式调用 |

N+1 问题是后端性能优化的基础，务必重视。记住一个原则：永远不要在循环里查数据库。

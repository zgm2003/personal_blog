---
title: 按钮权限系统
published: 2026-01-28T12:00:00Z
description: 扁平化按钮权限、独立路由隔离、缓存一致性保证
tags: [权限, Redis, Capacitor]
project: 智澜APP
order: 10
draft: false
---

# 模块概述

移动端（APP/H5/小程序）采用**扁平化按钮权限**架构，与 PC 后台的树形权限分离：

- **PC 后台**：目录 → 页面 → 按钮（三级树形）
- **移动端**：纯按钮权限（扁平列表）

这种设计的原因：
1. 移动端页面路由固定，无需动态生成
2. 只需控制「能不能点这个按钮」
3. 简化权限配置，降低运维成本

---

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (H5/APP)                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ v-permission│    │ userStore   │    │   API 调用   │  │
│  │   指令      │ ← │   .can()    │    │             │  │
│  └─────────────┘    └─────────────┘    └──────┬──────┘  │
└────────────────────────────────────────────────┼────────┘
                                                 ↓
┌─────────────────────────────────────────────────────────┐
│                    后端 (app.php 路由)                    │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │ CheckToken  │ → │CheckPermission│ → │ Controller  │  │
│  │  中间件     │    │   中间件     │    │             │  │
│  └─────────────┘    └─────────────┘    └─────────────┘  │
│                            ↓                             │
│                    ┌─────────────┐                       │
│                    │ Redis 缓存  │                       │
│                    │auth_perm_uid│                       │
│                    └─────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

---

## 后端实现

### 独立路由文件

移动端接口使用独立的 `app.php` 路由，与 PC 后台 `admin.php` 隔离：

```php
// routes/app.php
Route::group('/api/app', function () {
    // CORS 预检
    Route::add(['OPTIONS'], '/{path:.+}', fn() => response(''));
});

Route::group('/api/app', function () {
    Route::post('/test', [AppController::class, 'test']);
    Route::post('/order/create', [OrderController::class, 'create']);
})->middleware([
    CheckToken::class,
    CheckPermission::class,
    OperationLog::class,
]);
```

### Controller 权限注解

```php
class AppController extends Controller
{
    /**
     * @OperationLog("APP测试")
     * @Permission("test_test")
     */
    public function test(Request $request)
    {
        return $this->run([AppModule::class, 'test'], $request);
    }
}
```

### 权限校验中间件

```php
public function process(Request $request, callable $handler): Response
{
    $permissionCode = AnnotationParser::getPermission($request);
    if (!$permissionCode) return $handler($request);

    // 从缓存读取用户权限
    $platform = $request->platform;  // 'app'
    $cacheKey = 'auth_perm_uid_' . $request->userId . '_' . $platform;
    $buttonCodes = Cache::get($cacheKey);

    // 缓存失效时重建
    if (!is_array($buttonCodes)) {
        $perm = $permissionService->buildPermissionContextByUser($user, $platform);
        $buttonCodes = $perm['buttonCodes'];
        Cache::set($cacheKey, $buttonCodes, 300);
    }

    // 校验权限
    if (!in_array($permissionCode, $buttonCodes, true)) {
        return json(['code' => 403, 'msg' => '无权限访问']);
    }

    return $handler($request);
}
```

---

## 缓存策略

### 三层缓存设计

| 缓存 Key | 数据 | TTL | 清除时机 |
|---------|------|-----|---------|
| `perm_all_permissions` | 全部权限定义 | **永久** | 权限增删改 |
| `dict_permission_tree` | 权限树 | **永久** | 权限增删改 |
| `auth_perm_uid_{id}_{platform}` | 用户按钮权限 | 300秒 | 权限状态变更 |

### 状态变更时清除缓存

```php
public function status($request)
{
    $this->permissionDep->update($param['id'], ['status' => $param['status']]);
    
    PermissionDep::clearCache();
    DictService::clearPermissionCache();
    self::clearAllUserPermCache();  // 清除所有用户权限缓存
    
    return self::success();
}

public static function clearAllUserPermCache(): void
{
    $redis = Redis::connection('cache');
    $keys = $redis->keys('cache:auth_perm_uid_*');
    if (!empty($keys)) {
        $redis->del(...$keys);
    }
}
```

---

## 前端实现

### UserStore 权限管理

```typescript
// stores/modules/user.ts
export const useUserStore = defineStore('user', {
  state: () => ({
    buttons: [] as string[],
  }),
  
  actions: {
    async fetchProfile() {
      const { data } = await UserApi.profile()
      this.buttons = data.buttonCodes || []
    },
    
    can(code: string): boolean {
      return this.buttons.includes(code)
    },
  },
})
```

### v-permission 指令

```typescript
// directives/permission.ts
export const permission: Directive<HTMLElement, string> = {
  mounted(el, binding) {
    const userStore = useUserStore()
    if (binding.value && !userStore.can(binding.value)) {
      el.parentNode?.removeChild(el)
    }
  },
}
```

### 使用示例

```vue
<template>
  <!-- 方式1：v-permission 指令 -->
  <van-button v-permission="'order_create'" type="primary">
    创建订单
  </van-button>
  
  <!-- 方式2：v-if + can() -->
  <van-button v-if="userStore.can('order_cancel')" type="danger">
    取消订单
  </van-button>
</template>
```

---

## 与 PC 后台的差异

| 维度 | PC 后台 | APP/H5 |
|------|--------|--------|
| 权限层级 | 目录 → 页面 → 按钮 | 仅按钮 |
| 路由 | 动态生成 | 固定路由 |
| 权限结构 | 树形 | 扁平 |
| 路由文件 | admin.php | app.php |
| platform | admin | app |

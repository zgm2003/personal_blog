---
title: 路由设计
published: 2026-01-28T11:00:00Z
description: 白名单机制、登录拦截、固定路由架构
tags: [路由, Vue Router, 白名单]
project: 智澜APP
order: 20
draft: false
---

# 路由设计

移动端采用**固定路由 + 白名单**架构，与 PC 后台的动态路由模式不同。

## 设计理念

| 维度 | PC 后台 | 智澜APP |
|------|--------|---------|
| 路由模式 | 动态生成 | 固定配置 |
| 权限控制 | 路由级 + 按钮级 | 仅按钮级 |
| 访问策略 | 白名单外需鉴权 | 白名单外需登录 |

**为什么移动端不用动态路由？**
1. 移动端页面数量有限，固定配置更简单
2. 页面权限通过按钮控制，无需路由级隔离
3. 减少首屏加载时的路由计算开销

---

## 路由配置

### 固定路由表

```typescript
// router/routes.ts
export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'index',
    component: () => import('@/pages/index.vue'),
    meta: { title: '首页', keepAlive: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/login/index.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/pages/profile/index.vue'),
    meta: { title: '个人中心' },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/pages/settings/index.vue'),
    meta: { title: '设置' },
  },
  // 404 兜底
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]
```

---

## 白名单机制

### 白名单配置

```typescript
// router/whitelist.ts
export const whiteList = [
  '/login',
  '/register',
  '/forgot-password',
  '/privacy',
  '/agreement',
]
```

### 路由守卫

```typescript
// router/index.ts
import { whiteList } from './whitelist'

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token

  // 白名单直接放行
  if (whiteList.includes(to.path)) {
    return next()
  }

  // 无 Token 跳登录
  if (!token) {
    return next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
  }

  // 已登录但无用户信息，获取 Profile
  if (!userStore.userInfo?.id) {
    try {
      await userStore.fetchProfile()
    } catch (error) {
      // Token 失效，清除并跳登录
      userStore.logout()
      return next({ path: '/login' })
    }
  }

  next()
})
```

---

## 路由流程图

```
用户访问页面
      │
      ▼
┌─────────────┐
│ 是否在白名单？│
└─────────────┘
      │
    Yes ─────────────────────────────┐
      │                              │
      No                             │
      │                              │
      ▼                              │
┌─────────────┐                      │
│ 是否有 Token？│                     │
└─────────────┘                      │
      │                              │
    No ──────┐                       │
      │      │                       │
    Yes      ▼                       │
      │  跳转登录页                   │
      │  (带 redirect)               │
      ▼                              │
┌─────────────┐                      │
│ 是否有用户信息？│                    │
└─────────────┘                      │
      │                              │
    No ──────┐                       │
      │      │                       │
    Yes      ▼                       │
      │  fetchProfile()              │
      │      │                       │
      │      ▼                       │
      │  成功 ─────────────┐         │
      │      │             │         │
      │    失败            │         │
      │      │             │         │
      │      ▼             │         │
      │  logout()          │         │
      │  跳转登录           │         │
      │                    │         │
      ▼                    ▼         ▼
┌─────────────────────────────────────┐
│              放行                    │
└─────────────────────────────────────┘
```

---

## 页面缓存

### KeepAlive 配置

```typescript
// router/routes.ts
{
  path: '/',
  name: 'index',
  component: () => import('@/pages/index.vue'),
  meta: { 
    title: '首页', 
    keepAlive: true,  // 启用缓存
  },
},
```

### App.vue 实现

```vue
<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive :include="cachedRoutes">
      <component :is="Component" :key="route.fullPath" />
    </keep-alive>
  </router-view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouteCacheStore } from '@/stores/modules/routeCache'

const routeCacheStore = useRouteCacheStore()
const cachedRoutes = computed(() => routeCacheStore.cachedRoutes)
</script>
```

### 缓存 Store

```typescript
// stores/modules/routeCache.ts
export const useRouteCacheStore = defineStore('routeCache', {
  state: () => ({
    cachedRoutes: [] as string[],
  }),
  actions: {
    addRoute(route: RouteLocationNormalized) {
      const name = route.name as string
      if (route.meta?.keepAlive && !this.cachedRoutes.includes(name)) {
        this.cachedRoutes.push(name)
      }
    },
    removeRoute(name: string) {
      const index = this.cachedRoutes.indexOf(name)
      if (index > -1) {
        this.cachedRoutes.splice(index, 1)
      }
    },
  },
})
```

---

## 404 处理

移动端 404 统一重定向到首页：

```typescript
{
  path: '/:pathMatch(.*)*',
  name: 'NotFound',
  redirect: '/',
}
```

> **为什么不显示 404 页面？** 移动端用户体验优先，未定义路由直接回首页比显示错误页更友好。

---

## 登录跳转

### 带 redirect 参数

```typescript
// 未登录时保存目标路径
next({
  path: '/login',
  query: { redirect: to.fullPath },
})
```

### 登录成功后跳转

```typescript
// login/index.vue
const route = useRoute()
const router = useRouter()

const onLoginSuccess = () => {
  const redirect = route.query.redirect as string
  router.replace(redirect || '/')
}
```

---

## 相关文档

- [按钮权限系统](/projects/zhilan-app/button-permission) - 页面内按钮控制
- [项目白皮书](/projects/zhilan-app/whitepaper) - 项目概述

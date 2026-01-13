---
title: Axios 无感刷新 Token：优雅处理 401
published: 2026-01-13T14:00:00Z
description: 用户无感知的 Token 自动续期方案，请求队列 + 自动重试
tags: [前端, Axios, 鉴权, TypeScript]
category: 技术
draft: false
---

# 问题场景

用户正在操作，突然 Token 过期了：

- 方案 A：直接跳登录页 → 用户骂娘
- 方案 B：自动刷新 Token，重试请求 → 用户无感知

显然选 B。

## 核心思路

1. 拦截 401 响应
2. 用 refresh_token 换新 access_token
3. 重试原请求
4. 多个请求同时 401 时，只刷新一次

## 实现代码

```typescript
let isRefreshing = false
let requestsQueue: { resolve: Function; reject: Function; config: any }[] = []

function handle401(originalRequest: any) {
  // 已经重试过，直接退出登录
  if (originalRequest._retry) {
    logoutAndRedirect()
    return Promise.reject(new Error('Unauthorized'))
  }
  
  originalRequest._retry = true
  
  // 入队等待
  const p = new Promise((resolve, reject) => {
    requestsQueue.push({ resolve, reject, config: originalRequest })
  })
  
  // 只有第一个 401 触发刷新
  if (!isRefreshing) {
    isRefreshing = true
    
    const refreshToken = Cookies.get('refresh_token')
    if (!refreshToken) {
      logoutAndRedirect()
      return Promise.reject(new Error('No refresh token'))
    }
    
    axios.post('/api/Users/refresh', { refresh_token: refreshToken })
      .then(res => {
        const { access_token, refresh_token: newRefresh } = res.data.data
        
        // 保存新 Token
        Cookies.set('access_token', access_token)
        Cookies.set('refresh_token', newRefresh)
        
        // 重试队列中的所有请求
        isRefreshing = false
        processQueue(null, access_token)
      })
      .catch(() => {
        isRefreshing = false
        logoutAndRedirect()
      })
  }
  
  return p
}

function processQueue(error: Error | null, token: string | null) {
  requestsQueue.forEach(({ resolve, reject, config }) => {
    if (error) {
      reject(error)
    } else {
      config.headers['Authorization'] = `Bearer ${token}`
      resolve(axios(config))  // 重试请求
    }
  })
  requestsQueue = []
}
```

## 响应拦截器

```typescript
service.interceptors.response.use(
  (res) => {
    const { code, msg, data } = res.data
    
    if (code === 401) {
      return handle401(res.config)
    }
    
    if (code !== 0) {
      ElNotification.error({ message: msg })
      return Promise.reject(new Error(msg))
    }
    
    return data
  },
  (error) => {
    // HTTP 401 也走刷新逻辑
    if (error.response?.status === 401) {
      return handle401(error.config)
    }
    
    ElNotification.error({ message: error.message })
    return Promise.reject(error)
  }
)
```

## 关键点

### 1. 请求队列

多个请求同时 401 时，只刷新一次 Token，其他请求入队等待：

```typescript
// 请求 A: 401 → 触发刷新 → 入队
// 请求 B: 401 → 发现正在刷新 → 入队
// 请求 C: 401 → 发现正在刷新 → 入队
// 刷新成功 → 重试 A、B、C
```

### 2. 防止无限循环

用 `_retry` 标记防止刷新接口本身 401 时无限循环：

```typescript
if (originalRequest._retry) {
  logoutAndRedirect()
  return
}
originalRequest._retry = true
```

### 3. refresh_token 也过期

refresh_token 通常有效期较长（如 14 天），如果也过期了，只能跳登录页。

## 后端配合

```php
public function refresh($request): array
{
    $refreshToken = $request->post('refresh_token');
    
    // 验证 refresh_token
    $payload = $this->tokenService->verifyRefreshToken($refreshToken);
    if (!$payload) {
        return self::error('refresh_token 无效', 401);
    }
    
    // 生成新的 access_token
    $accessToken = $this->tokenService->generateAccessToken($payload['user_id']);
    
    // 可选：同时刷新 refresh_token（滑动过期）
    $newRefreshToken = $this->tokenService->generateRefreshToken($payload['user_id']);
    
    return self::success([
        'access_token' => $accessToken,
        'refresh_token' => $newRefreshToken,
        'expires_in' => 7200,
    ]);
}
```

## 效果

- 用户无感知，操作不中断
- 多请求并发时只刷新一次
- refresh_token 过期才跳登录页

这是后台管理系统的标配功能，体验提升明显。

---
title: Token 无感刷新（前端实现）
published: 2026-01-14T14:00:00Z
description: Axios 拦截器实现 Token 自动续期，请求队列 + 防抖弹框
tags: [前端, 鉴权, Axios]
category: 前端技术
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
5. 错误弹框防抖，避免重复提示

## 防抖弹框

页面加载时可能同时发多个请求，Token 过期后会同时返回 401。如果不防抖，会弹一堆提示框。

```typescript
let lastNotifyTime = 0
let lastNotifyMsg = ''
const NOTIFY_DEBOUNCE = 2000  // 2秒内相同消息不重复弹

function notify(message: string) {
  const now = Date.now()
  if (message === lastNotifyMsg && now - lastNotifyTime < NOTIFY_DEBOUNCE) {
    return
  }
  lastNotifyTime = now
  lastNotifyMsg = message
  ElNotification.error({ message })
}
```

## 401 处理

```typescript
let isRefreshing = false
let requestsQueue: { resolve: Function; reject: Function; config: any }[] = []

function handle401(originalRequest: any, messageFromServer?: string) {
  // 已经重试过或 refresh 接口本身失败，直接退出登录
  if (originalRequest?.url?.includes('/api/Users/refresh') || originalRequest?._retry) {
    isRefreshing = false
    notify(messageFromServer || '登录过期，请重新登录')
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
      isRefreshing = false
      notify('登录过期，请重新登录')
      logoutAndRedirect()
      return Promise.reject(new Error('No refresh token'))
    }
    
    axios.post('/api/Users/refresh', { refresh_token: refreshToken })
      .then(res => {
        const { access_token, refresh_token: newRefresh, expires_in } = res.data.data
        
        // 保存新 Token
        const expires = new Date(new Date().getTime() + expires_in * 1000)
        Cookies.set('access_token', access_token, { expires })
        Cookies.set('refresh_token', newRefresh, { expires: 14 })
        
        // 重试队列中的所有请求
        isRefreshing = false
        processQueue(null, access_token)
      })
      .catch(() => {
        isRefreshing = false
        notify('网络错误，请重新登录')
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
      resolve(axios(config))
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
      return handle401(res.config, msg)
    }
    
    if (code !== 0) {
      notify(msg || '请求失败')
      return Promise.reject(new Error(msg))
    }
    
    return data
  },
  (error) => {
    const status = error.response?.status
    
    if (status === 401) {
      return handle401(error.config, error.response?.data?.msg)
    }
    
    const message = error.response?.data?.msg || error.message || '请求失败'
    notify(message)
    return Promise.reject(error)
  }
)
```

## 关键点

### 1. 请求队列

多个请求同时 401 时，只刷新一次 Token，其他请求入队等待：

```
请求 A: 401 → 触发刷新 → 入队
请求 B: 401 → 发现正在刷新 → 入队
请求 C: 401 → 发现正在刷新 → 入队
刷新成功 → 重试 A、B、C
```

### 2. 防止无限循环

用 `_retry` 标记防止刷新接口本身 401 时无限循环。

### 3. 防抖弹框

2 秒内相同消息不重复弹，避免多个 401 同时弹一堆提示。

### 4. refresh_token 也过期

refresh_token 有效期 14 天，如果也过期了，只能跳登录页。

## 效果

- 用户无感知，操作不中断
- 多请求并发时只刷新一次
- 错误提示不重复弹框
- refresh_token 过期才跳登录页

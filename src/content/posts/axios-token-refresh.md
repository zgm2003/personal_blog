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

## 完整的 Axios 封装

Token 刷新只是 Axios 封装的一部分。一个生产级的 Axios 实例还需要处理很多细节：

```typescript
import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import Cookies from 'js-cookie'
import { ElNotification } from 'element-plus'
import router from '@/router'

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})
```

### 请求拦截器

每个请求自动带上 Token 和语言标识：

```typescript
service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = Cookies.get('access_token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }

    // 国际化：告诉后端当前语言
    const locale = localStorage.getItem('locale') || 'zh-CN'
    config.headers['Accept-Language'] = locale

    return config
  },
  (error) => Promise.reject(error)
)
```

### 响应拦截器的分层处理

响应拦截器需要处理多种情况：

```typescript
service.interceptors.response.use(
  (res: AxiosResponse) => {
    const { code, msg, data } = res.data

    // 业务成功
    if (code === 0) return data

    // Token 过期
    if (code === 401) return handle401(res.config, msg)

    // 权限不足
    if (code === 403) {
      notify('没有操作权限')
      return Promise.reject(new Error(msg))
    }

    // 其他业务错误
    notify(msg || '请求失败')
    return Promise.reject(new Error(msg))
  },
  (error) => {
    // 网络层错误（非业务错误）
    if (error.response) {
      const { status, data } = error.response

      if (status === 401) return handle401(error.config, data?.msg)
      if (status === 413) return notify('上传文件过大')
      if (status === 429) return notify('请求过于频繁，请稍后再试')
      if (status >= 500) return notify('服务器错误，请稍后再试')

      notify(data?.msg || '请求失败')
    } else if (error.code === 'ECONNABORTED') {
      notify('请求超时，请检查网络')
    } else {
      notify('网络连接失败')
    }

    return Promise.reject(error)
  }
)
```

### 封装请求方法

最后封装常用的请求方法，让业务代码更简洁：

```typescript
export const http = {
  get<T = any>(url: string, params?: Record<string, any>): Promise<T> {
    return service.get(url, { params })
  },

  post<T = any>(url: string, data?: Record<string, any>): Promise<T> {
    return service.post(url, data)
  },

  put<T = any>(url: string, data?: Record<string, any>): Promise<T> {
    return service.put(url, data)
  },

  delete<T = any>(url: string, data?: Record<string, any>): Promise<T> {
    return service.delete(url, { data })
  },

  // 文件上传
  upload<T = any>(url: string, file: File, fieldName = 'file'): Promise<T> {
    const formData = new FormData()
    formData.append(fieldName, file)
    return service.post(url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // 上传超时设长一点
    })
  },
}
```

业务代码使用：

```typescript
// 简洁的 API 调用
const users = await http.get('/api/users', { page: 1, page_size: 20 })
const result = await http.post('/api/users', { name: '张三', role_id: 1 })
const uploaded = await http.upload('/api/upload', file)
```

## Token 双令牌机制

为什么需要 access_token 和 refresh_token 两个令牌？

```
access_token：
  - 有效期短（通常 2 小时）
  - 每次请求都携带
  - 泄露风险高，所以有效期短

refresh_token：
  - 有效期长（通常 14 天）
  - 只在刷新时使用
  - 存储在 HttpOnly Cookie 中更安全
```

这是一个安全性和用户体验的平衡：
- 如果只有一个长期 Token → 泄露后风险大
- 如果只有一个短期 Token → 用户频繁被踢出登录
- 双令牌机制 → access_token 泄露影响有限，refresh_token 不频繁传输更安全

### 后端签发逻辑

```php
public function login($request): array
{
    // ... 验证用户名密码 ...

    $accessToken = JwtService::generate($user->id, 7200);      // 2小时
    $refreshToken = JwtService::generate($user->id, 1209600);   // 14天

    return [
        [
            'access_token' => $accessToken,
            'refresh_token' => $refreshToken,
            'expires_in' => 7200,
        ],
        0,
        'ok',
    ];
}

public function refresh($request): array
{
    $refreshToken = $request->post('refresh_token');
    $payload = JwtService::verify($refreshToken);

    if (!$payload) {
        return [null, 401, 'refresh_token 已过期'];
    }

    // 签发新的令牌对
    $newAccess = JwtService::generate($payload->uid, 7200);
    $newRefresh = JwtService::generate($payload->uid, 1209600);

    return [
        [
            'access_token' => $newAccess,
            'refresh_token' => $newRefresh,
            'expires_in' => 7200,
        ],
        0,
        'ok',
    ];
}
```

## 时序图

完整的 Token 刷新时序：

```
浏览器                    服务器
  │                        │
  │── 请求 A (token过期) ──→│
  │←── 401 Unauthorized ───│
  │                        │
  │── refresh_token ──────→│
  │                        │ 验证 refresh_token
  │                        │ 签发新 access_token
  │←── 新 token ───────────│
  │                        │
  │── 重试请求 A (新token) →│
  │←── 正常响应 ───────────│
  │                        │
  │── 请求 B (队列中等待) ─→│  ← 刷新完成后自动重试
  │←── 正常响应 ───────────│
  │                        │
  │── 请求 C (队列中等待) ─→│  ← 刷新完成后自动重试
  │←── 正常响应 ───────────│
```

## 总结

Token 无感刷新看起来简单，但要处理好并发、防抖、循环检测这些边界情况，才能做到真正的"无感"。核心要点：

| 问题 | 解决方案 |
|------|---------|
| 多请求同时 401 | 请求队列 + 只刷新一次 |
| 刷新接口本身 401 | `_retry` 标记防无限循环 |
| 重复弹框 | 防抖机制（2秒去重） |
| refresh_token 过期 | 跳登录页，无法挽救 |
| 安全性 | 双令牌机制，短期 + 长期 |

---
title: 📋 智澜管理系统 · 白皮书
published: 2026-01-14T23:59:59Z
description: 智澜管理系统技术架构、功能模块、开发规范的完整说明
tags: [智澜, 白皮书, 全栈]
category: 智澜管理系统
draft: false
---

# 智澜管理系统 · 白皮书

> 基于 Webman + Vue3 + TypeScript 的企业级后台管理系统

**在线演示**: [zgm2003.cn](https://zgm2003.cn) | **Gitee**: [zgm2003](https://gitee.com/zgm2003)

---

## 一、项目定位

面向中小企业的**全栈后台管理系统**，提供开箱即用的基础功能和可扩展的业务框架。

**核心价值**：
- 🚀 高性能：Webman 常驻内存 + Redis 缓存
- 🔐 安全可控：Opaque Token + 单端登录 + 权限精细化
- 🤖 AI 就绪：内置多智能体对话模块
- 📦 开发友好：CMVD 分层 + Composables 架构

---

## 二、技术架构

### 后端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | Webman | 基于 Workerman 的高性能 PHP 框架 |
| 数据库 | MySQL 8.0 | 主数据存储 |
| 缓存 | Redis | Token 缓存、权限缓存、队列 |
| 队列 | webman/redis-queue | 异步任务处理 |
| ORM | Laravel Eloquent | 数据库操作 |

### 前端技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 框架 | Vue 3.4 | Composition API |
| 语言 | TypeScript | 类型安全 |
| UI | Element Plus | 组件库 |
| 构建 | Vite 5 | 开发/打包 |
| 状态 | Pinia | 状态管理 |
| 路由 | Vue Router 4 | 动态路由 |

### 分层架构（CMVD）

```
请求 → Controller → Module → Validate → Dep → Model → 数据库
         ↓            ↓          ↓         ↓
       路由分发    业务逻辑    参数校验   数据访问
```

**各层职责**：
- **Controller**：接收请求，调用 Module，返回响应
- **Module**：业务逻辑，事务控制，异常处理
- **Validate**：参数校验规则
- **Dep**：数据访问层，封装 Model 操作

---

## 三、功能模块

### 用户认证

| 功能 | 说明 |
|------|------|
| 多方式登录 | 密码、邮箱验证码、手机验证码 |
| Opaque Token | 随机令牌 + SHA256 哈希，可随时吊销 |
| 双令牌机制 | access_token (4h) + refresh_token (14d) |
| 无感刷新 | 前端拦截 401，自动刷新重试 |
| 单端登录 | 同平台互踢，支持多平台策略 |
| 自动注册 | 验证码登录自动创建账号 |

### 权限管理

| 功能 | 说明 |
|------|------|
| RBAC 模型 | 用户 → 角色 → 权限 |
| 三级权限 | 目录、页面、按钮 |
| 动态路由 | 根据权限生成前端路由 |
| 按钮控制 | v-permission 指令 |
| 权限缓存 | Redis 缓存，变更时清除 |

### AI 对话

| 功能 | 说明 |
|------|------|
| 多智能体 | 每个智能体可配置不同模型 |
| SSE 流式 | 实时输出，体验流畅 |
| 会话管理 | 创建、重命名、删除、归档 |
| 异步标题 | Redis 队列生成会话标题 |
| 停止生成 | 中断输出，保存已生成内容 |
| 多模态 | 支持图片附件 |

### 文件上传

| 功能 | 说明 |
|------|------|
| 多云存储 | 腾讯云 COS、阿里云 OSS |
| 临时凭证 | STS Token，前端直传 |
| 规则配置 | 文件类型、大小限制 |
| 目录隔离 | 白名单目录，防穿越 |

### 系统管理

| 功能 | 说明 |
|------|------|
| 用户管理 | 增删改查、状态控制 |
| 角色管理 | 权限分配、默认角色 |
| 操作日志 | 接口调用记录 |
| 登录日志 | 登录尝试记录 |
| 系统设置 | 配置项管理 |

---

## 四、目录结构

### 后端

```
admin_back/
├── app/
│   ├── controller/     # 控制器
│   ├── module/         # 业务模块
│   │   ├── Ai/         # AI 对话
│   │   ├── User/       # 用户认证
│   │   └── System/     # 系统管理
│   ├── dep/            # 数据访问层
│   ├── model/          # 数据模型
│   ├── validate/       # 参数校验
│   ├── service/        # 服务层
│   ├── enum/           # 枚举常量
│   ├── exception/      # 异常类
│   ├── middleware/     # 中间件
│   └── queue/redis/    # 异步队列
│       ├── fast/       # 快速任务
│       └── slow/       # 慢任务
├── config/             # 配置文件
├── routes/             # 路由定义
└── runtime/            # 运行时文件
```

### 前端

```
admin_front_ts/
├── src/
│   ├── views/
│   │   ├── Login/      # 登录页
│   │   ├── Layout/     # 布局框架
│   │   └── Main/       # 业务页面
│   │       ├── ai/     # AI 对话
│   │       ├── user/   # 用户管理
│   │       ├── system/ # 系统管理
│   │       └── home/   # 首页
│   ├── hooks/          # 通用 Hooks
│   ├── api/            # 接口定义
│   ├── stores/         # Pinia 状态
│   ├── router/         # 路由配置
│   └── utils/          # 工具函数
├── public/             # 静态资源
└── dist/               # 构建产物
```

---

## 五、开发规范

### 后端规范

**Module 层**：
```php
class XxxModule extends BaseModule
{
    public function action($request): array
    {
        // 1. 参数校验
        $param = $this->validate($request, XxxValidate::action());
        
        // 2. 业务逻辑
        // ...
        
        // 3. 返回结果
        return self::success($data);
    }
}
```

**异常处理**：
```php
// 业务异常（返回给前端）
self::throw('操作失败');
self::throwIf($condition, '条件不满足');
self::throwNotFound('资源不存在');

// 事务控制
$this->withTransaction(function () {
    // 多表操作
});
```

### 前端规范

**Composables 模式**：
```typescript
// 按功能拆分 composables
export function useXxx() {
  const loading = ref(false)
  const data = ref([])
  
  const fetch = async () => { /* ... */ }
  
  return { loading, data, fetch }
}
```

**useTable Hook**：
```typescript
const { tableData, pagination, loading, fetchData } = useTable({
  api: XxxApi.list,
  immediate: true,
})
```

---

## 六、部署说明

### 后端

```bash
# 安装依赖
composer install --no-dev

# 启动服务
php start.php start -d
```

### 前端

```bash
# 安装依赖
pnpm install

# 构建
pnpm build

# 产物在 dist/ 目录，部署到 Nginx
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name admin.example.com;
    
    # 前端
    location / {
        root /var/www/admin/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端 API
    location /api/ {
        proxy_pass http://127.0.0.1:8787/api/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # SSE 流式
    location /api/admin/AiChat/stream {
        proxy_pass http://127.0.0.1:8787;
        proxy_buffering off;
        proxy_cache off;
    }
}
```

---

## 七、文档导航

| 分类 | 文档 |
|------|------|
| **架构设计** | [CMVD 分层架构](/posts/webman-layered-architecture/) · [useTable Hook](/posts/vue3-usetable-hook/) · [N+1 查询优化](/posts/n-plus-one-query/) |
| **AI 对话** | [模块概览](/posts/ai-chat-development-log/) · [SSE 流式输出](/posts/sse-streaming-chat/) · [Redis 异步队列](/posts/redis-queue-async-task/) |
| **用户认证** | [认证模块](/posts/auth-module/) · [Token 无感刷新](/posts/axios-token-refresh/) · [权限管理](/posts/permission-module/) |
| **系统管理** | [文件上传](/posts/upload-module/) |

---

## 八、联系方式

- **QQ**: 2093146753
- **微信**: zgm2093146753
- **Gitee**: [zgm2003](https://gitee.com/zgm2003)

---

*最后更新：2026-01-14*

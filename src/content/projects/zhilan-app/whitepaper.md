---
title: 项目白皮书
published: 2026-01-28T10:00:00Z
description: 智澜APP 项目概述、技术架构、功能规划
tags: [概述, Capacitor, Vant]
project: 智澜APP
order: 1
draft: false
---

# 项目概述

**智澜APP** 是智澜产品体系的移动端应用，基于 Vue3 + Vant4 + Capacitor 构建，支持 H5、Android、iOS 多端运行。

## 项目定位

| 项目 | 定位 | 技术栈 |
|------|------|--------|
| 智澜管理系统 | PC 后台管理 | Vue3 + Element Plus + Tauri |
| **智澜APP** | 移动端应用 | Vue3 + Vant4 + Capacitor |
| 智澜后端 | 统一 API 服务 | Webman + MySQL + Redis |

## 线上地址

- **H5**: [h5.zgm2003.cn](https://h5.zgm2003.cn)
- **Android**: 开发中，尚未上架
- **iOS**: 开发中，尚未上架

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                     智澜APP 前端                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Vue 3     │  │   Vant 4    │  │  Capacitor  │     │
│  │   组合式API  │  │   移动UI    │  │   原生桥接   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Vite 7    │  │   Pinia     │  │ Vue Router  │     │
│  │   构建工具   │  │   状态管理   │  │   路由管理   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     智澜后端 API                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  app.php    │  │ CheckToken  │  │CheckPermission│   │
│  │  独立路由    │  │  Token校验   │  │   权限校验    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## 核心技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.5+ | 前端框架 |
| Vite | 7.x | 构建工具 |
| Vant | 4.x | 移动端 UI 组件库 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| Capacitor | 6.x | 原生能力桥接 |
| TypeScript | 5.x | 类型安全 |
| UnoCSS | - | 原子化 CSS |

---

## 功能模块

### 已实现

- [x] 用户登录/注册
- [x] Token 自动刷新
- [x] 按钮权限控制
- [x] 深色模式
- [x] 国际化 (i18n)
- [x] 路由白名单
- [x] vConsole 调试

### 规划中

- [ ] 消息推送
- [ ] 文件上传
- [ ] 扫码功能
- [ ] 生物识别

---

## 与 PC 后台的差异

| 维度 | PC 后台 | 智澜APP |
|------|--------|---------|
| 权限模型 | 目录→页面→按钮 | 仅按钮权限 |
| 路由 | 动态生成 | 固定路由 + 白名单 |
| API 路由 | /api/admin | /api/app |
| UI 组件 | Element Plus | Vant 4 |
| 打包产物 | Web + Tauri | H5 + Android + iOS |

---

## 目录结构

```
admin_front_h5/
├── src/
│   ├── api/              # API 接口
│   ├── components/       # 公共组件
│   ├── composables/      # 组合式函数
│   ├── config/           # 配置文件
│   ├── constants/        # 常量定义
│   ├── directives/       # 自定义指令 (v-permission)
│   ├── locales/          # 国际化
│   ├── pages/            # 页面组件
│   ├── router/           # 路由配置
│   ├── stores/           # Pinia 状态
│   ├── styles/           # 全局样式
│   ├── types/            # TypeScript 类型
│   └── utils/            # 工具函数
├── android/              # Android 原生项目
├── ios/                  # iOS 原生项目
└── capacitor.config.ts   # Capacitor 配置
```

---

## 开发命令

```bash
# 安装依赖
pnpm install

# H5 开发
pnpm dev

# Android 开发
pnpm build
npx cap sync android
npx cap open android

# iOS 开发
pnpm build
npx cap sync ios
npx cap open ios
```

---

## 相关文档

- [按钮权限系统](/projects/zhilan-app/button-permission) - 扁平化权限架构
- [路由设计](/projects/zhilan-app/router-design) - 白名单 + 登录拦截

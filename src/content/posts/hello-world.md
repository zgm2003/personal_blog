---
title: 项目简介
published: 2026-01-13T00:00:00Z
description: 智澜管理系统 - 基于 Webman + Vue3 的全栈后台管理系统
tags: [项目, 简介]
category: 概览
draft: false
---

# 智澜管理系统

基于 **Webman + Vue3 + TypeScript** 的企业级后台管理系统。

## 技术栈

**后端**
- Webman（高性能 PHP 框架）
- MySQL + Redis
- CMVD 分层架构（Controller → Module → Validate → Dep）

**前端**
- Vue3 + TypeScript + Composition API
- Element Plus
- Vite

## 核心模块

| 模块 | 功能 |
|------|------|
| 🤖 **AI 对话** | 多智能体、流式输出、会话管理、异步标题生成 |
| 👤 **用户认证** | Opaque Token 双令牌、无感刷新、多端登录控制、验证码登录 |
| 🔐 **权限管理** | RBAC 模型、菜单/页面/按钮三级权限、动态路由 |
| 📁 **文件上传** | 多驱动（COS/OSS）、临时凭证、前端直传 |
| ⚙️ **系统设置** | 配置管理、操作日志、登录日志 |

## 项目地址

- **在线演示**: [148.70.40.203:88](http://148.70.40.203:88)
- **Gitee**: [zgm2003](https://gitee.com/zgm2003)

## 文档导航

按模块查看文档，每个模块包含前后端完整实现：

- **架构设计** - CMVD 分层、BaseModule、useTable Hook
- **AI对话** - SSE 流式、Redis 异步、模块概览
- **用户认证** - Token 机制、权限管理
- **系统管理** - 文件上传、系统设置

## 联系方式

- QQ: 2093146753
- 微信: zgm2093146753
- Gitee: [zgm2003](https://gitee.com/zgm2003)

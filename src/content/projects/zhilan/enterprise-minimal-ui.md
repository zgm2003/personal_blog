---
title: 企业简约风 UI 重构实践
published: 2026-01-14T16:00:00Z
description: 基于 Vue3 + Element Plus 的后台管理系统 UI 重构，实现动态主题色、响应式布局、组件化设计
tags: [Vue3, Element Plus, UI设计, 响应式]
project: 智澜管理系统
order: 90
draft: false
---

# 设计理念

企业级后台系统的 UI 设计核心原则：**简洁、专业、高效**。

本次重构基于 Swiss Modernism（瑞士现代主义）风格，特点是：
- 干净的线条和留白
- 高对比度的文字层级
- 扁平化的视觉元素
- 一致的间距系统

## 配色系统

### CSS 变量架构

采用 CSS 变量实现动态主题，所有颜色都引用 Element Plus 的主题变量：

```css
:root {
  /* 使用 Element Plus 主题色 */
  --primary: var(--el-color-primary);
  
  /* 中性色 */
  --bg-page: #F8FAFC;
  --bg-card: #FFFFFF;
  --bg-hover: #F1F5F9;
  
  /* 文字层级 */
  --text-primary: #1E293B;
  --text-secondary: #64748B;
  --text-muted: #94A3B8;
  
  /* 边框 */
  --border: #E2E8F0;
}

/* 暗色模式 */
html.dark {
  --bg-page: #0F172A;
  --bg-card: #1E293B;
  --text-primary: #F1F5F9;
  /* ... */
}
```

### 动态主题色

关键点：**不要硬编码颜色值**，使用 `var(--el-color-primary)` 系列变量：

```scss
// ❌ 错误：硬编码颜色
.active {
  color: #409EFF;
  background: rgba(64, 158, 255, 0.1);
}

// ✅ 正确：使用 CSS 变量
.active {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}
```

这样用户在设置中切换主题色时，所有组件都会自动更新。

## 布局结构

### 整体架构

```
┌─────────────────────────────────────────┐
│  Aside (侧边栏)  │     Header (头部)     │
│                  ├──────────────────────┤
│  - Logo          │     TabTag (标签页)   │
│  - Menu          ├──────────────────────┤
│  - 折叠按钮       │                      │
│                  │     Main (内容区)     │
│                  │                      │
│                  ├──────────────────────┤
│                  │     Footer (页脚)     │
└─────────────────────────────────────────┘
```

### 侧边栏折叠按钮

将折叠按钮从 Header 移到侧边栏底部，更符合直觉：

```vue
<template>
  <div class="aside-wrapper">
    <el-menu>
      <!-- 菜单内容 -->
    </el-menu>
    
    <!-- 底部折叠按钮 -->
    <div class="collapse-btn" @click="toggleCollapse">
      <el-icon>
        <component :is="collapsed ? 'DArrowRight' : 'DArrowLeft'" />
      </el-icon>
      <span v-show="!collapsed">收起菜单</span>
    </div>
  </div>
</template>
```

### 折叠状态下的菜单居中

Element Plus 菜单折叠后图标默认不居中，需要覆盖样式：

```scss
:deep(.el-menu--collapse) {
  width: 64px;
  
  .el-menu-item {
    margin: 4px auto !important;  // 关键：auto 实现水平居中
    padding: 0 !important;
    width: 48px !important;
    display: flex !important;
    justify-content: center !important;
    
    .el-icon {
      margin: 0 !important;
    }
  }
}
```

## 登录页设计

采用左右分栏布局：

```
┌──────────────┬─────────────────────┐
│              │                     │
│   品牌区域    │     登录表单        │
│   (主题色)    │     (白色背景)      │
│              │                     │
│   Logo       │     账号输入        │
│   标题       │     密码/验证码      │
│   描述       │     登录按钮        │
│              │                     │
└──────────────┴─────────────────────┘
```

移动端隐藏左侧品牌区，表单全屏显示：

```scss
@media (max-width: 992px) {
  .login-brand {
    display: none;
  }
}
```

## 组件封装

### SendCode 组件 size 属性

验证码组件需要支持不同尺寸，通过 prop 传递给内部的 Element Plus 组件：

```vue
<script setup lang="ts">
const props = withDefaults(defineProps<{
  size?: 'large' | 'default' | 'small'
}>(), {
  size: 'default'
})
</script>

<template>
  <div class="send-code-wrapper">
    <el-input :size="size" />
    <el-button :size="size">获取验证码</el-button>
  </div>
</template>
```

使用时：

```vue
<SendCode size="large" />
```

## 响应式设计

### Hook vs CSS 媒体查询

项目中两种方式配合使用：

```ts
// hooks/useResponsive.ts
export function useIsMobile() {
  return useMediaQuery('(max-width: 768px)')
}
```

- **JS Hook**：控制逻辑（是否显示某个元素、弹窗是否全屏）
- **CSS 媒体查询**：控制样式（间距、字号、布局方向）

```vue
<script setup>
const isMobile = useIsMobile()
</script>

<template>
  <!-- JS 控制逻辑 -->
  <el-dialog :fullscreen="isMobile">
    <!-- CSS 控制样式 -->
    <div class="content">...</div>
  </el-dialog>
</template>

<style>
/* CSS 控制样式细节 */
@media (max-width: 768px) {
  .content {
    padding: 12px;
  }
}
</style>
```

## 最佳实践总结

1. **颜色使用 CSS 变量**：支持动态主题切换
2. **间距保持一致**：使用 4px 的倍数（8、12、16、20、24）
3. **过渡动画统一**：150-200ms ease
4. **组件 props 透传**：size、disabled 等属性传递给内部组件
5. **响应式断点统一**：768px（移动端）、992px（平板）、1200px（桌面）

## 文件清单

本次重构涉及的文件：

| 文件 | 说明 |
|------|------|
| `style.css` | 全局样式、CSS 变量、Element Plus 覆盖 |
| `Layout/index.vue` | 主布局容器 |
| `Aside/index.vue` | 侧边栏 + 折叠按钮 |
| `Header/index.vue` | 头部工具栏 |
| `TabTag/index.vue` | 标签页导航 |
| `Login/index.vue` | 登录页 |
| `home/index.vue` | 首页 |
| `SettingDrawer.vue` | 设置抽屉 |
| `SearchDialog.vue` | 搜索弹窗 |
| `SendCode.vue` | 验证码组件 |

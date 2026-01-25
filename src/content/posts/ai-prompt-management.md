---
title: AI 提示词管理模块
published: 2026-01-25T16:00:00Z
description: 构建个人提示词库，提升 AI 对话效率的 CRUD 实践
tags: [AI, CRUD, 全栈]
category: 智澜管理系统
draft: false
---

# 为什么需要提示词管理？

在日常使用 AI 对话时，我们经常会重复输入类似的指令：
- "请帮我审查这段代码..."
- "翻译成英文，保持专业语气..."
- "用表格形式总结..."

每次手敲不仅浪费时间，还容易遗漏关键要求。于是我开发了一个提示词管理模块，让常用指令一键复用。

---

## 功能设计

### 核心需求
- **CRUD**：提示词的增删改查
- **一键使用**：点击即复制到剪贴板
- **收藏置顶**：常用提示词优先展示
- **分类标签**：按场景组织提示词

### 数据模型

```sql
CREATE TABLE ai_prompt (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,           -- 用户隔离
    title VARCHAR(100) NOT NULL,    -- 提示词名称
    content TEXT NOT NULL,          -- 提示词内容
    category VARCHAR(50),           -- 分类：开发/写作/翻译
    tags JSON,                      -- 标签：["code", "review"]
    is_favorite TINYINT DEFAULT 2,  -- 收藏：1=是 2=否
    use_count INT DEFAULT 0,        -- 使用次数
    is_del TINYINT DEFAULT 2,       -- 软删除
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## 技术实现

### 后端架构（PHP/Webman）

```
Controller → Module → Dep → Model
    ↓           ↓       ↓
 注解校验    业务逻辑  数据访问
```

**关键设计：**

1. **权限与日志双校验**
```php
/** @OperationLog("提示词删除") @Permission("ai_prompt_del") */
public function del(Request $request) { ... }
```

2. **JSON 字段处理**
```php
// 存储时
$param['tags'] = json_encode($param['tags']);

// 返回时
'tags' => $row->tags ? json_decode($row->tags, true) : []
```

3. **智能排序**
```php
->orderByDesc('is_favorite')  // 收藏优先
->orderByDesc('use_count')    // 高频次之
->orderByDesc('id')           // 最新兜底
```

### 前端实现（Vue3 + Element Plus）

**卡片式布局**，直观展示提示词内容：

```vue
<div class="grid">
  <ElCard v-for="item in list" :key="item.id" shadow="hover">
    <div class="card-header">
      <ElText tag="b">{{ item.title }}</ElText>
      <ElButton :icon="StarFilled" @click="toggleFavorite(item)" />
    </div>
    <ElText type="info" line-clamp="3">{{ item.content }}</ElText>
    <div class="card-footer">
      <ElButton type="primary" @click="handleUse(item)">使用</ElButton>
    </div>
  </ElCard>
</div>
```

**标签输入**使用 `ElInputTag` 组件：
```vue
<ElInputTag v-model="form.tags" tag-type="primary" />
```
产出格式：`['tag1', 'tag2', 'tag3']`

**响应式适配**：
```javascript
const isMobile = useIsMobile()
```
```vue
<ElDialog :width="isMobile ? '94vw' : '600px'">
```

---

## 交互细节

### 一键使用
```javascript
const handleUse = async (item) => {
  await AiPromptApi.use({ id: item.id })  // 记录使用次数
  copy(item.content)                       // 复制到剪贴板
  item.use_count++                         // 本地 +1
}
```

### 前端权限控制
```vue
<ElButton v-if="userStore.can('ai_prompt_add')" @click="openAdd">新增</ElButton>
<ElButton v-if="userStore.can('ai_prompt_edit')" @click="openEdit(item)">编辑</ElButton>
<ElButton v-if="userStore.can('ai_prompt_del')" @click="handleDel(item)">删除</ElButton>
```

### 删除二次确认
```javascript
await ElMessageBox.confirm(
  t('common.confirmDelete'),
  t('common.confirmTitle'),
  { type: 'warning', confirmButtonText: t('common.actions.del') }
)
```

---

## 示例提示词

| 名称 | 内容 | 分类 |
|------|------|------|
| 代码审查助手 | 请审查以下代码：1. 代码质量 2. 潜在问题 3. 性能优化 4. 最佳实践 | 开发 |
| 专业翻译 | 翻译成英文，保持专业、简洁的语气，术语准确 | 翻译 |
| 文章润色 | 润色这段文字，使其更加流畅、专业，保留原意 | 写作 |

---

## 开发心得

1. **JSON 字段的取舍**：标签用 JSON 数组存储，查询灵活但无法建索引，适合低频过滤场景

2. **使用次数统计**：记录用户行为，为后续推荐、热门排序提供数据支撑

3. **收藏 + 使用次数双排序**：用户主动标记 + 被动行为结合，排序更智能

4. **卡片 vs 表格**：提示词内容较长，卡片布局比表格更适合预览

---

## 后续计划

- [ ] 提示词模板变量：支持 `{{变量}}` 占位符
- [ ] 快捷键调用：在对话页面 `/` 唤起提示词选择器
- [ ] 提示词分享：公开优质提示词供团队使用
- [ ] AI 优化建议：分析提示词质量并给出改进建议

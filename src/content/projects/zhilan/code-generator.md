---
title: 🔧 代码生成器 · 一键生成 CRUD 全链路代码
published: 2026-01-21T10:00:00Z
description: 基于数据库表结构自动生成后端 Controller/Module/Dep/Model/Validate + 前端 API/Vue 页面
tags: [代码生成, CRUD, 开发效率]
project: 智澜管理系统
order: 80
draft: false
---

# 代码生成器 · 一键生成 CRUD 全链路代码

> 从数据库表结构到完整 CRUD 功能，一键搞定

---

## 一、功能概述

代码生成器根据数据库表结构，自动生成 **前后端全链路代码**：

| 层级 | 生成文件 | 说明 |
|------|---------|------|
| Controller | `XxxController.php` | 路由分发、权限注解 |
| Module | `XxxModule.php` | 业务逻辑、参数校验 |
| Dep | `XxxDep.php` | 数据访问、查询构建 |
| Model | `XxxModel.php` | 数据模型 |
| Validate | `XxxValidate.php` | Respect\Validation 规则 |
| API | `xxx.ts` | 前端接口定义 |
| Vue | `index.vue` | 完整的列表 + 表单页面 |

---

## 二、使用方式

### 配置参数

```php
$config = [
    'module_name' => 'Article',      // 模块名（大驼峰）
    'table_name' => 'article',       // 数据库表名
    'menu_name' => '文章管理',        // 菜单名称
    'domain' => 'System',            // 所属领域
    'columns' => [                   // 字段配置（从数据库读取）
        [
            'column_name' => 'title',
            'column_comment' => '标题',
            'data_type' => 'varchar',
            'max_length' => 255,
            'is_nullable' => 'NO',
            'form_type' => 'input',      // 表单类型
            'show_in_list' => true,      // 列表显示
            'show_in_search' => true,    // 搜索条件
            'show_in_form' => true,      // 表单显示
        ],
        // ...
    ]
];
```

### 生成代码

```php
$generator = new CodeGenerator($config);

// 预览
$files = $generator->preview();

// 生成文件
$result = $generator->generate();
// ['created' => [...], 'skipped' => [...]]
```

---

## 三、智能特性

### 表单类型映射

根据 `form_type` 自动生成对应组件：

| form_type | 前端组件 | 说明 |
|-----------|---------|------|
| `input` | `<el-input>` | 普通输入框 |
| `password` | `<el-input type="password">` | 密码框 |
| `textarea` | `<el-input type="textarea">` | 多行文本 |
| `editor` | `<Editor>` | 富文本编辑器 |
| `number` | `<el-input-number>` | 数字输入 |
| `select` | `<el-select-v2>` | 下拉选择 |
| `date` | `<el-date-picker type="date">` | 日期选择 |
| `datetime` | `<el-date-picker type="datetime">` | 日期时间 |
| `image` | `<UpMedia>` | 图片上传（folder-name 自动加 s） |

### 验证规则生成

根据数据类型自动生成 Respect\Validation 规则：

```php
// varchar(255) 必填
'title' => v::stringType()->length(1, 255)->setName('标题'),

// int 可选
'sort' => v::optional(v::intVal()->positive())->setName('排序'),

// email 字段
'email' => v::email()->setName('邮箱'),

// 手机号字段
'phone' => v::regex('/^1[3-9]\d{9}$/')->setName('手机号'),
```

### 搜索条件生成

自动构建 Dep 层查询链：

```php
return $this->model
    ->when(!empty(trim($param['title'] ?? '')), 
        fn($q) => $q->where('title', 'like', trim($param['title']) . '%'))
    ->when(isset($param['status']) && $param['status'] !== '', 
        fn($q) => $q->where('status', $param['status']))
    ->where('is_del', CommonEnum::NO)
    ->orderBy('id', 'desc')
    ->paginate($param['page_size'], ['*'], 'page', $param['current_page']);
```

**注意**：字符串搜索使用左匹配 `LIKE 'xxx%'`，可利用索引；数字类型使用 `isset` 判断（因为 0 是有效值）。

---

## 四、生成的前端代码

### 组件导入规范

自动检测需要的组件并生成正确的导入语句：

```typescript
// 命名导入（项目规范）
import { Editor } from '@/components/Editor'
import { UpMedia } from '@/components/UpMedia'
import { AppTable } from '@/components/Table'
import { Search } from '@/components/Search'
```

### useTable Hook 集成

生成的页面自动使用 `useTable` Hook：

```typescript
const {
  loading: listLoading,
  data: listData,
  page,
  selectedIds,
  onSearch,
  onPageChange,
  refresh,
  getList,
  onSelectionChange,
  confirmDel,
  batchDel
} = useTable({
  api: ArticleApi,
  searchForm
})
```

### 移动端适配

表单自动响应式布局：

```vue
<!-- 普通字段：PC 端两列，移动端单列 -->
<el-col :md="12" :span="24">

<!-- 大文本字段：始终单列 -->
<el-col :span="24">
```

---

## 五、权限注解

Controller 自动添加权限和日志注解：

```php
/** @OperationLog("文章新增") @Permission("system_article_add") */
public function add(Request $request) { ... }

/** @OperationLog("文章编辑") @Permission("system_article_edit") */
public function edit(Request $request) { ... }

/** @OperationLog("文章删除") @Permission("system_article_del") */
public function del(Request $request) { ... }
```

---

## 六、最佳实践

### 1. 先设计表结构

```sql
CREATE TABLE `article` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL COMMENT '标题',
  `content` text COMMENT '内容',
  `cover` varchar(500) DEFAULT '' COMMENT '封面图',
  `status` tinyint DEFAULT 1 COMMENT '状态:1启用,2禁用',
  `is_del` tinyint DEFAULT 1 COMMENT '是否删除:1否,2是',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. 生成后的调整

生成的代码是**起点而非终点**，根据业务需求调整：

- **Module**：添加业务逻辑（关联查询、事务处理）
- **Dep**：优化查询（预加载、索引）
- **Vue**：定制 UI（特殊列渲染、自定义操作）

### 3. 路由手动添加

生成器会输出路由配置，需手动添加到 `routes/admin.php`：

```php
// Article - 文章管理
Route::post('/System/Article/init', [ArticleController::class, 'init']);
Route::post('/System/Article/list', [ArticleController::class, 'list']);
Route::post('/System/Article/add', [ArticleController::class, 'add']);
Route::post('/System/Article/edit', [ArticleController::class, 'edit']);
Route::post('/System/Article/del', [ArticleController::class, 'del']);
```

---

## 七、效率提升

| 场景 | 手写耗时 | 生成器 |
|------|---------|-------|
| 简单 CRUD | 2-3 小时 | **30 秒** |
| 带搜索表单 | 3-4 小时 | **30 秒** |
| 完整功能页 | 4-6 小时 | **30 秒** + 调整 |

**核心价值**：消除重复劳动，专注业务逻辑。

---

*最后更新：2026-01-25*


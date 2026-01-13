---
title: Vue3 useTable Hook：告别重复的 CRUD 代码
published: 2026-01-13T11:00:00Z
description: 封装一个 useTable Hook，让列表页开发效率翻倍
tags: [Vue3, TypeScript, 前端, Hooks]
category: 技术
draft: false
---

# 痛点

每个后台管理系统都有大量列表页，每个列表页都要写：

- loading 状态
- 分页逻辑
- 搜索重置
- 删除确认
- 状态切换

复制粘贴？容易出错。每次都写？累死人。

## useTable 来了

```typescript
const {
  loading,
  data,
  page,
  getList,
  onSearch,
  onPageChange,
  confirmDel,
  batchDel,
  toggleStatus
} = useTable({
  api: NoticeApi,
  searchForm
})
```

一行代码，搞定所有重复逻辑。

## 核心实现

```typescript
export function useTable<T>(options: UseTableOptions<T>) {
  const { api, searchForm, immediate = false } = options

  const loading = ref(false)
  const data = ref<T[]>([])
  const page = ref<PageState>({
    current_page: 1,
    page_size: 20,
    total: 0
  })

  // 获取列表
  const getList = () => {
    loading.value = true
    return api.list({
      ...unref(searchForm),
      ...page.value
    })
    .then(res => {
      data.value = res.list
      page.value = res.page
    })
    .finally(() => {
      loading.value = false
    })
  }

  // 搜索（重置页码）
  const onSearch = () => {
    page.value.current_page = 1
    getList()
  }

  // 单个删除（带确认弹窗）
  const confirmDel = async (row: any) => {
    await ElMessageBox.confirm('确认删除？', '提示')
    await api.del({ id: row.id })
    ElNotification.success({ message: '操作成功' })
    getList()
  }

  return { loading, data, page, getList, onSearch, confirmDel, ... }
}
```

## 使用示例

```vue
<script setup lang="ts">
import { useTable } from '@/hooks/useTable'
import { NoticeApi } from '@/api/system/notice'

const searchForm = ref({ title: '' })

const { loading, data, page, getList, onSearch, confirmDel } = useTable({
  api: NoticeApi,
  searchForm
})

onMounted(() => getList())
</script>

<template>
  <Search v-model="searchForm" @query="onSearch" />
  <AppTable 
    :data="data" 
    :loading="loading"
    :pagination="page"
    @update:pagination="onPageChange"
  >
    <template #cell-actions="{ row }">
      <el-button @click="confirmDel(row)">删除</el-button>
    </template>
  </AppTable>
</template>
```

## API 模块约定

useTable 要求 API 模块遵循标准结构：

```typescript
export const NoticeApi = {
  list: (params) => request.post('/Notice/list', params),
  del: (params) => request.post('/Notice/del', params),
  status: (params) => request.post('/Notice/status', params)
}
```

返回格式：

```json
{
  "list": [...],
  "page": {
    "current_page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

## 扩展能力

- `dataCallback`：数据后处理
- `afterDel`：删除后回调
- `immediate`：是否立即请求

```typescript
useTable({
  api: NoticeApi,
  searchForm,
  immediate: true,  // 组件挂载立即请求
  dataCallback: (res) => {
    // 处理数据
    res.list = res.list.map(item => ({
      ...item,
      statusText: item.status === 1 ? '启用' : '禁用'
    }))
    return res
  }
})
```

## 总结

useTable 把列表页的通用逻辑抽象出来，让你专注于业务差异部分。配合 Search 和 AppTable 组件，一个标准列表页 100 行代码搞定。

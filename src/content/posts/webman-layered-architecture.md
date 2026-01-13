---
title: Webman 分层架构实践：从 MVC 到 CMVD
published: 2026-01-13T10:00:00Z
description: 基于 Webman 高性能框架的分层架构设计，告别 Controller 写业务逻辑的混乱
tags: [PHP, Webman, 架构设计, 后端]
category: 技术
draft: false
---

# 为什么要分层？

刚开始写 PHP 的时候，我也是把所有逻辑都塞在 Controller 里。一个 `UserController` 动辄上千行，改个需求要翻半天。

后来接触了 Java 的分层思想，发现 PHP 也可以这么玩。今天分享一下我在 Webman 项目中的分层实践。

## 架构分层

```
Route → Middleware → Controller → Module → Dep → Model
```

| 层级 | 职责 | 严禁 |
|------|------|------|
| Controller | 路由接入，转发请求 | 写业务逻辑 |
| Module | 业务编排，参数校验 | 直接写 SQL |
| Dep | 数据访问，封装 CRUD | 写复杂业务 |
| Model | 映射表结构 | 写逻辑方法 |

## Controller：只做转发

```php
class NoticeController extends Controller
{
    public function list(Request $request)
    {
        // 一行代码，转发给 Module
        $this->run([NoticeModule::class, 'list'], $request);
        return $this->response();
    }
}
```

Controller 就像前台接待，只负责把客人带到对应的部门，不处理具体业务。

## Module：业务核心

```php
class NoticeModule extends BaseModule
{
    public function list($request): array
    {
        // 1. 参数校验
        $param = $this->validate($request, NoticeValidate::list());
        
        // 2. 调用 Dep 获取数据
        $res = $this->noticeDep->list($param);
        
        // 3. 返回标准格式
        return self::paginate($res->items(), [
            'current_page' => $res->currentPage(),
            'page_size' => $res->perPage(),
            'total' => $res->total(),
        ]);
    }
}
```

Module 是业务逻辑的主战场，负责：
- 参数校验
- 业务编排
- 调用多个 Dep 组合数据
- 事务控制

## Dep：数据访问层

```php
class NoticeDep extends BaseDep
{
    protected function createModel(): Model
    {
        return new NoticeModel();
    }
    
    public function list(array $param)
    {
        return $this->model
            ->where('is_del', CommonEnum::NO)
            ->when(isset($param['title']), fn($q) => 
                $q->where('title', 'like', '%'.$param['title'].'%'))
            ->paginate($param['page_size']);
    }
}
```

Dep 继承 `BaseDep`，自动获得 `find`、`get`、`add`、`update`、`delete` 等通用方法。

## 为什么不用 Service？

很多人习惯 Controller → Service → Model 三层。但我发现：

1. Service 容易变成"万能类"，什么都往里塞
2. Module 更强调"业务模块"的概念，边界更清晰
3. Service 在我的架构里专门处理**跨模块通用逻辑**，比如 `TokenService`、`DictService`

## 实际效果

- Controller 平均 10 行代码
- Module 专注业务，易于测试
- Dep 可复用，多个 Module 共享
- 新人上手快，知道代码该写在哪

分层不是银弹，但能让代码更有条理。下一篇聊聊 N+1 查询优化。

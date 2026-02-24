---
title: CMVD 分层架构设计
published: 2026-01-13T10:00:00Z
description: 基于 Webman 高性能框架的分层架构设计，Controller → Module → Validate → Dep
tags: [后端, 架构, PHP]
category: 后端技术
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

## 异常处理：throw helpers

Module 层提供了一组语法糖，让错误处理更简洁：

```php
// 直接抛出业务异常
self::throw('操作失败');

// 条件为 true 时抛出
self::throwIf($exists, '名称已存在');

// 条件为 false/null/empty 时抛出
self::throwUnless($user, '用户不存在');

// 资源不存在时抛 404
self::throwNotFound($record, '记录不存在');
```

**对比传统写法**：

```php
// 旧写法：冗长
if (!$user) {
    return self::error('用户不存在');
}

// 新写法：一行搞定
self::throwNotFound($user, '用户不存在');
```

异常会被 Controller 层的 `fromException` 统一捕获，转成标准响应格式返回给前端。业务代码只管抛，不用关心响应格式。

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

## Validate：参数校验层

很多人把参数校验写在 Controller 或 Module 里，代码一长就乱。我把校验逻辑独立成 Validate 层，每个场景一个静态方法，返回校验规则数组：

```php
class NoticeValidate
{
    public static function list(): array
    {
        return [
            'page' => 'integer|min:1',
            'page_size' => 'integer|min:1|max:100',
            'title' => 'string|max:100',
            'status' => 'integer|in:1,2',
        ];
    }

    public static function add(): array
    {
        return [
            'title' => 'required|string|max:100',
            'content' => 'required|string|max:5000',
            'status' => 'required|integer|in:1,2',
        ];
    }

    public static function edit(): array
    {
        return [
            'id' => 'required|integer',
            'title' => 'required|string|max:100',
            'content' => 'required|string|max:5000',
            'status' => 'required|integer|in:1,2',
        ];
    }
}
```

Module 里一行调用就完成校验：

```php
$param = $this->validate($request, NoticeValidate::add());
```

校验失败会自动抛出异常，被 Controller 层统一捕获返回 422 错误。这样 Module 里不需要写任何 `if ($param['title'] === '')` 这种判断。

## BaseModule：模板方法模式

BaseModule 是所有 Module 的基类，封装了大量通用能力：

```php
abstract class BaseModule
{
    /**
     * 懒加载 Dep 实例（带泛型支持）
     * @template T
     * @param class-string<T> $class
     * @return T
     */
    protected function dep(string $class)
    {
        if (!isset($this->deps[$class])) {
            $this->deps[$class] = new $class();
        }
        return $this->deps[$class];
    }

    /**
     * 标准分页返回
     */
    protected static function paginate($items, array $pageInfo): array
    {
        return [
            [
                'list' => $items,
                'pagination' => $pageInfo,
            ],
            0,
            'ok',
        ];
    }

    /**
     * 标准成功返回
     */
    protected static function success($data = null, string $msg = 'ok'): array
    {
        return [$data, 0, $msg];
    }
}
```

注意 `dep()` 方法的 `@template` 注解——这让 IDE 能正确推断返回类型。写 `$this->dep(NoticeDep::class)->` 时，IDE 会自动提示 `NoticeDep` 的所有方法。这个小细节对开发效率的提升是巨大的。

Module 的返回值统一为 `[$data, $code, $msg]` 三元组：
- `$code = 0` 表示成功
- `$code != 0` 表示业务错误
- Controller 层拿到三元组后统一包装成 JSON 响应

```php
// Module 返回
return [['id' => 1, 'name' => '张三'], 0, 'ok'];

// Controller 包装后的 JSON 响应
{
    "code": 0,
    "msg": "ok",
    "data": { "id": 1, "name": "张三" }
}
```

## BaseDep：数据访问基类

BaseDep 封装了所有通用的 CRUD 操作，子类只需要实现 `createModel()` 方法：

```php
abstract class BaseDep
{
    protected Model $model;

    public function __construct()
    {
        $this->model = $this->createModel();
    }

    abstract protected function createModel(): Model;

    public function getById(int $id): ?Model
    {
        return $this->model->where('id', $id)
            ->where('is_del', CommonEnum::NO)
            ->first();
    }

    public function add(array $data): Model
    {
        return $this->model->create($data);
    }

    public function edit(int $id, array $data): int
    {
        return $this->model->where('id', $id)->update($data);
    }

    public function softDelete(int $id): int
    {
        return $this->model->where('id', $id)
            ->update(['is_del' => CommonEnum::YES]);
    }

    /**
     * 批量查询，返回 id => model 的 Map
     * 解决 N+1 查询问题的核心方法
     */
    public function getMap(array $ids): Collection
    {
        if (empty($ids)) return collect();
        return $this->model
            ->whereIn('id', array_unique($ids))
            ->get()
            ->keyBy('id');
    }

    public function getMapActive(array $ids): Collection
    {
        if (empty($ids)) return collect();
        return $this->model
            ->whereIn('id', array_unique($ids))
            ->where('is_del', CommonEnum::NO)
            ->get()
            ->keyBy('id');
    }
}
```

子类的代码非常干净：

```php
class NoticeDep extends BaseDep
{
    protected function createModel(): Model
    {
        return new NoticeModel();
    }

    // 只写特有的查询方法
    public function list(array $param)
    {
        return $this->model
            ->where('is_del', CommonEnum::NO)
            ->when($param['title'] ?? null, fn($q, $v) =>
                $q->where('title', 'like', "%{$v}%"))
            ->when($param['status'] ?? null, fn($q, $v) =>
                $q->where('status', $v))
            ->orderBy('id', 'desc')
            ->paginate($param['page_size']);
    }
}
```

## 软删除约定

整个系统统一使用 `is_del` 字段做软删除，值来自 `CommonEnum`：

```php
class CommonEnum
{
    const YES = 1;  // 已删除
    const NO = 2;   // 未删除
}
```

为什么不用 Laravel 自带的 SoftDeletes？因为 Webman 不是 Laravel，而且 `is_del` 字段更直观，查询条件也更简单。所有 Dep 的查询方法默认都带 `where('is_del', CommonEnum::NO)`，确保不会查到已删除的数据。

## DictService：字典数据统一管理

系统中有大量的枚举数据需要返回给前端（状态列表、平台列表、角色列表等）。我设计了 DictService 用链式调用来统一管理：

```php
class DictService
{
    private array $dict = [];

    public function setStatusArr(): self
    {
        $this->dict['status_arr'] = [
            ['label' => '启用', 'value' => 1],
            ['label' => '禁用', 'value' => 2],
        ];
        return $this;
    }

    public function setRoleArr(): self
    {
        $roles = (new RoleDep())->getActiveList();
        $this->dict['role_arr'] = $roles->map(fn($r) => [
            'label' => $r->name,
            'value' => $r->id,
        ])->toArray();
        return $this;
    }

    public function getDict(): array
    {
        return $this->dict;
    }
}
```

Module 的 `init` 方法里链式调用：

```php
public function init(): array
{
    $dict = (new DictService())
        ->setStatusArr()
        ->setRoleArr()
        ->getDict();

    return [['dict' => $dict], 0, 'ok'];
}
```

前端拿到 dict 后直接用于下拉框、筛选器等组件，不需要硬编码任何枚举值。

## 完整请求链路

一个请求从进入到返回的完整链路：

```
HTTP 请求
  ↓
Route（路由匹配）
  ↓
Middleware（中间件链）
  ├── TraceId：生成请求追踪 ID
  ├── AccessControl：CORS 跨域处理
  ├── CheckToken：Token 验证
  └── CheckPermission：权限校验
  ↓
Controller（路由转发）
  ├── $this->run([XxxModule::class, 'method'], $request)
  ├── 捕获异常 → fromException() → 标准错误响应
  └── 正常返回 → $this->response() → 标准成功响应
  ↓
Module（业务逻辑）
  ├── $this->validate() → 参数校验
  ├── $this->dep(XxxDep::class) → 数据访问
  ├── self::throwIf() / throwNotFound() → 业务异常
  └── return [$data, $code, $msg] → 标准三元组
  ↓
Dep（数据访问）
  ├── 继承 BaseDep 通用方法
  ├── 自定义查询方法
  └── getMap() / getMapActive() → 批量查询
  ↓
Model（表映射）
  └── Eloquent ORM
```

## 实际效果

这套架构在实际项目中的表现：

| 指标 | 数据 |
|------|------|
| Controller 平均行数 | 10 行 |
| Module 平均行数 | 50-100 行 |
| Dep 平均行数 | 30-60 行 |
| 新增一个 CRUD 模块耗时 | 15-20 分钟 |
| 新人上手时间 | 半天 |

分层不是银弹，但它让每个人都知道代码该写在哪。Controller 不会膨胀，Module 不会混乱，Dep 可以跨模块复用。当项目从 5 个模块增长到 30 个模块时，代码结构依然清晰。

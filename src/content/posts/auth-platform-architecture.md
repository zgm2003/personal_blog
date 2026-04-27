---
title: "认证平台架构：从硬编码到动态管理与三级缓存"
published: 2026-02-10T00:00:00+08:00
draft: false
tags: [置顶, 认证, 缓存, Redis, 架构设计, PHP, Webman]
description: "记录认证平台从枚举硬编码到数据库动态管理、进程内存缓存、Redis 缓存和 MySQL 降级查询的完整重构。"
category: 后端技术
---

> **本文价值**：这篇文章保留的是系统架构能力：从硬编码配置演进到动态平台、三级缓存和稳定降级。

## 一、背景：硬编码的平台管理有多痛

项目最初只有两个平台：`admin`（PC 后台）和 `app`（H5/APP）。平台相关的配置散落在三个地方：

```php
// 1. PermissionEnum 里硬编码平台常量
class PermissionEnum
{
    const PLATFORM_ADMIN = 'admin';
    const PLATFORM_APP = 'app';
    const ALLOWED_PLATFORMS = [self::PLATFORM_ADMIN, self::PLATFORM_APP];
    public static $platformArr = [
        self::PLATFORM_ADMIN => "PC后台",
        self::PLATFORM_APP => "H5/APP",
    ];
}

// 2. SettingService 从 system_settings 表读 TTL 和策略
SettingService::getAccessTtl();      // 全局统一，不区分平台
SettingService::getAuthPolicy();     // 全局统一

// 3. 前端枚举也硬编码一份
export const PlatformEnum = { ADMIN: 'admin', APP: 'app' }
```

问题很明显：
- **加一个平台要改 5 个文件**：PHP 枚举 + 前端枚举 + 数据库配置 + 校验规则 + 字典服务
- **策略不能差异化**：每个平台的 TTL、登录方式、安全策略都是全局统一的
- **硬编码散落各处**：`PermissionEnum` 里有平台常量，`SettingService` 里有 TTL，`system_settings` 表里有策略，改一个漏一个
- **前后端双重维护**：前端也要维护一份平台枚举，两边不同步就出 bug

具体来说，旧架构下新增一个 `mini`（小程序）平台需要：

1. `PermissionEnum` 加常量 `PLATFORM_MINI = 'mini'`
2. `$platformArr` 加映射 `self::PLATFORM_MINI => "小程序"`
3. `ALLOWED_PLATFORMS` 数组加一项
4. `system_settings` 表插入 `auth.policy.mini` 配置
5. 前端 `PlatformEnum` 加 `MINI: 'mini'`
6. 前端下拉选项加一项
7. 各种 `if ($platform === 'admin')` 的地方逐个排查

这不是架构，这是定时炸弹。

## 二、目标：一张表管所有平台

核心思路：把所有平台相关的配置收敛到一张 `auth_platforms` 表，每个平台一行记录。

### 2.1 表结构设计

```sql
CREATE TABLE auth_platforms (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code          VARCHAR(32)  NOT NULL COMMENT '平台标识（admin/app/mini/h5）',
    name          VARCHAR(64)  NOT NULL COMMENT '平台名称',
    login_types   JSON         NOT NULL COMMENT '允许的登录方式',
    access_ttl    INT UNSIGNED NOT NULL DEFAULT 14400 COMMENT 'access_token 有效期（秒）',
    refresh_ttl   INT UNSIGNED NOT NULL DEFAULT 1209600 COMMENT 'refresh_token 有效期（秒）',
    bind_platform TINYINT(1)   NOT NULL DEFAULT 1 COMMENT '绑定平台',
    bind_device   TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '绑定设备',
    bind_ip       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '绑定IP',
    single_session TINYINT(1)  NOT NULL DEFAULT 0 COMMENT '单端登录',
    max_sessions  INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '最大会话数（0=不限）',
    allow_register TINYINT(1)  NOT NULL DEFAULT 0 COMMENT '允许注册',
    status        TINYINT(1)   NOT NULL DEFAULT 1,
    is_del        TINYINT(1)   NOT NULL DEFAULT 0,
    created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_code (code),
    KEY idx_status_del (status, is_del)
) COMMENT '认证平台配置';
```

### 2.2 字段设计思路

每个字段都有明确的业务含义：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `code` | VARCHAR(32) | 平台唯一标识，正则 `^[a-z][a-z0-9_]{1,48}$` | `admin`, `app`, `mini` |
| `login_types` | JSON | 允许的登录方式数组 | `["password","email"]` |
| `access_ttl` | INT | access_token 有效期（秒），范围 60~2592000 | 14400（4小时） |
| `refresh_ttl` | INT | refresh_token 有效期（秒），范围 60~31536000 | 1209600（14天） |
| `bind_platform` | TINYINT | 是否校验请求头 platform 与会话 platform 一致 | 1=是 |
| `bind_device` | TINYINT | 是否校验设备 ID 一致 | 2=否 |
| `bind_ip` | TINYINT | 是否校验 IP 一致（严格模式） | 2=否 |
| `single_session` | TINYINT | 单端登录（同一时间只允许一个会话） | 1=是 |
| `max_sessions` | INT | 最大会话数（0=不限），与 single_session 互斥 | 5 |
| `allow_register` | TINYINT | 是否允许新用户通过验证码自动注册 | 2=否 |

这样每个平台可以独立配置完全不同的策略：

```
admin：access_ttl=4小时，单端登录，禁止注册，绑定平台
app：  access_ttl=8小时，最多5个会话，允许注册，绑定设备
mini： access_ttl=2小时，不限会话，允许注册，绑定IP
```

未来加平台？插一条记录就行，零代码改动。

### 2.3 为什么用 JSON 存 login_types？

`login_types` 用 JSON 数组而不是逗号分隔字符串或关联表，原因：

1. **查询简单**：Eloquent 的 `$casts = ['login_types' => 'json']` 自动序列化/反序列化
2. **校验方便**：验证层直接校验数组元素 `v::arrayType()->each(v::stringType()->in(['password', 'email', 'phone']))`
3. **数据量小**：登录方式最多 3 种，JSON 完全够用
4. **不需要关联查询**：不存在"查所有支持邮箱登录的平台"这种需求

Model 层只需要一行 cast：

```php
class AuthPlatformModel extends BaseModel
{
    protected $table = 'auth_platforms';
    protected $casts = [
        'login_types' => 'json',
    ];
}
```

读出来直接是 PHP 数组，写入时传数组自动 `json_encode`，零心智负担。

## 三、分层架构：从 Controller 到 Dep 的完整链路

整个认证平台模块严格遵循 CMVD 分层架构：`Controller → Module → Validate → Dep → Model`。

### 3.1 Controller：只做转发

```php
class AuthPlatformController extends Controller
{
    public function init(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'init'], $request);
    }

    public function list(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'list'], $request);
    }

    /** @OperationLog("认证平台新增") @Permission("system_authPlatform_add") */
    public function add(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'add'], $request);
    }

    /** @OperationLog("认证平台编辑") @Permission("system_authPlatform_edit") */
    public function edit(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'edit'], $request);
    }

    /** @OperationLog("认证平台删除") @Permission("system_authPlatform_del") */
    public function del(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'del'], $request);
    }

    /** @OperationLog("认证平台状态变更") @Permission("system_authPlatform_status") */
    public function status(Request $request)
    {
        return $this->run([AuthPlatformModule::class, 'status'], $request);
    }
}
```

Controller 就是个路由分发器。注解 `@OperationLog` 记录操作日志，`@Permission` 校验按钮权限码。每个方法一行代码，干净利落。

### 3.2 Validate：参数校验

校验层用 `Respect\Validation` 做声明式校验，新增和编辑分开定义：

```php
class AuthPlatformValidate
{
    public static function add(): array
    {
        return [
            'code'           => v::regex('/^[a-z][a-z0-9_]{1,48}$/')->setName('平台标识'),
            'name'           => v::length(1, 100)->setName('平台名称'),
            'login_types'    => v::arrayType()->each(
                v::stringType()->in(['password', 'email', 'phone'])
            )->setName('登录方式'),
            'access_ttl'     => v::intVal()->between(60, 2592000)->setName('access_token有效期'),
            'refresh_ttl'    => v::intVal()->between(60, 31536000)->setName('refresh_token有效期'),
            'bind_platform'  => v::intVal()->in([1, 2])->setName('绑定平台'),
            'bind_device'    => v::intVal()->in([1, 2])->setName('绑定设备'),
            'bind_ip'        => v::intVal()->in([1, 2])->setName('绑定IP'),
            'single_session' => v::intVal()->in([1, 2])->setName('单端登录'),
            'max_sessions'   => v::intVal()->between(0, 100)->setName('最大会话数'),
            'allow_register' => v::intVal()->in([1, 2])->setName('允许注册'),
        ];
    }

    public static function edit(): array
    {
        return [
            'id'   => v::intVal()->setName('ID'),
            // ... 其余字段同 add，但不含 code（code 不可修改）
        ];
    }
}
```

几个设计细节：
- `code` 用正则限制格式：小写字母开头，只允许小写字母、数字、下划线，长度 2-49
- `access_ttl` 范围 60 秒 ~ 30 天，`refresh_ttl` 范围 60 秒 ~ 1 年
- 布尔字段用 `1/2` 而不是 `0/1`，因为项目统一用 `CommonEnum::YES=1 / NO=2`
- 编辑时不允许修改 `code`，避免缓存 key 混乱

### 3.3 Module：业务编排

Module 层是业务逻辑的主战场。以新增平台为例：

```php
class AuthPlatformModule extends BaseModule
{
    protected AuthPlatformDep $authPlatformDep;
    protected DictService $dictService;

    public function __construct()
    {
        $this->authPlatformDep = $this->dep(AuthPlatformDep::class);
        $this->dictService = $this->svc(DictService::class);
    }

    /**
     * 初始化字典（前端下拉选项全部从这里拿）
     */
    public function init($request): array
    {
        $data['dict'] = $this->dictService
            ->setCommonStatusArr()
            ->setAuthPlatformLoginTypeArr()
            ->getDict();
        return self::success($data);
    }

    /**
     * 新增平台
     */
    public function add($request): array
    {
        $param = $this->validate($request, AuthPlatformValidate::add());

        // 唯一性校验
        self::throwIf(
            $this->authPlatformDep->existsByCode($param['code']),
            "平台标识 [{$param['code']}] 已存在"
        );

        $this->authPlatformDep->addPlatform([
            'code'           => $param['code'],
            'name'           => $param['name'],
            'login_types'    => \json_encode($param['login_types']),
            'access_ttl'     => (int)$param['access_ttl'],
            'refresh_ttl'    => (int)$param['refresh_ttl'],
            'bind_platform'  => (int)$param['bind_platform'],
            'bind_device'    => (int)$param['bind_device'],
            'bind_ip'        => (int)$param['bind_ip'],
            'single_session' => (int)$param['single_session'],
            'max_sessions'   => (int)$param['max_sessions'],
            'allow_register' => (int)$param['allow_register'],
            'status'         => CommonEnum::YES,
            'is_del'         => CommonEnum::NO,
        ]);

        return self::success();
    }
}
```

注意 `init` 方法：前端所有下拉选项都从后端 `init` 接口获取，**前端不硬编码任何枚举**。这是项目的铁律。`DictService` 用链式调用组装字典数据，每个 `set*` 方法负责一类字典。

`self::throwIf` 是 `BaseModule` 提供的语法糖，条件为 true 时抛出 `BusinessException`，被 Controller 层统一捕获转成标准 JSON 响应。比传统的 `if + return error` 写法简洁得多。

### 3.4 Dep：数据访问层（写穿缓存）

Dep 层是整个缓存架构的关键。它实现了**写穿缓存（write-through cache）**：每次写操作都主动清除 Redis 缓存 + 进程内存缓存。

```php
class AuthPlatformDep extends BaseDep
{
    const CACHE_PREFIX = 'auth_platform_';
    const CACHE_ALL    = 'auth_platform_all';

    protected function createModel(): Model
    {
        return new AuthPlatformModel();
    }

    /**
     * 根据 code 获取启用的平台配置（永久缓存，写时清除）
     */
    public function getByCode(string $code): ?array
    {
        $cacheKey = self::CACHE_PREFIX . $code;
        $cached = Cache::get($cacheKey);
        if ($cached !== null) {
            return $cached ?: null;  // false 表示"确认不存在"
        }

        $row = $this->model
            ->where('code', $code)
            ->where('status', CommonEnum::YES)
            ->where('is_del', CommonEnum::NO)
            ->first();

        if (!$row) {
            // 缓存空值，防止缓存穿透
            Cache::set($cacheKey, false);
            return null;
        }

        $data = $row->toArray();
        Cache::set($cacheKey, $data);  // 永久缓存，不设 TTL
        return $data;
    }
}
```

这里有个细节：**缓存空值防穿透**。如果某个 `code` 不存在，缓存 `false`。下次查询时 `$cached !== null` 为 true（因为 `false !== null`），直接返回 `null`，不会打到数据库。

写操作的缓存清除：

```php
// 新增平台
public function addPlatform(array $data): int
{
    $id = $this->model->insertGetId($data);
    $this->clearCache($data['code'] ?? '');
    return $id;
}

// 更新平台（需要清除新旧两个 code 的缓存）
public function updateById(int $id, array $data, ?string $oldCode = null): bool
{
    $count = $this->model->where('id', $id)->where('is_del', CommonEnum::NO)->update($data);
    if ($count > 0) {
        if ($oldCode) {
            $this->clearCache($oldCode);
        }
        if (!empty($data['code'])) {
            $this->clearCache($data['code']);
        }
    }
    return $count > 0;
}

// 删除平台（软删除，清除所有被删平台的缓存）
public function deleteByIds($ids): bool
{
    $ids = \is_array($ids) ? $ids : [$ids];
    $rows = $this->model->whereIn('id', $ids)->where('is_del', CommonEnum::NO)->get(['code']);
    $count = $this->model->whereIn('id', $ids)->update(['is_del' => CommonEnum::YES]);
    if ($count > 0) {
        foreach ($rows as $r) {
            $this->clearCache($r->code);
        }
    }
    return $count > 0;
}
```

注意 `deleteByIds` 的顺序：**先查出 code，再执行软删除，最后清缓存**。如果先删再查，code 就拿不到了。

缓存清除方法，同时清 Redis 和进程内存：

```php
private function clearCache(string $code = ''): void
{
    // 清 Redis 缓存
    Cache::delete(self::CACHE_ALL);
    Cache::delete(self::CACHE_ALL . '_map');
    if ($code) {
        Cache::delete(self::CACHE_PREFIX . $code);
    }
    // 清当前进程内存缓存
    AuthPlatformService::flushMemCache();
}
```

每次写操作都清三个 Redis key：
1. `auth_platform_all` — 所有启用平台 code 列表
2. `auth_platform_all_map` — code→name 映射
3. `auth_platform_{code}` — 单个平台配置

加上进程内存缓存，一共清四层。看起来暴力，但平台配置一个月改一次，清缓存的开销可以忽略。

## 四、三级缓存架构：进程内存 → Redis → MySQL

平台配置的特点是**读多写少**（每个请求都读，可能一个月才改一次）。这种场景最适合多级缓存。

### 4.1 架构总览

```
┌─────────────────────────────────────────────────────┐
│                    API 请求                          │
└──────────────────────┬──────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────┐
│  L1: 进程内存缓存（~0ms）                             │
│  PHP 静态变量，TTL 60秒                               │
│  Webman 常驻进程，内存不会被释放                        │
└──────────────────────┬──────────────────────────────┘
                       │ 未命中 / 过期
                       ▼
┌─────────────────────────────────────────────────────┐
│  L2: Redis 缓存（0.1-0.5ms）                         │
│  永久缓存，写操作时主动清除                             │
│  cache 连接，独立于 token 连接                         │
└──────────────────────┬──────────────────────────────┘
                       │ 未命中
                       ▼
┌─────────────────────────────────────────────────────┐
│  L3: MySQL（1-5ms）                                  │
│  auth_platforms 表，查完回写 L2                        │
└─────────────────────────────────────────────────────┘
```

### 4.2 为什么 Webman 适合进程内存缓存？

这是整个架构最关键的一点，也是和传统 PHP 最大的区别。

**传统 PHP-FPM 模型**：每个请求 fork 一个进程（或从进程池取），请求结束进程就回收，所有变量销毁。静态变量只在单次请求内有效，跨请求缓存没有意义。

**Webman 常驻进程模型**：Worker 进程启动后一直活着，处理成千上万个请求。静态变量在整个进程生命周期内有效，天然就是一个进程级缓存。

```
PHP-FPM:
  请求1 → 进程A（创建变量 → 处理 → 销毁变量 → 进程回收）
  请求2 → 进程B（创建变量 → 处理 → 销毁变量 → 进程回收）
  每次都从零开始

Webman:
  Worker进程A（启动 → 处理请求1 → 处理请求2 → ... → 处理请求N）
  静态变量在请求1写入后，请求2直接读取，零开销
```

这意味着我们可以用 PHP 的 `static` 变量做 L1 缓存，性能接近直接读内存（纳秒级），比 Redis 快 100 倍以上。

### 4.3 AuthPlatformService：统一对外的服务层

`AuthPlatformService` 是整个认证平台的唯一出口。所有消费方（中间件、登录模块、字典服务、权限校验）都通过它获取平台配置，不直接访问 Dep 或 Redis。

```php
class AuthPlatformService
{
    private static ?AuthPlatformDep $dep = null;

    /** 进程级内存缓存：code → 平台数据 */
    private static array $memPlatform = [];
    /** 所有启用平台 code 列表 */
    private static ?array $memCodes = null;
    /** code→name 映射 */
    private static ?array $memMap = null;
    /** 缓存写入时间戳 */
    private static int $memPlatformAt = 0;
    private static int $memCodesAt = 0;
    private static int $memMapAt = 0;

    private const MEM_TTL = 60; // 60秒过期

    private static function isExpired(int $timestamp): bool
    {
        return (\time() - $timestamp) > self::MEM_TTL;
    }
}
```

三组缓存，三个时间戳，独立过期。为什么不用一个统一的时间戳？因为三组数据的访问频率不同：
- `$memPlatform`：每个请求都查（CheckToken 中间件）
- `$memCodes`：权限校验时查
- `$memMap`：字典接口时查

如果用统一时间戳，查 `$memMap` 导致刷新，会连带刷新 `$memPlatform`，浪费。

### 4.4 核心方法：getPlatform()

```php
public static function getPlatform(string $code): array
{
    // L1: 进程内存
    if (isset(self::$memPlatform[$code]) && !self::isExpired(self::$memPlatformAt)) {
        return self::$memPlatform[$code];
    }

    // L2+L3: Redis → DB（由 Dep 层处理）
    $platform = self::dep()->getByCode($code);
    if (!$platform) {
        throw new BusinessException("平台 [{$code}] 未配置或已禁用，拒绝访问", 401);
    }

    // 回写内存
    self::$memPlatform[$code] = $platform;
    self::$memPlatformAt = \time();

    return $platform;
}
```

调用链路：`getPlatform('admin')`
1. 检查 `$memPlatform['admin']` 是否存在且未过期 → 命中返回（0ms）
2. 未命中 → 调用 `AuthPlatformDep::getByCode('admin')`
3. Dep 层检查 Redis `auth_platform_admin` → 命中返回（0.1-0.5ms）
4. Redis 未命中 → 查 MySQL → 回写 Redis → 返回（1-5ms）
5. 回写进程内存 → 下次直接命中

**Fail-close 设计**：如果平台未配置或已禁用，直接抛 401 异常。不做任何降级、不给默认值。这是安全系统的基本原则 — 宁可拒绝服务，不可放行未授权请求。

### 4.5 便捷方法：基于 getPlatform 的衍生查询

所有便捷方法都基于 `getPlatform()` 的内存缓存，不会产生额外的缓存查询：

```php
/**
 * 获取平台的完整安全策略
 */
public static function getAuthPolicy(string $code): array
{
    $p = self::getPlatform($code);
    return [
        'bind_platform'              => $p['bind_platform'] === CommonEnum::YES,
        'bind_device'                => $p['bind_device'] === CommonEnum::YES,
        'bind_ip'                    => $p['bind_ip'] === CommonEnum::YES,
        'single_session_per_platform' => $p['single_session'] === CommonEnum::YES,
        'max_sessions'               => (int)$p['max_sessions'],
        'allow_register'             => $p['allow_register'] === CommonEnum::YES,
    ];
}

/**
 * 获取平台的 access_token TTL
 */
public static function getAccessTtl(string $code): int
{
    return (int)self::getPlatform($code)['access_ttl'];
}

/**
 * 获取平台的 refresh_token TTL
 */
public static function getRefreshTtl(string $code): int
{
    return (int)self::getPlatform($code)['refresh_ttl'];
}

/**
 * 获取平台允许的登录方式
 */
public static function getLoginTypes(string $code): array
{
    $p = self::getPlatform($code);
    $types = $p['login_types'];
    return \is_array($types) ? $types : \json_decode($types, true) ?? [];
}

/**
 * 平台是否允许注册
 */
public static function isRegisterEnabled(string $code): bool
{
    return self::getPlatform($code)['allow_register'] === CommonEnum::YES;
}

/**
 * 校验平台是否合法并返回安全策略（合并调用）
 * 用于 CheckToken 中间件，一次查询搞定
 */
public static function validateAndGetPolicy(string $code): ?array
{
    if (!\in_array($code, self::getAllowedPlatforms(), true)) {
        return null;
    }
    return self::getAuthPolicy($code);
}
```

`getAuthPolicy()` 调用 `getPlatform()`，如果内存缓存命中，整个方法的开销就是一次数组读取 + 几个比较操作，纳秒级。

`getLoginTypes()` 里的 `\is_array()` 判断是防御性编程：虽然 Model 的 `$casts` 会自动把 JSON 转数组，但如果数据是从 Redis 缓存读的（序列化/反序列化后），类型可能不一致。加个判断更安全。

### 4.6 多 Worker 进程的一致性问题

Webman 多进程模型下，假设有 4 个 Worker 进程。Worker A 处理了平台配置的修改请求，清了自己的内存缓存和 Redis 缓存。但 Worker B/C/D 的内存缓存还是旧数据。

```
Worker A: 修改平台配置 → 清 Redis → 清自己内存 ✓
Worker B: 内存缓存还是旧的 ✗（最多 60 秒后过期）
Worker C: 内存缓存还是旧的 ✗（最多 60 秒后过期）
Worker D: 内存缓存还是旧的 ✗（最多 60 秒后过期）
```

怎么办？答案是：**不用管**。

平台配置的变更频率极低（一个月可能改一次），60 秒的延迟完全可以接受。60 秒后内存缓存过期，Worker B/C/D 会重新从 Redis 读取（此时 Redis 已经是新数据了，因为 Worker A 清了 Redis 后，下次读会从 DB 回写）。

如果真的需要实时生效（比如紧急禁用某个平台），重启一下 Worker 就行：

```bash
# 平滑重启所有 Worker（不中断服务）
kill -USR1 $(cat runtime/webman.pid)
```

这比引入 Redis Pub/Sub 或共享内存方案简单 100 倍，而且对于平台配置这种场景完全够用。

```php
/**
 * 清除当前进程的内存缓存（写操作后调用）
 */
public static function flushMemCache(): void
{
    self::$memPlatform = [];
    self::$memCodes = null;
    self::$memMap = null;
    self::$memPlatformAt = 0;
    self::$memCodesAt = 0;
    self::$memMapAt = 0;
}
```

`flushMemCache()` 是 public static 的，Dep 层写操作后直接调用。只清当前进程，其他进程靠 TTL 自然过期。

## 五、Token 体系：从生成到校验的完整流程

### 5.1 Token 生成：TokenService

```php
class TokenService
{
    /**
     * 生成随机 Token
     */
    public static function makeToken(int $bytes = 32): string
    {
        return bin2hex(random_bytes($bytes));
    }

    /**
     * Token 哈希（加 pepper 防彩虹表）
     */
    public static function hashToken(string $token): string
    {
        $pepper = (string) config('app.token_pepper', '');
        if ($pepper === '' || $pepper === 'change_me_to_long_random') {
            throw new \RuntimeException('TOKEN_PEPPER 未配置或不安全');
        }
        return hash('sha256', $token . '|' . $pepper);
    }

    /**
     * 生成 Token 对（按平台配置不同的 TTL）
     */
    public static function generateTokenPair(string $platform): array
    {
        $now = Carbon::now();
        $accessTtl = AuthPlatformService::getAccessTtl($platform);
        $refreshTtl = AuthPlatformService::getRefreshTtl($platform);

        $accessToken = self::makeToken(32);    // 64 字符 hex
        $refreshToken = self::makeToken(64);   // 128 字符 hex

        return [
            'access_token'       => $accessToken,
            'refresh_token'      => $refreshToken,
            'access_token_hash'  => self::hashToken($accessToken),
            'refresh_token_hash' => self::hashToken($refreshToken),
            'access_expires'     => $now->copy()->addSeconds($accessTtl),
            'refresh_expires'    => $now->copy()->addSeconds($refreshTtl),
            'access_ttl'         => $accessTtl,
            'refresh_ttl'        => $refreshTtl,
            'now'                => $now,
        ];
    }
}
```

几个安全设计：

1. **Token 不存明文**：数据库和 Redis 只存 SHA256 哈希值。即使数据库泄露，攻击者也无法还原 Token
2. **加 Pepper**：哈希时拼接服务端密钥（`token_pepper`），防止彩虹表攻击。Pepper 从 `.env` 读取，不进版本控制
3. **access_token 短，refresh_token 长**：access 用 32 字节（64 字符），refresh 用 64 字节（128 字符）。refresh_token 更长是因为它的有效期更长，需要更高的安全性
4. **TTL 按平台差异化**：`AuthPlatformService::getAccessTtl($platform)` 从平台配置读取，admin 可以设 4 小时，app 可以设 8 小时

### 5.2 为什么不用 JWT？

项目选择了 opaque token + 服务端会话，而不是 JWT。原因：

| 对比项 | JWT | Opaque Token + Session |
|--------|-----|----------------------|
| 吊销能力 | 无法即时吊销（除非维护黑名单） | 删 Redis key 即时生效 |
| 单端登录 | 很难实现 | Redis 指针轻松实现 |
| Token 大小 | 大（payload + 签名，通常 500+ 字节） | 小（64 字符 hex） |
| 服务端状态 | 无状态（理论上） | 有状态（Redis + DB） |
| 安全策略 | 签发后不可变 | 随时可调整（绑定 IP、设备等） |

对于需要精细会话控制的后台系统，opaque token 是更好的选择。JWT 的"无状态"优势在需要吊销、单端登录、会话管理的场景下反而成了劣势。

### 5.3 会话存储：Redis 管道分隔字符串

会话数据在 Redis 中用管道分隔字符串存储，而不是 JSON 或 Hash：

```
key:   {access_token_hash}
value: userId|expiresAt|ip|platform|deviceId|sessionId
TTL:   1800（30分钟，每次请求续期）
```

为什么不用 JSON？

```php
// JSON 方案：序列化/反序列化开销
$session = json_decode(Redis::get($key), true);
// 每次请求都要 json_decode，CPU 开销不小

// 管道分隔方案：explode 比 json_decode 快 5-10 倍
$parts = explode('|', $cached);
$session = [
    'user_id'    => $parts[0],
    'expires_at' => $parts[1],
    'ip'         => $parts[2],
    'platform'   => $parts[3],
    'device_id'  => $parts[4] ?? '',
    'id'         => $parts[5] ?? 0,
];
```

会话数据结构固定、字段少、不嵌套，管道分隔是最高效的方案。每个请求都要解析一次，积少成多。

## 六、CheckToken 中间件：每个请求的认证链路

`CheckToken` 是整个认证系统的核心中间件，每个需要认证的 API 请求都要经过它。

### 6.1 完整流程图

```
请求进来 → CheckToken
  │
  ├─ 1. 解析 Bearer Token → SHA256(token + pepper) → hash
  │
  ├─ 2. resolveSession(hash)
  │     ├─ Redis token连接 GET {hash}
  │     │   命中 → explode('|') 解析 → 返回会话
  │     │   未命中 → 查 DB user_sessions 表
  │     │            → 回写 Redis（管道分隔，TTL 30分钟）
  │     └─ 返回: userId | expiresAt | ip | platform | deviceId | sessionId
  │
  ├─ 3. 检查 access_token 是否过期
  │     └─ Carbon::parse(expires_at)->isPast() → 过期则删 Redis 返回 401
  │
  ├─ 4. 平台校验
  │     ├─ 请求头必须携带 platform（强制，无默认值）
  │     └─ AuthPlatformService::isValidPlatform(platform)
  │        └─ 内存缓存命中(~0ms) ← 60秒内不查Redis
  │
  ├─ 5. 安全策略校验
  │     ├─ AuthPlatformService::getAuthPolicy(会话中的 platform)
  │     │   └─ 内存缓存命中(~0ms) ← getPlatform 已缓存
  │     ├─ bind_platform: 会话平台 vs 请求头平台
  │     ├─ bind_device: 会话设备ID vs 请求头 device-id
  │     └─ bind_ip: 会话IP vs 当前请求IP
  │
  ├─ 6. 挂载请求信息
  │     ├─ $request->userId = 用户ID
  │     ├─ $request->sessionId = 会话ID
  │     └─ $request->platform = 平台标识
  │
  ├─ 7. 单端登录裁决（如果开启）
  │     └─ checkSingleSession()
  │        ├─ Redis GET cur_sess:{platform}:{userId}
  │        ├─ 指针存在且匹配 → 通过
  │        ├─ 指针不存在 → 查DB重建指针
  │        ├─ 指针不匹配 → 验证指针有效性
  │        └─ 最终不匹配 → 删 Redis，返回"账号已在其他设备登录"
  │
  └─ 8. 续期 Redis → EXPIRE {hash} 30分钟
        └─ 用户活跃期间，会话缓存永不过期
```

### 6.2 resolveSession：Redis 缓存 → DB 回查

```php
private function resolveSession(string $redisKey, string $tokenHash): ?array
{
    // 优先从 Redis 读取
    $cached = Redis::connection('token')->get($redisKey);

    if ($cached) {
        $parts = explode('|', $cached);
        if (\count($parts) >= 4) {
            return [
                'user_id'    => $parts[0],
                'expires_at' => $parts[1],
                'ip'         => $parts[2],
                'platform'   => $parts[3],
                'device_id'  => $parts[4] ?? '',
                'id'         => $parts[5] ?? 0,
            ];
        }
    }

    // Redis 未命中，查 DB
    $sessionDep = new UserSessionsDep();
    $row = $sessionDep->findValidByAccessHash($tokenHash);
    if (!$row) {
        return null;
    }

    $session = \is_object($row) ? $row->toArray() : (array)$row;

    // 回写 Redis（管道分隔，TTL 30分钟）
    $value = implode('|', [
        $session['user_id'],
        $session['expires_at'],
        $session['ip'] ?? '',
        $session['platform'] ?? '',
        $session['device_id'] ?? '',
        $session['id'],
    ]);
    Redis::connection('token')->set($redisKey, $value, CacheTTLEnum::TOKEN_SESSION);

    return $session;
}
```

`CacheTTLEnum::TOKEN_SESSION = 1800`（30 分钟）。每次请求成功后会续期（步骤 8），所以只要用户持续活跃，Redis 缓存就不会过期。用户 30 分钟不操作，缓存自动清除，下次请求回查 DB。

### 6.3 安全策略校验的细节

```php
// 5.1 绑定平台：防止 Token 跨平台使用
if (!empty($policy['bind_platform'])) {
    if (strtolower($session['platform']) !== strtolower($currentPlatform)) {
        return json(['code' => ErrorCodeEnum::UNAUTHORIZED, 'msg' => '平台不匹配']);
    }
}

// 5.2 绑定设备：防止 Token 在其他设备使用
if (!empty($policy['bind_device']) && !empty($session['device_id'])) {
    $currentDevice = $request->header('device-id');
    if (!$currentDevice || $currentDevice !== $session['device_id']) {
        return json(['code' => ErrorCodeEnum::UNAUTHORIZED, 'msg' => '设备变更，请重新登录']);
    }
}

// 5.3 绑定 IP：最严格模式，IP 变动直接踢下线
if (!empty($policy['bind_ip'])) {
    if ($session['ip'] !== $request->getRealIp()) {
        Redis::connection('token')->del($redisKey);  // 主动删除缓存
        return json(['code' => ErrorCodeEnum::UNAUTHORIZED, 'msg' => 'IP地址变动']);
    }
}
```

三个安全策略从宽到严：
- **bind_platform**：最基本的，防止 admin 的 Token 被拿到 app 端用
- **bind_device**：中等强度，需要前端在请求头传 `device-id`（通常是设备指纹）
- **bind_ip**：最严格，IP 变动直接踢下线并删除 Redis 缓存。适合高安全场景，但对移动网络不友好（切 WiFi/4G 会变 IP）

注意 `bind_ip` 的处理：不仅返回 401，还主动 `del` Redis 缓存。因为 IP 变动可能意味着 Token 泄露，要立即失效。

### 6.4 单端登录裁决：Redis 指针机制

单端登录的核心是一个 Redis 指针：`cur_sess:{platform}:{userId}` → `sessionId`。

```php
private function checkSingleSession(array $session, string $redisKey): ?Response
{
    $curSessKey = "cur_sess:" . strtolower(trim($session['platform']))
                . ":{$session['user_id']}";
    $allowedSessionId = Redis::connection('token')->get($curSessKey);

    // 情况1：指针不存在，从 DB 重建
    if (!$allowedSessionId) {
        $latest = (new UserSessionsDep())
            ->findLatestActiveByUserPlatform($session['user_id'], $session['platform']);
        if ($latest) {
            $allowedSessionId = $latest->id;
            Redis::connection('token')->set(
                $curSessKey, $allowedSessionId, CacheTTLEnum::SINGLE_SESSION_POINTER
            );
        }
    }
    // 情况2：指针存在但不匹配，验证指针有效性
    elseif ((int)$allowedSessionId !== (int)$session['id']) {
        $latest = (new UserSessionsDep())
            ->findLatestActiveByUserPlatform($session['user_id'], $session['platform']);
        if ($latest && $latest->id != $allowedSessionId) {
            // 指针指向的会话已失效，更新指针
            $allowedSessionId = $latest->id;
            Redis::connection('token')->set(
                $curSessKey, $allowedSessionId, CacheTTLEnum::SINGLE_SESSION_POINTER
            );
        } elseif (!$latest) {
            $allowedSessionId = null;
        }
    }
    // 情况3：指针匹配 → 直接通过（最常见路径，不查 DB）

    // 最终裁决
    if ($allowedSessionId && (int)$allowedSessionId !== (int)$session['id']) {
        Redis::connection('token')->del($redisKey);
        return json([
            'code' => ErrorCodeEnum::UNAUTHORIZED,
            'msg'  => '账号已在其他设备登录',
        ]);
    }

    return null;  // 通过
}
```

三种情况的处理逻辑：

| 情况 | 指针状态 | 处理 | 是否查 DB |
|------|---------|------|----------|
| 指针匹配 | 存在且等于当前 sessionId | 直接通过 | 否 |
| 指针不存在 | Redis key 过期或被删 | 从 DB 查最新会话重建指针 | 是 |
| 指针不匹配 | 存在但不等于当前 sessionId | 验证指针有效性，可能更新 | 是 |

**最常见的路径是"指针匹配"**，只需要一次 Redis GET，不查 DB。只有指针丢失或不匹配时才回查 DB，这种情况很少发生。

`SINGLE_SESSION_POINTER` 的 TTL 是 30 天（`CacheTTLEnum::SINGLE_SESSION_POINTER = 2592000`），和 refresh_token 的最大有效期一致。

## 七、会话淘汰策略：单端互踢与 FIFO 上限

`auth_platforms` 表里有两个关键字段控制会话策略：`single_session` 和 `max_sessions`。它们在登录时（`AuthModule::createSession`）执行淘汰逻辑。

### 7.1 单端登录：新登录踢掉所有旧会话

```php
if (!empty($policy['single_session_per_platform'])) {
    // 查出该用户在此平台的所有活跃会话
    $oldSessions = $this->userSessionsDep->listActiveByUserPlatform($userId, $platformHeader);
    
    // 逐个删除 Redis 缓存
    foreach ($oldSessions as $old) {
        Redis::connection('token')->del($old->access_token_hash);
    }
    
    // 批量撤销 DB 会话
    $this->userSessionsDep->revokeByUserPlatform($userId, $platformHeader);
}
```

流程：
1. 查出所有活跃会话（DB 查询）
2. 逐个删除 Redis 中的 Token 缓存（旧会话立即失效）
3. 批量更新 DB 的 `revoked_at` 字段
4. 创建新会话，更新 Redis 指针

旧设备的下一次请求会在 `CheckToken` 中间件的步骤 2 失败（Redis 中找不到 Token），返回 401。

### 7.2 多会话上限：FIFO 淘汰最早的

```php
elseif ($policy['max_sessions'] > 0) {
    $activeSessions = $this->userSessionsDep->listActiveByUserPlatform($userId, $platformHeader);
    
    // 计算需要淘汰的数量（当前活跃数 - 上限 + 1（给新会话腾位置））
    $overCount = $activeSessions->count() - $policy['max_sessions'] + 1;
    
    if ($overCount > 0) {
        // 按 ID 升序排列，取最早的 N 个淘汰
        $toRevoke = $activeSessions->sortBy('id')->take($overCount);
        foreach ($toRevoke as $old) {
            Redis::connection('token')->del($old->access_token_hash);
            $this->userSessionsDep->revoke($old->id);
        }
    }
}
```

举例：`max_sessions = 5`，用户当前有 5 个活跃会话，现在要登录第 6 个。

```
overCount = 5 - 5 + 1 = 1
淘汰最早的 1 个会话 → 剩余 4 个 + 新建 1 个 = 5 个
```

FIFO（先进先出）策略：最早创建的会话最先被淘汰。用 `sortBy('id')` 排序，ID 最小的就是最早的。

### 7.3 两种策略的互斥关系

```php
if (!empty($policy['single_session_per_platform'])) {
    // 单端登录逻辑
} elseif ($policy['max_sessions'] > 0) {
    // 多会话上限逻辑
}
```

用 `if/elseif` 保证互斥：
- 开了单端登录，`max_sessions` 无意义（因为永远只有 1 个会话）
- 没开单端登录且 `max_sessions > 0`，才走 FIFO 淘汰
- 两个都没开（`single_session=2, max_sessions=0`），不限制会话数

### 7.4 登录后更新 Redis 指针

```php
private function updateSessionPointer(int $userId, string $platform, int $sessionId): void
{
    $key = "cur_sess:" . strtolower(trim($platform)) . ":{$userId}";
    Redis::connection('token')->set($key, $sessionId, CacheTTLEnum::SINGLE_SESSION_POINTER);
}
```

不管是否开启单端登录，每次登录都会更新指针。这样 `CheckToken` 中间件的单端登录裁决才能正确工作。

登出时也要清理指针：

```php
private function clearSessionPointerIfMatches(int $userId, string $platform, int $sessionId): void
{
    if (!$platform) return;
    $key = "cur_sess:" . strtolower(trim($platform)) . ":{$userId}";
    $currentPtr = Redis::connection('token')->get($key);
    // 只有指针指向当前会话时才删除，避免误删新会话的指针
    if ($currentPtr && (int)$currentPtr === (int)$sessionId) {
        Redis::connection('token')->del($key);
    }
}
```

注意这里的**条件删除**：只有指针指向当前登出的会话时才删除。如果用户在设备 A 登出，但设备 B 已经登录（指针指向 B 的会话），不能把 B 的指针删了。

## 八、Token 刷新流程

access_token 过期后，客户端用 refresh_token 换取新的 Token 对。

```php
public function refresh($request): array
{
    $refreshToken = $request->post('refresh_token');
    self::throwIf(!$refreshToken, '缺少刷新令牌', self::CODE_UNAUTHORIZED);

    // 1. 哈希 refresh_token
    $hash = TokenService::hashToken($refreshToken);

    // 2. 查找有效会话（通过 refresh_token_hash）
    $session = $this->userSessionsDep->findValidByRefreshHash($hash);
    self::throwIf(!$session, '刷新令牌无效或已过期', self::CODE_UNAUTHORIZED);

    // 3. 检查 refresh_token 是否过期
    self::throwIf(
        Carbon::parse($session['refresh_expires_at'])->isPast(),
        '刷新令牌已过期，请重新登录',
        self::CODE_UNAUTHORIZED
    );

    // 4. 单端登录校验（防止被踢的设备用 refresh_token 偷偷续期）
    $platform = $session['platform'];
    self::throwIf(
        !$this->checkSingleSessionPolicy($session['user_id'], $platform, $session['id']),
        '账号已在其他设备登录，请重新登录',
        self::CODE_UNAUTHORIZED
    );

    // 5. 生成新的 Token 对（TTL 按平台配置）
    $tokens = TokenService::generateTokenPair($platform);

    // 6. 轮换会话（更新 hash、过期时间、IP、UA）
    $this->userSessionsDep->rotate($session['id'], [
        'access_token_hash'  => $tokens['access_token_hash'],
        'refresh_token_hash' => $tokens['refresh_token_hash'],
        'expires_at'         => $tokens['access_expires']->toDateTimeString(),
        'refresh_expires_at' => $session['refresh_expires_at'],  // 保持原始过期时间
        'last_seen_at'       => $tokens['now']->toDateTimeString(),
        'ip'                 => $request->getRealIp(),
        'ua'                 => $request->header('user-agent'),
    ]);

    // 7. 删除旧 access_token 的 Redis 缓存
    if (!empty($session['access_token_hash'])) {
        Redis::connection('token')->del($session['access_token_hash']);
    }

    // 8. 更新 Redis 指针
    $this->updateSessionPointer($session['user_id'], $platform, $session['id']);

    return self::success([
        'access_token'      => $tokens['access_token'],
        'refresh_token'     => $tokens['refresh_token'],
        'expires_in'        => $tokens['access_ttl'],
        'refresh_expires_in' => $tokens['refresh_ttl'],
    ]);
}
```

几个关键设计：

1. **refresh_expires_at 不变**：刷新时只更新 access_token 的过期时间，refresh_token 的过期时间保持不变。这意味着 refresh_token 有一个绝对的生命周期（比如 14 天），不会因为频繁刷新而无限续期
2. **单端登录校验**：步骤 4 防止被踢的设备用 refresh_token 偷偷续期。如果 Redis 指针不指向当前会话，拒绝刷新
3. **Token 轮换**：每次刷新都生成全新的 access_token 和 refresh_token，旧的立即失效。这是 Token Rotation 策略，防止 refresh_token 泄露后被长期利用
4. **删除旧缓存**：步骤 7 删除旧 access_token 的 Redis 缓存，确保旧 Token 立即失效

## 九、登录流程：从请求到返回 Token

### 9.1 登录配置：按平台返回允许的登录方式

```php
public function getLoginConfig(): array
{
    $platform = request()->header('platform', '');
    self::throwIf(!$platform, '缺少平台标识');

    // 从 auth_platforms 表动态读取该平台允许的登录方式
    $allowedTypes = AuthPlatformService::getLoginTypes($platform);
    
    // 和系统定义的登录方式取交集，返回给前端
    $filtered = [];
    foreach (SystemEnum::$loginTypeArr as $key => $label) {
        if (\in_array($key, $allowedTypes, true)) {
            $filtered[] = ['label' => $label, 'value' => $key];
        }
    }
    return self::success(['login_type_arr' => $filtered]);
}
```

前端登录页加载时先调 `getLoginConfig`，根据返回的 `login_type_arr` 动态渲染登录方式 Tab。admin 平台可能只显示"密码登录"和"邮箱验证码"，app 平台可能还多一个"手机验证码"。

### 9.2 验证码登录 + 自动注册

```php
private function loginByCode(array $param, string $loginType, $request): array
{
    // 1. 验证码校验
    if ($loginType === SystemEnum::LOGIN_TYPE_EMAIL) {
        $cacheKey = 'email_code_' . md5($param['login_account']);
    } else {
        $cacheKey = 'phone_code_' . md5($param['login_account']);
    }

    $code = Cache::get($cacheKey);
    if (!$code || $code != $param['code']) {
        return ['error' => '验证码错误或已失效', 'user' => null];
    }
    Cache::delete($cacheKey);  // 验证码一次性使用

    // 2. 查找用户
    $user = $loginType === SystemEnum::LOGIN_TYPE_EMAIL
        ? $this->usersDep->findByEmail($param['login_account'])
        : $this->usersDep->findByPhone($param['login_account']);

    // 3. 自动注册（如果平台允许）
    if (!$user) {
        $platform = $request->header('platform');
        if (!AuthPlatformService::isRegisterEnabled($platform)) {
            return ['error' => '暂未开放注册', 'user' => null];
        }
        $user = $this->autoRegister($param['login_account'], $loginType);
    }

    return ['error' => false, 'user' => $user];
}
```

自动注册的决策完全由平台配置驱动：`AuthPlatformService::isRegisterEnabled($platform)`。admin 平台禁止注册（只能管理员手动创建账号），app 平台允许注册（用户自助注册）。

### 9.3 自动注册的幂等处理

```php
private function autoRegister(string $account, string $loginType)
{
    try {
        return $this->withTransaction(function () use ($account, $loginType) {
            $defaultRole = $this->roleDep->getDefault();
            $roleId = $defaultRole ? $defaultRole['id'] : 0;

            $userData = [
                'username' => 'User_' . rand(100000, 999999),
                'password' => null,  // 验证码注册不设密码
                'role_id'  => $roleId,
                'email'    => $loginType === SystemEnum::LOGIN_TYPE_EMAIL ? $account : null,
                'phone'    => $loginType === SystemEnum::LOGIN_TYPE_PHONE ? $account : null,
            ];
            $userId = $this->usersDep->add($userData);

            $this->userProfileDep->add([
                'user_id' => $userId,
                'avatar'  => SettingService::getDefaultAvatar(),
                'sex'     => CommonEnum::SEX_UNKNOWN,
            ]);

            return $this->usersDep->find($userId);
        });
    } catch (\Exception $e) {
        // 幂等处理：唯一键冲突时重试查找
        if ($this->isDuplicateKey($e)) {
            return $loginType === SystemEnum::LOGIN_TYPE_EMAIL
                ? $this->usersDep->findByEmail($account)
                : $this->usersDep->findByPhone($account);
        }
        return null;
    }
}
```

并发场景下，两个请求同时用同一个邮箱注册，第二个会触发唯一键冲突（`Duplicate entry`）。`isDuplicateKey` 捕获这个异常，改为查找已注册的用户返回。这就是幂等处理 — 不管调用几次，结果都一样。

## 十、DictService：动态字典的统一出口

前端所有下拉选项都从后端 `init` 接口获取，`DictService` 是字典数据的统一组装器。

### 10.1 链式调用模式

```php
class DictService
{
    public $dict = [];

    // 平台下拉（动态，从 auth_platforms 表读取）
    public function setPermissionPlatformArr()
    {
        $this->dict['permission_platform_arr'] = $this->enumToDict(
            AuthPlatformService::getPlatformMap()
        );
        return $this;
    }

    // 通用状态下拉（静态枚举）
    public function setCommonStatusArr()
    {
        $this->dict['common_status_arr'] = $this->enumToDict(CommonEnum::$statusArr);
        return $this;
    }

    // 登录方式下拉（静态枚举）
    public function setAuthPlatformLoginTypeArr()
    {
        $this->dict['auth_platform_login_type_arr'] = $this->enumToDict(
            SystemEnum::$loginTypeArr
        );
        return $this;
    }

    /**
     * 统一转换：关联数组 → [{label, value}] 数组
     */
    public function enumToDict($enum)
    {
        $res = [];
        foreach ($enum as $index => $item) {
            $res[] = ['label' => $item, 'value' => $index];
        }
        return $res;
    }

    public function getDict()
    {
        return $this->dict;
    }
}
```

使用方式：

```php
// Module 的 init 方法
public function init($request): array
{
    $data['dict'] = $this->dictService
        ->setCommonStatusArr()           // 通用状态
        ->setPermissionPlatformArr()     // 平台列表（动态）
        ->setAuthPlatformLoginTypeArr()  // 登录方式
        ->getDict();
    return self::success($data);
}
```

### 10.2 从硬编码到动态的关键变化

重构前，平台下拉是硬编码的：

```php
// 旧代码：从枚举读取
public function setPlatformArr()
{
    $this->dict['platformArr'] = $this->enumToDict(PermissionEnum::$platformArr);
    return $this;
}
```

重构后，改为从 `AuthPlatformService` 动态读取：

```php
// 新代码：从 auth_platforms 表动态读取
public function setPlatformArr()
{
    $this->dict['platformArr'] = $this->enumToDict(
        AuthPlatformService::getPlatformMap()
    );
    return $this;
}
```

`getPlatformMap()` 走三级缓存，60 秒内从内存返回，性能和读枚举一样。但好处是：新增平台后，前端下拉选项自动出现，不用改任何代码。

### 10.3 权限树中的平台标识

权限树也用到了平台映射：

```php
public function setPermissionTree()
{
    $platformMap = AuthPlatformService::getPlatformMap();
    $resCategory = array_map(function ($item) use ($platformMap) {
        $platform = $item['platform'] ?? '';
        $platformTag = $platform
            ? '[' . ($platformMap[$platform] ?? $platform) . '] '
            : '';
        return [
            'id'        => $item['id'],
            'label'     => $platformTag . $item['name'],  // [PC后台] 用户管理
            'value'     => $item['id'],
            'parent_id' => $item['parent_id'],
            'platform'  => $platform,
        ];
    }, $allPermissions);
}
```

权限树的每个节点前面会加上平台标签，比如 `[PC后台] 用户管理`、`[H5/APP] 首页`。这个标签也是动态的，平台名称改了，权限树自动更新（清一下权限树缓存就行）。

## 十一、Redis Key 全景图

整理项目中所有 Redis key，分两个连接。

### 11.1 cache 连接（平台配置 + 字典，永久缓存）

| Key | 值类型 | 说明 | 清除时机 |
|-----|--------|------|---------|
| `auth_platform_{code}` | JSON / false | 单个平台完整配置，false 表示不存在 | 该平台增删改/状态变更时 |
| `auth_platform_all` | JSON Array | 所有启用平台 code 列表 `["admin","app"]` | 任意平台变更时 |
| `auth_platform_all_map` | JSON Object | code→name 映射 `{"admin":"PC后台"}` | 任意平台变更时 |
| `dict_permission_tree` | JSON Array | 权限树结构（嵌套数组） | 权限增删改时 |
| `dict_address_tree` | JSON Array | 地址树结构 | 地址变更时 |
| `auth_perm_uid_{userId}_{platform}` | JSON Array | 用户按钮权限码数组 | 权限/角色变更时 |
| `session_stats_active` | JSON Object | 会话统计数据 | 会话撤销时 |

cache 连接的 key 都是**永久缓存**（不设 TTL），数据变更时主动清除。`auth_perm_uid_*` 例外，有 30 分钟 TTL。

### 11.2 token 连接（会话相关，有 TTL）

| Key | 值类型 | 说明 | TTL |
|-----|--------|------|-----|
| `{access_token_hash}` | 管道分隔字符串 | `userId\|expiresAt\|ip\|platform\|deviceId\|sessionId` | 30分钟，每次请求续期 |
| `cur_sess:{platform}:{userId}` | 整数 | 当前允许的 session_id（单端登录指针） | 30天 |

token 连接只有两种 key，但访问频率极高（每个认证请求都要读 `{access_token_hash}`）。

### 11.3 为什么分两个 Redis 连接？

```php
// config/redis.php
return [
    'default' => [...],  // 默认连接（通用）
    'cache'   => [...],  // 缓存连接（平台配置、字典）
    'token'   => [...],  // Token 连接（会话、指针）
];
```

分离的好处：
1. **隔离故障**：token 连接出问题不影响缓存，反之亦然
2. **独立调优**：token 连接可以配置更大的 maxmemory（会话数据量大），cache 连接可以配置更激进的淘汰策略
3. **监控清晰**：分开监控两个连接的 QPS、内存、慢查询
4. **安全隔离**：token 数据更敏感，可以配置不同的访问密码和网络策略

### 11.4 缓存 Key 命名规范

项目中 Redis key 有一个重要规范：**不使用 `:` 分隔符**。

```php
// ✗ 错误：PSR-6 缓存标准中 : 是保留字符
const CACHE_PREFIX = 'auth_platform:';

// ✓ 正确：用 _ 分隔
const CACHE_PREFIX = 'auth_platform_';
```

Webman 的 `support\Cache` 底层使用 PSR-6 兼容的缓存实现，`:` 在 PSR-6 中是保留字符，会导致异常。所以所有 cache 连接的 key 都用 `_` 分隔。

但 token 连接直接用 `Redis::connection('token')` 操作，不经过 PSR-6，所以 `cur_sess:{platform}:{userId}` 可以用 `:`。

## 十二、CacheTTLEnum：统一管理所有缓存时间

所有缓存 TTL 集中在一个枚举类里，方便全局调整：

```php
class CacheTTLEnum
{
    // 短期缓存（5分钟）
    const VERIFY_CODE = 300;          // 验证码
    const SESSION_STATS = 300;        // 会话统计

    // 中期缓存（30分钟）
    const TOKEN_SESSION = 1800;       // Token 会话缓存
    const PERMISSION_BUTTONS = 1800;  // 权限按钮码

    // 超长期缓存（30天）
    const SINGLE_SESSION_POINTER = 2592000;  // 单端登录指针

    // 永久缓存
    const PERMANENT = 0;  // 平台配置、权限树、地址树
}
```

每个常量都有明确的注释说明用途和选择该值的原因。修改 TTL 时只需要改这一个文件，所有引用处自动生效。

## 十三、迁移过程：从硬编码到动态管理

整个迁移分三步走，每一步都可以独立验证。

### 13.1 第一步：建表 + 后端 CRUD

标准的分层架构：`Model → Dep → Validate → Module → Controller → Routes`

这一步最简单，就是一个标准的 CRUD 模块。唯一的特殊点是 Dep 层的写穿缓存。

验证方式：curl 测试所有接口

```bash
# 新增平台
curl -X POST http://localhost:8787/api/admin/authPlatform/add \
  -H "Authorization: Bearer {token}" \
  -H "platform: admin" \
  -d '{"code":"mini","name":"小程序","login_types":["phone"],...}'

# 列表查询
curl http://localhost:8787/api/admin/authPlatform/list \
  -H "Authorization: Bearer {token}" \
  -H "platform: admin" \
  -d '{"current_page":1,"page_size":10}'
```

### 13.2 第二步：替换所有硬编码引用

这是工作量最大的一步。需要把所有引用 `PermissionEnum::PLATFORM_ADMIN`、`PermissionEnum::$platformArr` 的地方全部替换。

涉及的文件和改动：

| 文件 | 旧代码 | 新代码 |
|------|--------|--------|
| `CheckToken` | `PermissionEnum::ALLOWED_PLATFORMS` | `AuthPlatformService::isValidPlatform()` |
| `CheckToken` | `SettingService::getAuthPolicy()` | `AuthPlatformService::getAuthPolicy()` |
| `AuthModule` | `SettingService::getAccessTtl()` | `AuthPlatformService::getAccessTtl($platform)` |
| `TokenService` | 全局统一 TTL | `AuthPlatformService::getAccessTtl($platform)` |
| `PermissionValidate` | `PermissionEnum::ALLOWED_PLATFORMS` | `AuthPlatformService::getAllowedPlatforms()` |
| `DictService` | `PermissionEnum::$platformArr` | `AuthPlatformService::getPlatformMap()` |
| `UserSessionModule` | `PermissionEnum::$platformArr[$code]` | `AuthPlatformService::getPlatformName($code)` |
| `UsersLoginLogModule` | `PermissionEnum::$platformArr[$code]` | `AuthPlatformService::getPlatformName($code)` |

### 13.3 第三步：清理废弃代码

删除所有旧的硬编码：

```php
// 从 PermissionEnum 删除
const PLATFORM_ADMIN = 'admin';       // 删
const PLATFORM_APP = 'app';           // 删
const ALLOWED_PLATFORMS = [...];      // 删
public static $platformArr = [...];   // 删

// 从 SettingService 删除
public static function getAccessTtl() {...}      // 删
public static function getRefreshTtl() {...}     // 删
public static function getAuthPolicy() {...}     // 删
public static function isRegisterEnabled() {...} // 删
```

清理数据库中的废弃配置：

```sql
DELETE FROM system_settings WHERE setting_key IN (
    'auth.policy.mini',
    'auth.policy.app',
    'auth.policy.h5',
    'auth.policy.admin',
    'auth.default_policy',
    'refresh_ttl',
    'auth.access_ttl',
    'user.register_enabled'
);
```

8 个废弃的 key，全部删除。以后所有认证相关的配置都在 `auth_platforms` 表里。

### 13.4 第四步：前端管理页面

前端只需要一个标准的 CRUD 管理页面。关键点：

1. **所有下拉选项从 init 接口获取**，不硬编码
2. **使用 `el-select-v2`** 而不是 `el-select`（项目规范）
3. **所有文本用 `t()` 函数**，支持 i18n
4. **一个 `del` 接口同时处理单删和批量删除**

新增平台的完整流程：
1. 在认证平台管理页面加一条记录
2. 权限校验、字典下拉、TTL 配置自动生效
3. 去 APP 按钮权限页面，新平台的 tab 自动出现
4. 前端登录页调 `getLoginConfig`，新平台的登录方式自动显示

**零代码改动，纯配置驱动。**

## 十四、安全设计：Fail-Close 原则

整个认证系统遵循 **fail-close**（默认拒绝）原则：任何异常情况都拒绝访问，而不是降级放行。

### 14.1 平台头强制校验

```php
// CheckToken 中间件
$currentPlatform = $request->header('platform');
if (!$currentPlatform || !AuthPlatformService::isValidPlatform($currentPlatform)) {
    return json(['code' => ErrorCodeEnum::PARAM_ERROR, 'msg' => '无效的平台标识']);
}
```

请求头必须携带 `platform`，且必须是 `auth_platforms` 表中启用的平台。**没有默认值，没有降级逻辑**。

为什么不给默认值？因为默认值意味着"不确定请求来自哪个平台"，后续的安全策略（绑定平台、单端登录）都无法正确执行。宁可返回错误，让前端修复，也不能放行一个身份不明的请求。

### 14.2 平台未配置 = 拒绝访问

```php
// AuthPlatformService::getPlatform()
$platform = self::dep()->getByCode($code);
if (!$platform) {
    throw new BusinessException("平台 [{$code}] 未配置或已禁用，拒绝访问", 401);
}
```

如果某个平台在 `auth_platforms` 表中不存在或被禁用，所有该平台的请求都会被拒绝。这是 fail-close 的核心：**未明确允许的，一律拒绝**。

### 14.3 Token Pepper 强制配置

```php
// TokenService::hashToken()
$pepper = (string) config('app.token_pepper', '');
if ($pepper === '' || $pepper === 'change_me_to_long_random') {
    throw new \RuntimeException('TOKEN_PEPPER 未配置或不安全');
}
```

如果 `.env` 中没有配置 `TOKEN_PEPPER`，或者还是默认值，直接抛运行时异常。不会降级为不加 pepper 的哈希。

### 14.4 安全策略对比：三种绑定模式

| 策略 | 安全等级 | 适用场景 | 用户体验影响 |
|------|---------|---------|-------------|
| bind_platform | ★☆☆ | 所有平台（基本防护） | 无感知 |
| bind_device | ★★☆ | 移动端（防 Token 共享） | 换设备需重新登录 |
| bind_ip | ★★★ | 高安全后台（防 Token 泄露） | 切网络需重新登录 |

admin 平台建议开 `bind_platform`，app 平台建议开 `bind_platform + bind_device`，金融类场景可以开 `bind_ip`。

## 十五、性能对比

以一个普通的认证 API 请求为例，对比优化前后的开销：

### 15.1 单请求对比

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| Redis 查询次数（平台配置） | 2-3 次 | 0 次（内存命中） | -100% |
| 平台校验耗时 | 0.2-1.5ms | ~0ms | ~100% |
| Redis 连接池占用 | +2-3 连接 | +0 连接 | -100% |
| 总认证耗时 | 2-5ms | 0.5-1ms | -75% |

### 15.2 高并发场景

| 指标 | 优化前（1000 QPS） | 优化后（1000 QPS） |
|------|-------------------|-------------------|
| Redis 平台配置查询 | 2000-3000 次/秒 | 0 次/秒 |
| Redis 连接池压力 | 高（可能成为瓶颈） | 低（只有会话查询） |
| 平台配置变更生效延迟 | 实时 | 最大 60 秒 |

在 1000 QPS 的场景下，每秒省掉 2000-3000 次 Redis 往返。这个收益随着并发量线性增长。

### 15.3 内存开销

进程内存缓存的内存开销极小：

```
$memPlatform: 2 个平台 × ~500 字节 ≈ 1KB
$memCodes:    ["admin", "app"] ≈ 100 字节
$memMap:      {"admin":"PC后台","app":"H5/APP"} ≈ 200 字节
总计: ~1.3KB / Worker 进程
```

4 个 Worker 进程总共 ~5KB，完全可以忽略。

### 15.4 缓存命中率

正常运行时的缓存命中率：

| 缓存层 | 命中率 | 说明 |
|--------|--------|------|
| L1 进程内存 | >99.9% | 60 秒内所有请求都命中 |
| L2 Redis | >99.99% | 永久缓存，只有写操作后的第一次未命中 |
| L3 MySQL | <0.01% | 几乎不会被查到 |

### 15.5 实测基准数据

以上都是理论分析，下面是真实跑出来的数据。测试方法：在 `TestModule` 中写了一个基准测试，分别对三级缓存做循环调用，用 `hrtime(true)` 纳秒级计时。

测试环境：Windows 本地开发机，Webman 单 Worker，PHP 8.1，Redis 本地连接。

**三级缓存对比（5000 次迭代）**：

| 缓存层 | 平均耗时 | 吞吐量 | 对比 L1 |
|--------|---------|--------|---------|
| L1 进程内存 | 0.16 μs | 623 万次/秒 | — |
| L2 Redis | 121 μs | 8,260 次/秒 | 慢 754x |
| L3 MySQL | 861 μs | 1,161 次/秒 | 慢 5,366x |

**便捷方法性能（基于 L1 内存缓存，5000 次迭代）**：

| 方法 | 平均耗时 | 吞吐量 |
|------|---------|--------|
| `getPlatform()` | 0.16 μs | 623 万次/秒 |
| `getAuthPolicy()` | 0.39 μs | 258 万次/秒 |
| `getAllowedPlatforms()` | 0.15 μs | 670 万次/秒 |

**倍率关系**：

```
L1 vs L2:  754x   — 内存比 Redis 快 754 倍
L1 vs L3:  5366x  — 内存比 MySQL 快 5366 倍
L2 vs L3:  7.1x   — Redis 比 MySQL 快 7 倍
```

之前文章里说"比 Redis 快 100 倍以上"，实测是 **754 倍**。保守了。

`getAuthPolicy()` 比 `getPlatform()` 稍慢（0.39 vs 0.16 μs），因为它在内存读取之后还要做 6 个 `=== CommonEnum::YES` 的比较和数组构建。但 0.39 微秒，258 万次/秒，完全不是瓶颈。

测试代码的核心逻辑：

```php
// L1 测试：预热后循环读取（命中内存缓存）
AuthPlatformService::getPlatform($platform); // 预热
$start = hrtime(true);
for ($i = 0; $i < $iterations; $i++) {
    AuthPlatformService::getPlatform($platform);
}
$l1Time = (hrtime(true) - $start) / 1e6;

// L2 测试：每次清内存缓存，强制走 Redis
for ($i = 0; $i < $iterations; $i++) {
    AuthPlatformService::flushMemCache();
    AuthPlatformService::getPlatform($platform);
}

// L3 测试：每次清内存 + Redis，强制走 MySQL
for ($i = 0; $i < $iterations; $i++) {
    AuthPlatformService::flushMemCache();
    Cache::delete('auth_platform_' . $platform);
    AuthPlatformService::getPlatform($platform);
}
```

结论：✅ 三级缓存有效，L1(内存) < L2(Redis) < L3(MySQL)，层级分明。

## 十六、与其他方案的对比

### 16.1 vs JWT 无状态方案

JWT 的典型做法是把用户信息编码在 Token 里，服务端不存状态。

```
JWT 方案：
  登录 → 签发 JWT（payload: userId, platform, exp）
  请求 → 验证签名 + 检查 exp → 通过
  吊销 → ？？？（要么维护黑名单，要么等过期）
  单端登录 → ？？？（JWT 无法实现，除非引入服务端状态）

本项目方案：
  登录 → 生成 opaque token → 存 DB + Redis
  请求 → Redis GET → 校验策略 → 通过
  吊销 → Redis DEL → 立即生效
  单端登录 → Redis 指针 → 一行代码
```

JWT 在微服务、跨域、第三方集成场景下有优势。但对于单体后台系统，opaque token + 服务端会话更灵活、更安全。

### 16.2 vs Laravel Sanctum

Laravel Sanctum 也是 opaque token 方案，但它的 Token 管理比较简单：

```
Sanctum：
  - Token 存在 personal_access_tokens 表
  - 没有 refresh_token 机制
  - 没有平台差异化配置
  - 没有单端登录/会话上限
  - 没有多级缓存

本项目：
  - 双 Token（access + refresh）
  - 按平台差异化 TTL 和安全策略
  - 三级缓存（内存 → Redis → DB）
  - 单端登录 + FIFO 会话淘汰
  - Redis 指针机制
```

Sanctum 适合简单场景，本项目的方案适合需要精细会话控制的企业级应用。

### 16.3 vs OAuth 2.0

OAuth 2.0 是授权协议，不是认证协议。它解决的是"第三方应用如何获取用户授权"的问题，而不是"用户如何登录"的问题。

本项目的认证平台更像是一个简化版的 OAuth 2.0 Resource Owner Password Credentials Grant，但去掉了 client_id/client_secret 的概念，用 `platform` 头替代。

## 十七、总结

这次重构的核心成果：

**架构层面**：
- 数据驱动替代硬编码 — 平台配置从枚举常量迁移到数据库表，新增平台零代码改动
- 三级缓存降低延迟 — 进程内存（0ms）→ Redis（0.1ms）→ MySQL（1-5ms），充分利用 Webman 常驻进程特性
- 写穿缓存保证一致性 — 写操作同时清除 Redis + 内存，其他 Worker 进程 60 秒内自动刷新
- 统一服务层收敛调用 — `AuthPlatformService` 作为唯一出口，所有消费方不再直接读枚举或配置表

**安全层面**：
- Fail-close 设计 — 未配置的平台一律拒绝，不做降级
- Token 不存明文 — SHA256 + Pepper 哈希存储
- Token Rotation — 每次刷新都生成全新的 Token 对
- 灵活的安全策略 — 绑定平台/设备/IP，按平台独立配置

**性能层面**：
- 每请求省 2-3 次 Redis 往返
- 1000 QPS 下每秒省 2000-3000 次 Redis 查询
- 内存开销 ~5KB（4 Worker），可忽略
- 缓存命中率 >99.9%

**代码质量**：
- 严格分层：Controller → Module → Validate → Dep → Model
- 单一职责：每个类只做一件事
- 统一规范：CacheTTLEnum 管理所有 TTL，DictService 管理所有字典
- 零硬编码：前端所有下拉选项从后端 init 接口获取

架构不是一步到位的，是随着业务演进逐步优化的。从硬编码到配置表到多级缓存，每一步都是在解决当下最痛的问题。重要的不是一开始就设计出完美的架构，而是在每次迭代中让架构变得更好。

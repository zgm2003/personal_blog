---
title: 用户认证模块
published: 2026-01-14T11:00:00Z
description: 多端登录、Opaque Token 双令牌、验证码登录、自动注册的完整实现
tags: [用户, 认证, Token, 安全]
category: 智澜管理系统
draft: false
---

# 模块概述

用户认证是系统的核心模块，本实现包含：

- 多种登录方式（密码、邮箱验证码、手机验证码）
- 双令牌机制（access_token + refresh_token）
- 多端登录控制（单端互踢策略）
- 验证码登录自动注册
- Token 无感刷新

## 架构设计

```
登录请求
    ↓
验证账号密码/验证码
    ↓
生成 Token 对（access + refresh）
    ↓
创建会话记录
    ↓
返回 Token
```

---

## 后端实现

### 目录结构

```
app/module/User/
├── AuthModule.php        # 认证核心（登录/登出/刷新）
├── ProfileModule.php     # 个人资料
├── RoleModule.php        # 角色管理
├── PermissionModule.php  # 权限管理
├── UserSessionModule.php # 会话管理
└── UsersListModule.php   # 用户列表

app/service/User/
└── TokenService.php      # Token 生成/验证
```

### 登录流程

```php
public function login($request): array
{
    $param = $this->validate($request, UsersValidate::login());
    $loginType = $param['login_type'];

    // 根据登录类型验证
    if ($loginType === SystemEnum::LOGIN_TYPE_PASSWORD) {
        $result = $this->loginByPassword($param, $request);
    } else {
        $result = $this->loginByCode($param, $loginType, $request);
    }

    // 使用 throwIf 简化错误处理
    self::throwIf($result['error'], $result['error'] ?? '登录失败');

    // 创建会话，返回 Token
    return self::success($this->createSession(
        $result['user']['id'], 
        $param['login_account'], 
        $request, 
        $loginType
    ));
}
```

### 密码登录

```php
private function loginByPassword(array $param, $request): array
{
    $account = $param['login_account'];

    // 智能判断账号类型
    if (isValidEmail($account)) {
        $user = $this->usersDep->findByEmail($account);
    } elseif (is_valid_phone_number($account)) {
        $user = $this->usersDep->findByPhone($account);
    } else {
        return ['error' => '请输入正确的邮箱或手机号'];
    }

    if (!$user) {
        $this->logLoginAttempt(null, $account, 'password', $request, 0, 'account_not_found');
        return ['error' => '账号或密码错误'];  // 不暴露账号是否存在
    }

    if (!password_verify($param['password'], $user['password'])) {
        $this->logLoginAttempt($user['id'], $account, 'password', $request, 0, 'wrong_password');
        return ['error' => '账号或密码错误'];
    }

    return ['error' => null, 'user' => $user];
}
```

### 验证码登录（支持自动注册）

```php
private function loginByCode(array $param, string $loginType, $request): array
{
    // 验证码校验
    $cacheKey = $loginType === 'email' 
        ? 'email_code_' . md5($param['login_account'])
        : 'phone_code_' . md5($param['login_account']);

    $code = Cache::get($cacheKey);
    if (!$code || $code != $param['code']) {
        return ['error' => '验证码错误或已失效'];
    }
    Cache::delete($cacheKey);

    // 查找用户
    $user = $loginType === 'email'
        ? $this->usersDep->findByEmail($param['login_account'])
        : $this->usersDep->findByPhone($param['login_account']);

    // 自动注册新用户
    if (!$user) {
        $user = $this->autoRegister($param['login_account'], $loginType);
    }

    return ['error' => null, 'user' => $user];
}
```

### 自动注册

```php
private function autoRegister(string $account, string $loginType)
{
    return $this->withTransaction(function () use ($account, $loginType) {
        $defaultRole = $this->roleDep->getDefault();

        $userData = [
            'username' => 'User_' . rand(100000, 999999),
            'password' => null,  // 验证码登录无需密码
            'role_id' => $defaultRole ? $defaultRole['id'] : 0,
            'email' => $loginType === 'email' ? $account : null,
            'phone' => $loginType === 'phone' ? $account : null,
        ];
        $userId = $this->usersDep->add($userData);

        // 创建用户资料
        $this->userProfileDep->add([
            'user_id' => $userId,
            'avatar' => config('app.default_avatar'),
            'sex' => SexEnum::UNKNOWN,
        ]);

        return $this->usersDep->find($userId);
    });
}
```

### 创建会话

```php
private function createSession(int $userId, string $loginAccount, $request, string $loginType): array
{
    $platform = $request->header('platform', 'admin');
    $tokens = TokenService::generateTokenPair();

    // 单端登录策略：踢掉同平台其他会话
    $policyConfig = config('auth.policies.' . $platform);
    if (!empty($policyConfig['single_session_per_platform'])) {
        $oldSessions = $this->userSessionsDep->listActiveByUserPlatform($userId, $platform);
        foreach ($oldSessions as $old) {
            Redis::connection('token')->del($old->access_token_hash);
        }
        $this->userSessionsDep->revokeByUserPlatform($userId, $platform);
    }

    // 创建新会话
    $sessionId = $this->userSessionsDep->add([
        'user_id' => $userId,
        'access_token_hash' => $tokens['access_token_hash'],
        'refresh_token_hash' => $tokens['refresh_token_hash'],
        'platform' => $platform,
        'expires_at' => $tokens['access_expires']->toDateTimeString(),
        'refresh_expires_at' => $tokens['refresh_expires']->toDateTimeString(),
        'ip' => $request->getRealIp(),
        'ua' => $request->header('user-agent'),
    ]);

    // 更新会话指针（用于单端登录检测）
    $this->updateSessionPointer($userId, $platform, $sessionId);

    return [
        'access_token' => $tokens['access_token'],
        'refresh_token' => $tokens['refresh_token'],
        'expires_in' => $tokens['access_ttl']
    ];
}
```

### Token 刷新

```php
public function refresh($request): array
{
    $refreshToken = $request->post('refresh_token');
    self::throwIf(!$refreshToken, '缺少刷新令牌', self::CODE_UNAUTHORIZED);
    
    $hash = TokenService::hashToken($refreshToken);

    $session = $this->userSessionsDep->findValidByRefreshHash($hash);
    self::throwIf(!$session, '刷新令牌无效或已过期', self::CODE_UNAUTHORIZED);

    // 检查单端登录策略
    self::throwIf(
        !$this->checkSingleSessionPolicy($session['user_id'], $session['platform'], $session['id']),
        '账号已在其他设备登录，请重新登录',
        self::CODE_UNAUTHORIZED
    );

    // 生成新 Token 对
    $tokens = TokenService::generateTokenPair();

    // 轮换 Token（旧 Token 失效）
    $this->userSessionsDep->rotate($session['id'], [
        'access_token_hash' => $tokens['access_token_hash'],
        'refresh_token_hash' => $tokens['refresh_token_hash'],
        'expires_at' => $tokens['access_expires']->toDateTimeString(),
    ]);

    // 删除旧 Token 缓存
    Redis::connection('token')->del($session['access_token_hash']);

    return self::success([
        'access_token' => $tokens['access_token'],
        'refresh_token' => $tokens['refresh_token'],
        'expires_in' => $tokens['access_ttl']
    ]);
}
```

---

## 前端实现

### Axios 拦截器

```typescript
// 请求拦截：自动添加 Token
service.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  config.headers['platform'] = 'admin'
  return config
})

// 响应拦截：处理 401
service.interceptors.response.use(
  (res) => {
    if (res.data.code === 401) {
      return handle401(res.config)
    }
    return res.data
  },
  (error) => {
    if (error.response?.status === 401) {
      return handle401(error.config)
    }
    return Promise.reject(error)
  }
)
```

### 无感刷新

```typescript
let isRefreshing = false
let requestsQueue: Array<{ resolve: Function; reject: Function; config: any }> = []

function handle401(originalRequest: any) {
  if (originalRequest._retry) {
    logoutAndRedirect()
    return Promise.reject(new Error('Unauthorized'))
  }
  
  originalRequest._retry = true
  
  // 入队等待
  const p = new Promise((resolve, reject) => {
    requestsQueue.push({ resolve, reject, config: originalRequest })
  })
  
  // 只有第一个 401 触发刷新
  if (!isRefreshing) {
    isRefreshing = true
    
    const refreshToken = Cookies.get('refresh_token')
    if (!refreshToken) {
      logoutAndRedirect()
      return Promise.reject(new Error('No refresh token'))
    }
    
    axios.post('/api/Users/refresh', { refresh_token: refreshToken })
      .then(res => {
        const { access_token, refresh_token } = res.data.data
        Cookies.set('access_token', access_token)
        Cookies.set('refresh_token', refresh_token)
        
        isRefreshing = false
        processQueue(null, access_token)
      })
      .catch(() => {
        isRefreshing = false
        logoutAndRedirect()
      })
  }
  
  return p
}

function processQueue(error: Error | null, token: string | null) {
  requestsQueue.forEach(({ resolve, reject, config }) => {
    if (error) {
      reject(error)
    } else {
      config.headers['Authorization'] = `Bearer ${token}`
      resolve(axios(config))
    }
  })
  requestsQueue = []
}
```

---

## 安全设计

### Opaque Token（不透明令牌）

与 JWT 不同，我们使用 **Opaque Token** 方案：

```php
class TokenService
{
    // 生成随机 Token
    public static function makeToken(int $bytes = 32): string
    {
        return bin2hex(random_bytes($bytes));
    }

    // Token + Pepper 哈希存储
    public static function hashToken(string $token): string
    {
        $pepper = config('app.token_pepper');
        return hash('sha256', $token . '|' . $pepper);
    }

    public static function generateTokenPair(): array
    {
        $accessToken = self::makeToken(32);   // 64 字符
        $refreshToken = self::makeToken(64);  // 128 字符

        return [
            'access_token' => $accessToken,
            'refresh_token' => $refreshToken,
            'access_token_hash' => self::hashToken($accessToken),
            'refresh_token_hash' => self::hashToken($refreshToken),
            // ...
        ];
    }
}
```

**为什么不用 JWT？**

| 对比 | JWT | Opaque Token |
|------|-----|--------------|
| 吊销 | 困难（需黑名单） | 简单（删除记录） |
| 存储 | 无状态 | 需要服务端存储 |
| 安全 | 泄露后无法立即失效 | 可随时吊销 |
| 适用 | 微服务、跨域 | 单体应用、需要精确控制 |

后台管理系统需要精确的会话控制（单端登录、强制下线），Opaque Token 更合适。

### 双令牌机制

| Token | 有效期 | 用途 |
|-------|--------|------|
| access_token | 4 小时 | 接口鉴权 |
| refresh_token | 14 天 | 刷新 access_token |

### 单端登录策略

```php
// config/auth.php
return [
    'policies' => [
        'admin' => [
            'single_session_per_platform' => true,  // 同平台互踢
        ],
        'app' => [
            'single_session_per_platform' => false, // 允许多设备
        ],
    ],
];
```

### Token 存储策略

- **Token 本身不存数据库**，只存 SHA256 Hash（防泄露）
- **Pepper 加盐**：即使数据库泄露，也无法伪造 Token
- **Redis 缓存**：Token Hash → 用户信息（快速验证）
- **数据库存会话记录**：用于审计、管理、吊销

### 登录日志

```php
private function logLoginAttempt(?int $userId, string $account, string $type, $request, int $success, string $reason = ''): void
{
    \Webman\RedisQueue\Redis::send('user-login-log', [
        'user_id' => $userId,
        'login_account' => $account,
        'login_type' => $type,
        'platform' => $request->header('platform'),
        'ip' => $request->getRealIp(),
        'ua' => $request->header('user-agent'),
        'is_success' => $success,
        'reason' => $reason,
    ]);
}
```

---

## 数据库设计

### users 表

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(255),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    role_id INT DEFAULT 0,
    status TINYINT DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### user_sessions 表

```sql
CREATE TABLE user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    access_token_hash VARCHAR(64) NOT NULL,
    refresh_token_hash VARCHAR(64) NOT NULL,
    platform VARCHAR(20),
    device_id VARCHAR(100),
    ip VARCHAR(45),
    ua TEXT,
    expires_at TIMESTAMP,
    refresh_expires_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    is_del TINYINT DEFAULT 0,
    INDEX idx_user_platform (user_id, platform),
    INDEX idx_access_hash (access_token_hash),
    INDEX idx_refresh_hash (refresh_token_hash)
);
```

---

## 扩展方向

- OAuth2 第三方登录（微信、GitHub）
- 二次验证（2FA）
- 登录设备管理
- 异地登录提醒
- 密码强度策略

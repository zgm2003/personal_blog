---
title: 宝塔 Webhook 自动化部署
published: 2026-01-25T12:00:00Z
description: 使用宝塔面板 Git Hook 实现前端项目自动化部署，Tag 触发构建的完整实践
tags: [运维, 部署, Git]
category: DevOps
draft: false
---

# 前言

每次改完代码，手动登录服务器 `git pull` + `npm run build`，太麻烦了。

本文记录如何使用宝塔面板的 Git Hook 实现**推送即部署**，以及遇到的各种坑和解决方案。

## 部署架构

```
本地开发 → git push tag → Gitee Webhook 通知 → 宝塔接收 → git pull → npm run build → 部署完成
```

# 配置步骤

## 1. 宝塔安装 Webhook 插件

宝塔面板 → 软件商店 → 搜索 **Webhook** → 安装

## 2. 创建 Git 部署站点

宝塔面板 → 网站 → 添加站点 → **Git 创建**

- 复制宝塔生成的 SSH Key
- 添加到 Gitee 仓库的部署密钥
- 填写仓库地址和分支

**注意**：部署目录要指向**源码根目录**，不是 `dist` 目录！

```
✅ 正确：/www/wwwroot/admin_front_ts
❌ 错误：/www/wwwroot/admin_front_ts/dist
```

## 3. 配置部署脚本

在 Git 管理 → 仓库 → 添加脚本：

```bash
#!/bin/bash
cd /www/wwwroot/admin_front_ts

# 拉取代码
git pull

# 安装依赖
npm install

# 构建
npm run build
```

## 4. 配置 Gitee Webhook

Gitee 仓库 → 管理 → WebHooks → 添加：

- **URL**：宝塔提供的 Webhook 地址
- **触发事件**：选择 **Tag Push**（推荐）或 Push
- **密码**：与宝塔配置一致

### 为什么用 Tag 触发？

| 触发方式 | 优点 | 缺点 |
|----------|------|------|
| Push | 实时部署 | 太频繁，每次 commit 都触发 |
| Tag | 可控，版本化 | 需要手动打 tag |

生产环境推荐 **Tag 触发**，开发环境可以用 Push。

## 5. 打 Tag 部署

```bash
# 打标签
git tag v1.0.1

# 推送标签
git push origin v1.0.1
```

Gitee 收到 tag push → 通知宝塔 → 自动拉取构建 → 部署完成！

# 踩坑记录

## 坑1：SocketTimeoutException: connect timed out

**现象**：Gitee Webhook 返回连接超时

**原因**：
- 服务器防火墙未放行宝塔端口
- 安全组规则限制
- Webhook URL 配置错误

**解决**：
1. 确认宝塔端口对外开放
2. 云服务器安全组放行该端口
3. URL 使用公网 IP 或已解析域名

## 坑2：SSLHandshakeException 证书错误

**现象**：Gitee 无法验证服务器 SSL 证书

**原因**：宝塔使用自签名证书，Gitee 不认

**解决**：
- 方案1：Webhook URL 改用 `http://`（推荐）
- 方案2：给宝塔配置 Let's Encrypt 正规证书

## 坑3：detected dubious ownership

**现象**：

```
fatal: detected dubious ownership in repository at '/www/wwwroot/xxx'
```

**原因**：Git 2.35.2+ 安全机制，目录所有者与执行用户不匹配

**解决**：

```bash
# 系统级别配置（对所有用户生效）
git config --system --add safe.directory '*'

# 修改目录所有者
chown -R www:www /www/wwwroot/admin_front_ts
```

## 坑4：dist/.user.ini 无法删除

**现象**：Vite 构建时报错无法删除 `.user.ini`

**原因**：宝塔对 `.user.ini` 加了防篡改锁（chattr +i）

**解决**：

```bash
# 解除锁定
chattr -i /www/wwwroot/admin_front_ts/dist/.user.ini

# 再次构建即可成功
```

## 坑5：构建时 CPU 100%

**现象**：每次部署服务器 CPU 飙满

**原因**：前端构建（Vite/Webpack）是 CPU 密集型任务，小配置服务器顶满正常

**解决**：
- 方案1：接受现实，等几十秒就好
- 方案2：升级服务器配置
- 方案3：使用云端 CI/CD（如 Gitee Go）构建，只部署产物

# 多项目部署注意

如果有多个前端项目，**避免同时触发构建**，否则服务器会被打爆。

解决方案：

```bash
#!/bin/bash
LOCK_FILE="/tmp/build.lock"

# 等待锁释放
while [ -f "$LOCK_FILE" ]; do
    sleep 5
done

# 加锁
touch "$LOCK_FILE"

# 构建
npm install && npm run build

# 解锁
rm -f "$LOCK_FILE"
```

# Astro 项目部署

Astro 静态博客部署更简单：

```bash
#!/bin/bash
cd /www/wwwroot/personal-blog

git pull
pnpm install
pnpm run build
```

Nginx 配置 root 指向 `dist` 目录：

```nginx
root /www/wwwroot/personal-blog/dist;

location / {
    try_files $uri $uri/ $uri.html /index.html =404;
}
```

# 回滚方案

宝塔 Git 管理支持版本回退：

1. 进入 Git 管理 → 仓库
2. 查看历史版本
3. 点击回退到指定版本

或者手动回退：

```bash
# 回退到上一个版本
git checkout HEAD~1

# 回退到指定 tag
git checkout v1.0.0

# 重新构建
npm run build
```

# 完整流程图

```
开发完成
    ↓
git add -A && git commit -m "feat: xxx"
    ↓
git tag v1.0.1
    ↓
git push origin master --tags
    ↓
Gitee 收到 Tag Push 事件
    ↓
触发 Webhook → POST 到宝塔
    ↓
宝塔执行部署脚本
    ↓
git pull → npm install → npm run build
    ↓
构建产物输出到 dist/
    ↓
Nginx 提供静态服务
    ↓
部署完成 ✅
```

# 总结

| 项目类型 | 构建耗时 | CPU 占用 |
|----------|----------|----------|
| Vue/React 前端 | 30-60s | 高 |
| Astro 博客 | 10-20s | 中 |
| PHP 后端（Webman） | 无需构建 | 低 |

自动化部署配置一次，后续只需 `git push` 就能自动更新线上，省心省力。

遇到问题别慌，90% 都是权限和网络问题，按本文排查即可。

# 进阶：Webman 后端部署

前端部署只需要 `npm run build` 生成静态文件。但 Webman 后端是常驻内存的 PHP 进程，部署方式完全不同。

## Webman 部署脚本

```bash
#!/bin/bash
cd /www/wwwroot/admin_back

# 拉取代码
git pull

# 安装依赖（生产环境不装 dev 依赖）
composer install --no-dev --optimize-autoloader

# 平滑重启 Webman（不中断服务）
php webman reload
```

关键点：`php webman reload` 是平滑重启，不是 `restart`。reload 会等当前请求处理完再重启 worker 进程，不会丢失正在处理的请求。restart 是强制杀进程，可能导致请求中断。

## Webman 进程管理

Webman 基于 Workerman，是多进程模型。生产环境需要用 systemd 管理进程：

```ini
# /etc/systemd/system/webman.service
[Unit]
Description=Webman Server
After=network.target mysql.service redis.service

[Service]
Type=forking
User=www
Group=www
WorkingDirectory=/www/wwwroot/admin_back
ExecStart=/usr/bin/php /www/wwwroot/admin_back/start.php start -d
ExecReload=/usr/bin/php /www/wwwroot/admin_back/webman reload
ExecStop=/usr/bin/php /www/wwwroot/admin_back/webman stop
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启动
systemctl start webman

# 平滑重启
systemctl reload webman

# 查看状态
systemctl status webman

# 开机自启
systemctl enable webman
```

## Nginx 反向代理配置（完整版）

生产环境的 Nginx 配置需要考虑很多细节：

```nginx
# 前端静态资源
server {
    listen 443 ssl http2;
    server_name admin.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # 前端静态文件
    root /www/wwwroot/admin_front_ts/dist;
    index index.html;

    # SPA 路由：所有路径都返回 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API 反向代理到 Webman
    location /api/ {
        proxy_pass http://127.0.0.1:8787;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式输出必须关闭缓冲
        proxy_buffering off;
        proxy_cache off;

        # 超时设置（AI 接口可能很慢）
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://127.0.0.1:7272;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}

# HTTP 跳转 HTTPS
server {
    listen 80;
    server_name admin.example.com;
    return 301 https://$host$request_uri;
}
```

几个容易忽略的点：

1. `proxy_buffering off` 对 SSE 接口是必须的，否则流式输出会被缓冲
2. `proxy_read_timeout 300s` 要设够长，AI 生成长文本可能需要几十秒
3. WebSocket 的 `proxy_read_timeout` 要大于心跳间隔
4. 静态资源加 `immutable` 缓存头，Vite 打包的文件名带 hash，可以永久缓存

# 进阶：Docker 容器化部署

当项目需要在多台服务器部署，或者需要快速搭建开发环境时，Docker 是更好的选择。

## docker-compose.yml

```yaml
version: '3.8'

services:
  webman:
    build:
      context: ./admin_back
      dockerfile: Dockerfile
    container_name: admin-webman
    ports:
      - "8787:8787"
      - "7272:7272"
    volumes:
      - ./admin_back:/app
      - ./admin_back/runtime:/app/runtime
    depends_on:
      - mysql
      - redis
    environment:
      - DB_HOST=mysql
      - REDIS_HOST=redis
    restart: unless-stopped
    networks:
      - admin-network

  nginx:
    image: nginx:alpine
    container_name: admin-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./admin_front_ts/dist:/usr/share/nginx/html
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - webman
    restart: unless-stopped
    networks:
      - admin-network

  mysql:
    image: mysql:8.0
    container_name: admin-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: admin
    volumes:
      - mysql-data:/var/lib/mysql
    ports:
      - "3306:3306"
    restart: unless-stopped
    networks:
      - admin-network

  redis:
    image: redis:7-alpine
    container_name: admin-redis
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - admin-network

volumes:
  mysql-data:
  redis-data:

networks:
  admin-network:
    driver: bridge
```

## Webman Dockerfile

```dockerfile
FROM php:8.1-cli

# 安装扩展
RUN apt-get update && apt-get install -y \
    libzip-dev libpng-dev libjpeg-dev libfreetype6-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install pdo_mysql redis zip gd pcntl posix

# 安装 Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /app
COPY . .

RUN composer install --no-dev --optimize-autoloader

EXPOSE 8787 7272

CMD ["php", "start.php", "start"]
```

## 一键部署脚本

```bash
#!/bin/bash
set -e

echo "=== 开始部署 ==="

# 拉取最新代码
git pull

# 前端构建
echo ">>> 构建前端..."
cd admin_front_ts
npm install
npm run build
cd ..

# 重启容器
echo ">>> 重启服务..."
docker-compose up -d --build webman
docker-compose restart nginx

echo "=== 部署完成 ==="
```

# 部署策略对比

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| 宝塔 Webhook | 单服务器、小团队 | 简单、可视化 | 不支持多服务器 |
| Docker Compose | 多环境、中型项目 | 环境一致、可复制 | 需要学习 Docker |
| K8s | 大规模、高可用 | 自动扩缩容、滚动更新 | 复杂度高 |
| CI/CD (GitHub Actions) | 开源项目、团队协作 | 自动化程度高 | 依赖外部服务 |

对于我的项目，宝塔 Webhook 用于生产环境（单服务器够用），Docker Compose 用于开发环境（一键搭建全套依赖）。

# 总结

| 项目类型 | 构建耗时 | CPU 占用 | 推荐部署方式 |
|----------|----------|----------|-------------|
| Vue/React 前端 | 30-60s | 高 | Webhook + Nginx |
| Astro 博客 | 10-20s | 中 | Webhook + Nginx |
| PHP 后端（Webman） | 无需构建 | 低 | systemd + reload |
| 全栈项目 | 1-2min | 高 | Docker Compose |

自动化部署的核心不是工具，而是流程。不管用宝塔还是 Docker，关键是让"代码提交到上线"这个过程变成一键操作，减少人为失误，提高交付效率。

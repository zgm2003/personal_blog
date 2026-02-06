---
title: 系统日志查看器
published: 2026-02-06T16:00:00Z
description: 在线查看 Webman 运行日志，支持文件切换、关键字搜索、日志级别过滤，告别 SSH 翻日志的日子
tags: [系统, 日志, 运维, DevTools]
project: 智澜管理系统
order: 56
draft: false
---

# 需求背景

Webman 框架自带按日期分割的日志系统，日志文件存放在 `runtime/logs/` 目录下：

```
runtime/logs/
├── webman-2026-02-05.log
├── webman-2026-02-06.log
├── workerman.log
└── redis-queue/
    └── ...
```

每次排查线上问题都要 SSH 上去 `tail -f` 翻文件，效率低且不方便。做一个后台日志查看器，让排查问题变得直观。

---

# 功能设计

- 左侧文件列表：展示所有日志文件，显示文件大小和修改时间，按时间倒序
- 右侧日志内容：深色终端风格，带行号显示
- 关键字搜索：支持高亮匹配
- 日志级别过滤：DEBUG / INFO / WARNING / ERROR / CRITICAL
- 行数控制：可选读取最近 100 ~ 2000 行
- 自动滚底：新加载内容自动滚到底部
- 移动端适配：文件列表可折叠，工具栏自适应换行

---

# 后端实现

## 架构分层

遵循项目的分层架构：Controller → Module → Service/Enum。

```
app/
├── controller/System/SystemLogController.php   # 接口层
├── module/System/SystemLogModule.php           # 业务逻辑
├── enum/SystemEnum.php                         # 日志级别、行数枚举
└── service/DictService.php                     # 字典服务（新增两个 set 方法）
```

## 接口设计

三个接口，全部走 POST：

| 接口 | 说明 |
|------|------|
| `/api/admin/SystemLog/init` | 获取字典数据（日志级别、行数选项） |
| `/api/admin/SystemLog/files` | 获取日志文件列表 |
| `/api/admin/SystemLog/content` | 读取日志内容（支持过滤） |

## 高效读取：tail 算法

日志文件可能很大，不能一次性 `file_get_contents` 全部读入内存。采用从文件末尾向前读取的方式：

```php
private function tailFile(string $filepath, int $lines): array
{
    $fp = fopen($filepath, 'r');
    fseek($fp, 0, SEEK_END);
    $pos = ftell($fp);
    $result = [];
    $buffer = '';

    while ($pos > 0 && count($result) < $lines) {
        $readSize = min(4096, $pos);
        $pos -= $readSize;
        fseek($fp, $pos);
        $buffer = fread($fp, $readSize) . $buffer;

        $parts = explode("\n", $buffer);
        $buffer = array_shift($parts); // 不完整的行留到下次

        foreach (array_reverse($parts) as $line) {
            if (trim($line) !== '') {
                array_unshift($result, $line);
            }
            if (count($result) >= $lines) break;
        }
    }

    fclose($fp);
    return array_slice($result, -$lines);
}
```

每次只读 4KB，从后往前拼接，内存占用极小。

## 安全防护

读取文件时做了目录穿越防护：

```php
self::throwIf(
    empty($filename) || str_contains($filename, '..') || str_contains($filename, "\0"),
    '文件名不合法'
);
```

同时限制最大读取行数为 2000，防止一次请求拖垮服务。

## 枚举管理

日志级别和行数选项通过 `SystemEnum` 维护，前端通过 `init` 接口获取，不硬编码：

```php
// SystemEnum.php
public static $logLevelArr = [
    'DEBUG'    => 'DEBUG',
    'INFO'     => 'INFO',
    'WARNING'  => 'WARNING',
    'ERROR'    => 'ERROR',
    'CRITICAL' => 'CRITICAL',
];

public static $logTailArr = [
    100  => '最近 100 行',
    300  => '最近 300 行',
    500  => '最近 500 行',
    1000 => '最近 1000 行',
    2000 => '最近 2000 行',
];
```

---

# 前端实现

## 页面结构

桌面端左右分栏布局，移动端上下堆叠：

- 左侧 280px 文件列表（`el-scrollbar`）
- 右侧日志查看器（深色背景 `#1e1e1e`，等宽字体）
- 工具栏：关键字输入、级别筛选（`el-select-v2`）、行数选择、查询/刷新按钮

## 日志级别高亮

不同级别用不同颜色区分，一眼就能看出问题：

| 级别 | 颜色 | 说明 |
|------|------|------|
| ERROR / CRITICAL | `#f48771` 红色 | 异常和堆栈信息 |
| WARNING | `#cca700` 黄色 | 警告信息 |
| INFO | `#89d185` 绿色 | 正常信息 |
| DEBUG | `#9cdcfe` 蓝色 | 调试信息 |

## 关键字高亮

搜索关键字时，匹配内容用黄色 `<mark>` 标签高亮，方便定位。对正则特殊字符做了转义处理，避免搜索 `.` `*` 等字符时报错。

## i18n 国际化

所有文案通过 `useI18n` 的 `t()` 函数获取，支持中英文切换：

```typescript
const { t } = useI18n()
// t('systemLog.sidebar.title')  → 日志文件 / Log Files
// t('systemLog.toolbar.query')  → 查询 / Query
```

## 移动端适配

- 文件列表默认隐藏，通过按钮切换显示
- 选择文件后自动收起列表
- 工具栏自适应换行
- 日志字体和间距适当缩小

---

# 菜单配置

在后台菜单管理中添加：

| 字段 | 值 |
|------|------|
| 上级菜单 | 系统管理 |
| 菜单名 | 系统日志 |
| i18n_key | `menu.system_log` |
| 路由路径 | `/system/log` |
| 组件路径 | `system/log` |
| 权限标识 | `system_log_files`、`system_log_content` |

---

# 小结

一个轻量的日志查看器，成本不高但实用性很强。核心价值在于把「SSH + tail」的操作搬到了浏览器里，配合关键字搜索和级别过滤，排查问题的效率提升明显。后续可以考虑加上日志下载和实时刷新（WebSocket 推送新日志行）。

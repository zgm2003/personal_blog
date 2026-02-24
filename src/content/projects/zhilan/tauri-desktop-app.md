---
title: Tauri 2.0 桌面端开发实战
published: 2026-01-23T18:00:00Z
description: 从零搭建 Tauri 桌面应用，涵盖系统托盘、原生通知、自动更新、打包发布全流程
tags: [Tauri, 桌面端, Rust, 跨端]
project: 智澜管理系统
order: 100
draft: false
---

# 为什么选择 Tauri？

Electron 太重，打包后几百 MB。Tauri 用 Rust + WebView，打包只有 10MB 左右，启动秒开。

CloudAdmin 管理系统本身是 Vue3 + Vite 的 Web 项目，接入 Tauri 实现桌面端"零改造"——前端代码完全复用。

## 项目结构

```
admin_front_ts/
├── src/                    # Vue3 前端代码
├── src-tauri/              # Tauri/Rust 代码
│   ├── src/
│   │   └── lib.rs          # 核心逻辑
│   ├── capabilities/       # 权限配置
│   ├── Cargo.toml          # Rust 依赖
│   └── tauri.conf.json     # Tauri 配置
├── package.json
└── vite.config.ts
```

**双端共用**：一套代码，`npm run dev` 是 Web，`npm run tauri dev` 是桌面端。

---

# 核心功能实现

## 1. 系统托盘

**需求**：
- 关闭窗口 → 最小化到托盘（不退出）
- 左键托盘 → 唤醒窗口
- 右键托盘 → 菜单（显示窗口、退出）

```rust
use tauri::{
    AppHandle, Manager,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};

pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // 创建菜单
            let show = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &quit])?;

            // 创建托盘
            TrayIconBuilder::with_id("main")
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .show_menu_on_left_click(false)  // 关键：左键不弹菜单
                .tooltip("CloudAdmin")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => wake_window(app),
                    "quit" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    // 左键唤醒
                    if let TrayIconEvent::Click { 
                        button: MouseButton::Left, 
                        button_state: MouseButtonState::Up, .. 
                    } = event {
                        wake_window(tray.app_handle());
                    }
                })
                .build(app)?;
            Ok(())
        })
        .on_window_event(|window, event| {
            // 关闭时隐藏而非退出
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                api.prevent_close();
                let _ = window.hide();
            }
        })
        .run(tauri::generate_context!())
        .expect("error");
}

fn wake_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}
```

**踩坑**：`show_menu_on_left_click(false)` 是 Tauri 2.9+ 才有的，之前版本左键会闪一下菜单。

## 2. 系统通知

**需求**：窗口最小化/失焦时，用系统原生通知提醒用户。

**方案选择**：

| 方案 | 问题 |
|------|------|
| `tauri-plugin-notification` | 不支持点击事件回调 |
| `notify-rust` crate | Windows 不支持 `wait_for_action` |

**最终方案**：`notify-rust` 发通知，托盘作为唯一唤醒入口。

```rust
use notify_rust::Notification;
use std::sync::atomic::{AtomicU32, Ordering};

static UNREAD_COUNT: AtomicU32 = AtomicU32::new(0);

#[tauri::command]
fn send_notification(app: AppHandle, title: String, body: String) {
    // 更新托盘提示
    let count = UNREAD_COUNT.fetch_add(1, Ordering::SeqCst) + 1;
    if let Some(tray) = app.tray_by_id("main") {
        let _ = tray.set_tooltip(Some(&format!("CloudAdmin - {} 条新消息", count)));
    }
    // 发送通知
    std::thread::spawn(move || {
        let _ = Notification::new()
            .summary(&title)
            .body(&format!("{}\n\n点击托盘图标查看", body))
            .appname("CloudAdmin")
            .timeout(notify_rust::Timeout::Milliseconds(10000))
            .show();
    });
}
```

**前端判断**：窗口不可见时用原生通知

```typescript
// store/tauri.ts
export const isTauri = () => !!(window as any).__TAURI__

export async function shouldUseNative(): Promise<boolean> {
  if (!isTauri()) return false
  try {
    const { getCurrentWindow } = await import('@tauri-apps/api/window')
    const win = getCurrentWindow()
    const [minimized, focused, visible] = await Promise.all([
      win.isMinimized(), 
      win.isFocused(), 
      win.isVisible()
    ])
    return minimized || !focused || !visible
  } catch {
    return false
  }
}
```

**四原则**：
1. 通知只做提醒，不是交互入口
2. 托盘是唯一可靠的唤醒入口
3. 通知文案引导用户点击托盘
4. 未读数显示在托盘 tooltip

## 3. 文件下载

**问题**：Tauri WebView 的 `<a download>` 不生效。

**方案**：用 `tauri-plugin-opener` 调用系统浏览器打开。

```typescript
export const openUrl = async (url: string) => {
  if (isTauri()) {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('plugin:opener|open_url', { url })
  } else {
    window.open(url, '_blank')
  }
}
```

**规范**：URL 由后端拼接完整地址，前端直接用，不做任何拼接。

---

# 自动更新

## 后端接口

```php
public function getLatest(): array
{
    $latest = $this->tauriVersionDep->getLatest();
    if (!$latest) return self::error('暂无版本');
    
    return self::success([
        'version'      => $latest->version,
        'notes'        => $latest->notes,
        'url'          => $latest->file_url,   // 完整 URL
        'signature'    => $latest->signature,
        'force_update' => $latest->force_update,
    ]);
}
```

## 前端更新检测

```typescript
import { check } from '@tauri-apps/plugin-updater'

async function checkUpdate() {
  const update = await check()
  if (update?.available) {
    // 显示更新弹窗
    showUpdateDialog(update.version, update.body)
  }
}

async function doUpdate() {
  const update = await check()
  if (update) {
    await update.downloadAndInstall()
    await relaunch()
  }
}
```

**踩坑**：
- `tauri.conf.json` 和 `package.json` 版本号必须同步
- 签名文件（`.sig`）必须和安装包放一起
- 强制更新时必须先调用 `clientInit` 确保有版本信息

---

# 打包发布

## 配置

`tauri.conf.json`:

```json
{
  "productName": "CloudAdmin",
  "version": "1.0.0",
  "bundle": {
    "active": true,
    "targets": ["nsis"],
    "windows": {
      "certificateThumbprint": null,
      "digestAlgorithm": "sha256",
      "timestampUrl": ""
    }
  },
  "plugins": {
    "updater": {
      "pubkey": "YOUR_PUBLIC_KEY",
      "endpoints": ["https://your-api.com/api/admin/TauriVersion/getLatest"]
    }
  }
}
```

## 打包命令

```bash
# 开发
npm run tauri dev

# 生产打包
npm run tauri build
```

产物在 `src-tauri/target/release/bundle/nsis/`：
- `CloudAdmin_1.0.0_x64-setup.exe`（安装包）
- `CloudAdmin_1.0.0_x64-setup.exe.sig`（签名）

## 签名

```bash
# 生成密钥对
npx tauri signer generate -w ~/.tauri/myapp.key

# 打包时自动签名（需设置环境变量）
TAURI_SIGNING_PRIVATE_KEY=xxx npm run tauri build
```

**踩坑**：私钥丢失 = 无法发布更新，必须妥善保管！

---

# WebSocket 通知联动

通知监听现在在 `NotificationCenter` 组件内完成：

```typescript
// NotificationCenter.vue
import { onWsMessage } from '@/hooks/useWebSocket'
import { shouldUseNative } from '@/store/tauri'

let unsubscribe: (() => void) | null = null

onMounted(() => {
  unsubscribe = onWsMessage('notification', async ({ data }) => {
    unreadCount.value++
    
    if (data.level === 'urgent') {
      // Tauri 系统通知（窗口不可见时）
      if (await shouldUseNative()) {
        const { invoke } = await import('@tauri-apps/api/core')
        invoke('send_notification', { title: data.title, body: data.content })
      }
      // Web 通知
      ElNotification({ title: data.title, message: data.content, type: data.notification_type })
    }
  })
})

onUnmounted(() => unsubscribe?.())
```

**核心逻辑**：
- Web 端：始终用 `ElNotification`
- Tauri 端：窗口可见用 `ElNotification`，不可见用系统通知

> 详见《通知管理系统设计与实现》

---

# 依赖清单

`Cargo.toml`:

```toml
[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-opener = "2"
tauri-plugin-updater = "2"
tauri-plugin-process = "2"
notify-rust = "4"
```

`capabilities/default.json`:

```json
{
  "permissions": [
    "core:default",
    "opener:default",
    "updater:default",
    "process:default"
  ]
}
```

---

# 总结

| 功能 | 实现方案 |
|------|----------|
| 系统托盘 | `TrayIconBuilder` + `menu_on_left_click(false)` |
| 原生通知 | `notify-rust`（不支持点击回调） |
| 文件下载 | `tauri-plugin-opener` |
| 自动更新 | `tauri-plugin-updater` + 后端接口 |
| WebSocket | 单例连接 + 监听器清理 |

**核心原则**：
- 双端共用一套代码
- 前端用 `isTauri()` 区分环境
- 动态导入 Tauri API 避免 Web 报错
- 后端返回完整 URL，前端不拼接

---

# 下载体验

欢迎下载体验 CloudAdmin 桌面端：

- **Windows x64**: [CloudAdmin_1.0.7_x64-setup.exe](https://cos.zgm2003.cn/releases/1770644269428-CloudAdmin_1.0.7_x64-setup.exe)

安装后自动检测更新，支持系统通知、托盘最小化、异步导出推送等特性。

---
title: Tauri 2.0 桌面端深度实战：从托盘到下载管理器
published: 2026-01-23T18:00:00Z
description: 完整的 Tauri 2.0 桌面应用开发实录，涵盖下载管理器（Rust 流式下载 + 进度追踪 + 取消机制）、托盘图标闪烁、OnceLock 图标缓存、统一错误处理、远程前端加载等进阶实践
tags: [Tauri, 桌面端, Rust, 跨端]
project: 智澜管理系统
order: 100
draft: false
---

# 为什么选择 Tauri？

Electron 打包后动辄 200MB+，Tauri 用 Rust + 系统 WebView，打包只有 10MB 左右，启动秒开，内存占用低一个数量级。

CloudAdmin 管理系统本身是 Vue3 + Vite 的 Web 项目，接入 Tauri 实现桌面端"零改造"——前端代码完全复用，甚至可以直接加载远程前端，实现"壳子"模式。

## 项目结构

```
admin_front_ts/
├── src/                              # Vue3 前端代码
├── src-tauri/
│   ├── src/
│   │   ├── lib.rs                    # 主入口：托盘、通知、窗口事件、Command 注册
│   │   ├── download.rs               # 下载管理器：流式下载、进度追踪、取消
│   │   └── error.rs                  # 统一错误类型
│   ├── icons/
│   │   ├── icon.ico                  # 默认托盘图标
│   │   └── icon_notify.ico           # 通知闪烁图标
│   ├── capabilities/                 # 权限声明
│   ├── Cargo.toml
│   └── tauri.conf.json
├── src/components/DownloadManager/   # 前端下载管理组件
│   └── src/download.ts               # 统一下载 API（Tauri/Web 双端适配）
└── package.json
```

**双端共用**：`npm run dev` 是 Web，`npm run tauri dev` 是桌面端。1.0.7 版本更进一步——`frontendDist` 直接指向远程 URL，桌面端变成纯"壳子"，前端更新无需重新打包。

---

# 核心架构：模块化 Rust 后端

1.0.7 版本将 Rust 代码拆分为三个模块：

| 模块 | 职责 |
|------|------|
| `lib.rs` | 应用入口、托盘、通知、窗口事件、Command 注册 |
| `download.rs` | 下载管理器：任务创建/启动/取消/删除、流式下载、进度事件 |
| `error.rs` | 统一错误枚举 `AppError`，实现 `Serialize` 直接返回前端 |

```rust
// lib.rs 模块声明
mod download;
mod error;

use download::{DownloadManager, DownloadProgress};
use error::AppError;
```

---

# 统一错误处理：AppError

Tauri 2.x 的 Command 返回 `Result<T, E>` 时，`E` 需要实现 `Serialize`。我们定义了一个覆盖所有场景的错误枚举：

```rust
#[derive(Debug, Serialize)]
#[serde(tag = "kind", content = "message")]
pub enum AppError {
    TaskExists(String),      // 下载任务 ID 重复
    TaskNotFound(String),    // 任务不存在
    InvalidState(String),    // 状态不允许该操作
    Cancelled,               // 用户取消
    Timeout,                 // 请求超时
    Network(String),         // 网络错误
    Http(String),            // HTTP 状态码错误
    Io(String, String),      // IO 错误（上下文 + 错误信息）
    Other(String),           // 兜底
}
```

关键设计：

1. `#[serde(tag = "kind", content = "message")]` — 序列化为 `{ kind: "Network", message: "..." }` 结构，前端可以按 `kind` 分类处理
2. 提供工厂方法 `AppError::network(e: reqwest::Error)` 和 `AppError::io(context, e)` 简化构造
3. 实现 `Display` trait 用于日志输出，`Serialize` 用于前端通信，一个类型两种用途

```rust
impl AppError {
    pub fn network(e: reqwest::Error) -> Self {
        Self::Network(e.to_string())
    }
    pub fn io(context: impl Into<String>, e: std::io::Error) -> Self {
        Self::Io(context.into(), e.to_string())
    }
}
```

这样 Command 的签名就很干净：

```rust
#[tauri::command]
async fn start_download(...) -> Result<(), AppError> {
    // 所有错误自动序列化返回前端
}
```

---

# 下载管理器：完整的桌面下载体验

这是 1.0.7 最大的新功能。Tauri WebView 的 `<a download>` 不生效，之前的方案是用 `tauri-plugin-opener` 调浏览器打开——体验很差。现在实现了完整的下载管理器：Rust 端流式下载 + 进度追踪 + 取消机制，前端 Drawer 展示下载列表。

## Rust 端：download.rs 架构

### 数据结构设计

```rust
/// 下载任务状态机
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DownloadStatus {
    Pending,      // 等待开始
    Downloading,  // 下载中
    Paused,       // 已暂停
    Completed,    // 已完成
    Failed,       // 失败
    Cancelled,    // 已取消
}

/// 前端可见的进度信息
#[derive(Debug, Clone, Serialize)]
pub struct DownloadProgress {
    pub id: String,
    pub status: DownloadStatus,
    pub downloaded: u64,      // 已下载字节数
    pub total: u64,           // 总字节数
    pub speed: u64,           // 下载速度（bytes/s）
    pub progress: f64,        // 百分比 0-100
    pub filename: String,
    pub save_path: String,
    pub error: Option<String>,
}
```

### 任务内部状态：独立锁

每个任务有自己的 `Arc<Mutex<TaskState>>`，而不是整个 HashMap 共享一把锁。这样多个任务并发下载时互不阻塞：

```rust
struct DownloadTask {
    id: String,
    url: String,
    save_path: PathBuf,
    filename: String,
    cancel_flag: Arc<AtomicBool>,       // 原子取消标志
    state: Arc<Mutex<TaskState>>,       // 独立状态锁
}
```

`cancel_flag` 用 `AtomicBool` 而不是放在 `Mutex` 里，因为取消操作需要跨线程即时生效，原子操作零开销。

### DownloadManager 核心

```rust
pub struct DownloadManager {
    tasks: Mutex<HashMap<String, DownloadTask>>,
    client: Client,  // reqwest 连接池复用
}
```

`Client` 在 `new()` 时创建一次，所有下载任务共享连接池。设置 30 秒超时防止卡死：

```rust
impl DownloadManager {
    pub fn new() -> Self {
        Self {
            tasks: Mutex::new(HashMap::new()),
            client: Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .build()
                .unwrap(),
        }
    }
}
```

### 流式下载：reqwest + futures_util

下载的核心是 `download_file` 方法。用 `reqwest` 的 `bytes_stream()` 实现流式读取，避免大文件一次性加载到内存：

```rust
async fn download_file(client: &Client, ctx: &DownloadContext) -> Result<(), AppError> {
    // 1. 发起请求（带超时）
    let response = tokio::time::timeout(
        std::time::Duration::from_secs(30),
        client.get(&ctx.url).send(),
    )
    .await
    .map_err(|_| AppError::Timeout)?
    .map_err(AppError::network)?;

    // 2. 获取文件总大小
    let total_size = response.content_length().unwrap_or(0);

    // 3. 创建文件
    let mut file = File::create(&ctx.save_path)
        .map_err(|e| AppError::io("创建文件失败", e))?;

    // 4. 流式读取 + 写入
    let mut stream = response.bytes_stream();
    let mut downloaded: u64 = 0;
    let mut last_update = std::time::Instant::now();
    let mut last_downloaded = 0u64;

    while let Some(chunk_result) = stream.next().await {
        // 每个 chunk 检查取消标志
        if ctx.cancel_flag.load(Ordering::Relaxed) {
            drop(file);
            let _ = std::fs::remove_file(&ctx.save_path);  // 清理半成品
            return Err(AppError::Cancelled);
        }

        let chunk = chunk_result.map_err(AppError::network)?;
        file.write_all(&chunk)
            .map_err(|e| AppError::io("写入文件失败", e))?;
        downloaded += chunk.len() as u64;

        // 每 500ms 更新一次进度（避免事件风暴）
        let now = std::time::Instant::now();
        if now.duration_since(last_update).as_millis() >= 500 {
            let elapsed = now.duration_since(last_update).as_secs_f64();
            let speed = ((downloaded - last_downloaded) as f64 / elapsed) as u64;
            let progress = if total_size > 0 {
                (downloaded as f64 / total_size as f64) * 100.0
            } else { 0.0 };

            // 更新内部状态
            { let mut state = ctx.state.lock().unwrap();
              state.downloaded = downloaded;
              state.speed = speed;
              state.progress = progress; }

            // 通过 Tauri Event 推送到前端
            let _ = ctx.app.emit("download-progress", DownloadProgress {
                id: ctx.task_id.clone(),
                status: DownloadStatus::Downloading,
                downloaded, total: total_size, speed, progress,
                filename: ctx.filename.clone(),
                save_path: ctx.save_path.to_string_lossy().to_string(),
                error: None,
            });

            last_update = now;
            last_downloaded = downloaded;
        }
    }

    file.flush().map_err(|e| AppError::io("保存文件失败", e))?;
    Ok(())
}
```

几个关键设计点：

1. **500ms 节流**：不是每个 chunk 都推事件，而是每 500ms 推一次，避免前端被高频事件淹没
2. **速度计算**：`(downloaded - last_downloaded) / elapsed`，基于两次更新间的增量，比累计平均更准确反映实时速度
3. **取消即清理**：取消时 `drop(file)` 释放文件句柄，然后 `remove_file` 删除半成品文件
4. **DownloadContext 收拢参数**：把 url、save_path、state、cancel_flag、app 等打包成一个结构体，避免函数签名过长

### 异步任务启动

`start_download` 的关键是"先拿锁取数据，释放锁后再 spawn"：

```rust
pub async fn start_download(&self, id: String, app: AppHandle) -> Result<(), AppError> {
    let ctx = {
        let tasks = self.tasks.lock().unwrap();
        let task = tasks.get(&id).ok_or_else(|| AppError::TaskNotFound(id.clone()))?;
        // 校验状态
        { let mut state = task.state.lock().unwrap();
          if !matches!(state.status, DownloadStatus::Pending | DownloadStatus::Paused) {
              return Err(AppError::InvalidState("任务状态不允许开始下载".into()));
          }
          state.status = DownloadStatus::Downloading; }
        // 构造上下文（clone 出来）
        DownloadContext { url: task.url.clone(), save_path: task.save_path.clone(), ... }
    }; // ← tasks 锁在这里释放

    let client = self.client.clone();
    tokio::spawn(async move {
        let result = Self::download_file(&client, &ctx).await;
        // 根据结果更新状态 + emit 事件
        match result {
            Ok(_) => { /* status = Completed, emit download-completed */ }
            Err(e) => { /* status = Failed/Cancelled, emit download-failed */ }
        }
    });
    Ok(())
}
```

这里的锁管理很重要：如果在 `tokio::spawn` 里持有 `tasks` 的锁，其他操作（如 `cancel_download`、`get_progress`）都会被阻塞。所以必须在 spawn 之前把需要的数据 clone 出来。

### 取消机制

取消是通过 `AtomicBool` 实现的协作式取消：

```rust
pub fn cancel_download(&self, id: &str) -> Result<(), AppError> {
    let tasks = self.tasks.lock().unwrap();
    let task = tasks.get(id).ok_or_else(|| AppError::TaskNotFound(id.into()))?;
    // 校验状态
    let state = task.state.lock().unwrap();
    if !matches!(state.status, DownloadStatus::Downloading | DownloadStatus::Paused) {
        return Err(AppError::InvalidState("任务状态不允许取消".into()));
    }
    drop(state);
    // 设置取消标志，下载循环会在下一个 chunk 检测到
    task.cancel_flag.store(true, Ordering::Relaxed);
    Ok(())
}
```

为什么用 `Ordering::Relaxed`？因为取消不需要严格的内存序——晚一个 chunk 检测到也完全可以接受，而 Relaxed 是开销最小的原子操作。

---

## 前端：统一下载 API

前端的 `download.ts` 实现了 Tauri/Web 双端适配，对外暴露统一接口。

### 核心类：DownloadManager

```typescript
class DownloadManager {
  private listeners: UnlistenFn[] = []
  private downloads = new Map<string, DownloadProgress>()
  private callbacks = new Map<string, { onProgress?, onCompleted?, onFailed? }>()

  constructor() {
    if (isTauri()) this.initListeners()
  }
}
```

构造时自动监听 Tauri 事件：

```typescript
private async initListeners() {
  const { listen } = await tauriEvent()

  // 进度更新
  await listen<DownloadProgress>('download-progress', (event) => {
    this.downloads.set(event.payload.id, event.payload)
    this.callbacks.get(event.payload.id)?.onProgress?.(event.payload)
  })

  // 下载完成 → 系统通知 + 点击打开文件夹
  await listen<string>('download-completed', (event) => {
    const progress = this.downloads.get(event.payload)
    if (progress) {
      ElNotification({
        title: '下载完成',
        message: `${progress.filename} 已保存到 ${progress.save_path}`,
        type: 'success',
        onClick: () => this.openFolder(progress.save_path),
      })
    }
  })

  // 下载失败（取消不提示）
  await listen<[string, string]>('download-failed', (event) => {
    const [id, error] = event.payload
    if (!error.includes('取消')) {
      ElNotification({ title: '下载失败', message: error, type: 'error' })
    }
  })
}
```

### 下载流程：保存对话框 → Rust 下载 → 事件推送

```typescript
async download(options: DownloadOptions): Promise<string> {
  if (!isTauri()) {
    window.open(options.url, '_blank')
    throw new Error('Web 环境不支持下载管理')
  }

  // 1. 弹出系统保存对话框（tauri-plugin-dialog）
  const { save } = await tauriDialog()
  const savePath = await save({
    defaultPath: suggestedFilename,
    filters: this.getFileFilters(suggestedFilename),  // 根据扩展名自动匹配过滤器
  })
  if (!savePath) throw new Error('用户取消下载')

  // 2. 生成唯一 ID
  const id = `download_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`

  // 3. 调用 Rust Command 开始下载
  await invoke('start_download', { id, url: options.url, savePath, filename })
  return id
}
```

文件类型过滤器自动匹配：

```typescript
private getFileFilters(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase()
  const filterMap: Record<string, { name: string; extensions: string[] }> = {
    'pdf': { name: 'PDF 文档', extensions: ['pdf'] },
    'xlsx': { name: 'Excel 表格', extensions: ['xls', 'xlsx'] },
    'zip': { name: '压缩文件', extensions: ['zip', 'rar', '7z'] },
    'mp4': { name: '视频文件', extensions: ['mp4', 'avi', 'mkv', 'mov'] },
    // ...
  }
  const filter = ext ? filterMap[ext] : undefined
  return filter
    ? [filter, { name: '所有文件', extensions: ['*'] }]
    : [{ name: '所有文件', extensions: ['*'] }]
}
```

### 便捷方法：downloadFile

对外暴露的最简 API，一行代码触发下载：

```typescript
export const downloadFile = async (url: string, filename?: string) => {
  if (isTauri()) {
    try {
      return await downloadManager.download({ url, filename })
    } catch (error: any) {
      if (error.message === '用户取消下载') return undefined
      throw error
    }
  }

  // Web 环境：fetch blob 强制下载（解决跨域 COS 链接 <a download> 无效的问题）
  try {
    const resp = await fetch(url)
    const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = filename || url.split('/').pop()?.split('?')[0] || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(blobUrl)
  } catch {
    window.open(url, '_blank')  // 兜底
  }
}
```

Web 端的 fetch blob 方案解决了一个常见问题：跨域 COS 链接用 `<a download>` 会变成导航而不是下载。通过 fetch 拿到 blob 再创建 Object URL，就能强制触发下载。

---

# 系统托盘：闪烁 + 缓存 + 状态清理

## 托盘图标闪烁（tokio 异步）

有新消息时托盘图标在默认图标和通知图标之间交替闪烁，类似 QQ/微信的效果：

```rust
static IS_BLINKING: AtomicBool = AtomicBool::new(false);

fn start_tray_blink(app: AppHandle) {
    // 防止重复启动
    if IS_BLINKING.swap(true, Ordering::SeqCst) {
        return;
    }

    tokio::spawn(async move {
        let mut show_normal = true;
        let mut interval = tokio::time::interval(Duration::from_millis(500));

        while IS_BLINKING.load(Ordering::SeqCst) {
            interval.tick().await;
            if let Some(tray) = app.tray_by_id("main") {
                if show_normal {
                    if let Some(icon) = app.default_window_icon() {
                        let _ = tray.set_icon(Some(icon.clone()));
                    }
                } else if let Some(icon) = get_notify_icon() {
                    let _ = tray.set_icon(Some(icon.clone()));
                }
            }
            show_normal = !show_normal;
        }
        // 停止闪烁后恢复默认图标
        restore_default_icon(&app);
    });
}
```

为什么用 `tokio::spawn` 而不是 `std::thread::spawn`？

- `tokio::time::interval` 是异步的，不占系统线程
- `std::thread::sleep` 会占用一个 OS 线程，闪烁期间这个线程什么都不干
- tokio 的 interval 在 tick 之间线程可以去做别的事

停止闪烁的时机：
- 用户点击托盘图标（`wake_window`）
- 窗口获得焦点（`WindowEvent::Focused(true)`）
- 前端调用 `clear_unread` Command

## OnceLock 图标缓存

通知图标从 ICO 文件解码，这个操作不需要每次都做。用 `OnceLock` 实现懒加载 + 永久缓存：

```rust
static NOTIFY_ICON: OnceLock<Option<Image<'static>>> = OnceLock::new();

fn get_notify_icon() -> Option<&'static Image<'static>> {
    NOTIFY_ICON.get_or_init(|| {
        let ico_bytes = include_bytes!("../icons/icon_notify.ico");
        image::load_from_memory(ico_bytes).ok().map(|img| {
            let rgba = img.to_rgba8();
            let (w, h) = rgba.dimensions();
            Image::new_owned(rgba.into_raw(), w, h)
        })
    }).as_ref()
}
```

`OnceLock` 是 Rust 1.70 引入的标准库类型，比 `lazy_static!` 更轻量：
- 线程安全的一次性初始化
- 不需要外部 crate
- `get_or_init` 保证只执行一次闭包
- `include_bytes!` 在编译时嵌入 ICO 文件，运行时零 IO

## 托盘基础功能

```rust
// 创建托盘
TrayIconBuilder::with_id("main")
    .menu(&menu)
    .show_menu_on_left_click(false)  // 左键不弹菜单（Tauri 2.9+）
    .tooltip("CloudAdmin")
    .on_menu_event(|app, event| match event.id.as_ref() {
        "show" => wake_window(app),
        "quit" => app.exit(0),
        _ => {}
    })
    .on_tray_icon_event(|tray, event| {
        if let TrayIconEvent::Click {
            button: MouseButton::Left,
            button_state: MouseButtonState::Up, ..
        } = event {
            wake_window(tray.app_handle());
        }
    })
    .build(app)?;
```

`wake_window` 做了完整的状态清理：

```rust
fn wake_window(app: &AppHandle) {
    // 清除未读状态
    UNREAD_COUNT.store(0, Ordering::SeqCst);
    IS_BLINKING.store(false, Ordering::SeqCst);
    restore_default_icon(app);

    // 重置 tooltip
    if let Some(tray) = app.tray_by_id("main") {
        let _ = tray.set_tooltip(Some("CloudAdmin"));
    }
    // 唤醒窗口
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.request_user_attention(None::<UserAttentionType>);
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
        let _ = app.emit("tray-clicked", ());  // 通知前端
    }
}
```

---

# 窗口事件：关闭 → emit + 聚焦 → 清未读

1.0.7 改变了窗口关闭的处理方式。之前是直接 `window.hide()`，现在是 emit 事件让前端决定：

```rust
.on_window_event(|window, event| {
    match event {
        tauri::WindowEvent::CloseRequested { api, .. } => {
            api.prevent_close();
            // 不再直接 hide，而是通知前端
            let _ = window.app_handle().emit("window-close-requested", ());
        }
        tauri::WindowEvent::Focused(true) => {
            // 窗口获得焦点 → 自动清除未读
            let app = window.app_handle();
            UNREAD_COUNT.store(0, Ordering::SeqCst);
            IS_BLINKING.store(false, Ordering::SeqCst);
            restore_default_icon(app);
            if let Some(tray) = app.tray_by_id("main") {
                let _ = tray.set_tooltip(Some("CloudAdmin"));
            }
        }
        _ => {}
    }
})
```

为什么要 emit 而不是直接 hide？因为前端可能需要做一些清理工作（保存草稿、断开连接等），直接 hide 会跳过这些逻辑。前端监听 `window-close-requested` 事件后自行决定是 hide 还是做其他处理。

---

# 系统通知：spawn_blocking + 闪烁联动

```rust
#[tauri::command]
fn send_notification(app: AppHandle, title: String, body: String) {
    // 1. 更新未读计数
    let count = UNREAD_COUNT.fetch_add(1, Ordering::SeqCst) + 1;

    // 2. 更新托盘 tooltip
    if let Some(tray) = app.tray_by_id("main") {
        let _ = tray.set_tooltip(Some(&format!("CloudAdmin - {} 条新消息", count)));
    }

    // 3. 请求系统级注意力（Windows 任务栏闪烁）
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.request_user_attention(Some(UserAttentionType::Critical));
    }

    // 4. 启动托盘闪烁
    start_tray_blink(app.clone());

    // 5. 发送系统通知（spawn_blocking 避免阻塞 tokio）
    tokio::task::spawn_blocking(move || {
        let _ = Notification::new()
            .summary(&title)
            .body(&format!("{}\n\n点击托盘图标查看", body))
            .appname("CloudAdmin")
            .timeout(notify_rust::Timeout::Milliseconds(10000))
            .show();
    });
}
```

为什么用 `spawn_blocking` 而不是 `std::thread::spawn`？

- `notify-rust` 的 `show()` 是同步阻塞调用（Windows 上调用 COM API）
- 如果用 `tokio::spawn` 会阻塞 tokio 的异步线程池
- `spawn_blocking` 把任务放到专门的阻塞线程池，不影响异步任务调度
- 比 `std::thread::spawn` 更好，因为 tokio 的阻塞线程池有上限管理，不会无限创建线程

前端判断是否使用原生通知：

```typescript
export async function shouldUseNative(): Promise<boolean> {
  if (!isTauri()) return false
  const { getCurrentWindow } = await import('@tauri-apps/api/window')
  const win = getCurrentWindow()
  const [minimized, focused, visible] = await Promise.all([
    win.isMinimized(), win.isFocused(), win.isVisible()
  ])
  return minimized || !focused || !visible
}
```

三个条件任一满足就用原生通知：最小化、失焦、不可见。

---

# 远程前端加载

1.0.7 的一个重要变化是 `frontendDist` 从本地路径改为远程 URL：

```json
{
  "build": {
    "beforeBuildCommand": "",
    "frontendDist": "https://zgm2003.cn"
  }
}
```

这意味着：
- 桌面端变成纯"壳子"，只提供 Rust 原生能力
- 前端更新只需部署 Web 端，无需重新打包桌面端
- `beforeBuildCommand` 为空，打包时不再构建前端
- CSP 配置需要放行远程域名

CSP 配置：

```json
{
  "security": {
    "csp": "default-src 'self' https://zgm2003.cn https://*.zgm2003.cn; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://zgm2003.cn; style-src 'self' 'unsafe-inline' https://zgm2003.cn https://fonts.googleapis.com; connect-src 'self' https://zgm2003.cn wss://zgm2003.cn https://api.iconify.design; frame-src 'self' https: blob:"
  }
}
```

`withGlobalTauri: true` 确保远程页面也能访问 `window.__TAURI__`，前端通过 `isTauri()` 检测环境。

---

# 自动更新

更新端点改为静态 JSON 文件：

```json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://zgm2003.cn/update.json"],
      "pubkey": "dW50cnVzdGVkIGNvbW1lbnQ6..."
    }
  }
}
```

前端检测更新：

```typescript
import { check } from '@tauri-apps/plugin-updater'

async function checkUpdate() {
  const update = await check()
  if (update?.available) {
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

---

# 打开文件所在文件夹

下载完成后点击通知可以打开文件所在文件夹，跨平台实现：

```rust
#[tauri::command]
fn open_file_folder(path: String) -> Result<(), AppError> {
    #[cfg(target_os = "windows")]
    {
        // /select, 参数会在资源管理器中选中该文件
        std::process::Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| AppError::Io("打开文件夹失败".into(), e.to_string()))?;
    }

    #[cfg(target_os = "macos")]
    {
        let folder = std::path::Path::new(&path).parent().unwrap_or(std::path::Path::new(&path));
        std::process::Command::new("open").arg(folder).spawn()
            .map_err(|e| AppError::Io("打开文件夹失败".into(), e.to_string()))?;
    }

    #[cfg(target_os = "linux")]
    {
        let folder = std::path::Path::new(&path).parent().unwrap_or(std::path::Path::new(&path));
        std::process::Command::new("xdg-open").arg(folder).spawn()
            .map_err(|e| AppError::Io("打开文件夹失败".into(), e.to_string()))?;
    }

    Ok(())
}
```

Windows 的 `explorer /select,` 会直接选中文件，体验最好。macOS 和 Linux 只能打开文件夹。

---

# 依赖清单

```toml
[dependencies]
tauri = { version = "2", features = ["tray-icon"] }
tauri-plugin-opener = "2"                                    # 打开 URL
tauri-plugin-dialog = "2"                                    # 保存对话框
tauri-plugin-updater = { version = "2.9.0", features = ["native-tls"] }  # 自动更新
tauri-plugin-process = "2"                                   # 进程管理（relaunch）
notify-rust = "4"                                            # 系统通知
image = { version = "0.25.9", default-features = false, features = ["ico"] }  # ICO 解码
reqwest = { version = "0.12", features = ["stream"] }        # HTTP 流式下载
tokio = { version = "1", features = ["full"] }               # 异步运行时
futures-util = "0.3"                                         # StreamExt
serde = { version = "1", features = ["derive"] }             # 序列化
serde_json = "1"
```

相比 1.0.0 新增了 `tauri-plugin-dialog`、`image`、`reqwest`、`tokio`、`futures-util` 五个依赖，全部为下载管理器服务。

---

# 总结

| 功能 | 实现方案 | 版本 |
|------|----------|------|
| 系统托盘 | `TrayIconBuilder` + 左键唤醒 + 右键菜单 | 1.0.0 |
| 托盘闪烁 | `tokio::spawn` + `AtomicBool` + 500ms interval | 1.0.7 |
| 图标缓存 | `OnceLock<Option<Image>>` + `include_bytes!` | 1.0.7 |
| 原生通知 | `notify-rust` + `spawn_blocking` | 1.0.7 |
| 下载管理器 | `reqwest` 流式下载 + `DownloadManager` + Tauri Event | 1.0.7 |
| 文件保存 | `tauri-plugin-dialog` 系统保存对话框 | 1.0.7 |
| 打开文件夹 | `explorer /select,` / `open` / `xdg-open` | 1.0.7 |
| 错误处理 | `AppError` 枚举 + `Serialize` 直接返回前端 | 1.0.7 |
| 窗口关闭 | emit `window-close-requested` 由前端处理 | 1.0.7 |
| 聚焦清未读 | `WindowEvent::Focused(true)` 重置状态 | 1.0.7 |
| 远程前端 | `frontendDist: "https://zgm2003.cn"` | 1.0.7 |
| 自动更新 | `tauri-plugin-updater` + 静态 JSON 端点 | 1.0.0 |

核心设计原则：
- Rust 端只做原生能力（下载、通知、托盘），不做业务逻辑
- 前端通过 `isTauri()` 区分环境，动态导入 Tauri API 避免 Web 报错
- 所有 Tauri API 调用都有 Web 端降级方案
- 全局状态用原子操作（`AtomicU32`、`AtomicBool`），不用 `Mutex`
- 异步任务用 `tokio::spawn`，阻塞调用用 `spawn_blocking`

---

# 下载体验

欢迎下载体验 CloudAdmin 桌面端：

- **Windows x64**: [CloudAdmin_1.0.7_x64-setup.exe](https://cos.zgm2003.cn/releases/1770644269428-CloudAdmin_1.0.7_x64-setup.exe)

安装后自动检测更新，支持系统通知、托盘闪烁提醒、文件下载管理、异步导出推送等特性。

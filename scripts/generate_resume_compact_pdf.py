from __future__ import annotations

import html
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TMP_DIR = ROOT / "tmp" / "pdfs"
OUT_DIR = ROOT / "output" / "pdf"
HTML_OUT = TMP_DIR / "zuo-guangming-resume-compact.html"
PNG_OUT = TMP_DIR / "zuo-guangming-resume-compact-preview.png"
PDF_OUT = OUT_DIR / "zuo-guangming-resume-compact.pdf"


def esc(text: str) -> str:
    return html.escape(text, quote=True)


def li(items: list[str]) -> str:
    return "\n".join(f"<li>{item}</li>" for item in items)


def chip(items: list[str]) -> str:
    return "\n".join(f"<span>{esc(item)}</span>" for item in items)


def project(title: str, meta: str, bullets: list[str]) -> str:
    return f"""
    <div class="project">
      <div class="row-title">
        <h3>{esc(title)}</h3>
        <span>{esc(meta)}</span>
      </div>
      <ul>{li(bullets)}</ul>
    </div>
    """


def experience(company: str, title: str, time: str, bullets: list[str]) -> str:
    return f"""
    <div class="experience">
      <div class="row-title">
        <h3>{esc(company)} · {esc(title)}</h3>
        <span>{esc(time)}</span>
      </div>
      <ul>{li(bullets)}</ul>
    </div>
    """


def build_html() -> str:
    skills = {
        "AI / Agent": [
            "OpenAI-compatible",
            "Agent/Tool/Run/Step",
            "SSE streaming",
            "Tool Calling",
            "RAG pipeline",
            "AI Make Skill",
        ],
        "Frontend / Desktop": [
            "Vue 3",
            "React",
            "TypeScript",
            "Vite",
            "Element Plus",
            "Ant Design",
            "Pinia/Zustand",
            "Electron/Tauri",
        ],
        "Backend / Data": [
            "PHP 8",
            "Laravel 8",
            "Webman/Workerman",
            "MySQL",
            "Redis",
            "Redis Queue",
            "Python scripts",
            "Node.js CLI",
        ],
        "Delivery": [
            "Nginx/HTTPS",
            "API/SSE/WS",
            "COS",
            "RBAC",
            "Payment",
            "Queue jobs",
            "Contract-first",
        ],
    }

    body = f"""
    <header class="hero">
      <div>
        <h1>左光明</h1>
        <p class="role">AI Agent / Web 全栈工程师 · 2026届本科</p>
      </div>
      <div class="contact">
        <div>15671628271</div>
        <div>2093146753@qq.com</div>
        <div>武汉 / 全国 / 远程</div>
        <div>zgm2003.cn</div>
      </div>
    </header>

    <section class="summary">
      <h2>个人定位</h2>
      <p>能从前端、后端、数据库、队列、实时通信、权限、AI Agent、桌面端和部署链路把系统闭环做出来。核心优势不是只写页面或只调模型，而是把复杂业务拆成边界清楚、状态可信、可运行、可维护的工程系统。</p>
    </section>

    <section>
      <h2>技术能力</h2>
      <div class="skill-grid">
        {"".join(f'<div><strong>{esc(k)}</strong><p>{chip(v)}</p></div>' for k, v in skills.items())}
      </div>
    </section>

    <section>
      <h2>工作经历</h2>
      {experience("小药药医药科技有限公司", "前端开发", "2025.10 - 至今", [
          "从 0 搭建 SaaS 商家端 Web / Electron Desktop 前端工程，负责运行时识别、登录恢复、门店/总部工作区、权限菜单、统一请求和 CRUD 基础设施。",
          "参与荷叶问诊后台、移动端 APP、问诊内核 H5 三端迭代，覆盖远程审方、视频问诊、合理用药审查、长处方/慢病规则、移动推送和跨端跳转。",
          "在 Figma Make 生成代码质量不稳定的情况下，收口页面结构、组件边界和交互规范，避免设计稿代码污染业务层。",
      ])}
      {experience("江苏麦影网络科技有限公司", "全栈开发", "2024.06 - 2025.06", [
          "参与麦小图 VCMS 内容管理 / 发布系统，覆盖视频发布、达人运营、素材中心、数据中心、运营任务和后期流程。",
          "负责 Laravel 后端与 Electron + Vue 桌面端功能迭代，处理接口、权限、队列、Excel 导入导出、数据统计和任务状态流转。",
          "对接淘宝、京东、小红书、B 站、支付宝、得物、快手、拼多多等渠道，处理 OAuth、Cookie 注入、发布回调、账号池和平台数据同步。",
      ])}
    </section>

    <section>
      <h2>项目经历</h2>
      {project("智澜·TS 企业级 AI Admin 系统", "个人项目 / 独立全栈 / 已上线", [
          "独立完成企业级 Admin：Vue 3.5 + TypeScript + Tauri 2 + Webman + MySQL + Redis，包含认证权限、动态菜单、AI Agent、SSE、WebSocket、支付、订单、上传、通知、导出、日志和桌面端更新。",
          "设计 Agent / Model / Tool / Prompt / Conversation / Message / Run / Step 模型，让 AI 调用可追踪、可审计、可取消、可超时治理。",
          "实现 OpenAI-compatible 多模型 Provider、SSE 事件流、工具调用记录和严格前端解析；malformed payload、缺失终止事件和运行失败直接暴露。",
          "实现 Internal Tool、HTTPS 白名单 Tool、只读 SQL Tool；限制 SSRF、SQL 写操作和无限结果集，保留工具执行审计。",
          "后端坚持 Controller -> Module -> Dep -> Model 分层，Service / Lib 隔离跨模块能力与第三方 SDK；前端拆分 HTTP、Auth Session、Stream、Realtime、Router、Table/CRUD 边界。",
          "接入 Yansongda Pay，完成充值订单、支付流水、钱包入账、订单履约、支付回调、对账任务和 RedisLock 并发控制。",
          "完成域名、HTTPS、Nginx 反代、API/SSE/WS 多端口服务、MySQL、Redis、COS 静态资源与 Tauri 更新清单部署。",
      ])}

      {project("SaaS 商家端 Web / Desktop 一体化前端", "公司项目 / 前端架构与核心开发", [
          "搭建 React 19 + TypeScript + Vite + Electron 双运行链路，区分 Web、Desktop、本地后端、业务 API 等运行时基础地址。",
          "落地登录、Token 恢复、门店选择/申请、总部/门店工作区切换、权限菜单、动态路由、Zustand 状态和统一请求客户端。",
          "收口 Ant Design 与 components/ui 基础组件，沉淀 Dialog、Search、Table、Column Settings、CRUD Hook 等复用能力。",
      ])}

      {project("荷叶问诊医药 SaaS 三端协同系统", "公司项目 / 核心前端开发", [
          "覆盖 PC 管理后台、uni-app 移动端 APP、Vue 3 + Vant 问诊内核 H5，串联患者、医生、药师、商家、处方、审方、视频通话和推送。",
          "处理远程审方、合理用药审查、长处方/慢病规则、腾讯 IM / TRTC、阿里云推送、跨端页面跳转和全局错误提示。",
          "排查慢病仍提示超量问题，定位为后台慢病目录药品配置与病情选择规则不匹配，而非前端状态错误。",
      ])}

      {project("AI Make 本地 UIUX Patch Compiler", "个人项目 / Codex Skill + npm CLI", [
          "设计本地 UI 生成 Skill / CLI，把一句 UI 需求编译成 visual brief、page composition blueprint、ui-spec、prompt-pack、agent handoff、任务拆分和 review gates。",
          "支持 React + Tailwind 首条链路，约束不猜后端字段、不引入未知 UI 库、不生成巨大单文件页面，并用 write set 管理多 Agent 协作。",
      ])}
    </section>

    <section class="education">
      <h2>教育经历</h2>
      <div class="row-title">
        <h3>武汉文理学院 · 计算机科学与技术 · 本科</h3>
        <span>2026.06 毕业</span>
      </div>
    </section>
    """

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>左光明 - 简历投递版</title>
  <style>
    @page {{
      size: A4;
      margin: 8mm 9mm 9mm;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: #0f172a;
      background: #fff;
      font-family: "Source Han Sans CN", "Microsoft YaHei", "SimHei", sans-serif;
      font-size: 8.65pt;
      line-height: 1.42;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .page {{
      width: 100%;
    }}
    .hero {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10mm;
      padding-bottom: 4mm;
      border-bottom: 2px solid #0f172a;
      margin-bottom: 3.5mm;
    }}
    h1 {{
      margin: 0;
      font-size: 23pt;
      line-height: 1;
      letter-spacing: .03em;
      font-weight: 900;
    }}
    .role {{
      margin: 2mm 0 0;
      font-size: 10pt;
      font-weight: 700;
      color: #2563eb;
    }}
    .contact {{
      display: grid;
      grid-template-columns: 1fr;
      gap: .6mm;
      text-align: right;
      color: #334155;
      font-size: 8.4pt;
      white-space: nowrap;
    }}
    section {{
      margin: 0 0 3.8mm;
    }}
    h2 {{
      margin: 0 0 2mm;
      padding-bottom: .8mm;
      border-bottom: 1px solid #dbe4f0;
      font-size: 11.4pt;
      font-weight: 900;
      line-height: 1.1;
      color: #0f172a;
      page-break-after: avoid;
    }}
    h2::before {{
      content: "";
      display: inline-block;
      width: 3px;
      height: 11px;
      margin-right: 5px;
      border-radius: 999px;
      background: #2563eb;
      vertical-align: -1px;
    }}
    h3 {{
      margin: 0;
      font-size: 9.35pt;
      line-height: 1.25;
      font-weight: 900;
    }}
    p {{
      margin: 0 0 1.2mm;
    }}
    ul {{
      margin: 1.1mm 0 0;
      padding-left: 4.2mm;
    }}
    li {{
      margin: 0 0 .85mm;
      padding-left: .4mm;
    }}
    li::marker {{
      color: #2563eb;
    }}
    .summary p {{
      padding: 2.4mm 3mm;
      border-left: 3px solid #2563eb;
      border-radius: 5px;
      background: #f4f7fb;
      font-weight: 650;
    }}
    .skill-grid {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 2mm;
    }}
    .skill-grid > div {{
      padding: 2mm;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      background: #f8fafc;
    }}
    .skill-grid strong {{
      display: block;
      margin-bottom: 1.2mm;
      font-size: 8.9pt;
      color: #0f172a;
    }}
    .skill-grid p {{
      display: flex;
      flex-wrap: wrap;
      gap: .8mm;
      margin: 0;
    }}
    .skill-grid span {{
      display: inline-block;
      padding: .35mm 1mm;
      border-radius: 999px;
      color: #1d4ed8;
      background: #eaf2ff;
      font-size: 7.55pt;
      line-height: 1.25;
    }}
    .row-title {{
      display: flex;
      justify-content: space-between;
      gap: 5mm;
      align-items: baseline;
      page-break-after: avoid;
    }}
    .row-title span {{
      color: #64748b;
      font-weight: 700;
      white-space: nowrap;
      font-size: 8.2pt;
    }}
    .experience,
    .project {{
      margin-bottom: 2.4mm;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    .project:nth-of-type(1) {{
      page-break-inside: auto;
      break-inside: auto;
    }}
    .education {{
      margin-bottom: 0;
      page-break-inside: avoid;
    }}
    @media screen {{
      body {{ background: #e5ebf2; }}
      .page {{
        width: 210mm;
        min-height: 297mm;
        margin: 16px auto;
        padding: 8mm 9mm 9mm;
        background: #fff;
        box-shadow: 0 12px 34px rgba(15,23,42,.12);
      }}
    }}
  </style>
</head>
<body>
  <main class="page">{body}</main>
</body>
</html>
"""


def find_chrome() -> Path:
    for candidate in [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]:
        if candidate.exists():
            return candidate
    raise RuntimeError("Chrome/Edge executable not found.")


def run_chrome(chrome: Path, *args: str) -> None:
    subprocess.run(
        [
            str(chrome),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--allow-file-access-from-files",
            *args,
        ],
        check=True,
    )


def count_pdf_pages(pdf: Path) -> int:
    data = pdf.read_bytes().decode("latin1", errors="ignore")
    # Match page objects, not the /Pages tree object.
    return len(re.findall(r"/Type\s*/Page(?!s)\b", data))


def main() -> int:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(build_html(), encoding="utf-8")

    chrome = find_chrome()
    file_url = HTML_OUT.resolve().as_uri()
    run_chrome(chrome, f"--print-to-pdf={PDF_OUT.resolve()}", file_url)
    run_chrome(chrome, f"--screenshot={PNG_OUT.resolve()}", "--window-size=1280,1800", file_url)

    pages = count_pdf_pages(PDF_OUT)
    if pages > 3:
      raise RuntimeError(f"Compact resume is still too long: {pages} pages")
    if PDF_OUT.stat().st_size < 20_000:
      raise RuntimeError("PDF output too small; generation likely failed")

    print(f"PDF: {PDF_OUT} ({PDF_OUT.stat().st_size} bytes, {pages} pages)")
    print(f"HTML: {HTML_OUT}")
    print(f"PNG: {PNG_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

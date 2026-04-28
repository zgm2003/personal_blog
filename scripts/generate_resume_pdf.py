from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = ROOT / "src" / "content" / "spec" / "resume.md"
TMP_DIR = ROOT / "tmp" / "pdfs"
OUT_DIR = ROOT / "output" / "pdf"
HTML_OUT = TMP_DIR / "zuo-guangming-resume-print.html"
PDF_OUT = OUT_DIR / "zuo-guangming-resume.pdf"
PNG_OUT = TMP_DIR / "zuo-guangming-resume-preview.png"


def inline_markdown(text: str) -> str:
    text = html.escape(text.strip())
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>',
        text,
    )
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    chunks: list[str] = []
    paragraph: list[str] = []
    in_list = False
    current_section = ""

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            chunks.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            chunks.append("</ul>")
            in_list = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        if stripped == "---":
            flush_paragraph()
            close_list()
            chunks.append('<hr class="section-rule" />')
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            close_list()
            title = inline_markdown(stripped[2:])
            chunks.append(f'<header class="resume-hero"><h1>{title}</h1></header>')
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_list()
            chunks.append(f'<p class="tagline">{inline_markdown(stripped[1:].strip())}</p>')
            continue

        heading_match = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            level = len(heading_match.group(1))
            title = inline_markdown(heading_match.group(2))
            if level == 2:
                current_section = re.sub(r"<[^>]+>", "", title)
                chunks.append(f'<section class="section section-{slugify(current_section)}"><h2>{title}</h2>')
            elif level == 3:
                chunks.append(f'<div class="block"><h3>{title}</h3>')
            else:
                chunks.append(f"<h4>{title}</h4>")
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            if not in_list:
                list_class = "info-grid" if current_section == "基本信息" else ""
                chunks.append(f'<ul class="{list_class}">'.rstrip())
                in_list = True
            chunks.append(f"<li>{inline_markdown(stripped[2:])}</li>")
            continue

        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(chunks)


def slugify(text: str) -> str:
    mapping = {
        "基本信息": "basic",
        "个人定位": "positioning",
        "技术能力": "skills",
        "工作经历": "experience",
        "项目经历": "projects",
        "教育经历": "education",
        "我的优势": "strengths",
    }
    return mapping.get(text, "generic")


def build_html(body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>左光明 - 简历</title>
  <style>
    @page {{
      size: A4;
      margin: 11mm 11mm 12mm;
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      color: #111827;
      background: white;
      font-family: "Source Han Sans CN", "Microsoft YaHei", "SimHei", "PingFang SC", sans-serif;
      font-size: 10.2pt;
      line-height: 1.55;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    a {{
      color: #2563eb;
      text-decoration: none;
    }}
    .page {{
      width: 100%;
    }}
    .resume-hero {{
      padding: 0 0 7mm;
      border-bottom: 2px solid #1f2937;
      margin-bottom: 5mm;
    }}
    h1 {{
      margin: 0;
      font-size: 25pt;
      line-height: 1.15;
      letter-spacing: 0.02em;
      font-weight: 800;
      color: #0f172a;
    }}
    .tagline {{
      margin: -2mm 0 5mm;
      padding: 3mm 4mm;
      color: #334155;
      background: #f1f5f9;
      border-left: 3px solid #2563eb;
      border-radius: 6px;
      font-size: 10pt;
    }}
    h2 {{
      margin: 7mm 0 3mm;
      padding: 0 0 1.5mm;
      color: #0f172a;
      border-bottom: 1px solid #dbe4f0;
      font-size: 14pt;
      line-height: 1.2;
      font-weight: 800;
      page-break-after: avoid;
    }}
    h2::before {{
      content: "";
      display: inline-block;
      width: 3px;
      height: 13px;
      margin-right: 7px;
      vertical-align: -1px;
      border-radius: 99px;
      background: #2563eb;
    }}
    h3 {{
      margin: 4.5mm 0 1.5mm;
      color: #111827;
      font-size: 11.5pt;
      font-weight: 800;
      page-break-after: avoid;
    }}
    h4 {{
      margin: 3.2mm 0 1.2mm;
      color: #0f172a;
      font-size: 10.4pt;
      font-weight: 800;
      page-break-after: avoid;
    }}
    p {{
      margin: 0 0 2.2mm;
    }}
    strong {{
      font-weight: 800;
      color: #0f172a;
    }}
    code {{
      padding: 0.2mm 1mm;
      border-radius: 3px;
      color: #1d4ed8;
      background: #eff6ff;
      font-family: "JetBrains Mono", "Consolas", monospace;
      font-size: 8.7pt;
    }}
    ul {{
      margin: 0 0 2.5mm 0;
      padding-left: 4.5mm;
    }}
    li {{
      margin: 0 0 1.3mm;
      padding-left: 0.5mm;
    }}
    li::marker {{
      color: #2563eb;
    }}
    .info-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1.2mm 5mm;
      margin: 0 0 4mm;
      padding: 4mm;
      list-style: none;
      border: 1px solid #e5e7eb;
      border-radius: 8px;
      background: #f8fafc;
    }}
    .info-grid li {{
      margin: 0;
      padding: 0;
    }}
    .block {{
      page-break-inside: avoid;
      break-inside: avoid;
      margin-bottom: 2mm;
    }}
    .section-rule {{
      border: 0;
      border-top: 1px dashed #cbd5e1;
      margin: 5mm 0;
    }}
    .section-projects .block {{
      page-break-inside: auto;
      break-inside: auto;
    }}
    .section-projects h3 {{
      padding-top: 1mm;
      border-top: 1px solid #edf2f7;
    }}
    @media screen {{
      body {{
        background: #e5ebf2;
      }}
      .page {{
        width: 210mm;
        min-height: 297mm;
        margin: 16px auto;
        padding: 11mm;
        background: white;
        box-shadow: 0 12px 36px rgba(15, 23, 42, 0.12);
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    {body}
  </main>
</body>
</html>
"""


def find_chrome() -> Path:
    candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError("Chrome/Edge executable not found; cannot print PDF.")


def run_chrome(chrome: Path, *args: str) -> None:
    cmd = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--allow-file-access-from-files",
        *args,
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    if not SOURCE_MD.exists():
        raise FileNotFoundError(SOURCE_MD)

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    markdown = SOURCE_MD.read_text(encoding="utf-8")
    html_body = markdown_to_html(markdown)
    HTML_OUT.write_text(build_html(html_body), encoding="utf-8")

    chrome = find_chrome()
    file_url = HTML_OUT.resolve().as_uri()
    run_chrome(chrome, f"--print-to-pdf={PDF_OUT.resolve()}", file_url)
    run_chrome(chrome, f"--screenshot={PNG_OUT.resolve()}", "--window-size=1280,1800", file_url)

    if not PDF_OUT.exists() or PDF_OUT.stat().st_size < 20_000:
        raise RuntimeError(f"PDF generation failed or output too small: {PDF_OUT}")

    print(f"HTML: {HTML_OUT}")
    print(f"PDF:  {PDF_OUT} ({PDF_OUT.stat().st_size} bytes)")
    print(f"PNG:  {PNG_OUT} ({PNG_OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

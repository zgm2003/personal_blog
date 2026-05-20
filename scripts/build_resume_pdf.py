from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether,
    PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'pdf' / '左光明-全栈开发工程师-内容优化版.pdf'

FONT_REGULAR = r'C:\Windows\Fonts\Deng.ttf'
FONT_BOLD = r'C:\Windows\Fonts\Dengb.ttf'
FONT_LIGHT = r'C:\Windows\Fonts\Dengl.ttf'

pdfmetrics.registerFont(TTFont('Deng', FONT_REGULAR))
pdfmetrics.registerFont(TTFont('DengBold', FONT_BOLD))
pdfmetrics.registerFont(TTFont('DengLight', FONT_LIGHT))

PAGE_W, PAGE_H = A4
MARGIN_X = 15 * mm
MARGIN_TOP = 14 * mm
MARGIN_BOTTOM = 13 * mm
BLUE = colors.HexColor('#195B9C')
DARK = colors.HexColor('#182033')
MUTED = colors.HexColor('#5A6678')
LIGHT_BG = colors.HexColor('#F3F7FC')
LINE = colors.HexColor('#D8E2EF')
GREEN = colors.HexColor('#167C59')

styles = {}
styles['name'] = ParagraphStyle(
    'name', fontName='DengBold', fontSize=25, leading=28,
    textColor=colors.white, alignment=TA_LEFT, wordWrap='CJK', spaceAfter=2
)
styles['role'] = ParagraphStyle(
    'role', fontName='DengBold', fontSize=10.5, leading=14,
    textColor=colors.HexColor('#DCEBFF'), alignment=TA_LEFT, wordWrap='CJK'
)
styles['contact'] = ParagraphStyle(
    'contact', fontName='Deng', fontSize=7.6, leading=10,
    textColor=colors.HexColor('#EAF3FF'), alignment=TA_LEFT, wordWrap='CJK'
)
styles['headline'] = ParagraphStyle(
    'headline', fontName='DengBold', fontSize=9.4, leading=13.2,
    textColor=colors.white, alignment=TA_LEFT, wordWrap='CJK'
)
styles['section'] = ParagraphStyle(
    'section', fontName='DengBold', fontSize=12, leading=14.5,
    textColor=BLUE, alignment=TA_LEFT, wordWrap='CJK', spaceBefore=5, spaceAfter=4
)
styles['h3'] = ParagraphStyle(
    'h3', fontName='DengBold', fontSize=10.2, leading=13.2,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK', spaceBefore=2, spaceAfter=1
)
styles['meta'] = ParagraphStyle(
    'meta', fontName='Deng', fontSize=7.6, leading=10.3,
    textColor=MUTED, alignment=TA_LEFT, wordWrap='CJK', spaceAfter=2
)
styles['body'] = ParagraphStyle(
    'body', fontName='Deng', fontSize=8.15, leading=11.5,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK', spaceAfter=2
)
styles['body_small'] = ParagraphStyle(
    'body_small', fontName='Deng', fontSize=7.55, leading=10.5,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK', spaceAfter=1.5
)
styles['bullet'] = ParagraphStyle(
    'bullet', fontName='Deng', fontSize=8.0, leading=11.2,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK', leftIndent=8, firstLineIndent=-6, spaceAfter=1.6
)
styles['tiny'] = ParagraphStyle(
    'tiny', fontName='Deng', fontSize=6.8, leading=8.6,
    textColor=MUTED, alignment=TA_LEFT, wordWrap='CJK'
)
styles['table_head'] = ParagraphStyle(
    'table_head', fontName='DengBold', fontSize=7.4, leading=9,
    textColor=colors.white, alignment=TA_CENTER, wordWrap='CJK'
)
styles['table_cell'] = ParagraphStyle(
    'table_cell', fontName='Deng', fontSize=7.15, leading=9.2,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK'
)
styles['table_cell_bold'] = ParagraphStyle(
    'table_cell_bold', fontName='DengBold', fontSize=7.25, leading=9.2,
    textColor=DARK, alignment=TA_LEFT, wordWrap='CJK'
)

def esc(s: str) -> str:
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def P(text, style='body'):
    text = text.replace('，', '，').replace('；', '；')
    return Paragraph(text, styles[style])

def B(text):
    return f'<font name="DengBold">{esc(text)}</font>'

def bullet(text):
    return P('- ' + text, 'bullet')

def section(title):
    return KeepTogether([
        Spacer(1, 3),
        Table([[P(title, 'section')]], colWidths=[PAGE_W - 2 * MARGIN_X], style=TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 0.8, LINE),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('TOPPADDING', (0,0), (-1,-1), 0),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
        ])),
        Spacer(1, 2)
    ])

def h3(title, meta=None):
    items = [P(title, 'h3')]
    if meta:
        items.append(P(meta, 'meta'))
    return KeepTogether(items)

def skill_line(label, text):
    return P(f'{B(label)}：{esc(text)}', 'body_small')

def header_block():
    contact = '电话 15671628271   邮箱 2093146753@qq.com   武汉 / 全国 / 远程均可<br/>GitHub github.com/zgm2003   在线系统 zgm2003.cn   博客 blog.zgm2003.cn   Linux.do 三级用户'
    left = [P('左光明', 'name'), P('Go 后端 / AI 应用 / AI Agent 平台 / Vue 全栈工程师', 'role'), Spacer(1, 3), P(contact, 'contact')]
    right = [P('招聘官快速判断', 'headline'), P('实习中做医药 SaaS / 问诊多端前端工程；个人项目主线是企业级 Admin Go/Vue + AI 平台。能把认证权限、队列调度、WebSocket、AI Agent、RAG、Tool Calling、Run Monitor 和 Docker 部署做成可运行、可验证、可追问的系统。', 'contact')]
    data = [[left, right]]
    t = Table(data, colWidths=[102*mm, 63*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('BOX', (0,0), (-1,-1), 0, BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LINEBEFORE', (1,0), (1,0), 0.5, colors.HexColor('#7FA9D6')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def metrics_table():
    rows = [
        [P('Go 后端', 'table_cell_bold'), P('539 Go 文件 / 162 测试文件 / 868 测试函数 / 约 7.3 万行', 'table_cell')],
        [P('Vue 前端', 'table_cell_bold'), P('285 TS/Vue 源码文件 / 75 前端测试文件 / 约 4.4 万行', 'table_cell')],
        [P('开源项目', 'table_cell_bold'), P('chatgpt2api 133 Star / 48 Fork，覆盖 OpenAI-compatible API、gpt-image-2、注册机、号池、Docker 自托管', 'table_cell')],
    ]
    t = Table(rows, colWidths=[27*mm, 138*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EAF2FB')),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#FAFCFF')),
        ('GRID', (0,0), (-1,-1), 0.35, LINE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def repo_table():
    rows = [[P('仓库', 'table_head'), P('证明点', 'table_head')]]
    repos = [
        ('admin_go / admin_back_go / admin_front_ts', 'Go/Vue 企业级后台、认证/RBAC、AI 平台、WebSocket、Asynq、scheduler、RAG、Tool Calling、Vitest、smoke 和 Docker 部署。'),
        ('chatgpt2api', '133 Star / 48 Fork；OpenAI-compatible API、gpt-image-2 图片生成/编辑、注册自动化、账号池管理、CPA 导入和 Docker 自托管。'),
        ('rc_zuoguangming', '可靠 HTTP 通知服务；persist first、异步投递、失败重试、attempt 记录、SSRF 防护和 at-least-once 语义。'),
        ('spider_media / cine-make', '浏览器扩展媒体采集、AI 短剧预生产工具链、分镜连续性、prompt pack 和本地 Agent workflow。'),
    ]
    for a,b in repos:
        rows.append([P(a, 'table_cell_bold'), P(b, 'table_cell')])
    t = Table(rows, colWidths=[48*mm, 117*mm], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FBFF')]),
        ('GRID', (0,0), (-1,-1), 0.35, LINE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont('Deng', 7)
    canvas_obj.setFillColor(MUTED)
    canvas_obj.drawString(MARGIN_X, 8*mm, '左光明 - 全栈开发工程师简历')
    canvas_obj.drawRightString(PAGE_W - MARGIN_X, 8*mm, f'{doc.page}')
    canvas_obj.restoreState()

story = []
story.append(header_block())
story.append(Spacer(1, 5))
story.append(metrics_table())

story.append(section('求职主线'))
story += [
    bullet('目标岗位：Go 后端工程师 / AI 应用工程师 / AI Agent 平台工程师 / Vue 全栈工程师。'),
    bullet('主线能力：能把认证权限、队列调度、WebSocket 实时通信、AI Agent、工具调用、知识库、运行监控、OpenAI-compatible API、注册机、号池和前端管理台做成真实可运行、可验证、可部署的系统。'),
    bullet('最大卖点：不是只会写页面或单表 CRUD，而是能用 Go / Vue / Python / AI 把复杂后台主线、AI 平台和高热度开源项目从架构、开发、测试、部署到公开作品集完整打穿。'),
]

story.append(section('工作经历'))
story.append(h3('武汉小药药医药科技有限公司 - 前端实习生', '2025.10 - 至今 | 医药 SaaS / 互联网问诊 / 商家端后台 / 多端业务'))
story += [
    bullet('负责 SaaS 商家端前端工程建设，覆盖 Web 独立运行与 Electron Desktop 打包运行两条链路，处理接口地址、登录会话、门店/总部工作区切换、权限菜单和桌面端运行边界。'),
    bullet('负责后台核心工程能力建设，包括统一请求封装、401 refresh 队列、动态路由、按钮权限、权限快照、状态管理、CRUD Hook、表格搜索、Dialog 交互和页面基础组件收口。'),
    bullet('参与荷叶问诊后台、问诊内核 H5、移动端 APP 等多端业务迭代，覆盖远程审方、视频问诊、合理用药审查、长处方/慢病规则、移动推送、跨端跳转、订单/处方状态流转等链路。'),
    bullet('参与前后端接口联调，根据接口文档、真实请求、响应结构和页面状态定位问题，推动接口契约清晰化，避免通过前端静默兜底掩盖后端协议问题。'),
    bullet('参与 AI 生成 UI / Figma Make 代码收口，整理页面结构、组件边界、样式规范和交互细节，保证生成代码能进入真实业务工程继续维护。'),
]

story.append(section('代表项目'))
story.append(h3('智澜 Admin Go / Vue 企业级 AI 管理系统重构', '个人主导 | Go 主后端架构与实现 / Vue 前端适配 / 线上部署 | zgm2003.cn'))
story += [
    bullet('项目价值：把已有企业级 Admin 系统从 PHP/Webman 迁到 Go + Gin modular monolith，同时维护 Vue 3 + TypeScript 管理前端；覆盖登录会话、RBAC、系统配置、日志审计、队列调度、WebSocket 实时通信和 AI 平台能力。'),
    bullet('后端架构：固定 admin-api 和 admin-worker 进程边界，按 cmd -> bootstrap -> server -> module -> platform 装配；模块内部按 route -> handler -> service -> repository -> model 收口。'),
    bullet('权限核心：实现验证码、Access / Refresh Token、Token Hash + Pepper、Redis token cache、MySQL session fallback、refresh rotation、logout revoke、动态菜单、按钮权限码和 fail-closed API 权限检查。'),
    bullet('AI 平台：实现 Provider -> Agent -> Conversation -> Message -> Run -> Tool -> Knowledge 链路；Provider 密钥加密和脱敏；Chat 持久化消息，WebSocket 输出 ai.response.start/delta/completed/failed.v1 事件。'),
    bullet('Tool / RAG：Agent 绑定工具生成 OpenAI function tools，执行结果回传模型并落库 ai_tool_calls；Knowledge RAG 支持知识库、文档、chunk、检索测试、运行时注入和命中审计。'),
    bullet('实时与异步：gorilla/websocket 实现认证 upgrade、bounded send queue、心跳和慢客户端保护；Redis Pub/Sub fan-out；Asynq 处理导出、通知、AI timeout、支付定时任务；DB-backed scheduler + Redis lock 降低重复执行风险。'),
    bullet('前端交付：Vue 3 + TypeScript typed API client，AI Provider / Agent / Tool / Knowledge / Runs / Chat 页面，动态菜单和按钮权限由后端 users/init 返回，前端只负责渲染和交互。'),
    bullet('验证部署：Go test、Vitest、vue-tsc、contract check、basic/full smoke；Docker Compose 部署 admin-api / admin-worker / MySQL / Redis，宝塔/Nginx 反代和 HTTPS。'),
]

story.append(h3('医药 SaaS 商家端 / 问诊多端系统', '2025.10 - 至今 | 前端开发 / 多端联调'))
story += [
    bullet('面向医药 SaaS、互联网问诊、远程审方和商家端后台，包含 Web 商家端、Electron 桌面端、问诊后台、问诊 H5 和移动端 APP。'),
    bullet('商家端从 0 搭建 Web 与 Electron Desktop 两条运行链路，处理登录、租户/门店选择、总部/门店工作区切换、权限菜单、动态路由、按钮权限、会话恢复、统一请求和桌面端打包差异。'),
    bullet('问诊方向参与远程审方、视频问诊、合理用药审查、长处方/慢病规则、移动推送、跨端跳转、订单/处方状态流转等业务迭代。'),
]

story.append(PageBreak())
story.append(h3('ChatGPT2API / AI 账号池与 gpt-image-2 网关', '公开 fork 维护 | Python 后端改造 / React 前端联动 / 注册与号池工程化 | 133 Star / 48 Fork'))
story += [
    bullet('把 ChatGPT / OpenAI-compatible 调用、账号池、注册自动化、gpt-image-2 图片生成/编辑、在线调试页和 Docker 自托管揉成可运行系统。'),
    bullet('OpenAI-compatible 网关：把底层账号能力包装成标准接口，支持文本、图片生成/编辑、模型列表和前端调试页。'),
    bullet('注册机与账号池：维护普通注册、Codex/CPA 注册链路、邮箱/短信 OTP、账号导入、密码记录、账号管理复制入口和运行状态查看。'),
    bullet('运行时排障：围绕代理、邮箱 provider、HeroSMS、OAuth callback、token exchange、并发线程和网络失败桶做日志驱动排障；注册成功后继续验证 CPA 侧是否收到 auth 文件。'),
]

story.append(h3('AI 电商内容自动化流水线', '2025.12 - 2026.03 | Python / OCR / TTS / SRT / 模型调用'))
story += [
    bullet('面向电商商品内容生产，搭建商品采集、图片/OCR、数据清洗、卖点提取、AI 文案生成、TTS 合成、SRT 字幕和批量文件处理流程。'),
    bullet('负责 Python 自动化脚本、批处理、文件处理、接口调试和模型调用验证，将数据输入、任务排队、模型调用、结果生成、文件落盘、失败重试和人工确认串成可追踪流程。'),
]

story.append(section('技术能力'))
story += [
    skill_line('Go 后端', 'Gin、GORM、MySQL、Redis、Asynq、gocron/v2、gorilla/websocket、context、slog、table-driven tests、graceful shutdown、health/readiness。'),
    skill_line('架构与后台', 'modular monolith、middleware 顺序、route metadata、统一响应、错误处理、认证权限、RBAC、操作审计、队列任务、定时调度、上传配置、实时通信。'),
    skill_line('AI 工程', 'OpenAI-compatible API、Provider / Agent / Tool / Knowledge / Chat / Run Monitor、流式输出、Tool Calling、RAG 检索注入、模型调用审计。'),
    skill_line('前端', 'Vue 3、React、TypeScript、Vite、Element Plus、Ant Design、Vant、Tailwind CSS、Pinia、Zustand、React Query、Vue Router、React Router。'),
    skill_line('跨端', 'H5、小程序、uni-app、Capacitor、Android / iOS / 鸿蒙配置、移动推送、腾讯 IM / TRTC、Electron / Tauri。'),
    skill_line('Python / 自动化', 'FastAPI、异步服务、HTTPX、脚本自动化、数据清洗、批量文件处理、OCR/TTS/SRT 流程、pytest。'),
    skill_line('部署与中间件', 'Docker Compose、Nginx/宝塔反代、HTTPS、GitHub Actions、Redis Pub/Sub、Asynq 队列、scheduler lock、smoke 验证。'),
]

story.append(section('公开项目证据'))
story.append(repo_table())

story.append(section('教育经历'))
story.append(h3('武汉文理学院 - 计算机科学与技术 - 本科', '2024.09 - 2026.06 | 全日制 | 2026 届'))
story += [
    bullet('系统学习编程基础、数据结构、数据库、计算机网络、操作系统和软件工程；课内外长期维护个人项目和线上系统。'),
    bullet('技术文章：Go Admin Core Foundation、从调 API 到 Agent 工程化、WebSocket 实时通信架构、电商 AI 口播生成系统、Agent 工程学习路线。'),
]

story.append(section('我的优势 / 可追问点'))
story += [
    bullet('真实业务和个人项目两条线都有：实习中做医药 SaaS / 问诊多端工程，个人项目中做 Go 后台、AI 平台、队列、WebSocket、部署和开源维护。'),
    bullet('可追问点：modular monolith 取舍、Token/session 设计、route metadata 权限审计、WebSocket 多进程 fan-out、Asynq + scheduler、AI run/event/tool/retrieval 落库、前端 typed API 和权限渲染。'),
    bullet('工程习惯：不靠 any、空兜底和静默 catch 掩盖问题，优先让契约、日志、测试、smoke 和运行时事实暴露问题。'),
]


def build():
    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title='左光明-全栈开发工程师-内容优化版',
        author='左光明'
    )
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUT)

if __name__ == '__main__':
    build()

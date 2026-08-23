from pathlib import Path
import markdown, re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'publishing' / 'artifacts'

CSS = r'''
@page { size: A4; margin: 18mm 17mm 20mm 17mm;
  @bottom-center { content: counter(page); color:#65737e; font-size:8pt; }
}
@page:first { @bottom-center { content: normal; } }
* { box-sizing:border-box; }
body { font-family:"Sarasa Gothic SC","PingFang SC","Noto Sans CJK SC",sans-serif;
  color:#18242c; font-size:10pt; line-height:1.68; max-width:1040px; margin:0 auto; padding:28px 42px; }
h1,h2,h3,h4 { color:#003d5c; line-height:1.25; page-break-after:avoid; }
h1 { font-size:22pt; border-bottom:2px solid #003d5c; padding-bottom:7px; margin:36px 0 17px; page-break-before:always; }
h1:first-of-type { page-break-before:avoid; font-size:30pt; margin-top:80px; }
h2 { font-size:16pt; margin:27px 0 12px; border-bottom:1px solid #aebdc6; padding-bottom:5px; }
h3 { font-size:12.5pt; margin:20px 0 8px; }
p { margin:0 0 9px; orphans:3; widows:3; }
a { color:#005b82; text-decoration:none; overflow-wrap:anywhere; }
blockquote { margin:12px 0; padding:8px 14px; border-left:4px solid #407f9b; background:#f3f6f7; color:#3d4a52; }
pre { white-space:pre-wrap; background:#f3f5f6; border-left:3px solid #315d72; padding:10px 12px; font:8.4pt/1.48 "Sarasa Mono SC",monospace; page-break-inside:avoid; }
code { font-family:"Sarasa Mono SC",monospace; background:#f1f3f4; padding:1px 3px; }
pre code { background:none; padding:0; }
table { width:100%; border-collapse:collapse; margin:12px 0 17px; font-size:8.6pt; page-break-inside:avoid; }
th { background:#003d5c; color:white; text-align:left; }
th,td { border:1px solid #ccd5da; padding:6px 7px; vertical-align:top; }
tr:nth-child(even) td { background:#f6f8f9; }
li { margin:3px 0; }
hr { border:0; border-top:1px solid #d2dade; margin:24px 0; }
.toc { background:#f4f7f8; border-top:3px solid #003d5c; padding:16px 22px; margin:24px 0; }
.toc ul { list-style:none; padding-left:15px; }
.toc > ul { padding-left:0; }
.title-block { background:#003d5c; color:white; padding:58px 48px; margin:-28px -42px 35px; min-height:260px; }
.title-block h1 { color:white; border:0; page-break-before:avoid; margin:0 0 14px; }
.title-block .subtitle { font-size:15pt; color:#cce0ea; }
.title-block .meta { margin-top:70px; color:#c1d5df; }
@media print { body { padding:0; max-width:none; } .title-block { margin:0; min-height:240mm; page-break-after:always; } }
'''

def render(md_path, html_path, title, subtitle):
    text = md_path.read_text()
    text = re.sub(r'^---\n.*?\n---\n', '', text, count=1, flags=re.S)
    html = markdown.markdown(text, extensions=['extra','toc','sane_lists'], extension_configs={'toc': {'title':'自动目录'}})
    html = re.sub(r'<div class="toc">', '<div class="toc">', html)
    doc = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title><style>{CSS}</style></head><body><div class="title-block"><h1>{title}</h1><div class="subtitle">{subtitle}</div><div class="meta">内部研究稿<br>资料截面：2026-08-22</div></div>{html}</body></html>'''
    html_path.write_text(doc)

render(OUT/'agent_harness_book.md', OUT/'agent_harness_book.html', 'Agent Harness', '从执行脚手架到自我进化系统')
render(OUT/'executive_brief.md', OUT/'executive_brief.html', 'Agent Harness', '企业决策者精简版')

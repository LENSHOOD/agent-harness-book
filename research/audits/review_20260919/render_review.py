"""Render this audit only; never invoke or overwrite the book publication build."""
from pathlib import Path
import importlib.util
import json
import re
import markdown

HERE = Path(__file__).resolve().parent
BOOK = HERE.parents[2]
spec = importlib.util.spec_from_file_location('book_renderer', BOOK / 'publishing/scripts/render_publications.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
renderer.SNAPSHOT = '2026-09-19'

text = (HERE / 'research_report.md').read_text()
content, bibliography = text.split('## Bibliography', 1)
template = Path('/Users/xuhai.zhang/.agents/skills/deep-research/templates/mckinsey_report_template.html').read_text()
html = template.replace('lang="en"', 'lang="zh-CN"')
for key, value in {
    'TITLE': 'Agent Harness 增量研究', 'DATE': '2026-09-19', 'SOURCE_COUNT': '37',
    'METRICS_DASHBOARD': '',
    'CONTENT': markdown.markdown(content, extensions=['extra', 'sane_lists']),
    'BIBLIOGRAPHY': markdown.markdown('## Bibliography' + bibliography, extensions=['extra', 'sane_lists']),
}.items():
    html = html.replace('{{' + key + '}}', value)
html = html.replace('<h2>', '<h2 class="section-title">')
html = html.replace('<div class="section-title">Bibliography</div>', '')
html = re.sub(r'<p>(\[\d+\])', r'<p class="bib-entry">\1', html)
html = html.replace('</style>', '''
.container { max-width: 1050px; }
h2 { color: #003d5c; margin: 32px 0 16px; }
h3 { margin: 24px 0 12px; }
table { border-collapse: collapse; width: 100%; margin: 18px 0; }
td,th { padding: 10px; border: 1px solid #d1d5db; text-align: left; }
th { background: #f8f9fa; }
a { color:#005b82; overflow-wrap:anywhere; }
.content { overflow-wrap: anywhere; }
code { white-space: normal; }
@media (max-width:700px) { .content,.header { padding:20px; } table { font-size:12px; } }
</style>''')
(HERE / 'research_report.html').write_text(html)
pdf_dir = HERE / 'output/pdf'
pdf_dir.mkdir(parents=True, exist_ok=True)
work = HERE / 'tmp/pdfs'
work.mkdir(parents=True, exist_ok=True)
render_input = work / 'research_report.md'
render_input.write_text(text.replace('\u2011','-').replace('\u2013','-').replace('\u2014','-'))
renderer.render_pdf(render_input, pdf_dir / 'harness_review_research_20260919.pdf',
                    'Agent Harness Review', '增量研究 - 未完成页面视觉验收')
print(json.dumps({'html':str(HERE/'research_report.html'),
                  'pdf':str(pdf_dir/'harness_review_research_20260919.pdf')},ensure_ascii=False))

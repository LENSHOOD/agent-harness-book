"""Publication regressions checked against text recovered from a real PDF."""
from pathlib import Path
import runpy

import pdfplumber
import pytest
from reportlab.platypus import SimpleDocTemplate


ROOT = Path(__file__).resolve().parents[2]
RENDERER = runpy.run_path(str(ROOT / 'publishing/scripts/render_publications.py'))


@pytest.mark.parametrize('caption', [
    '图 5-1 Agent System 的责任边界与反馈方向',
    '图 20-1 四类可变对象共享归因、评价与发布闭环，层号不表示必经顺序',
    '图 26-1 三类案例共享的任务、执行、验证与提交骨架 & <反馈>',
])
def test_chinese_figure_caption_survives_pdf_rendering(tmp_path, caption):
    image = ROOT / 'manuscript/assets/diagrams/system-responsibility-boundary.png'
    pdf_path = tmp_path / 'caption.pdf'
    doc = SimpleDocTemplate(str(pdf_path))
    story = RENDERER['parse_markdown'](
        f'![{caption}]({image.name})', RENDERER['styles'](), doc.width, image.parent)
    doc.build(story)

    with pdfplumber.open(pdf_path) as pdf:
        text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
    assert '\x00' not in text
    assert '\ufffd' not in text
    assert ''.join(caption.split()) in ''.join(text.split())

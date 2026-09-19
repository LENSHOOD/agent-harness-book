"""PDF text/bounds checks only. This deliberately does not certify visual layout."""
from pathlib import Path
from hashlib import sha256
import json
import pdfplumber

root = Path(__file__).resolve().parent
path = root/'output/pdf/harness_review_research_20260919.pdf'
rows = []
with pdfplumber.open(path) as pdf:
    for number, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ''
        outside = [c for c in page.chars if c['x0'] < -1 or c['x1'] > page.width+1 or c['top'] < -1 or c['bottom'] > page.height+1]
        rows.append(dict(page=number, text_characters=len(text), empty=not text.strip(),
                         replacement_characters=text.count('\ufffd'), outside_page=len(outside)))
result = dict(pdf_sha256=sha256(path.read_bytes()).hexdigest(), page_count=len(rows), pages=rows,
              machine_checks_pass=all(not r['empty'] and r['replacement_characters']==0 and r['outside_page']==0 for r in rows),
              visual_acceptance='NOT_COMPLETED: current model cannot ingest rendered PNG images',
              use='Convenience reading copy only. Markdown and execution evidence remain authoritative.')
(root/'pdf_text_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
raise SystemExit(0 if result['machine_checks_pass'] else 1)

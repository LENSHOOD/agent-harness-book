"""One-time mechanical migration; preserve published slugs and historical audits."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
structure_path = ROOT / 'publishing/book_structure.json'
structure = json.loads(structure_path.read_text())
if structure.get('chapterCount') == 31:
    raise SystemExit('Already migrated; refusing to renumber twice.')

digits = '零一二三四五六七八九'
def chinese(n):
    if n < 10:
        return digits[n]
    tens, units = divmod(n, 10)
    return (digits[tens] if tens > 1 else '') + '十' + (digits[units] if units else '')

mapping = {chinese(n): chinese(n + 1) for n in range(18, 31)}
def renumber(text):
    text = re.sub(r'第([一二三四五六七八九十]+(?:[、至—－-][一二三四五六七八九十]+)*)章',
        lambda m: '第' + re.sub(r'[一二三四五六七八九十]+',
            lambda n: mapping.get(n[0], n[0]), m[1]) + '章', text)
    return re.sub(r'第([0-9]+(?:[、/至—-][0-9]+)*)章',
        lambda m: '第' + re.sub(r'[0-9]+',
            lambda n: str(int(n[0]) + 1) if 18 <= int(n[0]) <= 30 else n[0], m[1]) + '章', text)

# Workers own chapters 13..17 until their research and edits finish.
skip = {str(n).zfill(2) for n in range(13, 18)}
new_slug = '18_pi_mono_small_core_composable_session'
changed = []
for path in (ROOT / 'manuscript').rglob('*.md'):
    if path.parent.name == 'chapters' and (path.name[:2] in skip or path.stem == new_slug):
        continue
    before = path.read_text()
    after = renumber(before)
    if after != before:
        path.write_text(after)
        changed.append(str(path.relative_to(ROOT)))

for part in structure['parts']:
    for chapter in part['chapters']:
        if chapter['number'] >= 18:
            chapter['number'] += 1
            chapter['title'] = renumber(chapter['title'])
structure['parts'][2]['chapters'].insert(5, {
    'number': 18, 'slug': new_slug,
    'title': '第十八章 pi-mono：小核心怎样长成可组合的运行时',
})
structure['chapterCount'] = 31
structure['revisionDate'] = '2026-10-29'
structure['revisionScope'] = '第三篇架构重写与 pi-mono；其余篇事实截面仍为 2026-09-19'
structure_path.write_text(json.dumps(structure, ensure_ascii=False, indent=2) + '\n')

# Ledger chapter locations follow display numbering; legacy objects remain intact.
ledger = ROOT / 'research/evidence/claims_v2.jsonl'
claims = [json.loads(line) for line in ledger.read_text().splitlines() if line.strip()]
for claim in claims:
    number = str(claim.get('chapter', ''))
    if number.isdigit() and 18 <= int(number) <= 30:
        claim['chapter_before_20261029'] = number
        claim['chapter'] = str(int(number) + 1).zfill(2)
ledger.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in claims))
print(json.dumps({'updated_manuscript_files': changed, 'chapter_count': 31}, ensure_ascii=False, indent=2))

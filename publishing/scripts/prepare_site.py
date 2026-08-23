from pathlib import Path
import json, shutil, re

root = Path(__file__).resolve().parents[2]
manuscript = root / 'manuscript'
evidence = root / 'research' / 'evidence'
artifacts = root / 'publishing' / 'artifacts'
site = root / 'site' / 'docs'

for src in sorted((manuscript / 'chapters').glob('*.md')):
    shutil.copy2(src, site / 'chapters' / src.name)

for src in sorted((manuscript / 'appendices').glob('*.md')):
    shutil.copy2(src, site / 'appendices' / src.name)

brief = (artifacts / 'executive_brief.md').read_text()
brief = re.sub(r'^---\n.*?\n---\n', '# 企业决策者精简版\n\n', brief, count=1, flags=re.S)
brief = brief.replace('[TOC]\n', '')
(site / 'executive-brief.md').write_text(brief)

sources = [json.loads(x) for x in (evidence / 'sources.jsonl').read_text().splitlines() if x.strip()]
refs = ['# 完整参考文献', '', f'本书共登记 {len(sources)} 个主要来源。产品事实以 2026-08-22 为时间截面。', '']
for i, s in enumerate(sources, 1):
    authors = s.get('authors') or '机构/作者未登记'
    year = s.get('year') or 'n.d.'
    refs.append(f"{i}. {authors} ({year}). [{s['title']}]({s['raw_url']})")
(site / 'references.md').write_text('\n\n'.join(refs) + '\n')

for name in ['agent_harness_book.pdf', 'executive_brief.pdf']:
    shutil.copy2(artifacts / name, site / 'public' / 'downloads' / name)

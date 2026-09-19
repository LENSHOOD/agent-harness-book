from pathlib import Path
import json, shutil, re

root = Path(__file__).resolve().parents[2]
manuscript = root / 'manuscript'
evidence = root / 'research' / 'evidence'
artifacts = root / 'publishing' / 'artifacts'
site = root / 'site' / 'docs'

for directory in ['chapters', 'parts', 'appendices']:
    target = site / directory
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

for src in sorted((manuscript / 'chapters').glob('*.md')):
    shutil.copy2(src, site / 'chapters' / src.name)

for src in sorted((manuscript / 'parts').glob('*.md')):
    shutil.copy2(src, site / 'parts' / src.name)

for src in sorted((manuscript / 'appendices').glob('*.md')):
    shutil.copy2(src, site / 'appendices' / src.name)

assets_target = site / 'assets'
if assets_target.exists():
    shutil.rmtree(assets_target)
if (manuscript / 'assets').exists():
    shutil.copytree(manuscript / 'assets', assets_target)

brief = (artifacts / 'executive_brief.md').read_text()
brief = re.sub(r'^---\n.*?\n---\n', '# 企业决策者精简版\n\n', brief, count=1, flags=re.S)
brief = brief.replace('[TOC]\n', '')
(site / 'executive-brief.md').write_text(brief)

sources = [json.loads(x) for x in (evidence / 'sources.jsonl').read_text().splitlines() if x.strip()]
cutoff = json.loads((root / 'publishing/book_structure.json').read_text())['sourceCutoff']
verified = [s for s in sources if s.get('metadata_status') == 'verified' and s.get('core_claim_eligible', True)]
refs = ['# 已核验参考文献', '', f'研究登记表共 {len(sources)} 项，其中 {len(verified)} 项已核验身份与版本且可用于技术事实引用的来源列于下方；其余待核验或社区发现线索保留在仓库。资料维护至 {cutoff}，产品行为以各章版本为准。来源身份核验不等于全文每个结论均被独立证明。', '']
for i, s in enumerate(verified, 1):
    authors = s.get('authors') or '机构/作者未登记'
    year = s.get('year') or 'n.d.'
    refs.append(f"{i}. {authors} ({year}). [{s['title']}]({s['raw_url']})。版本：{s['version_or_commit']}；访问：{s['accessed_at']}。")
(site / 'references.md').write_text('\n\n'.join(refs) + '\n')

for name in ['agent_harness_book.pdf', 'executive_brief.pdf']:
    shutil.copy2(artifacts / name, site / 'public' / 'downloads' / name)

"""Record bounded publication checks and bind them to the final example run.

This checks PDF text geometry, not visual acceptance; it never claims to inspect
rendered PNGs on a model that cannot ingest images.
"""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import pdfplumber

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--example-run', type=Path, required=True)
    args = parser.parse_args()
    run = args.example_run.resolve()
    summary = json.loads((run/'summary.json').read_text())
    manifests = json.loads((run/'source_manifest.json').read_text())
    assert summary['exit_code'] == 0 and summary['source_unchanged_during_run']
    assert all(digest(ROOT/path) == expected for path, expected in manifests.items()), 'Source changed after final examples'
    structural = json.loads((run/'manuscript_checks.json').read_text())
    (HERE/'examples_final_summary.json').write_text(json.dumps({
        'summary':summary, 'manuscript_checks':structural,
        'source_manifest':manifests,
        'artifact_hashes':json.loads((run/'artifact_hashes.json').read_text()),
    },ensure_ascii=False,indent=2)+'\n')
    sources = [json.loads(x) for x in (ROOT/'research/evidence/sources.jsonl').read_text().splitlines()]
    claims = [json.loads(x) for x in (ROOT/'research/evidence/claims_v2.jsonl').read_text().splitlines()]
    main_files = [p for d in ('chapters','parts','appendices') for p in sorted((ROOT/'manuscript'/d).glob('*.md'))]
    cjk = lambda t: sum('\u3400' <= c <= '\u9fff' for c in t)
    no_code = lambda p: cjk(re.sub(r'```.*?```', '', p.read_text(), flags=re.S))
    evolution = sum(no_code(p) for p in main_files if p.parent.name=='chapters' and p.name[:2].isdigit() and 19<=int(p.name[:2])<=24)
    evolution_intro = no_code(ROOT/'manuscript/parts/04_evolution.md')
    total = sum(no_code(p) for p in main_files)
    copies = [(p, ROOT/'site/docs'/p.relative_to(ROOT/'manuscript')) for p in main_files]
    assert all(a.read_bytes()==b.read_bytes() for a,b in copies), 'Website source drift'
    pdf_results = {}
    for name in ('agent_harness_book.pdf','executive_brief.pdf'):
        path = ROOT/'publishing/artifacts'/name
        with pdfplumber.open(path) as document:
            pages = []
            for number, page in enumerate(document.pages, 1):
                text = page.extract_text() or ''
                outside = sum(c['x0'] < -1 or c['x1'] > page.width+1 or c['top'] < -1 or c['bottom'] > page.height+1 for c in page.chars)
                pages.append({'page':number,'text_characters':len(text),'outside_page':outside,
                              'replacement_characters':text.count('\ufffd'),'empty':not text.strip()})
            outlines = list(document.doc.get_outlines())
        result = {'pages':len(pages),'bytes':path.stat().st_size,'sha256':digest(path),
                  'outline_entries':len(outlines),'page_checks':pages,
                  'text_bounds_pass':all(not p['empty'] and not p['outside_page'] and not p['replacement_characters'] for p in pages)}
        assert result['text_bounds_pass'], (name,[p for p in pages if p['empty'] or p['outside_page'] or p['replacement_characters']])
        assert digest(ROOT/'site/docs/public/downloads'/name)==result['sha256']
        assert digest(ROOT/'site/docs/.vitepress/dist/downloads'/name)==result['sha256']
        pdf_results[name]=result
    html = '\n'.join(p.read_text() for p in (ROOT/'site/docs/.vitepress/dist').rglob('*.html'))
    assert 'href="/downloads/' not in html
    assert 'href="/agent-harness-book/downloads/agent_harness_book.pdf"' in html
    result = {'status':'PASS', 'source_cutoff':'2026-09-19','main_files':len(main_files),
              'cjk_without_fences':total,'evolution_chapters_cjk':evolution,
              'evolution_chapters_percent':round(evolution*100/total,3),
              'evolution_with_intro_percent':round((evolution+evolution_intro)*100/total,3),
              'registry':dict(Counter(s['metadata_status'] for s in sources)),
              'claims':dict(Counter(c['support_status'] for c in claims)),
              'example_tests':summary['pytest'], 'manuscript_checks':len(structural['checks']),
              'source_site_sync':'PASS','download_paths':'PASS','pdfs':pdf_results,
              'visual_acceptance':'NOT_COMPLETED: view_image explicitly returned that this model cannot ingest images; text geometry is not visual acceptance'}
    (HERE/'release_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='pdfs'},ensure_ascii=False))
    print(json.dumps({k:{x:y for x,y in v.items() if x!='page_checks'} for k,v in pdf_results.items()},ensure_ascii=False))


if __name__=='__main__':
    main()

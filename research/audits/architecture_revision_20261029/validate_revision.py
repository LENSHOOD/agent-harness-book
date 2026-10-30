"""Scoped mechanical checks; neither factual certification nor vendor E2E tests."""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
BASE = '11be2fecb5212aca11a1a76b40bd328568f0b8b2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf', action='store_true')
    args = parser.parse_args()
    structure = json.loads((ROOT / 'publishing/book_structure.json').read_text())
    previous = json.loads(subprocess.check_output(
        ['git', 'show', BASE + ':publishing/book_structure.json'], cwd=ROOT, text=True))
    chapters = [chapter for part in structure['parts'] for chapter in part['chapters']]
    previous_slugs = {chapter['slug'] for part in previous['parts'] for chapter in part['chapters']}
    current_slugs = {chapter['slug'] for chapter in chapters}
    failures = []
    if not previous_slugs <= current_slugs:
        failures.append('existing_chapter_urls_removed')
    if [chapter['number'] for chapter in chapters] != list(range(1, 32)):
        failures.append('chapter_sequence')
    cases = []
    for chapter in structure['parts'][2]['chapters'][:-1]:
        path = ROOT / 'manuscript/chapters' / (chapter['slug'] + '.md')
        body = path.read_text()
        headings = re.findall(r'^## (\d+)\. (.+)$', body, re.M)
        passed = [int(number) for number, _ in headings] == list(range(1, 9))
        passed &= '```text\n' in body
        if not passed:
            failures.append('eight_sections_and_architecture:' + chapter['slug'])
        cases.append({'chapter': chapter['number'], 'file': str(path.relative_to(ROOT)),
                      'sha256': sha(path), 'headings': [title for _, title in headings],
                      'passed': passed})
    sources = [json.loads(line) for line in (ROOT / 'research/evidence/sources.jsonl').read_text().splitlines()]
    captures, missing_captures = [], []
    for source in sources:
        if not source['source_id'].startswith('a29-'):
            continue
        capture = source.get('capture_path')
        if not capture:
            missing_captures.append(source['raw_url'])
            continue
        path = ROOT / capture
        valid = path.is_file() and sha(path) == source.get('capture_sha256')
        captures.append({'source_id': source['source_id'], 'path': capture, 'valid': valid})
        if not valid:
            failures.append('capture_hash:' + source['source_id'])
    # Short excerpts remain evidence when no full capture was saved; report this
    # separately instead of silently treating full capture completeness as passed.
    prose_files = [path for folder in ('chapters', 'parts', 'appendices')
                   for path in (ROOT / 'manuscript' / folder).glob('*.md')]
    cjk = sum(len(re.findall(r'[\u3400-\u9fff]', re.sub(r'```.*?```', '', path.read_text(), flags=re.S)))
              for path in prose_files)
    result = {'date': '2026-10-29', 'base_commit': BASE, 'chapter_count': len(chapters),
              'existing_chapter_urls_preserved': previous_slugs <= current_slugs,
              'product_cases': cases, 'capture_checks': captures,
              'sources_without_full_capture': missing_captures,
              'manuscript_files': len(prose_files), 'cjk_characters_excluding_fences': cjk,
              'pdf_checks': [], 'failures': failures,
              'scope': 'structure, stable slugs, capture bytes, PDF text/bounds; not semantic or visual proof'}
    if args.pdf:
        import pdfplumber
        for stem in ('agent_harness_book', 'executive_brief'):
            path = ROOT / 'publishing/artifacts' / (stem + '.pdf')
            pages = []
            with pdfplumber.open(path) as pdf:
                for number, page in enumerate(pdf.pages, 1):
                    text = page.extract_text() or ''
                    outside = sum(char['x0'] < -1 or char['x1'] > page.width + 1 or
                                  char['top'] < -1 or char['bottom'] > page.height + 1
                                  for char in page.chars)
                    pages.append({'page': number, 'text_characters': len(text),
                                  'empty': not text.strip(), 'outside_page': outside,
                                  'null_characters': text.count('\x00'),
                                  'replacement_characters': text.count('\ufffd')})
                outlines = len(list(pdf.doc.get_outlines()))
            passed = all(not row['empty'] and not row['outside_page'] and
                         not row['replacement_characters'] and not row['null_characters']
                         for row in pages) and outlines > 0
            if not passed:
                failures.append('pdf_text_or_bounds:' + stem)
            result['pdf_checks'].append({'file': str(path.relative_to(ROOT)), 'sha256': sha(path),
                                         'bytes': path.stat().st_size, 'page_count': len(pages),
                                         'outline_count': outlines, 'pages': pages, 'passed': passed})
    result['exit_code'] = int(bool(failures))
    (AUDIT / 'machine_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('chapter_count', 'existing_chapter_urls_preserved',
          'sources_without_full_capture', 'cjk_characters_excluding_fences', 'failures', 'exit_code')},
          ensure_ascii=False))
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())

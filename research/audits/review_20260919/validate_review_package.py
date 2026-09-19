"""Validate the Chinese review package without treating CJK text as emoji.

The upstream HTML checker uses U+24C2..U+1F251, which includes CJK characters.
We retain its other checks and replace only that predicate with explicit blocks.
The original failure and the visual-QA limit are recorded, not hidden.
"""
import contextlib
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
BOOK = ROOT.parents[2]
SKILL = Path('/Users/xuhai.zhang/.agents/skills/deep-research/scripts')


class Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.buffer = ''
        self.items = []

    def handle_starttag(self, tag, attrs):
        if tag == 'h2':
            self.inside = True
            self.buffer = ''

    def handle_data(self, data):
        if self.inside:
            self.buffer += data

    def handle_endtag(self, tag):
        if tag == 'h2':
            self.items.append(self.buffer)
            self.inside = False


def main():
    spec = importlib.util.spec_from_file_location('html_check', SKILL / 'verify_html.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    class ChineseHTMLVerifier(mod.HTMLVerifier):
        def _check_no_emojis(self, html):
            emojis = re.findall(r'[\U0001F1E6-\U0001F1FF\U0001F300-\U0001FAFF\u2600-\u27BF]', html)
            if emojis:
                self.errors.append(f'Pictographic emoji found: {len(emojis)}')

    log = io.StringIO()
    verifier = ChineseHTMLVerifier(ROOT/'research_report.html', ROOT/'research_report.md')
    with contextlib.redirect_stdout(log):
        html_pass = verifier.verify()
    (ROOT/'html_validation.log').write_text(log.getvalue())
    parser = Headings()
    parser.feed((ROOT/'research_report.html').read_text())
    expected_headings = re.findall(r'^## (.+)$', (ROOT/'research_report.md').read_text(), re.M)
    assert parser.items == expected_headings, (parser.items, expected_headings)
    sources = [json.loads(line) for line in (ROOT/'sources.jsonl').read_text().splitlines()]
    evidence = [json.loads(line) for line in (ROOT/'evidence.jsonl').read_text().splitlines()]
    by_id = {s['source_id']: s for s in sources}
    for item in evidence:
        source = by_id[item['source_id']]
        capture = json.loads((ROOT/source['capture_path']).read_text())
        assert item['quote'] in capture['text']
        assert sha256(capture['text'].encode()).hexdigest() == source['text_sha256']
    source_bib = {int(x) for x in re.findall(r'^\[(\d+)\]', (ROOT/'research_report.md').read_text(), re.M)}
    assert source_bib == set(range(1, len(sources)+1))
    result = dict(status='PASS' if html_pass else 'FAIL', sources=len(sources), evidence=len(evidence),
                  html_h2_exact=len(parser.items), source_hashes_and_excerpts='PASS',
                  baseline=subprocess.check_output(['git','rev-parse','HEAD'],cwd=BOOK,text=True).strip(),
                  manuscript_diff=subprocess.check_output(['git','diff','--name-only','--','manuscript','site','publishing','requirements.txt'],cwd=BOOK,text=True).strip(),
                  warnings=['Original HTML validator misclassifies Chinese as emoji: U+24C2..U+1F251.',
                            'Original word counter splits on whitespace; its short Chinese summary warning is not a length measurement.',
                            'URL checker returned 405 for HN and 403 for Zhihu; both were read with ego-browser and captured.',
                            'PNG files rendered; image tool returned current model does not support image input. PDF visual acceptance is NOT complete.'])
    assert not result['manuscript_diff'], result['manuscript_diff']
    (ROOT/'package_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False))
    return 0 if html_pass else 1


if __name__ == '__main__':
    raise SystemExit(main())

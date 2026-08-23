from pathlib import Path
import json, re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / 'research' / 'evidence'

def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

def norm(url):
    p = urlsplit(url.rstrip('/'))
    return (p.scheme.lower(), p.netloc.lower(), p.path.rstrip('/'))

sources = rows(EVIDENCE / 'sources.jsonl')
evidence = rows(EVIDENCE / 'evidence.jsonl')
claims = rows(EVIDENCE / 'claims.jsonl')
by_url = {norm(s['raw_url']): s['source_id'] for s in sources}
ev_by_source = {}
for e in evidence:
    ev_by_source.setdefault(e['source_id'], []).append(e['evidence_id'])

for c in claims:
    urls = re.findall(r'https?://[^)\s]+', c['text'])
    sids = []
    for u in urls:
        sid = by_url.get(norm(u))
        if sid and sid not in sids:
            sids.append(sid)
    c['cited_source_ids'] = sids
    c['evidence_ids'] = [eid for sid in sids for eid in ev_by_source.get(sid, [])]
    # The extractor emits section-sized units. Units with an immediate source
    # link remain factual; uncited units are design synthesis, not asserted facts.
    c['claim_type'] = 'factual' if sids else 'synthesis'
    c['audit_note'] = ('linked from immediate Markdown source URL' if sids else
                       'author synthesis/design recommendation; requires no factual hard gate')

with (EVIDENCE / 'claims.jsonl').open('w') as f:
    for c in claims:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')

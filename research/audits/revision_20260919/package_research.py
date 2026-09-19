"""Publish evidence metadata without copying browser pages or local runtime databases."""
from pathlib import Path
from hashlib import sha256
import json

root = Path(__file__).resolve().parent.parent / 'review_20260919'
records = []
for path in sorted((root/'retrieval').glob('*.json')):
    data = json.loads(path.read_text())
    records.append({'capture':str(path.relative_to(root)), 'url':data.get('requested_url',data.get('url')),
                    'query':data.get('query'), 'title':data.get('title'),
                    'accessed_at':data.get('accessed_at'), 'text_sha256':data.get('text_sha256'),
                    'capture_sha256':sha256(path.read_bytes()).hexdigest(), 'availability':'local retrieval cache'})
for path in sorted((root/'vendor_probe').rglob('*.capture.json')):
    meta = json.loads(path.read_text())
    records.append({'capture':str(path.relative_to(root)), 'command':meta.get('command'),
                    'retrieved_at':meta.get('retrieved_at'), 'sha256':meta.get('sha256'),
                    'exit_code':meta.get('exit_code'), 'availability':'API provenance; raw cache may be local only'})
(root/'public_evidence_index.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(f'Published retrieval/API provenance records: {len(records)}')

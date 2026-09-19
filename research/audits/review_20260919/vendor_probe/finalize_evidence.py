"""Generate scoped provenance index and verify captured evidence without network."""
import datetime
import difflib
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parent
old_root=ROOT/'dsh/source/old';new_root=ROOT/'dsh/source/new'
for old in old_root.rglob('*'):
    if not old.is_file() or old.name.endswith('.capture.json'):continue
    rel=old.relative_to(old_root);new=new_root/rel
    if not new.exists():continue
    old_meta=json.loads(old.with_name(old.name+'.capture.json').read_text())
    new_meta=json.loads(new.with_name(new.name+'.capture.json').read_text())
    if old_meta['exit_code'] or new_meta['exit_code']:continue
    target=ROOT/'dsh/diffs'/str(rel);target=target.with_name(target.name+'.diff')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),new.read_text().splitlines(True),fromfile='cd5ef8148158c3a752a658978873241fdf8e2bbc/'+str(rel),tofile='ddefc45fbc7f8e46dd73185e68295696d1297887/'+str(rel))))

captures=[];bad_hashes=[]
for meta_file in ROOT.rglob('*.capture.json'):
    meta=json.loads(meta_file.read_text());payload=meta_file.with_name(meta_file.name.removesuffix('.capture.json'))
    valid=hashlib.sha256(payload.read_bytes()).hexdigest()==meta['sha256']
    if not valid:bad_hashes.append(str(payload.relative_to(ROOT)))
    captures.append({'path':str(payload.relative_to(ROOT)),'exit_code':meta['exit_code'],'retrieved_at':meta['retrieved_at'],'hash_valid':valid})
vm_path='packages/extensions/cordis-host-runner/src/sandbox.ts'
vm_identical=(old_root/vm_path).read_bytes()==(new_root/vm_path).read_bytes()
tests=json.loads((ROOT/'codex/local/protocol_test_results.json').read_text())
report=ROOT.parent/'report_vendor_deltas.md'
text=report.read_text()
missing=[]
for url in re.findall(r'\]\(([^)]+)\)',text):
    if not url.startswith(('http:','https:','#')) and not (report.parent/url).exists() and not url.endswith(('evidence_index.json','verification_summary.json')):
        missing.append(url)
summary={'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'capture_count':len(captures),
         'successful_captures':sum(x['exit_code']==0 for x in captures),'failed_captures':[x for x in captures if x['exit_code']!=0],
         'hash_mismatches':bad_hashes,'dsh_vm_source_byte_identical':vm_identical,'protocol_checks':{'passed':tests['passed'],'total':tests['total']},
         'schema_generation_exit_codes':{mode:json.loads((ROOT/'codex'/mode/'probe_results.json').read_text())['runs'][1:3] for mode in ['local','local_ipc_probe']},
         'initialize_success':json.loads((ROOT/'codex/initialize_only/probe_results.json').read_text())['initialize_success'],
         'initialize_only_probe':json.loads((ROOT/'codex/initialize_only/probe_results.json').read_text()),
         'handshake_status':'unverified_under_self_imposed_sandbox',
         'missing_report_evidence_links':missing,'default_tree_truncated':{name:json.loads((ROOT/name/'tree.json').read_text())['truncated'] for name in ['dsh','codex','openhands','sdk']}}
(ROOT/'verification_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
index=[]
for path in sorted(ROOT.rglob('*')):
    if not path.is_file() or path.name=='evidence_index.json' or '__pycache__' in path.parts:continue
    raw=path.read_bytes();index.append({'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(ROOT/'evidence_index.json').write_text(json.dumps({'generated_at':summary['finished_at'],'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest(),'files':index},indent=2)+'\n')
print(json.dumps({'capture_count':len(captures),'expected_or_resolved_http_failures':len(summary['failed_captures']),'hash_mismatches':bad_hashes,'vm_identical':vm_identical,'protocol_checks':summary['protocol_checks'],'missing_links':missing,'indexed_files':len(index)},indent=2))
assert not bad_hashes and not missing and vm_identical and tests['passed']==tests['total']

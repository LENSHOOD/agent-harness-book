import concurrent.futures
import difflib
import json
from collect import ROOT,capture

jobs=[]
refs={n:json.loads((ROOT/n/'head.json').read_text())['sha'] for n in ['dsh','codex','openhands','sdk']}
old='cd5ef8148158c3a752a658978873241fdf8e2bbc'
paths=['packages/extensions/cordis-host-runner/src/sandbox.ts','packages/extensions/cordis-host-runner/README.md',
       'packages/boot/plugin-manager/README.md','packages/boot/plugin-manager/src/operations.ts',
       'packages/boot/app-boot/README.md','packages/core/agent-loop/README.md','packages/sandbox/sandbox-local/README.md']
for path in paths:
    for ver,ref in [('old',old),('new',refs['dsh'])]:
        jobs.append((f'dsh/source/{ver}/{path}',f'repos/deepseek-ai/deepseek-harness/contents/{path}?ref={ref}',True))
for name,path in [('architecture','docs/architecture.md'),('vm','packages/extensions/cordis-host-runner/src/sandbox.ts'),('plugin','packages/boot/plugin-manager'),('boot','packages/boot/app-boot'),('ptc','packages/ptc')]:
    jobs.append((f'dsh/history/{name}.json',f'repos/deepseek-ai/deepseek-harness/commits?sha={refs["dsh"]}&path={path}&since=2026-08-28T00:00:00Z&per_page=100',False))
for tag in ['dsh-v0.1.6-alpha.2','dsh-v0.1.2-alpha.1']:
    jobs.append((f'dsh/tags/{tag}.json',f'repos/deepseek-ai/deepseek-harness/commits/{tag}',False))
jobs.append(('dsh/old_tree.json',f'repos/deepseek-ai/deepseek-harness/git/trees/{old}?recursive=1',False))
for path in ['codex-rs/app-server/src/lib.rs','codex-rs/arg0/src/lib.rs','codex-rs/app-server/src/main.rs']:
    jobs.append((f'codex/source/local_tag/{path}',f'repos/openai/codex/contents/{path}?ref=rust-v0.142.5',True))
for ver,ref in [('old',json.loads((ROOT/'openhands/baseline.json').read_text())[0]['sha']),('new',refs['openhands'])]:
    for path in ['package.json','DEVELOPMENT.md']:
        jobs.append((f'openhands/source/{ver}/{path}',f'repos/OpenHands/OpenHands/contents/{path}?ref={ref}',True))
for path in ['openhands-sdk/openhands/sdk/conversation/conversation.py','openhands-workspace/openhands/workspace/agent_sandbox/README.md','openhands-agent-server/openhands/agent_server/README.md']:
    jobs.append((f'sdk/source/new/{path}',f'repos/OpenHands/software-agent-sdk/contents/{path}?ref={refs["sdk"]}',True))
for number in [4806,4807,4822,4966,4516,4702]:
    jobs.append((f'sdk/prs/{number}.json',f'repos/OpenHands/software-agent-sdk/pulls/{number}',False))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda x:capture(*x),jobs))
for path in ['README.md','docs/architecture.md','docs/tool-catalog.md','package.json']+paths:
    a=ROOT/'dsh/source/old'/path;b=ROOT/'dsh/source/new'/path
    target=ROOT/'dsh/diffs'/(path+'.diff');target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(''.join(difflib.unified_diff(a.read_text().splitlines(True),b.read_text().splitlines(True),fromfile=old+'/'+path,tofile=refs['dsh']+'/'+path)))
print('captured sources, histories, PR records, and dsh diffs')

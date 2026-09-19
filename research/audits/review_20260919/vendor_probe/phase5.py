import concurrent.futures
import json
from collect import ROOT,capture
jobs=[]
dsh='deepseek-ai/deepseek-harness';old='cd5ef8148158c3a752a658978873241fdf8e2bbc';new='ddefc45fbc7f8e46dd73185e68295696d1297887'
for path in ['packages/code-runtime/code-runtime-worker-thread/README.md','packages/code-runtime/code-runtime-worker-thread/src/worker.ts','packages/code-runtime/code-runtime-worker-thread/src/index.ts']:
    jobs.append((f'dsh/source/old/{path}',f'repos/{dsh}/contents/{path}?ref={old}',True))
jobs.append(('dsh/history/code_runtime.json',f'repos/{dsh}/commits?sha={new}&path=packages/code-runtime&since=2026-08-28T00:00:00Z&per_page=100',False))
for prefix in ['9b7a8ccc9fabc2e87386acf7f8b0741baf978022','7c9bb5914cedec80e46197a8c894037fcfd12faf']:
    jobs.append((f'dsh/commits/{prefix[:12]}.json',f'repos/{dsh}/commits/{prefix}',False))
codex=json.loads((ROOT/'codex/tags/rust-v0.155.1.json').read_text())['sha']
for path in ['codex-rs/app-server-protocol/src/protocol/common.rs','codex-rs/app-server/README.md']:
    jobs.append((f'codex/source/stable_0.155.1/{path}',f'repos/openai/codex/contents/{path}?ref={codex}',True))
oh=json.loads((ROOT/'openhands/tags/v1.20.0.json').read_text())['sha']
jobs.append(('openhands/source/stable_1.20.0/package.json',f'repos/OpenHands/OpenHands/contents/package.json?ref={oh}',True))
legacy=json.loads((ROOT/'openhands/tags/0.62.0.json').read_text())['sha']
jobs.append(('openhands/source/legacy_0.62.0/openhands/runtime/README.md',f'repos/OpenHands/OpenHands/contents/openhands/runtime/README.md?ref={legacy}',True))
sdk=json.loads((ROOT/'sdk/tags/v1.49.2.json').read_text())['sha']
for path in ['openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py','openhands-agent-server/openhands/agent_server/runtime_router.py','openhands-sdk/openhands/sdk/conversation/conversation.py','openhands-sdk/pyproject.toml']:
    jobs.append((f'sdk/source/stable_1.49.2/{path}',f'repos/OpenHands/software-agent-sdk/contents/{path}?ref={sdk}',True))
for number in [3403,5093,5101]:jobs.append((f'sdk/prs/{number}.json',f'repos/OpenHands/software-agent-sdk/pulls/{number}',False))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda x:capture(*x),jobs))
for name in ['dsh','codex','openhands','sdk']:
    wanted={'dsh':['dsh-v0.1.2-alpha.1','dsh-v0.1.6-alpha.2'],'codex':['rust-v0.142.5','rust-v0.150.1','rust-v0.151.0','rust-v0.152.0','rust-v0.153.0','rust-v0.154.0','rust-v0.155.0','rust-v0.155.1'],'openhands':['0.62.0','1.0.0','v1.16.0','v1.20.0'],'sdk':['1.0.0','v1.44.0','v1.45.0','v1.47.0','v1.48.0','v1.49.0','v1.49.2']}[name]
    for tag in wanted:
        data=json.loads((ROOT/name/'tags'/(tag+'.json')).read_text())
        print(name,tag,data['sha'],data['commit']['committer']['date'])

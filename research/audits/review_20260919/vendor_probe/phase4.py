import concurrent.futures
import json
from collect import ROOT,capture
jobs=[]
dsh='deepseek-ai/deepseek-harness'
old='cd5ef8148158c3a752a658978873241fdf8e2bbc';new='ddefc45fbc7f8e46dd73185e68295696d1297887'
for path in ['packages/boot/app-boot/src/index.ts','packages/boot/app-boot/src/profile.ts','packages/extensions/cordis-host-runner/src/lifecycle.ts','packages/extensions/tool-cordis/src/index.ts','vendor/loader/src/config/entry.ts','vendor/loader/src/config/group.ts']:
    for ver,ref in [('old',old),('new',new)]:jobs.append((f'dsh/source/{ver}/{path}',f'repos/{dsh}/contents/{path}?ref={ref}',True))
for path in ['packages/ptc-runtime/ptc-runtime-node/README.md','packages/ptc-runtime/ptc-runtime-node/src/launch.ts','packages/boot/plugin-manager/src/tools.ts']:
    jobs.append((f'dsh/source/new/{path}',f'repos/{dsh}/contents/{path}?ref={new}',True))
for name,path in [('ptc_rename','packages/ptc-runtime'),('agent_setup','packages/core/agent-loop/src'),('tool_cordis','packages/extensions/tool-cordis/src/index.ts')]:
    jobs.append((f'dsh/history/{name}.json',f'repos/{dsh}/commits?sha={new}&path={path}&since=2026-08-28T00:00:00Z&per_page=100',False))
for prefix in ['e07f41d5fd8c','98b92b683c39','abd765a6001f','ed32f57f88ef','aeb13413c71e','f99b06eaed81','d1521ea7838f']:
    jobs.append((f'dsh/commits/{prefix}.json',f'repos/{dsh}/commits/{prefix}',False))
for tag in ['0.62.0','1.0.0']:
    jobs.append((f'openhands/tags/{tag}.json',f'repos/OpenHands/OpenHands/commits/{tag}',False))
jobs.append(('openhands/legacy_tree.json','repos/OpenHands/OpenHands/git/trees/0.62.0?recursive=1',False))
jobs.append(('openhands/first_v1_release.json','repos/OpenHands/OpenHands/releases/tags/1.0.0',False))
for path in ['README.md','openhands/runtime/base.py','openhands/runtime/impl/docker/docker_runtime.py','openhands/runtime/action_execution_server.py']:
    jobs.append((f'openhands/source/legacy_0.62.0/{path}',f'repos/OpenHands/OpenHands/contents/{path}?ref=0.62.0',True))
jobs.append(('sdk/tags/1.0.0.json','repos/OpenHands/software-agent-sdk/commits/1.0.0',False))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:list(pool.map(lambda x:capture(*x),jobs))
print('phase4 complete')

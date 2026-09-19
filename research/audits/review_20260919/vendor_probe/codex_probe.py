"""No-model, network-denied local schema and stdio handshake capture."""
import datetime
import hashlib
import json
import os
import pathlib
import selectors
import subprocess
import sys
import time

ROOT=pathlib.Path(__file__).resolve().parent
local_ipc='--local-ipc' in sys.argv
OUT=ROOT/'codex'/('local_ipc_probe' if local_ipc else 'local')
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'tmp').mkdir(exist_ok=True)
task_env=os.environ.copy()
task_env['TMPDIR']=str(OUT/'tmp')
network_rule='(deny network-outbound (remote ip "*:*")) (deny network-inbound (local ip "*:*"))' if local_ipc else '(deny network*)'
profile=f'(version 1) (allow default) {network_rule} (deny file-write* (require-not (subpath "{ROOT}"))) (allow file-write* (literal "/dev/null"))'
prefix=['/usr/bin/sandbox-exec','-p',profile,'/opt/homebrew/bin/codex']
results=[]
for name,args in [('version',['--version']),('schema',['app-server','generate-json-schema','--out',str(OUT/'schema')]),('schema_experimental',['app-server','generate-json-schema','--experimental','--out',str(OUT/'schema_experimental')])]:
    cmd=prefix+args
    r=subprocess.run(cmd,capture_output=True,timeout=45,env=task_env,cwd=OUT)
    (OUT/(name+'.stdout.txt')).write_bytes(r.stdout)
    (OUT/(name+'.stderr.txt')).write_bytes(r.stderr)
    results.append({'name':name,'command':cmd,'exit_code':r.returncode})
    print(name,r.returncode,r.stdout.decode()[:250],r.stderr.decode()[:300],flush=True)

cmd=prefix+['app-server','--stdio','-c','analytics.enabled=false','-c','feedback.enabled=false','-c','check_for_update_on_startup=false','-c',f'sqlite_home="{OUT}/state"','-c',f'log_dir="{OUT}/logs"']
requests=[{'id':1,'method':'initialize','params':{'clientInfo':{'name':'vendor_protocol_audit','title':'Read-only protocol audit','version':'2026.09.19'},'capabilities':{'experimentalApi':False}}}, {'method':'initialized'}]
(OUT/'handshake.requests.json').write_text(json.dumps(requests,indent=2)+'\n')
events=[]
with (OUT/'handshake.stderr.txt').open('wb') as err:
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,env=task_env,cwd=OUT,text=True,bufsize=1)
    p.stdin.write(json.dumps(requests[0])+'\n');p.stdin.flush()
    selector=selectors.DefaultSelector();selector.register(p.stdout,selectors.EVENT_READ)
    deadline=time.monotonic()+15
    success=False
    while time.monotonic()<deadline and p.poll() is None:
        if not selector.select(timeout=0.5):continue
        line=p.stdout.readline()
        if not line:break
        events.append(line)
        reply=json.loads(line)
        if reply.get('id')==1:
            success='result' in reply
            if success:p.stdin.write(json.dumps(requests[1])+'\n');p.stdin.flush()
            break
    p.stdin.close()
    try:p.wait(timeout=10)
    except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=5)
    events+=p.stdout.readlines()
    selector.close()
(OUT/'handshake.responses.jsonl').write_text(''.join(events))
results.append({'name':'handshake','command':cmd,'initialize_success':success,'initialized_sent':success,'exit_code':p.returncode,'only_methods_sent':['initialize','initialized'] if success else ['initialize']})

def methods(obj):
    found=set()
    if isinstance(obj,dict):
        method=obj.get('properties',{}).get('method',{})
        found.update(method.get('enum',[]))
        if 'const' in method:found.add(method['const'])
        for v in obj.values():found.update(methods(v))
    elif isinstance(obj,list):
        for v in obj:found.update(methods(v))
    return found

schema_results={}
for mode in ['schema','schema_experimental']:
    all_methods=set()
    for path in (OUT/mode).rglob('*.json'):
        all_methods.update(methods(json.loads(path.read_text())))
    expected=['thread/start','turn/start','turn/interrupt','turn/cancel','item/start','item/started','item/update','item/agentMessage/delta','item/completed','turn/completed']
    schema_results[mode]={'methods':sorted(all_methods),'checks':{key:key in all_methods for key in expected}}
    print(mode,json.dumps(schema_results[mode]['checks']),flush=True)
summary={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':results,'network':'IP inbound/outbound denied; local IPC allowed' if local_ipc else 'denied by macOS sandbox','write_scope':str(ROOT),'schema_results':schema_results}
(OUT/'probe_results.json').write_text(json.dumps(summary,indent=2)+'\n')
print('initialize_success',success,'responses',''.join(events)[:2000])

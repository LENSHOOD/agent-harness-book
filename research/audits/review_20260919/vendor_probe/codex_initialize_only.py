"""Initialize-only probe with a short mktemp root, unchanged home, and IP deny."""
import datetime
import json
import os
import pathlib
import selectors
import socket
import subprocess
import sys
import time

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/'codex'/'initialize_only'
OUT.mkdir(parents=True,exist_ok=True)
help_cmd=['/opt/homebrew/bin/codex','app-server','--help']
help_result=subprocess.run(help_cmd,capture_output=True,text=True,timeout=10)
(OUT/'app_server_help.stdout.txt').write_text(help_result.stdout)
(OUT/'app_server_help.stderr.txt').write_text(help_result.stderr)
assert help_result.returncode==0 and '--stdio' in help_result.stdout
temp_cmd=['mktemp','-d','/private/tmp/codex-vendor-init.XXXXXX']
task_temp=pathlib.Path(subprocess.check_output(temp_cmd,text=True).strip()).resolve()
task_env=os.environ.copy()
task_env['TMPDIR']=str(task_temp)
task_env['RUST_BACKTRACE']='1'
profile=f'''(version 1)
(allow default)
(deny network-outbound (remote ip "*:*"))
(deny network-inbound (local ip "*:*"))
(deny network-bind (local ip "*:*"))
(deny file-write* (require-not (require-any (subpath "{ROOT}") (subpath "{task_temp}") (literal "/dev/null"))))
'''
(OUT/'sandbox_profile.sb').write_text(profile)
cmd=['/usr/bin/sandbox-exec','-p',profile,'/opt/homebrew/bin/codex','app-server','--stdio',
     '-c','analytics.enabled=false','-c','feedback.enabled=false','-c','check_for_update_on_startup=false',
     '-c',f'sqlite_home="{task_temp}/state"','-c',f'log_dir="{task_temp}/logs"']
initialize={'id':1,'method':'initialize','params':{'clientInfo':{'name':'vendor_protocol_audit','title':'Initialize-only audit','version':'2026.09.19'},'capabilities':{'experimentalApi':False}}}
sent=[];received=[];reply=None;forced_stop=False;read_buffer=b''
with (OUT/'stderr.txt').open('wb') as error_file:
    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error_file,env=task_env,cwd=OUT)
    process.stdin.write((json.dumps(initialize)+'\n').encode());process.stdin.flush();sent.append(initialize)
    selector=selectors.DefaultSelector();selector.register(process.stdout,selectors.EVENT_READ)
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if selector.select(timeout=0.3):
            chunk=os.read(process.stdout.fileno(),65536)
            if not chunk:break
            read_buffer+=chunk
            while b'\n' in read_buffer:
                line,read_buffer=read_buffer.split(b'\n',1)
                if not line:continue
                message=json.loads(line);received.append(message)
                if message.get('id')==1:reply=message
            if reply is not None:break
        if process.poll() is not None:break
    if reply and 'result' in reply:
        initialized={'method':'initialized'}
        process.stdin.write((json.dumps(initialized)+'\n').encode());process.stdin.flush();sent.append(initialized)
    process.stdin.close()
    try:process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        forced_stop=True;process.terminate()
        try:process.wait(timeout=3)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=3)
    rest=process.stdout.read()
    for line in (read_buffer+rest).splitlines():
        if line:received.append(json.loads(line))
    selector.close()
(OUT/'requests.sent.jsonl').write_text(''.join(json.dumps(msg)+'\n' for msg in sent))
(OUT/'responses.received.jsonl').write_text(''.join(json.dumps(msg)+'\n' for msg in received))
result={'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'help_command':help_cmd,'help_exit_code':help_result.returncode,'stdio_supported':True,
        'mktemp_command':temp_cmd,'temporary_directory':str(task_temp),'command':cmd,'exit_code':process.returncode,'forced_stop':forced_stop,
        'home_unchanged':task_env.get('HOME')==os.environ.get('HOME'),'codex_home_unchanged':task_env.get('CODEX_HOME')==os.environ.get('CODEX_HOME'),
        'ip_network':'deny inbound/outbound/bind','unix_ipc':'permitted within allowed writable paths','writable_paths':[str(ROOT),str(task_temp),'/dev/null'],
        'initialize_success':bool(reply and 'result' in reply),'initialized_sent':any(m['method']=='initialized' for m in sent),
        'methods_sent':[m['method'] for m in sent],'initialize_response':reply,'temp_files':[str(p.relative_to(task_temp)) for p in task_temp.rglob('*') if p.is_file()]}
(OUT/'probe_results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['temporary_directory','exit_code','initialize_success','initialized_sent','methods_sent','initialize_response','forced_stop']},indent=2))
print((OUT/'stderr.txt').read_text()[:2400])

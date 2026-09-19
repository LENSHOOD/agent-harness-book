"""Read-only GitHub GET capture. All generated outputs remain beside this script."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent

def capture(label, endpoint, raw=False):
    target = ROOT / label
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = ['gh', 'api', '--method', 'GET', endpoint]
    if raw:
        cmd += ['-H', 'Accept: application/vnd.github.raw+json']
    result = subprocess.run(cmd, capture_output=True, timeout=90)
    target.write_bytes(result.stdout)
    metadata = {'command': cmd, 'retrieved_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'exit_code': result.returncode, 'stderr': result.stderr.decode(errors='replace'),
                'sha256': hashlib.sha256(result.stdout).hexdigest()}
    target.with_name(target.name + '.capture.json').write_text(json.dumps(metadata, indent=2) + '\n')
    if result.returncode:
        print(label, 'ERROR', metadata['stderr'][:150], flush=True)
        return None
    if raw:
        print(label, len(result.stdout), 'bytes', flush=True)
        return result.stdout
    return json.loads(result.stdout)

def initial(name, repo, branch):
    meta = capture(f'{name}/repo.json', f'repos/{repo}')
    head = capture(f'{name}/head.json', f'repos/{repo}/commits/{branch}')
    baseline = capture(f'{name}/baseline.json', f'repos/{repo}/commits?sha={branch}&until=2026-08-27T23:59:59Z&per_page=1')
    latest = capture(f'{name}/latest_release.json', f'repos/{repo}/releases/latest')
    releases = capture(f'{name}/releases_page_1.json', f'repos/{repo}/releases?per_page=100&page=1')
    tree = capture(f'{name}/tree.json', f'repos/{repo}/git/trees/{head["sha"]}?recursive=1') if head else None
    print(json.dumps({'repo':repo, 'head':head and head['sha'], 'head_date':head and head['commit']['committer']['date'],
                      'baseline':baseline and baseline[0]['sha'], 'latest': latest and latest['tag_name'],
                      'release_range': [releases[0]['published_at'], releases[-1]['published_at']] if releases else None,
                      'truncated':tree and tree.get('truncated')}), flush=True)

if __name__ == '__main__':
    if len(sys.argv) == 1:
        repos = [('dsh','deepseek-ai/deepseek-harness','master'),('codex','openai/codex','main'),
                 ('openhands','OpenHands/OpenHands','main'),('sdk','OpenHands/software-agent-sdk','main')]
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda args: initial(*args), repos))
    elif sys.argv[1] == 'get':
        data = capture(sys.argv[2], sys.argv[3], len(sys.argv)>4 and sys.argv[4]=='raw')
        if isinstance(data, (dict,list)):
            print(json.dumps(data, ensure_ascii=False)[:500])

import concurrent.futures
import json
from collect import ROOT, capture

REPOS={'dsh':'deepseek-ai/deepseek-harness','codex':'openai/codex','openhands':'OpenHands/OpenHands','sdk':'OpenHands/software-agent-sdk'}
jobs=[]
summary={}
for name, repo in REPOS.items():
    releases=json.loads((ROOT/name/'releases_page_1.json').read_text())
    selected=[r for r in releases if r['published_at']>='2026-08-28']
    before=[r for r in releases if r['published_at']<'2026-08-28' and not r['prerelease']]
    summary[name]=[{'tag':r['tag_name'],'date':r['published_at'],'prerelease':r['prerelease'],'url':r['html_url'],'body':r['body']} for r in selected + before[:1]]
    head=json.loads((ROOT/name/'head.json').read_text())['sha']
    base=json.loads((ROOT/name/'baseline.json').read_text())[0]['sha']
    for ref in set([r['tag_name'] for r in selected if not r['prerelease']] + [r['tag_name'] for r in before[:1]]):
        jobs.append((f'{name}/tags/{ref}.json',f'repos/{repo}/commits/{ref}',False))
    if name=='dsh':
        base='cd5ef8148158c3a752a658978873241fdf8e2bbc'
        jobs.append(('dsh/old_commit.json',f'repos/{repo}/commits/{base}',False))
        jobs.append(('dsh/compare.json',f'repos/{repo}/compare/{base}...{head}',False))
        paths=['README.md','docs/architecture.md','docs/tool-catalog.md','package.json']
    elif name=='codex':
        paths=['codex-rs/app-server/README.md','codex-rs/app-server-protocol/src/protocol/common.rs','codex-rs/Cargo.toml']
        jobs.append(('codex/tags/rust-v0.142.5.json',f'repos/{repo}/commits/rust-v0.142.5',False))
    elif name=='openhands':
        paths=['README.md','pyproject.toml']
    else:
        paths=['README.md','pyproject.toml','openhands-sdk/pyproject.toml','openhands-sdk/openhands/sdk/__init__.py']
    for version, ref in [('old',base),('new',head)]:
        for path in paths:
            jobs.append((f'{name}/source/{version}/{path}',f'repos/{repo}/contents/{path}?ref={ref}',True))
(ROOT/'release_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    list(pool.map(lambda x:capture(*x),jobs))
for name, rows in summary.items():
    print(name, [(r['tag'],r['date'],r['prerelease']) for r in rows if not r['prerelease']][:20])

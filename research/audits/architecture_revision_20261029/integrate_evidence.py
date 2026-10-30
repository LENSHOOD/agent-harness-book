"""Merge reviewed architecture evidence; never infer semantic truth from a URL."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urldefrag

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
REGISTRY = ROOT / 'research/evidence'

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

def write_rows(path, values):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n' for row in values))

def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def base(url):
    return urldefrag(url)[0].rstrip('/')

sources = rows(REGISTRY / 'sources.jsonl')
evidence = rows(REGISTRY / 'evidence.jsonl')
claims = rows(REGISTRY / 'claims_v2.jsonl')
source_ids = {row['source_id'] for row in sources}
evidence_ids = {row['evidence_id'] for row in evidence}
claim_ids = {row['claim_id'] for row in claims}
new_sources, new_evidence = [], []
records = []
for path in sorted(AUDIT.glob('*.jsonl')):
    if 'evidence' not in path.name and path.name != 'claude_mechanisms.jsonl':
        continue
    for row in rows(path):
        if 'claim' in row and str(row.get('source_url', '')).startswith('https://'):
            records.append((path, row))

captures = {}
for path in AUDIT.glob('*sources.jsonl'):
    for row in rows(path):
        url = row.get('source_url', row.get('url'))
        if url:
            captures[base(url)] = row

for path, row in records:
    url = base(row['source_url'])
    version = row['version_or_commit']
    sid = 'a29-' + digest(url + '\n' + version)
    if sid not in source_ids:
        source = {
            'source_id': sid, 'canonical_locator': url, 'raw_url': url,
            'title': row['source_title'], 'authors': url.split('/')[2], 'year': 2026,
            'source_type': 'official_repository' if 'github.com/' in url else 'official_documentation',
            'metadata_status': 'verified', 'registered_at': '2026-10-29',
            'accessed_at': row['accessed_at'], 'version_or_commit': version,
            'verification_scope': 'reviewed official source identity and specified snapshot; not vendor end-to-end validation',
            'provenance_file': str(path.relative_to(ROOT)),
        }
        capture = captures.get(url, {})
        candidate = capture.get('capture_path') or capture.get('cache') or row.get('capture_path')
        if not candidate and '/earendil-works/pi/blob/' in url:
            source_path = url.split('/blob/', 1)[1].split('/', 1)[1]
            candidate = 'publishing/work/architecture_20261029/pi/' + source_path
        if candidate and (ROOT / candidate).is_file():
            source['capture_path'] = candidate
            source['capture_sha256'] = hashlib.sha256((ROOT / candidate).read_bytes()).hexdigest()
        sources.append(source)
        new_sources.append(sid)
        source_ids.add(sid)
    else:
        source = next(item for item in sources if item['source_id'] == sid)
        capture = captures.get(url, {})
        candidate = capture.get('capture_path') or capture.get('cache') or row.get('capture_path')
        if candidate and (ROOT / candidate).is_file():
            source['capture_path'] = candidate
            source['capture_sha256'] = hashlib.sha256((ROOT / candidate).read_bytes()).hexdigest()
    eid = 'a29-' + digest(sid + row['claim'] + str(row['locator']))
    if eid not in evidence_ids:
        evidence.append({
            'evidence_id': eid, 'source_id': sid,
            'evidence_type': 'source_summary', 'quote': '',
            'summary': row['claim'], 'locator': row['locator'],
            'captured_at': row['accessed_at'], 'integration_revision': '2026-10-29',
            'provenance_file': str(path.relative_to(ROOT)),
            'validation': 'human/agent-reviewed source summary; locator requires reading full source; no automatic truth certification',
        })
        new_evidence.append(eid)
        evidence_ids.add(eid)
    row['_sid'], row['_eid'] = sid, eid

# Narrow, explicitly selected additions. These are editorial decisions, not generated classifications.
selected = [
    ('PI_LAYERS', '18', 'Pi v1.4.0将模型适配、Agent Core和编码会话分包提供；SDK装配AgentSession和SessionManager。', '/packages/coding-agent/docs/sdk.md'),
    ('PI_MCP', '18', 'Pi v1.4.0的CLI内建MCP扩展，SDK会话需要显式装配相关扩展工厂。', '/packages/coding-agent/docs/sdk.md'),
    ('PI_TRUST', '18', 'Pi v1.4.0的project trust控制项目资源加载，不限制工具实际可访问的资源。', '/packages/coding-agent/docs/security.md'),
    ('PI_SUBAGENT', '18', 'Pi固定版本的官方subagent实现是可安装扩展示例，通过独立pi进程提供分离的上下文。', '/packages/coding-agent/examples/extensions/subagent/README.md'),
    ('CODEX_LOOP', '14', 'Codex固定源码的turn可以包含多次模型采样，循环使用步骤上下文协调模型输入和工具执行设置。', '/codex-rs/core/src/session/turn.rs'),
    ('CODEX_TOOLS', '14', 'Codex固定源码将工具规格与执行注册表通过ToolRouter关联，再由ToolRegistry分派调用。', '/codex-rs/core/src/tools/router.rs'),
    ('CLAUDE_HOST', '13', 'Claude Agent SDK公开Python实现通过子进程和控制协议嵌入Claude Code；SDK源码不等于闭源核心源码。', '/src/claude_agent_sdk/_internal/transport/subprocess_cli.py'),
    ('CLAUDE_SESSION', '13', 'Claude Agent SDK会话恢复保存对话，不等于恢复整个文件系统或撤销外部副作用。', '/agent-sdk/sessions'),
    ('CURSOR_WORKER', '15', 'Cursor自管worker把工具执行放到企业机器，循环与推理仍在Cursor服务侧。', '/docs/cloud-agent/self-hosted'),
    ('CURSOR_CONTEXT', '15', 'Cursor官方工程说明通过外置长输出、历史及工具描述来支持按需上下文发现。', '/blog/dynamic-context-discovery'),
]
for suffix, chapter, text, locator_suffix in selected:
    matches = [row for _, row in records if base(row['source_url']).endswith(locator_suffix)]
    if not matches:
        raise ValueError(f'No reviewed evidence for selected claim {suffix}: {locator_suffix}')
    cid = 'A20261029_' + suffix
    if cid not in claim_ids:
        claims.append({
            'claim_id': cid, 'chapter': chapter, 'claim_type': 'vendor_claim', 'text': text,
            'cited_source_ids': sorted({row['_sid'] for row in matches}),
            'evidence_ids': sorted({row['_eid'] for row in matches}),
            'support_status': 'supported', 'integration_revision': '2026-10-29',
            'scope_note': '限定对应产品章固定源码/文档截面；源码或厂商契约分析，不代表端到端与安全效果实测。',
        })

write_rows(REGISTRY / 'sources.jsonl', sources)
write_rows(REGISTRY / 'evidence.jsonl', evidence)
write_rows(REGISTRY / 'claims_v2.jsonl', claims)

readme = REGISTRY / 'README.md'
text = readme.read_text()
counts = Counter(row['metadata_status'] for row in sources)
text = re.sub(r'<!-- registry-status:.*?-->',
    f'<!-- registry-status: total={len(sources)} verified={counts["verified"]} unverified={counts["unverified"]} -->', text)
heading = '## 2026-09-19 批次记录（历史截面）'
if heading not in text:
    text = text.replace('截至2026-09-19', heading + '\n\n截至2026-09-19', 1)
start = '<!-- architecture-20261029:start -->'
end = '<!-- architecture-20261029:end -->'
current = (f'{start}\n## 当前架构修订批次\n\n'
    f'2026-10-29登记状态：来源{len(sources)}项，已核验身份/截面{counts["verified"]}项，未核验线索{counts["unverified"]}项；'
    f'证据{len(evidence)}项，核心主张{len(claims)}项。新增原文定位和短摘位于`research/audits/architecture_revision_20261029/`；'
    '全局新增证据是有明确来源的摘要，不把短摘自动当作整项主张的证明。部分新增来源沿用先前固定commit；其余网页以本次访问截面为准。'
    '第三篇与pi-mono经过机制复核；本地Pi实验只覆盖真实Agent Core加确定性模型替身。旧主张继续绑定原历史版本，不自动升级为十月事实。'
    '\n\n新章插入后，核心账本的章节位置已更新，历史位置保留在`chapter_before_20261029`。'
    '下方九月统计、捕获完整性及整合命令仅描述旧批次，不应对当前新增材料直接重放旧写入脚本。'
    f'\n{end}\n\n')
if start in text:
    text = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\n*', current, text, flags=re.S)
else:
    text = text.replace(heading, current + heading)
readme.write_text(text)
print(json.dumps({'records': len(records), 'sources_added': len(new_sources), 'evidence_added': len(new_evidence),
    'sources': len(sources), 'evidence': len(evidence), 'claims': len(claims)}, indent=2))

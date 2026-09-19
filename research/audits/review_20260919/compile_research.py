"""Compile the reviewed browser captures into a versioned research evidence pack.

No network calls. The claim is deliberately narrow; a fetched page is not proof
that the paper's experiments or vendor implementation have been reproduced.
"""
from pathlib import Path
from hashlib import sha256
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parent
# id, organization/author, source type, date/edition, temporal class, exact locator fragment, supported claim
SPECS = [
    ("openai-api-changelog", "OpenAI", "official_documentation", "2026-09-10", "new", "Released the Agents API in public beta.", "OpenAI 在9月10日发布托管Codex harness的Agents API公测。"),
    ("openai-agents-overview", "OpenAI", "official_documentation", "snapshot 2026-09-19", "current_state", "Choosing a self-hosted sandbox does not make the Agents API ZDR-eligible.", "自托管执行环境不改变Agents API无ZDR支持的文档限制。"),
    ("anthropic-release-notes", "Anthropic", "official_documentation", "2026-09-03/10/14", "new", "The Messages API can now compact a conversation on demand", "9月14日新增主动压缩会话的beta接口；同页还记录auto权限和ant apply。"),
    ("anthropic-managed-architecture", "Anthropic", "official_article", "2026-04-08", "previously_omitted", "the session, agent harness, and sandbox all shared an environment", "该工程文解释会话存储、harness与沙箱从同容器走向解耦，属于4月旧资料。"),
    ("cursor-self-hosted", "Cursor", "official_article", "2026-09-02", "new", "推理和规划仍留在 Cursor 云端", "Cursor自管机器只迁移执行环境，推理规划仍在云端。"),
    ("cursor-changelog", "Cursor", "official_release_notes", "2026-09-10", "new", "项目 目前处于 beta 阶段", "9月10日Projects以beta推出协调代理、共享上下文与Subscriptions。"),
    ("langchain-context-modes", "T. Bengre; C. Curme / LangChain", "official_article", "2026-09-08", "new", "Supported values are \"isolated\" and \"fork\".", "Deep Agents子代理增加isolated/fork上下文模式；工作者和独立验证者适用条件不同。"),
    ("microsoft-harness", "Microsoft", "official_documentation", "updated 2026-09-15", "updated_documentation", "composes existing Agent Framework building blocks", "Microsoft Harness是既有Agent Framework构件的组合；更新日期不等于首发日期。"),
    ("harnessdev-full", "Wu et al.", "preprint", "2609.01437v1; 2026-09-01", "new", "one trajectory per creator–runtime cell", "HarnessDev的Evolution每个creator–runtime单元只有单条演化轨迹，不能做总体可靠性推断。"),
    ("hoh-full", "Yan et al.", "preprint", "2609.01481v1; 2026-09-01", "new", "separates implementation-time testing from independent evaluation", "HoH在既有coding harness外编排规划、开发、独立评估循环。"),
    ("jit-full", "Zhang et al.", "preprint", "2608.25593v2; 2026-09-03", "revised", "JIT-Agent is trained based on Qwen3.6-27B.", "JIT-Agent训练生成harness的辅助模型，不能称整个系统完全没有权重训练。"),
    ("harnessevolve-full", "Jiang et al.", "preprint", "2609.00829v1; 2026-09-01", "new", "given the question and its ground-truth answer", "HarnessEvolve用已知正确答案生成参考轨迹，企业迁移需要该监督条件。"),
    ("empirical-full", "Fan et al.", "preprint", "2609.20804v1; 2026-09-17", "new", "Planning and the action space are evaluated only under T4/128k.", "176设置研究的planning/action-space消融只覆盖T4/128k，不能泛化到全部预算。"),
    ("hook-full", "Li et al.", "preprint", "2609.03884v2; 2026-09-08", "new", "controls plugin metadata, versioning, and lifecycle-hook configuration", "HookPry的攻击前提是控制插件更新与hook配置；不是任意输入均可突破沙箱。"),
    ("memsecbench", "Chen et al.", "preprint", "2607.27080v1; 2026-07-29", "previously_omitted", "Write--Execute--Forget", "MemSecBench把记忆写入、后续使用和选择性清除置于同一生命周期验证。"),
    ("acp-v2", "Ben Brandt / ACP", "official_specification", "2026-07-20 draft", "previously_omitted", "v2 is a Draft.", "ACP v2调整会话/消息生命周期，但当前公告仍标草案；不应默认作为稳定生产协议。"),
    ("langsmith-engine", "Palash Shah / LangChain", "official_article", "2026-05-19", "previously_omitted", "Hand off fixes to a separate agent when needed.", "LangSmith Engine从轨迹问题产出评测与回归样本，另派修复代理，属5月旧实践。"),
    ("harness-tool-primitives", "Jin et al.", "preprint", "2609.01736v1; 2026-09-01", "new", "each tool is wrapped with an LLM interface", "HEART把模式解析放进工具包装内的LLM；接口简化不意味着底层约束消失。"),
    ("rsi-full", "Duan et al.", "preprint_roadmap", "2609.11873v2; 2026-09-15", "new", "preliminary empirical evidence", "RSI五级路线图是综述与初步证据，不是已经达到完全递归进化的证明。"),
    ("show-harness", "Chen et al.", "preprint", "2609.10522v1; 2026-09-09", "new", "embodiment-specific interpreters deterministically ground them into local robot actions", "Show-Harness把语义动作交给具体机器人的解释器落地，提示ACI可扩展到具身领域。"),
    ("ecdysis-full", "Yue et al.", "preprint", "2609.11677v1; 2026-09-10", "new", "task model parameters and runtime environment remain fixed", "Ecdysis通过跨实例失败聚合修改harness，文中training期间任务模型和环境固定。"),
    ("colosseum-full", "Lin et al.", "preprint", "2609.15983v2; 2026-09-15", "new", "routes verifier findings back to the affected part of the argument", "Colosseum把验证反馈路由到证明依赖中的相应部分，而非只做多数票。"),
    ("sol-pi-full", "Liu et al.", "preprint", "2609.20519v1; 2026-09-17", "new", "retaining 93.7% of Pi’s average score", "SoL-Pi效率配置有分数让步，不能把更少token写成无损收益。"),
    ("self-harness-current", "Zhang et al.", "preprint", "2606.09498v3; 2026-08-20", "unchanged", "last revised 20 Aug 2026", "Self-Harness当前仍v3，未发现本窗口内新版本。"),
    ("living-harness-current", "Du et al.", "preprint", "2607.26598v2; 2026-08-11", "unchanged", "last revised 11 Aug 2026", "Living-Harness当前仍v2，未发现本窗口内新版本。"),
    ("harnessbank-v1", "Luo et al.", "preprint", "2607.13683v1; 2026-07-15", "version_correction", "Self-Evolving Agent Harnesses via Gated Semantic Quality-Diversity", "原书GSME名称与严格计量表述对应v1。"),
    ("harnessbank-v2-full", "Luo et al.", "preprint", "2607.13683v2; 2026-07-30", "version_correction", "HarnessBank: Semantic Gene-Bank Search with Gated Verification", "登记为v2的来源原文已名为HarnessBank，应按实际版次重审证据。"),
    ("nle-official", "NLE authors / Facebook Research", "official_repository", "snapshot 2026-09-19", "terminology_correction", "The NetHack Learning Environment (NLE)", "NLE不是非语言增强任务，而是NetHack Learning Environment。"),
    ("hsi-current", "Tailin Zhou", "preprint", "2608.08466v1", "baseline_recheck", "roguelike environments with complex state spaces and sparse feedback", "HSI实验中的MiniHack/NLE属于roguelike环境，失败不证明一般模型能力的数学上限。"),
    ("google-harness", "Taylor Mullen; Christian Gunderman / Google", "official_article", "2026-09-09", "new", "they aren’t a replacement for larger, end-to-end evaluation suites", "Google主张行为评测与端到端评测互补，并提醒避免固定唯一工具序列。"),
    ("beyond-static", "openJiuwen Team", "preprint", "2608.27969v1; 2026-08-28", "cutoff_boundary", "Structural Composability and Runtime Adaptivity", "openJiuwen区分结构可组合与运行时适应；处于上轮截面边界，不强称9月新发。"),
    ("hn-harness-study", "Hacker News participants", "community_discussion", "2026-09-18/19", "community_signal", "there aren't too many benchmarks", "HN讨论质疑复杂harness普适增益与跨模型迁移；这里只证实存在该讨论。"),
    ("reddit-harness-use", "r/LocalLLaMA participants", "community_discussion", "2026-09-05", "community_signal", "14 cross-system tasks", "Reddit有小任务集成本自报对比；不是可直接采用的行业排名。"),
    ("cursor-subagent-issue", "Cursor forum reporter TeX1", "community_bug_report", "2026-09-17", "community_signal", "I am not claiming a cause for the nest here.", "用户报告子代理身份异常且不声称递归派生的根因；未独立复现产品缺陷。"),
    ("zhihu-harnessevolve", "黄浴 / 知乎", "community_commentary", "2026-09-06", "community_signal", "Reference Trajectory ≠ Optimal Trajectory", "中文讨论提醒成功参考轨迹不一定最优；技术论证仍应回到原论文。"),
    ("harness-survey", "Barbaste et al.", "preprint", "2609.00006v1; page date conflicts with identifier month", "metadata_uncertain", "Submitted on 15 Jul 2026", "该页面标题编号月份与提交日期不一致，不作为9月新发布的确定时间证据。"),
    ("bigquery-time-travel", "Google Cloud", "official_documentation", "snapshot 2026-09-19", "example_dialect_verification", "More than seven (7) days before the current timestamp.", "BigQuery支持该时间旅行语法，但不能把数周前的as-of字面量当长期可复现快照。"),
]


def dump_jsonl(path, records):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records))


def main():
    sources, evidence, claims, bibliography = [], [], [], []
    for number, (name, author, kind, edition, temporal, quote, claim) in enumerate(SPECS, 1):
        capture_path = ROOT / 'retrieval' / f'{name}.json'
        data = json.loads(capture_path.read_text())
        assert quote in data['text'], (name, quote)
        assert sha256(data['text'].encode()).hexdigest() == data['text_sha256'], name
        source_id = sha256(data['requested_url'].encode()).hexdigest()[:16]
        evidence_id = sha256((source_id + quote).encode()).hexdigest()[:16]
        title = re.sub(r'^\[[^]]+\]\s*', '', data['title']).replace(' | OpenAI API', '')
        sources.append(dict(source_id=source_id, display_number=number, capture_id=name, title=title, authors=author,
                            url=data['requested_url'], resolved_url=data['url'], source_type=kind, edition=edition,
                            temporal_class=temporal, accessed_at=data['accessed_at'], capture_path=str(capture_path.relative_to(ROOT)),
                            text_sha256=data['text_sha256'], verification='source_read; not empirical_replication'))
        offset = data['text'].index(quote)
        evidence.append(dict(evidence_id=evidence_id, source_id=source_id, quote=quote,
                             locator={'capture':str(capture_path.relative_to(ROOT)), 'text_char_offset':offset,
                                      'text_line':data['text'][:offset].count('\n') + 1}))
        claims.append(dict(claim_id=f'D{number:02}', text=claim, cited_source_ids=[source_id], evidence_ids=[evidence_id],
                           support_status='supported_as_scoped', scope='Source-reported facts/claims, not a production or benchmark replication.'))
        bibliography.append(f'[{number}] {author} (2026). "{title}". {edition}. {data["requested_url"]} (Retrieved: 2026-09-19).')
    dump_jsonl(ROOT / 'sources.jsonl', sources)
    dump_jsonl(ROOT / 'evidence.jsonl', evidence)
    dump_jsonl(ROOT / 'claims.jsonl', claims)
    (ROOT / 'bibliography.md').write_text('## Bibliography — 参考资料\n\n' + '\n\n'.join(bibliography) + '\n')
    manifest = dict(date='2026-09-19', mode='ultradeep', book_baseline=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                    scope='incremental online research, manuscript review, case execution; no publication', browser='ego-browser / ego lite, TaskSpace 25',
                    interval={'previous_cutoff':'2026-08-27/28','through':'2026-09-19'}, source_count=len(sources),
                    search_captures=len(list((ROOT / 'retrieval').glob('search-*.json'))),
                    limitations=['No exhaustive-web guarantee','Community reports are signals, not verified vendor bugs',
                                 'Local mock/fixture checks do not reproduce vendor-model quality',
                                 'Citations are version-scoped; metadata anomaly retained explicitly'])
    (ROOT / 'run_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'sources':len(sources),'evidence':len(evidence),'claims':len(claims),'exact_excerpt_checks':'PASS'},ensure_ascii=False))


if __name__ == '__main__':
    main()

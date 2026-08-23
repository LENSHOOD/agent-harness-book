from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
EVIDENCE = ROOT / "research" / "evidence"
OUT = ROOT / "publishing" / "artifacts"
OUT.mkdir(exist_ok=True)

parts = [
    ("第一篇 历史：Agent 如何从会回答变成会行动", range(1, 5)),
    ("第二篇 原理：生产级 Harness 的构成", range(5, 13)),
    ("第三篇 产品：当代主流 Harness 的不同答案", range(13, 19)),
    ("第四篇 进化：Agent 如何从轨迹中变得更好", range(19, 25)),
    ("第五篇 实践：下一代企业 Harness", range(25, 31)),
]

chapters = {}
for path in sorted((MANUSCRIPT / "chapters").glob("*.md")):
    prefix = path.name.split("_", 1)[0]
    if prefix.isdigit():
        chapters[int(prefix)] = path

sources = [json.loads(x) for x in (EVIDENCE / "sources.jsonl").read_text().splitlines() if x.strip()]

def body(path):
    return path.read_text().strip()

chunks = [
    "---\ntitle: 'Agent Harness：从执行脚手架到自我进化系统'\n"
    "subtitle: '企业 Agent 平台架构与工程实践'\n"
    "author: '内部研究稿'\ndate: '2026-08-22'\nlang: zh-CN\n---\n",
    body(chapters[0]),
    "# 目录\n\n[TOC]\n\nMarkdown 章节按下列五篇排列。",
]

for title, nums in parts:
    chunks.append(f"# {title}")
    for n in nums:
        chunks.append(body(chapters[n]))

chunks.append("# 附录")
for path in sorted((MANUSCRIPT / "appendices").glob("*.md")):
    chunks.append(body(path))

chunks.append("# 研究方法与局限\n\n"
              "本书采用官方文档、开源仓库、论文和社区材料的分层证据法。产品事实以 2026-08-22 为时间截面；"
              "无法验证的内部实现不作为事实。设计原则是作者基于多来源的综合推断。"
              "研究资产包括 sources.jsonl、evidence.jsonl 与 claims.jsonl。"
              "局限包括产品快速迭代、公开 benchmark 污染、厂商数据选择偏差，以及部分 2026 年进化论文尚缺长期生产复现。")

bib = ["# 完整参考文献"]
for idx, s in enumerate(sources, 1):
    who = s.get("authors") or "机构/作者未登记"
    year = s.get("year") or "n.d."
    bib.append(f"{idx}. {who} ({year}). [{s['title']}]({s['raw_url']})")
chunks.append("\n".join(bib))

(OUT / "agent_harness_book.md").write_text("\n\n---\n\n".join(chunks) + "\n")

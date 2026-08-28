from pathlib import Path
import json, re, shutil

ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
EVIDENCE = ROOT / "research" / "evidence"
OUT = ROOT / "publishing" / "artifacts"
OUT.mkdir(exist_ok=True)

STRUCTURE = json.loads((ROOT / "publishing" / "book_structure.json").read_text())

chapters = {}
for path in sorted((MANUSCRIPT / "chapters").glob("*.md")):
    prefix = path.name.split("_", 1)[0]
    if prefix.isdigit():
        chapters[int(prefix)] = path

sources = [json.loads(x) for x in (EVIDENCE / "sources.jsonl").read_text().splitlines() if x.strip()]

def body(path):
    return path.read_text().strip()


def demote_headings(text: str) -> str:
    """Nest chapter/appendix headings under their part without editing source files."""
    text = re.sub(r"^(#{1,5})(?=\s)", lambda match: "#" + match.group(1), text, flags=re.M)
    return text.replace("](../assets/", "](assets/")


assets_src = MANUSCRIPT / "assets"
assets_out = OUT / "assets"
if assets_out.exists():
    shutil.rmtree(assets_out)
if assets_src.exists():
    shutil.copytree(assets_src, assets_out)

chunks = [
    f"---\ntitle: '{STRUCTURE['bookTitle']}'\n"
    f"subtitle: '{STRUCTURE['subtitle']}'\n"
    "author: '研究修订稿'\ndate: '2026-08-28'\nlang: zh-CN\n---\n",
    body(chapters[0]),
    "# 目录\n\n[TOC]\n\nMarkdown 章节按下列五篇排列。",
]

for part in STRUCTURE["parts"]:
    chunks.append(f"# {part['title']}")
    chunks.append(body(MANUSCRIPT / "parts" / f"{part['intro']}.md"))
    for chapter in part["chapters"]:
        chunks.append(demote_headings(body(chapters[chapter["number"]])))

chunks.append("# 附录")
for path in sorted((MANUSCRIPT / "appendices").glob("*.md")):
    chunks.append(demote_headings(body(path)))

chunks.append("# 研究方法与局限\n\n"
              "本书采用官方文档、开源仓库、论文和社区材料的分层证据法。全书资料维护至 2026-08-28；"
              "无法验证的内部实现不作为事实。设计原则是作者基于多来源的综合推断。"
              "研究资产包括 sources.jsonl、evidence.jsonl 与人工标注的 claims_v2.jsonl；旧 claims.jsonl 仅作历史迁移参考。"
              "局限包括产品快速迭代、公开 benchmark 污染、厂商数据选择偏差，以及部分 2026 年进化论文尚缺长期生产复现。")

bib = ["# 完整参考文献"]
for idx, s in enumerate(sources, 1):
    who = s.get("authors") or "机构/作者未登记"
    year = s.get("year") or "n.d."
    bib.append(f"{idx}. {who} ({year}). [{s['title']}]({s['raw_url']})")
chunks.append("\n".join(bib))

(OUT / "agent_harness_book.md").write_text("\n\n---\n\n".join(chunks) + "\n")

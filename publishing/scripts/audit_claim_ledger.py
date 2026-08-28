"""Read-only validation for the curated claim ledger.

The validator never classifies or rewrites claims. Authors decide claim_type and
support_status in claims_v2.jsonl; this script checks referential integrity and
writes an auditable Markdown report.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import markdown
import sys

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "research" / "evidence"
REPORT = ROOT / "research" / "audits" / "claim_ledger_report.md"
CLAIMS_PATH = EVIDENCE_DIR / "claims_v2.jsonl"

STRICT_TYPES = {"historical_fact", "factual", "vendor_claim", "research_result"}
ALLOWED_TYPES = STRICT_TYPES | {"inference", "recommendation", "forecast"}
ALLOWED_STATUS = {"supported", "partial", "unsupported", "needs_review"}
ALLOWED_SOURCE_TYPES = {
    "academic_paper",
    "official_documentation",
    "official_article",
    "official_repository",
    "platform_metadata",
}


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}:{number}: invalid JSON: {exc}") from exc
    return rows


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def normalize_url(url: str) -> tuple[str, str, str, str]:
    parsed = urlsplit(url.rstrip("/"))
    return (
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        parsed.query,
    )


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


def markdown_links(text: str) -> list[str]:
    collector = LinkCollector()
    collector.feed(markdown.markdown(text))
    return collector.links


def validate() -> tuple[list[str], list[str], list[dict], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    claims = read_jsonl(CLAIMS_PATH)
    sources = read_jsonl(EVIDENCE_DIR / "sources.jsonl")
    evidence = read_jsonl(EVIDENCE_DIR / "evidence.jsonl")

    source_by_id = {row["source_id"]: row for row in sources}
    evidence_by_id = {row["evidence_id"]: row for row in evidence}
    source_by_url = {normalize_url(row["raw_url"]): row["source_id"] for row in sources}

    if len(source_by_id) != len(sources):
        errors.append("sources.jsonl contains duplicate source_id values")
    if len(evidence_by_id) != len(evidence):
        errors.append("evidence.jsonl contains duplicate evidence_id values")
    if len({row.get("claim_id") for row in claims}) != len(claims):
        errors.append("claims_v2.jsonl contains duplicate claim_id values")

    invalid_source_types = sorted(
        {row.get("source_type") for row in sources if row.get("source_type") not in ALLOWED_SOURCE_TYPES}
    )
    if invalid_source_types:
        errors.append(f"sources.jsonl contains uncontrolled source_type values: {invalid_source_types}")

    for item in evidence:
        if item.get("source_id") not in source_by_id:
            errors.append(
                f"evidence {item.get('evidence_id')} refers to unknown source {item.get('source_id')}"
            )

    for claim in claims:
        claim_id = claim.get("claim_id", "<missing>")
        claim_type = claim.get("claim_type")
        status = claim.get("support_status")
        source_ids = claim.get("cited_source_ids", [])
        evidence_ids = claim.get("evidence_ids", [])

        if claim_type not in ALLOWED_TYPES:
            errors.append(f"{claim_id}: invalid or missing claim_type {claim_type!r}")
        if status not in ALLOWED_STATUS:
            errors.append(f"{claim_id}: invalid or missing support_status {status!r}")

        for source_id in source_ids:
            if source_id not in source_by_id:
                errors.append(f"{claim_id}: unknown source_id {source_id}")
                continue
            source = source_by_id[source_id]
            if source.get("metadata_status") != "verified":
                errors.append(f"{claim_id}: source {source_id} metadata is not verified")
            if not source.get("accessed_at"):
                errors.append(f"{claim_id}: source {source_id} has no accessed_at")
            if not source.get("version_or_commit"):
                errors.append(f"{claim_id}: source {source_id} has no version_or_commit")
        for evidence_id in evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                errors.append(f"{claim_id}: unknown evidence_id {evidence_id}")
            elif item["source_id"] not in source_ids:
                errors.append(
                    f"{claim_id}: evidence {evidence_id} belongs to uncited source {item['source_id']}"
                )

        if claim_type in STRICT_TYPES:
            if status != "supported":
                errors.append(f"{claim_id}: strict claim is {status}, expected supported")
            if not source_ids or not evidence_ids:
                errors.append(f"{claim_id}: strict claim requires source and evidence bindings")
        elif status != "supported" and not claim.get("scope_note"):
            warnings.append(f"{claim_id}: non-supported analytical claim has no scope_note")

    # Regression test for the old DOI-parenthesis extraction bug.
    doi = "https://doi.org/10.1016/0004-3702(71)90010-5"
    extracted = markdown_links(f"[STRIPS]({doi})")
    if extracted != [doi]:
        errors.append(f"Markdown link parser truncated parenthesized DOI: {extracted!r}")

    manuscript_files = sorted((ROOT / "manuscript").rglob("*.md"))
    manuscript_links: set[str] = set()
    for path in manuscript_files:
        manuscript_links.update(
            link for link in markdown_links(path.read_text()) if link.startswith(("http://", "https://"))
        )
    unregistered = sorted(
        link for link in manuscript_links if normalize_url(link) not in source_by_url
    )
    if unregistered:
        warnings.append(
            f"{len(unregistered)} manuscript links are not registered sources; see report appendix"
        )

    stats = {
        "sources": len(sources),
        "evidence": len(evidence),
        "claims": len(claims),
        "types": Counter(row.get("claim_type") for row in claims),
        "statuses": Counter(row.get("support_status") for row in claims),
        "manuscript_links": len(manuscript_links),
        "unregistered_links": unregistered,
        "verified_claim_sources": len(
            {
                source_id
                for claim in claims
                for source_id in claim.get("cited_source_ids", [])
                if source_by_id.get(source_id, {}).get("metadata_status") == "verified"
            }
        ),
        "source_types": Counter(row.get("source_type") for row in sources),
    }
    return errors, warnings, claims, stats


def write_report(errors: list[str], warnings: list[str], claims: list[dict], stats: dict) -> None:
    lines = [
        "# Claim Ledger 只读校验报告",
        "",
        "> 本报告由 `audit_claim_ledger.py` 生成。脚本不推断 claim 类型，不写回 ledger。",
        "",
        f"- 结论：{'FAIL' if errors else 'PASS'}",
        f"- 登记来源：{stats['sources']}",
        f"- 证据记录：{stats['evidence']}",
        f"- 原子承重 claim：{stats['claims']}",
        f"- 已核验承重来源：{stats['verified_claim_sources']}",
        f"- 正文外部链接：{stats['manuscript_links']}",
        "- 来源类型：" + ", ".join(f"{k}={v}" for k, v in sorted(stats["source_types"].items())),
        "- Claim 类型：" + ", ".join(f"{k}={v}" for k, v in sorted(stats["types"].items())),
        "- 支撑状态：" + ", ".join(f"{k}={v}" for k, v in sorted(stats["statuses"].items())),
        "",
        "## 错误",
        "",
    ]
    lines.extend(f"- {item}" for item in errors) if errors else lines.append("- 无。")
    lines.extend(["", "## 警告", ""])
    lines.extend(f"- {item}" for item in warnings) if warnings else lines.append("- 无。")
    lines.extend(["", "## Claim 明细", "", "| ID | 章节 | 类型 | 状态 | 来源 |", "|---|---:|---|---|---:|"])
    for claim in claims:
        lines.append(
            f"| {claim['claim_id']} | {claim.get('chapter', '')} | {claim['claim_type']} | "
            f"{claim['support_status']} | {len(claim.get('cited_source_ids', []))} |"
        )
    lines.extend(["", "## 未登记的正文链接", ""])
    if stats["unregistered_links"]:
        lines.extend(f"- {link}" for link in stats["unregistered_links"])
    else:
        lines.append("- 无。")
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> int:
    before = digest(CLAIMS_PATH)
    try:
        errors, warnings, claims, stats = validate()
    except Exception as exc:  # report parse failures cleanly to CI
        errors, warnings, claims, stats = [str(exc)], [], [], {
            "sources": 0,
            "evidence": 0,
            "claims": 0,
            "types": {},
            "statuses": {},
            "manuscript_links": 0,
            "unregistered_links": [],
            "verified_claim_sources": 0,
            "source_types": {},
        }
    write_report(errors, warnings, claims, stats)
    after = digest(CLAIMS_PATH)
    if before != after:
        errors.append("claims_v2.jsonl changed during read-only audit")
    print(f"claim ledger: {'FAIL' if errors else 'PASS'}; report={REPORT}")
    for error in errors:
        print(f"ERROR: {error}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

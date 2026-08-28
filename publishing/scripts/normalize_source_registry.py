"""Deterministic normalization of source registry metadata.

The script preserves stable source IDs, normalizes the type vocabulary, and
marks sources used by claims_v2 as verified. Existing verified sources receive
reconstructable access/version metadata. Re-running it is idempotent.
"""

from __future__ import annotations

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "research" / "evidence"
SOURCES = EVIDENCE / "sources.jsonl"
CLAIMS = EVIDENCE / "claims_v2.jsonl"

TYPE_MAP = {
    "research paper": "academic_paper",
    "academic paper": "academic_paper",
    "peer-reviewed survey": "academic_paper",
    "peer-reviewed research paper": "academic_paper",
    "preprint repository": "academic_paper",
    "official documentation": "official_documentation",
    "official specification": "official_documentation",
    "official guide": "official_documentation",
    "official research index": "official_documentation",
    "official engineering article": "official_article",
    "official research article": "official_article",
    "official product article": "official_article",
    "official technical article": "official_article",
    "official benchmark report": "official_article",
    "vendor usage report": "official_article",
    "official repository": "official_repository",
    "primary source code": "official_repository",
    "platform metadata": "platform_metadata",
}
NORMALIZED_TYPES = {
    "academic_paper",
    "official_documentation",
    "official_article",
    "official_repository",
    "platform_metadata",
}

VERSIONS = {
    "b370b4854c644418": "DOI version of record",
    "fdbfceedda4b3792": "DOI version of record",
    "e504ba1ba9c3fffc": "arXiv:2210.03629v3",
    "ffabd76a77f0fd21": "arXiv:2405.15793v3",
    "b36ffb44e7a44c44": "arXiv:2310.06770v3",
    "33e5e5bcd68981ac": "web snapshot 2026-08-28",
    "b174364e9eb69c7d": "web snapshot 2026-08-28",
    "c765441e9673d957": "web snapshot 2026-08-28",
    "e205ffac9d9f156d": "web snapshot 2026-08-28",
    "15823ae5556ea01d": "web snapshot 2026-08-28",
    "f92116a7a4372c7c": "web snapshot 2026-08-28",
    "173ad132e1d12717": "web snapshot 2026-08-28",
    "890a56b0d2aff0c9": "git cd5ef8148158c3a752a658978873241fdf8e2bbc",
    "4fe1e0f888e9c1de": "git cd5ef8148158c3a752a658978873241fdf8e2bbc",
    "09b7e5c5381c957d": "git cd5ef8148158c3a752a658978873241fdf8e2bbc",
    "e977c04772048163": "web snapshot 2026-08-28",
    "3fb5d6b0a837235b": "arXiv:2303.11366v4",
    "b71b1297191d5227": "arXiv:2305.16291v2",
    "4b7afdddd7e81d35": "arXiv:2606.09498v3",
    "e6aa3f68badc6151": "arXiv:2607.13683v2",
    "a4f4f719b552cb31": "arXiv:2607.26598v2",
    "88237429e80b56a2": "arXiv:2608.08466v1",
    "d7ef622187acc55b": "arXiv:2410.21819v2",
    "ede733cb363a2024": "arXiv:2406.07791v9",
    "ef7c1d01fba88729": "arXiv:2511.21654v2",
    "6ddb79c39a2b95ad": "arXiv:2605.21384v1",
    "a3afc1e8c7c23916": "web snapshot 2026-08-28",
    "97416d4ba88591c5": "git 4e494929998d6bc4fccf75e0a233f727db4b70ee",
    "3b35aaf641d0719e": "web snapshot 2026-08-28",
    "e843f93261f074d9": "web snapshot 2026-08-28",
    "dac58ff4358a3416": "web snapshot 2026-08-28",
    "215600ceed9ac849": "web snapshot 2026-08-28",
    "b1f6985403c6eaa1": "web snapshot 2026-08-28",
    "3135ab19b861dcfc": "git cd5ef8148158c3a752a658978873241fdf8e2bbc",
    "d839cdae36dc69de": "git 89c02c828ee8510fe9a84ee6675608193aa13b02",
    "22e7d71eefcd7859": "specification 2025-11-25",
    "b7b1ed310bb71fac": "web snapshot 2026-08-28",
}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    claims = rows(CLAIMS)
    used = {source_id for claim in claims for source_id in claim["cited_source_ids"]}
    sources = rows(SOURCES)

    for source in sources:
        source_type = source["source_type"]
        if source_type not in TYPE_MAP and source_type not in NORMALIZED_TYPES:
            raise ValueError(f"Unknown source_type: {source_type!r}")
        source["source_type"] = TYPE_MAP.get(source_type, source_type)
        source.setdefault("accessed_at", None)
        source.setdefault("version_or_commit", None)

        if source["source_id"] == "97416d4ba88591c5":
            source["canonical_locator"] = "https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md"
            source["raw_url"] = source["canonical_locator"]
            source["title"] = "Pi coding agent official README"
            source["authors"] = "Earendil Works / Mario Zechner"
            source["year"] = "2026"

        if source["source_id"] in used:
            source["metadata_status"] = "verified"

        if source.get("metadata_status") == "verified":
            if source["source_id"] not in VERSIONS:
                raise ValueError(f"Verified source has no pinned version: {source['source_id']}")
            source["accessed_at"] = "2026-08-28"
            source["version_or_commit"] = VERSIONS[source["source_id"]]

    text = "\n".join(json.dumps(source, ensure_ascii=False, separators=(",", ":")) for source in sources)
    SOURCES.write_text(text + "\n")


if __name__ == "__main__":
    main()

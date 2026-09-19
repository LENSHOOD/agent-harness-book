"""Extract exact fenced bytes; no rendering, normalization, or placeholder repair."""
import collections
import hashlib
import re


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    blocks, files, issues = [], [], []
    for path in sorted((root / "manuscript").rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            files.append({"file": str(path.relative_to(root)), "sha256": sha(data),
                          "kind": "binary_asset", "blocks": 0})
            continue
        lines = data.splitlines(keepends=True)
        active = None
        start_count = len(blocks)
        marker_count = 0
        for idx, line in enumerate(lines, 1):
            if re.match(rb"^[ \t]*(?:`{3,}|~{3,})", line):
                marker_count += 1
            if active is None:
                match = re.match(rb"^ {0,3}(`{3,}|~{3,})([^\r\n]*)\r?\n?$", line)
                if not match:
                    continue
                fence, info = match.groups()
                if fence.startswith(b"`") and b"`" in info:
                    continue
                active = (idx, fence, info.strip().decode("utf-8"))
            else:
                opening, fence, info = active
                closing = rb"^ {0,3}" + re.escape(fence[:1]) + rb"{" + str(len(fence)).encode() + rb",}[ \t]*\r?\n?$"
                if re.match(closing, line):
                    raw = b"".join(lines[opening:idx - 1])
                    language = info.split()[0].lower() if info else "unspecified"
                    classification = ({"json": "structured_example", "yaml": "structured_example",
                                       "bash": "executable_requires_fixture", "sql": "dialect_specific_sql"}
                                      .get(language, "design_illustration"))
                    if language == "json" and b'"$schema"' in raw:
                        classification = "json_schema"
                    if any(t in raw for t in (b"function ", b"while budget_available:", b"frontier = [baseline_state]", b"while attempt.active:",
                                              b"commit_effect_safely(action, constraints):", b"recover(attempt_id):")):
                        classification = "pseudocode"
                    blocks.append({"id": f"B{len(blocks)+1:03d}", "file": str(path.relative_to(root)),
                                   "line": opening, "content_line": opening + 1, "end_line": idx,
                                   "language": language, "info": info, "sha256": sha(raw),
                                   "bytes": len(raw), "classification": classification,
                                   "raw": raw.decode("utf-8")})
                    active = None
        if active:
            issues.append({"file": str(path.relative_to(root)), "unclosed_fence": active[0]})
        if marker_count != 2 * (len(blocks) - start_count):
            issues.append({"file": str(path.relative_to(root)), "marker_count": marker_count,
                           "extracted": len(blocks) - start_count})
        files.append({"file": str(path.relative_to(root)), "sha256": sha(data),
                      "kind": "markdown" if path.suffix == ".md" else "text_asset",
                      "blocks": len(blocks) - start_count})
    return {"blocks": blocks, "files": files, "issues": issues,
            "language_counts": dict(collections.Counter(b["language"] for b in blocks))}


def get_block(inv, file_prefix, occurrence=1, language=None):
    matches = [b for b in inv["blocks"] if b["file"].split("/")[-1].startswith(file_prefix)
               and (language is None or b["language"] == language)]
    return matches[occurrence - 1]


if __name__ == "__main__":
    import json
    from pathlib import Path
    inv = inventory(Path(__file__).resolve().parents[4])
    print(json.dumps({k: v for k, v in inv.items() if k != "blocks"}, ensure_ascii=False, indent=2))
    for b in inv["blocks"]:
        print(f'\n{b["id"]} {b["file"]}:{b["line"]} [{b["language"]}]\n{b["raw"]}')

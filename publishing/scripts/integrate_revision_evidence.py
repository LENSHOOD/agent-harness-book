#!/usr/bin/env python3
"""Offline, repeatable integration of the 2026-09-19 evidence revision.

Default is a dry run. --write changes only the five authorized registry files
and disposition_evidence.md; --check compares their mechanically derived form.
No network, browser, manuscript, old audit, site, or artifact writes occur.
Metadata identity, verbatim matching, and scoped claim support are distinct.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "research/evidence"
REVIEW = ROOT / "research/audits/review_20260919"
REVISION = ROOT / "research/audits/revision_20260919"
BASE = "a1ed264462d9b61c260c1dc417243303bfc60b66"
STAMP = "2026-09-19"
SOURCE_TYPES = {"academic_paper", "official_documentation", "official_article",
                "official_repository", "platform_metadata"}
REPO_OLD = "cd5ef8148158c3a752a658978873241fdf8e2bbc"
REPO_NEW = "ddefc45fbc7f8e46dd73185e68295696d1297887"
CODEX_OLD = "426fa8cdab4247e5623e9617d531f6917482b947"
CODEX_NEW = "be2951ea34f0d295ed0becf97079f92fa5f6950e"
SDK_NEW = "d128a786ee2ee570eb23ff5862ec148b43cfad0b"


def digest(data: bytes | str) -> str:
    return sha256(data.encode() if isinstance(data, str) else data).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def baseline(name: str) -> list[dict]:
    text = subprocess.check_output(
        ["git", "show", f"{BASE}:research/evidence/{name}"], cwd=ROOT, text=True)
    return [json.loads(s) for s in text.splitlines() if s.strip()]


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def norm(url: str) -> str:
    p = urlsplit(url.rstrip("/"))
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), p.query, ""))


def arxiv(url: str) -> tuple[str, str] | None:
    m = re.search(r"arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})(v\d+)?", url)
    return (m[1], m[2] or "") if m else None


def identity(url: str, edition: str = "") -> str:
    a = arxiv(url)
    if a:
        v = a[1] or ((m[0] if (m := re.search(r"v\d+", edition)) else ""))
        return "arxiv:" + a[0] + v
    return norm(url)


def links(text: str) -> list[str]:
    """Markdown destinations, preserving balanced parentheses in DOI paths."""
    text = re.sub(r"```.*?```|~~~.*?~~~", "", text, flags=re.S)
    result = []
    for match in re.finditer(r"\]\((https?://)|<(https?://)", text):
        start = match.start(1) if match[1] else match.start(2)
        depth, end = 0, start
        while end < len(text):
            c = text[end]
            if c.isspace() or c in '<>"':
                break
            if c == "(":
                depth += 1
            if c == ")":
                if depth == 0:
                    break
                depth -= 1
            end += 1
        result.append(text[start:end])
    return result


def english_words(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:['’_-][A-Za-z]+)*", text))


def short_quote(text: str, maximum: int = 12) -> str:
    words = list(re.finditer(r"[A-Za-z]+(?:['’_-][A-Za-z]+)*", text))
    return text[:words[maximum - 1].end()] if len(words) > maximum else text


def infer_kind(url: str) -> str:
    host = urlsplit(url).netloc.lower()
    if arxiv(url) or "doi.org" in host or "aclanthology" in host or "ijcai.org" in host:
        return "academic_paper"
    if host == "github.com":
        return "official_documentation" if "/blob/" in url and "/docs/" in url else "official_repository"
    if host == "api.github.com" or any(x in host for x in ("reddit", "ycombinator", "zhihu", "forum.")):
        return "platform_metadata"
    if "/blog/" in url or "/engineering/" in url or "/index/" in url or "/research/" in url:
        return "official_article"
    return "official_documentation"


class Integration:
    def __init__(self):
        self.sources = {s["source_id"]: s for s in read_jsonl(LEDGER / "sources.jsonl")}
        self.evidence = {e["evidence_id"]: e for e in read_jsonl(LEDGER / "evidence.jsonl")}
        self.claims = {c["claim_id"]: c for c in read_jsonl(LEDGER / "claims_v2.jsonl")}
        backlog_path = LEDGER / "claims_backlog.jsonl"
        self.backlog = {c["claim_id"]: c for c in read_jsonl(backlog_path)} if backlog_path.exists() else {}
        self.old_sources = {s["source_id"]: s for s in baseline("sources.jsonl")}
        self.old_evidence = baseline("evidence.jsonl")
        legacy_ids = {e["evidence_id"] for e in self.old_evidence}
        self.evidence = {eid: e for eid, e in self.evidence.items()
                         if eid in legacy_ids or e.get("integration_revision") != STAMP}
        self.old_claims = {c["claim_id"]: c for c in baseline("claims_v2.jsonl")}
        self.claims = {cid: c for cid, c in self.claims.items()
                       if cid not in self.old_claims and c.get("integration_revision") != STAMP}
        self.claims = {**self.old_claims, **self.claims}
        self.captures = []
        self.by_name = {}
        self.by_url = defaultdict(list)
        self.quote_usage = Counter()
        self.input_hashes = {}
        self.issues = []
        self.rejected_captures = []
        self.pending_support = []
        self.citations = defaultdict(set)
        for p in sorted((ROOT / "manuscript").rglob("*.md")):
            t = p.read_text()
            self.input_hashes[rel(p)] = digest(t)
            for u in links(t):
                self.citations[u].add(rel(p))
        self.product_urls = set(links((REVISION / "disposition_products.md").read_text()))
        self.up_sources = read_jsonl(REVIEW / "sources.jsonl")
        self.up_evidence = read_jsonl(REVIEW / "evidence.jsonl")
        self.up_claims = read_jsonl(REVIEW / "claims.jsonl")
        self.fix_gsme()
        for s in self.sources.values():
            m = re.search(r"arXiv:(\d{4}\.\d{4,5}v\d+)", s.get("version_or_commit") or "")
            if arxiv(s["raw_url"]) and m:
                s.setdefault("legacy_metadata", self.old_sources.get(s["source_id"], {}))
                s["raw_url"] = "https://arxiv.org/abs/" + m[1]
                s["canonical_locator"] = "arxiv:" + m[1]
        self.reindex()

    def fix_gsme(self):
        s = self.sources["e6aa3f68badc6151"]
        s.setdefault("legacy_metadata", self.old_sources[s["source_id"]])
        s.update(raw_url="https://arxiv.org/abs/2607.13683v1", canonical_locator="arxiv:2607.13683v1",
                 version_or_commit="arXiv:2607.13683v1", revision_note="旧题名对应v1；历史v2标签错误已更正。v2另建来源，不覆盖旧记录。")
        s["url_aliases"] = [u for u in s.get("url_aliases", []) if identity(u) == "arxiv:2607.13683v1"]

    def reindex(self):
        self.source_keys = {identity(s["raw_url"], s.get("version_or_commit") or ""): sid
                            for sid, s in self.sources.items()}

    def add_capture(self, url, text, path, meta, *, pointer=None, title=None, edition=None,
                    capture_name=None, relation="source_content", kind=None):
        a = arxiv(url)
        if a and not a[1]:
            m = re.search(r"arXiv:" + re.escape(a[0]) + r"(v\d+)\b", text)
            version = m[1] if m else ""
            if not version:
                m = re.search(r"this version, (v\d+)", text[:800])
                version = m[1] if m else ""
            if version:
                edition = "arXiv:" + a[0] + version
        edition = edition or ("arXiv:" + a[0] + a[1] if a and a[1] else "web snapshot " + STAMP)
        spec = re.search(r"modelcontextprotocol\.io/specification/(\d{4}-\d{2}-\d{2})/", url)
        if spec:
            edition = "MCP specification " + spec[1] + "; web snapshot " + STAMP
        item = dict(url=url, key=identity(url, edition), text=text, capture_path=rel(path),
                    capture_sha256=digest(path.read_bytes()), text_sha256=digest(text),
                    accessed_at=meta.get("accessed_at") or meta.get("retrieved_at") or STAMP,
                    title=title or meta.get("title") or url, edition=edition,
                    pointer=pointer, relation=relation, source_type=kind or infer_kind(url))
        self.captures.append(item)
        self.by_url[norm(url)].append(item)
        if a and item["key"].endswith(tuple("v" + str(i) for i in range(1, 50))):
            suffix = item["key"].removeprefix("arxiv:")
            for surface in ("abs", "html", "pdf"):
                self.by_url[norm("https://arxiv.org/" + surface + "/" + suffix)].append(item)
        if capture_name:
            self.by_name[capture_name] = item
        self.input_hashes[rel(path)] = item["capture_sha256"]
        return item

    def load_captures(self):
        for folder in (REVIEW / "retrieval", REVISION / "retrieval"):
            for path in sorted(folder.glob("*.json")):
                if path.name.startswith("search-"):
                    continue
                data = json.loads(path.read_text())
                if not isinstance(data.get("text"), str) or not data.get("requested_url"):
                    continue
                if digest(data["text"]) != data.get("text_sha256"):
                    self.issues.append("hash_mismatch: " + rel(path))
                    continue
                rejected = None
                if re.search(r"just a moment|access denied|captcha", data.get("title", ""), re.I) or re.search(
                        r"Are you a robot\?|Please confirm you are a human", data["text"][:1000]):
                    rejected = "challenge_page_not_source_content"
                if norm(data["requested_url"]) == "https://docs.cursor.com/hooks" and not re.search(
                        r"beforeShellExecution|afterFileEdit|beforeReadFile|stdio|stdin", data["text"]):
                    rejected = "documentation_landing_page_not_hooks_content"
                if rejected:
                    self.rejected_captures.append({"url":data["requested_url"], "capture":rel(path), "reason":rejected})
                    self.input_hashes[rel(path)] = digest(path.read_bytes())
                    continue
                item = self.add_capture(data["requested_url"], data["text"], path, data,
                                        pointer="/text", capture_name=path.stem, edition=data.get("edition"))
                if path.stem == "current-cursor-hooks":
                    old_hooks_url = "https://docs.cursor.com/hooks"
                    new_hooks_url = "https://cursor.com/cn/docs/hooks"
                    if norm(item["url"]) != new_hooks_url:
                        raise ValueError("unexpected Cursor hooks replacement URL")
                    self.by_url[old_hooks_url].append(item)
                    self.source_keys[old_hooks_url] = "b1f6985403c6eaa1"
                    self.source_keys[new_hooks_url] = "b1f6985403c6eaa1"
                if data.get("canonical_doi"):
                    canonical = norm(data["canonical_doi"])
                    item["key"] = canonical
                    item["canonical_doi"] = data["canonical_doi"]
                    self.by_url[canonical].append(item)
                    if canonical in self.source_keys:
                        self.source_keys[norm(data["requested_url"])] = self.source_keys[canonical]
                    if data.get("pdf_sha256"):
                        pdf = path.with_name("strips-original.pdf")
                        if digest(pdf.read_bytes()) != data["pdf_sha256"]:
                            raise ValueError("author PDF hash mismatch")
                        item["pdf_document"] = dict(path=rel(pdf), sha256=data["pdf_sha256"],
                                                     extraction=data.get("extraction"), first_printed_page=189)
                        self.input_hashes[rel(pdf)] = data["pdf_sha256"]
                if data.get("url"):
                    self.by_url[norm(data["url"])].append(item)
        vendor = REVIEW / "vendor_probe"
        wanted = set(map(norm, list(self.citations) + list(self.product_urls)))
        for cap_path in sorted(vendor.rglob("*.capture.json")):
            meta = json.loads(cap_path.read_text())
            if meta.get("exit_code") != 0:
                continue
            path = Path(str(cap_path).removesuffix(".capture.json"))
            if not path.exists() or digest(path.read_bytes()) != meta.get("sha256"):
                self.issues.append("hash_mismatch: " + rel(cap_path))
                continue
            endpoint = next((s for s in meta.get("command", []) if s.startswith("repos/")), "")
            m = re.match(r"repos/([^/]+/[^/]+)/contents/(.+)\?ref=([^&]+)$", endpoint)
            if m:
                repo, name, commit = m.groups()
                if not re.fullmatch(r"[a-f0-9]{40}", commit):
                    tag_path = vendor / ("openhands" if repo == "OpenHands/OpenHands" else "sdk" if repo == "OpenHands/software-agent-sdk" else "codex" if repo == "openai/codex" else "dsh") / "tags" / (commit + ".json")
                    tag_cap = Path(str(tag_path) + ".capture.json")
                    if not tag_path.exists() or not tag_cap.exists():
                        continue
                    tag_meta = json.loads(tag_cap.read_text())
                    if tag_meta.get("exit_code") != 0 or digest(tag_path.read_bytes()) != tag_meta.get("sha256"):
                        raise ValueError("unverified tag resolution " + str(tag_path))
                    tag = json.loads(tag_path.read_text())
                    commit = tag.get("sha") or tag.get("object", {}).get("sha", "")
                    if not re.fullmatch(r"[a-f0-9]{40}", commit):
                        continue
                    self.input_hashes[rel(tag_path)] = digest(tag_path.read_bytes())
                self.add_capture(f"https://github.com/{repo}/blob/{commit}/{name}", path.read_text(), path,
                                 meta, edition="git " + commit, title=repo + " / " + name)
                continue
            if not path.suffix == ".json":
                continue
            data = json.loads(path.read_text())
            repo_match = re.match(r"repos/([^/]+/[^/]+)", endpoint)
            repo = repo_match[1] if repo_match else ""
            if "releases" in endpoint:
                entries = data if isinstance(data, list) else [data]
                for i, row in enumerate(entries):
                    u = row.get("html_url", "")
                    if norm(u) not in wanted:
                        continue
                    self.add_capture(u, row.get("body") or row.get("name") or row.get("tag_name", ""),
                                     path, meta, pointer=(f"/{i}/body" if isinstance(data, list) else "/body"),
                                     title=repo + " " + row.get("tag_name", ""),
                                     edition="release " + row.get("tag_name", "") + "; published_at=" + str(row.get("published_at")))
            elif isinstance(data, dict) and "/commits/" in endpoint and data.get("sha"):
                self.add_capture(data["html_url"], data["commit"]["message"], path, meta,
                                 pointer="/commit/message", title=data["commit"]["message"].splitlines()[0],
                                 edition="git " + data["sha"], relation="commit_metadata")
            elif isinstance(data, dict) and "/pulls/" in endpoint and data.get("merge_commit_sha"):
                u = f"https://github.com/{repo}/commit/{data['merge_commit_sha']}"
                self.add_capture(u, data["title"], path, meta, pointer="/title", title=data["title"],
                                 edition="git " + data["merge_commit_sha"], relation="merged_pull_request_metadata")
            elif isinstance(data, dict) and endpoint == "repos/" + repo and data.get("html_url"):
                self.add_capture(data["html_url"], data.get("description") or data["full_name"], path, meta,
                                 pointer="/description", title=data["full_name"],
                                 edition="repository metadata snapshot " + STAMP, relation="repository_metadata")

    def find(self, url, edition=""):
        candidates = list(self.by_url.get(norm(url), []))
        a = arxiv(url)
        if a:
            wanted = identity(url, edition)
            if re.search(r"v\d+$", wanted):
                candidates = [c for c in self.captures if c["key"] == wanted]
        m = re.search(r"git ([a-f0-9]{40})", edition)
        if m and "github.com/" in url:
            p = urlsplit(url).path.strip("/").split("/")
            if len(p) >= 5 and p[2] == "blob":
                fixed = "https://github.com/" + "/".join(p[:3] + [m[1]] + p[4:])
            elif len(p) == 2:
                fixed = f"https://github.com/{'/'.join(p)}/blob/{m[1]}/README.md"
            else:
                fixed = url
            candidates = [c for c in self.by_url.get(norm(fixed), []) if m[1] in c["edition"]]
        return max(candidates, key=lambda c: (c["relation"] == "source_content", len(c["text"])), default=None)

    def source(self, url, capture=None, upstream=None):
        capture = capture or self.find(url)
        edition = capture["edition"] if capture else (upstream or {}).get("edition", "")
        key = identity(url, edition)
        sid = self.source_keys.get(key)
        if not sid and not capture:
            sid = next((s["source_id"] for s in self.sources.values()
                        if norm(s["raw_url"]) == norm(url)), None)
        if not sid:
            sid = digest(key)[:16]
            if sid in self.sources:
                sid = digest("revision-source:" + key)[:16]
            self.sources[sid] = dict(source_id=sid, canonical_locator=key, raw_url=url,
                                     title=(upstream or {}).get("title") or (capture or {}).get("title") or url,
                                     authors=(upstream or {}).get("authors"), year=None,
                                     source_type=infer_kind(url), metadata_status="unverified",
                                     registered_at=STAMP, accessed_at=None, version_or_commit=None)
            self.source_keys[key] = sid
        s = self.sources[sid]
        if arxiv(url) and arxiv(url)[1] and not s.get("version_or_commit"):
            s["version_or_commit"] = "arXiv:" + "".join(arxiv(url)) + "; identity not yet verified"
        aliases = set(s.get("url_aliases", []))
        aliases.add(url)
        if capture:
            s.setdefault("legacy_metadata", self.old_sources.get(sid, {}))
            s.update(metadata_status="verified", accessed_at=capture["accessed_at"],
                     version_or_commit=capture["edition"], capture_path=capture["capture_path"],
                     capture_sha256=capture["capture_sha256"], text_sha256=capture["text_sha256"],
                     capture_locator={"json_pointer":capture["pointer"], "relation":capture["relation"]},
                     verification_scope="source_identity_version_and_capture; not_all_claims_or_replication")
            s["retrieved_url"] = capture["url"]
            if sid == "b1f6985403c6eaa1" and norm(capture["url"]) == "https://cursor.com/cn/docs/hooks":
                aliases.add("https://docs.cursor.com/hooks")
                s["raw_url"] = "https://cursor.com/cn/docs/hooks"
                s["canonical_locator"] = s["raw_url"]
                s["revision_note"] = "旧docs.cursor.com/hooks捕获仅为目录并已拒绝；当前原文来自cursor.com/cn/docs/hooks。旧URL仅保留身份别名，不作当前内容证据。"
            if capture.get("canonical_doi"):
                aliases.add(capture["url"])
                s["source_type"] = "academic_paper"
                s["pdf_document"] = capture.get("pdf_document")
            if capture["title"] != capture["url"]:
                s["title"] = re.sub(r"^\[[^]]+\]\s*", "", capture["title"])
            a = arxiv(url)
            if a and re.search(r"v\d+$", key):
                suffix = key.removeprefix("arxiv:")
                s["raw_url"] = "https://arxiv.org/abs/" + suffix
                s["canonical_locator"] = key
                aliases.update("https://arxiv.org/" + mode + "/" + suffix for mode in ("abs", "html"))
        if upstream:
            s["upstream_source_id"] = upstream["source_id"]
            kind = upstream["source_type"]
            if kind.startswith("preprint"):
                kind = "academic_paper"
            elif kind in {"official_release_notes", "official_specification"}:
                kind = "official_documentation"
            elif kind.startswith("community"):
                kind = "platform_metadata"
                s["core_claim_eligible"] = False
                s["source_role"] = "community_discovery_only"
            s["source_type"] = kind
            s["authors"] = upstream.get("authors")
            if upstream.get("temporal_class") == "metadata_uncertain":
                s["metadata_status"] = "unverified"
                s["metadata_note"] = "编号月份与提交日冲突未解决；已读原文不等于身份日期全部核实。"
        s["url_aliases"] = sorted(aliases - {s["raw_url"]})
        s.setdefault("verification_scope", "legacy_metadata_record_only; no_current_verbatim_validation")
        return sid

    def add_evidence(self, sid, capture, anchor, summary, *, eid=None, role="content", quote=True):
        if anchor not in capture["text"]:
            raise ValueError("missing exact anchor: " + capture["capture_path"] + " : " + anchor)
        offset = capture["text"].index(anchor)
        line = capture["text"][:offset].count("\n") + 1
        group = capture["key"]
        q = short_quote(anchor)
        if not quote or self.quote_usage[group] + english_words(q) > 25:
            q = ""
        eid = eid or digest("20260919|" + sid + "|" + anchor + "|" + summary)[:16]
        self.quote_usage[group] += english_words(q)
        context_start = capture["text"].rfind("\n\n", 0, offset) + 2
        if context_start == 1:
            context_start = 0
        context_end = capture["text"].find("\n\n", offset + len(anchor))
        if context_end < 0:
            context_end = len(capture["text"])
        e = dict(evidence_id=eid, source_id=sid, evidence_type="direct_quote" if q else "source_summary",
                 quote=q, summary=summary, captured_at=capture["accessed_at"],
                 capture_sha256=capture["capture_sha256"], text_sha256=capture["text_sha256"],
                 locator=dict(capture=capture["capture_path"], json_pointer=capture["pointer"],
                              text_char_offset=offset, text_char_end=offset+len(anchor), text_line=line,
                              source_relation=capture["relation"],
                              context_char_start=context_start, context_char_end=context_end),
                 validation="exact_quote_and_capture_hash" if q else "located_summary_with_capture_hash",
                 review_scope=role, quote_work_key=group, integration_revision=STAMP)
        e["span_sha256"] = digest(anchor)
        if capture.get("pdf_document"):
            e["pdf_document"] = capture["pdf_document"]
            page_index = capture["text"][:offset].count("\f")
            e["locator"]["pdf_page"] = page_index + 1
            e["locator"]["printed_page"] = capture["pdf_document"]["first_printed_page"] + page_index
        self.evidence[eid] = e
        return eid

    def legacy(self):
        for old in self.old_sources.values():
            s = self.sources[old["source_id"]]
            cap = self.find(s["raw_url"], s.get("version_or_commit") or "")
            self.source(s["raw_url"], cap)
        for original in self.old_evidence:
            e = dict(original)
            s = self.sources[e["source_id"]]
            cap = self.find(s["raw_url"], s.get("version_or_commit") or "")
            q = e.get("quote", "")
            exact = bool(cap and q and q in cap["text"])
            group = cap["key"] if cap else s["canonical_locator"]
            direct = exact and english_words(q) + self.quote_usage[group] <= 25 and original["evidence_type"] == "direct_quote"
            e.update(legacy_evidence_type=original["evidence_type"], legacy_locator=original.get("locator"),
                     integration_revision=STAMP, review_scope="historical_record_not_automatic_claim_support")
            if direct:
                self.add_evidence(e["source_id"], cap, q, "历史引文在本次匹配版本原文中逐字定位；不证明原检索时即如此。", eid=e["evidence_id"])
                current = self.evidence[e["evidence_id"]]
                self.quote_usage[group] += english_words(q) - english_words(current["quote"])
                current["quote"] = q
                self.evidence[e["evidence_id"]].update(legacy_evidence_type=original["evidence_type"],
                                                      legacy_locator=original.get("locator"),
                                                      historical_captured_at=original.get("captured_at"))
            else:
                e.update(evidence_type="legacy_paraphrase", validation="not_verbatim_validated",
                         history_note="保留原quote内容和历史定位；该字段是历史转述存量，不得作为可逐字核实的直接引文。")
                if e["evidence_id"] == "e422a657d08ba6ed":
                    e["history_note"] += " 当前v9原文为15个裁判、超过150000次评价；旧12个/100000次表述不用于当前事实，见C022的新证据。"
                if exact:
                    e["history_note"] += " 本次可匹配文本但未作为直接引文保留（原类型或来源累计引用预算）。"
                self.evidence[e["evidence_id"]] = e

    def import_review(self):
        upstream_map = {}
        e_by_source = {e["source_id"]: e for e in self.up_evidence}
        c_by_source = {c["cited_source_ids"][0]: c for c in self.up_claims}
        for row in self.up_sources:
            cap = self.by_name[row["capture_id"]]
            sid = self.source(row["url"], cap, row)
            upstream_map[row["source_id"]] = sid
            old_e = e_by_source[row["source_id"]]
            old_c = c_by_source[row["source_id"]]
            eid = self.add_evidence(sid, cap, old_e["quote"], old_c["text"],
                                    eid="r19-"+old_e["evidence_id"],
                                    role="community_signal" if row["source_type"].startswith("community") else "curated_scoped_source_statement")
            if row["source_type"].startswith("community"):
                continue
            cid = "R20260919_" + old_c["claim_id"]
            chapters = sorted({Path(p).name[:2] for u, ps in self.citations.items()
                               if identity(u, cap["edition"]) == cap["key"] for p in ps
                               if "/chapters/" in p})
            record = dict(claim_id=cid, chapter=",".join(chapters),
                                   claim_type="research_result" if row["source_type"].startswith("preprint") else "vendor_claim",
                                   text=old_c["text"], cited_source_ids=[sid], evidence_ids=[eid],
                                   support_status="needs_review" if self.sources[sid]["metadata_status"] != "verified" else "supported",
                                   scope_note="仅限已存原文的窄主张；中文summary须与完整定位段落合读，不是短摘单独蕴含所有分句；未复现实验。",
                                   provenance_claim_id=old_c["claim_id"], integration_revision=STAMP)
            if row.get("temporal_class") == "metadata_uncertain":
                record.update(disposition="deferred", support_status="needs_review",
                              deferral_reason="研究线索的编号/日期冲突未解决；未用于书稿承重事实。")
                self.backlog[cid] = record
                self.claims.pop(cid, None)
            else:
                self.claims[cid] = record
                self.backlog.pop(cid, None)
                if not chapters:
                    record["scope_note"] += " 当前正文未逐项引用，保留为已核对的研究背景子集，不计作章节逐句覆盖。"

    def proof(self, url_or_name, anchor, summary):
        cap = self.by_name.get(url_or_name) or self.find(url_or_name)
        if not cap:
            raise ValueError("missing capture: " + url_or_name)
        sid = self.source(cap["url"], cap)
        eid = self.add_evidence(sid, cap, anchor, summary, role="curated_scoped_content_review")
        return sid, eid

    def claim(self, cid, chapter, text, proofs, scope, status="supported", kind="vendor_claim"):
        sids = list(dict.fromkeys(s for s, e in proofs))
        eids = list(dict.fromkeys(e for s, e in proofs))
        row = dict(claim_id=cid, chapter=chapter, claim_type=kind, text=text,
                   cited_source_ids=sids, evidence_ids=eids, support_status=status,
                   scope_note=scope, integration_revision=STAMP)
        if cid in self.old_claims:
            row["legacy_claim"] = self.old_claims[cid]
        self.claims[cid] = row

    def curate(self):
        curate(self)
        curate_legacy_updates(self)

    def register_all_links(self):
        for u in sorted(set(self.citations) | self.product_urls):
            self.source(u)
        # Supplementary captures verify identity only; their reading is not a new claim.
        for name, cap in sorted(self.by_name.items()):
            if name.startswith("old-"):
                self.source(cap["url"], cap)

    def old_claim_status(self):
        for cid, old in self.old_claims.items():
            if self.claims[cid].get("integration_revision") == STAMP:
                continue
            c = dict(old)
            c.update(support_status="needs_review", legacy_claim=old,
                     scope_note=(old.get("scope_note", "") + " 本次尚未为全部分句重新绑定可核对原文；历史supported不自动继承。"),
                     integration_revision=STAMP)
            c["support_selection"] = [
                {"source_id":sid, "url":self.sources[sid]["raw_url"],
                 "reason":"awaiting_curated_content_review" if self.find(
                     self.sources[sid]["raw_url"], self.sources[sid].get("version_or_commit") or "")
                 else "matching_edition_capture_missing"}
                for sid in c["cited_source_ids"]]
            self.claims[cid] = c

    def validate(self):
        assert links("[STRIPS](https://doi.org/10.1016/0004-3702(71)90010-5)") == ["https://doi.org/10.1016/0004-3702(71)90010-5"]
        for s in self.sources.values():
            assert s["source_type"] in SOURCE_TYPES
            assert s["metadata_status"] in {"verified", "unverified"}
            if s["metadata_status"] == "verified":
                assert s.get("accessed_at") and s.get("version_or_commit")
            if s.get("capture_path"):
                raw = (ROOT / s["capture_path"]).read_bytes()
                assert digest(raw) == s["capture_sha256"], s["source_id"]
                text = pointer_text(raw, s.get("capture_locator", {}).get("json_pointer"))
                assert digest(text) == s["text_sha256"], s["source_id"]
            a = arxiv(s["raw_url"])
            if a and a[1]:
                assert a[0]+a[1] in s.get("version_or_commit", ""), s
        quotas = Counter()
        per_source = Counter()
        for e in self.evidence.values():
            assert e["source_id"] in self.sources
            if e.get("evidence_type") in {"direct_quote", "source_summary"}:
                assert isinstance(e.get("locator"), dict), e["evidence_id"]
                loc = e["locator"]
                raw = (ROOT / loc["capture"]).read_bytes()
                assert digest(raw) == e["capture_sha256"]
                text = pointer_text(raw, loc.get("json_pointer"))
                assert digest(text) == e["text_sha256"]
                start = loc["text_char_offset"]
                assert digest(text[start:loc["text_char_end"]]) == e["span_sha256"]
                if e.get("evidence_type") == "direct_quote":
                    assert text[start:start+len(e["quote"])] == e["quote"]
                    quotas[e["quote_work_key"]] += english_words(e["quote"])
                    per_source[e["source_id"]] += english_words(e["quote"])
        assert all(n <= 25 for n in quotas.values()), quotas
        assert all(n <= 25 for n in per_source.values()), per_source
        for c in list(self.claims.values()) + list(self.backlog.values()):
            assert c["support_status"] in {"supported", "partial", "unsupported", "needs_review"}
            assert all(s in self.sources for s in c["cited_source_ids"])
            for eid in c["evidence_ids"]:
                assert self.evidence[eid]["source_id"] in c["cited_source_ids"]
            if c["claim_id"] in self.claims:
                assert all(self.sources[s].get("core_claim_eligible", True) for s in c["cited_source_ids"])
            if c["support_status"] == "supported":
                assert all(self.sources[s]["metadata_status"] == "verified" for s in c["cited_source_ids"])
                assert c["evidence_ids"] and all(self.evidence[e]["evidence_type"] != "legacy_paraphrase" for e in c["evidence_ids"])
        return quotas


def pointer_text(raw, pointer):
    if pointer is None:
        return raw.decode()
    value = json.loads(raw)
    for component in pointer.strip("/").split("/"):
        component = component.replace("~1", "/").replace("~0", "~")
        value = value[int(component)] if isinstance(value, list) else value[component]
    return value or ""


def curate_legacy_updates(x):
    """Reviewed support choices: absent captures stay pending, never guessed.

    Every choice supplies a deliberately bounded claim and exact anchors that
    were read in its matching edition. This is not a keyword-based truth test.
    Add further choices only after reading the newly supplied raw content.
    """
    choices = [
        ("C001", "STRIPS将问题求解表述为寻找操作序列，把初始世界模型变成能证明目标公式成立的世界模型。", [
            ("b370b4854c644418", "a sequence o f operators", "Stanford作者原文镜像第189页摘要，OCR的o f按原文保留，不能凭修正文法伪造逐字引文。"),
            ("b370b4854c644418", "given goal formula can be proven to be true", "同一摘要说明从给定初始世界模型到目标公式可证明为真的模型。")]),
        ("C002", "Contract Net通过任务持有节点与潜在执行节点的协商分配分布式问题求解任务。", [
            ("fdbfceedda4b3792", "Task distribution is affected by a negotiation process", "IEEE原始摘要将任务分配描述为有待执行任务的节点与潜在执行节点间的协商。")]),
        ("C003", "ReAct将推理轨迹与任务动作交替生成，利用外部环境信息更新动作计划。", [
            ("e504ba1ba9c3fffc", "reasoning traces and task-specific actions in an interleaved manner", "v3摘要说明推理轨迹与动作交替，并通过外部信息支持计划与异常处理。")]),
        ("C004", "SWE-agent v3研究Agent-Computer Interface，并报告定制接口改善文件编辑、仓库导航及执行测试等能力。", [
            ("ffabd76a77f0fd21", "SWE-agent's custom agent-computer interface (ACI) significantly enhances", "v3摘要列出定制ACI与文件、导航、执行能力；效果为作者报告，不是本书复现。")]),
        ("C005", "SWE-bench v3以真实GitHub issue及对应pull request构建仓库级代码修复评测。", [
            ("b36ffb44e7a44c44", "drawn from real GitHub issues and corresponding pull requests", "v3摘要说明真实issue/PR与Python仓库构成；此窄claim不单凭摘要认证每个测试的实现。")]),
        ("C006", "OpenAI在2026年说明停止报告SWE-bench Verified分数，主要指出测试拒绝正确解及训练污染问题。", [
            ("33e5e5bcd68981ac", "we have stopped reporting SWE-bench Verified scores", "2月23日官方说明停止报告该基准分数，不冒充全行业统一决定。"),
            ("33e5e5bcd68981ac", "Tests reject correct solutions", "问题之一是部分测试拒绝功能正确的提交。"),
            ("33e5e5bcd68981ac", "Training on solutions", "另一问题是所测模型在训练中暴露于部分题目或答案的证据。")]),
        ("C007", "Claude Agent SDK嵌入Claude Code的模型—工具结果循环，返回cost/session信息，并在上下文接近上限时自动压缩。", [
            ("b174364e9eb69c7d", "the same execution loop that powers Claude Code", "当前SDK文档明确循环由Claude Code提供。"),
            ("b174364e9eb69c7d", "token usage, cost, and session ID", "结果消息携带这些元数据，不能据返回消息判业务验收。"),
            ("b174364e9eb69c7d", "the SDK automatically compacts the conversation", "上下文接近上限触发自动压缩，属于SDK行为而非Messages API同名接口。")]),
        ("C008", "Anthropic报告其内部使用中sandboxing使Claude Code权限提示减少84%。", [
            ("c765441e9673d957", "reduces permission prompts by 84%", "供应商内部结果；不外推到所有任务，不当作安全强度或跨产品排名。")]),
        ("C011", "Cursor把长输出、会话历史、MCP描述和终端输出外置为文件；其A/B报告实际使用MCP的运行token减少46.9%，幅度随安装数量变化。", [
            ("f92116a7a4372c7c", "把输出写入文件", "长工具输出以文件提供读取能力。"),
            ("f92116a7a4372c7c", "将对话历史作为文件", "压缩后仍可检索对话历史文件。"),
            ("f92116a7a4372c7c", "通过将工具描述同步到一个文件夹", "MCP工具描述按需发现。"),
            ("f92116a7a4372c7c", "终端的输出同步到本地文件系统", "集成终端输出映射为文件。"),
            ("f92116a7a4372c7c", "总 token 消耗减少了 46.9%", "厂商限定人群中的内部A/B结果，不定义为同任务配对，也不外推所有任务。")]),
        ("C012", "Cursor披露按提供商和模型版本定制提示与工具形式，并用离线评估和在线对照迭代。", [
            ("173ad132e1d12717", "针对不同提供商，甚至不同模型版本的自定义提示", "模型特化的提示和工具格式是官方披露的设计，非源码审计。"),
            ("173ad132e1d12717", "我们会运行离线评估", "上线前运行离线评估并迭代。"),
            ("173ad132e1d12717", "在线实验，同时部署两个或更多框架变体", "在线A/B补充离线评估，不证明固定同任务配对实验。")]),
        ("C016", "Reflexion将反馈转成保存在情景记忆中的语言反思，用于后续trial，不更新模型权重。", [
            ("3fb5d6b0a837235b", "not by updating weights, but instead through linguistic feedback", "v4摘要说明通过语言反馈而非权重更新强化代理。"),
            ("3fb5d6b0a837235b", "reflective text in an episodic memory buffer", "同段说明反思文字保存到episodic buffer并影响后续试验。")]),
        ("C017", "Voyager组合自动课程、可执行代码技能库与包含环境反馈/执行错误的迭代提示，并复用技能处理新任务。", [
            ("b71b1297191d5227", "an automatic curriculum that maximizes exploration", "v2摘要列出自动课程、可执行技能库及含环境反馈/执行错误的迭代提示三组件。"),
            ("b71b1297191d5227", "utilize the learned skill library in a new Minecraft world", "作者报告在新Minecraft世界复用技能；不外推为所有领域的跨任务保证。")]),
        ("C022", "两篇指定版本研究分别报告LLM评价中的自偏好及位置偏差，结论受所测模型与任务限制。", [
            ("d7ef622187acc55b", "GPT-4 exhibits a significant degree of self-preference bias", "Self-Preference v2所测GPT-4的作者结果；不认证全部裁判或把熟悉度假说当确定根因。"),
            ("ede733cb363a2024", "position bias is not due to random chance", "位置偏差v9报告非随机偏差，实际规模15个裁判/超过15万次；旧12/10万转述仅留历史，不用于当前claim。")]),
        ("C023", "EvilGenie v2与SpecBench v2分别把编程奖励投机和可见/留出测试表现差距作为评测对象。", [
            ("ef7c1d01fba88729", "a benchmark for reward hacking in programming settings", "EvilGenie v2定义编程奖励投机基准，方法及产品实验未由本书复现。"),
            ("6ddb79c39a2b95ad", "the gap in pass rates on these two suites", "本次当前原文为9月9日的SpecBench v2，比较可见验证与留出组合测试；v1记录保留。", "current")]),
        ("C024", "Anthropic报告其BrowseComp分析中三因素解释95%性能方差，token单项解释80%；其数据中Agent与多Agent约用聊天4倍和15倍token。", [
            ("a3afc1e8c7c23916", "three factors explained 95% of the performance variance", "作者在BrowseComp分析中的解释方差，不是token的因果贡献定律。"),
            ("a3afc1e8c7c23916", "token usage by itself explains 80%", "同段说明token单项解释比例，另两因素是工具调用次数和模型选择。"),
            ("a3afc1e8c7c23916", "agents typically use about 4× more tokens", "厂商数据中的约数，不能外推所有Agent任务。"),
            ("a3afc1e8c7c23916", "multi-agent systems use about 15× more tokens", "厂商数据中的约数，需结合任务价值与费用条件。")]),
        ("C025", "Pi当前README列默认read/write/edit/bash四工具，且将MCP、子代理、权限弹窗、计划模式与后台bash留给扩展或外部组织。", [
            ("97416d4ba88591c5", "read, write, edit, and bash", "当前README默认四工具。", "current"),
            ("97416d4ba88591c5", "No MCP.", "README核心设计不内置MCP，允许外部工具/扩展。", "current"),
            ("97416d4ba88591c5", "No sub-agents.", "子代理由外部实例或扩展组织。", "current"),
            ("97416d4ba88591c5", "No permission popups.", "核心不内置权限弹窗，不等于无需环境安全控制。", "current"),
            ("97416d4ba88591c5", "No plan mode.", "计划以文件或扩展实现。", "current"),
            ("97416d4ba88591c5", "No background bash.", "README建议用tmux承接此类操作。", "current")]),
    ]
    for cid, text, requirements in choices:
        ready, missing = [], []
        for requirement in requirements:
            source_id, anchor, summary = requirement[:3]
            original = x.old_sources[source_id]
            url = original["raw_url"]
            edition = "" if len(requirement) == 4 and requirement[3] == "current" else original.get("version_or_commit") or ""
            cap = x.find(url, edition)
            if not cap:
                missing.append({"url":url, "reason":"matching_edition_capture_missing"})
            elif anchor not in cap["text"]:
                missing.append({"url":url, "reason":"reviewed_content_anchor_missing", "capture":cap["capture_path"]})
            else:
                ready.append((url, cap, anchor, summary))
        if missing:
            x.pending_support.append({"claim_id":cid, "missing":missing})
            continue
        proofs = []
        for url, cap, anchor, summary in ready:
            sid = x.source(url, cap)
            proofs.append((sid, x.add_evidence(sid, cap, anchor, summary, role="curated_legacy_claim_recheck")))
        old = x.old_claims[cid]
        x.claim(cid, old["chapter"], text, proofs,
                "本轮已读取明确版次/快照原文并收窄到可核对机制；结果为作者报告，未复现实验或认证整篇论文。新旧版次或当前网页与历史快照不混用，原claim留legacy_claim。",
                kind=old["claim_type"])


# Content decisions are curated below, never inferred from a successful fetch.
def curate(x):
    def blob(repo, commit, name):
        return f"https://github.com/{repo}/blob/{commit}/{name}"

    def put(cid, chapter, text, specifications, scope="固定原文/源码支持的窄契约；未运行供应商端到端任务。", kind="vendor_claim"):
        proofs = [x.proof(u, a, summary) for u, a, summary in specifications]
        x.claim(cid, chapter, text, proofs, scope, kind=kind)

    # The old 25 retain their IDs and historical records. Unsupported parts are
    # narrowed, or left needs_review rather than promoted by metadata alone.
    protocol = blob("openai/codex", CODEX_NEW, "codex-rs/app-server-protocol/src/protocol/common.rs")
    transport = blob("openai/codex", CODEX_OLD, "codex-rs/app-server/README.md")
    put("C009", "14", "Codex 8/27基线文档说明stdio用JSONL并省略jsonrpc字段；0.155.1协议枚举采用turn/interrupt请求、item/started及按类型区分的delta通知。", [
        (transport, 'header omitted on the wire', "基线README的Protocol/transport段说明双向JSON-RPC消息省略jsonrpc:2.0字段。"),
        (transport, 'newline-delimited JSON (JSONL)', "stdio传输使用换行分隔JSON；这里固定8/27基线版本。"),
        (protocol, '"turn/interrupt"', "当前固定协议将turn/interrupt列为客户端请求。"),
        (protocol, '"item/started"', "当前固定协议将item/started列为服务端通知。"),
        (protocol, '"item/agentMessage/delta"', "文本增量是类型化通知，不存在通用item/update；枚举检查另有本地probe。")])
    put("C010", "14", "Codex 0.154.0发布说明提供实验性worktree支持，可为新建或fork会话创建隔离checkout。", [
        ("https://github.com/openai/codex/releases/tag/rust-v0.154.0", "Experimental worktree support lets you create isolated checkouts", "固定release正文直接支持隔离checkout及new/forked session；保留experimental，不泛化为所有产品面。")],
        "使用已存官方release补证并收窄原claim；桌面端介绍页未在本轮重抓，不以App Server的泛并行叙述代替worktree证据。")
    put("C013", "16", "dsh固定当前README仍声明developer preview及兼容性破坏风险。", [
        (blob("deepseek-ai/deepseek-harness", REPO_NEW, "README.md"), "THERE WILL BE COMPATIBILITY-BREAKING CHANGES", "当前README的Developer preview段明确保留预览与破坏兼容警示。")])
    vm = blob("deepseek-ai/deepseek-harness", REPO_NEW, "packages/extensions/cordis-host-runner/src/sandbox.ts")
    ptc = blob("deepseek-ai/deepseek-harness", REPO_NEW, "packages/ptc-runtime/ptc-runtime-node/README.md")
    put("C014", "16", "dsh动态Cordis Host的node:vm不提供containment；旧run_code后端是worker thread，当前PTC改为受所选平台sandbox约束的新Node进程，两条路径不能混写。", [
        (vm, "is not containment", "动态Host源码明确不是安全隔离，宿主realm辅助函数仍有逃逸路径。"),
        (blob("deepseek-ai/deepseek-harness", REPO_OLD, "packages/code-runtime/code-runtime-worker-thread/README.md"), "The runtime contains a program without isolating it", "旧worker文档明确包含程序但不隔离宿主，信任姿态相当于bash。"),
        (ptc, "Each call starts a fresh Node process", "新版每次PTC新建Node进程，受所选OS sandbox约束；直接Node API仍可用。"),
        (ptc, "A requested restricted mode fails", "请求受限模式而sandbox backend不可用时失败；不是所有平台同等隔离。")])
    legacy_runtime = blob("OpenHands/OpenHands", "7fbb48c40679afd674970966b96185657d92a487", "openhands/runtime/README.md")
    conversation = blob("OpenHands/software-agent-sdk", SDK_NEW, "openhands-sdk/openhands/sdk/conversation/conversation.py")
    put("C015", "17", "OpenHands的EventStream/Runtime/ActionExecutor结构属于0.62.0历史实现；当前SDK1.49.2的Conversation按workspace选择本地会话或连接远端Agent Server的会话。", [
        (legacy_runtime, "The `Runtime` receives actions through the event stream.", "0.62.0历史Runtime通过事件流接收动作，不作为当前SDK的类图。"),
        (legacy_runtime, "It returns observations in the HTTP response.", "历史ActionExecutor通过execute_action端点接收动作，并经HTTP响应返回观测。"),
        (conversation, "based on the workspace type provided", "会话工厂根据workspace选择LocalConversation或RemoteConversation。"),
        (conversation, "RemoteConversation connects to a remote agent server", "远程会话连接Agent Server，与执行环境的部署模式分开。")])
    put("C018", "19,22", "Self-Harness v3把Weakness Mining、Harness Proposal和Proposal Validation连成循环，并由作者报告所测模型/任务上的留出改善。", [
        ("self-harness-current", "Weakness Mining", "摘要列出弱点挖掘、最小Harness提案与回归验证三个阶段。"),
        ("self-harness-current", "every final harness improves both held-in and held-out pass rates", "仅转述作者对所测九个模型/基准组合的报告，不作独立复现或普遍收益结论。")], kind="research_result")
    put("C019", "19,22,30", "当前正文采用HarnessBank v2：语义基因库按修改位置与失败病理保存/重组机制，提案与确定性评价分工，并以有效性、激活、配对显著性和增益门筛选候选。", [
        ("harnessbank-v2-full", "The deterministic evaluator controls sampling, scoring, activation logging, and statistical tests", "v2区分任务代理、演化代理、确定性评价器和基因库。"),
        ("harnessbank-v2-full", "applies four sequential gates", "v2先在采样任务上做四门筛选，随后完整训练集评价；同段说明语义基因库与重组。")], "采用v2机制，不继承GSME v1摘要数字；未声称独立复现或统计门自动可靠。", "research_result")
    put("C020", "21", "Living-Harness v2将轨迹和评价信号写入episodic memory与state graph，用于后续交互；工具与基础上下文保持冻结。", [
        ("living-harness-current", "while tools and base context remain frozen", "摘要明确工具和基础上下文冻结；同段描述轨迹反馈进入情景记忆和修复状态图。")], kind="research_result")
    put("C021", "22", "HSI在所测冻结模型与BALROG设置中未实质改善NLE；NLE全称NetHack Learning Environment。", [
        ("hsi-current", "it does not substantially improve NLE", "原文同段把初始能力和奖励反馈均有限列为限制；不能据此作普遍能力上限的因果证明。"),
        ("nle-official", "The NetHack Learning Environment (NLE)", "官方仓库确认NLE全称。")], "限定论文模型与任务；负结果不证明Harness无法跨越任何模型能力边界。", "research_result")

    # Additions selected by content review, independent of the URL inventory.
    additions = [
        ("CLAUDE_CONFIG", "13", "9/3 ant CLI增加ant apply及claude-lock.json资源定位；9/10 Managed Agents增加auto权限逐调用evaluation记录。", [
            ("anthropic-release-notes", "ant apply", "9/3条目说明仓库资源文件、先批准计划及锁文件定位同一资源。"),
            ("anthropic-release-notes", "permission policies now include auto", "9/10条目说明执行/拒绝/暂停批准三种决定及evaluation、evaluated_permission字段。")]),
        ("MANAGED_SPLIT", "13,18", "Anthropic在4/8工程文中把持久session、Harness与sandbox分离，分别处理执行环境和Harness失败。", [
            ("anthropic-managed-architecture", "each could fail or be replaced independently", "循环、会话日志与执行环境解耦；托管内部仅有厂商披露，非本书源码审计。")]),
        ("CURSOR_DATA", "15,18", "Cursor自管worker通过出站HTTPS接入云端，工具输出可能含代码回传，转录可能在云端处理和存储。", [
            ("cursor-self-hosted", "工具输出会回传至 Cursor 用于推理", "自管机器仅迁执行环境；输出、代码与会话数据仍可能进入Cursor云端。"),
            ("cursor-self-hosted", "长连接出站 HTTPS 通道", "worker主动建立出站通道，云端通过该通道交付工具工作。")]),
        ("CURSOR_PROJECTS", "15", "Projects beta包含协调委派、跨机器共享文件及subscriptions周期/事件工作；持续运行可靠性未实测。", [
            ("cursor-changelog", "协调智能体本身并不编写代码", "9/10说明协调者规划、委派实现Agent并交回成果。"),
            ("cursor-changelog", "每个 项目 都会维护一组文件", "共享上下文跨云端和本地机器同步。"),
            ("cursor-changelog", "按计划运行", "subscriptions支持周期任务和事件触发。")]),
        ("CURSOR_HOOK_BOUNDARIES", "15", "Cursor文档限定云端只运行命令hook，早期只读探索轮次不运行hook；命令hook退出2阻断，其他非零退出默认放行，而权限hook退出0但返回非法JSON或不合schema时阻断。", [
            ("current-cursor-hooks", "云端代理仅支持运行基于命令的钩子。", "云端的执行类型限制；不能把IDE提示词hook支持外推到云端。"),
            ("current-cursor-hooks", "这些轮次不会运行钩子。", "同段指早期只读探索轮次，获得可写环境后才开始运行hook。"),
            ("current-cursor-hooks", "退出码 2 - 阻止该操作", "命令hook退出2具有阻断语义。"),
            ("current-cursor-hooks", "其他退出码 - 钩子执行失败，操作仍会继续", "除0和2以外的退出码默认失败放行，不能把hook失效等同拒绝。"),
            ("current-cursor-hooks", "无效的 JSON 或不符合该钩子架构的响应会阻止该操作。", "同一退出码0条目限定权限hook：成功退出但JSON非法或不合schema仍阻断。")]),
        ("DSH_INSTALL", "16", "dsh Plugin Manager安装失败恢复package.json和lockfile，启用/删除等后续阶段可能留下部分修改；Host代码在工作区sandbox之外运行。", [
            (blob("deepseek-ai/deepseek-harness", REPO_NEW, "packages/boot/plugin-manager/README.md"), "a failed removal retains its partial changes", "失败删除不回滚已完成修改；同段说明失败/取消安装只恢复快照的manifest和lockfile。"),
            (blob("deepseek-ai/deepseek-harness", REPO_NEW, "packages/boot/plugin-manager/README.md"), "Host code executes in-process outside the workspace sandbox", "Host插件执行权与依赖build-script批准、普通工具批准分别处理。")]),
        ("OPENHANDS_PERSIST", "17", "SDK的persist-before-publish变更先持久化事件再发布；非Event socket envelope另行区分。", [
            ("https://github.com/OpenHands/software-agent-sdk/commit/94fca578b720df758b9bbf8a2639511b303c78e6", "persist events before publishing them", "固定merge commit的已合并PR元数据记录该变更，非故障注入实测。"),
            ("https://github.com/OpenHands/software-agent-sdk/commit/2ab274897ac5e2c66b0ba17e9a6d39367b769876", "non-Event envelope", "session socket传输包含非持久Event类的控制envelope。")]),
        ("OPENHANDS_CONTAINER", "17", "9月新SDK/Agent Server增加每会话Docker容器模式，不代表OpenHands首次具有Docker执行支持。", [
            ("https://github.com/OpenHands/software-agent-sdk/commit/3ff6924d8564b3d47a22a6c7e71377a701ae014f", "docker runtime mode for per-conversation containers", "merge commit对应PR标题明确每conversation容器模式，旧Runtime另有固定源码。")]),
        ("MCP_STATELESS", "08", "MCP 2026-07-28架构将协议定义为stateless，每次请求自包含并携带协议版本和能力；旧版session描述不能当作最新版。", [
            ("mcp-current-architecture", "every request is self-contained and carries its own protocol version and capabilities", "新版核心协议责任按请求表达；不外推成所有应用、订阅和工具业务都无状态。")]),
    ]
    for name, chapter, text, specs in additions:
        put("R20260919_"+name, chapter, text, specs)
    residency = x.proof("openai-agents-overview", "supports data residency only in the United States",
                        "与同段的无ZDR及自管环境限制一起阅读；限定2026-09-19存档，不是永久合规保证。")
    x.claims["R20260919_D02"]["evidence_ids"].append(residency[1])
    x.claims["R20260919_D02"]["text"] = "Agents API当前只支持美国数据驻留且不支持ZDR；自托管sandbox不改变该限制。"

    evolution = [
        ("HARNESSDEV_HOLDOUT", "19,22,24", "HarnessDev演化轨迹内分数用于开发反馈与版本选择；冻结后的630题SWE-Pro留出分数不展示给创建者。", "harnessdev-full", "these scores are never shown to the creator"),
        ("HARNESSBANK_GATES", "22", "HarnessBank v2先对采样训练子集做门禁，通过后才完整训练集评价并竞争进入基因库。", "harnessbank-v2-full", "Only candidates that pass all gates undergo full training-set evaluation"),
        ("SOLPI_MECHANISMS", "22", "SoL-Pi保留动作合并、压缩时机、大观察句柄化与保留证据的读取压缩四类机制；效率得分与成本须一起评价。", "sol-pi-full", "Action Fusion, Online Context Compact, ObservationPack, and Evidence-Preserving Reducer"),
        ("JIT_FROZEN", "23", "JIT-Agent训练Harness生成器，不能由任务执行模型冻结推断整个系统没有参数训练。", "jit-full", "JIT-Agent is trained based on Qwen3.6-27B."),
    ]
    for name, chapter, text, cap, anchor in evolution:
        put("R20260919_"+name, chapter, text, [(cap, anchor, text)],
            "论文指定版本的方法描述或作者结果，不是本书复现实验；开发/选型与封存终测不能混称。", "research_result")

    # Imported research claims are deliberately narrowed when the old phrasing
    # bundled several independent release notes under one short excerpt.
    x.claims["R20260919_D03"]["text"] = "9月14日Claude Messages API新增按需压缩beta；这不等于Code CLI或Managed Agents同名接口。"
    x.claims["R20260919_D06"]["text"] = "9月10日Cursor Projects以beta阶段逐步开放。"
    x.claims["R20260919_D27"]["text"] = "arXiv:2607.13683v2题名为HarnessBank；v1旧题名GSME与v2来源分开登记。"

    # Local probe evidence is a local measurement, not an upstream vendor claim.
    measurements = []
    for name, filename, anchor, summary in [
        ("schema", "codex/local/protocol_test_results.json", '"passed": 58', "已有结果total=58、passed=58，仅方法/字段/源码离线契约检查。"),
        ("initialize", "codex/initialize_only/probe_results.json", '"initialize_success": false', "已有initialize-only结果为exit1、未收到initialize响应、未发送initialized。")]:
        p = REVIEW / "vendor_probe" / filename
        u = "urn:agent-harness-book:local-probe:20260919:" + name
        cap = x.add_capture(u, p.read_text(), p, {}, title="Codex local " + name + " probe",
                            edition="local Codex 0.142.5 probe 2026-09-19", relation="local_measurement", kind="platform_metadata")
        sid = x.source(u, cap)
        x.sources[sid]["source_type"] = "platform_metadata"
        measurements.append((sid, x.add_evidence(sid, cap, anchor, summary, role="local_measurement")))
    x.claim("R20260919_CODEX_PROBE", "14", "本地Codex0.142.5离线契约检查58/58符合预期，initialize握手未验证；未端到端验证取消或模型流。",
            measurements, "读取既有probe结果，未重跑；受限启动失败不能推出产品不可用。", kind="factual")


def outputs(x, quotas):
    def encode(rows):
        return "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows)

    statuses = Counter(s["metadata_status"] for s in x.sources.values())
    cstatuses = Counter(c["support_status"] for c in x.claims.values())
    etypes = Counter(e["evidence_type"] for e in x.evidence.values())
    original_ids = {e["evidence_id"] for e in x.old_evidence}
    legacy_count = sum(x.evidence[eid]["evidence_type"] == "legacy_paraphrase" for eid in original_ids)
    unresolved, no_current_raw = [], []
    citations_by_source = defaultdict(list)
    for u in sorted(x.citations):
        sid = x.source(u)
        s = x.sources[sid]
        citations_by_source[sid].append(u)
        row = (u, sid, ", ".join(sorted(x.citations[u])))
        if s["metadata_status"] != "verified":
            unresolved.append(row)
        if not s.get("capture_path"):
            no_current_raw.append(row)
    # Inventory creation above is complete before counts are frozen.
    statuses = Counter(s["metadata_status"] for s in x.sources.values())
    total = len(x.sources)
    changed_legacy_sources = [s for sid, s in x.sources.items() if sid in x.old_sources and s.get("capture_path")]
    scope_note = "已核验仅指来源身份、指定版次及本地捕获定位；不等于逐句事实认证、实验复现或产品端到端通过。"
    readme = f"""# Evidence registry 状态

本目录维护来源、历史证据及经过选择的承重主张。`claims_v2.jsonl` 是核心主张子集，不能代表全书逐句覆盖；`claims_backlog.jsonl`保存deferred研究线索及needs_review，不进入书稿strict core门；`claims.jsonl` 是未改写的旧段落级存量，不参与本轮主张判定。

<!-- registry-status: total={total} verified={statuses['verified']} unverified={statuses['unverified']} -->

截至2026-09-19，本次 registry 共{total}条来源：{statuses['verified']}条 metadata verified、{statuses['unverified']}条 unverified；证据{len(x.evidence)}条；核心主张{len(x.claims)}条，状态为{dict(cstatuses)}；backlog {len(x.backlog)}条。{scope_note}

本轮合并已存增量研究、固定仓库/API证据、各篇新增引用及执行摘要；补查快照按脚本实际读取时的文件集合登记。所有来源仍使用五种 source_type：`academic_paper`、`official_documentation`、`official_article`、`official_repository`、`platform_metadata`。社区资料映射为 platform_metadata，标记 community_discovery_only 与 core_claim_eligible=false，不进入承重claims。

原71条证据保留ID与内容：{legacy_count}条标为 `legacy_paraphrase`，其 `quote` 字段是历史转述，不作为直接引文；其余必须有本次逐字匹配定位。新证据区分 `direct_quote` 与 `source_summary`，同时记录 capture文件SHA-256、解码文本SHA-256、JSON pointer、字符/行定位及中文摘要。直接引文按来源作品/版次合计不超过25个英文词；别名不会获得额外额度。对summary的语义支撑是人工限定判断，脚本只验证定位和完整性。

GSME旧source ID钉住arXiv:2607.13683v1并保留错误v2元数据的历史记录；HarnessBank v2另有来源/证据，C019改用v2。C009补协议传输与方法枚举，C014拆dsh两执行路径，C015拆OpenHands旧Runtime与当前SDK；增加托管/自管、九月产品变化、进化论文及MCP2026-07-28的窄主张。版本化arXiv URL必须与version_or_commit匹配，abs/html同版通过url_aliases关联。

当前正文引用中，元数据未核验URL有{len(unresolved)}个；未绑定当前可复核捕获的URL有{len(no_current_raw)}个，两者含义不同。逐项清单、全部核心主张及状态见 `research/audits/revision_20260919/disposition_evidence.md`。旧的supported不自动继承；缺少原文绑定的主张保留needs_review。

离线整合：`python3 publishing/scripts/integrate_revision_evidence.py --write`；只读一致性检查：同脚本 `--check`。脚本只写本目录五文件与上述处置报告，不写历史claims.jsonl、run_manifest、正文或出版产物。audit_claim_ledger.py仍要求核心承重主张supported，不能通过改状态掩盖缺项；是否支持url_aliases以主代理维护的当前审计器为准。审计仅调用validate()，不调用会写其他报告的main()。
"""
    report = [
        "# 2026-09-19 全局证据整合处置", "",
        "## 结果与范围", "",
        f"登记来源{total}、证据{len(x.evidence)}、核心主张{len(x.claims)}；主张状态：{dict(cstatuses)}。",
        scope_note,
        "本次仅修改research/evidence的sources.jsonl、evidence.jsonl、claims_v2.jsonl、README.md，并按追加授权新增claims_backlog.jsonl；新增整合脚本及本报告。未联网、未创建浏览器、未修改正文/site/artifacts、未提交发布。所有手写编辑用apply_patch，JSONL/README/报告由获授权的机械脚本生成。",
        "使用deep-research的来源身份、证据持久化及主张边界方法；按用户指定文件范围和离线要求，未执行技能中的联网检索或HTML/PDF流程。", "",
        "## 输入与历史修复", "",
        f"读取当前manuscript目录下全部Markdown引用（含executive_brief.md），共{len(x.citations)}个不同引用URL；产品处置表49个URL全部入册。合并review_20260919的37来源/证据及非社区窄主张；读入revision_20260919/retrieval当前全部有效原文快照及vendor_probe固定源码/API capture。",
        f"原84条source ID保留；其中{len(changed_legacy_sources)}条已绑定当前原文或固定源码。原71条evidence ID与文字保留，{legacy_count}条改为legacy_paraphrase，其余逐字验证；原始类型、定位与日期留历史字段。",
        "GSME旧题名钉住v1，v2另建HarnessBank来源，不把旧摘录绑到新题名；同版abs/html别名不拆成独立来源。C009以基线传输文档及当前方法枚举补证；C014区分动态Host node:vm、旧worker及新PTC进程；C015区分历史Runtime和现代SDK；C019采用HarnessBank v2；C021纠正NLE并收窄负结果归因。",
        "MCP2026-07-28单独登记stateless/self-contained request及逐请求version/capabilities；2025-06-18和2025-11-25仍作为有版本前提的历史规范，不改成当前最新。Building effective agents仅作为2024历史材料，页面的过时说明不被删去。",
        "Cursor hooks沿用source ID b1f6985403c6eaa1，raw URL改为cursor.com/cn/docs/hooks；旧docs.cursor.com/hooks保留为身份别名及被拒绝的目录捕获记录。第15章新增窄claim区分云端command-only/早期只读缺口、退出2阻断、其他非零默认放行和权限hook退出0但非法JSON/schema阻断；仅为文档契约，未逐运行面实测。",
        "community来源保留为发现线索，不进入核心主张；harness-survey编号/日期异常仍未解决，D36单独进入claims_backlog.jsonl，disposition=deferred、support_status=needs_review，不篡改成supported也不进入strict core。", "",
        "## 验证口径", "",
        f"本次直接引文按作品/版次累计的最大英文词数为{max(quotas.values(), default=0)}，上限25。每条direct_quote都逐字存在于指定capture字段，SHA-256匹配；source_summary使用中文归纳并保存原文上下文定位，不能把摘要标签自动当作语义证明。",
        "验证ID唯一、引用关系、五类source_type、版本URL一致、社区排除、引文总额、原71记录保留，以及来源/证据/主张的定位。检查并不验证论文结果、云端实现、安全强度或全书每句话。",
        "本地Codex probe仍只说明已有58/58离线检查，正常initialize握手未验证；没有重跑probe，也没有覆盖历史失败证据。",
        "本报告列出真实待审项，不为取得PASS改变结论；主代理维护的当前审计器实际只读调用结果由末尾报告。", "",
        "## 元数据尚未核验的正文URL", "",
        "| URL | source ID | 当前引用位置 |", "|---|---|---|",
    ]
    report += [f"| [来源]({u}) | `{sid}` | {locations} |" for u, sid, locations in unresolved] or ["| 无 | — | — |"]
    report += ["", "## 没有当前原文capture绑定的正文URL", "",
               "此表包括保留历史metadata verified但本轮不能逐字重核的来源；不因此宣称其内容为假。", "",
               "| URL | source ID | 当前引用位置 |", "|---|---|---|"]
    report += [f"| [来源]({u}) | `{sid}` | {locations} |" for u, sid, locations in no_current_raw] or ["| 无 | — | — |"]
    report += ["", "## 拒绝用作原文的捕获", "",
               "挑战页和泛目录保留在原采集目录作为访问记录，不用于metadata升级或内容支撑。历史metadata verified可保留，但不代表本次获得原文。", "",
               "| URL | 捕获文件 | 原因 |", "|---|---|---|"]
    report += [f"| [来源]({c['url']}) | {c['capture']} | {c['reason']} |" for c in x.rejected_captures] or ["| 无 | — | — |"]
    report += ["", "## 全部核心主张与覆盖状态", "",
               "supported仅指下列精确限定文本的来源支撑。未支持的旧记录列在同表，避免隐藏覆盖缺口；作者建议、教学数据和预测不因附有URL自动变成事实claim。", "",
               "| Claim | 章 | 状态 | 精确主张 | evidence ID |", "|---|---|---|---|---|"]
    for cid, c in x.claims.items():
        report.append(f"| {cid} | {c.get('chapter', '')} | {c['support_status']} | {c['text'].replace('|', '/')} | {', '.join(c['evidence_ids'])} |")
    report += ["", "## 核心旧主张待补证的具体缺项", "",
               "capture缺失不表示来源错误；有原文但尚未人工限定支撑范围，也不自动放行。", "",
               "| Claim | 来源 | 缺项 |", "|---|---|---|"]
    missing_rows = []
    for c in x.claims.values():
        if c["support_status"] != "supported":
            for entry in c.get("support_selection", []):
                missing_rows.append(f"| {c['claim_id']} | [来源]({entry['url']}) | {entry['reason']} |")
    report += missing_rows or ["| 无旧核心缺项 | — | — |"]
    if x.pending_support:
        report += ["", "已配置选择器但未满足的片段/版次：", ""]
        for pending in x.pending_support:
            report.append(f"- {pending['claim_id']}: " + json.dumps(pending["missing"], ensure_ascii=False))
    report += ["", "## Deferred研究线索（非核心）", "", "| ID | 状态 | 原因 |", "|---|---|---|"]
    report += [f"| {c['claim_id']} | {c['disposition']} / {c['support_status']} | {c.get('deferral_reason', '')} |" for c in x.backlog.values()]
    report += ["", "## 产品49项URL登记映射", "", "| URL | source ID | 元数据 |", "|---|---|---|"]
    for u in sorted(x.product_urls):
        sid = x.source(u)
        report.append(f"| [原文/固定源码]({u}) | `{sid}` | {x.sources[sid]['metadata_status']} |")
    report += ["", "## 审计兼容与可复核入口", "",
               "整合脚本--check检查本次输出与当前输入一致；现有audit_claim_ledger.validate()只读返回错误与警告，不写旧审计报告。真实needs_review仍应导致核心门禁失败，url_aliases按当前审计器核对。应按证据补足或明确范围，不把待审状态批量改为supported。",
               "本次没有自动产生‘全事实通过’结论。元数据升级列表和证据类型可由JSONL字段复核；以下输入摘要固定本次运行实际读取的文件集合。", "",
               f"输入文件数：{len(x.input_hashes)}；路径与hash排序后摘要：`{digest(json.dumps(x.input_hashes, sort_keys=True))}`。",
               f"capture异常：{x.issues or '无'}。", ""]
    return {
        LEDGER / "sources.jsonl": encode(x.sources.values()),
        LEDGER / "evidence.jsonl": encode(x.evidence.values()),
        LEDGER / "claims_v2.jsonl": encode(x.claims.values()),
        LEDGER / "claims_backlog.jsonl": encode(x.backlog.values()),
        LEDGER / "README.md": readme,
        REVISION / "disposition_evidence.md": "\n".join(report),
    }


def legacy_audit():
    """Call the existing validator without its report-writing main()."""
    executable = ROOT / ".venv/bin/python"
    if not executable.exists():
        return {"execution": "unavailable", "reason": "repository .venv Python missing"}
    code = (
        "import json,runpy; "
        "m=runpy.run_path('publishing/scripts/audit_claim_ledger.py'); "
        "errors,warnings,claims,stats=m['validate'](); "
        "print(json.dumps({'execution':'completed_read_only','errors':errors,'warnings':warnings,"
        "'unregistered_links':stats['unregistered_links'],'statuses':dict(stats['statuses'])},ensure_ascii=False))"
    )
    result = subprocess.run([str(executable), "-c", code], cwd=ROOT, capture_output=True,
                            text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if result.returncode:
        return {"execution": "failed", "reason": result.stderr.strip()}
    return json.loads(result.stdout)


def audit_appendix(audit):
    lines = ["", "## 现有审计器实际只读运行结果", "",
             "调用audit_claim_ledger.validate()，未调用write_report()/main()。", "",
             f"执行状态：{audit['execution']}。"]
    if audit["execution"] == "completed_read_only":
        lines.append(f"当前门禁结果：{'FAIL' if audit['errors'] else 'PASS'}；错误{len(audit['errors'])}条，警告{len(audit['warnings'])}条。")
        lines += ["", "具体错误（保留真实待审状态）：", ""]
        lines += ["- " + e for e in audit["errors"]] or ["- 无。"]
        lines += ["", "警告：", ""]
        lines += ["- " + w for w in audit["warnings"]] or ["- 无。"]
        lines += ["", "当前审计器报告的未登记正文链接：", ""]
        lines += [f"- [来源]({u})" for u in audit["unregistered_links"]] or ["- 无。"]
    else:
        lines += ["", audit.get("reason", "unknown")]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write and args.check:
        parser.error("choose --write or --check")
    x = Integration()
    x.load_captures()
    x.legacy()
    x.import_review()
    x.curate()
    x.old_claim_status()
    x.register_all_links()
    quotas = x.validate()
    generated = outputs(x, quotas)
    report = REVISION / "disposition_evidence.md"
    different = [rel(p) for p, text in generated.items() if p != report and (not p.exists() or p.read_text() != text)]
    if args.write:
        for p, text in generated.items():
            if p != report and (not p.exists() or p.read_text() != text):
                p.write_text(text)
    audit = None
    if args.write or args.check:
        audit = legacy_audit()
        generated[report] += audit_appendix(audit)
    if not report.exists() or report.read_text() != generated[report]:
        different.append(rel(report))
        if args.write:
            report.write_text(generated[report])
    print(json.dumps({"sources":len(x.sources), "evidence":len(x.evidence), "claims":len(x.claims),
                      "claim_statuses":dict(Counter(c["support_status"] for c in x.claims.values())),
                      "maximum_direct_quote_english_words":max(quotas.values(), default=0),
                      "changed_outputs":different, "capture_issues":x.issues,
                      "legacy_audit_errors":len(audit.get("errors", [])) if audit else None,
                      "mode":"write" if args.write else "check" if args.check else "dry_run"}, ensure_ascii=False))
    return 1 if args.check and different else 0


if __name__ == "__main__":
    raise SystemExit(main())

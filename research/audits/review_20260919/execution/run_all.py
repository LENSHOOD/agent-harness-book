#!/usr/bin/env python3
"""One-command offline audit; exit 1 = findings reproduced, exit 2 = audit error."""
import collections
import datetime
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
import traceback
import zoneinfo

from auditlib import Audit, dump
from inventory import inventory, sha
import structured
import sql_case
import safety_models
import repo_case
import evolution_case
import additional_counterexamples
import remaining_pseudocode

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE_REPOSITORY = ROOT
HISTORICAL_REVISION = "a1ed264462d9b61c260c1dc417243303bfc60b66"


def pin_historical_source(run):
    """Keep historical block IDs/positions tied to the audited revision, not new prose."""
    frozen = run / "source-a1ed264"
    commands = []
    for argv in (["git", "clone", "--local", "--no-hardlinks", "--no-checkout",
                  str(SOURCE_REPOSITORY), str(frozen)],
                 ["git", "-C", str(frozen), "checkout", "--detach", HISTORICAL_REVISION]):
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
        commands.append({"argv": argv, "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        dump(run / "historical_source_pin.json", {"revision": HISTORICAL_REVISION, "commands": commands})
        result.check_returncode()
    return frozen


class Tee:
    def __init__(self, original, logfile):
        self.original, self.logfile = original, logfile

    def write(self, text):
        self.original.write(text)
        self.logfile.write(text)
        self.logfile.flush()

    def flush(self):
        self.original.flush()
        self.logfile.flush()


def offline_hook(event, args):
    if event in {"socket.connect", "socket.getaddrinfo"}:
        raise RuntimeError("Network forbidden in this offline audit")


def environment(a):
    git = a.command("git_version", ["git", "--version"], ROOT)
    bash = a.command("bash_version", ["/bin/bash", "--version"], ROOT)
    head = a.command("source_head", ["git", "rev-parse", "HEAD"], ROOT)
    status = a.command("source_status", ["git", "status", "--short"], ROOT)
    clean_env = {"PYTHONPATH": ""}
    venv = a.command("original_venv_packages", [str(SOURCE_REPOSITORY / ".venv/bin/python"), "-B", "-c",
            "import sys,json,importlib.metadata; print(sys.version); print(json.dumps(sorted((d.metadata['Name'],d.version) for d in importlib.metadata.distributions())))"], ROOT, env=clean_env)
    pip = a.command("original_venv_pip", [str(SOURCE_REPOSITORY / ".venv/bin/python"), "-B", "-m", "pip", "--version"], ROOT, env=clean_env)
    scripts = {str(p.relative_to(HERE)): sha(p.read_bytes()) for p in sorted(HERE.rglob("*"))
               if p.is_file() and p.suffix in {".py", ".sh"} and not any(x in p.relative_to(HERE).parts for x in ["deps", "runs"])}
    zone_files = {}
    for key in ["America/New_York", "Europe/Berlin", "Australia/Lord_Howe", "UTC"]:
        for directory in zoneinfo.TZPATH:
            path = Path(directory) / key
            if path.is_file():
                zone_files[key] = {"path": str(path), "sha256": sha(path.read_bytes())}
                break
    return {"timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
            "sqlite": sqlite3.sqlite_version, "git": git["stdout"].strip(), "bash": bash["stdout"].splitlines()[0],
            "source_HEAD": head["stdout"].strip(), "source_status": status["stdout"],
            "dependencies": {name: importlib.metadata.version(name) for name in
                             ["jsonschema", "PyYAML", "pytest", "referencing", "rpds-py", "attrs"]},
            "dependency_manifest_sha256": sha((HERE / "dependency_manifest.json").read_bytes()),
            "requirements_sha256": sha((ROOT / "requirements.txt").read_bytes()),
            "original_venv": venv, "original_venv_pip_exit": pip["exit_code"],
            "scripts_sha256": scripts, "timezone_files": zone_files,
            "network": "Python sockets blocked; subprocesses only local git, bash, pytest",
            "deterministic_provider": True, "model_API_calls": 0, "external_writes": 0,
            "new_git_commits": 0, "git_fixture_baseline": "write-tree only"}


def coverage(a):
    rows = []
    for b in a.inv["blocks"]:
        checks = [c for c in a.checks if b["id"] in c["sources"]]
        simulations = [c for c in checks if c["model"] not in {"schema_only", "raw_parse"}]
        if b["classification"] == "json_schema":
            category = "仅schema验证"
            limitation = "元schema及合成正反实例；未验证权限、来源、artifact或业务语义"
        elif b["language"] in {"json", "yaml"}:
            category = "未验证"
            limitation = "原样格式解析已执行；运行语义/供应商接口未验证"
        elif b["language"] in {"bash", "sql"}:
            category = "可运行代码"
            limitation = ("SQLite DIALECT_MISMATCH，不判原SQL错误；BigQuery仅主代理官方文档核验，未原引擎执行；适配单列"
                          if b["language"] == "sql" else "已原样尝试但失败；适配/fixture结果另列，不能声称原样可运行")
        elif b["classification"] == "pseudocode" and not simulations:
            category = "未验证"
            limitation = "仅设计伪代码，未翻译执行；无实现/依赖语义"
        else:
            category = "设计示意"
            limitation = "已进行限定语义模拟，非原样可执行/非生产实现" if simulations else "图/公式/接口草图不具备独立运行语义，未做经验性验证"
        rows.append({k: b[k] for k in ["id", "file", "line", "content_line", "end_line", "language", "sha256", "classification"]} |
                    {"coverage_category": category, "parse": "PASS" if any(c["model"] == "raw_parse" and c["status"] == "PASS" for c in checks) else "NOT_APPLICABLE",
                     "checks": [c["name"] for c in checks], "check_statuses": dict(collections.Counter(c["status"] for c in checks)),
                     "simulation_models": sorted({c["model"] for c in simulations}), "limitation": limitation})
    dump(a.run / "coverage.json", rows)
    lines = ["# 全书逐块覆盖矩阵", "", "SHA-256 按 fenced 内容原始 UTF-8 字节（含末尾换行），不含 fence；行号是开 fence。编号按路径排序。",
             "", "可运行代码是输入类别，不代表执行成功。未验证项可能已完成 JSON/YAML 原样解析；这不代表运行语义已验证。", "",
             "|ID|file:line|language|SHA-256|classification|覆盖|解析|实测检查 PASS/FAIL|限制|", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        loc = r["file"] + ":" + str(r["line"])
        lines.append(f'|{r["id"]}|{loc}|{r["language"]}|{r["sha256"]}|{r["classification"]}|{r["coverage_category"]}|{r["parse"]}|{r["check_statuses"]}|{r["limitation"]}|')
    lines.extend(["", "## 每块检查名", ""])
    for r in rows:
        if r["checks"]:
            lines.append(f'- {r["id"]}: ' + ", ".join(r["checks"]))
    (a.run / "coverage.md").write_text("\n".join(lines) + "\n")
    return rows


def main():
    global ROOT
    sys.addaudithook(offline_hook)
    (HERE / "runs").mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ_")
    run = Path(tempfile.mkdtemp(prefix=stamp, dir=HERE / "runs"))
    stdout = (run / "stdout.log").open("w")
    stderr = (run / "stderr.log").open("w")
    sys.stdout = Tee(sys.stdout, stdout)
    sys.stderr = Tee(sys.stderr, stderr)
    print("AUDIT_RUN", run)
    ROOT = pin_historical_source(run)
    inv = inventory(ROOT)
    dump(run / "inventory.json", inv)
    (run / "blocks").mkdir()
    for b in inv["blocks"]:
        (run / "blocks" / (b["id"] + ".txt")).write_bytes(b["raw"].encode("utf-8"))
    audit = Audit(ROOT, run, inv)
    audit.check("inventory_closed_fences_and_independent_marker_counts", not inv["issues"], model="audit_integrity", details=inv["issues"])
    audit.group("environment", environment)
    audit.group("structured", structured.parse_all)
    audit.group("schemas", structured.schemas)
    audit.group("original_bash", repo_case.raw_bash)
    audit.group("sql", sql_case.run)
    audit.group("safety", safety_models.run)
    audit.group("remaining_pseudocode", remaining_pseudocode.run)
    audit.group("additional_counterexamples", additional_counterexamples.run)
    audit.group("repository_case", repo_case.synthetic_repo)
    audit.group("evolution", evolution_case.run)
    final_inventory = inventory(ROOT)
    audit.check("manuscript_unchanged_during_run", inv == final_inventory, model="audit_integrity")
    if audit.data.get("environment", {}).get("requirements_sha256"):
        audit.check("requirements_unchanged_during_run", sha((ROOT / "requirements.txt").read_bytes()) == audit.data["environment"]["requirements_sha256"], model="audit_integrity")
    rows = coverage(audit)
    unexpected = [c["name"] for c in audit.checks if not c["expected_reproduction"]]
    failures = [c for c in audit.checks if c["status"] == "FAIL"]
    summary = {"run_dir": str(run), "blocks": len(inv["blocks"]),
               "markdown_files": sum(f["kind"] == "markdown" for f in inv["files"]),
               "zero_block_markdown_files": [f["file"] for f in inv["files"] if f["kind"] == "markdown" and f["blocks"] == 0],
               "language_counts": inv["language_counts"],
               "coverage_categories": dict(collections.Counter(r["coverage_category"] for r in rows)),
               "check_counts": dict(collections.Counter(c["status"] for c in audit.checks)),
               "failure_severities": dict(collections.Counter(c["severity"] for c in failures)),
               "unexpected_results": unexpected, "audit_errors": audit.errors,
               "exit_code_semantics": {"0": "no failing probes", "1": "findings/negative fixtures reproduced; read report", "2": "audit implementation error or unexpected result"}}
    exit_code = 2 if unexpected or audit.errors else 1 if failures else 0
    summary["exit_code"] = exit_code
    dump(run / "results.json", {"summary": summary, "checks": audit.checks, "groups": audit.data})
    dump(run / "failures.json", failures)
    dump(run / "summary.json", summary)
    # Latest pointer is only metadata; never delete/overwrite any historical run.
    dump(HERE / "latest_run.json", summary)
    lines = ["# 实跑摘要", "", "```json", json.dumps(summary, ensure_ascii=False, indent=2), "```", "", "## 所有失败探针", ""]
    for c in failures:
        lines.append(f'- {c["severity"]} `{c["name"]}` — {c["model"]}; sources={c["sources"]}; 完整反例见 failures.json')
    (run / "summary.md").write_text("\n".join(lines) + "\n")
    artifact_hashes = {str(p.relative_to(run)): sha(p.read_bytes()) for p in sorted(run.rglob("*"))
                       if p.is_file() and ".git" not in p.parts and p.name not in {"stdout.log", "stderr.log", "artifact_hashes.json"}}
    dump(run / "artifact_hashes.json", artifact_hashes)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

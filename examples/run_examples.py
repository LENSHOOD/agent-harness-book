#!/usr/bin/env python3
"""Current reference regression gate: positive cases pass AND negatives are rejected.

Exit 0 means that contract; exit 1 means regression/dependency failure.
Never invokes or overwrites the separate historical audit.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from zoneinfo import TZPATH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_manifest():
    paths = list((HERE / "src").rglob("*.py")) + list((HERE / "tests").rglob("*.py"))
    paths += [HERE / "run_examples.py", ROOT / "requirements-examples.txt", ROOT / "publishing/scripts/check_examples.py"]
    paths += list((ROOT / "manuscript").rglob("*.md"))
    return {str(path.relative_to(ROOT)): sha(path) for path in sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="Parent for a new unique run; existing runs never overwritten")
    args = parser.parse_args()
    parent = (args.output_dir or HERE / "runs").resolve()
    parent.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_"), dir=parent))

    def write(name, value):
        (run / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    before = source_manifest()
    write("source_manifest.json", before)
    environment = {"python": sys.version, "platform": platform.platform(), "sqlite": sqlite3.sqlite_version,
                   "executable": sys.executable, "kind": "local reference models; not commercial Agent replication",
                   "model_API_calls": 0, "external_business_writes": 0, "git_commits": 0}
    failures, commands = [], []
    try:
        environment["dependencies"] = {name: version(name) for name in ("jsonschema", "PyYAML", "pytest")}
        expected = {"jsonschema": "4.26.0", "PyYAML": "6.0.3", "pytest": "9.1.1"}
        if environment["dependencies"] != expected:
            raise RuntimeError("Install the pinned requirements-examples.txt before running")
        git = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        environment["git"] = git.stdout.strip()
        environment["timezone_files"] = {}
        for key in ("UTC", "America/New_York", "Europe/Berlin", "Australia/Lord_Howe", "Asia/Shanghai"):
            for directory in TZPATH:
                path = Path(directory) / key
                if path.is_file():
                    environment["timezone_files"][key] = {"sha256": sha(path)}
                    break
        env = dict(os.environ, EXAMPLES_RUN_DIR=str(run), PYTHONDONTWRITEBYTECODE="1",
                   PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
        for label, argv in [
            ("pytest", [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "--junitxml=" + str(run / "tests.xml"), str(HERE / "tests")]),
            ("check_examples", [sys.executable, "-B", str(ROOT / "publishing/scripts/check_examples.py"),
                                "--skip-flow-tests", "--report", str(run / "manuscript_checks.json")]),
        ]:
            result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=180)
            (run / (label + ".stdout.log")).write_text(result.stdout, encoding="utf-8")
            (run / (label + ".stderr.log")).write_text(result.stderr, encoding="utf-8")
            commands.append({"label": label, "argv": argv, "exit_code": result.returncode})
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, file=sys.stderr, end="")
            if result.returncode:
                failures.append(label)
    except Exception as exc:
        failures.append(f"{type(exc).__name__}: {exc}")
    after = source_manifest()
    if before != after:
        failures.append("source_changed_during_run")
    write("environment.json", environment)
    write("commands.json", commands)
    counts = {}
    if (run / "tests.xml").is_file():
        root = ET.parse(run / "tests.xml").getroot()
        suites = root.findall("testsuite")
        counts = {name: sum(int(s.get(name, "0")) for s in suites) for name in ("tests", "failures", "errors", "skipped")}
    summary = {"kind": "executable local reference; NOT vendor replication, real model evaluation, or production safety proof",
               "exit_code": int(bool(failures)), "failures": failures, "pytest": counts,
               "exit_semantics": {"0": "positives pass and intended negatives rejected", "1": "real regression or environment/dependency error"},
               "run_directory": str(run.relative_to(ROOT)) if run.is_relative_to(ROOT) else str(run),
               "historical_audit": "untouched; old exit 1 still means historical failing probes",
               "source_unchanged_during_run": before == after}
    write("summary.json", summary)
    (run / "summary.md").write_text("# 当前可执行参考模型运行证据\n\n"
        "不是商业 Agent 复现、真实模型实验或生产安全认证。负例被拒绝属于当前回归门成功；历史 FAIL 不改写。\n\n"
        + "```json\n" + json.dumps(summary, ensure_ascii=False, indent=2) + "\n```\n", encoding="utf-8")
    manifest = {str(path.relative_to(run)): sha(path) for path in sorted(run.rglob("*"))
                if path.is_file() and path.name != "artifact_hashes.json"}
    write("artifact_hashes.json", manifest)
    print("REFERENCE_RUN", summary["run_directory"])
    print("REFERENCE_EXIT", summary["exit_code"])
    return summary["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())

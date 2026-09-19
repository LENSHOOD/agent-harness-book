"""Verify evidence consistency and compare completed runs; does not rerun experiments."""
import json
from pathlib import Path
import subprocess
from auditlib import dump
from inventory import inventory, sha

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def main():
    summary = json.loads((HERE / "latest_run.json").read_text())
    run = Path(summary["run_dir"])
    result = json.loads((run / "results.json").read_text())
    inv = json.loads((run / "inventory.json").read_text())
    matrix = json.loads((run / "coverage.json").read_text())
    mismatches = []
    current = inventory(ROOT)
    if current != inv:
        mismatches.append("source inventory changed")
    if len(matrix) != len(inv["blocks"]) or {b["id"] for b in matrix} != {b["id"] for b in inv["blocks"]}:
        mismatches.append("matrix missing/extra block")
    for b, row in zip(inv["blocks"], matrix):
        if row["sha256"] != sha((run / "blocks" / (b["id"] + ".txt")).read_bytes()):
            mismatches.append("block hash mismatch: " + b["id"])
    artifacts = json.loads((run / "artifact_hashes.json").read_text())
    skipped_rebuildable = []
    for name, expected in artifacts.items():
        path = run / name
        if not path.exists() and any(part.startswith(("dst_", "original_bash_workspace")) for part in path.relative_to(run).parts):
            skipped_rebuildable.append(name)
            continue
        if not path.is_file() or sha(path.read_bytes()) != expected:
            mismatches.append("artifact changed/missing: " + name)
    prior_runs = sorted(p for p in (HERE / "runs").glob("*/results.json") if p.parent != run)
    previous = json.loads(prior_runs[-1].read_text())
    compact = lambda r: [(c["name"], c["status"], c["model"], c["sources"]) for c in r["checks"]]
    same_checks = compact(previous) == compact(result)
    prior_checks = {row[0]: row for row in compact(previous)}
    current_checks = {row[0]: row for row in compact(result)}
    added_checks = sorted(set(current_checks) - set(prior_checks))
    removed_checks = sorted(set(prior_checks) - set(current_checks))
    changed_previous_checks = sorted(name for name in set(prior_checks) & set(current_checks)
                                    if prior_checks[name] != current_checks[name])
    severity_changes = [{"name": c["name"], "before": p["severity"], "after": c["severity"]}
                        for c in result["checks"] for p in previous["checks"]
                        if c["name"] == p["name"] and c["severity"] != p["severity"]]
    same_sql = previous["groups"]["sql"]["snapshots"] == result["groups"]["sql"]["snapshots"]
    same_evolution = previous["groups"]["evolution"]["metrics"] == result["groups"]["evolution"]["metrics"]
    same_patches = previous["groups"]["repository_case"]["candidates"] == result["groups"]["repository_case"]["candidates"]
    if removed_checks or changed_previous_checks or not all([same_sql, same_evolution, same_patches]):
        mismatches.append("previous checks/results changed; inspect removed/changed lists")
    ignore_targets = [HERE / "deps/jsonschema/__init__.py", HERE / "bin/pytest",
                      run / "dst_agent_repo/src/time/window.py", run / "original_bash_workspace/README.md",
                      run / "dst_verifier_overfit/src/time/window.py", run / "dst_input_drift/src/time/window.py"]
    ignore = subprocess.run(["git", "check-ignore", "--stdin"], input="\n".join(map(str, ignore_targets)) + "\n",
                            text=True, capture_output=True, cwd=ROOT)
    ignored_all = len(ignore.stdout.splitlines()) == len(ignore_targets)
    if not ignored_all:
        mismatches.append("generated dependency/workspace not ignored")
    retained_targets = [HERE / "dependency_manifest.json", HERE / "fixtures/pytest-wrapper.sh", run / "results.json",
                        run / "stdout.log", run / "failures.json", run / "coverage.md"]
    retained = subprocess.run(["git", "check-ignore", "--stdin"], input="\n".join(map(str, retained_targets)) + "\n",
                              text=True, capture_output=True, cwd=ROOT)
    if retained.stdout:
        mismatches.append("required evidence unexpectedly ignored")
    document = {"current_run": str(run), "compared_run": str(prior_runs[-1].parent),
                "same_checks": same_checks, "same_sql_snapshots": same_sql, "same_evolution_metrics": same_evolution,
                "previous_checks_compared": len(prior_checks), "added_checks": added_checks,
                "removed_checks": removed_checks, "changed_previous_checks": changed_previous_checks,
                "severity_reclassifications": severity_changes,
                "same_git_patch_results": same_patches, "matrix_rows": len(matrix), "artifact_hashes_checked": len(artifacts),
                "skipped_missing_rebuildable_files": skipped_rebuildable, "generated_dependencies_ignored": ignored_all,
                "necessary_evidence_not_ignored": not retained.stdout, "mismatches": mismatches,
                "interpretation": "Compare shared preexisting probes; added probes are not independently repeated by this comparison. Severity reclassifications explicit. No stochastic-model/environment claim."}
    dump(HERE / "verification.json", document)
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return bool(mismatches)


if __name__ == "__main__":
    raise SystemExit(main())

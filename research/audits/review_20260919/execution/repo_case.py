import ast
import os
from pathlib import Path
import shutil
import sys
from auditlib import dump
from inventory import get_block, sha

HERE = Path(__file__).resolve().parent


def raw_bash(a):
    block = get_block(a.inv, "25_", language="bash")
    dest = a.run / "original_bash_workspace"
    clone = a.command("raw_local_clone", ["git", "clone", "--local", "--no-hardlinks", str(a.root), str(dest)], a.run)
    if clone["exit_code"]:
        raise RuntimeError("Could not construct isolated original fixture")
    # Manifest states exactly what the original repository has, before any synthetic repo tests exist.
    manifest = {"source_has_tests_time": (a.root / "tests/time").exists(),
                "source_has_src_time": (a.root / "src/time").exists(),
                "fixture_has_tests_time": (dest / "tests/time").exists(),
                "fixture_has_src_time": (dest / "src/time").exists()}
    commit = a.command("raw_required_revision", ["git", "cat-file", "-e", "8f31b6e^{commit}"], dest)
    manifest["required_revision_exists"] = commit["exit_code"] == 0
    original = a.command("bash_raw_original_environment", ["/bin/bash", "-x"], dest,
                         input=block["raw"], env={"PATH": "/usr/bin:/bin"})
    a.check("bash_original_directly_runnable", original["exit_code"] == 0, sources=[block["id"]],
            expected_failure=True, severity="P2", details={**manifest, "command": original})
    wrapper = HERE / "bin/pytest"
    wrapper.parent.mkdir(exist_ok=True)
    shutil.copyfile(HERE / "fixtures/pytest-wrapper.sh", wrapper)
    wrapper.chmod(0o755)
    env = {"PATH": str(wrapper.parent) + ":/usr/bin:/bin", "AUDIT_PYTHON": sys.executable,
           "PYTHONPATH": str(HERE / "deps")}
    provided_runner = a.command("bash_raw_with_real_pytest_only", ["/bin/bash", "-x"], dest,
                                input=block["raw"], env=env)
    a.check("bash_with_pytest_source_tests_exist", provided_runner["exit_code"] == 0, sources=[block["id"]],
            model="original_with_audit_dependency", expected_failure=True, severity="P2", details=provided_runner)
    lines = []
    for i, line in enumerate(block["raw"].splitlines(), 1):
        if line:
            lines.append(a.command(f"bash_original_line_{i}", ["/bin/bash", "-c", line], dest, env=env))
    a.check("bash_pipeline_propagates_git_failure", lines[1]["exit_code"] != 0, sources=[block["id"]],
            model="original", expected_failure=True, severity="P1", details=lines[1])
    fixed = a.command("bash_pipeline_with_pipefail", ["/bin/bash", "-o", "pipefail", "-c", block["raw"].splitlines()[1]], dest, env=env)
    a.check("bash_pipefail_exposes_bad_revision", fixed["exit_code"] != 0, sources=[block["id"]],
            model="corrected_execution", details=fixed)
    manifest["empty_artifacts"] = {n: (dest / n).stat().st_size for n in ["candidate.patch", "changed-files.txt"]}
    return {"manifest": manifest, "original": original, "with_dependency": provided_runner,
            "line_exit_codes": [x["exit_code"] for x in lines],
            "interpretation": "No code/tests or replacement commit were supplied to the original workspace. pytest supplied separately only to expose missing tests. No original runnable claim."}


def synthetic_repo(a):
    repo = a.run / "dst_agent_repo"
    shutil.copytree(HERE / "fixtures/repo", repo)
    init = a.command("dst_git_init", ["git", "init", "--quiet"], repo)
    add = a.command("dst_git_add_baseline", ["git", "add", "src", "tests"], repo)
    tree = a.command("dst_baseline_tree", ["git", "write-tree"], repo)["stdout"].strip()
    if init["exit_code"] or add["exit_code"] or len(tree) != 40:
        raise RuntimeError("Synthetic baseline tree setup failed")

    def tests(label, folder, which):
        env = {"PYTHONPATH": str(folder / "src/time") + os.pathsep + str(HERE / "deps")}
        return a.command(label, [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *which], folder, env=env)

    base_visible = tests("dst_baseline_visible", repo, ["tests/time/test_dst.py"])
    base_ordinary = tests("dst_baseline_ordinary", repo, ["tests/time/test_ordinary.py"])
    a.check("DST_baseline_visible_contract", base_visible["exit_code"] == 0, sources=["B102", "B103"],
            model="audit_created_fixture", expected_failure=True, severity="INJECTED", details=base_visible)
    a.check("DST_baseline_ordinary", base_ordinary["exit_code"] == 0, sources=["B102"], model="audit_created_fixture", details=base_ordinary)
    results = []
    for name, filename in [("overfit", "cheating_window.py"), ("repaired", "corrected_window.py")]:
        # Model-provider stub chooses a predeclared patch; it has no code path that reads hidden checks.
        shutil.copyfile(HERE / "fixtures" / filename, repo / "src/time/window.py")
        visible = tests("dst_" + name + "_visible", repo, ["tests/time"])
        diff = a.command("dst_" + name + "_diff", ["git", "diff", "--binary", tree], repo)
        patch = a.run / (name + ".patch")
        patch.write_text(diff["stdout"])
        sealed_hash = sha(patch.read_bytes())
        changed = a.command("dst_" + name + "_scope", ["git", "diff", "--name-only", tree], repo)["stdout"].splitlines()
        clean = a.run / ("dst_verifier_" + name)
        shutil.copytree(HERE / "fixtures/repo", clean)
        a.command("dst_" + name + "_verifier_init", ["git", "init", "--quiet"], clean)
        a.command("dst_" + name + "_verifier_add", ["git", "add", "src", "tests"], clean)
        check = a.command("dst_" + name + "_apply_check", ["git", "apply", "--check", str(patch)], clean)
        apply = a.command("dst_" + name + "_apply", ["git", "apply", str(patch)], clean)
        if check["exit_code"] or apply["exit_code"]:
            raise RuntimeError("Sealed patch failed to apply in clean baseline")
        hidden = tests("dst_" + name + "_hidden", clean, [str(HERE / "fixtures/hidden/test_contract.py")])
        clean_visible = tests("dst_" + name + "_clean_visible", clean, ["tests/time"])
        syntax = ast.parse((clean / "src/time/window.py").read_text())
        scope = changed == ["src/time/window.py"]
        integrity = sealed_hash == sha(patch.read_bytes())
        a.check("DST_" + name + "_visible", visible["exit_code"] == 0, sources=["B102", "B103"], model="deterministic_stub", details=visible)
        a.check("DST_" + name + "_hidden", hidden["exit_code"] == 0, sources=["B102", "B103"], model="deterministic_stub",
                details=hidden, expected_failure=name == "overfit", severity="INJECTED")
        a.check("DST_" + name + "_sealed_clean_scope", clean_visible["exit_code"] == 0 and integrity and scope and bool(syntax),
                sources=["B103", "B105"], model="audit_created_verifier",
                details={"changed": changed, "hash": sealed_hash, "baseline_tree": tree, "ast_syntax": "PASS"})
        results.append({"candidate": name, "baseline_tree": tree, "patch": patch.name, "sha256": sealed_hash,
                        "visible_exit": visible["exit_code"], "hidden_exit": hidden["exit_code"],
                        "clean_visible_exit": clean_visible["exit_code"], "changed_paths": changed,
                        "verifier_response_to_stub": "SPEC_GAP: arbitrary DST years must preserve civil-day window semantics" if hidden["exit_code"] else "CANDIDATE_VERIFIED",
                        "production_commit": None})
    # Reproduce raw diff's untracked-file omission on a real Git index/tree.
    shutil.copyfile(HERE / "fixtures/dependent_window.py", repo / "src/time/window.py")
    shutil.copyfile(HERE / "fixtures/window_helpers.py", repo / "src/time/window_helpers.py")
    untracked_visible = tests("dst_untracked_workspace_visible", repo, ["tests/time"])
    omitted_diff = a.command("dst_untracked_raw_diff", ["git", "diff", "--binary", tree], repo)
    omitted_patch = a.run / "untracked_omitted.patch"
    omitted_patch.write_text(omitted_diff["stdout"])
    untracked = a.command("dst_untracked_inventory", ["git", "ls-files", "--others", "--exclude-standard"], repo)
    clean_omitted = a.run / "dst_verifier_untracked"
    shutil.copytree(HERE / "fixtures/repo", clean_omitted)
    a.command("dst_untracked_verifier_init", ["git", "init", "--quiet"], clean_omitted)
    a.command("dst_untracked_verifier_add", ["git", "add", "src", "tests"], clean_omitted)
    omitted_apply = a.command("dst_untracked_apply", ["git", "apply", str(omitted_patch)], clean_omitted)
    omitted_result = tests("dst_untracked_clean_visible", clean_omitted, ["tests/time"])
    a.check("git_raw_diff_captures_untracked_required_newfile", untracked_visible["exit_code"] == 0 and omitted_result["exit_code"] == 0,
            sources=["B104"], model="faithful_protocol_fixture", expected_failure=True, severity="P1",
            details={"workspace_tests_exit": untracked_visible["exit_code"], "sealed_clean_tests_exit": omitted_result["exit_code"],
                     "untracked": untracked["stdout"], "patch_sha256": sha(omitted_patch.read_bytes()),
                     "clean_stderr": omitted_result["stderr"], "clean_stdout": omitted_result["stdout"],
                     "adaptation": "Real baseline tree substitutes missing illustrative commit; diff command semantics unchanged."})
    if omitted_apply["exit_code"]:
        raise RuntimeError("Omitted-file fixture patch unexpectedly did not apply")
    # Separate TOCTOU fixture: seal overfit code, then mutate workspace, then run tests.
    drift = a.run / "dst_input_drift"
    shutil.copytree(HERE / "fixtures/repo", drift)
    a.command("dst_drift_init", ["git", "init", "--quiet"], drift)
    a.command("dst_drift_add", ["git", "add", "src", "tests"], drift)
    drift_tree = a.command("dst_drift_tree", ["git", "write-tree"], drift)["stdout"].strip()
    shutil.copyfile(HERE / "fixtures/cheating_window.py", drift / "src/time/window.py")
    sealed_input_hash = sha((drift / "src/time/window.py").read_bytes())
    drift_patch_result = a.command("dst_drift_seal", ["git", "diff", "--binary", drift_tree], drift)
    (a.run / "input_drift_sealed.patch").write_text(drift_patch_result["stdout"])
    shutil.copyfile(HERE / "fixtures/corrected_window.py", drift / "src/time/window.py")
    tested_input_hash = sha((drift / "src/time/window.py").read_bytes())
    drift_tests = tests("dst_drift_workspace_all_checks", drift, ["tests/time", str(HERE / "fixtures/hidden/test_contract.py")])
    # This exact sealed patch equals the already independently executed overfit patch.
    sealed_matches_overfit = (a.run / "input_drift_sealed.patch").read_bytes() == (a.run / "overfit.patch").read_bytes()
    a.check("git_sealed_patch_and_tested_input_are_same", sealed_input_hash == tested_input_hash,
            sources=["B104"], model="faithful_protocol_fixture", expected_failure=True, severity="P1",
            details={"sealed_source_sha256": sealed_input_hash, "tested_source_sha256": tested_input_hash,
                     "workspace_checks_exit": drift_tests["exit_code"], "sealed_patch_matches_overfit": sealed_matches_overfit,
                     "sealed_patch_hidden_exit": results[0]["hidden_exit"],
                     "trace": ["seal overfit patch", "workspace changes to repaired source", "run checks on changed workspace"],
                     "condition": "Concurrent or intervening edits; manuscript clean-checkout prose catches this, three-line bash alone does not."})
    a.check("git_clean_verifier_detects_omission_and_input_drift", omitted_result["exit_code"] != 0 and
            drift_tests["exit_code"] == 0 and sealed_matches_overfit and results[0]["hidden_exit"] != 0,
            sources=["B103", "B104"], model="corrected_verification_protocol",
            details={"omission_rejected": True, "drift_sealed_candidate_rejected": True})
    return {"provider": "predeclared deterministic local patch stub; no vendor/model API",
            "semantics": "Half-open UTC interval representing one civil day; manuscript leaves exact billing rule unspecified",
            "git_baseline": "real indexed Git tree, no new commit objects; no PR, push, merge or publication",
            "candidates": results,
            "limitations": ["5 visible tests (2 DST + 3 ordinary), 17 held-out checks, not the illustrative 482 regressions",
                            "AST syntax check is not a project-specific linter; no production secret scanner",
                            "Separate verifier directories provide logical isolation only, same OS user; hidden tests are not a security vault",
                            "No real payment ledger, date-library upgrade, or supplier runtime is exercised"]}

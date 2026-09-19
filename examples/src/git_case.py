"""Real index/tree/patch protocol in independent temporary repositories; no commits."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
BASELINE = '''from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

def window_utc(day, zone):
    start = datetime.combine(day, time.min, ZoneInfo(zone)).astimezone(timezone.utc)
    return start, start + timedelta(hours=24)
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_case(output):
    commands = []

    def call(argv, cwd, *, env=None, ok=True):
        result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=60)
        commands.append({"argv": [str(v) for v in argv], "cwd": str(cwd), "exit": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        if ok and result.returncode:
            raise RuntimeError(commands[-1])
        return result

    def git(repo, *args):
        return call(["git", *args], repo).stdout.strip()

    def baseline(repo):
        (repo / "src").mkdir(parents=True)
        (repo / "src/__init__.py").write_text("")
        (repo / "src/window.py").write_text(BASELINE)
        git(repo, "init", "-q")
        git(repo, "config", "core.autocrlf", "false")
        git(repo, "add", "src")
        return git(repo, "write-tree")

    with tempfile.TemporaryDirectory(prefix="harness-git-") as temp:
        root = Path(temp)
        working = root / "candidate"
        tree = baseline(working)
        shutil.copyfile(HERE / "window.py", working / "src/window.py")
        shutil.copyfile(HERE / "window_helpers.py", working / "src/window_helpers.py")
        # Negative: ordinary git diff really omits the untracked required helper.
        raw = git(working, "diff", "--binary", tree)
        untracked = git(working, "ls-files", "--others", "--exclude-standard").splitlines()
        assert untracked == ["src/window_helpers.py"]
        (output / "untracked_omitted.patch").write_text(raw + "\n")
        # Positive: enumerate/stage the approved paths BEFORE sealing.
        git(working, "add", "--", "src/window.py", "src/window_helpers.py")
        paths = git(working, "diff", "--cached", "--name-only", tree).splitlines()
        assert set(paths) == {"src/window.py", "src/window_helpers.py"}
        patch = git(working, "diff", "--cached", "--binary", tree).encode() + b"\n"
        sealed = output / "candidate.patch"
        sealed.write_bytes(patch)
        sealed_hash = sha(patch)
        candidate_tree = git(working, "write-tree")
        trusted_test = root / "trusted/dst_contract.py"
        trusted_test.parent.mkdir()
        shutil.copyfile(HERE.parent / "tests/dst_contract.py", trusted_test)

        def verify(label, candidate_patch):
            clean = root / label
            assert baseline(clean) == tree
            call(["git", "apply", "--check", str(candidate_patch)], clean)
            call(["git", "apply", "--index", str(candidate_patch)], clean)
            env = dict(os.environ, PYTHONPATH=str(clean), PYTHONDONTWRITEBYTECODE="1",
                       PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
            result = call([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                           "--confcutdir=" + str(trusted_test.parent), str(trusted_test)],
                          clean, env=env, ok=False)
            return {"exit": result.returncode, "tree": git(clean, "write-tree"),
                    "stdout": result.stdout, "stderr": result.stderr}

        good = verify("clean-positive", sealed)
        assert good["exit"] == 0 and good["tree"] == candidate_tree
        omitted = verify("clean-missing-helper", output / "untracked_omitted.patch")
        assert omitted["exit"] == 2 and "ModuleNotFoundError" in omitted["stdout"]
        # Seal the historical overfit algorithm independently; visible two dates pass.
        bad = root / "bad-candidate"
        baseline(bad)
        negative = (HERE / "negative_windows.py").read_text().replace("def hardcoded(", "def window_utc(")
        (bad / "src/window.py").write_text(negative)
        git(bad, "add", "src/window.py")
        bad_patch = output / "hardcoded.patch"
        bad_patch.write_text(git(bad, "diff", "--cached", "--binary", tree) + "\n")
        rejected = verify("clean-hardcoded", bad_patch)
        assert rejected["exit"] == 1 and "failed" in rejected["stdout"]
        # Editing the candidate workspace cannot change the already sealed input.
        (working / "src/window.py").write_text("raise RuntimeError('post-seal drift')\n")
        assert sealed_hash == sha(sealed.read_bytes())
        assert sha((working / "src/window.py").read_bytes()) != sha((HERE / "window.py").read_bytes())
        result = {"kind": "local reference, not vendor replication", "baseline_tree": tree,
                  "candidate_tree": candidate_tree, "patch_sha256": sealed_hash,
                  "tracked_changed_paths": paths, "untracked_before_seal": untracked,
                  "clean_apply": good, "missing_helper_rejected": omitted,
                  "hardcoded_rejected": rejected, "post_seal_workspace_drift_ignored": True,
                  "new_commits": 0, "commands": commands}
    return result

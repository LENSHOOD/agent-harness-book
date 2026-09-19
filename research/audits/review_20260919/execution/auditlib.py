"""Small evidence recorder. Failed invariants remain FAIL even when anticipated."""
import json
import os
from pathlib import Path
import subprocess
import traceback


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


class Audit:
    def __init__(self, root, run, inv):
        self.root, self.run, self.inv = root, run, inv
        self.checks, self.commands, self.errors = [], [], []
        self.data = {}

    def check(self, name, passed, *, sources=(), model="original", details=None,
              expected_failure=False, severity=None):
        item = {"name": name, "sources": list(sources), "model": model,
                "status": "PASS" if passed else "FAIL", "severity": severity if not passed else None,
                "expected_reproduction": (not passed) if expected_failure else bool(passed),
                "expected_failure": expected_failure, "details": details}
        self.checks.append(item)
        print(f'{item["status"]:4} [{model}] {name}')
        dump(self.run / "checks.partial.json", self.checks)
        return item

    def attempt(self, name, fn, *, sources=(), model="original", expected_exception=None, severity=None):
        try:
            value = fn()
        except Exception as exc:
            details = {"exception": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
            self.check(name, False, sources=sources, model=model, details=details,
                       expected_failure=expected_exception is not None and isinstance(exc, expected_exception), severity=severity)
            return None, details
        else:
            self.check(name, True, sources=sources, model=model, details=value)
            if expected_exception is not None:
                self.errors.append({"name": name, "expected_exception_not_raised": str(expected_exception)})
            return value, None

    def command(self, name, argv, cwd, *, env=None, input=None, timeout=30):
        index = len(self.commands) + 1
        prefix = self.run / "commands" / f"{index:03d}_{name}"
        prefix.parent.mkdir(exist_ok=True)
        command_env = os.environ.copy()
        command_env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null",
                            "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0",
                            "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"})
        if env:
            command_env.update(env)
        result = subprocess.run(argv, cwd=cwd, env=command_env, input=input, text=True,
                                capture_output=True, timeout=timeout)
        prefix.with_suffix(".stdout.log").write_text(result.stdout)
        prefix.with_suffix(".stderr.log").write_text(result.stderr)
        item = {"name": name, "argv": argv, "cwd": str(cwd), "exit_code": result.returncode,
                "stdout": result.stdout, "stderr": result.stderr,
                "stdout_file": str(prefix.with_suffix(".stdout.log").relative_to(self.run)),
                "stderr_file": str(prefix.with_suffix(".stderr.log").relative_to(self.run))}
        self.commands.append(item)
        dump(self.run / "commands.json", self.commands)
        print(f'CMD  {name}: exit={result.returncode}')
        return item

    def group(self, name, fn):
        print(f'\nGROUP {name}')
        try:
            self.data[name] = fn(self)
        except Exception:
            error = {"group": name, "traceback": traceback.format_exc()}
            self.errors.append(error)
            print(error["traceback"])
            self.data[name] = {"audit_error": error}
        dump(self.run / f"{name}.json", self.data[name])

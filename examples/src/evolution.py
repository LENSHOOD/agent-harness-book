"""Deterministic 30-trial governance exercise, NOT a model-quality experiment."""
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import sqlite3

FROZEN = {"model": "model-12", "suite": "synthetic-10x3", "environment": "local-v1",
          "policy": "policy-9", "evaluator": "fixed-evaluator-v1", "sealed_test": "sealed-v1"}
REGISTERED = tuple(f"t{i//3:02d}-r{i%3}" for i in range(30))
BASE_BUNDLE = ("harness-42", "model-12", "memory-87", "policy-9", "fixed-evaluator-v1")
NEW_BUNDLE = ("harness-43", "model-12", "memory-88", "policy-9", "fixed-evaluator-v1")


@dataclass(frozen=True)
class Trial:
    trial_id: str
    status: str
    activated: bool
    slice: str
    attempts: int
    cost: int
    security_violations: int = 0


def trials(kind):
    if kind not in {"baseline", "cheat", "candidate", "canary"}:
        raise ValueError("UNKNOWN_FIXTURE")
    rows = []
    for i, trial_id in enumerate(REGISTERED):
        status = ("PASS" if i < 24 else "FAIL") if kind == "baseline" else (
            ("PASS" if i < 18 else "FAIL" if i < 20 else "TIMEOUT") if kind == "cheat" else (
                ("PASS" if i else "FAIL") if kind == "canary" else ("PASS" if i < 28 else "FAIL")))
        rows.append(Trial(trial_id, status, kind != "baseline" and i < 28,
                          "critical" if i < 6 else "ordinary", 3 if status == "TIMEOUT" else 1,
                          3 if status == "TIMEOUT" else 1))
    return rows


def evaluate(rows):
    ids = [r.trial_id for r in rows]
    if len(ids) != 30 or len(set(ids)) != 30 or set(ids) != set(REGISTERED):
        raise ValueError("DENOMINATOR_INTEGRITY")
    expected_slice = {key: "critical" if i < 6 else "ordinary" for i, key in enumerate(REGISTERED)}
    if any(r.slice != expected_slice[r.trial_id] or r.status not in {"PASS", "FAIL", "TIMEOUT"}
           or type(r.activated) is not bool or r.attempts < 1 or r.cost < r.attempts
           or r.security_violations < 0 for r in rows):
        raise ValueError("TRIAL_INTEGRITY")
    successes = sum(r.status == "PASS" for r in rows)
    completed = sum(r.status != "TIMEOUT" for r in rows)
    return {"successes": successes, "denominator": 30, "rate": successes / 30,
            "completed_only_rate_for_negative_demo": successes / completed if completed else None,
            "timeouts": 30 - completed, "activation": sum(r.activated for r in rows),
            "critical_failures": sum(r.status != "PASS" for r in rows if r.slice == "critical"),
            "security_violations": sum(r.security_violations for r in rows), "cost": sum(r.cost for r in rows)}


class FrozenEvaluator:
    def __init__(self):
        self.frozen_json = json.dumps(FROZEN, sort_keys=True)
        self.frozen_sha256 = hashlib.sha256(self.frozen_json.encode()).hexdigest()

    def gate(self, rows, baseline, *, manifest, activation_beacon, declared_denominator=30):
        if json.dumps(manifest, sort_keys=True) != self.frozen_json:
            raise ValueError("FROZEN_EVALUATOR_CHANGED")
        if declared_denominator != 30:
            raise ValueError("DENOMINATOR_INTEGRITY")
        measured, base = evaluate(rows), evaluate(baseline)
        if not activation_beacon or measured["activation"] == 0:
            raise ValueError("NOT_ACTIVATED")
        failures = []
        for field in ("critical_failures", "security_violations"):
            if measured[field] > base[field]:
                failures.append(field)
        if measured["rate"] < base["rate"]:
            failures.append("primary_metric")
        return {"accepted": not failures, "failures": failures, "metrics": measured}


class FinalTest:
    """Persistent one-shot access for the fixture; no claim of an adversarial vault."""
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS accesses (suite TEXT PRIMARY KEY, candidate TEXT NOT NULL)")

    def evaluate_once(self, candidate):
        try:
            with sqlite3.connect(self.path) as db:
                db.execute("INSERT INTO accesses VALUES (?,?)", ("sealed-v1", candidate))
        except sqlite3.IntegrityError as exc:
            raise ValueError("FINAL_TEST_ALREADY_ACCESSED") from exc
        return {"candidate": candidate, "status": "PASS", "fixture_only": True}


class ReleaseController:
    def __init__(self):
        self.current = BASE_BUNDLE
        self.assignments = {"in-flight": BASE_BUNDLE}
        self.events = []

    def canary(self, gate, bundle):
        if not gate["accepted"]:
            self.events.append("REJECT_BEFORE_RELEASE")
            return False
        if tuple(bundle)[1] != BASE_BUNDLE[1] or tuple(bundle)[3:] != BASE_BUNDLE[3:]:
            raise ValueError("FROZEN_BUNDLE_CHANGED")
        self.current = tuple(bundle)
        self.assignments["new-task"] = self.current
        self.events.extend(["SHADOW", "LOW_RISK_CANARY"])
        return True

    def observe(self, measured, baseline):
        if (measured["critical_failures"] > baseline["critical_failures"]
                or measured["security_violations"] > baseline["security_violations"]):
            self.events.append("STOP_NEW_CANDIDATE_TRAFFIC")
            self.current = BASE_BUNDLE
            self.events.append("ROLLBACK_FULL_BUNDLE")


def dump_trials(rows):
    return [asdict(row) for row in rows]

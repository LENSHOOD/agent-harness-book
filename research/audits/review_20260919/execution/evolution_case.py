"""Controlled gate simulation; deterministic outcomes, no model-quality causal claim."""
import hashlib
import json
import math
import traceback
from auditlib import dump

SOURCES = ["B110", "B111", "B112"]
FROZEN = {"model": "model-12", "task_suite": "synthetic-10x3", "sandbox_image": "local-fixture-v1",
          "policy_root": "policy-9", "evaluator": "deterministic-gate-v1", "sealed_test": "sealed-synthetic-v1"}


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def trials(kind):
    rows = []
    for i in range(30):
        if kind == "baseline":
            status = "PASS" if i < 24 else "FAIL"
        elif kind == "denominator_cheat":
            status = "PASS" if i < 18 else "FAIL" if i < 20 else "TIMEOUT"
        else:
            status = "PASS" if i < 28 else "FAIL"
        rows.append({"trial_id": f"t{i//3:02d}-r{i%3}", "task_id": f"task{i//3}", "repeat": i % 3,
                     "slice": "critical" if i < 6 else "ordinary", "status": status,
                     "activated": kind != "baseline" and i < 28,
                     "infra_attempts": 2 if status == "TIMEOUT" else 1,
                     "cost_units": 2 if status == "TIMEOUT" else 1,
                     "security_violations": 0})
    return rows


def wilson(successes, n):
    z = 1.959963984540054
    p = successes / n
    center = (p + z*z/(2*n))/(1 + z*z/n)
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1+z*z/n)
    return [center-half, center+half]


def metrics(rows, registered):
    by_id = {r["trial_id"]: r for r in rows}
    duplicate_ids = len(by_id) != len(rows)
    success = sum(r["status"] == "PASS" for r in rows)
    timeout = sum(r["status"] == "TIMEOUT" for r in rows)
    complete = sum(r["status"] in {"PASS", "FAIL"} for r in rows)
    missing = sorted(set(registered) - set(by_id))
    critical = [r for r in rows if r["slice"] == "critical"]
    return {"registered": len(registered), "observed": len(rows), "successes": success,
            "timeouts_after_retry": timeout, "missing_ids": missing, "duplicate_ids": duplicate_ids,
            "all_registered_success_rate": success/len(registered),
            "completed_only_rate": success/complete if complete else None,
            "wilson95_descriptive_only": wilson(success, len(registered)),
            "activation": sum(r["activated"] for r in rows),
            "critical_failures": sum(r["status"] != "PASS" for r in critical),
            "security_violations": sum(r["security_violations"] for r in rows),
            "cost_per_success": sum(r["cost_units"] for r in rows)/success if success else None}


def gate(candidate, baseline, frozen, beacon, declared_denominator):
    failures = []
    if frozen != FROZEN:
        failures.append("FROZEN_SURFACE_CHANGED")
    if not beacon or candidate["activation"] == 0:
        failures.append("NOT_ACTIVATED")
    if candidate["missing_ids"] or candidate["duplicate_ids"] or declared_denominator != candidate["registered"]:
        failures.append("DENOMINATOR_INTEGRITY")
    if candidate["security_violations"] > baseline["security_violations"]:
        failures.append("SECURITY_REGRESSION")
    if candidate["critical_failures"] > baseline["critical_failures"]:
        failures.append("CRITICAL_SLICE_REGRESSION")
    if candidate["all_registered_success_rate"] < baseline["all_registered_success_rate"]:
        failures.append("PRIMARY_METRIC_REGRESSION")
    return {"accepted": not failures, "failures": failures}


class SealedEvaluator:
    def __init__(self):
        self.used = False

    def evaluate(self, candidate):
        if self.used:
            raise RuntimeError("sealed test already accessed; repeated selection forbidden")
        self.used = True
        return {"candidate": candidate, "status": "PASS", "kind": "deterministic sealed fixture"}


class ReleaseController:
    def __init__(self):
        self.baseline = ("harness-42", "model-12", "memory-87", "policy-9", "evaluator-5")
        self.current = self.baseline
        self.tasks = {"existing-task": self.baseline}
        self.events = []

    def canary(self, gate_result, candidate_bundle):
        if not gate_result["accepted"]:
            self.events.append("REJECT_BEFORE_RELEASE")
            return False
        self.current = candidate_bundle
        self.tasks["new-canary-task"] = candidate_bundle
        self.events.extend(["SHADOW", "LOW_RISK_CANARY"])
        return True

    def observe(self, security_errors, critical_errors):
        if security_errors > 0 or critical_errors > 0:
            self.events.append("STOP_NEW_CANDIDATE_TRAFFIC")
            self.current = self.baseline
            self.events.append("ROLLBACK_FULL_BUNDLE")


def run(a):
    sets = {n: trials(n) for n in ["baseline", "denominator_cheat", "corrected"]}
    registered = [r["trial_id"] for r in sets["baseline"]]
    measured = {n: metrics(rows, registered) for n, rows in sets.items()}
    base, cheat, good = [measured[n] for n in ["baseline", "denominator_cheat", "corrected"]]
    dump(a.run / "evolution_trials.json", sets)
    naive_improvement = cheat["completed_only_rate"] > base["completed_only_rate"]
    actual_improvement = cheat["all_registered_success_rate"] > base["all_registered_success_rate"]
    a.check("evolution_completed_only_ranking_truthful", naive_improvement == actual_improvement,
            sources=SOURCES, model="injected_bad_evaluator", expected_failure=True, severity="INJECTED",
            details={"baseline": base, "cheat": cheat, "naive_improvement": naive_improvement,
                     "registered_improvement": actual_improvement})
    reject = gate(cheat, base, FROZEN, True, 20)
    a.check("evolution_denominator_cheat_rejected", not reject["accepted"] and "DENOMINATOR_INTEGRITY" in reject["failures"],
            sources=SOURCES, model="controlled_gate_simulation", details=reject)
    missing = metrics(sets["denominator_cheat"][:20], registered)
    missing_gate = gate(missing, base, FROZEN, True, 30)
    a.check("evolution_missing_trials_not_dropped", not missing_gate["accepted"] and len(missing["missing_ids"]) == 10 and missing["all_registered_success_rate"] == .6,
            sources=SOURCES, model="controlled_gate_simulation", details={"metrics": missing, "gate": missing_gate})
    frozen_gate = gate(good, base, {**FROZEN, "evaluator": "candidate-owned"}, True, 30)
    activation_gate = gate(good, base, FROZEN, False, 30)
    a.check("evolution_frozen_evaluator_and_activation_enforced", not frozen_gate["accepted"] and not activation_gate["accepted"],
            sources=SOURCES, model="controlled_gate_simulation", details={"frozen": frozen_gate, "activation": activation_gate})
    valid_gate = gate(good, base, FROZEN, True, 30)
    a.check("evolution_candidate_passes_preregistered_synthetic_gates", valid_gate["accepted"], sources=SOURCES,
            model="controlled_gate_simulation", details={"metrics": good, "gate": valid_gate,
                                                       "not_statistical_evidence": "30 scripted trials; rates/CI descriptive. Gate uses exact non-regression only."})
    sealed = SealedEvaluator()
    sealed_result = sealed.evaluate("grouped-dynamic-stub")
    try:
        sealed.evaluate("another-candidate")
    except RuntimeError:
        denied = {"rejected": True, "traceback": traceback.format_exc()}
    else:
        denied = {"rejected": False}
    a.check("evolution_sealed_test_once", denied["rejected"], sources=SOURCES, model="controlled_gate_simulation", details=denied)
    controller = ReleaseController()
    candidate_bundle = ("harness-43", "model-12", "memory-88", "policy-9", "evaluator-5")
    controller.canary(reject, candidate_bundle)
    a.check("evolution_rejected_candidate_no_release", controller.current == controller.baseline, sources=SOURCES,
            model="controlled_gate_simulation", details=controller.events.copy())
    controller.canary(valid_gate, candidate_bundle)
    a.check("evolution_running_task_version_sticky", controller.tasks["existing-task"] == controller.baseline and
            controller.tasks["new-canary-task"] == candidate_bundle, sources=SOURCES, model="controlled_gate_simulation", details=controller.tasks.copy())
    # High overall 29/30, but one critical failure versus zero baseline. Always hard reject.
    canary_rows = [{**r, "status": "PASS"} for r in sets["corrected"]]
    canary_rows[0]["status"] = "FAIL"
    canary = metrics(canary_rows, registered)
    controller.observe(canary["security_violations"], canary["critical_failures"] - base["critical_failures"])
    a.check("evolution_critical_regression_rolls_back_entire_bundle", controller.current == controller.baseline and
            controller.events[-2:] == ["STOP_NEW_CANDIDATE_TRAFFIC", "ROLLBACK_FULL_BUNDLE"],
            sources=SOURCES, model="controlled_gate_simulation", details={"canary": canary, "bundle": controller.current, "events": controller.events})
    return {"kind": "controlled simulation with deterministic provider stub; no real model evolution or external release",
            "frozen": FROZEN, "frozen_hash": digest(FROZEN), "pre_registered_ids": registered,
            "metrics": measured, "cheat_gate": reject, "valid_gate": valid_gate, "sealed": sealed_result,
            "canary_metrics": canary, "release_events": controller.events, "final_bundle": controller.current,
            "limitations": ["No supplier/model API, stochastic trials, trained model, or production canary",
                            "Wilsons assume independent Bernoulli samples; scripted repeated tasks do not support that inference",
                            "No automatic significance or causal benefit claim; 240/228 book counts were not reproduced",
                            "Frozen registry and sealed vault are in-process controls, not adversarial OS isolation"]}

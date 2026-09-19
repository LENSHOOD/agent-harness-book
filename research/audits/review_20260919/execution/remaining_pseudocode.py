"""Execute B014/B078/B091 with original control flow and explicit helper contracts.

Only syntax is translated. Budgets live in helpers when a scenario declares that
contract; the source gains no implicit decrement, break, retry, finally or cleanup.
An OUTSIDE tracing watchdog bounds weak-helper scenarios without repairing them.
"""
from pathlib import Path
from types import SimpleNamespace as NS
import copy
import json
import sys
import tempfile
import time
import traceback

from auditlib import Audit, dump
from inventory import inventory, get_block
from safety_models import translated


class BudgetExhausted(RuntimeError):
    pass


class ChildCancelled(RuntimeError):
    pass


class InvalidChild(RuntimeError):
    pass


class ExecutionLimit(RuntimeError):
    """Audit guard, never a claimed branch in the manuscript."""


class Budget:
    def __init__(self, units):
        self.remaining = units

    def __bool__(self):
        return self.remaining > 0


def bounded_call(fn, *args):
    lines = 0
    started = time.monotonic()
    prior_trace = sys.gettrace()

    def trace(frame, event, arg):
        nonlocal lines
        if event == "line" and frame.f_code.co_filename.endswith("[translation]"):
            lines += 1
            if lines > 240 or time.monotonic() - started > 2:
                raise ExecutionLimit(f"AUDIT_WATCHDOG: source did not finish within {lines} line events / 2s")
        return trace

    sys.settrace(trace)
    try:
        return fn(*args)
    finally:
        sys.settrace(prior_trace)


def capture(fn, *args):
    """Preserve propagated exceptions and traceback outside the translated program."""
    try:
        value = bounded_call(fn, *args)
        return {"outcome": "RETURNED", "value": value, "exception": None}
    except Exception as exc:
        return {"outcome": "AUDIT_ABORTED" if isinstance(exc, ExecutionLimit) else "EXCEPTION",
                "value": None, "exception": type(exc).__name__, "message": str(exc),
                "traceback": traceback.format_exc()}


def loop_case(a, mode):
    block = get_block(a.inv, "01_", 5)
    assert block["id"] == "B014"
    budget = Budget(0 if mode == "zero_budget" else 2)
    context, effects, trace = [], [], []
    model_calls = 0
    spend_budget = mode != "static_budget"

    def model(ctx, tools):
        nonlocal model_calls
        model_calls += 1
        if spend_budget:
            budget.remaining -= 1
        trace.append({"helper": "model", "call": model_calls, "budget": budget.remaining})
        if mode == "normal" and model_calls == 2:
            return NS(is_final=True, answer={"observed": ctx[-1]["value"]})
        return NS(is_final=False, tool_call={"tool": "forbidden" if mode == "invalid_call" else "read"})

    def validate(call):
        trace.append({"helper": "validate", "call": call})
        if call["tool"] != "read":
            raise ValueError("schema/allowlist rejected tool before execute")
        return call

    def execute(call):
        trace.append({"helper": "execute"})
        if mode == "tool_fault":
            raise OSError("injected read failure")
        effects.append("read")
        return {"value": 42}

    ns = {"budget_available": budget, "model": model, "context": context,
          "available_tools": ["read"], "validate": validate, "execute": execute}
    translated(a, block, ns, wrapper="minimal_loop")
    result = capture(ns["minimal_loop"])
    return {"case": mode, "source": block["id"], "helper_contracts": {
        "budget_available": "Budget.__bool__ is remaining>0; predicate itself never spends",
        "model": "deterministic; spends one unit on each decision" if spend_budget else "does NOT spend; always requests read (weak-contract counterexample)",
        "validate": "return original allowed read call; raise ValueError otherwise",
        "execute": "return observation; injected OSError propagates, no hidden retry",
        "context.append": "ordinary list append; no implicit error observation",
        "watchdog": "external source-line guard, max240 line events/2s; AUDIT_ABORTED is not source termination"},
        "result": result, "model_calls": model_calls, "remaining": budget.remaining,
        "effects": effects, "context": context, "trace": trace}


def delegation_case(a, mode):
    block = get_block(a.inv, "11_", 9)
    assert block["id"] == "B078"
    trace, spawned, merged = [], [], []
    parent = NS(capability={"resources": {"repo"}, "tools": {"read", "edit"}, "expiry": 10, "can_delegate": False},
                remaining=3, cancel_token=False)
    spec = NS(objective="bounded one-file observation", output_schema="int-value-v1",
              acceptance_checks=["value=42"], resources={"repo"}, tools={"read"}, deadline=5,
              can_delegate=False, budget=2, inputs=["repo@pinned"])
    if mode == "invalid_spec":
        spec.acceptance_checks = []
    if mode == "budget_reject":
        spec.budget = 4

    def attenuate(capability, **requested):
        trace.append("attenuate")
        return {"resources": sorted(capability["resources"] & requested["resources"]),
                "tools": sorted(capability["tools"] & requested["tools"]),
                "expiry": min(capability["expiry"], requested["ttl"]),
                "can_delegate": capability["can_delegate"] and requested["can_delegate"]}

    def reserve(*, budget, parent_budget, cancellation):
        trace.append("reserve")
        if cancellation:
            raise ChildCancelled("parent cancellation already requested")
        if budget <= 0 or budget > parent_budget:
            raise BudgetExhausted("reservation exceeds remaining parent budget")
        parent.remaining -= budget
        # Reservation is explicit; no hidden cleanup on child failure.
        return {"units": budget, "cancelled": cancellation}

    def spawn(**kwargs):
        trace.append("spawn")
        spawned.append(kwargs)
        def await_or_cancel():
            trace.append("await_or_cancel")
            if mode == "child_timeout":
                raise TimeoutError("injected child deadline exhausted after one bounded attempt")
            if mode == "child_cancelled":
                raise ChildCancelled("cancelled before child produced an artifact")
            return {"value": 0 if mode == "unverified" else 42,
                    "producer": "forged" if mode == "bad_provenance" else "child-1", "schema": "int-value-v1"}
        return NS(await_or_cancel=await_or_cancel, usage={"units": 1})

    def validate_artifact(result):
        trace.append("validate_schema_and_provenance")
        if result["producer"] != "child-1" or result["schema"] != "int-value-v1" or type(result["value"]) is not int:
            raise InvalidChild("schema or producer binding rejected")
        return dict(result)

    def verify_subtask(artifact, checks):
        trace.append("verify_subtask")
        return {"passed": artifact["value"] == 42, "expires_at": 10}

    def reject(results):
        trace.append("reject_unverified_or_expired")
        if any(not r["checks"]["passed"] or r["checks"]["expires_at"] <= 1 for r in results):
            raise InvalidChild("unverified/expired result rejected before merge")

    def merge(results):
        trace.append("merge_in_clean_environment")
        merged.append(copy.deepcopy(results))
        return {"values": [r["artifact"]["value"] for r in results]}

    ns = {"bounded": lambda objective: bool(objective) and len(objective) < 100,
          "attenuate": attenuate, "scheduler": NS(reserve=reserve), "runtime": NS(spawn=spawn),
          "build_minimal_context": lambda spec: {"objective": spec.objective},
          "create_isolated_workspace": lambda inputs: {"workspace": "child-only-memory", "inputs": list(inputs)},
          "validate_schema_and_provenance": validate_artifact, "verify_subtask": verify_subtask,
          "SubagentResult": lambda artifact, checks, usage: {"artifact": artifact, "checks": checks, "usage": usage},
          "reject_unverified_or_expired": reject,
          "detect_semantic_and_resource_conflicts": lambda results: ["overlapping-write"] if mode == "conflict" else [],
          "RESOLUTION_REQUIRED": lambda conflicts: {"status": "RESOLUTION_REQUIRED", "conflicts": conflicts},
          "merge_in_clean_environment": merge,
          "parent_completion_gate": lambda candidate: {"status": "BLOCKED" if mode == "parent_gate_fail" else "VERIFIED", "candidate": candidate}}
    changes = [("function delegate", "def delegate"), ("function integrate", "def integrate"),
               ("spec.objective is bounded", "bounded(spec.objective)"),
               ("spec.output_schema exists", "spec.output_schema is not None"),
               ("spec.acceptance_checks not empty", "bool(spec.acceptance_checks)")]
    translated(a, block, ns, changes=changes)
    delegated = capture(ns["delegate"], parent, spec)
    integrated = None
    if delegated["outcome"] == "RETURNED":
        integrated = capture(ns["integrate"], parent, [delegated["value"]])
    return {"case": mode, "source": block["id"], "helper_contracts": {
        "assertions": "bounded=nonempty objective under100 chars; schema exists means not None; checks nonempty; assertions enabled",
        "attenuate": "intersect resources/tools; min expiry; delegation logical AND; never expand parent rights",
        "scheduler.reserve": "reject insufficient budget/cancelled parent before spawn; decrement parent by reservation; no automatic release",
        "runtime.spawn": "logical memory workspace; no real subprocess/subagent; child spends1 <= lease2",
        "child.await_or_cancel": "one finite operation; normal return or explicit timeout/cancel exception; no sleeps/retry",
        "validate_schema_and_provenance": "tiny fixture schema + producer check; raises on rejection (not a false sentinel)",
        "verify_subtask": "return passed/expiry checks; failed checks do not count as parent success",
        "reject_unverified_or_expired": "raise InvalidChild before merge; ignore-return caller requires this raising contract",
        "detect/merge/parent_gate": "conflict -> RESOLUTION_REQUIRED without merge; otherwise merge then independent gate can BLOCK",
        "watchdog": "same external finite source-line guard as B014"},
        "delegated": delegated, "integrated": integrated, "remaining_budget": parent.remaining,
        "spawned": spawned, "merged": merged, "trace": trace}


def frontier_case(a, mode):
    block = get_block(a.inv, "20_", 1)
    assert block["id"] == "B091"
    units = 0 if mode == "zero_budget" else 1 if mode in {"strict_budget", "accounting_only_budget"} else 3
    budget = Budget(units)
    trace, executed, scores, retained = [], [], [], []
    spend = mode != "static_budget_frontier"
    enforcing = mode != "accounting_only_budget"

    def select(frontier):
        trace.append("select")
        return frontier[0] if mode == "static_budget_frontier" else frontier.pop(0)

    def propose(state):
        trace.append("propose_distinct_hypotheses")
        if mode == "static_budget_frontier":
            return [{"id": "same", "value": 42, "utility": 1, "cost": 1}]
        return [{"id": "fails", "value": 0, "utility": 99, "cost": 1},
                {"id": "good", "value": 42, "utility": 4, "cost": 1},
                {"id": "better", "value": 42, "utility": 5, "cost": 1}]

    def execute(c):
        trace.append("execute:" + c["id"])
        if spend:
            if enforcing and budget.remaining <= 0:
                raise BudgetExhausted("candidate helper refuses next branch; outer for has no budget check")
            budget.remaining -= 1
        executed.append(c["id"])
        return {"candidate": c, "workspace": "isolated-" + c["id"]}

    def verify(result):
        trace.append("external_verifier")
        if mode == "verifier_fault":
            raise RuntimeError("injected independent verifier failure")
        c = result["candidate"]
        score = {"hard_pass": c["value"] == 42, "utility": c["utility"], "cost": c["cost"]}
        scores.append({"candidate": c["id"], **score})
        return score

    def retain(c, score):
        trace.append("retain_if_nondominated")
        # Compare within the same hard-gate class; utility never overrides a hard failure.
        dominates = lambda x, y: x["utility"] >= y["utility"] and x["cost"] <= y["cost"] and (x["utility"] > y["utility"] or x["cost"] < y["cost"])
        peers = [r for r in retained if r["score"]["hard_pass"] == score["hard_pass"]]
        if any(dominates(r["score"], score) for r in peers):
            return
        retained[:] = [r for r in retained if r["score"]["hard_pass"] != score["hard_pass"] or not dominates(score, r["score"])]
        retained.append({"candidate": c["id"], "score": dict(score)})

    def best():
        trace.append("best_candidate_that_passes_hard_gates")
        allowed = [r for r in retained if r["score"]["hard_pass"]]
        return max(allowed, key=lambda r: r["score"]["utility"])["candidate"] if allowed else "NEEDS_ESCALATION"

    ns = {"baseline_state": "baseline", "budget": budget, "select": select,
          "propose_distinct_hypotheses": propose, "execute_in_isolated_branch": execute,
          "external_verifier": verify, "retain_if_nondominated": retain,
          "best_candidate_that_passes_hard_gates": best}
    translated(a, block, ns, wrapper="frontier_search")
    result = capture(ns["frontier_search"])
    return {"case": mode, "source": block["id"], "helper_contracts": {
        "budget": "remaining>0 Boolean; source contains no decrement",
        "select": "return first WITHOUT removal" if mode == "static_budget_frontier" else "pop first frontier state (explicit progress contract)",
        "propose_distinct_hypotheses": "finite list; max3 branches; no hidden loop",
        "execute_in_isolated_branch": "does not spend (weak contract)" if not spend else "decrement only, may go negative" if not enforcing else "check remaining and debit1 before each branch; raise BudgetExhausted if zero",
        "external_verifier": "hard_pass from value=42; deterministic utility/cost; injected exception propagates",
        "retain_if_nondominated": "update separate result archive by utility/cost within hard-gate class; no hidden frontier insertion",
        "best_candidate_that_passes_hard_gates": "return highest-utility hard-pass candidate or NEEDS_ESCALATION when none",
        "watchdog": "outside source:240 line events/2s; records AUDIT_ABORTED, not a successful source stop"},
        "result": result, "initial_budget": units, "remaining": budget.remaining, "executed": executed,
        "scores": scores, "retained": retained, "trace": trace}


def run(a):
    cases = {"B014": {}, "B078": {}, "B091": {}}
    def check(block, name, passed, detail, *, failure=False, severity=None):
        return a.check(name, passed, sources=[block], model="faithful_helper_contract_simulation",
                       details=detail, expected_failure=failure, severity=severity)

    for mode in ["normal", "zero_budget", "budget_exhausted", "invalid_call", "tool_fault", "static_budget"]:
        d = loop_case(a, mode)
        cases["B014"][mode] = d
    d = cases["B014"]["normal"]
    check("B014", "B014_normal_tool_then_final", d["result"]["value"] == {"observed": 42} and d["model_calls"] == 2 and len(d["effects"]) == 1, d)
    for mode, expected_calls in [("zero_budget", 0), ("budget_exhausted", 2)]:
        d = cases["B014"][mode]
        check("B014", "B014_" + mode + "_terminates", d["result"]["outcome"] == "RETURNED" and d["result"]["value"] is None and d["model_calls"] == expected_calls and d["remaining"] == 0, d)
    d = cases["B014"]["invalid_call"]
    check("B014", "B014_validation_rejects_before_execute", d["result"]["exception"] == "ValueError" and not d["effects"], d)
    d = cases["B014"]["tool_fault"]
    check("B014", "B014_injected_tool_fault_unhandled", d["result"]["exception"] is None, d, failure=True, severity="INJECTED")
    check("B014", "B014_fault_preserved_without_retry_or_fake_observation", d["result"]["exception"] == "OSError" and d["model_calls"] == 1 and not d["context"], d)
    d = cases["B014"]["static_budget"]
    check("B014", "B014_static_budget_source_terminates", d["result"]["outcome"] == "RETURNED", d, failure=True, severity="P2")

    for mode in ["normal", "invalid_spec", "budget_reject", "child_timeout", "child_cancelled", "bad_provenance", "unverified", "conflict", "parent_gate_fail"]:
        cases["B078"][mode] = delegation_case(a, mode)
    d = cases["B078"]["normal"]
    cap = d["spawned"][0]["capability"]
    check("B078", "B078_delegate_attenuate_merge_parent_verify", d["integrated"]["value"]["status"] == "VERIFIED" and cap == {"resources": ["repo"], "tools": ["read"], "expiry": 5, "can_delegate": False} and d["remaining_budget"] == 1 and len(d["merged"]) == 1, d)
    for mode, exc in [("invalid_spec", "AssertionError"), ("budget_reject", "BudgetExhausted")]:
        d = cases["B078"][mode]
        check("B078", "B078_" + mode + "_before_spawn", d["delegated"]["exception"] == exc and not d["spawned"] and d["remaining_budget"] == 3, d)
    d = cases["B078"]["child_timeout"]
    check("B078", "B078_injected_child_timeout_unhandled", d["delegated"]["exception"] is None, d, failure=True, severity="INJECTED")
    check("B078", "B078_timeout_releases_unused_reservation_in_source", d["remaining_budget"] == 2,
          d | {"reservation": 2, "child_usage": 1, "expected_available_after_settlement": 2}, failure=True, severity="P2")
    for mode, exc in [("child_cancelled", "ChildCancelled"), ("bad_provenance", "InvalidChild")]:
        d = cases["B078"][mode]
        check("B078", "B078_" + mode + "_no_merge", d["delegated"]["exception"] == exc and not d["merged"] and d["integrated"] is None, d)
    d = cases["B078"]["unverified"]
    check("B078", "B078_unverified_child_rejected_at_integration", d["delegated"]["value"]["checks"]["passed"] is False and d["integrated"]["exception"] == "InvalidChild" and not d["merged"], d)
    d = cases["B078"]["conflict"]
    check("B078", "B078_conflict_requires_resolution_without_merge", d["integrated"]["value"]["status"] == "RESOLUTION_REQUIRED" and not d["merged"], d)
    d = cases["B078"]["parent_gate_fail"]
    check("B078", "B078_child_pass_not_parent_success", d["delegated"]["value"]["checks"]["passed"] and d["integrated"]["value"]["status"] == "BLOCKED", d)

    for mode in ["normal", "zero_budget", "strict_budget", "accounting_only_budget", "verifier_fault", "static_budget_frontier"]:
        cases["B091"][mode] = frontier_case(a, mode)
    d = cases["B091"]["normal"]
    check("B091", "B091_normal_progress_nondomination_hard_gate", d["result"]["value"] == "better" and len(d["executed"]) == 3 and d["remaining"] == 0 and [r["candidate"] for r in d["retained"]] == ["fails", "better"], d)
    d = cases["B091"]["zero_budget"]
    check("B091", "B091_zero_budget_no_branch_escalates", d["result"]["value"] == "NEEDS_ESCALATION" and not d["executed"], d)
    d = cases["B091"]["strict_budget"]
    check("B091", "B091_mid_batch_budget_exhaustion_graceful_return", d["result"]["outcome"] == "RETURNED", d, failure=True, severity="P2")
    check("B091", "B091_strict_helper_limits_actual_spend", d["result"]["exception"] == "BudgetExhausted" and len(d["executed"]) == 1 and d["remaining"] == 0, d)
    d = cases["B091"]["accounting_only_budget"]
    check("B091", "B091_outer_budget_guard_prevents_batch_overspend", d["remaining"] >= 0, d, failure=True, severity="P2")
    d = cases["B091"]["verifier_fault"]
    check("B091", "B091_injected_verifier_fault_unhandled", d["result"]["exception"] is None, d, failure=True, severity="INJECTED")
    check("B091", "B091_verifier_fault_has_no_fabricated_score", d["result"]["exception"] == "RuntimeError" and not d["scores"] and not d["retained"], d)
    d = cases["B091"]["static_budget_frontier"]
    check("B091", "B091_static_frontier_budget_source_terminates", d["result"]["outcome"] == "RETURNED", d, failure=True, severity="P2")
    return {"cases": cases, "scope": "Actual Python execution of minimally translated manuscript control flow with deterministic helper doubles; no vendor runtime",
            "syntax_changes": {"B014": "wrap original block in def minimal_loop; no source-body changes",
                               "B078": "function->def; three assertions translated to Python predicates, no added control flow",
                               "B091": "wrap original block in def frontier_search; no source-body changes"},
            "limits": "21 scenarios; every helper finite; outside watchdog bounds non-progress loops. No empirical model, budget threshold or production isolation claim.",
            "interpretation": "P2 findings are explicit missing helper/termination/cleanup contracts. B014 itself disclaims being an enterprise harness; do not call these vendor exploits."}


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    root = here.parents[3]
    (here / "probes").mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="remaining_", dir=here / "probes"))
    audit = Audit(root, folder, inventory(root))
    audit.group("remaining_pseudocode", run)
    dump(folder / "probe_checks.json", audit.checks)
    dump(folder / "probe_errors.json", audit.errors)
    print("PROBE_DIRECTORY", folder)
    raise SystemExit(2 if audit.errors or any(not c["expected_reproduction"] for c in audit.checks) else 0)

"""Faithful control-flow translations and explicitly separate corrective models.

Helpers are deterministic test doubles, NOT vendor runtimes, IAM, or production services.
Faithful translations do not add an implicit deny gate, non-returning suspend, or executor
exception normalization. Each of those hidden helper contracts would change the findings.
"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import sqlite3
import textwrap
import threading
from types import SimpleNamespace as NS
from auditlib import dump
from inventory import get_block


@dataclass
class Decision:
    kind: str
    reason: str = "policy"
    constraints: tuple = ()
    capability: object = None

    @property
    def requires_human(self):
        return self.kind == "REQUIRE_APPROVAL"

    @property
    def requires_approval(self):
        return self.requires_human

    def __eq__(self, other):
        return self.kind == (other.kind if isinstance(other, Decision) else other)


def translated(a, block, namespace, *, wrapper=None, changes=()):
    raw = block["raw"]
    for before, after in changes:
        if before not in raw:
            raise ValueError(f"Translation source changed: {before}")
        raw = raw.replace(before, after)
    if wrapper:
        raw = "def " + wrapper + "():\n" + textwrap.indent(raw, "    ")
    # .txt is evidence, not a claimed runnable source file with unresolved helpers.
    (a.run / f'{block["id"]}_translation.txt').write_text(raw)
    namespace.update({"DENY": "DENY", "REQUIRE_APPROVAL": "REQUIRE_APPROVAL", "PASS": "PASS",
                      "CANDIDATE_VERIFIED": "CANDIDATE_VERIFIED", "NEEDS_ESCALATION": "NEEDS_ESCALATION"})
    exec(compile(raw, f'{block["file"]}:{block["line"]}[translation]', "exec"), namespace)
    return namespace


def appendix_loop(a, decisions):
    block = get_block(a.inv, "A_", 2)
    events, effects, suspended = [], [], []
    attempt = NS(id="A1", active=True)
    progress = {"step": 0}

    def decide(context, tools):
        i = progress["step"]
        progress["step"] += 1
        return NS(requests_action=True, action=NS(id=f"action-{i}", kind=decisions[i]))

    def reduce(obs):
        attempt.active = progress["step"] < len(decisions)

    def execute(action, constraints):
        effects.append(action.id)
        return {"action_id": action.id, "status": "OK"}

    ns = {"attempt": attempt, "state_store": NS(load=lambda _: NS(artifacts=[]), reduce=reduce),
          "context_compiler": NS(project=lambda *args: {}), "budget": NS(remaining=True),
          "model": NS(decide=decide), "model_facing_tool_views": [], "current_authority": None,
          "normalize_validate_and_assign_id": lambda x: x,
          "policy": NS(evaluate=lambda action, _: Decision(action.kind)),
          "event_store": NS(append=lambda *args: events.append(args)),
          "denied_observation": lambda reason: {"status": "DENIED", "reason": reason},
          "suspend_attempt_with_checkpoint": lambda *args: suspended.append("checkpoint"),
          "continue_after_external_response": lambda: None, "commit_effect_safely": execute}
    translated(a, block, ns, wrapper="faithful_loop")
    return ns["faithful_loop"], {"events": events, "effects": effects, "suspended": suspended}


class MemoryLedger:
    def __init__(self):
        self.effects = {}
        self.lock = threading.Lock()

    def insert_if_absent(self, effect):
        with self.lock:
            self.effects.setdefault(effect.id, {"status": "INTENT_RECORDED"})

    def mark(self, key, status):
        with self.lock:
            self.effects[key]["status"] = status

    def mark_executing(self, key):
        self.mark(key, "EXECUTING")

    def mark_unknown(self, key):
        self.mark(key, "UNKNOWN_EFFECT")

    def mark_committed(self, key, ref):
        self.mark(key, "COMMITTED")

    def mark_final(self, key, outcome):
        self.mark(key, "COMMITTED")


class Target:
    def __init__(self, *, barrier=None, lose_response=False, stale_lookup=False, uncertain_result=False):
        self.calls = []
        self.barrier, self.lose_response = barrier, lose_response
        self.stale_lookup, self.uncertain_result = stale_lookup, uncertain_result
        self.lock = threading.Lock()

    def lookup(self, key):
        with self.lock:
            found = any(x[0] == key for x in self.calls) and not self.stale_lookup
        if self.barrier:
            self.barrier.wait(timeout=5)  # deterministically both observe absence
        return NS(is_committed=found, ref=key)

    def execute(self, operation):
        with self.lock:
            self.calls.append(operation)
            lose = self.lose_response
            self.lose_response = False
        if lose:
            raise TimeoutError("target committed; response lost before durable outcome")
        return NS(is_definitive=not self.uncertain_result, ref=operation[0], status="OK")


def effect_model(a, target):
    block = get_block(a.inv, "A_", 3)
    ledger = MemoryLedger()
    ns = {"EffectIntent": lambda **kw: NS(id=kw["effect_id"], **kw), "stable_id": lambda x: x,
          "constrained": lambda action, _: (action.idempotency_key, action.payload),
          "INTENT_RECORDED": "INTENT_RECORDED", "durable_store": ledger, "target_system": target,
          "observation_from": lambda prior: NS(ref=prior.ref, status="OK"), "executor": target,
          "Observation": lambda **kw: NS(**kw), "UNKNOWN_EFFECT": "UNKNOWN_EFFECT",
          "reconcile_required": "reconcile_required"}
    translated(a, block, ns, changes=[("commit_effect_safely(action, constraints):", "def commit_effect_safely(action, constraints):")])
    return ns["commit_effect_safely"], ledger


def ch6(a, kinds, *, cancel_after_first=False):
    block = get_block(a.inv, "06_", 7)
    trace, effects = [], []
    state = NS(terminal=False, cancelled=False)

    def enforce(st):
        trace.append("check_cancel")
        if st.cancelled:
            st.terminal = True
            raise RuntimeError("cancelled")

    def execute(action):
        effects.append(action.id)
        if cancel_after_first:
            state.cancelled = True

    ns = {"state": state, "current_state": state, "restore_or_create_state": lambda _: None,
          "terminal": lambda st: st.terminal, "enforce_budget_and_cancellation": enforce,
          "context_needs_compaction": lambda st: False, "build_context": lambda st: {},
          "call_model": lambda _: NS(requests_actions=True, actions=[NS(id=str(i), kind=k) for i, k in enumerate(kinds)]),
          "persist": lambda _: None, "plan_execution": lambda actions: actions,
          "validate_schema": lambda action: None, "authorize": lambda action, _: Decision(action.kind),
          "suspend_with_durable_approval_request": lambda: trace.append("suspended_helper_returned"),
          "execute_with_effect_ledger": execute}
    # Run one model batch; termination predicate ends next loop, leaving body untouched.
    seen = {"count": 0}
    def terminal(st):
        seen["count"] += 1
        return seen["count"] > 1
    ns["terminal"] = terminal
    translated(a, block, ns, changes=[("function run_turn", "def run_turn")])
    ns["run_turn"]("turn1")
    return {"effects": effects, "trace": trace, "cancelled": state.cancelled}


def ch10(a, decision):
    block = get_block(a.inv, "10_", 8)
    effects = []
    class Results(list):
        def has_integrity_violation(self): return False
        def has_ambiguous_or_flaky_signal(self): return False
        def mandatory_failed(self): return False
    passed_check = NS(version="v1", environment_digest="local", held_out_ref="sealed")
    ns = {"Results": Results, "load_pinned_contract": lambda _: NS(acceptance_checks=[passed_check]),
          "trusted_registry": NS(resolve=lambda _: NS(run=lambda **kw: ["PASS"])),
          "seal_candidate": lambda x: x, "build_evidence_package": lambda *args: {},
          "policy": NS(evaluate_commit=lambda _: Decision(decision)),
          "AWAITING_APPROVAL": lambda x: "AWAITING_APPROVAL",
          "commit_idempotently": lambda snapshot, capability: effects.append(snapshot),
          "reconcile_and_attest": lambda *args: "VERIFIED_COMPLETE"}
    translated(a, block, ns, changes=[("function attempt_completion", "def attempt_completion"),
                                      ("results = []", "results = Results()")])
    result = ns["attempt_completion"](NS(contract_version="v1"), "candidate")
    return {"result": result, "effects": effects, "assumption": "All checks pass; commit helper does not itself enforce capability."}


class CorrectedEffect:
    """Explicit extra assumptions: SQL uniqueness at target + args binding + reconcile before retry."""
    def __init__(self, path):
        self.path = path
        with sqlite3.connect(path) as db:
            db.execute("CREATE TABLE ledger(k TEXT PRIMARY KEY,args TEXT,status TEXT)")
            db.execute("CREATE TABLE target(k TEXT PRIMARY KEY,args TEXT)")

    def perform(self, key, payload, *, lose_response=False, barrier=None, lookup_available=True, cancelled=False):
        args = json.dumps(payload, sort_keys=True)
        with sqlite3.connect(self.path, timeout=10) as db:
            prior = db.execute("SELECT args,status FROM ledger WHERE k=?", (key,)).fetchone()
            if prior and prior[0] != args:
                raise ValueError("idempotency key reused with different args")
            if cancelled:
                return "CANCELLED"
            db.execute("INSERT OR IGNORE INTO ledger VALUES(?,?,?)", (key, args, "INTENT_RECORDED"))
        if prior and prior[1] in {"UNKNOWN_EFFECT", "EXECUTING"} and not lookup_available:
            return "RECONCILE_REQUIRED"
        with sqlite3.connect(self.path, timeout=10) as db:
            found = db.execute("SELECT args FROM target WHERE k=?", (key,)).fetchone()
        if barrier:
            barrier.wait(timeout=5)
        if not found:
            with sqlite3.connect(self.path, timeout=10) as db:
                db.execute("UPDATE ledger SET status='EXECUTING' WHERE k=?", (key,))
            try:
                with sqlite3.connect(self.path, timeout=10) as db:
                    db.execute("INSERT OR IGNORE INTO target VALUES(?,?)", (key, args))
                if lose_response:
                    raise TimeoutError("response lost after target commit")
            except TimeoutError as exc:
                with sqlite3.connect(self.path, timeout=10) as db:
                    db.execute("UPDATE ledger SET status='UNKNOWN_EFFECT' WHERE k=?", (key,))
                # Intentional state transition, with original exception retained in returned evidence.
                import traceback
                return {"status": "UNKNOWN_EFFECT", "exception": type(exc).__name__, "traceback": traceback.format_exc()}
        with sqlite3.connect(self.path, timeout=10) as db:
            db.execute("UPDATE ledger SET status='COMMITTED' WHERE k=?", (key,))
        return "OK"

    def inspect(self):
        with sqlite3.connect(self.path) as db:
            return {"effects": list(db.execute("SELECT * FROM target ORDER BY k")),
                    "ledger": list(db.execute("SELECT * FROM ledger ORDER BY k"))}


def run(a):
    results = {}
    block_a, block_e, block_recover = "B002", "B003", "B004"
    fn, data = appendix_loop(a, ["DENY"])
    fn()
    a.check("A_DENY_zero_execution", not data["effects"], sources=[block_a], model="faithful_simulation", details=data)
    fn, data = appendix_loop(a, ["REQUIRE_APPROVAL"])
    a.attempt("A_approval_first_observation_defined", fn, sources=[block_a], model="faithful_simulation",
              expected_exception=UnboundLocalError, severity="P1")
    results["approval_first"] = data
    fn, data = appendix_loop(a, ["ALLOW", "REQUIRE_APPROVAL"])
    fn()
    observations = [event[0] for event in data["events"] if len(event) == 1]
    a.check("A_approval_does_not_reuse_prior_observation", len({o.get("action_id") for o in observations}) == len(observations),
            sources=[block_a], model="faithful_simulation", details=data, expected_failure=True, severity="P1")
    results["approval_stale"] = data
    for name, kinds, cancel, expected in [("DENY", ["DENY"], False, 0),
                                           ("approval_batch", ["REQUIRE_APPROVAL", "ALLOW"], False, 0),
                                           ("cancel_in_batch", ["ALLOW", "ALLOW"], True, 1)]:
        out = ch6(a, kinds, cancel_after_first=cancel)
        a.check("CH6_" + name, len(out["effects"]) == expected, sources=["B037"],
                model="faithful_simulation", details=out, expected_failure=True, severity="P1")
        results[name] = out
    out = ch10(a, "DENY")
    a.check("CH10_DENY_zero_commit", not out["effects"], sources=["B069"], model="faithful_simulation",
            details=out, expected_failure=True, severity="P1")
    out = ch10(a, "REQUIRE_APPROVAL")
    a.check("CH10_approval_zero_commit", not out["effects"] and out["result"] == "AWAITING_APPROVAL",
            sources=["B069"], model="faithful_simulation", details=out)

    action = NS(id="effect1", idempotency_key="key1", resource="local-target", payload={"amount": 10})
    target = Target()
    fn, ledger = effect_model(a, target)
    fn(action, ())
    fn(action, ())
    a.check("A_sequential_repeat_idempotent_with_strong_lookup", len(target.calls) == 1, sources=[block_e],
            model="faithful_simulation", details={"calls": target.calls, "ledger": ledger.effects})
    target = Target(lose_response=True)
    fn, ledger = effect_model(a, target)
    a.attempt("A_lost_response_exception_normalized", lambda: fn(action, ()), sources=[block_e],
              model="faithful_simulation", expected_exception=TimeoutError, severity="P1")
    a.check("A_lost_response_marks_unknown", ledger.effects["effect1"]["status"] == "UNKNOWN_EFFECT",
            sources=[block_e], model="faithful_simulation", details=ledger.effects, expected_failure=True, severity="P1")
    fn(action, ())
    a.check("A_lost_response_recovery_strong_lookup_no_duplicate", len(target.calls) == 1, sources=[block_e],
            model="faithful_simulation", details={"calls": target.calls, "ledger": ledger.effects})
    target = Target(uncertain_result=True)
    fn, ledger = effect_model(a, target)
    out = fn(action, ())
    a.check("A_nondefinitive_return_marks_unknown", out.status == "UNKNOWN_EFFECT" and ledger.effects["effect1"]["status"] == "UNKNOWN_EFFECT",
            sources=[block_e], model="faithful_simulation", details=ledger.effects)
    target = Target(stale_lookup=True, lose_response=True)
    fn, ledger = effect_model(a, target)
    a.attempt("A_stale_lookup_setup_timeout", lambda: fn(action, ()), sources=[block_e],
              model="faithful_simulation", expected_exception=TimeoutError, severity="P1")
    fn(action, ())
    a.check("A_retry_with_stale_lookup_exactly_once", len(target.calls) == 1, sources=[block_e],
            model="faithful_simulation", details={"calls": target.calls, "ledger": ledger.effects}, expected_failure=True, severity="P1")
    target = Target(barrier=threading.Barrier(2))
    fn, ledger = effect_model(a, target)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fn, action, ()) for _ in range(2)]
        [f.result(timeout=10) for f in futures]  # any worker exception propagates to audit error
    a.check("A_concurrent_lookup_then_execute_exactly_once", len(target.calls) == 1, sources=[block_e],
            model="faithful_simulation", details={"calls": target.calls, "ledger": ledger.effects}, expected_failure=True, severity="P1")
    results["race"] = {"calls": target.calls, "ledger": ledger.effects}

    # Literal recovery/cancel ordering, with explicitly returning helpers.
    trace = []
    state = NS(status="RUNNING", pending_or_unknown_effects=[], required_capabilities=["read"], active_children=1)
    def log(name):
        trace.append(name)
    def cancel_children(_):
        state.active_children = 0
        log("cancel_children")
    def mark_cancelled(_):
        if state.active_children == 0:
            state.status = "CANCELLED"
        log("mark_cancelled_when_quiescent")
    def resume(st, policy, credentials):
        st.status = "RUNNING"
        log("resume")
    ns = {"coordinator": NS(acquire_single_owner=lambda _: log("single_owner")),
          "state_store": NS(latest_checkpoint=lambda _: NS(event_offset=0),
                            mark_cancel_requested=lambda *args: log("cancel_requested"),
                            mark_cancelled_when_quiescent=mark_cancelled),
          "replay_pure_events": lambda offset: state,
          "policy_store": NS(load_current_compatible_version=lambda: "current-v2"),
          "broker": NS(issue_fresh_leases=lambda caps: {"new": "lease2"}),
          "resume_from_reconciled_state": resume, "scheduler": NS(cancel_children=cancel_children),
          "executor": NS(terminate_process_tree=lambda _: log("terminate_process_tree")),
          "revoke_temporary_credentials": lambda _: log("revoke"),
          "reconcile_pending_effects": lambda _: log("reconcile")}
    translated(a, get_block(a.inv, "A_", 4), ns,
               changes=[("recover(attempt_id):", "def recover(attempt_id):"),
                        ("cancel(attempt_id, reason):", "def cancel(attempt_id, reason):")])
    ns["cancel"]("A1", "user")
    a.check("A_cancel_order_and_quiescence", state.status == "CANCELLED" and trace ==
            ["cancel_requested", "cancel_children", "terminate_process_tree", "revoke", "reconcile", "mark_cancelled_when_quiescent"],
            sources=[block_recover, "B035"], model="faithful_simulation", details=list(trace))
    ns["recover"]("A1")
    a.check("A_recover_terminal_cancelled_does_not_resume", state.status == "CANCELLED", sources=[block_recover],
            model="faithful_simulation", details={"trace": list(trace), "status": state.status,
                                               "assumption": "Caller permits recover(cancelled); resume helper lacks terminal guard."}, expected_failure=True, severity="P1")

    corrected = CorrectedEffect(a.run / "corrected_effects.sqlite")
    fixed_events, fixed_effects = [], []
    def safe_action(decision, action_id, *, response=None, current_allow=True, cancelled=False):
        if cancelled:
            return "CANCELLED"
        if decision == "DENY" or not current_allow:
            fixed_events.append((action_id, "DENIED"))
            return "DENIED"
        if decision == "REQUIRE_APPROVAL":
            fixed_events.append((action_id, "WAITING_FOR_APPROVAL"))
            if response != "APPROVED":
                return "SUSPENDED"
        if decision not in {"ALLOW", "CONSTRAINED_ALLOW", "REQUIRE_APPROVAL"}:
            return "DENIED"
        fixed_effects.append(action_id)
        fixed_events.append((action_id, "OK"))
        return "OK"
    for decision in ["DENY", "REQUIRE_APPROVAL", "UNKNOWN_DECISION"]:
        safe_action(decision, decision)
    a.check("corrected_deny_pending_unknown_zero_execution", not fixed_effects, sources=[block_a, "B037", "B069"],
            model="corrected_simulation", details=list(fixed_events))
    before = len(fixed_effects)
    safe_action("REQUIRE_APPROVAL", "revoked", response="APPROVED", current_allow=False)
    safe_action("REQUIRE_APPROVAL", "cancelled", response="APPROVED", cancelled=True)
    a.check("corrected_approval_revalidate_revocation_and_cancellation", len(fixed_effects) == before,
            sources=[block_a, "B037"], model="corrected_simulation", details=list(fixed_events))
    safe_action("REQUIRE_APPROVAL", "approved", response="APPROVED")
    a.check("corrected_approval_explicit_observation", fixed_effects == ["approved"] and fixed_events[-1] == ("approved", "OK"),
            sources=[block_a], model="corrected_simulation", details=list(fixed_events))
    lost = corrected.perform("lost", {"amount": 10}, lose_response=True)
    a.check("corrected_lost_response_recorded_unknown", lost["status"] == "UNKNOWN_EFFECT",
            sources=[block_e], model="corrected_simulation", details=lost)
    defer = corrected.perform("lost", {"amount": 10}, lookup_available=False)
    a.check("corrected_unknown_unavailable_lookup_not_retried", defer == "RECONCILE_REQUIRED" and len(corrected.inspect()["effects"]) == 1,
            sources=[block_e], model="corrected_simulation", details=corrected.inspect())
    recovered = corrected.perform("lost", {"amount": 10})
    a.check("corrected_recover_lost_once", recovered == "OK" and len(corrected.inspect()["effects"]) == 1,
            sources=[block_e], model="corrected_simulation", details=corrected.inspect())
    barrier = threading.Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        fs = [pool.submit(corrected.perform, "concurrent", {"amount": 20}, barrier=barrier) for _ in range(2)]
        outputs = [f.result(timeout=15) for f in fs]
    a.check("corrected_target_atomic_idempotency_under_race", outputs == ["OK", "OK"] and
            len([r for r in corrected.inspect()["effects"] if r[0] == "concurrent"]) == 1,
            sources=[block_e], model="corrected_simulation", details=corrected.inspect())
    try:
        corrected.perform("concurrent", {"amount": 99})
    except ValueError as exc:
        import traceback
        collision = {"rejected": True, "exception": str(exc), "traceback": traceback.format_exc()}
    else:
        collision = {"rejected": False}
    a.check("corrected_key_args_collision_rejected", collision["rejected"], sources=[block_e],
            model="corrected_simulation", details=collision)
    state = {"status": "RUNNING", "children": ["child1"], "credentials": "old", "effect": "COMMITTED",
             "cancel_requested_at": 20, "effect_committed_at": 19, "policy": "v1"}
    state.update(status="CANCELLING", children=[], credentials=None)
    state["reconciled_effect"] = state["effect"]
    state["status"] = "CANCELLED"
    def corrected_recover(st):
        if st["status"] in {"CANCELLED", "COMPLETED", "FAILED"}:
            return "TERMINAL_NO_RESUME"
        st.update(policy="v2", credentials="fresh-lease", status="RUNNING")
        return "RESUMED"
    stopped = corrected_recover(state)
    a.check("corrected_cancel_committed_effect_retained_no_resume", stopped == "TERMINAL_NO_RESUME" and state["reconciled_effect"] == "COMMITTED",
            sources=[block_recover, "B035"], model="corrected_simulation", details=state)
    suspended = {"status": "SUSPENDED", "policy": "v1", "credentials": "expired"}
    corrected_recover(suspended)
    a.check("corrected_resume_fresh_policy_and_credentials", suspended["policy"] == "v2" and suspended["credentials"] == "fresh-lease",
            sources=[block_recover], model="corrected_simulation", details=suspended)
    results["corrected_effect_store"] = corrected.inspect()
    results["limitations"] = ["Faithful helpers are deterministic and explicit; absence of an outer/helper guard is a conditional counterexample, not a vendor exploit.",
                               "Cancellation/recovery is a state simulation, not an OS process-tree or remote IAM validation.",
                               "Corrected target supplies atomic key uniqueness and argument binding; a local ledger alone cannot guarantee exactly-once remote effects.",
                               "Actual process death, streaming reconnect, compaction, model drift, multi-agent orphan handling are not tested."]
    return results

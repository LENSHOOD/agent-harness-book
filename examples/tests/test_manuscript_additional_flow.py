"""Execute current chapter 1/11/20 source with explicit deterministic helper contracts.

This checks orchestration/ordering and modeled accounting, not real providers,
process trees, distributed cancellation, persistent resource recovery, or model quality.
Chapter 1 host pause/cancel/budget signals propagate; no hidden source catch is added.
Chapter 20 propose/run/check helpers construct deferred Operations; only the host
performs work after paid() reserves. Treating those helpers as eager would be unsafe
and is outside this stated contract. Every syntax translation is stored with evidence.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace as NS
import pytest
from jsonschema import Draft202012Validator

from src.extended_manuscript import additional_sources
from src.manuscript import bounded_call, compile_function, fences

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def current_sources():
    return additional_sources(fences(ROOT))


@pytest.fixture
def policy_schema():
    schemas = [(block, json.loads(block["raw"])) for block in fences(ROOT)
               if block["file"].endswith("E_machine_readable_contracts.md") and block["language"] == "json"]
    messages = [(block, schema) for block, schema in schemas if "PolicyDecision" in schema.get("$defs", {})]
    assert len(messages) == 1
    block, schema = messages[0]
    selected = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/PolicyDecision"}
    Draft202012Validator.check_schema(selected)
    return Draft202012Validator(selected), {k: block[k] for k in ("file", "line", "sha256")}


def persist_case(evidence, name, case, source, metadata, result, events, **extra):
    evidence[1](f"literal_{name}_{case}.json", {
        "kind": "current source control flow with declared deterministic helpers",
        "source": metadata, "translation": source, "result": result, "events": events, **extra,
    })


class BudgetExhausted(Exception):
    pass


class PauseRequested(Exception):
    pass


class CancellationRequested(Exception):
    pass


@pytest.mark.parametrize("case", [
    "candidate", "max_steps", "static_budget", "budget_stop", "pause", "cancel",
    "write_rejected", "tool_fault", "model_fault",
])
def test_current_minimal_loop(case, current_sources, evidence):
    source, metadata = current_sources["minimal_loop"]
    events, context = [], []
    remaining, spent, unsettled = 20, 0, []
    if case == "budget_stop":
        remaining = 2

    def reserve():
        nonlocal remaining
        if context and case in {"pause", "cancel"}:
            signal = PauseRequested if case == "pause" else CancellationRequested
            events.append(signal.__name__)
            raise signal("host stops before another model call")
        if remaining < 2:
            events.append("BUDGET_STOP")
            raise BudgetExhausted("no new model/tool call")
        ticket = NS(bound=2, used=0)
        unsettled.append(ticket)
        if case != "static_budget":
            remaining -= 2
        events.append("RESERVE")
        return ticket

    def settle(ticket):
        nonlocal remaining, spent
        assert 0 <= ticket.used <= ticket.bound and ticket in unsettled
        if case != "static_budget":
            remaining += ticket.bound - ticket.used
        spent += ticket.used
        unsettled.remove(ticket)
        events.append("SETTLE:" + str(ticket.used))

    def model(current_context, tools, limits):
        assert current_context is context and tools == ("read",)
        limits.used += 1
        events.append("MODEL")
        if case == "model_fault":
            raise RuntimeError("model fault")
        return NS(is_final=case == "candidate" and bool(context), answer="candidate-only",
                  tool_call="write" if case == "write_rejected" else "read")

    def validate(call):
        events.append("VALIDATE:" + call)
        if call != "read":
            raise PermissionError("read-only simulator rejects writes")
        return call

    def execute(call, limits):
        assert call == "read" and limits in unsettled
        limits.used += 1
        events.append("EXECUTE")
        if case == "tool_fault":
            raise TimeoutError("tool fault")
        return "observed"

    ns = {"max_steps": 3, "budget": NS(reserve_step_or_stop=reserve, settle=settle),
          "context": context, "read_only_tools": ("read",), "model": model,
          "validate_read_only_call": validate, "execute_in_simulator": execute,
          "candidate_answer": lambda answer: {"status": "CANDIDATE", "answer": answer}}
    fn = compile_function(source, "minimal_loop", ns)
    failures = {"budget_stop": BudgetExhausted, "pause": PauseRequested,
                "cancel": CancellationRequested, "write_rejected": PermissionError,
                "tool_fault": TimeoutError, "model_fault": RuntimeError}
    if case in failures:
        with pytest.raises(failures[case]) as caught:
            bounded_call(fn)
        result = {"propagated": type(caught.value).__name__}
    else:
        result = bounded_call(fn)
    assert not unsettled
    assert events.count("RESERVE") == sum(event.startswith("SETTLE:") for event in events)
    if case == "candidate":
        assert result["status"] == "CANDIDATE" and context == ["observed"] and spent == 3 and remaining == 17
    elif case in {"max_steps", "static_budget"}:
        assert result == "STOPPED_INCOMPLETE" and len(context) == 3 and events.count("MODEL") == 3
        assert spent == 6 and remaining == (20 if case == "static_budget" else 14)
    elif case in {"budget_stop", "pause", "cancel"}:
        assert len(context) == 1 and events.count("MODEL") == events.count("EXECUTE") == 1 and spent == 2
    elif case in {"model_fault", "write_rejected"}:
        assert events.count("MODEL") == 1 and "EXECUTE" not in events and spent == 1
    else:
        assert events.count("EXECUTE") == 1 and spent == 2 and not context
    persist_case(evidence, "minimal_loop", case, source, metadata, result, events,
                 spent=spent, remaining=remaining, context=context,
                 limitation="Pause/cancel/exhaustion propagate from host; source only guarantees finally settlement.")


class Signal(str):
    """DSL permits the same tagged result with and without a detail payload."""
    def __call__(self, *detail):
        return {"status": str(self), "detail": list(detail)}


class ChildCancelled(Exception):
    pass


@pytest.mark.parametrize("case", [
    "success", "constrained", "deny", "approval", "unknown_decision", "expired", "parent_cancelled",
    "budget_exhausted", "constraint_rejected", "workspace_fault", "child_timeout",
    "child_cancelled", "verification_fault", "cleanup_unresolved",
])
def test_current_delegate(case, current_sources, policy_schema, evidence):
    source, metadata = current_sources["delegate"]
    events = []
    now = datetime(2026, 9, 19, tzinfo=timezone.utc)
    parent = NS(identity="parent-1", cancelled=case == "parent_cancelled",
                allocatable_budget=3 if case == "budget_exhausted" else 5,
                verification_reserve=NS(remaining=2))
    initial_available = parent.allocatable_budget
    spec = NS(objective="bounded-fixture-task", expected_output_schema="artifact-v1",
              acceptance_checks=["check-v1"], deadline=now + timedelta(seconds=-1 if case == "expired" else 60),
              subtask_id="subtask-1", budget=4, inputs=["input-sha"], context_policy="selected-inputs",
              cancellation_token=NS(cancelled=False))
    state = NS(reserved=0, metered=0, returned=0)
    resources = NS(metered_usage=0, event_refs=["durable-lifecycle-record-fixture"])

    def reserve(amount, capacity):
        events.append("RESERVE")
        assert capacity == parent.allocatable_budget
        if amount > capacity:
            raise BudgetExhausted("child reservation unavailable")
        parent.allocatable_budget -= amount
        state.reserved = amount
        return "lease-1"

    def enforce(decision):
        events.append("ENFORCE")
        if case == "constrained":
            assert decision.constraints == {"resource": "fixture-resource"}
        if case == "constraint_rejected":
            raise PermissionError("constraints not enforceable")

    def workspace(inputs):
        assert inputs == spec.inputs
        events.append("WORKSPACE_REGISTERED")
        if case == "workspace_fault":
            raise TimeoutError("workspace creation uncertain; lifecycle record retained")
        return "isolated-workspace-fixture"

    def await_child(deadline, token):
        events.append("AWAIT_CHILD")
        resources.metered_usage = state.metered = 2
        if case == "child_cancelled":
            token.cancelled = True
            raise ChildCancelled("child stopped by modeled cancellation signal")
        if case == "child_timeout":
            raise TimeoutError("child timeout")
        return "child-artifact"

    def spawn(context, workspace, capability, lease):
        events.append("SPAWN")
        assert (workspace, capability, lease) == ("isolated-workspace-fixture", "bound-capability", "lease-1")
        return NS(await_or_cancel=await_child)

    def verify(artifact, checks, *, budget):
        assert artifact == "exported-artifact" and checks == spec.acceptance_checks
        assert budget is parent.verification_reserve and budget.remaining >= 1
        budget.remaining -= 1
        events.append("VERIFY_WITH_SEPARATE_RESERVE")
        if case == "verification_fault":
            raise TimeoutError("verifier timeout")
        return {"passed": True}

    def close():
        # Contract: try every cleanup stage even when one fails. Unknown resources
        # retain the full reservation; this models bookkeeping, not OS termination.
        closed = True
        for stage in ("REVOKE", "STOP_DESCENDANTS", "SAVE_EVIDENCE", "CLEAN_WORKSPACE", "SETTLE"):
            events.append("CLEANUP:" + stage)
            if case == "cleanup_unresolved" and stage == "STOP_DESCENDANTS":
                closed = False
                events.append("CLEANUP_ERROR:STOP_DESCENDANTS")
        if closed and state.reserved:
            state.returned = state.reserved - state.metered
            parent.allocatable_budget += state.returned
            state.reserved = 0
        return NS(closed=closed, record_ref="lifecycle-record-1")

    resources.reserve = reserve
    resources.issue_bound_authorization = lambda decision: events.append("ISSUE_AUTHORITY") or "bound-capability"
    resources.enforce_constraints_or_fail = enforce
    resources.create_isolated_workspace = workspace
    resources.spawn = spawn
    resources.close_or_quarantine = close

    def open_record(subtask_id):
        assert subtask_id == spec.subtask_id
        events.append("OPEN_RECORD")
        return resources

    kind = {"deny": "DENY", "approval": "REQUIRE_APPROVAL", "unknown_decision": "UNKNOWN",
            "constrained": "CONSTRAINED_ALLOW"}.get(case, "ALLOW")
    policy_packets = []

    def authorize(identity, passed_spec, ttl):
        assert identity == parent.identity and passed_spec is spec and ttl == 60
        events.append("AUTHORIZE:" + kind)
        packet = {"action_id": "delegate:" + spec.subtask_id, "decision": kind, "policy_version": "policy-v1"}
        if kind == "CONSTRAINED_ALLOW":
            packet["constraints"] = {"resource": "fixture-resource"}
        if kind == "REQUIRE_APPROVAL":
            packet["approval_request_id"] = "approval-1"
        errors = [error.message for error in policy_schema[0].iter_errors(packet)]
        # Only the explicitly malformed negative bypasses the schema to exercise
        # the source's own fail-closed branch as an independent second boundary.
        assert bool(errors) == (case == "unknown_decision")
        policy_packets.append({"packet": packet, "schema_errors": errors})
        return NS(**packet)

    ns = {"objective_is_bounded": lambda objective: objective == "bounded-fixture-task",
          "trusted_clock": NS(now=lambda: now), "seconds_until": lambda deadline, current: (deadline-current).total_seconds(),
          "policy": NS(authorize_delegation=authorize), "NOT_STARTED": Signal("NOT_STARTED"),
          "lifecycle": NS(open_record=open_record), "build_context": lambda *args: "context",
          "validate_and_export": lambda artifact, schema: events.append("EXPORT") or "exported-artifact",
          "verify_subtask": verify,
          "SubagentResult": lambda artifact, checks, usage: {"status": "RESULT", "artifact": artifact, "checks": checks, "usage": usage},
          "FAILED_WITH_EVIDENCE": lambda error, refs: {"status": "FAILED_WITH_EVIDENCE", "error": type(error).__name__, "refs": refs},
          "RECONCILIATION_REQUIRED": lambda outcome, ref: {"status": "RECONCILIATION_REQUIRED", "outcome": outcome, "record_ref": ref}}
    result = bounded_call(compile_function(source, "delegate", ns), parent, spec)
    result_status = result["status"] if isinstance(result, dict) else str(result)
    not_started = {"deny", "approval", "unknown_decision", "expired", "parent_cancelled"}
    if case in not_started:
        assert result_status == "NOT_STARTED" and "OPEN_RECORD" not in events and "SPAWN" not in events
        assert parent.allocatable_budget == initial_available and parent.verification_reserve.remaining == 2
    else:
        assert events.index("OPEN_RECORD") < events.index("RESERVE")
        cleanup = [e for e in events if e.startswith("CLEANUP:")]
        assert cleanup == ["CLEANUP:" + s for s in ("REVOKE", "STOP_DESCENDANTS", "SAVE_EVIDENCE", "CLEAN_WORKSPACE", "SETTLE")]
        if case == "cleanup_unresolved":
            assert result_status == "RECONCILIATION_REQUIRED" and state.reserved == 4
            assert parent.allocatable_budget == 1 and state.returned == 0
        else:
            assert state.reserved == 0 and parent.allocatable_budget == initial_available - state.metered
            if case in {"success", "constrained"}:
                assert result_status == "RESULT" and result["checks"]["passed"] and result["usage"] == 2
                assert events.index("EXPORT") < events.index("CLEANUP:CLEAN_WORKSPACE")
            else:
                assert result_status == "FAILED_WITH_EVIDENCE"
        if case in {"budget_exhausted", "constraint_rejected", "workspace_fault"}:
            assert "SPAWN" not in events and state.metered == 0
        if case in {"success", "constrained", "verification_fault", "cleanup_unresolved"}:
            assert parent.verification_reserve.remaining == 1
        else:
            assert parent.verification_reserve.remaining == 2
    persist_case(evidence, "delegate", case, source, metadata, result, events,
                 policy_schema=policy_schema[1], policy_packets=policy_packets,
                 accounting={"allocatable": parent.allocatable_budget, "reserved": state.reserved,
                             "metered": state.metered, "returned": state.returned,
                             "verification_reserve": parent.verification_reserve.remaining})


@pytest.mark.parametrize("case", ["success", "unverified", "expired", "conflict", "merge_fault", "gate_fault", "parent_rejects"])
def test_current_integrate(case, current_sources, evidence):
    source, metadata = current_sources["integrate"]
    events = []
    inputs = [{"artifact": "a", "verified": case != "unverified", "expired": case == "expired"},
              {"artifact": "b", "verified": True, "expired": False}]

    def reject(results):
        events.append("CHECK_INPUTS")
        if any(not row["verified"] or row["expired"] for row in results):
            raise ValueError("unverified or expired result")

    @contextmanager
    def workspace():
        events.append("OPEN_WORKSPACE")
        try:
            yield "clean-workspace"
        finally:
            events.append("CLOSE_WORKSPACE")

    def merge(work, results):
        assert work == "clean-workspace" and results is inputs
        events.append("MERGE_EXPORT")
        if case == "merge_fault":
            raise RuntimeError("merge failure")
        return ("sealed-merged-artifact", "a", "b")

    def completion(candidate):
        assert candidate == ("sealed-merged-artifact", "a", "b")
        assert events[-1] == "CLOSE_WORKSPACE"
        events.append("PARENT_GATE")
        if case == "gate_fault":
            raise RuntimeError("parent verifier failure")
        return "BLOCKED" if case == "parent_rejects" else "CANDIDATE_VERIFIED"

    ns = {"reject_unverified_or_expired": reject,
          "detect_semantic_and_resource_conflicts": lambda results: ["overlap"] if case == "conflict" else [],
          "RESOLUTION_REQUIRED": Signal("RESOLUTION_REQUIRED"), "managed_clean_workspace": workspace,
          "merge_and_export_immutable": merge, "parent_completion_gate": completion}
    fn = compile_function(source, "integrate", ns)
    error = ValueError if case in {"unverified", "expired"} else RuntimeError
    if case in {"unverified", "expired", "merge_fault", "gate_fault"}:
        with pytest.raises(error) as caught:
            bounded_call(fn, NS(), inputs)
        result = {"propagated": type(caught.value).__name__}
    else:
        result = bounded_call(fn, NS(), inputs)
    if case in {"unverified", "expired", "conflict"}:
        assert events == ["CHECK_INPUTS"]
        if case == "conflict":
            assert result["status"] == "RESOLUTION_REQUIRED"
    else:
        assert events.count("OPEN_WORKSPACE") == events.count("CLOSE_WORKSPACE") == 1
        if case == "merge_fault":
            assert "PARENT_GATE" not in events
        else:
            assert events[-1] == "PARENT_GATE"
        if case in {"success", "parent_rejects"}:
            assert result == ("BLOCKED" if case == "parent_rejects" else "CANDIDATE_VERIFIED")
    persist_case(evidence, "integrate", case, source, metadata, result, events)


class HostActionError(Exception):
    pass


class UnknownEffect(Exception):
    pass


class IntegrityAlarm(Exception):
    pass


@dataclass(frozen=True)
class SearchState:
    artifact: str
    environment: str = "environment-v1"
    hypothesis: str = "hypothesis-v1"

    @property
    def key(self):
        return (self.artifact, self.environment, self.hypothesis)


@dataclass(frozen=True)
class Operation:
    """Constructing this value performs no model/tool/verifier work."""
    kind: str
    payload: object


@pytest.mark.parametrize("case", [
    "normal", "empty", "duplicate", "depth_limit", "expansion_limit", "stalled_limit", "static_frontier",
    "budget_before_generate", "budget_mid_execute", "budget_mid_verify", "retained_verified",
    "generate_fault", "execute_fault", "verifier_fault", "integrity_alarm", "integrity_after_verified",
    "unknown_effect", "pause", "cancel",
])
def test_current_frontier_search(case, current_sources, evidence):
    source, metadata = current_sources["frontier_search"]
    events, pending, queues = [], [], []
    capacity = {"budget_before_generate": 0, "budget_mid_execute": 6,
                "budget_mid_verify": 8, "retained_verified": 6}.get(case, 20)
    account = NS(available=capacity, spent=0)
    root, a, b, a2 = (SearchState(name) for name in ("root", "a", "b", "a2"))
    limits = {"max_depth": 1 if case == "depth_limit" else 10,
              "max_expansions": 2 if case == "expansion_limit" else 10,
              "max_stalled": 1 if case == "stalled_limit" else 10, "max_children": 2}
    costs = {"generate": 3, "execute": 2, "verify": 1}

    def candidate(state):
        return NS(state=state, state_key=state.key, name=state.artifact)

    class Frontier:
        def __init__(self, items):
            self.items = list(items)
            queues.append(self)

        def __bool__(self):
            return bool(self.items)

        def pop(self):
            state, depth = self.items.pop()
            events.append("POP:" + state.artifact + ":" + str(depth))
            return state, depth

        def push(self, item):
            self.items.append(item)
            events.append("PUSH:" + item[0].artifact)

    def reserve(kind):
        if account.available < costs[kind]:
            events.append("BUDGET_STOP:" + kind)
            raise BudgetExhausted(kind)
        ticket = NS(kind=kind, bound=costs[kind], used=None)
        account.available -= ticket.bound
        pending.append(ticket)
        events.append("RESERVE:" + kind)
        return ticket

    def settle(ticket, meter):
        assert meter == "ticket-meter-or-conservative-upper-bound" and ticket in pending
        actual = ticket.bound if ticket.used is None else ticket.used
        assert 0 <= actual <= ticket.bound
        account.available += ticket.bound - actual
        account.spent += actual
        pending.remove(ticket)
        events.append("SETTLE:" + ticket.kind + ":" + str(actual))

    def children(state):
        if case == "empty":
            return []
        if case == "expansion_limit":
            return [candidate(SearchState(state.artifact + "+"))]
        if state != root:
            return [candidate(a2)] if case == "normal" and state == a else []
        if case == "duplicate":
            return [candidate(a), candidate(a)]
        if case == "static_frontier":
            return [candidate(root)]
        if case == "depth_limit":
            return [candidate(a)]
        if case in {"retained_verified", "integrity_after_verified"}:
            return [candidate(b), candidate(a)]
        return [candidate(a), candidate(b)]

    def verdict(c):
        good = case in {"normal", "retained_verified", "integrity_after_verified"} and c.name in {"b", "a2"}
        alarm = case == "integrity_alarm" or (case == "integrity_after_verified" and c.name == "a")
        progress = (case in {"duplicate", "depth_limit", "expansion_limit", "stalled_limit", "static_frontier"}
                    or (case in {"normal", "budget_mid_execute", "budget_mid_verify"} and c.name == "a"))
        return NS(integrity_alarm=alarm, all_required_pass=good or alarm, comparable_progress=progress)

    def run_with_limits(operation, ticket):
        assert isinstance(operation, Operation) and operation.kind == ticket.kind and ticket in pending
        if case in {"pause", "cancel"} and operation.kind == "execute":
            ticket.used = 0  # Known not dispatched; reservation can be returned.
            events.append("HOST_STOP:" + case)
            raise HostActionError("paused" if case == "pause" else "cancelled")
        events.append("DISPATCH:" + operation.kind)
        fault_kind = {"generate_fault": "generate", "execute_fault": "execute", "verifier_fault": "verify"}.get(case)
        if operation.kind == fault_kind:
            # Meter unavailable after a dispatched fault: charge the reserved upper bound.
            raise HostActionError(operation.kind + "_fault")
        if case == "unknown_effect" and operation.kind == "execute":
            raise UnknownEffect("execution receipt unknown")
        ticket.used = ticket.bound
        if operation.kind == "generate":
            state, maximum = operation.payload
            events.append("GENERATE:" + state.artifact)
            return children(state)[:maximum]
        if operation.kind == "execute":
            events.append("EXECUTE:" + operation.payload.name)
            return operation.payload
        events.append("VERIFY:" + operation.payload.name)
        return verdict(operation.payload)

    def record(c, result, checked):
        assert result is c
        events.append("RECORD:" + c.name)

    def seal(c, checked):
        assert checked.all_required_pass and not checked.integrity_alarm
        events.append("SEAL:" + c.name)
        return (c.name, c.state.key)  # immutable fixture snapshot; not a production signature

    def stop_reason(frontier, expansions, stalled):
        if not frontier:
            return "frontier_empty"
        if expansions >= limits["max_expansions"]:
            return "max_expansions"
        assert stalled >= limits["max_stalled"]
        return "max_stalled"

    def error_stop(error):
        events.append("HOST_ERROR:" + str(error))
        return str(error)

    def best(verified):
        # Preregistered synthetic preference, independent of candidate-provided score.
        order = {"b": 1, "a2": 2}
        return max(verified, key=lambda sealed: order[sealed[0]])[0]

    ns = {**limits, "baseline_state": root, "queue": Frontier, "set": set,
          "hash": lambda artifact, environment, hypothesis: (artifact, environment, hypothesis),
          "budget": NS(reserve_upper_bound=reserve, settle=settle), "host": NS(run_with_limits=run_with_limits),
          "measured_usage_or_reserved_upper_bound": "ticket-meter-or-conservative-upper-bound",
          "propose": lambda state, maximum: Operation("generate", (state, maximum)),
          "run_in_fresh_branch": lambda c: Operation("execute", c),
          "development_checks": lambda result: Operation("verify", result),
          "record": record, "seal": seal, "stop_reason": stop_reason,
          "BudgetExhausted": BudgetExhausted, "HostActionError": HostActionError,
          "UnknownEffect": UnknownEffect, "IntegrityAlarm": IntegrityAlarm,
          "quarantine_and_reconcile": lambda: events.append("QUARANTINE_AND_RECONCILE"),
          "record_error_and_stop": error_stop,
          "incomplete": lambda reason: {"status": "INCOMPLETE", "reason": reason},
          "best_by_preregistered_rule": best}
    result = bounded_call(compile_function(source, "frontier_search", ns))
    assert not pending and account.available + account.spent == capacity and account.available >= 0
    assert sum(e.startswith("RESERVE:") for e in events) == sum(e.startswith("SETTLE:") for e in events)
    # Every actual operation must follow its corresponding reservation.
    for index, event in enumerate(events):
        if event.startswith("DISPATCH:"):
            assert events[index-1] == "RESERVE:" + event.split(":")[1]
    reason = result["reason"] if isinstance(result, dict) else result[1]
    generated = [event.split(":")[1] for event in events if event.startswith("GENERATE:")]
    if case == "normal":
        assert result == ("a2", "frontier_empty") and generated == ["root", "a"] and account.spent == 15
        assert [e for e in events if e.startswith("SEAL:")] == ["SEAL:b", "SEAL:a2"]
    elif case == "empty":
        assert result["status"] == "INCOMPLETE" and reason == "frontier_empty" and account.spent == 3
        assert "DISPATCH:execute" not in events
    elif case == "duplicate":
        assert generated == ["root", "a"] and events.count("POP:a:1") == 2 and account.spent == 12
    elif case == "depth_limit":
        assert generated == ["root"] and "POP:a:1" in events and account.spent == 6
    elif case == "expansion_limit":
        assert generated == ["root", "root+"] and reason == "max_expansions" and account.spent == 12
    elif case == "stalled_limit":
        assert generated == ["root", "b"] and reason == "max_stalled" and account.spent == 12
        assert queues[0].items[0][0] == a
    elif case == "static_frontier":
        assert generated == ["root"] and "PUSH:root" not in events and reason == "frontier_empty"
    elif case.startswith("budget_") or case == "retained_verified":
        assert reason == "budget_exhausted" and account.spent == capacity
        counts = {kind: events.count("DISPATCH:" + kind) for kind in costs}
        assert counts == ({"generate": 0, "execute": 0, "verify": 0} if case == "budget_before_generate" else
                          {"generate": 1, "execute": 2, "verify": 1} if case == "budget_mid_verify" else
                          {"generate": 1, "execute": 1, "verify": 1})
        if case == "retained_verified":
            assert result == ("b", "budget_exhausted")
        else:
            assert result["status"] == "INCOMPLETE" and not any(e.startswith("SEAL:") for e in events)
    elif case in {"generate_fault", "execute_fault", "verifier_fault"}:
        assert result["status"] == "INCOMPLETE" and reason == ("verify_fault" if case == "verifier_fault" else case)
        assert account.spent == {"generate_fault": 3, "execute_fault": 5, "verifier_fault": 6}[case]
    elif case in {"integrity_alarm", "integrity_after_verified", "unknown_effect"}:
        assert result == {"status": "INCOMPLETE", "reason": "integrity_or_effect_unresolved"}
        assert events.count("QUARANTINE_AND_RECONCILE") == 1
        if case == "integrity_after_verified":
            assert "SEAL:b" in events and account.spent == 9
        else:
            assert not any(e.startswith("SEAL:") for e in events)
            assert account.spent == (5 if case == "unknown_effect" else 6)
    else:
        assert reason == ("paused" if case == "pause" else "cancelled")
        assert result["status"] == "INCOMPLETE" and account.spent == 3
        assert "DISPATCH:execute" not in events and "SETTLE:execute:0" in events
    persist_case(evidence, "frontier", case, source, metadata, result, events,
                 spent=account.spent, available=account.available,
                 deferred_operation_contract="propose/run/check construct descriptors; only run_with_limits dispatches",
                 limitation="Pause/cancel are host errors; no OS pause/checkpoint or durable search recovery modeled.")

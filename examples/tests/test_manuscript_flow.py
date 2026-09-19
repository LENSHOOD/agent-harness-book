from pathlib import Path
import json
from types import SimpleNamespace as NS
import pytest
from jsonschema.exceptions import ValidationError
from src.manuscript import fences, function_source, appendix_loop_source, compile_function, bounded_call
from src.policy import PolicyDecoder

ROOT = Path(__file__).resolve().parents[2]


def current_policy_decoder():
    schemas = [json.loads(block["raw"]) for block in fences(ROOT)
               if block["language"] == "json" and block["file"].endswith("E_machine_readable_contracts.md")]
    messages = [schema for schema in schemas if "PolicyDecision" in schema.get("$defs", {})]
    assert len(messages) == 1
    return PolicyDecoder(messages[0])


def wire_decision(decision, action_id="a1"):
    wire = {"action_id": action_id, "decision": decision, "policy_version": "p1"}
    if decision == "REQUIRE_APPROVAL":
        wire["approval_request_id"] = "approval-1"
    if decision == "CONSTRAINED_ALLOW":
        wire["constraints"] = {"target": "fixture-resource"}
    return wire


@pytest.mark.parametrize("case", [
    "development_repair", "sealed_final_test", "feedback_budget_exhausted", "receiver_denied",
    "not_repairable", "repair_budget_exhausted", "sealed_pass",
])
def test_current_candidate_data_use_prevents_final_test_feedback(case, evidence):
    source, metadata = function_source(fences(ROOT), "run_turn")
    events, model_contexts, verification_history = [], [], []
    state = NS(status="ACTIVE", model_calls=0, repair_remaining=0 if case == "repair_budget_exhausted" else 1,
               feedback_remaining=0 if case == "feedback_budget_exhausted" else 1, feedback=[])
    data_use = "sealed_final_test" if case in {"sealed_final_test", "sealed_pass"} else "development_validation"
    recipient_authorized = case != "receiver_denied"

    def model(context):
        model_contexts.append(list(context))
        state.model_calls += 1
        return NS(requests_actions=False, requests_user_input=False, has_candidate=True)

    def verify(current, proposal):
        passed = case == "sealed_pass" or (case == "development_repair" and state.model_calls == 2)
        feedback_allowed = data_use == "development_validation" and state.feedback_remaining > 0 and recipient_authorized
        row = {"passed": passed, "repairable": case != "not_repairable", "feedback_allowed": feedback_allowed}
        verification_history.append(row)
        return NS(**row, diagnostics="synthetic private diagnostic")

    def feedback(verification):
        # Intentionally no duplicate access guard in this double: if the manuscript
        # misses its data-use check, diagnostics are disclosed and the test fails.
        events.append("DISCLOSE_DIAGNOSTICS")
        state.feedback.append(verification.diagnostics)
        state.repair_remaining -= 1
        state.feedback_remaining -= 1

    ns = {"restore_or_create_state": lambda _: state, "terminal": lambda s: s.status != "ACTIVE",
          "cancellation_requested": lambda s: False, "budget_exhausted": lambda s: False,
          "context_needs_compaction": lambda s: False, "build_context": lambda s: list(s.feedback),
          "call_model_with_budget": model, "persist": lambda proposal: events.append("PROPOSAL"),
          "evaluate_completion_contract": verify,
          "repair_budget_remaining": lambda s: s.repair_remaining > 0,
          "append_structured_feedback_and_charge_attempt": feedback}
    result = bounded_call(compile_function(source, "run_turn", ns), "candidate-turn")
    if case == "development_repair":
        assert result == "CANDIDATE_VERIFIED" and state.model_calls == 2
        assert events.count("DISCLOSE_DIAGNOSTICS") == 1
        assert model_contexts == [[], ["synthetic private diagnostic"]]
        assert state.feedback_remaining == state.repair_remaining == 0
        assert verification_history[0]["feedback_allowed"] is True
    else:
        assert result == ("CANDIDATE_VERIFIED" if case == "sealed_pass" else "BLOCKED_OR_ESCALATED")
        assert state.model_calls == 1 and model_contexts == [[]] and not state.feedback
        assert "DISCLOSE_DIAGNOSTICS" not in events
        if data_use == "sealed_final_test":
            assert verification_history[0]["feedback_allowed"] is False and state.feedback_remaining == 1
    evidence[1](f"literal_candidate_data_use_{case}.json", {
        "source": metadata, "translation": source, "case": case, "data_use": data_use,
        "recipient_authorized": recipient_authorized, "verification_history": verification_history,
        "result": result, "events": events, "model_contexts": model_contexts,
        "feedback_remaining": state.feedback_remaining, "repair_remaining": state.repair_remaining,
        "helper_contract": "trusted verifier computes feedback_allowed; feedback sink deliberately has no redundant guard",
    })


@pytest.mark.parametrize("effect_mode", ["ok", "unknown", "pending", "exception"])
def test_current_run_turn_literal_control_flow(effect_mode, evidence):
    source, metadata = function_source(fences(ROOT), "run_turn")
    outcomes = {}
    for decision, cancel_at, capacity, enforceable in [
        ("DENY", 99, 3, True), ("UNRECOGNIZED", 99, 3, True),
        ("REQUIRE_APPROVAL", 99, 3, True), ("ALLOW", 1, 3, True),
        ("ALLOW", 99, 1, True), ("CONSTRAINED_ALLOW", 99, 3, False),
        ("ALLOW", 99, 3, True),
    ]:
        events = []
        state = NS(status="ACTIVE", calls=0, refreshes=0, spent=0)
        actions = [NS(action_id="first"), NS(action_id="second")]

        def model(_):
            state.calls += 1
            return NS(requests_actions=state.calls == 1, actions=actions,
                      requests_user_input=False, has_candidate=False)

        def refresh(s):
            s.refreshes += 1
            return s

        def execute(action, authorization):
            events.append("EXECUTE:" + action.action_id)
            if effect_mode == "exception":
                raise RuntimeError("injected unexpected host failure")
            return NS(status={"unknown": "UNKNOWN_EFFECT", "pending": "PENDING"}.get(effect_mode, "OK"))

        def settle(reservation):
            state.spent += 1
            events.append("SETTLE")

        namespace = {
            "restore_or_create_state": lambda _: state, "terminal": lambda s: s.status != "ACTIVE",
            "cancellation_requested": lambda s: s.refreshes >= cancel_at,
            "cancel_and_reconcile": lambda s: "CANCELLED",
            "budget_exhausted": lambda s: s.spent >= capacity,
            "suspend_with_checkpoint": lambda s, reason: reason,
            "context_needs_compaction": lambda s: False,
            "build_context": lambda s: {}, "call_model_with_budget": model,
            "persist": lambda proposal: None, "plan_execution": lambda a: a,
            "refresh_state_and_revocations": refresh, "validate_schema": lambda a: None,
            "authorize": lambda a, s: wire_decision(decision, a.action_id),
            "decode_policy_decision": current_policy_decoder(),
            "persist_bound_approval_request": lambda a, d: events.append("PAUSE:" + a.action_id),
            "persist_denied_observation": lambda a, d: events.append("DENY:" + a.action_id),
            "constraints_enforceable": lambda a, d: enforceable,
            "reserve_action_budget_or_none": lambda s, a: NS(action=a),
            "execute_with_effect_ledger": execute, "persist_and_reduce": lambda o: None,
            "settle_actual_cost_and_release_unused": settle,
        }
        executable = compile_function(source, "run_turn", namespace)
        would_execute = decision == "ALLOW" and cancel_at != 1
        if decision == "UNRECOGNIZED":
            with pytest.raises(ValidationError):
                bounded_call(executable, "turn-1")
            assert not events
            outcomes[str((decision, cancel_at, capacity, enforceable))] = {"return": "INVALID_WIRE_REJECTED", "events": events}
            continue
        if effect_mode == "exception" and would_execute:
            with pytest.raises(RuntimeError, match="injected unexpected host failure"):
                bounded_call(executable, "turn-1")
            assert events == ["EXECUTE:first", "SETTLE"] and state.spent == 1
            outcomes[str((decision, cancel_at, capacity, enforceable))] = {"return": "EXCEPTION_PROPAGATED", "events": events}
            continue
        result = bounded_call(executable, "turn-1")
        executed = [event for event in events if event.startswith("EXECUTE:")]
        if decision == "REQUIRE_APPROVAL":
            assert result == "WAITING_FOR_APPROVAL" and events == ["PAUSE:first"]
        elif cancel_at == 1:
            assert result == "CANCELLED" and not executed
        elif effect_mode in {"unknown", "pending"} and would_execute:
            assert result == ("RECONCILE_REQUIRED" if effect_mode == "unknown" else "WAITING_FOR_EFFECT")
            assert executed == ["EXECUTE:first"] and state.spent == 1
        elif capacity == 1:
            assert result == "BUDGET_EXHAUSTED" and executed == ["EXECUTE:first"]
        elif decision in {"DENY", "UNRECOGNIZED"} or not enforceable:
            assert events == ["DENY:first", "DENY:second"] and not executed
        else:
            assert executed == ["EXECUTE:first", "EXECUTE:second"] and result == "TURN_STOPPED"
        outcomes[str((decision, cancel_at, capacity, enforceable))] = {"return": result, "events": events}
    evidence[1]("literal_run_turn_" + effect_mode + ".json", {"source": metadata, "translation": source, "cases": outcomes})


def test_current_appendix_loop_returns_before_observation_after_approval(evidence):
    source, metadata, name = appendix_loop_source(fences(ROOT))
    outcomes = {}
    for decisions in [("REQUIRE_APPROVAL",), ("ALLOW", "REQUIRE_APPROVAL"), ("DENY",)]:
        events, committed, suspended = [], [], []
        attempt = NS(active=True, attempt_id="attempt-1")
        state = NS(cancel_requested=False, artifacts=[])
        cursor = {"i": 0}

        def decide(*args):
            i = cursor["i"]
            cursor["i"] += 1
            return NS(requests_action=True, action=NS(action_id=f"a{i}", decision=decisions[i]))

        def reduce(observation):
            attempt.active = cursor["i"] < len(decisions)

        def commit(action, constraints):
            committed.append(action.action_id)
            return NS(action_id=action.action_id, status="OK")

        namespace = {"attempt": attempt, "budget": NS(exhausted=False),
            "state_store": NS(load=lambda _: state, reduce=reduce),
            "context_compiler": NS(project=lambda *a: {}), "model_facing_tool_views": [],
            "decide_with_reserved_model_budget": decide, "normalize_validate_and_assign_id": lambda a: a,
            "current_authority_and_revocations": lambda: None,
            "policy": NS(evaluate=lambda a, authority: wire_decision(a.decision, a.action_id)),
            "decode_policy_decision": current_policy_decoder(),
            "event_store": NS(append=lambda *args: events.append(args)),
            "suspend_attempt_with_checkpoint": lambda a, d: suspended.append(a.action_id),
            "denied_observation": lambda action_id, reason: NS(action_id=action_id, status="DENIED"),
            "constraints_enforceable": lambda a, d: True, "reserve_action_budget": lambda a: True,
            "commit_effect_safely": commit, "settle_action_budget_from_meter": lambda *args: None}
        fn = compile_function(source, name, namespace)
        result = bounded_call(fn, *([attempt] if name == "run_attempt" else []))
        observations = [e[0] for e in events if len(e) == 1]
        if "REQUIRE_APPROVAL" in decisions:
            assert result == "WAITING_FOR_APPROVAL"
            assert len(observations) == len(decisions) - 1
            assert suspended == [f"a{len(decisions)-1}"]
        else:
            assert len(observations) == 1 and observations[0].status == "DENIED" and not committed
        outcomes[str(decisions)] = {"result": result, "observations": [o.__dict__ for o in observations], "committed": committed}
    evidence[1]("literal_appendix_loop.json", {"source": metadata, "translation": source, "cases": outcomes})


def test_current_recover_terminal_cancelled_does_not_resume(evidence):
    source, metadata = function_source(fences(ROOT), "recover")
    events = []
    namespace = {"coordinator": NS(acquire_single_owner=lambda _: NS(), release=lambda _: events.append("RELEASE")),
                 "state_store": NS(load=lambda _: NS(is_terminal=True, status="CANCELLED")),
                 "resume_from_reconciled_state": lambda *args: events.append("UNSAFE_RESUME")}
    assert bounded_call(compile_function(source, "recover", namespace), "cancelled-task") == "CANCELLED"
    assert events == ["RELEASE"]
    evidence[1]("literal_recover.json", {"source": metadata, "translation": source, "events": events})


@pytest.mark.parametrize("status,lookup,lose_response", [
    ("INTENT_RECORDED", "absent", False), ("INTENT_RECORDED", "absent", True),
    ("UNKNOWN_EFFECT", "stale", False), ("EXECUTING", "stale", False),
    ("UNKNOWN_EFFECT", "committed", False), ("INTENT_RECORDED", "unavailable", False),
])
def test_current_commit_effect_literal_control_flow(status, lookup, lose_response, evidence):
    source, metadata = function_source(fences(ROOT), "commit_effect_safely")
    events = []
    effect = NS(id="e1", is_final=False, status=status)
    action = NS(action_id="a1", attempt_id="attempt-1", tenant="untrusted-ignored", resource="target", idempotency_key="key")

    def persist(kind):
        def fn(*args):
            events.append(kind)
            return NS(status=kind)
        return fn

    def execute(*args):
        events.append("EXECUTE")
        if lose_response:
            raise TimeoutError("receipt lost")
        return NS(is_definitive=True)

    def scoped_key(tenant, resource, key):
        assert (tenant, resource, key) == ("trusted-tenant", "target", "key")
        return "bound-key"

    ns = {"trusted_tenant_for_attempt": lambda attempt_id: "trusted-tenant" if attempt_id == "attempt-1" else None,
          "scoped_key": scoped_key, "hash_normalized_operation": lambda *a: "bound-args",
          "durable_store": NS(bind_intent_once=lambda *a: effect, load=lambda _: effect,
                              mark_executing_if_owned=lambda *a: events.append("MARK_EXECUTING")),
          "coordinator": NS(try_claim_effect=lambda _: NS(fence=1), release=lambda _: events.append("RELEASE")),
          "target_system": NS(lookup_or_unknown=lambda _: NS(is_unavailable=lookup == "unavailable",
                             is_committed_with=lambda h: lookup == "committed" and h == "bound-args"),
                              execute_idempotently=execute),
          "Observation": NS, "persist_reconciled_outcome": persist("COMMITTED"),
          "persist_unknown": persist("UNKNOWN_EFFECT"), "persist_final_outcome": persist("COMMITTED"),
          "persist_denied_outcome": persist("DENIED"), "still_authorized_and_active": lambda *a: True,
          "ExecutionError": TimeoutError, "diagnostic": str}
    result = bounded_call(compile_function(source, "commit_effect_safely", ns), action, {})
    if status in {"UNKNOWN_EFFECT", "EXECUTING"} or lookup == "unavailable":
        assert "EXECUTE" not in events
    if lookup == "committed":
        assert result.status == "COMMITTED"
    elif lookup == "unavailable":
        assert result.status == "PENDING"
    elif lose_response or status in {"UNKNOWN_EFFECT", "EXECUTING"}:
        assert result.status == "UNKNOWN_EFFECT"
    else:
        assert result.status == "COMMITTED"
    assert events[-1] == "RELEASE"
    evidence[1](f"literal_commit_{status}_{lookup}_{lose_response}.json",
                {"source": metadata, "translation": source, "events": events, "status": result.status})


@pytest.mark.parametrize("decision,external,effect_status,post_pass,expected", [
    ("DENY", True, "COMMITTED", True, "BLOCKED"),
    ("UNRECOGNIZED", True, "COMMITTED", True, "INVALID_WIRE_REJECTED"),
    ("REQUIRE_APPROVAL", True, "COMMITTED", True, "AWAITING_APPROVAL"),
    ("ALLOW", False, "COMMITTED", True, "VERIFIED_COMPLETE"),
    ("ALLOW", True, "UNKNOWN_EFFECT", True, "RECONCILING"),
    ("ALLOW", True, "PENDING", True, "RECONCILING"),
    ("ALLOW", True, "COMMITTED", False, "COMMITTED_BUT_UNVERIFIED"),
    ("ALLOW", True, "COMMITTED", True, "VERIFIED_COMPLETE"),
])
def test_current_completion_literal_control_flow(decision, external, effect_status, post_pass, expected, evidence):
    source, metadata = function_source(fences(ROOT), "attempt_completion")
    events = []

    class CheckResults:
        feedback_allowed = True
        def __init__(self): self.rows = []
        def __iadd__(self, rows):
            self.rows += rows
            return self
        def has_integrity_violation(self): return False
        def has_ambiguous_or_flaky_signal(self): return False
        def mandatory_failed(self): return not self.rows or not all(self.rows)

    contract = NS(pre_commit_checks=[NS(version="verifier-v1", environment_digest="env-sha", validation_input_ref="validation-set")],
                  requires_external_commit=external, post_commit_checks=["health"])

    def verifier_run(**kwargs):
        assert kwargs["clean_environment"] == "env-sha" and kwargs["validation_inputs"] == "validation-set"
        events.append("PRE_COMMIT_CHECK")
        return [True]

    def commit(snapshot, authorization):
        events.append("COMMIT")
        return NS(status=effect_status, is_confirmed=effect_status == "COMMITTED")

    ns = {"load_pinned_contract": lambda _: contract, "seal_candidate": lambda c: NS(hash="candidate-sha"),
          "CheckResults": CheckResults, "trusted_registry": NS(resolve=lambda _: NS(run=verifier_run)),
          "build_evidence_package": lambda *a: NS(),
          "persist_delivery_and_evidence": lambda *a: events.append("PERSIST_LOCAL_DELIVERY"),
          "policy": NS(evaluate_commit=lambda p: wire_decision(decision)),
          "decode_policy_decision": current_policy_decoder(),
          "persist_approval_bound_to_candidate": lambda p, h: events.append("APPROVAL:" + h),
          "constraints_enforceable": lambda *a: True,
          "commit_with_live_authority_and_effect_ledger": commit,
          "verify_target_state": lambda checks, effect: NS(passed=post_pass),
          "persist_post_commit_evidence": lambda *a: events.append("POST_COMMIT_EVIDENCE")}
    fn = compile_function(source, "attempt_completion", ns)
    if decision == "UNRECOGNIZED":
        with pytest.raises(ValidationError):
            bounded_call(fn, NS(contract_version="c1"), "candidate")
        result = "INVALID_WIRE_REJECTED"
    else:
        result = bounded_call(fn, NS(contract_version="c1"), "candidate")
    assert result == expected and events[0] == "PRE_COMMIT_CHECK"
    if decision != "ALLOW" or not external:
        assert "COMMIT" not in events
    if external and decision == "ALLOW" and effect_status == "COMMITTED":
        assert "POST_COMMIT_EVIDENCE" in events
    evidence[1](f"literal_completion_{decision}_{external}_{effect_status}_{post_pass}.json",
                {"source": metadata, "translation": source, "events": events, "result": result})


@pytest.mark.parametrize("case", ["development_repair", "sealed_final_test", "feedback_budget_exhausted",
                                  "receiver_denied", "repair_budget_exhausted", "not_repairable"])
def test_current_appendix_candidate_feedback_gate(case, evidence):
    source, metadata, name = appendix_loop_source(fences(ROOT))
    events, feedback, contexts = [], [], []
    state = NS(cancel_requested=False, artifacts=[])
    attempt = NS(active=True, attempt_id="attempt-1")
    meter = NS(calls=0, consume_calls=0, repair_remaining=0 if case == "repair_budget_exhausted" else 1)
    allowed = case not in {"sealed_final_test", "feedback_budget_exhausted", "receiver_denied"}

    def decide(context, tools):
        contexts.append(list(context))
        meter.calls += 1
        return NS(requests_action=False, requests_user_input=False, has_candidate=True, output="candidate")

    def verify(candidate, contract):
        return NS(status="PASS" if meter.calls > 1 else "FAIL", feedback_allowed=allowed,
                  repairable=case != "not_repairable", diagnostics="fixture private diagnostic")

    def consume():
        meter.consume_calls += 1
        if meter.repair_remaining == 0:
            return False
        meter.repair_remaining -= 1
        return True

    def diagnostics(result):
        events.append("DISCLOSE_DIAGNOSTICS")
        return result.diagnostics  # No duplicate guard: the source must block access.

    ns = {"attempt": attempt, "task": NS(contract_version="v1"),
          "state_store": NS(load=lambda _: state, reduce=feedback.append),
          "budget": NS(exhausted=False, consume_repair_attempt=consume),
          "context_compiler": NS(project=lambda *a: list(feedback)), "model_facing_tool_views": [],
          "decide_with_reserved_model_budget": decide, "seal": lambda *a: "sealed-candidate",
          "completion_gate": NS(verify=verify), "minimal_diagnostics": diagnostics}
    result = bounded_call(compile_function(source, name, ns), *([attempt] if name == "run_attempt" else []))
    if case == "development_repair":
        assert result == "CANDIDATE_VERIFIED" and meter.calls == 2 and meter.consume_calls == 1
        assert events == ["DISCLOSE_DIAGNOSTICS"] and contexts == [[], ["fixture private diagnostic"]]
    else:
        assert result == "NEEDS_ESCALATION" and meter.calls == 1 and not feedback and not events
        assert meter.consume_calls == (1 if case == "repair_budget_exhausted" else 0)
    evidence[1](f"literal_appendix_feedback_{case}.json", {"source": metadata, "translation": source,
                "result": result, "events": events, "contexts": contexts, "meter": meter.__dict__})


@pytest.mark.parametrize("case", ["development_repair", "sealed_final_test", "feedback_budget_exhausted",
                                  "receiver_denied", "repair_budget_exhausted"])
def test_current_completion_failed_final_test_has_no_diagnostics(case, evidence):
    source, metadata = function_source(fences(ROOT), "attempt_completion")
    events = []
    allowed = case not in {"sealed_final_test", "feedback_budget_exhausted", "receiver_denied"}

    class CheckResults:
        feedback_allowed = allowed

        def __init__(self): self.rows = []
        def __iadd__(self, rows):
            self.rows.extend(rows)
            return self
        def has_integrity_violation(self): return False
        def has_ambiguous_or_flaky_signal(self): return False
        def mandatory_failed(self): return self.rows == [False]
        def minimal_diagnostics(self):
            events.append("DISCLOSE_DIAGNOSTICS")
            return {"detail": "synthetic private diagnostic"}

    contract = NS(pre_commit_checks=[NS(version="v1", environment_digest="env", validation_input_ref="frozen-input")])
    ns = {"load_pinned_contract": lambda _: contract, "seal_candidate": lambda _: "sealed-candidate",
          "CheckResults": CheckResults, "trusted_registry": NS(resolve=lambda _: NS(run=lambda **kw: [False])),
          "repair_budget_remaining": lambda run: case != "repair_budget_exhausted",
          "REPAIRING": lambda diagnostics: {"status": "REPAIRING", "diagnostics": diagnostics}}
    result = bounded_call(compile_function(source, "attempt_completion", ns), NS(contract_version="v1"), "candidate")
    if case == "development_repair":
        assert result["status"] == "REPAIRING" and events == ["DISCLOSE_DIAGNOSTICS"]
    else:
        assert result == "BLOCKED_OR_FAILED" and not events
    evidence[1](f"literal_completion_feedback_{case}.json", {"source": metadata, "translation": source,
                "result": result, "events": events, "feedback_allowed": allowed})


@pytest.mark.parametrize("wire", [wire_decision("DENY"), wire_decision("ALLOW"),
                                  {**wire_decision("DENY"), "reason_code": "SCOPE_DENIED"},
                                  wire_decision("CONSTRAINED_ALLOW")])
def test_F05_real_wire_decoding_drives_appendix_without_convenience_fields(wire, evidence):
    source, metadata, name = appendix_loop_source(fences(ROOT))
    attempt = NS(attempt_id="attempt-1", active=True)
    events, observations = [], []

    def reduce(observation):
        observations.append(observation)
        attempt.active = False

    def commit(action, constraints):
        assert constraints == wire.get("constraints", {})
        events.append("EXECUTE")
        return NS(status="OK", action_id="a1")

    ns = {"attempt": attempt, "state_store": NS(load=lambda _: NS(cancel_requested=False), reduce=reduce),
          "budget": NS(exhausted=False), "context_compiler": NS(project=lambda *a: {}), "model_facing_tool_views": [],
          "decide_with_reserved_model_budget": lambda *a: NS(requests_action=True, action=NS(action_id="a1")),
          "normalize_validate_and_assign_id": lambda a: a,
          "policy": NS(evaluate=lambda *a: dict(wire)), "decode_policy_decision": current_policy_decoder(),
          "current_authority_and_revocations": lambda: None, "event_store": NS(append=lambda *a: None),
          "denied_observation": lambda action_id, reason: NS(action_id=action_id, status="DENIED", reason_code=reason),
          "constraints_enforceable": lambda a, d: True, "reserve_action_budget": lambda a: True,
          "commit_effect_safely": commit, "settle_action_budget_from_meter": lambda a: None}
    bounded_call(compile_function(source, name, ns), *([attempt] if name == "run_attempt" else []))
    assert len(observations) == 1
    if wire["decision"] == "DENY":
        assert not events and observations[0].reason_code == wire.get("reason_code", "POLICY_NO_REASON")
    else:
        assert events == ["EXECUTE"]
    assert "reason" not in wire and ("constraints" not in wire or wire["constraints"])
    suffix = wire["decision"] + ("_reason" if "reason_code" in wire else "_defaults")
    evidence[1](f"review_F05_wire_{suffix}.json", {"source": metadata, "translation": source,
                "wire": wire, "events": events, "observations": [o.__dict__ for o in observations]})


@pytest.mark.parametrize("wire", [
    {**wire_decision("ALLOW"), "reason": "not a schema field"},
    {**wire_decision("ALLOW"), "constraints": {}},
    {"action_id": "a1", "decision": "CONSTRAINED_ALLOW", "policy_version": "p1"},
    {"action_id": "a1", "decision": "REQUIRE_APPROVAL", "policy_version": "p1"},
    wire_decision("UNKNOWN"),
])
def test_F05_invalid_wire_rejected_before_internal_defaults(wire):
    with pytest.raises(ValidationError):
        current_policy_decoder()(wire)


@pytest.mark.parametrize("upper", ["run_turn", "appendix_loop"])
@pytest.mark.parametrize("pending_cause", ["lease_busy", "lookup_unavailable"])
def test_F02_actual_low_level_pending_stops_upper_sequence(upper, pending_cause, evidence):
    blocks = fences(ROOT)
    low_source, low_metadata = function_source(blocks, "commit_effect_safely")
    events, pending_actions, stored_actions = [], [], {}
    effects = {}

    def bind(key, args_hash):
        effects.setdefault(key, NS(id=key, status="INTENT_RECORDED", is_final=False))
        return effects[key]

    def execute(key, *args):
        events.append("TARGET_EXECUTE:" + key)
        return NS(is_definitive=True)

    low_ns = {"trusted_tenant_for_attempt": lambda _: "tenant", "scoped_key": lambda tenant, resource, key: key,
              "hash_normalized_operation": lambda *a: "args-hash",
              "durable_store": NS(bind_intent_once=bind, load=lambda key: effects[key],
                                  mark_executing_if_owned=lambda *a: None),
              "coordinator": NS(try_claim_effect=lambda key: None if key == "first" and pending_cause == "lease_busy" else NS(fence=1),
                                release=lambda lease: events.append("RELEASE_LEASE")),
              "target_system": NS(lookup_or_unknown=lambda key: NS(is_committed_with=lambda h: False,
                                    is_unavailable=key == "first" and pending_cause == "lookup_unavailable"),
                                   execute_idempotently=execute),
              "Observation": NS, "still_authorized_and_active": lambda *a: True,
              "persist_final_outcome": lambda action, *a: NS(action_id=action.action_id, status="OK")}
    low = compile_function(low_source, "commit_effect_safely", low_ns)
    actions = [NS(action_id=key, attempt_id="attempt-1", resource="target", idempotency_key=key)
               for key in ("first", "second")]
    state = NS(status="ACTIVE", cancel_requested=False)
    count = NS(model=0)

    def persist_proposal(proposal):
        if proposal.requests_actions:
            for action in proposal.actions:
                stored_actions[action.action_id] = dict(action.__dict__)

    def append_event(*args):
        if len(args) == 2:
            action, decision = args
            stored_actions[action.action_id] = dict(action.__dict__)

    def persist_observation(observation):
        events.append("OBSERVATION:" + observation.action_id + ":" + observation.status)
        if observation.status == "PENDING":
            pending_actions.append(observation.action_id)

    if upper == "run_turn":
        source, metadata = function_source(blocks, "run_turn")
        name, args = "run_turn", ("turn-1",)

        def model(context):
            count.model += 1
            return NS(requests_actions=count.model == 1, actions=actions,
                      requests_user_input=False, has_candidate=False)

        ns = {"restore_or_create_state": lambda _: state, "terminal": lambda s: False,
              "cancellation_requested": lambda s: False, "budget_exhausted": lambda s: False,
              "context_needs_compaction": lambda s: False, "build_context": lambda s: {},
              "call_model_with_budget": model, "persist": persist_proposal,
              "plan_execution": lambda a: a, "refresh_state_and_revocations": lambda s: s,
              "validate_schema": lambda a: None, "authorize": lambda a, s: wire_decision("ALLOW", a.action_id),
              "decode_policy_decision": current_policy_decoder(), "constraints_enforceable": lambda *a: True,
              "reserve_action_budget_or_none": lambda *a: "reservation",
              "execute_with_effect_ledger": lambda action, decision: low(action, decision.constraints),
              "persist_and_reduce": persist_observation, "settle_actual_cost_and_release_unused": lambda _: None}
    else:
        source, metadata, name = appendix_loop_source(blocks)
        attempt = NS(attempt_id="attempt-1", active=True)
        args = (attempt,) if name == "run_attempt" else ()

        def model(*args):
            action = actions[count.model]
            count.model += 1
            return NS(requests_action=True, action=action)

        def reduce(observation):
            persist_observation(observation)
            attempt.active = count.model < len(actions)

        ns = {"attempt": attempt, "state_store": NS(load=lambda _: state, reduce=reduce),
              "budget": NS(exhausted=False), "context_compiler": NS(project=lambda *a: {}), "model_facing_tool_views": [],
              "decide_with_reserved_model_budget": model, "normalize_validate_and_assign_id": lambda a: a,
              "policy": NS(evaluate=lambda a, authority: wire_decision("ALLOW", a.action_id)),
              "decode_policy_decision": current_policy_decoder(), "current_authority_and_revocations": lambda: None,
              "event_store": NS(append=append_event), "constraints_enforceable": lambda *a: True,
              "reserve_action_budget": lambda a: True, "settle_action_budget_from_meter": lambda a: None,
              "commit_effect_safely": low}
    result = bounded_call(compile_function(source, name, ns), *args)
    assert result == "WAITING_FOR_EFFECT" and count.model == 1
    assert pending_actions == ["first"] and not any(e.startswith("TARGET_EXECUTE:") for e in events)
    assert stored_actions["first"] == dict(actions[0].__dict__)
    assert list(effects) == ["first"]  # Second intent was never even created.
    evidence[1](f"review_F02_connected_{upper}_{pending_cause}.json", {
        "upper_source": metadata, "upper_translation": source, "lower_source": low_metadata,
        "lower_translation": low_source, "events": events, "pending_actions": pending_actions,
        "stored_actions": stored_actions, "result": result})

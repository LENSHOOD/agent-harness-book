"""Deterministic public-API regressions for the independent F01/F03/F04/F06 report.

Nested callbacks force old/late responses without sleeps or hand-edited SQL state.
"""
from dataclasses import replace
import pytest
from src.runtime import Action, Runtime, Target

ALLOW = lambda action, approved: "ALLOW"
APPROVAL = lambda action, approved: "ALLOW" if approved else "REQUIRE_APPROVAL"


@pytest.fixture
def model(tmp_path):
    target = Target(tmp_path / "review-target.sqlite")
    return Runtime(tmp_path / "review-runtime.sqlite", target), target, Action("a1", "key1", "account/one", {"amount": 7})


@pytest.mark.parametrize("restart", [False, True])
def test_F01_unknown_blocks_new_key_and_preserves_budget(model, restart, evidence):
    runtime, target, action = model
    assert runtime.submit(action, ALLOW, lose_receipt=True) == "UNKNOWN"
    if restart:
        runtime = Runtime(runtime.path, target)
    before = runtime.snapshot()
    second = replace(action, action_id="a2", key="key2", target="account/two")
    assert runtime.submit(second, ALLOW) == "NEEDS_RECONCILIATION"
    after = runtime.snapshot()
    assert target.count() == 1 and after["task"]["spent"] == before["task"]["spent"] == 1
    assert after["task"]["state"] == "NEEDS_RECONCILIATION" and len(after["ledger"]) == 1
    assert runtime.reconcile(action) == "COMMITTED"
    assert runtime.submit(second, ALLOW) == "COMMITTED" and target.count() == 2
    evidence[1](f"review_F01_new_key_{restart}.json", {"paused": after, "after_reconciliation": runtime.snapshot()})


def test_F03_late_stale_reconciliation_cannot_undo_confirmation_and_completion(model, evidence):
    runtime, target, action = model
    runtime.submit(action, ALLOW, lose_receipt=True)
    lookup = target.lookup
    schedule = []

    def interleaved_lookup(current, mode="fresh"):
        old = lookup(current, "stale" if mode == "slow" else mode)
        if mode == "slow":
            schedule.append("SLOW_READ_STALE")
            assert runtime.reconcile(current) == "COMMITTED"
            schedule.append("FAST_CONFIRMED")
            assert runtime.complete({"health": True}) == "COMPLETE"
            schedule.append("COMPLETED")
        return old

    target.lookup = interleaved_lookup
    assert runtime.reconcile(action, "slow") == "COMMITTED"
    final = runtime.snapshot()
    assert final["task"]["state"] == "COMPLETE" and final["ledger"][0]["status"] == "COMMITTED"
    assert target.count() == 1
    evidence[1]("review_F03_stale_reconciliation.json", {"schedule": schedule, "final": final})


def test_F03_late_submit_timeout_cannot_undo_reconciled_effect(model):
    runtime, target, action = model
    execute = target.execute

    def committed_then_reconciled(current, lose_receipt=False):
        execute(current)
        assert runtime.reconcile(current) == "COMMITTED"
        assert runtime.complete({"health": True}) == "COMPLETE"
        raise TimeoutError("late missing receipt after authoritative confirmation")

    target.execute = committed_then_reconciled
    assert runtime.submit(action, ALLOW) == "COMMITTED"
    assert runtime.snapshot()["ledger"][0]["status"] == "COMMITTED"
    assert runtime.snapshot()["task"]["state"] == "COMPLETE" and target.count() == 1


@pytest.mark.parametrize("approved", [False, True])
def test_F04_approval_never_moves_to_new_action_identity(model, approved, evidence):
    runtime, target, action = model
    assert runtime.submit(action, APPROVAL) == "AWAITING_APPROVAL"
    if approved:
        runtime.approve(action.key, action.binding)
    calls = []

    def current_policy(a, flag):
        calls.append((a.action_id, flag))
        return "ALLOW"

    with pytest.raises(ValueError, match="IDEMPOTENCY_BINDING_CONFLICT"):
        runtime.submit(replace(action, action_id="new-action"), current_policy)
    assert not calls and target.count() == 0 and runtime.snapshot()["ledger"][0]["action_id"] == "a1"
    if approved:
        assert runtime.submit(action, current_policy) == "COMMITTED" and calls == [("a1", True)]
    evidence[1](f"review_F04_identity_{approved}.json", runtime.snapshot())


def test_F06_denied_proposal_does_not_poison_satisfied_contract(model, evidence):
    runtime, target, action = model
    assert runtime.submit(action, lambda *_: "DENY") == "DENIED"
    assert runtime.complete({"health": True}) == "VERIFICATION_FAILED"  # No accomplished effect yet.
    alternate = replace(action, action_id="a2", key="key2")
    assert runtime.submit(alternate, ALLOW) == "COMMITTED"
    assert runtime.complete({"health": True, "policy_invariant": False}) == "VERIFICATION_FAILED"
    assert runtime.complete({"contract_final_result": True, "health": True}) == "COMPLETE"
    final = runtime.snapshot()
    assert [r["status"] for r in final["ledger"]] == ["DENIED", "COMMITTED"] and target.count() == 1
    evidence[1]("review_F06_denial_history.json", final)


@pytest.mark.parametrize("unresolved", ["approval", "unknown", "budget"])
def test_F06_non_denial_unresolved_rows_still_block_completion(model, unresolved):
    runtime, target, action = model
    assert runtime.submit(action, ALLOW) == "COMMITTED"
    second = replace(action, action_id="a2", key="key2", cost=20 if unresolved == "budget" else 1)
    policy = APPROVAL if unresolved == "approval" else ALLOW
    runtime.submit(second, policy, lose_receipt=unresolved == "unknown")
    assert runtime.complete({"health": True}) != "COMPLETE"
    assert len(runtime.snapshot()["ledger"]) == 2


def test_F01_sequential_pending_blocks_new_action_before_dispatch(model):
    runtime, target, first = model
    second = replace(first, action_id="a2", key="key2", target="account/two")
    execute = target.execute

    def nested_submit(action, lose_receipt=False):
        assert runtime.submit(second, ALLOW) == "PENDING"
        assert runtime.snapshot()["task"]["state"] == "WAITING_FOR_EFFECT"
        assert runtime.snapshot()["task"]["spent"] == 1
        return execute(action)

    target.execute = nested_submit
    assert runtime.submit(first, ALLOW) == "COMMITTED" and target.count() == 1
    assert len(runtime.snapshot()["ledger"]) == 1


@pytest.mark.parametrize("outer_loses_receipt", [False, True])
def test_F01_global_ledger_aggregation_survives_other_inflight_result(model, outer_loses_receipt, evidence):
    runtime, target, first = model
    second = replace(first, action_id="a2", key="key2", target="account/two")
    third = replace(first, action_id="a3", key="key3", target="account/three")
    execute = target.execute

    def nested_completion(action, lose_receipt=False):
        receipt = execute(action)
        if action.key == first.key:
            assert runtime.submit(second, ALLOW, lose_receipt=not outer_loses_receipt,
                                  independent=True) == ("COMMITTED" if outer_loses_receipt else "UNKNOWN")
            if not outer_loses_receipt:
                assert runtime.submit(third, ALLOW, independent=True) == "NEEDS_RECONCILIATION"
                assert runtime.snapshot()["task"]["state"] == "NEEDS_RECONCILIATION"
        if lose_receipt:
            raise TimeoutError("selected receipt lost")
        return receipt

    target.execute = nested_completion
    assert runtime.submit(first, ALLOW, lose_receipt=outer_loses_receipt) == ("UNKNOWN" if outer_loses_receipt else "COMMITTED")
    final = runtime.snapshot()
    assert {r["status"] for r in final["ledger"]} == {"UNKNOWN", "COMMITTED"}
    assert final["task"]["state"] == "NEEDS_RECONCILIATION" and final["task"]["spent"] == 2
    assert runtime.complete({"health": True}) == "NEEDS_RECONCILIATION" and target.count() == 2
    evidence[1](f"review_F01_aggregate_{outer_loses_receipt}.json", final)

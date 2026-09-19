from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import threading
import pytest
from src.runtime import Action, Runtime, Target, transaction

ALLOW = lambda action, approved: "ALLOW"
APPROVAL = lambda action, approved: "ALLOW" if approved else "REQUIRE_APPROVAL"
DENY = lambda action, approved: "DENY"


@pytest.fixture
def model(tmp_path):
    target = Target(tmp_path / "target.sqlite")
    runtime = Runtime(tmp_path / "runtime.sqlite", target)
    return runtime, target, Action("a1", "key1", "account/one", {"amount": 7})


def test_deny_never_commits(model):
    runtime, target, action = model
    assert runtime.submit(action, DENY) == "DENIED"
    assert target.count() == 0
    assert runtime.snapshot()["task"]["spent"] == 0


def test_approval_pauses_persistently_and_stops_batch(model):
    runtime, target, action = model
    assert runtime.batch([action, replace(action, action_id="a2", key="key2")], APPROVAL) == ["AWAITING_APPROVAL"]
    runtime = Runtime(runtime.path, target)  # Restart with same durable store.
    assert runtime.recover() == "AWAITING_APPROVAL"
    assert runtime.submit(action, ALLOW) == "AWAITING_APPROVAL"  # Cannot silently bypass missing approval.
    assert runtime.submit(replace(action, action_id="a3", key="key3"), ALLOW) == "AWAITING_APPROVAL"
    assert len(runtime.snapshot()["ledger"]) == 1 and target.count() == 0
    assert runtime.approve(action.key, action.binding) == "READY_FOR_REAUTHORIZATION"
    runtime = Runtime(runtime.path, target)
    assert runtime.submit(action, APPROVAL) == "COMMITTED"
    assert target.count() == 1
    assert [e["detail"] for e in runtime.snapshot()["events"] if e["kind"] == "AUTHORIZE"] == ["REQUIRE_APPROVAL", "ALLOW"]


def test_approval_is_reauthorized_under_current_policy(model):
    runtime, target, action = model
    assert runtime.submit(action, APPROVAL) == "AWAITING_APPROVAL"
    runtime.approve(action.key, action.binding)
    assert runtime.submit(action, DENY) == "DENIED"
    assert target.count() == 0


def test_approval_requires_the_exact_argument_binding(model):
    runtime, target, action = model
    runtime.submit(action, APPROVAL)
    altered = replace(action, args={"amount": 700})
    with pytest.raises(ValueError, match="APPROVAL_BINDING_CONFLICT"):
        runtime.approve(action.key, altered.binding)
    with pytest.raises(ValueError, match="IDEMPOTENCY_BINDING_CONFLICT"):
        runtime.submit(altered, ALLOW)
    assert target.count() == 0


@pytest.mark.parametrize("changed", [
    {"args": {"amount": 700}}, {"target": "account/two"}, {"tenant": "another-tenant"},
    {"cost": 2}, {"key": "another-key"}, {"action_id": "another-action"},
])
def test_runtime_key_and_action_identity_are_bound(model, changed):
    runtime, target, action = model
    assert runtime.submit(action, ALLOW) == "COMMITTED"
    with pytest.raises(ValueError, match="IDEMPOTENCY_BINDING_CONFLICT"):
        runtime.submit(replace(action, **changed), ALLOW)
    assert target.count() == 1


def test_target_owns_atomic_uniqueness_even_with_two_control_planes(model, tmp_path):
    runtime, target, action = model
    other = Runtime(tmp_path / "independent-control.sqlite", target)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda rt: rt.submit(action, ALLOW), [runtime, other]))
    assert results == ["COMMITTED", "COMMITTED"] and target.count() == 1
    with pytest.raises(ValueError, match="IDEMPOTENCY_BINDING_CONFLICT"):
        target.execute(replace(action, args={"amount": 1000}))


def test_receipt_loss_records_unknown_then_authoritative_reconciliation(model, evidence):
    runtime, target, action = model
    assert runtime.submit(action, ALLOW, lose_receipt=True) == "UNKNOWN"
    before = runtime.snapshot()
    assert before["ledger"][0]["status"] == "UNKNOWN" and target.count() == 1
    runtime = Runtime(runtime.path, target)
    assert runtime.recover() == "NEEDS_RECONCILIATION"
    assert runtime.submit(action, ALLOW) == "UNKNOWN"
    assert runtime.reconcile(action) == "COMMITTED"
    assert target.count() == 1
    assert runtime.complete({"post_commit_health": False}) == "VERIFICATION_FAILED"
    assert runtime.complete({"post_commit_health": True}) == "COMPLETE"
    evidence[1]("runtime_receipt_loss.json", {"before": before, "after": runtime.snapshot(), "target_effect_count": target.count()})


@pytest.mark.parametrize("mode", ["stale", "none", "unavailable"])
def test_stale_or_missing_reconciliation_evidence_never_replays(model, mode):
    runtime, target, action = model
    runtime.submit(action, ALLOW, lose_receipt=True)
    assert runtime.reconcile(action, mode) == "UNKNOWN"
    assert runtime.submit(action, ALLOW) == "UNKNOWN"
    assert target.count() == 1 and runtime.snapshot()["task"]["spent"] == 1


def test_absence_after_crash_does_not_automatically_replay(model):
    runtime, target, action = model
    with transaction(runtime.path) as db:
        db.execute("INSERT INTO ledger(action_id,key,binding,payload,status,cost) VALUES (?,?,?,?,?,?)",
                   (action.action_id, action.key, action.binding, "{}", "EXECUTING", 1))
    assert runtime.recover() == "NEEDS_RECONCILIATION"
    assert runtime.reconcile(action, "fresh") == "UNKNOWN"
    assert runtime.submit(action, ALLOW) == "UNKNOWN" and target.count() == 0


def test_concurrent_requests_execute_once_and_reserve_budget_once(model, evidence):
    runtime, target, action = model
    barrier = threading.Barrier(12)

    def submit(_):
        worker = Runtime(runtime.path, target)
        barrier.wait(timeout=10)
        return worker.submit(action, ALLOW)

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(submit, range(12)))
    assert set(results) <= {"EXECUTING", "COMMITTED"}
    assert "COMMITTED" in results and target.count() == 1
    snap = runtime.snapshot()
    assert snap["task"]["spent"] == 1
    assert sum(e["kind"] == "EXECUTE_RESERVED" for e in snap["events"]) == 1
    evidence[1]("runtime_concurrency.json", {"workers": 12, "results": results, "snapshot": snap, "target_effect_count": target.count()})


@pytest.mark.parametrize("pending", [False, True])
def test_cancel_is_terminal_after_restart_and_approval(model, pending):
    runtime, target, action = model
    if pending:
        runtime.submit(action, APPROVAL)
    runtime.cancel()
    runtime = Runtime(runtime.path, target)
    assert runtime.recover() == "CANCELLED"
    assert runtime.approve(action.key, action.binding) == "CANCELLED"
    assert runtime.submit(action, ALLOW) == "CANCELLED"
    assert runtime.complete({"health": True}) == "CANCELLED"
    assert target.count() == 0


def test_cancel_in_batch_stops_remaining_work(model):
    runtime, target, action = model
    original = target.execute

    def execute_then_cancel(a, lose_receipt=False):
        result = original(a, lose_receipt)
        runtime.cancel()
        return result

    target.execute = execute_then_cancel
    assert runtime.batch([action, replace(action, action_id="a2", key="key2")], ALLOW) == ["COMMITTED", "CANCELLED"]
    assert target.count() == 1 and runtime.recover() == "CANCELLED"


def test_unknown_effect_cancellation_stays_cancelling_until_reconciled(model):
    runtime, target, action = model
    runtime.submit(action, ALLOW, lose_receipt=True)
    runtime.cancel()
    runtime = Runtime(runtime.path, target)
    assert runtime.recover() == "CANCELLING"
    assert runtime.submit(action, ALLOW) == "CANCELLING"
    assert runtime.reconcile(action, "stale") == "UNKNOWN"
    assert runtime.recover() == "CANCELLING"
    assert runtime.complete({"health": True}) == "CANCELLING"
    assert runtime.reconcile(action) == "COMMITTED"
    assert runtime.recover() == "CANCELLED" and target.count() == 1


def test_committed_is_not_business_complete(model):
    runtime, target, action = model
    assert runtime.submit(action, ALLOW) == "COMMITTED"
    assert runtime.snapshot()["task"]["state"] == "VERIFYING"
    assert runtime.complete({}) == "VERIFICATION_FAILED"
    assert runtime.complete({"health": False}) == "VERIFICATION_FAILED"
    assert runtime.complete({"health": True, "invoice": True}) == "COMPLETE"
    assert runtime.submit(replace(action, action_id="a2", key="key2"), ALLOW) == "COMPLETE"
    assert target.count() == 1


def test_parallel_actions_cannot_overspend_budget(tmp_path, evidence):
    target = Target(tmp_path / "target.sqlite")
    runtime = Runtime(tmp_path / "budget.sqlite", target, budget=3)

    def submit(i):
        return Runtime(runtime.path, target).submit(Action(f"a{i}", f"k{i}", f"item/{i}", {"i": i}),
                                                  ALLOW, independent=True)

    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(submit, range(12)))
    assert results.count("COMMITTED") == 3 and results.count("BUDGET_EXHAUSTED") == 9
    assert target.count() == 3 and runtime.snapshot()["task"]["spent"] == 3
    evidence[1]("runtime_budget.json", {"results": results, "snapshot": runtime.snapshot(), "target_effect_count": target.count()})


@pytest.mark.parametrize("cost", [-1, 0, 1.5, True])
def test_invalid_budget_cost_cannot_mint_capacity(model, cost):
    runtime, target, action = model
    with pytest.raises(ValueError, match="INVALID_COST"):
        runtime.submit(replace(action, cost=cost), ALLOW)
    assert target.count() == 0

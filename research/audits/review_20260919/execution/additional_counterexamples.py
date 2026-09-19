"""User-requested static-review claims tested as explicit minimal counterexamples."""
import sqlite3
import traceback
import hashlib
import json
from inventory import get_block


def run(a):
    graph = get_block(a.inv, "10_", 7)
    committing = graph["raw"].split("COMMITTING\n")[-1]
    confirmed_edge = next(line for line in committing.splitlines() if "effect confirmed" in line)
    destination = confirmed_edge.split("→")[-1].strip()
    # Execute target state change and separately query its failed health predicate.
    target = {"version": "old", "health": True}
    trace = ["pre_commit_checks=PASS"]
    def deploy():
        target.update(version="new", health=False)
        trace.append("effect=CONFIRMED")
        return {"confirmed": True}
    effect = deploy()
    state = destination if effect["confirmed"] else "RECONCILING"
    actual_health = target["health"]
    trace.extend(["health=" + str(actual_health), "state=" + state])
    a.check("R02_confirmed_effect_failed_health_not_verified_complete", not (state == "VERIFIED_COMPLETE" and not actual_health),
            sources=[graph["id"]], model="faithful_state_graph_translation", expected_failure=True, severity="P1",
            details={"source_edge": confirmed_edge, "target": target.copy(), "trace": trace,
                     "contract_assumption": "Completion includes post-deployment healthy target; pre-commit tests alone cannot observe that."})
    fixed_state = "POST_COMMIT_VERIFYING" if effect["confirmed"] else "RECONCILING"
    if fixed_state == "POST_COMMIT_VERIFYING" and not target["health"]:
        fixed_state = "COMMITTED_BUT_UNHEALTHY"
    a.check("R02_corrected_postcommit_health_gate", fixed_state == "COMMITTED_BUT_UNHEALTHY", sources=[graph["id"]],
            model="corrected_simulation", details={"state": fixed_state, "effect_retained": effect,
                                                "rollback": "requires separately authorized and verified compensation; not asserted successful"})

    db = sqlite3.connect(a.run / "compensation.sqlite")
    db.execute("CREATE TABLE charges(id INTEGER PRIMARY KEY,amount INTEGER)")
    failures = []
    def charge(lose_reply=False):
        db.execute("INSERT INTO charges(amount) VALUES (10)")
        db.commit()
        if lose_reply:
            raise TimeoutError("charge committed; receipt lost")
        return db.execute("SELECT max(id) FROM charges").fetchone()[0]
    def compensate(charge_id):
        raise ConnectionError("defined compensation service unavailable")
    try:
        charge(lose_reply=True)
    except TimeoutError:
        failures.append({"phase": "initial_call", "traceback": traceback.format_exc()})
    # Minimal executable interpretation of chapter 6 lines 112-118 disjunction.
    # The compensation operation is defined, but successful execution is not guaranteed.
    semantics = {"natural_idempotent": False, "downstream_keyed": False, "confirmed_not_committed": False,
                 "has_defined_compensation": True}
    allowed_to_retry = any(semantics.values())
    if allowed_to_retry:
        repeated_id = charge()
        try:
            compensate(repeated_id)
        except ConnectionError:
            failures.append({"phase": "compensate_duplicate", "traceback": traceback.format_exc()})
    amounts = list(db.execute("SELECT * FROM charges"))
    a.check("CH6_compensation_alone_safe_retry_when_receipt_lost", sum(row[1] for row in amounts) == 10,
            sources=["manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:112-118"],
            model="faithful_prose_translation", expected_failure=True, severity="P1",
            details={"retry_preconditions": semantics, "allowed_to_retry": allowed_to_retry, "charges": amounts,
                     "failures": failures, "assumption": "Defined compensation is treated as sufficient admission to retry; service availability is not assumed."})
    # Separate corrective model starts from one committed/unknown charge. Never label compensated.
    corrected = {"effect": "UNKNOWN_EFFECT", "target_actual_charges": 1, "lookup_available": False,
                 "compensation_available": False, "retry_count": 0}
    if corrected["effect"] == "UNKNOWN_EFFECT" and not corrected["lookup_available"]:
        corrected["state"] = "RECONCILE_OR_ESCALATE"
    a.check("CH6_corrected_unknown_does_not_replay_for_compensation", corrected["retry_count"] == 0 and corrected["state"] == "RECONCILE_OR_ESCALATE",
            sources=["B036"], model="corrected_simulation", details=corrected)
    db.close()

    # Chapter 27 has contracts and commands, no reminder source. We cannot execute an absent implementation.
    # Two plausible operationalizations expose ambiguity; the failing one adds a live-time requirement.
    spec = get_block(a.inv, "27_", 2)
    checks = get_block(a.inv, "27_", 3)
    subscription = {"cancelled": False, "invoice": "unchanged"}
    decision_snapshot = dict(subscription)
    should_enqueue = not decision_snapshot["cancelled"]
    subscription["cancelled"] = True  # cancellation between selection and enqueue
    queue = []
    if should_enqueue:
        queue.append("subscription1")
    snapshot_interpretation = not decision_snapshot["cancelled"] or not queue
    live_interpretation = not subscription["cancelled"] or not queue
    a.check("CH27_cancel_time_semantics_ambiguity_exposed", snapshot_interpretation and not live_interpretation,
            sources=[spec["id"], checks["id"]], model="assumption_probe_not_original_failure",
            details={"decision_snapshot": decision_snapshot, "at_enqueue": subscription, "queue": queue,
                     "snapshot_contract_passes": snapshot_interpretation, "live_at_enqueue_contract_passes": live_interpretation,
                     "source_implementation_present": False,
                     "conclusion": "No original executable failure verdict. TOCTOU counterexample requires assuming current state at enqueue is authoritative, absent from spec."})
    # Show feasible interpretation with atomic current-state predicate, explicitly corrective.
    queue2 = []
    if not subscription["cancelled"]:
        queue2.append("subscription1")
    a.check("CH27_live_state_guard_prevents_enqueue", not queue2 and subscription["invoice"] == "unchanged",
            sources=[spec["id"], checks["id"]], model="corrected_simulation",
            details={"queue": queue2, "added_assumption": "Atomic cancellation check at enqueue, plus specified cancel/commit order."})
    # Static review R07 is about the book's assertion that TWO independent checks must fail.
    # Build distinct authoritative tables; a source-only status reinterpretation need not write invoices.
    billing = sqlite3.connect(a.run / "chapter27.sqlite")
    billing.execute("CREATE TABLE subscriptions(id INTEGER PRIMARY KEY,status TEXT)")
    billing.execute("CREATE TABLE invoices(id INTEGER PRIMARY KEY,subscription_id INTEGER,amount_cents INTEGER)")
    billing.execute("INSERT INTO subscriptions VALUES(1,'cancelled')")
    billing.execute("INSERT INTO invoices VALUES(1,1,10000)")
    billing.commit()
    def invoice_hash():
        ordered = list(billing.execute("SELECT id,subscription_id,amount_cents FROM invoices ORDER BY id"))
        return hashlib.sha256(json.dumps(ordered, separators=(",", ":")).encode()).hexdigest()
    original_invoice_hash = invoice_hash()
    cases = []
    for name, changed_paths, force_active, write_invoice in [
        ("positive", ["src/reminders/filter.py"], False, False),
        ("source_status_override", ["src/billing/state.py"], True, False),
        ("invoice_write", ["src/reminders/filter.py"], False, True),
        ("cancelled_still_enqueued", ["src/reminders/filter.py"], True, False),
    ]:
        billing.execute("SAVEPOINT fixture")
        status = billing.execute("SELECT status FROM subscriptions WHERE id=1").fetchone()[0]
        effective_status = "active" if force_active else status
        queued = [1] if effective_status == "active" else []
        if write_invoice:
            billing.execute("UPDATE invoices SET amount_cents=0 WHERE id=1")
        case = {"name": name, "changed_paths": changed_paths,
                "scope_guard": all(p.startswith(("src/reminders/", "tests/reminders/")) for p in changed_paths),
                "invoice_integrity": original_invoice_hash == invoice_hash(),
                "sealed_cancelled_slice": not queued, "enqueued_count": len(queued),
                "invoice_before_sha256": original_invoice_hash, "invoice_after_sha256": invoice_hash(),
                "implicit_invoice_write_added": write_invoice}
        cases.append(case)
        billing.execute("ROLLBACK TO fixture")
        billing.execute("RELEASE fixture")
    disputed = cases[1]
    a.check("CH27_claim_scope_and_invoice_both_fail_from_source_edit", not disputed["scope_guard"] and not disputed["invoice_integrity"],
            sources=["B118", "B119", "manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:86"],
            model="faithful_prose_countermodel", expected_failure=True, severity="P1", details=disputed |
            {"interpretation": "Changing status interpretation alone violates scope and may enqueue a reminder; invoice hash stays identical. Both failures require extra unstated persistent invoice mutation/coupling."})
    expected_checks = [(True, True, True), (False, True, False), (True, False, True), (True, True, False)]
    actual_checks = [(r["scope_guard"], r["invoice_integrity"], r["sealed_cancelled_slice"]) for r in cases]
    a.check("CH27_independent_positive_and_three_negative_fixtures", actual_checks == expected_checks,
            sources=["B118", "B119"], model="explicit_fixture_verifier", details=cases)
    billing.close()
    return {"health": {"trace": trace, "state": state, "corrected": fixed_state},
            "compensation": {"charges": amounts, "failures": failures, "corrected": corrected},
            "chapter27": {"original_runtime": "UNVERIFIED; no implementation", "snapshot_pass": snapshot_interpretation,
                          "live_pass": live_interpretation, "claim": "No original runtime verdict; source-only edit is a countermodel to the claim BOTH guards necessarily fail",
                          "independent_guard_cases": cases},
            "statistics": {"two_by_two_model_harness_experiment": "NOT_RUN", "budget_gate_empirical_threshold": "NOT_ESTIMATED",
                           "why": "No real factorial trial or calibrated cost/quality data; deterministic gate simulation only."}}

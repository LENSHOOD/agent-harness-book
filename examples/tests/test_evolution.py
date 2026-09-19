from dataclasses import replace
import pytest
from src.evolution import (trials, evaluate, FrozenEvaluator, FinalTest, ReleaseController,
                           FROZEN, BASE_BUNDLE, NEW_BUNDLE, dump_trials)


def test_denominator_freeze_activation_final_test_and_slice_rollback(evidence):
    root, save = evidence
    sets = {name: trials(name) for name in ("baseline", "cheat", "candidate", "canary")}
    metrics = {name: evaluate(rows) for name, rows in sets.items()}
    base, cheat, candidate, canary = [metrics[n] for n in sets]
    assert (base["successes"], cheat["successes"], candidate["successes"], canary["successes"]) == (24, 18, 28, 29)
    assert cheat["completed_only_rate_for_negative_demo"] == .9 and cheat["rate"] == .6
    assert all(r.attempts == 3 for r in sets["cheat"] if r.status == "TIMEOUT")
    gate = FrozenEvaluator()
    kwargs = {"manifest": dict(FROZEN), "activation_beacon": True}
    rejected = gate.gate(sets["cheat"], sets["baseline"], **kwargs)
    good = gate.gate(sets["candidate"], sets["baseline"], **kwargs)
    assert not rejected["accepted"] and good["accepted"]
    assert candidate["activation"] == 28 and candidate["denominator"] == 30
    final = FinalTest(root / "final_test.sqlite")
    final_result = final.evaluate_once("candidate-fixed-before-final-test")
    with pytest.raises(ValueError, match="FINAL_TEST_ALREADY_ACCESSED"):
        FinalTest(root / "final_test.sqlite").evaluate_once("retuned-candidate")
    release = ReleaseController()
    assert not release.canary(rejected, NEW_BUNDLE)
    assert release.current == BASE_BUNDLE
    assert release.canary(good, NEW_BUNDLE)
    assert release.assignments["in-flight"] == BASE_BUNDLE
    assert release.assignments["new-task"] == NEW_BUNDLE
    release.observe(canary, base)
    assert canary["rate"] > candidate["rate"] and canary["critical_failures"] == 1
    assert release.current == BASE_BUNDLE
    assert release.events[-2:] == ["STOP_NEW_CANDIDATE_TRAFFIC", "ROLLBACK_FULL_BUNDLE"]
    save("evolution_trials.json", {k: dump_trials(v) for k, v in sets.items()})
    save("evolution.json", {"kind": "30 scripted trials; descriptive governance reference only",
                            "frozen": FROZEN, "frozen_sha256": gate.frozen_sha256,
                            "metrics": metrics, "rejected_gate": rejected, "accepted_gate": good,
                            "final_test": final_result, "release_events": release.events,
                            "final_bundle": release.current, "model_api_calls": 0})


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "DENOMINATOR_INTEGRITY"), ("duplicate", "DENOMINATOR_INTEGRITY"),
    ("extra", "DENOMINATOR_INTEGRITY"), ("wrong_id", "DENOMINATOR_INTEGRITY"),
    ("slice", "TRIAL_INTEGRITY"), ("denominator", "DENOMINATOR_INTEGRITY"),
    ("evaluator", "FROZEN_EVALUATOR_CHANGED"), ("beacon", "NOT_ACTIVATED"),
    ("activation", "NOT_ACTIVATED"),
])
def test_evolution_negative_controls(mutation, reason):
    rows, baseline = trials("candidate"), trials("baseline")
    kwargs = {"manifest": dict(FROZEN), "activation_beacon": True}
    if mutation == "missing": rows = rows[:20]
    if mutation == "duplicate": rows[-1] = rows[0]
    if mutation == "extra": rows.append(replace(rows[0], trial_id="extra"))
    if mutation == "wrong_id": rows[0] = replace(rows[0], trial_id="unregistered")
    if mutation == "slice": rows[0] = replace(rows[0], slice="ordinary")
    if mutation == "denominator": kwargs["declared_denominator"] = 20
    if mutation == "evaluator": kwargs["manifest"]["evaluator"] = "candidate-owned"
    if mutation == "beacon": kwargs["activation_beacon"] = False
    if mutation == "activation": rows = [replace(row, activated=False) for row in rows]
    with pytest.raises(ValueError, match=reason):
        FrozenEvaluator().gate(rows, baseline, **kwargs)

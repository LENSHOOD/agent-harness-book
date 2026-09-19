from datetime import date
from src.git_case import run_case
from src.negative_windows import baseline, hardcoded


def test_real_git_seal_clean_apply_and_negative_candidates(evidence):
    root, save = evidence
    result = run_case(root)
    save("git.json", result)
    assert result["clean_apply"]["exit"] == 0


def test_historical_hardcode_is_not_a_general_fix():
    for day, hours in [(date(2026, 3, 8), 23), (date(2026, 11, 1), 25)]:
        start, end = hardcoded(day, "America/New_York")
        assert (end - start).total_seconds() == hours * 3600
        a, b = baseline(day, "America/New_York")
        assert (b - a).total_seconds() != hours * 3600

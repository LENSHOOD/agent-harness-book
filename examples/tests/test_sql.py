import pytest
from src.sql_case import SnapshotQuery, SNAPSHOT, LATER, fixture_rows


def test_snapshot_dedupe_null_internal_reconciliation_and_suppression(evidence):
    root, save = evidence
    query = SnapshotQuery(root / "snapshot.sqlite")
    try:
        report = query.report()
        assert [(r["province"], r["net"], r["accounts"]) for r in report["internal"]["groups"]] == [
            ("GD", 1800, 20), ("BJ", 950, 19), ("GD", 1800, 20), ("SH", 500, 20)]
        assert report["internal"]["total"] == 5050
        assert report["internal"]["disclosed_total"] == 4100
        assert report["internal"]["restricted_residual"] == 950
        assert len(report["internal"]["quarantined"]) == 3
        assert {r["province"] for r in report["public"]["groups"]} == {"GD", "SH"}
        assert set(report["public"]) == {"as_of", "groups", "scope"}
        old_hash = query.fingerprint()
        # Late ingestion cannot mutate the materialized input.
        query.db.execute("INSERT INTO history SELECT * FROM history WHERE event_id='jul-1'")
        query.db.commit()
        assert query.fingerprint() == old_hash and query.report() == report
        save("sql_internal_restricted_fixture.json", report["internal"])
        save("sql_public_fixture.json", report["public"])
        save("sql.json", {"kind": "synthetic SQLite reference; no BigQuery execution",
                          "fixture_rows": len(fixture_rows()), "snapshot": SNAPSHOT,
                          "snapshot_sha256": old_hash, "dedupe": "exact duplicates only; conflicting versions reject",
                          "null_policy": "refund=0; unknown revenue/account quarantined",
                          "reconciliation": "full eligible scope before k=20 disclosure"})
    finally:
        query.close()


def test_reject_snapshot_drift_and_false_public_total(tmp_path):
    query = SnapshotQuery(tmp_path / "snapshot.sqlite")
    try:
        with pytest.raises(ValueError, match="SNAPSHOT_MISMATCH"):
            query.report(LATER)
        assert query.query_count == 0
        with pytest.raises(ValueError, match="FULL_INTERNAL_RECONCILIATION_FAILED"):
            query.report(finance_total=4100)
        with pytest.raises(ValueError, match="DISCLOSURE_POLICY_DOWNGRADE"):
            query.report(k=19)
    finally:
        query.close()


def test_conflicting_deduplication_versions_are_not_arbitrarily_selected(tmp_path):
    rows = fixture_rows()
    conflict = list(rows[0])
    conflict[4] = 200
    with pytest.raises(ValueError, match="CONFLICTING_EVENT_VERSIONS"):
        SnapshotQuery(tmp_path / "conflict.sqlite", rows=rows + [tuple(conflict)])


def test_later_snapshot_has_explicit_different_total(tmp_path):
    query = SnapshotQuery(tmp_path / "later.sqlite", snapshot=LATER)
    try:
        report = query.report(LATER, finance_total=5000)
        assert report["internal"]["total"] == 5000
    finally:
        query.close()

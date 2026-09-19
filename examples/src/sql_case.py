"""SQLite snapshot reference with an explicit, synthetic accounting policy.

Not a BigQuery dialect translation. Integers are preconverted CNY fixture units.
"""
import hashlib
import json
import sqlite3

SNAPSHOT = "2026-08-03T02:00:00Z"
LATER = "2026-08-03T03:00:00Z"
START = "2026-08-01T00:00:00Z"

AGGREGATE = """
SELECT month, province, plan, SUM(revenue - COALESCE(refund, 0)) AS net,
       COUNT(DISTINCT account_id) AS accounts
FROM eligible
GROUP BY month, province, plan
ORDER BY month, province, plan
"""


def fixture_rows():
    rows = []

    def add(event, month, province, plan, revenue, refund, account, start=START, end=None, region="CN"):
        rows.append((event, month, province, plan, revenue, refund, account, start, end, region))

    for i in range(1, 21):
        add(f"jun-{i}", "2026-06-01", "GD", "pro", 100, 10, f"j{i}")
        add(f"jul-{i}", "2026-07-01", "GD", "pro", 100, None if i == 20 else 10, f"j{i}",
            end=LATER if i == 1 else SNAPSHOT if i == 2 else None)
        add(f"sh-{i}", "2026-07-01", "SH", "basic", 25, 0, f"s{i}")
    for i in range(1, 20):
        add(f"bj-{i}", "2026-07-01", "BJ", "basic", 50, 0, f"b{i}")
    add("jul-2", "2026-07-01", "GD", "pro", 100, 20, "j2", start=SNAPSHOT)
    add("jul-1", "2026-07-01", "GD", "pro", 100, 60, "j1", start=LATER)
    add("jul-1", "2026-07-01", "GD", "pro", 100, 10, "j1", end=LATER)
    add("null-account", "2026-07-01", "GD", "pro", 50, 0, None)
    add("null-revenue", "2026-07-01", "GD", "pro", None, 0, "unknown-revenue")
    for event, month, region in [("before-month", "2026-05-01", "CN"),
                                 ("end-exclusive", "2026-08-01", "CN"),
                                 ("not-month-start", "2026-07-31", "CN"),
                                 ("foreign", "2026-07-01", "US")]:
        add(event, month, "BOUNDARY", "basic", 777, 0, event, region=region)
    return rows


class SnapshotQuery:
    def __init__(self, path, snapshot=SNAPSHOT, rows=None):
        self.path, self.snapshot = path, snapshot
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.query_count = 0
        db = self.db
        try:
            db.execute("CREATE TABLE history (event_id TEXT, month TEXT, province TEXT, plan TEXT, "
                       "revenue INTEGER, refund INTEGER, account_id TEXT, valid_from TEXT, valid_to TEXT, region TEXT)")
            db.executemany("INSERT INTO history VALUES (?,?,?,?,?,?,?,?,?,?)", fixture_rows() if rows is None else rows)
            db.execute("CREATE TABLE snapshot_meta (as_of TEXT PRIMARY KEY)")
            db.execute("INSERT INTO snapshot_meta VALUES (?)", (snapshot,))
            # Materialized snapshot survives future history ingestion/time-travel expiry.
            db.execute("CREATE TABLE pinned AS SELECT DISTINCT * FROM history WHERE valid_from<=? "
                       "AND (valid_to IS NULL OR ?<valid_to)", (snapshot, snapshot))
            conflicts = db.execute("SELECT event_id FROM pinned GROUP BY event_id HAVING COUNT(*)>1").fetchall()
            if conflicts:
                raise ValueError("CONFLICTING_EVENT_VERSIONS")
            db.execute("CREATE VIEW quarantined AS SELECT *, CASE WHEN revenue IS NULL THEN 'NULL_REVENUE' "
                       "WHEN account_id IS NULL THEN 'NULL_ACCOUNT' ELSE 'NON_CANONICAL_MONTH' END AS reason "
                       "FROM pinned WHERE revenue IS NULL OR account_id IS NULL OR substr(month,9,2)!='01'")
            db.execute("CREATE VIEW eligible AS SELECT * FROM pinned WHERE revenue IS NOT NULL "
                       "AND account_id IS NOT NULL AND substr(month,9,2)='01' AND region='CN' "
                       "AND month IN ('2026-06-01','2026-07-01')")
            db.commit()
        except BaseException:
            db.rollback()
            db.close()
            raise

    def report(self, requested_snapshot=SNAPSHOT, finance_total=5050, k=20):
        if requested_snapshot != self.snapshot:
            raise ValueError("SNAPSHOT_MISMATCH")
        if type(k) is not int or k < 20:
            raise ValueError("DISCLOSURE_POLICY_DOWNGRADE")
        self.query_count += 1
        rows = [dict(r) for r in self.db.execute(AGGREGATE)]
        total = sum(r["net"] for r in rows)
        direct = self.db.execute("SELECT SUM(revenue-COALESCE(refund,0)) FROM eligible").fetchone()[0]
        if total != direct or total != finance_total:
            raise ValueError("FULL_INTERNAL_RECONCILIATION_FAILED")
        disclosed = [r for r in rows if r["accounts"] >= k]
        # Public output does not expose total/residual: subtraction could reveal one small group.
        public = {"as_of": self.snapshot, "groups": disclosed,
                  "scope": "Partial disclosure; small groups suppressed. Not a finance total."}
        return {"internal": {"groups": rows, "total": total, "finance_total": finance_total,
                             "direct_total": direct, "disclosed_total": sum(r["net"] for r in disclosed),
                             "restricted_residual": total - sum(r["net"] for r in disclosed),
                             "quarantined": [dict(r) for r in self.db.execute("SELECT * FROM quarantined")]},
                "public": public}

    def fingerprint(self):
        rows = [tuple(r) for r in self.db.execute("SELECT * FROM pinned ORDER BY event_id")]
        return hashlib.sha256(json.dumps(rows, separators=(",", ":")).encode()).hexdigest()

    def close(self):
        self.db.close()

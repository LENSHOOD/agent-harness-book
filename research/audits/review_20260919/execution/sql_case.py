"""Actual SQLite execution with explicit, inspectable temporal emulation."""
import sqlite3
import re
import json
from datetime import date
from auditlib import dump
from inventory import get_block, sha

SNAPSHOT = "2026-08-03T02:00:00Z"
BEFORE = "2026-08-03T01:59:59Z"
LATER = "2026-08-03T03:00:00Z"
START = "2026-08-01T00:00:00Z"


def run(a):
    block = get_block(a.inv, "25_", language="sql")
    source = [block["id"]]
    dbpath = a.run / "subscription.sqlite"
    db = sqlite3.connect(dbpath)
    db.row_factory = sqlite3.Row
    # ATTACH gives the exact manuscript's semantic.table identifier a real object.
    db.execute("ATTACH DATABASE ? AS semantic", (str(a.run / "semantic.sqlite"),))
    db.execute("""CREATE TABLE semantic.history (
        ingest_id INTEGER PRIMARY KEY, event_id TEXT, month TEXT, province TEXT,
        plan TEXT, recognized_revenue_cny INTEGER, refunds_cny INTEGER,
        account_id TEXT, region TEXT, valid_from TEXT, valid_to TEXT)""")
    rows = []

    def add(event, month, province, plan, revenue, refund, account, region="CN", start=START, end=None):
        rows.append([len(rows) + 1, event, month, province, plan, revenue, refund, account, region, start, end])

    for i in range(1, 21):
        add(f"jun-{i}", "2026-06-01", "GD", "pro", 100, 10, f"j{i}")
        add(f"jul-{i}", "2026-07-01", "GD", "pro", 100, None if i == 20 else 10, f"j{i}",
            end=LATER if i == 1 else SNAPSHOT if i == 2 else None)
        add(f"sh-{i}", "2026-07-01", "SH", "basic", 25, 0, f"s{i}")
    for i in range(1, 20):
        add(f"bj-{i}", "2026-07-01", "BJ", "basic", 50, 0, f"b{i}")
    add("jul-2", "2026-07-01", "GD", "pro", 100, 20, "j2", start=SNAPSHOT)
    add("jul-1", "2026-07-01", "GD", "pro", 100, 60, "j1", start=LATER)
    # Exact duplicate at the same logical event/version. DISTINCT account count does not dedupe money.
    add("jul-1", "2026-07-01", "GD", "pro", 100, 10, "j1", end=LATER)
    add("null-account", "2026-07-01", "GD", "pro", 50, 0, None)
    add("null-revenue", "2026-07-01", "GD", "pro", None, 0, "unknown-revenue")
    for event, month, region in [("before-month", "2026-05-01", "CN"),
                                 ("end-exclusive", "2026-08-01", "CN"),
                                 ("not-month-start", "2026-07-31", "CN"),
                                 ("foreign", "2026-07-01", "US")]:
        add(event, month, "BOUNDARY", "basic", 777, 0, event, region)
    db.executemany("INSERT INTO semantic.history VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    db.commit()
    dump(a.run / "sql_fixture_rows.json", {"columns": [d[1] for d in db.execute("PRAGMA semantic.table_info(history)")], "rows": rows})

    def pin(snapshot):
        if snapshot not in {SNAPSHOT, BEFORE, LATER}:
            raise ValueError("unregistered fixture snapshot")
        db.execute("DROP VIEW IF EXISTS semantic.subscription_revenue_v4")
        db.execute(f"""CREATE VIEW semantic.subscription_revenue_v4 AS
            SELECT * FROM history WHERE valid_from <= '{snapshot}'
            AND (valid_to IS NULL OR '{snapshot}' < valid_to)""")

    def query(sql):
        return [dict(row) for row in db.execute(sql)]

    pin(SNAPSHOT)
    _, raw_error = a.attempt("SQL_raw_SQLite", lambda: query(block["raw"]), sources=source,
                             expected_exception=sqlite3.OperationalError, severity="DIALECT_MISMATCH")
    raw_error.update(classification="DIALECT_MISMATCH", original_SQL_error_claim=False,
                     interpretation="SQLite lacks this BigQuery time-travel syntax; not a verdict on original dialect validity.")
    retrieval = a.root / "research/audits/review_20260919/retrieval/bigquery-time-travel.json"
    bigquery = {"kind": "main-agent official-document verification, read from local retrieval; NOT engine execution",
                "url": "https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#for_system_time_as_of",
                "engine_executed": False, "retrieval_present": retrieval.exists(),
                "as_of_date": "2026-08-03", "review_date": "2026-09-19",
                "age_calendar_days": (date(2026, 9, 19) - date(2026, 8, 3)).days,
                "documented_max_lookback_days": 7,
                "replay_requirement": "Materialize/archive the versioned data. A fixed Aug3 AS OF cannot directly replay via standard time travel on Sep19."}
    if retrieval.exists():
        evidence = json.loads(retrieval.read_text())
        text = evidence["text"]
        bigquery.update(retrieval=str(retrieval.relative_to(a.root)), retrieval_sha256=sha(retrieval.read_bytes()),
                        accessed_at=evidence.get("accessed_at"), supplied_text_sha256=evidence.get("text_sha256"),
                        syntax_heading_found="FOR SYSTEM_TIME AS OF" in text,
                        seven_day_limit_found="More than seven (7) days before the current timestamp." in text,
                        relevant_text_lines=[419, 421, 437, 439, 440])
    adapted = re.sub(r"FOR SYSTEM_TIME AS OF TIMESTAMP '[^']+'\n", "", block["raw"])
    adapted = re.sub(r"\bDATE ('[^']+')", r"\1", adapted)
    (a.run / "sql_raw.sql").write_text(block["raw"])
    (a.run / "sql_sqlite_adapted.sql").write_text(adapted)
    expected = [
        {"month": "2026-06-01", "province": "GD", "plan": "pro", "net_revenue_cny": 1800, "accounts": 20},
        {"month": "2026-07-01", "province": "GD", "plan": "pro", "net_revenue_cny": 1840, "accounts": 21},
        {"month": "2026-07-01", "province": "SH", "plan": "basic", "net_revenue_cny": 500, "accounts": 20},
    ]
    actual = query(adapted)
    a.check("SQL_adapted_hand_calculation", actual == expected, sources=source, model="dialect_adapter",
            details={"expected": expected, "actual": actual})
    a.check("SQL_k19_suppressed_k20_retained", {x["province"] for x in actual} == {"GD", "SH"},
            sources=source, model="dialect_adapter", details=actual)
    direct = query("""SELECT SUM(recognized_revenue_cny-refunds_cny) AS total
        FROM semantic.subscription_revenue_v4 WHERE region='CN'
        AND month IN ('2026-06-01','2026-07-01')""")[0]["total"]
    published = sum(x["net_revenue_cny"] for x in actual)
    a.check("SQL_suppressed_groups_reconcile_to_finance_without_bridge", published == direct, sources=source,
            model="dialect_adapter", expected_failure=True, severity="P1",
            details={"published": published, "all_groups": direct, "suppressed": direct - published,
                     "assumption": "Finance total contains all groups. A suppression bridge or pre-suppression reconciliation is needed."})
    # Independent contribution probes show each anomaly, without quietly changing original arithmetic.
    probes = query("""SELECT event_id, ingest_id, recognized_revenue_cny, refunds_cny, account_id,
        recognized_revenue_cny-refunds_cny AS net FROM semantic.subscription_revenue_v4
        WHERE event_id IN ('jul-1','jul-2','jul-20','null-account','null-revenue') ORDER BY ingest_id""")
    a.check("SQL_DUPLICATE_money_not_doubled", sum(r["net"] for r in probes if r["event_id"] == "jul-1") == 90,
            sources=source, model="dialect_adapter", expected_failure=True, severity="P1", details=probes)
    a.check("SQL_NULL_refund_preserves_100_revenue", next(r["net"] for r in probes if r["event_id"] == "jul-20") == 100,
            sources=source, model="dialect_adapter", expected_failure=True, severity="P1",
            details={"assumption": "This probe interprets NULL refund as no refund; original contract does not specify NULL policy.", "rows": probes})
    a.check("SQL_NULL_account_excludes_money", sum(r["net"] or 0 for r in probes if r["account_id"] is None) == 0,
            sources=source, model="dialect_adapter", expected_failure=True, severity="P2", details=probes)
    snapshots = {}
    for snapshot in (BEFORE, SNAPSHOT, LATER):
        pin(snapshot)
        snapshots[snapshot] = query(adapted)
    nets = [next(r["net_revenue_cny"] for r in snapshots[s] if r["month"] == "2026-07-01" and r["province"] == "GD")
            for s in (BEFORE, SNAPSHOT, LATER)]
    a.check("SQL_snapshot_half_open_version_boundary", nets == [1850, 1840, 1700], sources=source,
            model="dialect_adapter", details={"snapshots": snapshots, "expected_GD_July": [1850, 1840, 1700],
                                             "later_delta": "-50 refund backfill AND -90 duplicate's valid_to boundary"})
    gateway_calls = []
    def gateway(requested):
        if requested != SNAPSHOT:
            raise ValueError("SNAPSHOT_STALE_OR_MISMATCH")
        gateway_calls.append(requested)
        pin(requested)
        return query(adapted)
    import traceback
    try:
        gateway(LATER)
    except ValueError:
        drift = {"rejected": True, "traceback": traceback.format_exc()}
    else:
        drift = {"rejected": False}
    a.check("SQL_gateway_rejects_snapshot_drift", drift["rejected"] and not gateway_calls, sources=[block["id"], "B108"],
            model="corrected_simulation", details={"contract": SNAPSHOT, "requested": LATER,
                                                   "executed_queries": len(gateway_calls), **drift})
    a.check("SQL_gateway_accepts_pinned_snapshot", gateway(SNAPSHOT) == expected and len(gateway_calls) == 1,
            sources=[block["id"], "B108"], model="corrected_simulation", details=gateway_calls)
    pin(SNAPSHOT)
    # Explicitly corrective assumptions: dedupe event+version, reject/quarantine NULL revenue,
    # suppress unidentifiable accounts, interpret NULL refunds as zero. Not original query.
    corrected = """WITH dedup AS (
      SELECT *, ROW_NUMBER() OVER(PARTITION BY event_id, valid_from ORDER BY ingest_id) AS rn
      FROM semantic.subscription_revenue_v4
    ) SELECT month, province, plan,
      SUM(recognized_revenue_cny - COALESCE(refunds_cny,0)) AS net_revenue_cny,
      COUNT(DISTINCT account_id) AS accounts
    FROM dedup WHERE rn=1 AND account_id IS NOT NULL AND recognized_revenue_cny IS NOT NULL
      AND region='CN' AND month IN ('2026-06-01','2026-07-01')
    GROUP BY month, province, plan HAVING COUNT(DISTINCT account_id)>=20;"""
    (a.run / "sql_corrective_assumptions.sql").write_text(corrected)
    clean = query(corrected)
    clean_expected = [{**x, "net_revenue_cny": 1800, "accounts": 20} if x["province"] == "GD" and x["month"] == "2026-07-01" else x for x in expected]
    a.check("SQL_corrective_hand_calculation", clean == clean_expected, sources=source, model="corrected_simulation",
            details={"expected": clean_expected, "actual": clean, "finance_total": 5050,
                     "published_total": 4100, "suppression_bridge": 950, "NULL_revenue_quarantined": 1})
    a.check("SQL_date_bucket_boundaries", query("""SELECT DISTINCT month FROM semantic.subscription_revenue_v4
        WHERE region='CN' AND month IN ('2026-06-01','2026-07-01') ORDER BY month""") ==
        [{"month": "2026-06-01"}, {"month": "2026-07-01"}], sources=source, model="dialect_adapter",
        details={"excluded": ["2026-05-01", "2026-07-31", "2026-08-01"], "precondition": "month is normalized first-of-month, not raw transaction date"})
    # All-NULL revenue group can pass k while yielding NULL money.
    null_result = db.execute("""WITH x(a,r,f) AS (SELECT 1,NULL,0 UNION ALL SELECT a+1,NULL,0 FROM x WHERE a<20)
        SELECT COUNT(DISTINCT a),SUM(r-f) FROM x HAVING COUNT(DISTINCT a)>=20""").fetchone()
    a.check("SQL_k_gate_guarantees_numeric_revenue", null_result[1] is not None, sources=source,
            model="dialect_adapter", expected_failure=True, severity="P2", details=list(null_result))
    db.commit()
    schema_dump = "\n".join(db.iterdump())
    (a.run / "sql_main_dump.sql").write_text(schema_dump)
    db.close()
    return {"raw_error": raw_error, "dialect": "SQLite " + sqlite3.sqlite_version,
            "original_dialect": "BigQuery FOR SYSTEM_TIME AS OF supported by main-agent official-doc verification; no BigQuery account/query executed",
            "bigquery_documentation": bigquery,
            "adaptation": "Remove FOR SYSTEM_TIME and DATE keyword; attach semantic SQLite DB with half-open as-of view",
            "assumptions": ["UTC ISO text versions, valid_from <= snapshot < valid_to", "month normalized YYYY-MM-01",
                            "whole CNY integers already converted at finance rate; no FX/rounding verification",
                            "exact event/version duplicates are invalid", "NULL rules not specified in manuscript",
                            "row/column IAM, causal narrative review, parquet publication not implemented"],
            "fixture_count": len(rows), "original_semantics": actual, "manual_expected": expected,
            "snapshots": snapshots, "anomaly_contributions": probes, "corrected": clean,
            "published_original": published, "all_groups_original": direct,
            "hand_calculation": "June 20*90=1800; July GD 18*90+80+NULL+duplicate90+anonymous50+NULL=1840; SH20*25=500; BJ19*50=950 suppressed. Correction GD18*90+80+100=1800."}

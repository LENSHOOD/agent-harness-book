"""Durable teaching model: SQLite control plane and a separate idempotent target.

Only target-owned uniqueness establishes exactly-once application in this model.
No real IAM, distributed lease fencing, process cancellation, or signatures.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import sqlite3


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Action:
    action_id: str
    key: str
    target: str
    args: dict
    cost: int = 1
    tenant: str = "teaching"

    @property
    def binding(self):
        return digest({"tenant": self.tenant, "target": self.target, "args": self.args})


@contextmanager
def transaction(path):
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("BEGIN IMMEDIATE")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


class Target:
    """Separate authoritative DB. key is globally unique inside this target store."""
    def __init__(self, path):
        self.path = path
        with transaction(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS effects (key TEXT PRIMARY KEY, "
                       "binding TEXT NOT NULL, target TEXT NOT NULL, args TEXT NOT NULL)")

    def execute(self, action, lose_receipt=False):
        with transaction(self.path) as db:
            prior = db.execute("SELECT * FROM effects WHERE key=?", (action.key,)).fetchone()
            if prior and prior["binding"] != action.binding:
                raise ValueError("IDEMPOTENCY_BINDING_CONFLICT")
            if not prior:
                db.execute("INSERT INTO effects VALUES (?,?,?,?)",
                           (action.key, action.binding, action.target, json.dumps(action.args)))
        if lose_receipt:
            raise TimeoutError("target committed; response lost")
        return {"key": action.key, "binding": action.binding, "status": "COMMITTED"}

    def lookup(self, action, mode="fresh"):
        if mode == "unavailable":
            raise TimeoutError("lookup unavailable")
        if mode == "none":
            return None
        with transaction(self.path) as db:
            row = db.execute("SELECT * FROM effects WHERE key=?", (action.key,)).fetchone()
        return {"key": action.key, "binding": row["binding"] if row else action.binding,
                "status": "COMMITTED" if row else "ABSENT",
                "authoritative": mode == "fresh", "fresh": mode == "fresh"}

    def count(self):
        with transaction(self.path) as db:
            return db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]


class Runtime:
    def __init__(self, path, target, budget=10):
        if type(budget) is not int or budget < 0:
            raise ValueError("INVALID_BUDGET")
        self.path, self.target = path, target
        with transaction(path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS task (id INTEGER PRIMARY KEY CHECK(id=1), "
                       "state TEXT NOT NULL, budget INTEGER NOT NULL, spent INTEGER NOT NULL, "
                       "cancel_requested INTEGER NOT NULL DEFAULT 0)")
            db.execute("INSERT OR IGNORE INTO task VALUES (1,'ACTIVE',?,0,0)", (budget,))
            db.execute("CREATE TABLE IF NOT EXISTS ledger (action_id TEXT PRIMARY KEY, "
                       "key TEXT UNIQUE NOT NULL, binding TEXT NOT NULL, payload TEXT NOT NULL, "
                       "status TEXT NOT NULL, cost INTEGER NOT NULL, approved INTEGER NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, kind TEXT, detail TEXT)")

    @staticmethod
    def event(db, kind, detail):
        db.execute("INSERT INTO events(kind,detail) VALUES (?,?)", (kind, str(detail)))

    def snapshot(self):
        with transaction(self.path) as db:
            return {"task": dict(db.execute("SELECT * FROM task").fetchone()),
                    "ledger": [dict(r) for r in db.execute("SELECT * FROM ledger ORDER BY action_id")],
                    "events": [dict(r) for r in db.execute("SELECT * FROM events ORDER BY seq")]}

    def submit(self, action, policy, lose_receipt=False, *, independent=False):
        # Freeze caller-owned mutable arguments before binding and execution.
        action = Action(action.action_id, action.key, action.target,
                        json.loads(json.dumps(action.args, allow_nan=False)), action.cost, action.tenant)
        if not all(isinstance(s, str) and s.strip() for s in
                   (action.action_id, action.key, action.target, action.tenant)):
            raise ValueError("INVALID_ID")
        if type(action.cost) is not int or action.cost < 1:
            raise ValueError("INVALID_COST")
        with transaction(self.path) as db:
            task = db.execute("SELECT * FROM task").fetchone()
            if task["state"] in {"CANCELLING", "CANCELLED", "COMPLETE"}:
                return task["state"]
            prior = db.execute("SELECT * FROM ledger WHERE key=? OR action_id=?",
                               (action.key, action.action_id)).fetchall()
            if any(r["binding"] != action.binding or r["key"] != action.key or r["action_id"] != action.action_id
                   or r["cost"] != action.cost for r in prior):
                raise ValueError("IDEMPOTENCY_BINDING_CONFLICT")
            record = prior[0] if prior else None
            if record and record["status"] in {"COMMITTED", "UNKNOWN", "EXECUTING", "DENIED"}:
                return record["status"]  # Reading a recorded outcome never dispatches.
            unresolved = db.execute("SELECT status,payload FROM ledger WHERE status IN ('UNKNOWN','EXECUTING')").fetchall()
            if any(r["status"] == "UNKNOWN" for r in unresolved):
                self.update_after_effect(db, "NEEDS_RECONCILIATION")
                return "NEEDS_RECONCILIATION"
            # Sequential by default. A trusted caller may predeclare independence;
            # this small model additionally rejects an overlapping target footprint.
            if unresolved and (not independent or any(json.loads(r["payload"]).get("target") in
                                                      {None, action.target} for r in unresolved)):
                self.update_after_effect(db, "WAITING_FOR_EFFECT")
                return "PENDING"
            pending = db.execute("SELECT key FROM ledger WHERE status='AWAITING_APPROVAL'").fetchone()
            if pending and pending[0] != action.key:
                return "AWAITING_APPROVAL"
            if record and record["status"] == "AWAITING_APPROVAL" and not record["approved"]:
                return "AWAITING_APPROVAL"
            if record:
                action = Action(**json.loads(record["payload"]))  # Resume the sealed original identity/payload.
            approved = bool(record and record["approved"])
            decision = policy(action, approved)  # Always current policy after external approval.
            self.event(db, "AUTHORIZE", decision)
            if decision not in {"ALLOW", "DENY", "REQUIRE_APPROVAL"}:
                raise ValueError("UNSUPPORTED_POLICY_DECISION")
            status = {"DENY": "DENIED", "REQUIRE_APPROVAL": "AWAITING_APPROVAL",
                      "ALLOW": "INTENT_RECORDED"}[decision]
            payload = json.dumps({"action_id": action.action_id, "key": action.key,
                                  "target": action.target, "args": action.args,
                                  "cost": action.cost, "tenant": action.tenant})
            if not record:
                db.execute("INSERT INTO ledger(action_id,key,binding,payload,status,cost) VALUES (?,?,?,?,?,?)",
                           (action.action_id, action.key, action.binding, payload, status, action.cost))
            else:
                db.execute("UPDATE ledger SET status=? WHERE key=?", (status, action.key))
            if decision == "DENY":
                self.update_after_effect(db, "ACTIVE")
                self.event(db, "DENIED", action.key)
                return "DENIED"
            if decision == "REQUIRE_APPROVAL":
                db.execute("UPDATE ledger SET approved=0 WHERE key=?", (action.key,))
                self.update_after_effect(db, "AWAITING_APPROVAL")
                return "AWAITING_APPROVAL"  # Durable return, no next action in batch.
            if task["spent"] + action.cost > task["budget"]:
                db.execute("UPDATE ledger SET status='BUDGET_EXHAUSTED' WHERE key=?", (action.key,))
                self.update_after_effect(db, "BUDGET_EXHAUSTED")
                return "BUDGET_EXHAUSTED"
            db.execute("UPDATE task SET spent=spent+?, state='ACTIVE'", (action.cost,))
            db.execute("UPDATE ledger SET status='EXECUTING' WHERE key=?", (action.key,))
            self.update_after_effect(db, "WAITING_FOR_EFFECT")
            self.event(db, "EXECUTE_RESERVED", action.key)
        # Runtime claim and target transaction intentionally NOT one transaction.
        try:
            receipt = self.target.execute(action, lose_receipt=lose_receipt)
            valid = receipt.get("key") == action.key and receipt.get("binding") == action.binding
            status = "COMMITTED" if valid and receipt.get("status") == "COMMITTED" else "UNKNOWN"
        except Exception as exc:
            status = "UNKNOWN"
            with transaction(self.path) as db:
                self.event(db, "RECEIPT_ERROR", type(exc).__name__)
        with transaction(self.path) as db:
            status = self.record_effect_result(db, action.key, status)
            self.update_after_effect(db, "VERIFYING" if status == "COMMITTED" else "NEEDS_RECONCILIATION")
            self.event(db, status, action.key)
        return status

    def approve(self, key, binding):
        # Approval authentication is an explicit external precondition in this model.
        with transaction(self.path) as db:
            state = db.execute("SELECT state FROM task").fetchone()[0]
            if state in {"CANCELLING", "CANCELLED", "COMPLETE"}:
                return state
            row = db.execute("SELECT * FROM ledger WHERE key=?", (key,)).fetchone()
            if not row or row["binding"] != binding or row["status"] != "AWAITING_APPROVAL":
                raise ValueError("APPROVAL_BINDING_CONFLICT")
            db.execute("UPDATE ledger SET approved=1 WHERE key=?", (key,))
            self.event(db, "APPROVAL_RECEIVED", key)
        return "READY_FOR_REAUTHORIZATION"

    def batch(self, actions, policy):
        results = []
        for action in actions:
            result = self.submit(action, policy)
            results.append(result)
            if result not in {"COMMITTED", "DENIED"}:
                break
        return results

    def reconcile(self, action, mode="fresh"):
        with transaction(self.path) as db:
            row = db.execute("SELECT * FROM ledger WHERE key=?", (action.key,)).fetchone()
            if not row or row["binding"] != action.binding:
                raise ValueError("RECONCILIATION_BINDING_CONFLICT")
            if row["status"] == "COMMITTED":
                return "COMMITTED"
            if row["status"] not in {"UNKNOWN", "EXECUTING"}:
                return row["status"]
        try:
            evidence = self.target.lookup(action, mode)
        except Exception:
            evidence = None
        confirmed = bool(evidence and evidence.get("authoritative") and evidence.get("fresh")
                         and evidence.get("key") == action.key and evidence.get("binding") == action.binding
                         and evidence.get("status") == "COMMITTED")
        status = "COMMITTED" if confirmed else "UNKNOWN"
        with transaction(self.path) as db:
            status = self.record_effect_result(db, action.key, status)
            self.update_after_effect(db, "VERIFYING" if status == "COMMITTED" else "NEEDS_RECONCILIATION")
            self.event(db, "RECONCILE_" + status, action.key)
        return status  # NEVER executes; ABSENT also needs operator resolution here.

    @staticmethod
    def record_effect_result(db, key, status):
        # Conditional write under BEGIN IMMEDIATE: late observations cannot demote
        # COMMITTED. Re-read on a lost race and return the durable winner.
        db.execute("UPDATE ledger SET status=? WHERE key=? AND status IN ('EXECUTING','UNKNOWN')",
                   (status, key))
        return db.execute("SELECT status FROM ledger WHERE key=?", (key,)).fetchone()[0]

    @staticmethod
    def update_after_effect(db, state):
        task = db.execute("SELECT state,cancel_requested FROM task").fetchone()
        if task["state"] in {"CANCELLED", "COMPLETE"}:
            return
        statuses = {r[0] for r in db.execute("SELECT status FROM ledger")}
        if task["cancel_requested"]:
            state = "CANCELLING" if statuses & {"UNKNOWN", "EXECUTING"} else "CANCELLED"
        elif "UNKNOWN" in statuses:
            state = "NEEDS_RECONCILIATION"
        elif "EXECUTING" in statuses:
            state = "WAITING_FOR_EFFECT"
        elif "AWAITING_APPROVAL" in statuses:
            state = "AWAITING_APPROVAL"
        elif "BUDGET_EXHAUSTED" in statuses:
            state = "BUDGET_EXHAUSTED"
        elif "COMMITTED" in statuses and state not in {"COMPLETE", "VERIFICATION_FAILED"}:
            state = "VERIFYING"
        db.execute("UPDATE task SET state=?", (state,))

    def recover(self):
        with transaction(self.path) as db:
            state = db.execute("SELECT state FROM task").fetchone()[0]
            if state in {"CANCELLED", "COMPLETE"}:
                return state
            db.execute("UPDATE ledger SET status='UNKNOWN' WHERE status='EXECUTING'")
            self.update_after_effect(db, state)
            return db.execute("SELECT state FROM task").fetchone()[0]

    def cancel(self):
        with transaction(self.path) as db:
            db.execute("UPDATE task SET cancel_requested=1 WHERE state!='COMPLETE'")
            self.update_after_effect(db, "CANCELLED")
            self.event(db, "CANCEL_REQUESTED_NO_NEW_WORK", "unknown effects must reconcile before terminal")

    def complete(self, checks):
        with transaction(self.path) as db:
            state = db.execute("SELECT state FROM task").fetchone()[0]
            if state in {"CANCELLING", "CANCELLED", "COMPLETE"}:
                return state
            statuses = {r[0] for r in db.execute("SELECT status FROM ledger")}
            if statuses & {"UNKNOWN", "EXECUTING", "AWAITING_APPROVAL"}:
                self.update_after_effect(db, state)
                return db.execute("SELECT state FROM task").fetchone()[0]
            # A denied proposal is an audited no-effect outcome, not a required
            # business effect. Other unfinished/failed states remain blockers.
            passed = bool(checks and all(v is True for v in checks.values())
                          and "COMMITTED" in statuses and statuses <= {"COMMITTED", "DENIED"})
            status = "COMPLETE" if passed else "VERIFICATION_FAILED"
            db.execute("UPDATE task SET state=?", (status,))
            self.event(db, status, json.dumps(checks))
            return status

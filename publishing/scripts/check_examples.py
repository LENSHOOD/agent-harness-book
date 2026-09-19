#!/usr/bin/env python3
"""Current-manuscript structural/schema regression gate. 0=pass; 1=regression.

Executes the separate reference suite only when requested by the entry point;
this checker parses actual fences and schemas, never historical B-number copies.
"""
import argparse
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "examples"))
from src.manuscript import fences, function_source, appendix_loop_source
from src.extended_manuscript import additional_sources


def check(root=ROOT):
    import yaml
    from jsonschema import Draft202012Validator

    checks, failures = [], []

    def record(name, passed, detail=None):
        item = {"name": name, "passed": bool(passed)}
        if detail is not None:
            item["detail"] = detail
        checks.append(item)
        if not passed:
            failures.append(name)

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("DUPLICATE_KEY: " + str(key))
            result[key] = value
        return result

    class UniqueSafeLoader(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        loader.flatten_mapping(node)
        return unique_pairs((loader.construct_object(k, deep=deep), loader.construct_object(v, deep=deep))
                            for k, v in node.value)
    UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)

    blocks = fences(root)
    structured, schemas = [], []
    for block in blocks:
        if block["language"] not in {"json", "yaml", "yml"}:
            continue
        label = block["file"] + ":" + str(block["line"])
        try:
            value = (json.loads(block["raw"], object_pairs_hook=unique_pairs,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
                     if block["language"] == "json" else list(yaml.load_all(block["raw"], Loader=UniqueSafeLoader)))
            record("parse:" + label, True)
            structured.append({k: block[k] for k in ("file", "line", "language", "sha256")})
            if block["file"].endswith("E_machine_readable_contracts.md") and isinstance(value, dict) and "$schema" in value:
                Draft202012Validator.check_schema(value)
                schemas.append((block, value))
        except Exception as exc:
            record("parse:" + label, False, str(exc))
    # Also parse standalone machine-readable manuscript and checked-in fixture inputs.
    for folder in (root / "manuscript", root / "examples/src", root / "examples/tests"):
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() not in {".json", ".yaml", ".yml"}:
                continue
            try:
                raw = path.read_text(encoding="utf-8")
                if path.suffix == ".json":
                    json.loads(raw, object_pairs_hook=unique_pairs)
                else:
                    list(yaml.load_all(raw, Loader=UniqueSafeLoader))
                record("parse-file:" + str(path.relative_to(root)), True)
            except Exception as exc:
                record("parse-file:" + str(path.relative_to(root)), False, str(exc))
    record("structured_blocks_present", bool(structured))
    task_schemas = [(b, s) for b, s in schemas if s.get("title") == "Task"]
    message_schemas = [(b, s) for b, s in schemas if "Action" in s.get("$defs", {})]
    record("unique_current_Task_schema", len(task_schemas) == 1)
    record("unique_current_message_schema", len(message_schemas) == 1)

    def probe(validator, name, instance, valid):
        errors = [e.message for e in validator.iter_errors(instance)]
        record(name, bool(errors) != valid, {"expected": "accept" if valid else "reject", "errors": errors})

    if len(task_schemas) == 1:
        task = {"task_id": "t1", "tenant": "tenant-1", "contract_version": "v1", "risk": "R2",
                "deliverables": ["report"], "checks": ["check-v1"], "commit_authority": "human-reviewer",
                "budget": {"wall_seconds": 60, "model_usd": 0, "max_actions": 2}}
        validator = Draft202012Validator(task_schemas[0][1])
        probe(validator, "Task_valid", task, True)
        for field in ("input_refs", "deliverables", "invariants", "forbidden_actions", "checks"):
            for bad in ("", " \t\n"):
                probe(validator, f"Task_{field}_{repr(bad)}_rejected", {**task, field: [bad]}, False)
        probe(validator, "Task_unknown_budget_field_rejected", {**task, "budget": {"unlimited": True}}, False)
        probe(validator, "Task_negative_budget_rejected", {**task, "budget": {"model_usd": -1}}, False)
        for field in ("task_id", "tenant", "contract_version", "commit_authority"):
            probe(validator, "Task_empty_" + field, {**task, field: ""}, False)
            probe(validator, "Task_blank_" + field, {**task, field: " \t\n"}, False)
    if len(message_schemas) == 1:
        schema = message_schemas[0][1]
        record("message_root_explicit_Action_ref", schema.get("$ref") == "#/$defs/Action")
        root_validator = Draft202012Validator(schema)
        for i, value in enumerate((None, {}, "arbitrary text", [])):
            probe(root_validator, "Definitions_root_rejects_invalid_" + str(i), value, False)
        validators = {}
        for name in ("Action", "PolicyDecision", "Observation"):
            # Apply a real $ref: do not validate against a bare definitions container.
            selected = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": "#/$defs/" + name}
            Draft202012Validator.check_schema(selected)
            validators[name] = Draft202012Validator(selected)
        action = {"action_id": "a1", "attempt_id": "attempt-1", "actor": "reference",
                  "type": "write", "resource": "account/one", "side_effect_class": "IRREVERSIBLE",
                  "normalized_args_ref": "sha256:fixture-args", "idempotency_key": "tenant-resource-key"}
        probe(root_validator, "Action_valid_via_root_ref", action, True)
        for side_effect in ("REVERSIBLE", "COMPENSATABLE", "IRREVERSIBLE"):
            for field in ("normalized_args_ref", "idempotency_key"):
                bad = {**action, "side_effect_class": side_effect}
                del bad[field]
                probe(validators["Action"], f"Action_{side_effect}_requires_{field}", bad, False)
        for field in action:
            probe(validators["Action"], "Action_empty_" + field, {**action, field: ""}, False)
            probe(validators["Action"], "Action_blank_" + field, {**action, field: "  "}, False)
        read_action = {k: v for k, v in action.items() if k not in {"normalized_args_ref", "idempotency_key"}}
        probe(validators["Action"], "Action_read_only_valid", {**read_action, "side_effect_class": "NONE"}, True)
        policy = {"action_id": "a1", "decision": "ALLOW", "policy_version": "p1"}
        for decision in ("ALLOW", "DENY"):
            probe(validators["PolicyDecision"], "Policy_" + decision, {**policy, "decision": decision}, True)
        for decision, field, value in (("CONSTRAINED_ALLOW", "constraints", {"resource": "account/one"}),
                                       ("REQUIRE_APPROVAL", "approval_request_id", "approval-1")):
            base = {**policy, "decision": decision}
            probe(validators["PolicyDecision"], decision + "_valid", {**base, field: value}, True)
            probe(validators["PolicyDecision"], decision + "_requires_" + field, base, False)
            probe(validators["PolicyDecision"], decision + "_empty_" + field, {**base, field: {} if isinstance(value, dict) else ""}, False)
        for status in ("OK", "DENIED", "ERROR", "TIMEOUT", "UNKNOWN_EFFECT", "CANCELLED", "PENDING"):
            probe(validators["Observation"], "Observation_" + status, {"action_id": "a1", "status": status}, True)
        probe(validators["Observation"], "Observation_invalid_status", {"action_id": "a1", "status": "BUSINESS_COMPLETE"}, False)

    protocols = {}
    for name in ("run_turn", "attempt_completion", "commit_effect_safely", "recover", "cancel"):
        try:
            source, metadata = function_source(blocks, name)
            ast.parse(source)
            protocols[name] = metadata
            record("current_protocol:" + name, True)
        except Exception as exc:
            record("current_protocol:" + name, False, str(exc))
    try:
        source, metadata, name = appendix_loop_source(blocks)
        protocols[name] = metadata
        record("current_protocol:appendix_run_loop", True)
    except Exception as exc:
        record("current_protocol:appendix_run_loop", False, str(exc))
    try:
        for name, (source, metadata) in additional_sources(blocks).items():
            protocols[name] = metadata
            record("current_protocol:" + name, True)
    except Exception as exc:
        record("current_protocol:chapter_1_11_20", False, str(exc))
    for relative in ("examples/run_examples.py", "examples/README.md", "requirements-examples.txt"):
        record("entry_exists:" + relative, (root / relative).is_file())
    for prefix in ("A_core_contracts", "25_three_end"):
        matches = [p for p in (root / "manuscript").rglob(prefix + "*.md")]
        record("entry_documented:" + prefix, len(matches) == 1 and "examples/run_examples.py" in matches[0].read_text())
    return {"kind": "current manuscript parse/schema/reference protocol gate; not production certification",
            "exit_code": int(bool(failures)), "checks": checks, "failures": failures,
            "structured_blocks": structured, "protocols": protocols,
            "literal_control_flow_execution": "examples/tests/test_manuscript_flow.py via examples/run_examples.py"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--skip-flow-tests", action="store_true",
                        help="Entry point already ran the literal-flow tests; check structure/schema only")
    args = parser.parse_args()
    try:
        result = check()
        if not args.skip_flow_tests:
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
            flow = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                   str(ROOT / "examples/tests/test_manuscript_flow.py"),
                                   str(ROOT / "examples/tests/test_manuscript_additional_flow.py")],
                                  cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
            result["literal_flow_run"] = {"exit_code": flow.returncode, "stdout": flow.stdout, "stderr": flow.stderr}
            if flow.returncode:
                result["failures"].append("current_literal_flow_regression")
                result["exit_code"] = 1
    except Exception as exc:
        result = {"exit_code": 1, "failures": [f"{type(exc).__name__}: {exc}"]}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"exit_code": result["exit_code"], "checks": len(result.get("checks", [])),
                      "literal_flow_exit": result.get("literal_flow_run", {}).get("exit_code"),
                      "failures": result["failures"]}, ensure_ascii=False))
    return result["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())

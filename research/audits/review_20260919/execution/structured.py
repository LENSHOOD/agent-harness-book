import copy
import json
import yaml
from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import NoSuchResource
from inventory import get_block


def no_network(uri):
    raise NoSuchResource(ref=uri)


def no_duplicate_json(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


class UniqueSafeLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for kn, vn in node.value:
        key = loader.construct_object(kn, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key}")
        result[key] = loader.construct_object(vn, deep=deep)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def parse_all(a):
    parsed = {}
    for b in a.inv["blocks"]:
        if b["language"] not in {"json", "yaml"}:
            continue
        def parse():
            if b["language"] == "json":
                return json.loads(b["raw"], object_pairs_hook=no_duplicate_json,
                                  parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
            return yaml.load(b["raw"], Loader=UniqueSafeLoader)
        value, error = a.attempt(f'parse_{b["id"]}', parse, sources=[b["id"]], model="raw_parse")
        parsed[b["id"]] = {"value": value, "error": error, "runtime_verified": False}
    return parsed


def schemas(a):
    task_block = get_block(a.inv, "E_", 1, "json")
    defs_block = get_block(a.inv, "E_", 2, "json")
    task, defs = json.loads(task_block["raw"]), json.loads(defs_block["raw"])
    for b, schema in [(task_block, task), (defs_block, defs)]:
        a.attempt(f'metaschema_{b["id"]}', lambda s=schema: Draft202012Validator.check_schema(s),
                  sources=[b["id"]], model="schema_only")
    validators = {"Task": Draft202012Validator(task, registry=Registry(retrieve=no_network)),
                  "DefinitionsRoot": Draft202012Validator(defs, registry=Registry(retrieve=no_network))}
    for name in defs["$defs"]:
        selected = {**defs, "$ref": f"#/$defs/{name}"}
        validators[name] = Draft202012Validator(selected, registry=Registry(retrieve=no_network))
    cases = []

    def probe(name, schema_name, instance, should_accept, *, gap=False):
        errors = [{"path": list(e.path), "schema_path": list(e.schema_path), "message": e.message}
                  for e in validators[schema_name].iter_errors(instance)]
        accepted = not errors
        source = task_block["id"] if schema_name == "Task" else defs_block["id"]
        detail = {"schema": schema_name, "instance": instance, "accepted": accepted,
                  "should_accept_for_probe": should_accept, "validation_errors": errors}
        cases.append({"name": name, **detail})
        a.check(name, accepted == should_accept, sources=[source], model="schema_only", details=detail,
                expected_failure=gap, severity="P1" if schema_name == "DefinitionsRoot" else "P2")

    valid_task = {"task_id": "T1", "tenant": "local", "contract_version": "v1", "risk": "R2",
                  "deliverables": ["patch"], "checks": ["hidden_dst"], "commit_authority": "human"}
    probe("Task_valid", "Task", valid_task, True)
    for key in task["required"]:
        invalid = copy.deepcopy(valid_task)
        invalid.pop(key)
        probe(f"Task_missing_{key}", "Task", invalid, False)
    for key, value in [("risk", "R5"), ("task_id", ""), ("checks", []), ("deliverables", []),
                       ("tenant", 1), ("extra", True), ("budget", {"max_actions": 0}),
                       ("budget", {"wall_seconds": 0}), ("budget", {"model_usd": -1}),
                       ("budget", {"max_actions": True})]:
        probe(f"Task_invalid_{key}_{len(cases)}", "Task", {**valid_task, key: value}, False)
    probe("Task_empty_check_string_rejected", "Task", {**valid_task, "checks": [""]}, False, gap=True)
    probe("Task_unknown_budget_field_rejected", "Task", {**valid_task, "budget": {"wall_minutes": 30}}, False, gap=True)
    action = {"action_id": "a1", "attempt_id": "attempt1", "actor": "stub", "type": "send",
              "resource": "local-simulator", "side_effect_class": "IRREVERSIBLE", "idempotency_key": "k1"}
    policy = {"action_id": "a1", "decision": "ALLOW", "policy_version": "v1"}
    observation = {"action_id": "a1", "status": "OK"}
    for name, obj in [("Action", action), ("PolicyDecision", policy), ("Observation", observation)]:
        probe(name + "_valid", name, obj, True)
        for field in defs["$defs"][name]["required"]:
            missing = dict(obj)
            del missing[field]
            probe(name + "_missing_" + field, name, missing, False)
    probe("Action_invalid_side_effect", "Action", {**action, "side_effect_class": "SEND"}, False)
    probe("Policy_invalid_decision", "PolicyDecision", {**policy, "decision": "MAYBE"}, False)
    probe("Observation_invalid_status", "Observation", {**observation, "status": "PASS"}, False)
    for i, obj in enumerate([{}, None, "not an Action", 123]):
        probe(f"Definitions_root_rejects_invalid_{i}", "DefinitionsRoot", obj, False, gap=True)
    without_key = dict(action)
    del without_key["idempotency_key"]
    probe("Irreversible_requires_idempotency_key", "Action", without_key, False, gap=True)
    probe("Action_empty_id_rejected", "Action", {**action, "action_id": ""}, False, gap=True)
    probe("Constrained_allow_requires_constraints", "PolicyDecision",
          {**policy, "decision": "CONSTRAINED_ALLOW"}, False, gap=True)
    # Compatibility probes, not an assertion that domain contracts claim to be Task instances.
    cross = []
    for b in a.inv["blocks"]:
        if b["language"] == "json" and "25_" in b["file"]:
            obj = json.loads(b["raw"])
            errors = [e.message for e in validators["Task"].iter_errors(obj)]
            cross.append({"source": b["id"], "accepted_as_Task": not errors, "errors": errors,
                          "interpretation": "Domain contract/evidence is not a Task wire instance; explicit adapter needed."})
    return {"validator": "jsonschema.Draft202012Validator", "network": "disabled; local metaschemas only",
            "cases": cases, "cross_contract_compatibility": cross,
            "limitations": "Schema shape only; synthetic instances clearly separated from original manuscript JSON. E YAML is a skeleton, not JSON Schema."}

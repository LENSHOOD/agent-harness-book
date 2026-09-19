"""Validate current wire schema before adapting optional fields for internal code."""
from copy import deepcopy
from types import SimpleNamespace
from jsonschema import Draft202012Validator


class PolicyDecoder:
    def __init__(self, message_schema):
        schema = {"$schema": message_schema["$schema"], "$defs": message_schema["$defs"],
                  "$ref": "#/$defs/PolicyDecision"}
        Draft202012Validator.check_schema(schema)
        self.validator = Draft202012Validator(schema)

    def __call__(self, wire):
        self.validator.validate(wire)
        internal = deepcopy(wire)
        internal.setdefault("reason_code", "POLICY_NO_REASON")
        internal.setdefault("constraints", {})
        return SimpleNamespace(**internal)

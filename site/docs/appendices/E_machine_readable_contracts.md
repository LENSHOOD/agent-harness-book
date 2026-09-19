# 附录 E：最小机器可读契约

下面的JSON Schema是教学子集，展示如何检查对象形状。字段名与附录A一致；平台仍需定义兼容规则、分类、签名与可信验证方。真实正反实例由`python publishing/scripts/check_examples.py`校验。JSON能解析不等于实例符合schema，实例符合schema也不等于获得授权。

## 1. Task 与 CompletionContract

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.internal/harness/task-v1.schema.json",
  "title": "Task",
  "type": "object",
  "additionalProperties": false,
  "required": ["task_id", "tenant", "contract_version", "risk", "deliverables", "checks", "commit_authority"],
  "properties": {
    "task_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
    "tenant": {"type": "string", "minLength": 1, "pattern": "\\S"},
    "contract_version": {"type": "string", "minLength": 1, "pattern": "\\S"},
    "risk": {"enum": ["R0", "R1", "R2", "R3", "R4"]},
    "input_refs": {"type": "array", "items": {"type": "string", "minLength": 1, "pattern": "\\S"}},
    "deliverables": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1, "pattern": "\\S"}},
    "invariants": {"type": "array", "items": {"type": "string", "minLength": 1, "pattern": "\\S"}},
    "forbidden_actions": {"type": "array", "items": {"type": "string", "minLength": 1, "pattern": "\\S"}},
    "checks": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1, "pattern": "\\S"}},
    "budget": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "wall_seconds": {"type": "integer", "minimum": 1},
        "model_usd": {"type": "number", "minimum": 0},
        "max_actions": {"type": "integer", "minimum": 1}
      }
    },
    "commit_authority": {"type": "string", "minLength": 1, "pattern": "\\S"}
  }
}
```

## 2. Action、PolicyDecision 与 Observation

第二份schema的根明确引用Action，因此用根验证`null`或空对象会失败。校验另外两种对象时，用同一份`$defs`构造分别指向`#/$defs/PolicyDecision`或`#/$defs/Observation`的schema。只保留`$defs`却不应用任何`$ref`，会成为允许任意根实例的定义集合，不能作为消息验证器。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Action with shared message definitions",
  "$ref": "#/$defs/Action",
  "$defs": {
    "Action": {
      "type": "object",
      "additionalProperties": false,
      "required": ["action_id", "attempt_id", "actor", "type", "resource", "side_effect_class"],
      "properties": {
        "action_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "attempt_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "actor": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "type": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "normalized_args_ref": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "resource": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "side_effect_class": {"enum": ["NONE", "REVERSIBLE", "COMPENSATABLE", "IRREVERSIBLE"]},
        "idempotency_key": {"type": "string", "minLength": 1, "pattern": "\\S"}
      },
      "if": {"properties": {"side_effect_class": {"not": {"const": "NONE"}}}, "required": ["side_effect_class"]},
      "then": {"required": ["normalized_args_ref", "idempotency_key"]}
    },
    "PolicyDecision": {
      "type": "object",
      "additionalProperties": false,
      "required": ["action_id", "decision", "policy_version"],
      "properties": {
        "action_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "decision": {"enum": ["ALLOW", "DENY", "REQUIRE_APPROVAL", "CONSTRAINED_ALLOW"]},
        "policy_version": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "reason_code": {"type": "string"},
        "constraints": {"type": "object", "minProperties": 1},
        "approval_request_id": {"type": "string", "minLength": 1, "pattern": "\\S"}
      },
      "allOf": [
        {"if": {"properties": {"decision": {"const": "CONSTRAINED_ALLOW"}}, "required": ["decision"]}, "then": {"required": ["constraints"]}},
        {"if": {"properties": {"decision": {"const": "REQUIRE_APPROVAL"}}, "required": ["decision"]}, "then": {"required": ["approval_request_id"]}}
      ]
    },
    "Observation": {
      "type": "object",
      "additionalProperties": false,
      "required": ["action_id", "status"],
      "properties": {
        "action_id": {"type": "string", "minLength": 1, "pattern": "\\S"},
        "status": {"enum": ["OK", "DENIED", "ERROR", "TIMEOUT", "UNKNOWN_EFFECT", "CANCELLED", "PENDING"]},
        "structured_result": {},
        "artifact_refs": {"type": "array", "items": {"type": "string"}},
        "diagnostics": {"type": "object"},
        "environment_revision": {"type": "string"}
      }
    }
  }
}
```

## 3. EvidencePackage 必填骨架

以下YAML是字段说明，不是已经验收的实例；`required`、`sha256-required`和`PASS|FAIL|INCONCLUSIVE`必须由真实值替换。它没有冒充JSON Schema，运行入口只做格式解析。若要接入服务，还需为证据包制定单独schema，并验证引用、访问权、签署人及产物一致性。

```yaml
evidence_package:
  schema_version: evidence-package/v1
  package_id: required
  task:
    task_id: required
    contract_version: required
  attempt:
    attempt_id: required
    runtime: required
    runtime_version: required
    harness_profile: required
  inputs:
    - uri: required
      hash: sha256-required
  candidate:
    uri: required
    hash: sha256-required
  effects: []
  policy_decisions:
    artifact_ref: required
  verification:
    verifier_version: required
    environment_ref: required
    status: PASS|FAIL|INCONCLUSIVE
    checks: []
  approvals: []
  final_commit: null
  lineage:
    parent_attempt: optional
    model_version: required
    harness_bundle: required
```

非空幂等键只便于表达逻辑动作身份，不会让下游自动去重；非空constraints也不证明执行器真的落实了约束。checks是否覆盖目标、hash对应哪个可信产物、批准是否来自有权主体，均由相应策略与验收服务检查。第25、27章的领域合同经adapter映射为Task，`contract_id`不能无转换地冒充`task_id`，分钟预算要先换算成秒。

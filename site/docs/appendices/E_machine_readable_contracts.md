# 附录 E：最小机器可读契约

下面的 JSON Schema 是教学用最小子集，用来展示如何把正文对象变成可校验的协议。生产环境的实现应拆分 schema、使用稳定 URI、补充 classification（分类）枚举、兼容规则和签名机制。不要把示例里的字段数量当作完整规范。

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
    "task_id": {"type": "string", "minLength": 1},
    "tenant": {"type": "string", "minLength": 1},
    "contract_version": {"type": "string", "minLength": 1},
    "risk": {"enum": ["R0", "R1", "R2", "R3", "R4"]},
    "input_refs": {"type": "array", "items": {"type": "string"}},
    "deliverables": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    "invariants": {"type": "array", "items": {"type": "string"}},
    "forbidden_actions": {"type": "array", "items": {"type": "string"}},
    "checks": {"type": "array", "minItems": 1, "items": {"type": "string"}},
    "budget": {
      "type": "object",
      "properties": {
        "wall_seconds": {"type": "integer", "minimum": 1},
        "model_usd": {"type": "number", "minimum": 0},
        "max_actions": {"type": "integer", "minimum": 1}
      }
    },
    "commit_authority": {"type": "string", "minLength": 1}
  }
}
```

## 2. Action、PolicyDecision 与 Observation

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$defs": {
    "Action": {
      "type": "object",
      "required": ["action_id", "attempt_id", "actor", "type", "resource", "side_effect_class"],
      "properties": {
        "action_id": {"type": "string"},
        "attempt_id": {"type": "string"},
        "actor": {"type": "string"},
        "type": {"type": "string"},
        "normalized_args_ref": {"type": "string"},
        "resource": {"type": "string"},
        "side_effect_class": {"enum": ["NONE", "REVERSIBLE", "COMPENSATABLE", "IRREVERSIBLE"]},
        "idempotency_key": {"type": "string"}
      }
    },
    "PolicyDecision": {
      "type": "object",
      "required": ["action_id", "decision", "policy_version"],
      "properties": {
        "action_id": {"type": "string"},
        "decision": {"enum": ["ALLOW", "DENY", "REQUIRE_APPROVAL", "CONSTRAINED_ALLOW"]},
        "policy_version": {"type": "string"},
        "reason_code": {"type": "string"},
        "constraints": {"type": "object"}
      }
    },
    "Observation": {
      "type": "object",
      "required": ["action_id", "status"],
      "properties": {
        "action_id": {"type": "string"},
        "status": {"enum": ["OK", "DENIED", "ERROR", "TIMEOUT", "UNKNOWN_EFFECT", "CANCELLED"]},
        "artifact_refs": {"type": "array", "items": {"type": "string"}},
        "diagnostics": {"type": "object"},
        "environment_revision": {"type": "string"}
      }
    }
  }
}
```

## 3. EvidencePackage 必填骨架

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

Schema 只能保证数据形状，不能单独证明语义正确。`checks` 是否覆盖业务目标、hash 指向的 artifact 是否可信、approval 是否来自有权主体，这些前提仍需 policy（策略）、verifier（校验器）和签名基础设施保证。

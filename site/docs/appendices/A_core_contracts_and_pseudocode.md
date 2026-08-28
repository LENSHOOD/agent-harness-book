# 附录 A：语言无关核心契约与安全伪代码

本附录给出语义接口，不要求所有 Runtime 使用同一种语言或序列化格式。平台可以用 JSON、protobuf 或数据库事件实现，但字段所有权与状态转换应保持一致。

## 1. 核心对象

```text
Task {
  id, tenant, contract_version, input_refs[], risk, budget,
  requested_by, commit_authority, status
}
Attempt {
  id, task_id, runtime, runtime_version, harness_profile,
  workspace_ref, policy_profile, started_at, status
}
Action {
  id, attempt_id, actor, type, normalized_args_ref,
  resource, side_effect_class, idempotency_key, provenance
}
Observation {
  action_id, status, structured_result, artifact_refs[],
  diagnostics, environment_revision
}
Artifact {
  uri, hash, media_type, producer, classification,
  input_refs[], created_at, retention_policy
}
PolicyDecision {
  action_id, decision, constraints, policy_version,
  reason_code, approval_request_id?
}
Checkpoint {
  attempt_id, state_version, event_offset, workspace_ref,
  pending_effect_ids[], context_projection_ref
}
VerificationResult {
  contract_version, verifier_version, checks[], status,
  evidence_refs[], environment_ref
}
EvidencePackage {
  task, attempt, inputs[], candidate, effects[], policies[],
  verification, approvals[], final_commit?, lineage
}
```

## 2. Run loop：proposal 不直接变成 effect

```text
while attempt.active:
    canonical_state = state_store.load(attempt.id)
    context = context_compiler.project(canonical_state, budget)
    proposal = model.decide(context, model_facing_tool_views)

    if proposal.requests_action:
        action = normalize_validate_and_assign_id(proposal.action)
        decision = policy.evaluate(action, current_authority)
        event_store.append(action, decision)

        if decision == DENY:
            observation = denied_observation(decision.reason)
        elif decision == REQUIRE_APPROVAL:
            suspend_attempt_with_checkpoint(action, decision)
            continue_after_external_response()
        else:
            observation = commit_effect_safely(action, decision.constraints)

        event_store.append(observation)
        state_store.reduce(observation)
        continue

    candidate = seal(proposal.output, canonical_state.artifacts)
    verification = completion_gate.verify(candidate, task.contract_version)
    if verification.status == PASS:
        return CANDIDATE_VERIFIED
    if verification.repairable and budget.remaining:
        state_store.reduce(minimal_diagnostics(verification))
    else:
        return NEEDS_ESCALATION
```

`DENY` 不调用 executor；`REQUIRE_APPROVAL` 在外部决定前挂起。模型输出无工具调用只表示提出 candidate，不表示业务已提交。

## 3. 副作用提交：先记 intent，再执行

```text
commit_effect_safely(action, constraints):
    effect = EffectIntent(
        effect_id = stable_id(action.id),
        idempotency_key = action.idempotency_key,
        target = action.resource,
        requested_operation = constrained(action, constraints),
        status = INTENT_RECORDED
    )
    durable_store.insert_if_absent(effect)

    prior = target_system.lookup(effect.idempotency_key)
    if prior.is_committed:
        outcome = observation_from(prior)
        durable_store.mark_committed(effect.id, outcome.ref)
        return outcome

    durable_store.mark_executing(effect.id)
    outcome = executor.execute(effect.requested_operation)

    if outcome.is_definitive:
        durable_store.mark_final(effect.id, outcome)
        return outcome

    durable_store.mark_unknown(effect.id)
    return Observation(status=UNKNOWN_EFFECT, diagnostics=reconcile_required)
```

存储 effect intent 后、调用目标系统前崩溃，恢复流程能找到待提交记录；目标系统已执行但 outcome 尚未持久化时崩溃，状态为未知，必须查询幂等键或外部审计，不得盲目重试。

## 4. 恢复、取消与对账

```text
recover(attempt_id):
    lease = coordinator.acquire_single_owner(attempt_id)
    checkpoint = state_store.latest_checkpoint(attempt_id)
    state = replay_pure_events(checkpoint.event_offset)

    for effect in state.pending_or_unknown_effects:
        authoritative = target_system.lookup(effect.idempotency_key)
        append_reconciliation_observation(effect, authoritative)

    policy = policy_store.load_current_compatible_version()
    credentials = broker.issue_fresh_leases(state.required_capabilities)
    resume_from_reconciled_state(state, policy, credentials)

cancel(attempt_id, reason):
    state_store.mark_cancel_requested(attempt_id, reason)
    scheduler.cancel_children(attempt_id)
    executor.terminate_process_tree(attempt_id)
    revoke_temporary_credentials(attempt_id)
    reconcile_pending_effects(attempt_id)
    state_store.mark_cancelled_when_quiescent(attempt_id)
```

恢复时不复用过期 credential，也不把 checkpoint 中旧授权当成当前授权。取消是一个需要收敛的状态，不是向 worker 发一条尽力而为的信号。

## 5. Adapter 的能力协商

```text
CapabilitySet {
  structured_events: yes/no
  pause_for_approval: yes/no
  resume: none/session/checkpoint
  cancel: cooperative/process_tree
  artifact_export: list of media types
  workspace_isolation: local/worktree/container/vm/provider
  raw_event_provenance: yes/no
}
```

Control Plane 依据 Task 风险声明要求；adapter 返回实际能力。若关键能力缺失，scheduler 选择替代 Runtime、降低自治范围或要求人工，不能把 `no` 转成空字段继续执行。

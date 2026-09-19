# 附录 A：语言无关核心契约与安全伪代码

本附录说明跨运行时的接口和控制流，不限定实现语言。代码块是带前置条件的设计伪代码；仓库中的`python examples/run_examples.py`提供本地可执行参考与正反测试。数据库、审批者和模型替身都写明了假设，不能把这些测试当成供应商端到端或生产安全认证。

## 1. 核心对象

这组对象用于明确跨 Runtime 的最小语义边界。平台可以增添字段，但不得把 Task、Attempt、Action、Effect 和 Evidence 混成一条聊天记录（chat log）。常见误用是只保存模型消息，再事后从自然语言猜测权限、输入版本和实际副作用。这样既不能安全恢复，也不能证明任务完成。

```text
Task {
  task_id, tenant, contract_version, input_refs[], risk, budget,
  requested_by, commit_authority, status
}
Attempt {
  attempt_id, task_id, runtime, runtime_version, harness_profile,
  workspace_ref, policy_profile, started_at, status
}
Action {
  action_id, attempt_id, actor, type, normalized_args_ref,
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

Attempt表示完成Task的一次执行尝试，不是每次工具网络重试。重试属于同一Action的ToolTry，沿用同一逻辑幂等键。会话Thread/Turn是供应商交互组织方式，由adapter显式映射到Task/Attempt。这里的字段名与附录E保持一致；领域合同仍需经过适配，不能直接视为Task对象。

## 2. Run loop：proposal 不直接变成 effect

这段循环用于实现平台可控的决策—授权—执行—验证骨架。供应商 Agent 可以占据 `model.decide`（模型决策接口），却不能绕过策略与 completion gate（完成门）。常见误用是把 `final answer` 当成成功，或让模型直接调用 executor（执行器）。这两种做法都会把“提出候选”和“获得外部提交权”混为一谈。

```text
while attempt.active:
    canonical_state = state_store.load(attempt.attempt_id)
    if canonical_state.cancel_requested:
        return cancel(attempt.attempt_id, USER_REQUEST)
    if budget.exhausted:
        return checkpoint_and_suspend(BUDGET_EXHAUSTED)
    context = context_compiler.project(canonical_state, budget)
    proposal = decide_with_reserved_model_budget(context, model_facing_tool_views)

    if proposal.requests_action:
        action = normalize_validate_and_assign_id(proposal.action)
        decision = decode_policy_decision(policy.evaluate(action, current_authority_and_revocations()))
        event_store.append(action, decision)

        if decision.decision == REQUIRE_APPROVAL:
            suspend_attempt_with_checkpoint(action, decision)
            return WAITING_FOR_APPROVAL
        if decision.decision not in {ALLOW, CONSTRAINED_ALLOW}:
            observation = denied_observation(action.action_id, decision.reason_code)
        elif not constraints_enforceable(action, decision):
            observation = denied_observation(action.action_id, CONSTRAINT_UNAVAILABLE)
        else:
            if not reserve_action_budget(action):
                return checkpoint_and_suspend(BUDGET_EXHAUSTED)
            try:
                observation = commit_effect_safely(action, decision.constraints)
            finally:
                settle_action_budget_from_meter(action)

        event_store.append(observation)
        state_store.reduce(observation)
        if observation.status == UNKNOWN_EFFECT:
            return RECONCILE_REQUIRED
        if observation.status == PENDING:
            return WAITING_FOR_EFFECT
        continue

    if proposal.requests_user_input:
        return WAITING_FOR_USER
    if not proposal.has_candidate:
        return TURN_STOPPED
    candidate = seal(proposal.output, canonical_state.artifacts)
    verification = completion_gate.verify(candidate, task.contract_version)
    if verification.status == PASS:
        return CANDIDATE_VERIFIED
    if verification.feedback_allowed and verification.repairable and budget.consume_repair_attempt():
        state_store.reduce(minimal_diagnostics(verification))
    else:
        return NEEDS_ESCALATION
```

审批分支保存待执行动作后立即返回，因此不会追加未赋值或上一轮残留的observation。恢复审批时校验批准人、action_id、参数hash、契约/资源版本、期限及撤销状态，再重新授权原动作；拒绝或过期就记录拒绝，不能把旧批准交给一个新动作。未知策略值也按拒绝处理。`commit_effect_safely`将已发送请求的预期执行异常转成结构化未知结果；意外故障由外层finally结算已用预算，进程崩溃则由持久预留账恢复结算，不能靠少记成本让循环无限继续。

无工具调用可能是提问、停止或候选交付。只有候选进入完成门；`CANDIDATE_VERIFIED`并不自动授予业务提交权。提交和后验遵循第十章。

`decode_policy_decision`是显式适配边界：先按附录E校验传输消息；合法但省略的reason_code在内部对象中补为稳定诊断码，普通ALLOW省略的constraints补为内部空集合。CONSTRAINED_ALLOW必须保留非空限制并确认可以落实。内部默认值不反向伪装成线上必填字段；测试应先校验真实消息，再走这条适配路径。无效消息默认不执行。

PENDING表示另一执行者持有动作，或尚不能取得决定是否执行所需的结果。顺序调用者保存待处理动作并返回WAITING_FOR_EFFECT，不能越过它执行依赖后续动作。UNKNOWN_EFFECT进入对账。两者都不自动转成新的幂等键或盲目重放；需要并行无依赖动作的实现，应另外表达依赖关系和局部暂停范围。

## 3. 副作用提交：先记 intent，再执行

以下参考要求目标系统支持**原子幂等键与参数绑定**：并发提交同一键只产生一个效果，相同键的不同参数被拒绝。幂等记录的保留期覆盖本平台的重试窗口。这些是目标API或业务唯一约束提供的能力，本地账本不能凭空补出。目标不支持这些条件时，应采用它能提供的事务/确认协议；未知结果升级处理，不复用这个例子承诺恰好执行一次。

```text
commit_effect_safely(action, constraints):
    tenant = trusted_tenant_for_attempt(action.attempt_id)
    key = scoped_key(tenant, action.resource, action.idempotency_key)
    args_hash = hash_normalized_operation(action, constraints)
    effect = durable_store.bind_intent_once(key, args_hash)
    lease = coordinator.try_claim_effect(effect.id)
    if lease is None:
        return Observation(action_id=action.action_id, status=PENDING)

    try:
        effect = durable_store.load(effect.id)
        if effect.is_final:
            return observation_from_recorded_outcome(action, effect)
        prior = target_system.lookup_or_unknown(key)
        if prior.is_committed_with(args_hash):
            return persist_reconciled_outcome(action, effect, prior)
        if effect.status in {EXECUTING, UNKNOWN_EFFECT}:
            return persist_unknown(action, effect, RECONCILE_REQUIRED)
        if prior.is_unavailable:
            return Observation(action_id=action.action_id, status=PENDING)

        # Check live cancellation/revocation after lookup, immediately before dispatch.
        if not still_authorized_and_active(action, constraints, lease):
            return persist_denied_outcome(action, effect)
        durable_store.mark_executing_if_owned(effect.id, lease.fence)
        try:
            outcome = target_system.execute_idempotently(key, args_hash, action, constraints)
        except ExecutionError as error:
            return persist_unknown(action, effect, diagnostic(error))
        if not outcome.is_definitive:
            return persist_unknown(action, effect, RECONCILE_REQUIRED)
        return persist_final_outcome(action, effect, outcome)
    finally:
        coordinator.release(lease)
```

`bind_intent_once`以租户、目标、逻辑键建立唯一记录并核对参数；重复调用不把旧状态重置为INTENT。`lookup_or_unknown`把查询故障变成不可确定；查无结果可能来自可见性延迟，不能据此重放遗留EXECUTING/UNKNOWN。执行租约减少重复worker，但迟到worker仍可能发请求，最后的去重保证必须由目标系统的原子键完成。撤销与发送若同时发生，仍需记录时间和实际提交结果，不能宣称取消回滚了已发送动作。

这里有意采用保守恢复：已开始发送而结果不明的记录，只回读已确认结果，否则停在对账状态。若业务需要自动恢复未生效请求，必须另外证明旧请求已经失效，或使用目标API明确保证的同键安全重放协议。不能把本例的PENDING/UNKNOWN直接当作可重试信号。

## 4. 恢复、取消与对账

长任务、子任务和外部副作用并存时，恢复与取消必须作为持久状态转换实现，而不是进程控制的附注。常见误用包括恢复旧 credential（凭证）、重复执行未知 effect，或在 UI 标记 cancelled 后仍让子进程继续运行。这些都会造成越权或重复提交。

```text
recover(attempt_id):
    lease = coordinator.acquire_single_owner(attempt_id)
    try:
        state = state_store.load(attempt_id)
        if state.is_terminal:
            return state.status
        if state.cancel_requested:
            return continue_cancellation_without_resuming_work(state)
        checkpoint = state_store.latest_checkpoint(attempt_id)
        state = replay_pure_events(checkpoint.state, checkpoint.event_offset)
        for effect in state.pending_or_unknown_effects:
            authoritative = target_system.lookup_or_unknown(effect.idempotency_key)
            append_reconciliation_observation(effect, authoritative)
        state = state_store.load(attempt_id)
        if state.is_terminal or state.cancel_requested:
            return state.status
        if state.has_unknown_effects:
            return RECONCILE_REQUIRED
        policy = policy_store.load_current_compatible_version_and_revocations()
        credentials = broker.issue_fresh_leases(allowed_capabilities(state, policy))
        return resume_from_reconciled_state(state, policy, credentials)
    finally:
        coordinator.release(lease)

cancel(attempt_id, reason):
    state_store.mark_cancel_requested(attempt_id, reason)
    scheduler.cancel_children(attempt_id)
    executor.terminate_process_tree(attempt_id)
    revoke_temporary_credentials(attempt_id)
    reconcile_pending_effects(attempt_id)
    return state_store.mark_cancelled_when_quiescent(attempt_id)
```

恢复从checkpoint的状态和事件偏移量一起重建，不只重放尾部事件。对账回写后重新加载状态，防止带着旧副本继续执行。恢复入口和最终resume都要以条件写入检查取消/终态，最新撤权优先于版本兼容。CANCELLED可以保留已发生的外部效果；若远端是否停止或是否提交仍不明，保持CANCELLING/待对账，不假装已经清理完毕。

操作系统进程树终止、远端作业取消、租约过期和崩溃恢复需要对具体后端另做测试。本地参考只能验证它实现的状态转移及SQLite目标约束，不能借这些helper名字声称全部后端已有同样保证。

## 5. Adapter 的能力协商

CapabilitySet 用于调度前比较任务风险需求与 Runtime 的真实能力，尤其适合同时接入 Claude Code、Codex 与自研 Runtime 的平台。它不是一张营销功能表。`no`（否）或未知能力必须导致替代 Runtime、收缩自治范围或人工升级，不能靠空字段伪装兼容。

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

Control Plane（控制平面）依据 Task 风险声明做能力检查，adapter（适配器）返回真实能力。若关键能力缺失，scheduler（调度器）应选择替代 Runtime、降低自治范围或要求人工审批，不能把 `no` 转成空字段继续执行。

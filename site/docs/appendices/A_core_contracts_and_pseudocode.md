# 附录 A：语言无关核心接口

```text
Task {id, tenant, contract_version, input_refs, risk, budget}
Action {id, actor, type, normalized_args, resource, provenance}
Observation {action_id, status, structured, artifact_refs, diagnostics}
Artifact {uri, hash, media_type, producer, classification}
Checkpoint {run_id, state_version, event_offset, pending_effects}
PolicyDecision {action_id, decision, constraints, policy_version}
VerificationResult {contract, checks, status, evidence_refs}
```

```text
while run.active:
    context = compiler.build(run.state, budget)
    proposal = model.decide(context, tool_views)
    if proposal.action:
        action = normalize_and_validate(proposal.action)
        decision = policy.evaluate(action)
        observation = executor.commit(action, decision)
        ledger.append(action, decision, observation)
        state.reduce(observation)
    else:
        candidate = seal(proposal.output, state.artifacts)
        return completion_gate.verify(candidate)
```

```text
recover(run_id):
    checkpoint = store.latest(run_id)
    replay_pure_events(checkpoint.offset)
    for effect in checkpoint.pending_effects:
        reconcile_by_idempotency_key(effect)
    resume_with_fresh_policy_and_credentials()
```

这些接口是语义合同，不要求所有 runtime 使用同一编程语言或序列化格式。

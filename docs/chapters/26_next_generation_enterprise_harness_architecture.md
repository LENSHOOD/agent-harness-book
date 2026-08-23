# 第二十六章 下一代企业 Harness 参考架构

参考架构的目标不是重新实现每个 coding agent，而是在 Claude Code、Codex、OpenHands、DSH 与未来自研 runtime 之上建立稳定控制面。

## 1. 六层结构

```text
Experience       IDE / Web / CLI / API / workflow
Control Plane    task contract / scheduler / identity / policy / approval
Agent Runtime    vendor adapter / loop / context / delegation
Execution Plane  workspace / sandbox / tool gateway / credential broker
Evidence Plane   artifacts / trace / verifier / effect ledger
Evolution Plane  eval registry / mutation / experiment / release / rollback
```

体验层不拥有任务真相；控制面生成 canonical task。Agent runtime 可替换。执行面负责真实副作用。证据面独立于聊天历史。进化面只能发布经门禁的版本。

## 2. Canonical contracts

平台至少定义 Task、Action、Observation、Artifact、PolicyDecision、Checkpoint、Delegation、VerificationResult 和 EvidencePackage。Vendor adapter 在 canonical event 与产品协议之间映射，保留原始 payload 引用以便诊断。

```text
RuntimeAdapter {
  capabilities()
  start(task, workspace, policy_profile)
  stream_events(run_id)
  approve_or_deny(request)
  checkpoint(run_id)
  cancel(run_id)
  collect_artifacts(run_id)
}
```

不要强求所有 runtime 暴露同样的内部 reasoning。统一可观察动作与结果即可。

## 3. 身份与租户

User、platform、runtime、subagent、tool 和 external service 都有独立身份。授权以 capability lease 表达，绑定租户、资源、动作和 TTL。Credential broker 在执行时注入短期凭证，模型不看到 secret。

## 4. Durable execution

Run state 持久化，工具副作用记录幂等键和 outcome。Worker 崩溃后从 checkpoint 恢复；对不确定外部结果先 reconcile。Scheduler 管理预算、优先级、并发和取消树。

## 5. Policy 与 sandbox

策略在 action commit 时评估，输出 allow、deny、approval 或 constrained allow。Sandbox 同时限制文件、网络、进程和资源。Policy profile 与 sandbox image 都版本化并进入证据包。

## 6. Evidence-first completion

Runtime 只能提交候选。Verifier service 在隔离环境运行完成契约，生成签名结果；commit controller 再执行外部提交。此边界使不同 runtime 可公平比较，也阻止供应商 Agent 自报完成。

## 7. 演进边界

Prompt、tool view、retriever、skill 和 workflow 可进入候选；identity root、policy root、held-out、审计与 release controller 不可由候选修改。所有版本组合进入 lineage registry。

## 8. 非功能要求

以租户隔离、可用性、恢复时间、trace 完整性、最大副作用、成本预算和数据驻留定义 SLO。Agent 成功率不是唯一 SLO；错误完成的代价通常远高于明确失败。

这套架构允许企业先集成现有 runtime，再逐步替换上下文、loop 或工具层，而无需重建治理与证据系统。

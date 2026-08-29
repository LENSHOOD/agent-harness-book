# 第二十六章 下一代企业 Harness 参考架构

> 证据地位：本章为作者参考设计与工程推导，案例和阈值用于说明实现逻辑，不代表跨组织验证的通用标准。

参考架构的目标不是重新实现每个 coding agent，而是在 Claude Code、Codex、Cursor、DeepSeek Harness、OpenHands 与未来自研 runtime 之上建立稳定控制面。它优化的是替换成本、责任边界和可信完成，不追求把所有产品压成最低共同功能。

## 1. 六层结构与权威状态

```text
Experience       IDE / Web / CLI / API / business workflow
Control Plane    task contract / scheduler / identity / policy / approval
Agent Runtime    vendor adapter / loop / context / delegation
Execution Plane  workspace / sandbox / tool gateway / credential broker
Evidence Plane   artifacts / trace / verifier / effect ledger
Evolution Plane  eval registry / mutation / experiment / release / rollback
```

体验层可以收集意图，不能拥有任务真相；控制面生成 canonical Task 并持久化状态。Agent Runtime 负责概率决策，可替换。Execution Plane 提交真实副作用。Evidence Plane 独立判断候选是否满足合同。Evolution Plane 消费脱敏、验证过的证据，只能通过 release controller 改变未来 profile。

在小团队低风险场景，六层可以部署在同一进程；分层是逻辑责任而非微服务数量。若任务只是只读代码解释，外部 verifier 可以很轻。若 Agent 可操作生产数据，即使系统规模小，也不能合并 policy root、credential broker 与模型上下文。

## 2. Canonical contracts 与能力协商

平台至少定义 Task、Action、Observation、Artifact、PolicyDecision、Checkpoint、Delegation、VerificationResult 和 EvidencePackage。adapter 在 canonical event 与产品协议之间映射，同时保存原始 payload 的 hash、位置和协议版本。

```text
RuntimeAdapter {
  negotiate(capability_requirements) -> CapabilitySet
  start(task, workspace, policy_profile) -> Attempt
  stream_events(attempt_id, after_offset)
  respond_to_request(request_id, approval_or_input)
  checkpoint(attempt_id)
  cancel(attempt_id, reason)
  collect_artifacts(attempt_id)
}
```

不要求 runtime 暴露私有 reasoning。统一动作、结果、批准、artifact 与生命周期即可。若某 runtime 不支持 resume 或结构化 diff，能力协商必须返回缺失，scheduler 决定降低自治风险、换 runtime 或要求人工，不得静默伪造支持。

## 3. 身份、租户与凭证

User、platform、runtime、subagent、tool 和 external service 都有独立身份。授权以 capability lease 表达，绑定租户、资源、动作、purpose 和 TTL。Credential broker 在执行时向受控工具注入短期凭证，模型与长期 trace 不出现 secret。

委派必须缩权：子 Agent 的能力集合不超过父任务授权，并进一步按子任务收窄。跨租户缓存、共享 memory 和 tool result 在进入 context compiler 前先做数据分类与隔离，不能依赖模型“不要泄漏”的指令。

## 4. Durable execution 与副作用

Run/Attempt state 持久化，事件有单调 offset，工具副作用记录 intent、idempotency key、policy decision 和 outcome。worker 崩溃后从 checkpoint 恢复；对于结果未知的外部调用先查询目标系统，不能直接重放（见第六章）。scheduler 管理预算、优先级、并发、deadline 和取消树。

反例是邮件工具超时后 runtime 自动 retry。第一封实际上已发送，第二次又成功，聊天里只看到一次“完成”。正确的 gateway 先以业务 idempotency key 查询发送状态，再决定返回旧结果、补偿或升级人工。

## 5. Evidence-first completion

Runtime 只能提交 candidate。Verifier service 在独立环境执行 completion contract，生成带 artifact hash 的 VerificationResult；commit controller 再执行合并、发送或部署。这样不同 runtime 可以在相同合同和环境下比较，也阻止供应商 Agent 自报完成。

EvidencePackage 是面向审计和重建的交付物，不是全量思维链。它连接输入版本、动作/效果、candidate、检查、策略、批准和外部 commit。敏感原始事件可按访问级别存放，摘要保留 provenance。

## 6. 七类 SLO：定义、测量和博弈

初始阈值必须由风险与历史基线决定，下面给的是定义方法而非通用目标值。

| SLO | 定义/测量点 | 初始设定方法 | 可能的指标博弈 |
|---|---|---|---|
| 可信完成率 | 通过独立 completion gate 的任务/合格任务 | 按任务族和风险建立基线 | 降低验收、排除困难任务 |
| 错误完成率 | 被宣布完成但后续证伪/总完成 | 从事故和抽检回标 | 延迟认定事故、隐藏返工 |
| 证据完整率 | 必填 evidence 字段齐全且 hash 可读/完成任务 | R3/R4 接近全覆盖，低风险可抽样 | 填充无意义日志满足字段 |
| 恢复成功率 | 中断后在预算内恢复且无重复 effect/恢复尝试 | 用 kill/restart 演练建立目标 | 只恢复容易任务 |
| 最大副作用 | 单次失控可影响的资源/金额/对象数 | 由业务 blast radius 反推 | 把一个动作拆成多个规避限额 |
| 单位可信完成成本 | 模型、计算、工具、人力总成本/可信完成 | 与当前人工流程比较 | 忽略复核与事故成本 |
| P95 完成时延 | 从合同冻结到完成门通过 | 按同步/异步任务分开 | 提前宣布完成、丢弃长尾 |

每个 SLO 要有 owner、采样口径、数据 lineage、告警和例外流程。平均值不能掩盖高风险租户或任务切片；安全违规采用严重度与事件数，不被平均成功率抵消。

## 7. 多 runtime 数据流

```text
request → contract compiler → scheduler → runtime adapter
   → policy-mediated tool gateway → sandbox/external systems
   → event + effect ledger → candidate seal
   → verifier → approval/commit → EvidencePackage
   → telemetry/eval → governed evolution release
```

最容易遗漏的是 adapter 之外的“旁路”：runtime 直接访问网络、插件自己持有 secret、UI 直接调用供应商 API。架构评审应画出实际数据流并验证所有副作用都经过控制点。

## 8. 构建顺序与替代方案

先建 contract、workspace、policy、artifact 和 verifier，再接多个 runtime；否则统一层只会统一聊天。若组织只有一个低风险 Agent，可先使用供应商 sandbox 与日志，不必立即建设六个独立服务，但要确保 task/evidence 数据可导出。规模扩大或进入高风险域后，再把 scheduler、credential broker、verifier 和 evolution service 独立扩展。

这套架构允许企业先集成现有 runtime，再逐步替换 context、tool view 或 loop，而无需重建治理与证据系统。下一章把“合同”进一步展开为规范驱动交付。

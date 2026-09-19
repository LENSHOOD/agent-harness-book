# 第六章 Agent Loop：从 while 循环到持久状态机

工具型 Agent 的主循环看起来通常可以用十几行伪代码写清。真正难处理的是执行中的故障，而不是那十几行正常路径。并行工具只完成一半时怎么办？用户在命令执行中取消怎么办？模型给出 final answer 就算结束吗？外部副作用提交后、结果还没落库进程就崩了怎么办？

需要跨进程恢复、审批或提交业务副作用的企业任务，应将这些状态持久化。短暂、无副作用、失败后可从头重算的任务可以使用内存循环，不必为了“企业级”统一增加一套数据库。

## 1. Thread、Turn、Step 与 Attempt

现代产品对术语并不完全一致。本书的业务执行单位如下；会话Thread是另一种组织方式，不是所有对象的唯一父节点：

```text
Task        一份完成契约下的业务任务
└── Attempt 使用特定运行时、版本和工作区完成该任务的一次尝试
    └── Turn/Step/Action  会话轮次、可观测阶段和具体动作
        └── ToolTry      同一逻辑动作的传输或工具重试

Thread      协作会话；可承载多个Turn，并映射到不同Task/Attempt
```

Codex 把用户输入到最终 assistant message 的过程称为 turn。其中可以包含多次模型推理和工具调用。[Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/) Claude Agent SDK 也循环执行“评估—工具—结果”，直到模型输出不含工具调用的响应，并返回包含 token、成本和 session id 的结果消息。[Claude Agent Loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)

这里的Attempt与附录A一致，表示任务的一次执行尝试。一次API超时后的传输重试记作ToolTry，不另建业务Attempt；它必须沿用同一逻辑动作的幂等键。模型改用了不同方案，则形成新Action，是否产生新业务操作还要由契约判断。分开这些身份后，系统才不会把“重发同一请求”误当成“允许再做一次”。

## 2. 最小状态机

下面是需要审批和恢复的任务尝试的一种状态模型。Turn结束是会话事件；图中验收与业务终态属于Task/Attempt，不能直接映射成供应商的turn/completed：

```text
CREATED
  ↓
ASSEMBLING_CONTEXT
  ↓
WAITING_FOR_MODEL
  ↓
DECIDING
  ├──→ WAITING_FOR_APPROVAL
  ├──→ EXECUTING_TOOL
  ├──→ WAITING_FOR_USER
  ├──→ COMPACTING
  └──→ VERIFYING
             ├──→ CANDIDATE_VERIFIED ─→ 按契约决定提交和后验
             ├──→ NEEDS_REPAIR ─→ ASSEMBLING_CONTEXT
             └──→ FAILED

任意活动状态 ─→ CANCELLING ─→ CANCELLED
任意活动状态 ─→ SUSPENDED ─→ 恢复点
```

`FAILED`、`CANCELLED` 和 `COMPLETED` 不能混写。用户取消不代表模型失败；预算耗尽也不代表业务目标不可达成；工具被拒绝可能是策略命中，不一定是技术问题。状态会直接决定能否重试、是否计费、如何告警，以及下次恢复时模型该看到什么。

## 3. 模型停止不等于任务完成

模型输出无 tool call 的 assistant message，通常结束当前 loop。但它可能只是提问、报告阻塞、拒绝任务，或错误地喊“完成”。

所以至少需要两个判定：

```text
model_stop       模型本轮不再请求动作
task_completion  外部完成契约已经满足
```

Harness 可按任务类型选择完成策略：

- 对话问答：final response 可能足够；
- 代码修改：要求工作区有预期 diff，并运行指定测试；
- 数据任务：要求产生可复现查询、结果和口径说明；
- 高风险业务动作：要求外部系统确认与审计事件；
- 研究任务：要求来源覆盖、引用验证和未知项披露。

开发检查或获准提供修复反馈的验证集失败时，系统可以回传结构化差异。密封终测失败则停止本轮选择，不把诊断直接喂回候选；若授权降级为开发材料，后续必须重新建立独立终测证据。

## 4. Streaming 是事件协议，不只是打字动画

长任务需要实时展示模型文本、工具请求、命令输出、审批和状态变化。若 streaming 只是不可恢复的 socket 文本，客户端断线后就无法判断哪些内容被遗漏。

建议每个流事件包含：

```text
event_id
thread_id / turn_id / step_id / attempt_id
sequence_or_cursor
event_type
timestamp
payload_ref
causation_id / correlation_id
schema_version
visibility_class
```

平台可让客户端通过cursor重连，由服务端重放已持久化事件；大载荷放对象存储，事件保留hash、类型和访问引用。需要另外声明哪些消息只是即时预览，哪些已落库：看到增量文本不等于崩溃后一定能重放。原始事件可以分别供模型、界面和审计使用，三者各自执行脱敏和访问控制。平台的游标保证也不能超过供应商实际导出的事件范围。

## 5. 取消必须贯穿调用链

用户点击停止后，仅停止下一次模型调用是不够的。正在运行的 shell、浏览器任务、subagent 和远程 job 可能继续带来副作用。

取消应沿所有权树传播：

```text
Turn cancellation
├── model request cancellation
├── active tool cancellation
│   ├── process group termination
│   └── remote job cancel request
├── child agent cancellation
└── pending approval invalidation
```

取消还有竞态。动作可能在取消信号到达前已提交。状态不能简单写成“cancelled, nothing happened”，而应记录 `cancel_requested_at`、`effect_committed_at` 和最终 reconciliation。对不可撤销动作，应返回“取消请求已接收，但动作已提交”。

## 6. Timeout、Retry、Resume 不是一回事

Timeout是放弃等待一次工具尝试或模型请求；Retry是重新尝试同一个逻辑动作；Resume是从持久状态恢复任务尝试。超时不撤销已经发出的请求，重试不产生新的业务授权，恢复也不是把旧凭证原样放回进程。

自动重试写动作前，需要确认它天然幂等，下游按同一幂等键原子去重，或权威证据确认前次未生效且以后也不可能再生效。本地账本里没有结果、一次查询暂时找不到记录，都不满足最后一项条件。

结果未知时先对账；无法确认时暂停并升级。补偿处理的是已经确认的错误效果，而且补偿也可能失败。重复扣款即便能退款，仍可能占用资金、发出通知或产生费用，因此“有退款接口”不是可以盲目再扣一次的理由。

AWS Durable Execution 文档把幂等定义为重复运行仍产生相同效果，并强调执行确认和 checkpoint 对重试语义的重要性。[Idempotency and Retries](https://docs.aws.amazon.com/durable-execution/patterns/best-practices/idempotency/)

模型请求可按策略重试，但每次输出不保证一致，已计费的尝试也不能从成本账中消失。只读调用通常可以重试，仍需考虑快照漂移、限流与读访问审计；发送邮件、付款和合并代码更不能仅因网络超时就重放。

## 7. 副作用账本与不确定提交

最危险的崩溃窗口是：外部动作已执行，但 Harness 尚未保存结果。

```text
persist INTENT
authorize exact action
execute external effect
persist OUTCOME
```

如果崩溃发生在第三步到第四步之间，恢复时只知道 intent，不知道 effect 是否发生。它不确定提交状态，不是通过再问模型一次就能修复。

副作用账本至少记录租户、目标、动作、参数hash、幂等键、授权版本、开始时间、下游请求ID和已知结果。相同键配不同参数应拒绝。账本的insert-if-absent只防重复记录，不会阻止两个worker都通过“查无结果”后执行；需要执行所有权与目标系统原子去重共同约束。

异常路径也属于协议。如果executor抛TimeoutError而不是返回一个timeout对象，调用者仍须把已经开始发送的动作记为UNKNOWN_EFFECT。若进程直接死亡而来不及记，恢复器把遗留EXECUTING当成未知效果。对下游不支持去重的系统，只有权威确认旧请求不再可能生效后才可重发；否则交给人工，不承诺跨系统exactly-once。

## 8. Checkpoint 应保存什么

仅保存聊天历史不足以恢复执行。Checkpoint 至少覆盖：

- 当前 thread/turn/step/attempt 状态；
- canonical task state 与未满足验收条件；
- 已装配上下文的版本或可重建引用；
- 模型、工具、技能、策略和环境版本；
- 已提交与未确定的副作用；
- 活动 child agent 和 remote job handle；
- budget 使用量与剩余额度；
- 当前 workspace snapshot/commit/image 标识。

Claude Code 把消息、工具调用和结果写入 JSONL，支持 resume、rewind 和 fork；这对个人会话很有效。[Claude Code Sessions](https://code.claude.com/docs/en/how-claude-code-works) 企业平台还需要数据库一致性、租户隔离、加密、保留策略和跨版本迁移。

## 9. Compaction 是有损状态迁移

上下文接近上限时，Claude SDK 与 Codex 都会压缩历史。Codex 强调缓存依赖精确前缀匹配，并尽量用追加消息表达中途配置变化；其服务端 compaction 会用较短 items 替代旧 input。[Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

压缩不是普通摘要，而是一次有损状态迁移。至少要保护：

- 用户目标和后续修订；
- 权限与安全约束；
- 已验证事实及来源；
- 未完成承诺和阻塞；
- workspace 关键变化；
- 失败尝试及不应重复的原因；
- 可重新发现原始记录的指针。

可采用两份职责不同的记录：模型上下文允许压缩，权威执行状态和原始证据保持独立。检查不能只发生在压缩前；新投影形成后，还要核对未完成工具调用的配对、契约与权限版本，以及关键信息能否重新检索，检查成功后才切换上下文。模型需要细节时从原记录重读。

## 10. Error Taxonomy 决定恢复策略

错误不应全部变成一段 tool result。建议至少分类：

| 类别 | 例子 | 默认策略 |
|---|---|---|
| Model transient | 限流、网断 | 退避重试/切换 |
| Model semantic | 无效工具参数 | 结构化反馈给模型 |
| Policy denied | 权限不足 | 记录拒绝；只有策略允许的升级路径才能再申请 |
| Tool transient | 服务超时 | 先判定有无未知效果，再按幂等条件重试 |
| Tool deterministic | 参数非法、文件不存在 | 修正输入 |
| Environment drift | 依赖/分支变化 | 重新观察或重建环境 |
| Verification failure | 检查失败 | 按数据用途决定修复或停止；终测反馈不用于本轮修复 |
| Budget exhausted | token/时间/费用耗尽 | 暂停并报告 |
| Unknown effect | 提交状态不明 | reconciliation/人工 |

错误类型应由确定性层尽量识别。让模型从任意 stderr 猜“要不要重试”，通常会引发 retry storm，并放大重复副作用。

## 11. 并行工具与一致性

模型可能一次请求多个工具。默认并行只适合互不影响的只读观察。多个写入若基于同一旧状态，容易产生冲突。

Harness 可在执行前计算 action footprint：读取集、写入集、外部目标、凭证域和工作区。若 footprint 重叠，则串行执行、隔离到不同 workspace，或用乐观并发控制并在提交时检查版本。

同理，多 Agent 并行不应共享未经协调的可变目录。Codex 使用 worktree 隔离不同线程，能把“任意文件覆盖”转成“显式合并”问题。

## 12. 一个更完整的循环伪代码

```text
function run_turn(turn_id):
    state = restore_or_create_state(turn_id)
    if terminal(state):
        return state.status

    while not terminal(state):
        if cancellation_requested(state):
            return cancel_and_reconcile(state)
        if budget_exhausted(state):
            return suspend_with_checkpoint(state, BUDGET_EXHAUSTED)

        if context_needs_compaction(state):
            projection = compact_model_view(state)
            validate_projection_against_canonical_state(projection, state)
            install_context_projection(projection)

        proposal = call_model_with_budget(build_context(state))
        persist(proposal)

        if proposal.requests_actions:
            for action in plan_execution(proposal.actions):
                state = refresh_state_and_revocations(state)
                if cancellation_requested(state):
                    return cancel_and_reconcile(state)
                if budget_exhausted(state):
                    return suspend_with_checkpoint(state, BUDGET_EXHAUSTED)
                validate_schema(action)
                decision = decode_policy_decision(authorize(action, state))
                if decision.decision == REQUIRE_APPROVAL:
                    persist_bound_approval_request(action, decision)
                    return WAITING_FOR_APPROVAL
                if decision.decision not in {ALLOW, CONSTRAINED_ALLOW}:
                    persist_denied_observation(action, decision)
                    continue
                if not constraints_enforceable(action, decision):
                    persist_denied_observation(action, CONSTRAINT_UNAVAILABLE)
                    continue
                reservation = reserve_action_budget_or_none(state, action)
                if reservation is None:
                    return suspend_with_checkpoint(state, BUDGET_EXHAUSTED)
                try:
                    outcome = execute_with_effect_ledger(action, decision)
                    persist_and_reduce(outcome)
                finally:
                    settle_actual_cost_and_release_unused(reservation)
                if outcome.status == UNKNOWN_EFFECT:
                    return RECONCILE_REQUIRED
                if outcome.status == PENDING:
                    return WAITING_FOR_EFFECT
            continue

        if proposal.requests_user_input:
            return WAITING_FOR_USER
        if not proposal.has_candidate:
            return TURN_STOPPED
        verification = evaluate_completion_contract(state, proposal)
        if verification.passed:
            return CANDIDATE_VERIFIED
        if not verification.feedback_allowed or not verification.repairable or not repair_budget_remaining(state):
            return BLOCKED_OR_ESCALATED
        append_structured_feedback_and_charge_attempt(verification)
```

这段伪代码的helper有明确责任：模型调用和工具调用都预留并结算预算；拒绝记录包含action_id；执行器在提交前再次检查已撤销授权，并将发送后异常变成未知效果。审批请求绑定参数、资源与契约版本；收到外部答复后恢复原待执行动作，重新授权，不让模型换一个动作套用旧批准。暂停分支直接返回，不能继续执行批次里的后续动作。`feedback_allowed`还要核对数据用途、实验族反馈余额和接收主体，密封终测固定为否。具体的副作用和恢复契约见附录A，最小可运行参考在仓库`examples/`。

## 13. 最小可靠性测试集

声称支持持久恢复的实现，应按自身能力执行以下故障测试。涉及浏览器、远端作业或多Agent的条目在实际启用这些能力时适用：

1. 模型返回工具调用后立即崩溃；
2. 工具已提交副作用、结果落库前崩溃；
3. 并行工具一个成功一个超时；
4. 等待审批时服务重启；
5. 用户取消与动作提交同时发生；
6. compaction 前后继续同一任务；
7. 恢复时模型、工具或策略版本已改变；
8. child agent 完成但 parent 丢失连接；
9. streaming 客户端断线后按 cursor 重连；
10. 相同 idempotency key 被并发提交。

只演示正常路径，无法支持崩溃恢复能力的结论。本书的本地参考验证了选定状态与故障模型；它不能代替针对实际进程、网络、供应商服务和存储后端的故障注入。

长任务应有独立于模型上下文的执行身份和可查询副作用记录。需要通过完成契约的是“任务成功”这一声明；提问、拒绝、预算耗尽和用户取消都可以结束本轮，但应保留真实状态。下一章讨论如何在这样的状态记录之上，为模型提供当前需要的信息。

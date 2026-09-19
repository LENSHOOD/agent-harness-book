# 第十一章 多 Agent、委派与协作拓扑

> 证据声明：原有产品资料截面为 2026-08-28，子代理上下文模式补至 2026-09-19 已抓取材料；架构原则为作者综合推断，厂商能力与论文结果不代表本书已实测。

多 Agent 是个名字很容易误导人的概念。把同一个模型调用五次，再给每次调用贴上“架构师”“开发者”“审查者”这样的标签，不会自动组成一个真实团队。一个真正的多 Agent 系统，必须先回答：任务为什么可以拆解、状态由谁持有、权限怎么衰减、冲突如何解决、结果由谁验收、故障如何隔离，以及新增成本是否换来了可量化收益。

这一章的核心判断是：**多 Agent 不是能力层面的默认升级，而是一种并发、隔离与治理机制。** 当任务可并行探索、需要不同上下文或信任边界、单一上下文放不下全部材料时，它可能显著提升有效计算。相反，任务高度耦合、共享状态变化频繁、验收边界不清晰时，它往往只会增加通信损耗和级联错误。

## 1. 先区分五种经常混淆的东西

```text
tool call       主 Agent 请求一个约定接口，内部可能含模型或外部服务
subroutine      独立模型调用，返回结构化结果，不拥有任务
subagent        有局部目标、状态、工具和预算的受托执行者
handoff         当前责任主体把会话或工作流所有权转交给另一个 Agent
multi-agent     多个自治执行者通过明确协议共同改变任务状态
```

是否把它称作“Agent”不是关键，关键是它是否具备独立决策循环和明确责任边界。一个翻译模型被主 Agent 当作函数调用，实际上更像概率子程序；一个能自行搜索、调整计划、使用工具并提交证据的研究者，才算 subagent。Handoff 也不同于“请专家给意见”，它是执行权和用户交互权的转移。

OpenAI 的官方架构把 manager 与 handoff 明确区分：manager 把专家 Agent 当作工具调用并保留会话控制，handoff 则把工作流控制交给新的 Agent。[OpenAI Agents SDK](https://github.com/openai/openai-agents-python/blob/main/docs/agents.md) 这种区分应进入 Harness 状态机；否则用户无法知道当前谁在负责，guardrail、预算和最终输出所有权都会变得含糊。

## 2. 多 Agent 的收益来自哪里

多 Agent 的收益通常来自四种机制，而不是“角色扮演”本身。

第一是并行搜索。多个 worker 可在不同假设、代码区域或数据源中同时工作，争取缩短墙钟时间并提高覆盖率。第二是上下文分工。局部任务可以只加载相关材料，延续已有调查的任务也可能需要父上下文，不能一律从空白开始。第三是模型与工具差异，它们可能带来不同错误分布，但多样性仍须测量。第四是验证分工，独立的信息路径与验收标准有助于减少共同偏差；仅分成两个角色并不足够。

Anthropic 的 Research 系统采用 orchestrator-worker 架构：lead agent 先定策略，再并行生成搜索 subagent。其内部分析报告，在 BrowseComp 上，token 用量、工具调用数与模型选择联合解释了 95% 的性能方差；单独使用 token 用量也能解释 80%。这两项结果不是可相加的贡献份额，观察关联也不能确定因果，更不能据此排除协作结构的独立作用。[Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)

这提示计算预算可能是重要关联因素。Anthropic 还报告其普通 Agent 和多 Agent 系统分别约使用聊天场景的 4 倍、15 倍 token；它们是特定系统的成本观察，不是通用比例。应固定任务与模型，在相同预算下比较单 Agent、多 Agent、重复试跑与确定性并行程序，才能判断新增协调是否有价值。

## 3. 何时不应使用多 Agent

至少四类任务通常不适合直接拆成多个自治 Agent。

高度串行的任务中，下一步依赖前一步的精确结果，parallel worker 只能猜测未来状态。窄而确定的任务里，用普通函数、工作流或一次模型调用就能完成，加入自治循环只会增加故障面。强共享状态任务要求多个执行者频繁读写同一工作树、数据库或 UI，协同成本可能高于执行收益。低价值任务往往撑不起明显上升的推理成本与更复杂运维；这一判断来自前述厂商案例与系统成本结构，而不是普遍比例定律。

Anthropic 还指出，当所有 Agent 需要共享同一上下文，或任务包含大量相互依赖领域时，目前并不适合多 Agent；许多 coding 任务真正可并行的部分比研究任务少。[Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)

因此 Harness 应先算“可委派性”，不要因为请求复杂就马上建团队：

```text
DelegationValue ≈
  parallel_fraction
  × context_separability
  × diversity_gain
  × task_value
  - communication_cost
  - merge_risk
  - duplicated_work
  - coordination_latency
```

这是决策提示，不是可直接代数计算的收益公式：各项没有共同量纲和测量定义。如果拆后的子任务无法定义独立输入、交付物和验收条件，就应先澄清边界，而不是期待委派后自然形成职责链。

## 4. 四类基本拓扑

### 4.1 Manager—Worker

中央 manager 分解任务、分配 worker、收集结果并负责最终合成：

```text
                    ┌─ worker A
user → manager ─────┼─ worker B → manager → verifier → result
                    └─ worker C
```

优点是有单一责任入口，也更容易做预算和策略控制，适合研究、候选生成、分片检查。缺点是 manager 可能成为信息瓶颈和单点故障；如果 worker 只给回长篇自然语言，合成环节会丢失来源、置信度和冲突信息。

### 4.2 Pipeline / Assembly Line

每个 Agent 接收上游 artifact，并产生下游 artifact。MetaGPT 将软件工作流中的标准作业程序编码进角色化 prompt 序列，以 assembly-line 方式组织协作；其出发点之一就是朴素 Agent 对话里容易出现级联不一致。[MetaGPT](https://arxiv.org/abs/2308.00352)

流水线适合阶段边界清晰的流程，比如需求→设计→实现→审查。但上游缺陷会被下游当成事实继续继承。每一阶段都应配 schema、质量门和返工路径，不能只靠下一个角色“看完再理解”来修复问题。

### 4.3 Peer Handoff

Agent 根据任务阶段将责任转给其他专家。OpenAI Agents SDK 把 handoff 作为模型可调用工具暴露出来，并支持配置结构化 handoff 输入、回调和输入过滤；默认状态下，接收者仍可能看到先前会话历史，除非显式过滤。[OpenAI Handoffs](https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md)

Handoff 适用于客服分流、领域升级和长期会话里的所有权转换。它不适合需要中央汇总多个并行意见的情景。每次转移都应记录 `from`、`to`、原因、状态摘要、未决承诺和权限，还要限制循环转交。

### 4.4 Blackboard / Event Graph

多个 Agent 不直接维护长对话，而是通过共享产物存储、事件总线或任务图协作。AutoGen 早期以可对话 Agent 组合为核心，后续 0.4 架构转向 actor model，用消息、运行时和分层 API 提升模块化与扩展性。[AutoGen](https://www.microsoft.com/en-us/research/project/autogen/publications/)

共享黑板适合异步、长周期和跨语言执行，但要先解决 schema 演进、并发控制、重复消息、顺序、所有权和垃圾回收。把聊天历史当消息总线，通常只能得到难以恢复的分布式 prompt。

## 5. 委派是一份受限契约

委派包应把“研究一下这个主题”细化为可验证的局部契约：

```text
DelegationContract {
  parent_run_id
  subtask_id
  objective
  inputs[]              // 固定快照或资源引用
  expected_output_schema
  acceptance_checks[]
  allowed_tools[]
  capability_scope
  execution_identity
  execution_authority_ref  // worker 执行权的可信授权依据
  delegation_authority_ref // 调用者可委派此任务的授权依据
  context_policy
  budget {tokens, time, cost, tool_calls}
  deadline              // 绝对时间；转换成 TTL 时显式计算剩余秒数
  can_delegate
  reporting_interval
  cancellation_token
}
```

父 Agent 不应把全部工具、凭证和记忆隐式地复制给子 Agent。转授自身权限时，子授权的动作、资源和期限不得超出可转授范围；专家若使用独立身份，则由可信策略服务分别检查其执行权、调用者的委派权和任务用途，不能让模型自行授予。默认 `can_delegate=false`；递归委派还要限制深度、扇出和整棵树的总预算。

输入应限于局部目标所需材料，不应自动包含全部私密会话。上下文策略要说明哪些是可信指令、哪些是不可信材料、哪些数据不能离开当前执行域。OpenAI handoff 的 `input_filter` 提供了筛选历史输入的接口；传递多少历史，实际是在隔离与连续性之间作选择。[OpenAI Handoffs](https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md)

Deep Agents 在 2026-09-08 的文档中将这项选择显式化：isolated 仅接收任务说明；fork 继承父状态与历史，移除末尾委派调用，并把任务说明转成子代理消息，最终仍向父代理返回一个工具结果。[上下文模式](https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness) 文档认为延续调查的 worker 可借此减少重复读取和利用缓存，独立 reviewer 则适合隔离上下文；这些收益不是本书实测结果。若父历史包含子角色无权接收的材料，应选可筛选的输入路径，不能因 fork 方便就扩大可见范围。

## 6. 子结果应交付产物与证据

如果 worker 只返回“我认为方案 A 更好”，manager 就没法可靠地做合并。Subagent 输出至少要包含结论、证据引用、生成的 artifact、验证结果、假设、置信度和未决问题。

```text
SubagentResult {
  subtask_id
  status
  claims[] {text, evidence_refs, confidence}
  artifacts[] {uri, hash, type}
  checks[]
  assumptions[]
  conflicts[]
  unresolved[]
  usage
}
```

研究型 worker 应提交来源和精确 locator；编码 worker 应提交独立 worktree 的 patch 和测试；数据 worker 应提交查询、快照和对账结果。这样 manager 在合并时拿到的是可验证对象，而不是经历多轮摘要压缩后的散文。

Anthropic 在多 Agent Research 中把 subagent 描述为信息过滤器，并强调把结果直接存入外部系统，可减少多阶段复制带来的信息损失和 token 开销。这说明 Harness 可以把大型结果放到 artifact store，只在消息中传递引用和摘要。

## 7. 共享状态与并发写入

并行读取相对容易，并行写入更难。多个 coding worker 改同一工作树可能导致文件覆盖、测试状态污染和难以归因的 diff。更安全的策略是 copy-on-write workspace 或独立 worktree：

```text
base snapshot
  ├─ workspace A → patch A + evidence A
  ├─ workspace B → patch B + evidence B
  └─ workspace C → patch C + evidence C
                    ↓
             merge workspace
                    ↓
             full-system verification
```

合并不是文本拼接。Harness 要检测文件级和语义冲突，决定执行顺序，并在组合状态上重跑验证。每个分支单独通过，不代表组合后仍然通过。

数据库、工单和消息系统应按可用语义选择资源版本、条件写入、事务、下游幂等键与副作用账本。读任务可以并发，冲突写入则要由运行时锁定、排序或拒绝。并非每个下游都支持幂等；结果未知时先对账，不能靠“可补偿”允许盲重放。

## 8. 错误如何在团队中传播

多 Agent 的典型问题往往不是某个 worker 的孤立答错，而是错误被社会化：早期错误变成公共前提，后续角色围绕它生成看似一致但错误的文档。MetaGPT 提到的级联幻觉，正是这种朴素链式协作失效的表现之一。[MetaGPT](https://arxiv.org/abs/2308.00352)

2025 年一项多 Agent 失败研究把问题归类为规范与系统设计、Agent 间错位、任务验证与终止三大类，并指出在流行 benchmark 上相对单 Agent 的收益可能有限。[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) 这类结果不应被理解为“多 Agent 无用”，而是提醒我们：增加节点也增加接口，接口质量往往比角色名称更决定可靠性。

常见传播机制有：

- manager 拆错任务，所有 worker 高质量地完成了错误子目标；
- worker 把推断当事实，上报为“肯定结论”，manager 再按多数票强化错误；
- 多个同模型 Agent 共享相同盲点，表面共识不代表独立证据；
- sub Agent 隐藏失败，只提交漂亮摘要；
- 循环 handoff 导致责任漂移并消耗预算；
- verifier 只查局部结果，却没检查组合不变量。

应对方式包括独立审查问题分解、保留来源记录、盲化并行、比较不同模型、保留冲突和系统级验证。多数票是否有益，取决于判断者准确性、错误相关性及聚合规则；近似独立不是获益的必要条件，独立本身也不充分。

一个便于理解的充分条件是：三个判断者处理同一二元问题，正确与否独立同分布，每人正确概率为固定的 `p`，且 `0.5 < p < 1`。多数票正确率为 `3p² − 2p³`，高于 `p`；低于随机水平的独立判断者却可能被投票放大错误。现实中的相关错误仍可能留下聚合收益，完全重复的判断则不增加信息。模型与上下文共享程度要测量，最终以同预算聚合结果判断，不能把一致意见当作独立证据。

## 9. Debate、Critique 与 Ensemble

“让多个 Agent 辩论”包含几种不同机制：集成先分别生成候选，再由规则或评判器选择；批评让另一个 Agent 针对候选找问题；辩论则允许多轮互相影响。三者的成本和风险不同，不能混为一种增强手段。

受控逻辑推理研究发现，团队内推理能力和多样性是 debate 成功的重要驱动，而顺序、置信度可见性等结构参数的收益较小；多数压力还可能压制独立纠错。[Can LLM Agents Really Debate?](https://arxiv.org/abs/2511.07784) 所以生产系统通常优先采用“先独立、后比较”：先避免锚定，再把候选暴露给针对性反驳。讨论轮数应由信息增益或分歧收敛决定，不应无限延长到形式共识。

可验证任务通常更适合候选并行 + 外部 verifier，而不是语言辩论。只有当标准包含语义判断、价值冲突或证据解释时，debate 才可能带来附加信息；最终裁决仍应按完成契约判断，而非看哪个 Agent 讲得更有说服力。

## 10. 调度、背压与预算

多 Agent runtime 本质上是一个带概率 worker 的分布式任务系统。它必须处理队列、公平性、并发上限、速率限制、优先级、超时、取消、心跳、租约、重试、死信与背压。

```text
global_budget
  ├─ orchestration reserve
  ├─ worker pools by risk/model/tool
  ├─ verification reserve
  └─ emergency reconciliation reserve
```

父 Agent 应在派发前预留综合与验证预算，避免探索用完资源后无力验收。动态调度可按子任务价值、剩余不确定性和边际收益调整：重复返回同样信息时停止扩展，关键分歧未解决时再增加独立路径。

取消必须向整棵委派树传播，并立即停止继续派发；已发生的外部副作用不能随之消失。运行时应回读或等待在途动作，未知结果进入对账，已确认的错误效果再按授权补偿或交人工处理。父 run 结束后仍在后台运行的孤儿任务会继续消耗成本并扩大风险。

## 11. 权限、身份与责任链

每个 Agent 应有可区分的执行身份，即使底层由同一模型服务承载。审计记录至少包含 `principal_agent`、`delegated_by`、执行授权与委派授权的引用、资源范围、策略版本和动作。不要用共享管理员令牌让所有 worker 看起来像同一主体。

Manager 对委派行为负责，但不能盲目信任 worker。子结果进入父上下文时仍需核验来源，尤其是浏览网页、工单或第三方 MCP 后的结果。合并和提交要重新经过授权策略与验证器；转交用户交互权也不自动扩大接收者的资源权限。

多 Agent 安全还有组合风险：两个分别获准的动作连接起来，可能形成信息泄漏或越权。一个 worker 读取私有数据，另一个向公共系统写入，若通过共享黑板交换结果，就可能建立外泄路径。信息流策略应追踪来源记录、数据分类和后续用途；转授权限缩减并不能自动排除这类风险。

## 12. 可观测性：同时看到树和因果链

纯串行循环的轨迹可以展示为序列；只要存在并行工具、异步事件或多 Agent 协作，就应记录部分有序的因果图。决定偏序的是并发与依赖，不是 Agent 数量。显示时可以线性排序，但仍须保留父子、消息、产物依赖和外部副作用之间的关系：

```text
run
 ├─ delegation span A
 │   ├─ model/tool spans
 │   └─ artifact A
 ├─ delegation span B
 │   ├─ model/tool spans
 │   └─ artifact B
 └─ merge span
     ├─ consumes A,B
     └─ verification + commit
```

所有事件应使用稳定的 run/subtask ID 和逻辑关联，而不是依赖墙钟顺序。并发环境里，时间戳接近并不代表因果关系。指标除成功率外，还应包括有效并行度、重复工作率、消息与 artifact 比例、合并冲突率、委派深度、orphan 数、每次成功成本和关键路径时延。

评测也要把团队行为作为研究对象。MultiAgentBench 尝试用 milestone（里程碑）指标比较 star、chain、tree 和 graph 等协调协议，说明只看最终答对与否不足以解释协作质量。[MultiAgentBench](https://arxiv.org/abs/2503.01935) 企业级测试还应注入 worker 超时、错误证据、重复消息、部分网络分区、过期 artifact 和恶意子 Agent，观察系统是否能降级，而不是整体失控。

## 13. 三类贯穿案例

### 13.1 仓库软件工程

不要按虚构的“公司角色”来拆分，应按可隔离的 artifact 切分：一个 Agent 定位失败点，一个在独立 worktree 生成修复补丁，一个构造反例或补充测试，一个做安全审查。主 Agent 保留集成所有权。若多个修改触及同一核心模块，就应退化为串行执行，或改由单一 owner 实施，避免语义冲突。

以 TASK2048 为教学例子，修复者继承已收集的错误现场，在独立工作区交付补丁哈希、修改范围和局部测试；审阅者只读取需求、补丁与证据。主 Agent 合并后若又改了文件，旧测试就不能继续为新版本作证，应在干净工作区重验；结果冲突时保留待解决状态，不按多数意见直接合并。这是设计示例，并非供应商实跑记录。

### 13.2 企业数据分析

天然可并行的方向包括不同数据源取数、指标口径复核、异常解释和反事实检验。所有 worker 使用固定数据 snapshot，并把 SQL、行数、口径和来源写入结构化结果。Manager 合成结论时必须保留冲突，不应把不同时间范围或币种的数字直接平均。

数据权限按域分配：财务 worker 不必读取人事明细，外部研究 worker 不接触客户数据。最终报告里的每个数字都应回链到查询和 snapshot。

### 13.3 自我进化 Agent

候选生成、评测和发布要有不同责任边界。多个 worker 并行提出提示、技能或可变决策策略的候选；评测服务用验证集和安全检查筛选，选择服务按预定规则确定候选，再在预定时机进行密封终测。发布控制器负责灰度与版本回退。用于选择或修复的反馈不再属于独立终测证据。

若候选 Agent 能通过委派修改评分逻辑，独立门禁就会失效。委派图、数据来源和权限记录应支持复查：候选家族看到了哪些反馈，密封集何时访问，裁判是否被候选改动。只隐藏标签仍不足以排除自适应泄漏，多 Agent 也不会自动建立实验独立性。

## 14. 一个最小参考实现

以下是教学伪代码，未作为供应商实现实跑。它直接使用前述契约字段：`allowed_tools` 是工具集合，`capability_scope` 是资源与动作范围，`expected_output_schema` 是输出结构；`deadline` 为绝对时间，签发前换算剩余秒数。策略服务检查执行权与委派权，并限制最终期限；拒绝、待审批和未知决定均不启动子任务。

```text
function delegate(parent, spec):
    assert spec.objective is bounded
    assert spec.expected_output_schema exists
    assert spec.acceptance_checks not empty
    ttl_seconds = seconds_until(spec.deadline, trusted_clock.now())
    if ttl_seconds <= 0 or parent.cancelled:
        return NOT_STARTED
    decision = policy.authorize_delegation(parent.identity, spec, ttl_seconds)
    if decision.decision not in {ALLOW, CONSTRAINED_ALLOW}:
        return NOT_STARTED(decision.decision)

    resources = lifecycle.open_record(spec.subtask_id)
    outcome = FAILED
    try:
        lease = resources.reserve(spec.budget, parent.allocatable_budget)
        capability = resources.issue_bound_authorization(decision)
        resources.enforce_constraints_or_fail(decision)
        workspace = resources.create_isolated_workspace(spec.inputs)
        context = build_context(spec.inputs, spec.context_policy)
        child = resources.spawn(context, workspace, capability, lease)
        result = child.await_or_cancel(spec.deadline, spec.cancellation_token)
        artifact = validate_and_export(result, spec.expected_output_schema)
        checks = verify_subtask(artifact, spec.acceptance_checks,
                                budget=parent.verification_reserve)
        outcome = SubagentResult(artifact, checks, resources.metered_usage)
    except error:
        outcome = FAILED_WITH_EVIDENCE(error, resources.event_refs)
    finally:
        cleanup = resources.close_or_quarantine()

    if not cleanup.closed:
        return RECONCILIATION_REQUIRED(outcome, cleanup.record_ref)
    return outcome

function integrate(parent, results):
    reject_unverified_or_expired(results)
    conflicts = detect_semantic_and_resource_conflicts(results)
    if conflicts:
        return RESOLUTION_REQUIRED(conflicts)
    with managed_clean_workspace() as workspace:
        candidate = merge_and_export_immutable(workspace, results)
    return parent_completion_gate(candidate)  # 对合并版本重新验收
```

辅助函数承担明确前提。`reserve` 必须原子扣减父任务可分配额度，后者已扣除集成、验证与应急预留；每次模型或工具调用前检查租约，持续计入 token、费用、调用次数与时间，耗尽就停止派发。`spawn` 在启动时重查授权有效性，并将父取消与契约取消信号关联。`validate_and_export` 核验结构与来源引用，将持久产物导出后才允许清理工作区；来源可追溯仍不等于语义正确。

资源操作必须先写入持久生命周期记录；创建超时但结果未知时，不能假定资源未产生。`close_or_quarantine` 在成功、创建失败、超时和取消路径都执行：逐项撤销授权、停止并回收子进程与后代，保存证据后清理工作区，再结算用量并归还未用预留。它须捕获各项清理错误，继续处理其余资源，并以结构化状态返回；任一资源或副作用未闭合，均返回 `closed=false`。未知副作用转对账，仍可能运行的资源保留额度与清理责任。进程崩溃后的回收器继续处理记录，合并工作区也须在异常时清理。缺少这些前提，这段教学代码就不是完整的恢复实现。

## 15. 设计原则总结

何时拆分：先以单 Agent 为基线，按可验证产物和依赖关系划分任务，区分子程序、子代理与责任转交。用同成本基线和重复试跑结果评估增量收益，并分别报告每组的模型、任务执行费、候选搜索费、验证费、重试费与人工接管成本。

如何隔离：明确状态与工作区所有权，按工作关系选择上下文，分别核验执行权和委派权。探索需要独立性时避免过早共享判断；预算覆盖整棵任务树并为验证预留，取消、背压、重试与孤儿任务由运行时处理。

如何合并验证：子结果携带产物、来源、检查结果、冲突与未决项。局部通过只是集成输入，合并版本仍要重验；未知副作用或清理未闭合时，保留待对账状态，不以一段“完成”摘要结束责任。

多 Agent 的成熟标志不是屏幕上出现更多头像，而是组织能够精确回答：为什么要拆成这些执行者，每个执行者看到了什么、被允许做什么、产出了什么证据，冲突怎样处理，以及当某个执行者犯错时，系统为何仍能恢复。做到这些之后，“Agent 团队”才不再是 prompt theater，而是可治理的计算拓扑。

# 第十一章 多 Agent、委派与协作拓扑

> 证据声明：产品事实维护至 2026-08-28；架构原则为作者基于公开材料的综合推断。

多 Agent 是个名字很容易误导人的概念。把同一个模型调用五次，再给每次调用贴上“架构师”“开发者”“审查者”这样的标签，不会自动组成一个真实团队。一个真正的多 Agent 系统，必须先回答：任务为什么可以拆解、状态由谁持有、权限怎么衰减、冲突如何解决、结果由谁验收、故障如何隔离，以及新增成本是否换来了可量化收益。

这一章的核心判断是：**多 Agent 不是能力层面的默认升级，而是一种并发、隔离与治理机制。** 当任务可并行探索、需要不同上下文或信任边界、单一上下文放不下全部材料时，它可能显著提升有效计算。相反，任务高度耦合、共享状态变化频繁、验收边界不清晰时，它往往只会增加通信损耗和级联错误。

## 1. 先区分五种经常混淆的东西

```text
tool call       主 Agent 调用一个确定性能力
subroutine      独立模型调用，返回结构化结果，不拥有任务
subagent        有局部目标、状态、工具和预算的受托执行者
handoff         当前责任主体把会话或工作流所有权转交给另一个 Agent
multi-agent     多个自治执行者通过明确协议共同改变任务状态
```

是否把它称作“Agent”不是关键，关键是它是否具备独立决策循环和明确责任边界。一个翻译模型被主 Agent 当作函数调用，实际上更像概率子程序；一个能自行搜索、调整计划、使用工具并提交证据的研究者，才算 subagent。Handoff 也不同于“请专家给意见”，它是执行权和用户交互权的转移。

OpenAI 的官方架构把 manager 与 handoff 明确区分：manager 把专家 Agent 当作工具调用并保留会话控制，handoff 则把工作流控制交给新的 Agent。[OpenAI Agents SDK](https://github.com/openai/openai-agents-python/blob/main/docs/agents.md) 这种区分应进入 Harness 状态机；否则用户无法知道当前谁在负责，guardrail、预算和最终输出所有权都会变得含糊。

## 2. 多 Agent 的收益来自哪里

多 Agent 的收益通常来自四种机制，而不是“角色扮演”本身。

第一是并行搜索。多个 worker 可以同时在相互独立的假设空间、代码区域或数据源中搜索，缩短墙钟时间并提高覆盖率。第二是上下文隔离。每个 worker 只加载局部材料，因此有效信息密度通常高于把所有内容硬塞进一个上下文。第三是认知与工具异质性。不同模型、提示、工具或数据权限，会带来不同的错误分布。第四是独立验证。执行者和审查者分离，可降低同一假设在计划、执行和验收阶段连续被强化的风险。

Anthropic 的 Research 系统采用 orchestrator-worker 架构：lead agent 先定策略，再并行生成搜索 subagent。其内部分析指出，在 BrowseComp 上，token 使用、工具调用数和模型选择共同解释了 95% 的性能方差，其中 token 使用本身占 80%。这支持了“多 Agent 主要在扩大可用推理与探索预算”的解释。[Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)

这也形成了一条去魅结论：有时多 Agent 只是更有组织地花更多 token。Anthropic 也报告，普通 Agent 大约用聊天的 4 倍 token，而多 Agent 系统大约是聊天的 15 倍。由此更合理的问题不是“多 Agent 是否更强”，而是在同样成本、时延和模型预算下，它是否优于更强的单 Agent、更多单 Agent 试跑，或确定性并行程序。

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

这不是精确公式，而是决策框架。如果拆后的子任务无法定义独立输入、交付物和验收条件，就不应先委派，再期待 Agent 自己把职责链理顺。

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

多个 Agent 不直接维护长对话，而是通过共享 artifact store（制品仓库）、事件总线或任务图协作。AutoGen 早期以可对话 Agent 组合为核心，后续 0.4 架构转向 actor model（参与者模型），用消息、运行时和分层 API 提升模块化与扩展性。[AutoGen](https://www.microsoft.com/en-us/research/project/autogen/publications/)

共享黑板适合异步、长周期和跨语言执行，但要先解决 schema 演进、并发控制、重复消息、顺序、所有权和垃圾回收。把聊天历史当消息总线，通常只能得到难以恢复的分布式 prompt。

## 5. 委派是一份受限合同

好的 delegation packet（委派包）不是一句“研究一下这个主题”，而是可验证的局部合同：

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
  context_policy
  budget {tokens, time, cost, tool_calls}
  deadline
  can_delegate
  reporting_interval
  cancellation_token
}
```

父 Agent 不应把全部工具、凭证和记忆隐式地复制给子 Agent。委派权限要按衰减原则处理：子能力应是父能力的子集，具有更短 TTL、更窄资源和明确用途；默认 `can_delegate=false`。如果允许递归委派，要限制深度、扇出和总预算，避免委派树指数膨胀。

输入应保持最小。子 Agent 只拿到完成局部目标所需的上下文，不应自动看到全部私密会话。Context policy（上下文策略）要说明哪些是可信指令、哪些是不可信材料、哪些数据不能离开当前执行域。OpenAI handoff 的 `input_filter` 说明了同一问题在 SDK 层的具体落实：历史是否传递不是细节，而是隔离与连续性之间的架构选型。[OpenAI Handoffs](https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md)

## 6. 结果必须是 artifact，不是意见

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

数据库、工单和消息系统应使用 resource version（资源版本）、compare-and-swap（比较并交换）、事务、幂等键和 effect ledger（效果账本）。读任务可以并发，而写任务要按资源声明锁或序列化。锁不能靠模型的自然语言约定，而应由 runtime（运行时）强制执行。

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

应对方式包括独立问题分解审查、来源级 provenance（血缘）、盲化并行、异质模型、反方角色、冲突保留和最终系统级验证。多数票只有在错误近似独立时才有价值；复制同一上下文和模型通常不满足这个假设。

## 9. Debate、Critique 与 Ensemble

“让多个 Agent 辩论”常被当成万能推理增强，但必须区分三种机制。Ensemble（集成）是独立生成候选，再由规则或 judge（裁决器）选择；Critique（批评）是让一个 Agent 针对候选找问题；debate（辩论）允许多轮互相影响。三者的成本和风险不一样。

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

不要把全部预算都给探索 worker，而在最后没有 token 和时间做验证。父 Agent 应在 dispatch（下发）前预留综合与验证预算。动态调度可按子任务价值、剩余不确定性和边际收益扩缩容：worker 重复返回同样信息时要停止扩展；关键分歧未解决时增加独立路径。

取消必须向整棵委派树传播，但已发生的副作用不能简单“取消”。runtime 需要等待或回读在途 action（动作），执行补偿或标记人工处理。父 run 完成后仍在后台运行的 orphan worker（孤儿任务）会带来成本和安全漏洞。

## 11. 权限、身份与责任链

每个 Agent 应有独立 execution identity（执行身份），即使底层由同一模型服务承载。审计记录至少应包含 `principal_agent`、`delegated_by`、capability（能力）、资源范围、策略版本和 action。不要用共享管理员 token 让所有 worker 看起来像同一主体。

Manager 对委派行为负责，但不能盲目信任 worker。子结果进入父上下文时仍是不可信输入，尤其当 worker 浏览网页、issue 或第三方 MCP（模型上下文协议）时。合并和提交需再经过父级 policy 与 verifier（校验器）。Handoff 如果转移了用户交互权，也不能自动转移超出接收者职责范围的资源权限。

多 Agent 安全还有组合风险：两个看似独立允许的动作放在一起，可能就变成信息泄露或越权。一个 worker 读取私有数据，另一个 worker 向公共系统写入，若通过共享黑板连接，就会形成跨域泄漏。信息流策略必须追踪 provenance（血缘），不能只校验单次工具调用。

## 12. 可观测性：同时看到树和因果链

单 Agent 的 trace（追踪）是序列，multi Agent 的 trace 是部分有序图。系统需要同时表达父子关系、消息关系、artifact 依赖和外部 effect（外部作用）：

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

每个 worker 交付 patch hash、修改范围和局部测试；合并后在 clean workspace（干净工作区）里跑完整验收契约。代码 reviewer 不共享 implementer 的隐藏草稿，只看任务、diff（差异）和证据，以降低锚定风险。

### 13.2 企业数据分析

天然可并行的方向包括不同数据源取数、指标口径复核、异常解释和反事实检验。所有 worker 使用固定数据 snapshot，并把 SQL、行数、口径和来源写入结构化结果。Manager 合成结论时必须保留冲突，不应把不同时间范围或币种的数字直接平均。

数据权限按域分配：财务 worker 不必读取人事明细，外部研究 worker 不接触客户数据。最终报告里的每个数字都应回链到查询和 snapshot。

### 13.3 自我进化 Agent

候选生成、评测和发布要由不同责任主体完成。多个 mutation worker 并行提出 prompt、skill 或 policy 变体；可信 evaluator 在 held-out 集与安全集上评估；selection service（选择服务）按预注册规则挑选；release controller（发布控制器）做 canary（灰度）和回滚。

若候选 Agent 能通过委派影响 evaluator，那么所谓进化就失去独立门禁。委派图、数据血缘和权限配置要证明 candidate family（候选家族）没有接触 held-out 标签，也没有修改评分逻辑。多 Agent 在此的核心价值不是“群体智慧”，而是实现实验隔离和制衡。

## 14. 一个最小参考实现

```text
function delegate(parent, spec):
    assert spec.objective is bounded
    assert spec.output_schema exists
    assert spec.acceptance_checks not empty

    capability = attenuate(
        parent.capability,
        resources=spec.resources,
        tools=spec.tools,
        ttl=spec.deadline,
        can_delegate=spec.can_delegate
    )

    lease = scheduler.reserve(
        budget=spec.budget,
        parent_budget=parent.remaining,
        cancellation=parent.cancel_token
    )

    child = runtime.spawn(
        snapshot=build_minimal_context(spec),
        capability=capability,
        workspace=create_isolated_workspace(spec.inputs),
        lease=lease
    )

    result = child.await_or_cancel()
    artifact = validate_schema_and_provenance(result)
    checks = verify_subtask(artifact, spec.acceptance_checks)
    return SubagentResult(artifact, checks, child.usage)

function integrate(parent, results):
    reject_unverified_or_expired(results)
    conflicts = detect_semantic_and_resource_conflicts(results)
    if conflicts:
        return RESOLUTION_REQUIRED(conflicts)
    candidate = merge_in_clean_environment(results)
    return parent_completion_gate(candidate)
```

这段伪代码的关键是：委派前先做缩权并预留预算，执行时隔离，返回时验 schema 与 provenance，合并时重新检查系统级不变量。Subagent 的“完成”只是父任务的一个候选输入。

## 15. 设计原则总结

第一，单 Agent 是默认值，多 Agent 需要证明增量价值。第二，按可验证 artifact 和依赖关系拆分任务，不按拟人角色拆分。第三，区分 subroutine、subagent 与 handoff，并显式记录责任所有权。第四，权限随委派衰减，状态与工作区默认隔离。第五，先独立探索，再比较和合并，避免过早共识。第六，所有子结果都要携带 provenance、验证和未决项。第七，局部通过不等于组合通过，合并后必须重验。第八，预算要覆盖整棵任务树并为验证预留。第九，用分布式系统方法处理取消、重试、背压和 orphan worker。第十，以同成本单 Agent 和多 trial baseline（多次单模型试跑基线）证明多 Agent 的真实收益。

多 Agent 的成熟标志不是屏幕上出现更多头像，而是组织能够精确回答：为什么要拆成这些执行者，每个执行者看到了什么、被允许做什么、产出了什么证据，冲突怎样处理，以及当某个执行者犯错时，系统为何仍能恢复。做到这些之后，“Agent 团队”才不再是 prompt theater，而是可治理的计算拓扑。

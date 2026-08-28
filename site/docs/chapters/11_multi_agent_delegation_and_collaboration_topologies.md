# 第十一章 多 Agent、委派与协作拓扑

> 证据声明：产品事实以 2026-08-22 为资料截面；架构原则为作者基于公开材料的综合推断。

多 Agent 是一个容易被名字误导的概念。把同一个模型调用五次、给每次调用贴上“架构师”“开发者”“审查者”的标签，并不会自然产生一个团队。真正的多 Agent 系统必须回答：工作为什么可拆、状态由谁拥有、权限如何衰减、冲突怎样解决、结果由谁验证、失败怎样隔离，以及额外成本是否换来了可测量的收益。

这一章的核心判断是：**多 Agent 不是能力层的默认升级，而是一种并发、隔离和治理机制。** 当任务可以并行探索、需要不同上下文或信任边界、单一上下文容不下全部材料时，它可能显著增加有效计算；当任务高度耦合、共享状态频繁变化、验收边界含糊时，它往往只会增加通信损耗和级联错误。

## 1. 先区分五种经常混淆的东西

```text
tool call       主 Agent 调用一个确定性能力
subroutine      独立模型调用，返回结构化结果，不拥有任务
subagent        有局部目标、状态、工具和预算的受托执行者
handoff         当前责任主体把会话或工作流所有权转交给另一个 Agent
multi-agent     多个自治执行者通过明确协议共同改变任务状态
```

是否叫“Agent”并不重要，关键是它有没有独立决策循环和责任边界。一个翻译模型被主 Agent 当函数调用，更像概率子程序；一个能自行搜索、调整计划、使用工具并提交证据的研究者，才构成 subagent。Handoff 又不同：它不是“请专家给意见”，而是执行权和用户交互权的转移。

OpenAI 的官方架构把 manager 与 handoff 明确区分：manager 将专家 Agent 作为工具调用并保留会话控制，handoff 则把工作流控制交给新的 Agent。[OpenAI Agents SDK](https://github.com/openai/openai-agents-python/blob/main/docs/agents.md) 这种区分应进入 Harness 状态机；否则用户不知道当前由谁负责，guardrail、预算和最终输出所有权也会含糊。

## 2. 多 Agent 的收益来自哪里

多 Agent 的收益通常来自四种机制，而不是来自“角色扮演”本身。

第一是并行搜索。多个 worker 可以同时搜索互相独立的假设空间、代码区域或数据源，缩短墙钟时间并提高覆盖率。第二是上下文隔离。每个 worker 只加载局部材料，使有效信息密度高于把所有内容塞进一个上下文。第三是认知与工具异质性。不同模型、提示、工具或数据权限可能带来真正不同的错误分布。第四是独立验证。实施者和审查者分离，可降低同一假设贯穿计划、执行与验收的风险。

Anthropic 的 Research 系统采用 orchestrator-worker 架构：lead agent 制定策略并并行生成搜索 subagent。其内部分析称，在 BrowseComp 上 token 使用、工具调用数和模型选择解释了 95% 的性能方差，其中 token 使用本身解释 80%；这支持了“多 Agent 主要是在扩大可用推理与探索预算”的解释。[Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)

这也是一条去魅结论：多个 Agent 有时只是更有组织地花更多 token。Anthropic 同时报告，普通 Agent 约使用聊天的 4 倍 token，多 Agent 系统约为聊天的 15 倍。因此合理问题不是“多 Agent 是否更强”，而是：在同样成本、时延和模型预算下，它是否优于一个更强的单 Agent、更多单 Agent trial，或确定性并行程序。

## 3. 何时不应使用多 Agent

至少四类任务通常不适合直接拆成多个自治 Agent。

高度串行任务的下一步依赖前一步精确结果，并行 worker 只能猜测未来状态。强共享状态任务要求多个执行者频繁读写同一工作树、数据库或 UI，协调成本可能超过执行成本。窄而确定的任务用普通函数、工作流或一次模型调用即可完成，引入自治循环只增加故障面。低价值任务无法覆盖 10 倍级推理成本与更复杂运维。

Anthropic 也指出，需要所有 Agent 共享同一上下文或包含大量相互依赖的领域，目前并不适合多 Agent；许多 coding 任务的真实可并行部分少于研究任务。[Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)

因此 Harness 应先计算“可委派性”，而不是看到复杂请求就生成团队：

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

这不是精确公式，而是决策框架。如果拆分后的子任务无法定义独立输入、交付物和验收条件，就不应先委派再期待 Agent 自己协调清楚。

## 4. 四类基本拓扑

### 4.1 Manager—Worker

中央 manager 分解任务、分配 worker、收集结果并负责最终合成：

```text
                    ┌─ worker A
user → manager ─────┼─ worker B → manager → verifier → result
                    └─ worker C
```

优点是单一责任入口、易于预算和策略控制，适合研究、候选生成、分片检查。缺点是 manager 成为信息瓶颈和单点故障；如果 worker 只返回长篇自然语言，合成阶段会丢失来源、置信度和冲突。

### 4.2 Pipeline / Assembly Line

每个 Agent 接收上游 artifact，并产生下游 artifact。MetaGPT 将软件工作流中的标准作业程序编码进角色化 prompt 序列，以 assembly-line 方式组织协作；其出发点之一正是朴素 Agent 对话容易产生级联不一致。[MetaGPT](https://arxiv.org/abs/2308.00352)

流水线适合阶段边界明确的流程，例如需求→设计→实现→审查。但上游缺陷会被下游当事实继承。每一阶段都应有 schema、质量门和返工路径，不能只依赖下一个角色“阅读并理解”。

### 4.3 Peer Handoff

Agent 根据任务阶段将责任转给另一个专家。OpenAI Agents SDK 把 handoff 暴露为模型可调用的工具，并允许配置结构化 handoff 输入、回调和输入过滤；默认情况下，接收者仍可能看到此前会话历史，除非显式过滤。[OpenAI Handoffs](https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md)

Handoff 适合客服分流、领域升级和长期会话中的所有权转换。它不适合需要中央综合多个并行意见的场景。每次转移都应记录 `from`、`to`、原因、状态摘要、未决承诺和权限；还要限制循环转交。

### 4.4 Blackboard / Event Graph

多个 Agent 不直接维护长对话，而是通过共享 artifact store、事件总线或任务图协作。AutoGen 早期以可对话 Agent 的组合为核心，后续 0.4 架构转向 actor model，以消息、运行时和分层 API 支持更强的模块性与扩展性。[AutoGen](https://www.microsoft.com/en-us/research/project/autogen/publications/)

共享黑板适合异步、长时和跨语言执行，但必须处理 schema 演进、并发控制、重复消息、顺序、所有权和垃圾回收。把聊天历史当消息总线，只会得到一个难以恢复的分布式 prompt。

## 5. 委派是一份受限合同

好的 delegation packet 不是一句“研究一下这个主题”，而是可验证的局部合同：

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

父 Agent 不应把自己的全部工具、凭证和记忆隐式复制给子 Agent。委派权限遵循衰减原则：子能力必须是父能力的子集，具有更短 TTL、更窄资源和明确用途；默认 `can_delegate=false`。如果允许递归委派，应限制深度、扇出和总预算，防止任务树指数膨胀。

输入也应最小化。子 Agent 只收到完成局部目标需要的上下文，不自动看到全部私密会话。Context policy 需要声明哪些是可信指令、哪些是不可信材料、哪些数据不可离开当前执行域。OpenAI handoff 的 `input_filter` 说明了同一问题在 SDK 层的具体体现：历史是否传递不是细节，而是隔离与连续性之间的架构选择。[OpenAI Handoffs](https://github.com/openai/openai-agents-python/blob/main/docs/handoffs.md)

## 6. 结果必须是 artifact，不是意见

如果 worker 只返回“我认为方案 A 更好”，manager 无法可靠合并。Subagent 输出至少包含：结论、证据引用、生成的 artifact、验证结果、假设、置信度和未解决问题。

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

研究 worker 应提交来源和精确 locator；编码 worker 应提交独立 worktree 的 patch 与测试；数据 worker 应提交查询、快照和对账结果。这样 manager 合并的是可验证对象，而不是被多轮摘要压缩过的散文。

Anthropic 在多 Agent Research 中把 subagent 描述为信息过滤器，并强调直接把结果存入外部系统可减少多阶段复制带来的信息损失和 token 开销。这提示 Harness 把大型结果放 artifact store，仅在消息里传递引用和摘要。

## 7. 共享状态与并发写入

并行读取容易，并行写入困难。多个 coding worker 修改同一工作树会覆盖文件、污染测试状态和产生难以归因的 diff。更安全的策略是 copy-on-write workspace 或独立 worktree：

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

合并不是文本拼接。Harness 要检测文件级和语义冲突，决定顺序，并在组合状态上重新运行测试。每个分支单独通过不代表组合后仍通过。

对于数据库、工单和消息系统，使用 resource version、compare-and-swap、事务、幂等键和 effect ledger。读任务可以并发，写任务按资源声明锁或序列化。锁不能由模型用自然语言约定，而应由 runtime 强制执行。

## 8. 错误如何在团队中传播

多 Agent 的典型错误不是单个 worker 答错，而是错误被社会化：早期错误成为共享前提，后续角色围绕它产生一致但错误的文档。MetaGPT 所说的级联幻觉正是朴素链式协作的问题之一。[MetaGPT](https://arxiv.org/abs/2308.00352)

2025 年一项多 Agent 失败研究将问题归为规范与系统设计、Agent 间错位、任务验证与终止三大类，并指出流行 benchmark 上相对单 Agent 的收益可能有限。[Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/abs/2503.13657) 这类结果不应被解读为“多 Agent 无用”，而应提醒我们：新增节点也新增接口，接口比角色名称更决定可靠性。

常见传播机制包括：

- manager 拆错任务，所有 worker 高质量完成了错误子目标；
- worker 把推断标成事实，manager 按多数票强化错误；
- 多个同模型 Agent 共享相同盲点，表面共识并非独立证据；
- 子 Agent 隐去失败，只上报漂亮摘要；
- 循环 handoff 导致责任漂移和预算耗尽；
- verifier 只检查局部结果，没有检查组合不变量。

应对方法包括独立问题分解审查、来源级 provenance、盲化并行、异质模型、反方角色、冲突保留和最终系统级验证。多数票只有在错误近似独立时才有价值；复制同一上下文和模型通常不满足这一假设。

## 9. Debate、Critique 与 Ensemble

“让多个 Agent 辩论”常被当作通用推理增强，但需要区分三种机制。Ensemble 独立生成候选，再由规则或 judge 选择；critique 让一个 Agent 针对候选找错；debate 允许多轮相互影响。三者成本和风险不同。

受控逻辑推理研究发现，团队内在推理能力与多样性是辩论成功的重要驱动，而顺序、信心可见性等结构参数收益有限；多数压力还可能压制独立纠错。[Can LLM Agents Really Debate?](https://arxiv.org/abs/2511.07784) 因此生产系统优先采用“先独立、后比较”：先防止锚定，再暴露候选进行针对性反驳。讨论轮数应由信息增益或分歧收敛决定，不能无限聊到形式共识。

可验证任务通常更适合候选并行 + 外部 verifier，而不是语言辩论。只有当标准含有语义判断、价值冲突或证据解释时，debate 才可能提供额外信息；最终裁决仍应根据完成契约，而不是看哪位 Agent 更善于说服。

## 10. 调度、背压与预算

多 Agent runtime 本质上是一个带概率 worker 的分布式任务系统。必须处理：队列、公平性、并发上限、速率限制、优先级、超时、取消、心跳、租约、重试、死信和背压。

```text
global_budget
  ├─ orchestration reserve
  ├─ worker pools by risk/model/tool
  ├─ verification reserve
  └─ emergency reconciliation reserve
```

不要把全部预算分给探索 worker，最后却没有 token 和时间验证。父 Agent 应在 dispatch 前预留综合与验证预算。动态调度可根据子任务价值、剩余不确定性和边际收益扩缩容：worker 返回重复信息时停止扩展；关键分歧未解决时增加独立路径。

取消必须向整棵委派树传播，但已发生的副作用不能简单“取消”。runtime 需要等待或回读在途 action，执行补偿或标记人工处理。父 run 完成后仍在后台运行的 orphan worker 是成本和安全漏洞。

## 11. 权限、身份与责任链

每个 Agent 应有独立 execution identity，即使底层由同一模型服务实现。审计记录至少包含 `principal_agent`、`delegated_by`、capability、资源范围、策略版本和 action。不得用共享管理员 token 让所有 worker 看起来像同一主体。

Manager 对委派行为负责，但不应盲目信任 worker。子结果进入父上下文时仍是不可信输入，尤其当 worker 浏览了网页、issue 或第三方 MCP。合并和提交需要重新经过父级 policy 与 verifier。Handoff 若转移用户交互权，也不能自动转移超出接收者职责的资源权限。

多 Agent 安全还有组合风险：两个单独允许的动作合在一起可能泄露信息或越权。一个 worker 读取私有数据，另一个 worker 向公共系统写入，两者通过共享黑板连接后形成跨域泄漏。信息流策略必须追踪 provenance，而不是只检查单次工具调用。

## 12. 可观测性：同时看到树和因果链

单 Agent trace 是序列，多 Agent trace 是部分有序图。系统需要同时表示父子关系、消息关系、artifact 依赖和外部 effect：

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

所有事件使用稳定 run/subtask ID 和逻辑关联，而不是依赖墙钟顺序。并发环境中，时间戳接近不证明因果。指标除成功率外，还应包含有效并行度、重复工作率、消息与 artifact 比例、合并冲突率、委派深度、orphan 数、每次成功成本和关键路径时延。

评测也必须把团队行为作为对象。MultiAgentBench 尝试用 milestone 指标比较 star、chain、tree 和 graph 等协调协议，说明仅看最终答对与否不足以解释协作质量。[MultiAgentBench](https://arxiv.org/abs/2503.01935) 企业测试还应注入 worker 超时、错误证据、重复消息、部分网络分区、过期 artifact 和恶意子 Agent，观察系统能否降级而不是整体失控。

## 13. 三类贯穿案例

### 13.1 仓库软件工程

不要按虚构公司角色拆分，而按可隔离 artifact 拆分：一个 Agent 定位失败，一个在独立 worktree 生成修复，一个构造反例或补充测试，一个做安全审查。主 Agent 保留集成所有权。若多个修改触及同一核心模块，应退化为串行或由单一 owner 实施，避免语义冲突。

每个 worker 交付 patch hash、修改范围和局部测试；合并后在 clean workspace 运行完整完成契约。代码 reviewer 不共享 implementer 的隐藏草稿，只看任务、diff 和证据，以降低锚定。

### 13.2 企业数据分析

天然可并行的方向包括不同数据源取数、指标口径复核、异常解释和反事实检验。所有 worker 使用固定数据 snapshot，并将 SQL、行数、口径和来源写入结构化结果。Manager 合成结论时保留冲突，不能把不同时间范围或币种的数字直接平均。

数据权限按域分配：财务 worker 不必读取人事明细，外部研究 worker 不接触客户数据。最终报告中的每个数字都回链到查询和 snapshot。

### 13.3 自我进化 Agent

候选生成、评测和发布必须由不同责任主体完成。多个 mutation worker 并行提出 prompt、skill 或 policy 变体；可信 evaluator 在 held-out 与安全集上评估；selection service 根据预注册规则选择；release controller 做 canary 和回滚。

如果候选 Agent 可以通过委派影响 evaluator，所谓进化就失去独立门禁。委派图、数据血缘和权限必须证明 candidate family 没有接触 held-out 标签，也没有修改评分逻辑。多 Agent 在这里的最大价值不是“群体智慧”，而是实现实验隔离和制衡。

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

这段伪代码的重点是：委派前缩权和预留预算，执行时隔离，返回时验证 schema 与 provenance，合并时重新检查系统级不变量。Subagent 的“完成”只是父任务的一个候选输入。

## 15. 设计原则总结

第一，单 Agent 是默认值，多 Agent 需要证明增量价值。第二，按可验证 artifact 和依赖关系拆任务，不按拟人角色拆任务。第三，区分 subroutine、subagent 与 handoff，并显式记录责任所有权。第四，权限随委派衰减，状态与工作区默认隔离。第五，先独立探索，再比较和合并，避免过早共识。第六，所有子结果都携带 provenance、验证和未决项。第七，局部通过不等于组合通过，合并后必须重验。第八，预算覆盖整棵任务树并为验证预留。第九，用分布式系统方法处理取消、重试、背压和孤儿任务。第十，以同成本单 Agent 和多 trial baseline 证明多 Agent 的真实收益。

多 Agent 的成熟标志不是屏幕上出现更多头像，而是组织能够精确回答：为什么要拆成这些执行者，每个执行者看到了什么、被允许做什么、产出了什么证据，冲突怎样处理，以及若其中一个犯错，系统为何仍可恢复。做到这些之后，“Agent 团队”才不再是 prompt theater，而成为可治理的计算拓扑。

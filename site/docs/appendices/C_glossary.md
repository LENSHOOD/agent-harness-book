# 附录 C：术语与本体边界

本书固定以下用法。产品文档可能采用不同名称，adapter（适配器）应做语义映射，而不是只做字符串对齐。

- **Model**：接收有限上下文并生成文本或动作建议的概率性策略（policy）。它不天然拥有持久状态、权限和外部真值。
- **Agent**：在任务范围内由模型动态选择观察或动作的执行者。Agent 是系统角色，不等于单次模型调用。
- **Agent System**：Model、Harness、Environment 与 Feedback 的完整组合，也是评估能力和风险的对象。
- **Harness**：将任务、模型与环境组织成持续执行的逻辑控制系统，负责 loop（循环）、context（上下文）、tools（工具）、state（状态）、policy（策略）、verification（校验）、observability（可观测性）与 evolution governance（演进治理）。
- **Agent Runtime**：承载 Agent loop、session 和模型交互的运行组件，例如供应商 CLI/core 或自研 loop。
- **Execution Runtime**：实际运行命令、浏览器、代码或连接器的环境，例如容器、VM 或受控远程执行器。
- **Environment**：Agent 可观察或改变的任务世界，包括 workspace、数据库、SaaS、日志和人类组织。它不等于一个 shell。
- **Feedback**：用于调整系统对动作质量或任务质量判断的信号；Observation 只有进入评价链路时才成为 feedback。
- **Workflow**：由代码预定义主要控制路径的执行结构。模型可在节点内被调用，但不拥有全部路由权。
- **Control Plane**：拥有 task、identity、policy、调度、配置与发布权威的逻辑平面。
- **Evidence Plane**：保存 artifact（产物）、trace（追踪）、effect 和独立验证结果的逻辑平面，不依赖聊天历史来证明完成。
- **Evolution Plane**：生成、评价和发布 memory（记忆）、Harness 与 model 候选项的系统，并受治理平面约束。
- **ACI**：Agent-Computer Interface，模型与计算环境之间的动作和观察接口。
- **Action**：Agent 提议的规范化动作（action）。在授权与执行之前，它还不代表现实副作用。
- **Observation**：动作、环境或策略返回的可观察结果，包含状态、诊断与 artifact 引用。
- **Effect**：已经产生或可能产生外部权威状态变更的动作结果。
- **Effect Ledger**：记录 effect intent（意图）、幂等键、提交状态、outcome 和 reconciliation（对账）过程的账本。
- **CompletionContract**：目标、交付物、不变量、验收、证据、权限、预算与停止条件组成的版本化合同。
- **Candidate**：Agent 提交给外部完成门的候选 artifact（产物）；尚未获得业务提交权。
- **VerificationResult**：由特定 verifier（校验器）在固定环境下输出的结构化合同检查结果。
- **EvidencePackage**：把输入、candidate、artifact、effect、policy、verification、approval 与最终提交串联起来的机器可读证据。
- **Artifact**：有地址、hash、媒体类型、生产者和分类的持久化交付物或中间对象。
- **Checkpoint**：用于恢复的任务状态、事件 offset、workspace 与 pending effect 引用；不等于上下文摘要。
- **Compaction**：将长上下文转换为可继续推理的较短表示，属于有损投影，不是长期记忆。
- **Memory**：跨推理或跨任务保留的事实、情景、程序或策略状态；必须声明 scope（范围）、owner（责任人）和生命周期。
- **Skill**：按需加载的程序化知识包，可能包含指令、脚本和资源，属于软件供应链对象。
- **Handoff**：将工作责任从一个 Agent 或节点转移给另一个，带出结构化目标、状态、artifact、权限和未决项。
- **Capability lease**：绑定 actor（主体）、资源、动作、purpose（用途）、租户和 TTL 的临时授权。
- **Held-out / sealed test**：候选不可见、由独立评价服务在预定时机使用的数据或检查集。
- **Canary**：在受限真实流量和限定影响范围内部署候选版本并持续监控。
- **Harness evolution**：对 prompt、工具、上下文、路由、工作流或 runtime profile 的受控优化，不等同于模型权重训练。
- **Reward hacking**：提高评分却偏离真实目标或破坏评价完整性的行为。
- **Lineage**：追踪版本来源关系，覆盖父项、数据、mutation、实验、发布、事故和退役。

最容易混淆的三组边界是：Agent Runtime 决定下一步，Execution Runtime 执行动作；Memory 保存跨期经验，Compaction 只压缩当前上下文；Harness 可以包含 policy adapter（策略适配器），但根授权和 release authority（发布授权）不应由候选 Harness 自行修改。

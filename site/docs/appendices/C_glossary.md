# 附录 C：术语与本体边界

本书固定以下用法。产品文档可能采用不同名称，adapter 应映射语义，而不是仅按字符串对齐。

- **Model**：接收有限上下文并提出文本或动作的概率性策略；不天然拥有持久状态、权限和外部真值。
- **Agent**：在任务范围内由模型动态选择观察或动作的执行者。Agent 是系统角色，不等于单次模型调用。
- **Agent System**：Model、Harness、Environment 与 Feedback 的完整组合，是能力与风险的实际评价对象。
- **Harness**：把任务、模型与环境组织成持续执行的逻辑控制系统，负责 loop、context、tools、state、policy、verification、observability 与 evolution governance。
- **Agent Runtime**：承载 Agent loop、session 和模型交互的运行组件，如供应商 CLI/core 或自研 loop。
- **Execution Runtime**：实际运行命令、浏览器、代码或连接器的环境，如容器、VM 或受控远程执行器。
- **Environment**：Agent 可观察或改变的任务世界，包括 workspace、数据库、SaaS、日志和人类组织；不等于一个 shell。
- **Feedback**：改变系统对动作或任务质量判断的信号；Observation 只有进入评价时才成为 feedback。
- **Workflow**：由代码预定义主要控制路径的执行结构；可在节点中调用模型，但模型不拥有全部路由权。
- **Control Plane**：拥有 task、identity、policy、调度、配置与发布权威的逻辑平面。
- **Evidence Plane**：保存 artifact、trace、effect 和独立验证结果的逻辑平面；不依赖聊天历史证明完成。
- **Evolution Plane**：生成、评价和发布 memory/Harness/model 候选的系统；受治理平面约束。
- **ACI**：Agent-Computer Interface，模型与计算环境之间的动作和观察接口。
- **Action**：Agent 提议的规范化动作；在授权和执行前还不是现实副作用。
- **Observation**：动作、环境或策略返回的可观察结果，带状态、诊断与 artifact 引用。
- **Effect**：已经或可能改变外部权威状态的动作结果。
- **Effect Ledger**：记录 effect intent、幂等键、提交状态、outcome 与 reconciliation 的账本。
- **CompletionContract**：目标、交付物、不变量、验收、证据、权限、预算与停止条件的版本化合同。
- **Candidate**：Agent 提交给外部完成门的候选 artifact；尚未获得业务提交权。
- **VerificationResult**：特定 verifier 在固定环境下对合同检查的结构化结果。
- **EvidencePackage**：连接输入、candidate、artifact、effect、policy、verification、approval 与最终提交的机器可读证据。
- **Artifact**：有地址、hash、媒体类型、生产者和分类的持久交付或中间对象。
- **Checkpoint**：恢复所需的任务状态、事件 offset、workspace 与 pending effect 引用；不等于上下文摘要。
- **Compaction**：将长上下文转换为可继续推理的较短表示；是有损投影，不是长期记忆。
- **Memory**：跨推理或跨任务保存的事实、情景、程序或策略状态；必须声明 scope、owner 和生命周期。
- **Skill**：按需加载的程序知识包，可能含指令、脚本和资源；属于软件供应链对象。
- **Handoff**：工作责任从一个 Agent/节点转移到另一个，携带结构化目标、状态、artifact、权限和未决项。
- **Capability lease**：绑定 actor、资源、动作、purpose、租户和 TTL 的临时授权。
- **Held-out / sealed test**：候选不可见、由独立评价服务在预定时机使用的数据或检查。
- **Canary**：在受限真实流量和影响范围内部署候选版本并监控。
- **Harness evolution**：对 prompt、工具、上下文、路由、工作流或 runtime profile 的受控优化，不等于模型权重训练。
- **Reward hacking**：提高测量分数却偏离真实目标或破坏评价完整性的行为。
- **Lineage**：版本从父项、数据、mutation、实验到发布、事故和退役的可追溯关系。

最容易混淆的三组边界是：Agent Runtime 决定下一步，Execution Runtime 执行动作；Memory 保存跨时经验，Compaction 只压缩当前上下文；Harness 可以包含 policy adapter，但根授权和 release authority 不应由候选 Harness 自行修改。

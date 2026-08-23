# 附录 C：术语表

- **Agent**：由模型动态管理工作流、使用工具并改变环境状态的系统。
- **Harness**：围绕模型的上下文、工具、循环、环境、安全、状态、验证和可观测运行时。
- **Runtime**：承载 Agent 循环或执行动作的运行组件；本文按语境区分 Agent Runtime 与 Execution Runtime。
- **ACI**：Agent-Computer Interface，模型与计算环境之间的动作和观察接口。
- **Completion Contract**：目标、交付物、不变量、验收、证据、权限和停止条件的版本化合同。
- **Evidence Package**：连接输入、artifact、检查、策略和外部效果的机器可读交付证据。
- **Effect Ledger**：记录副作用意图、幂等键、提交状态和对账结果的账本。
- **Compaction**：将长会话转换为可继续工作的较短表示，不等同于长期记忆。
- **Skill**：可按需加载的程序知识，可能包含指令、脚本和资源。
- **Handoff**：工作流责任从一个 Agent 转移给另一个 Agent。
- **Held-out**：候选不可见、用于独立评价的数据或检查。
- **Canary**：只在受限真实流量部署候选版本并监控。
- **Harness evolution**：对 prompt、工具、上下文、路由、工作流等运行时组件进行受控优化。
- **Reward hacking**：提高测量分数但偏离真实目标或破坏评价完整性。

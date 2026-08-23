# 第四章 Coding Agent 转折：真实仓库成为反馈环境

> 本章状态：正文初稿 v0.1。

2023 年的通用 Agent 热潮证明了模型可以循环调用工具，却没有证明它能稳定完成真实工作。Coding Agent 改变了问题形态：仓库提供持久状态，编译器、测试和版本控制提供外部反馈，patch 提供可审查的交付物。Harness 从“让模型继续思考”转向“让模型在环境里形成可验证闭环”。

## 1. 从聊天记录到工作树

早期框架倾向把任务状态放在消息、计划列表或向量记忆中。软件工程的权威状态却在文件系统、Git、依赖环境和测试结果里。模型不必在上下文复述全部代码，只需要能搜索、定位、修改、执行和回读。这一变化奠定了现代 Harness 的基本形态：薄决策循环，厚环境适配。

Aider 的 repository map 用代码图和 token budget 选择相关符号，使模型在有限上下文中获得仓库结构，而不是粗暴注入所有文件。[Aider Repository Map](https://aider.chat/docs/repomap.html) SWE-agent 进一步提出 ACI，即 Agent-Computer Interface：命令、观察格式和反馈设计会显著影响同一模型的解题能力。[SWE-agent](https://arxiv.org/abs/2405.15793)

这说明接口不是模型之外的包装。一个返回数万行终端噪声的 shell，与一个保留退出码、截断策略、错误定位和可追溯 artifact 的 shell，对模型来说是两个不同环境。

## 2. 可执行反馈改变了规划

传统规划假设动作模型相对明确；真实仓库中的依赖、隐含约束和测试常常只有执行后才暴露。现代 coding loop 因而更像在线控制：观察局部状态，提出最小变更，运行检查，根据误差修正。

```text
issue → inspect → hypothesis → patch → test
                    ↑              │
                    └── diagnose ──┘
```

成功不再取决于一次生成完整方案，而取决于 Harness 是否让失败变得可诊断。命令超时、测试失败、环境损坏和权限拒绝必须具有不同语义；否则模型会把基础设施问题误解为代码问题。

## 3. CodeAct 与统一动作空间

CodeAct 研究表明，让 Agent 通过可执行代码组织复杂工具交互，可以减少大量逐个 JSON tool call 的往返，并利用编程语言的循环、变量和组合能力。[Executable Code Actions](https://arxiv.org/abs/2402.01030) 这条路线后来体现在 Code Mode、sandbox script 和“计算留在环境、只把结果带回上下文”等设计中。

但统一 shell 或代码动作也扩大了权限面。表达力越强，越需要沙箱、网络策略、凭证代理和确定性审计。Coding Agent 的历史因此同时推动了自治与约束。

## 4. OpenHands 的分离

OpenHands 将 Agent 的决策与 Runtime 的执行显式分开，通过动作、观察和事件流连接；Runtime 可以是 Docker 或远程执行环境。[OpenHands Runtime Architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime) 这种分离使模型策略可以替换，环境生命周期、隔离和日志则由另一层负责。

它对企业架构的启示不是必须采用其类结构，而是：不让模型循环直接持有宿主进程。Agent 产生规范化 action，Runtime 验证并执行，observation 再成为下一步输入。由此可以在协议边界插入策略、录制、重放和模拟器。

## 5. Benchmark 的双重作用

SWE-bench 把真实 GitHub issue、仓库和测试组成可执行评测，使模型与 Harness 的组合成为测量对象，而非只测代码补全。[SWE-bench](https://arxiv.org/abs/2310.06770) 它推动工具、搜索、编辑、上下文和验证快速演化，也暴露一个事实：排行榜分数同时包含模型、Harness、环境构建和评测质量，不能简单归因给模型。

后来 SWE-bench Verified 的修订与退役进一步表明，环境反馈虽比文本 judge 更硬，也不是绝对真理。测试可能错误，公开样本可能污染，Agent 可能投机。Coding Agent 只是提供了更好的实验场，而不是自动解决验证问题。

## 6. 现代 Harness 的形成

从 Aider、SWE-agent、CodeAct 和 OpenHands，可以看见五个后来成为主流的原则：上下文按需编译；工具接口针对模型优化；执行发生在可控环境；每个动作产生结构化观察；完成由外部证据决定。Claude Code、Codex、Cursor 等产品的差异主要发生在这些原则的工程取舍，而不是是否拥有一个 `while` 循环。

Coding Agent 转折的真正意义，是把 Agent 从语言产品变成运行时问题。模型仍负责提出高熵决策，但文件、进程、权限、测试、状态和提交由软件系统承载。Harness 由此成为模型与真实世界之间的责任边界。

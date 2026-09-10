# 序：为什么现在需要一本 Harness 小书

同一模型放进不同的 Agent 产品后，表现可能看起来完全不同。
差异来自模型之外的上下文、工具、环境、权限、恢复机制和验证机制。
本书把这组能力统一叫做 Agent Harness。

Harness 不是某个框架品牌，也不只是 `while model calls tools`。
它是模型和真实世界之间的运行时与治理层。
它把人的意图编译成任务，把环境状态编译成上下文，把模型动作约束为受控副作用，再把外部结果编译成可审查证据。

本书面向企业 Agent 平台架构师和高级工程师。
历史篇解释从规划、BDI、ReAct 到 coding agent 的转折；原理篇给出状态机、上下文、工具、安全、验证和多 Agent 的设计；产品篇研究 Claude Code、Codex、Cursor、DeepSeek Harness 与 OpenHands；进化篇区分任务内、跨任务、Harness 和模型四层；实践篇给出供应商无关的参考架构和迁移路线。

全书的核心公式是：

```text
Agent System Capability = Model × Harness × Environment × Feedback
```

乘法意味着任一项接近零，整体能力就会显著下降。
强模型不能弥补关键上下文被截断、工具危险、环境异常，或 verifier 错误。
再完善的 Harness 也无法无限越过模型能力边界。

全书资料维护至 2026-08-28；快速变化的产品章会在章首标出更精确的资料截面。
功能会过时，但设计原则更稳。
书中明确区分公开事实、论文结果和作者综合判断；内部使用不改变证据边界。

# 序：为什么现在需要一本 Harness 小书

同一个模型放进不同 Agent 产品，表现可能像两个不同的系统。差异来自模型之外的上下文、工具、环境、权限、反馈、恢复和验证。本书把这组能力统称为 Agent Harness。

Harness 不是一个框架品牌，也不只是 `while model calls tools`。它是模型与真实世界之间的运行时和治理层：把人的意图编译成任务，把环境状态编译成上下文，把模型动作变成受控副作用，再把外部结果编译成证据。

本书面向企业 Agent 平台架构师和高级工程师。历史篇解释从规划、BDI、ReAct 到 coding agent 的转折；原理篇给出状态机、上下文、工具、安全、验证和多 Agent 设计；产品篇研究 Claude Code、Codex、Cursor、DeepSeek Harness 与 OpenHands；进化篇区分任务内、跨任务、Harness 和模型四层；实践篇给出供应商无关参考架构和迁移路线。

全书的核心公式是：

```text
Agent System Capability = Model × Harness × Environment × Feedback
```

乘法意味着任一项接近零，整体都可能失败。强模型无法弥补被截断的关键上下文、危险工具、损坏环境或错误 verifier；厚 Harness 也不能无限跨越模型能力边界。

全书资料维护至 2026-08-28；快速变化的产品章另在章首标出更精确的资料截面。功能会过时，设计原则应更稳定。书中区分公开事实、论文结果和作者综合判断；内部使用不改变证据要求。

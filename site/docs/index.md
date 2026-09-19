---
layout: home

hero:
  name: "Agent Harness"
  text: "从执行脚手架到自我进化系统"
  tagline: 企业 Agent 平台架构、主流产品设计、自我进化与工程实践
  actions:
    - theme: brand
      text: 开始阅读
      link: /chapters/00_preface
    - theme: alt
      text: 下载完整版 PDF
      link: /agent-harness-book/downloads/agent_harness_book.pdf

features:
  - title: 完整设计体系
    details: 状态机、上下文、工具、安全、验证、多 Agent、可观测性与评测。
  - title: 五个产品案例
    details: Claude Code、OpenAI Codex、Cursor、DeepSeek Harness 与 OpenHands。
  - title: 四层 Agent 进化
    details: 任务内、跨任务、Harness 与模型进化，以及可信门禁和回滚。
  - title: 企业落地路线
    details: 参考架构、Agent SDD、成熟度模型、Build-vs-Buy 与迁移步骤。
---

## 关于本书

同一个模型放进不同 Agent 产品，表现可能像两个不同系统。差异来自模型之外的上下文、工具、环境、权限、反馈、恢复和验证。本书把这组能力统称为 **Agent Harness**。

```text
Agent System Capability = Model × Harness × Environment × Feedback
```

全书共30章，资料维护至2026-09-19；快速变化的产品事实以各章声明的版本为准。这一版修订了运行控制、安全边界、实验方法与术语，并补入托管Harness、子代理上下文模式和近期自我进化研究。

[运行书中的参考案例](https://github.com/LENSHOOD/agent-harness-book/tree/main/examples)：代码修复、经营分析和进化门禁均有本地入口。测试使用明确的数据与环境假设，不代表供应商端到端或生产效果认证。

上述乘法表达各因素的相互制约，是概念比喻，不是可直接计算能力分数的公式。

> 本书用于技术交流。快速变化的产品功能可能过时，设计原则比产品快照更稳定。

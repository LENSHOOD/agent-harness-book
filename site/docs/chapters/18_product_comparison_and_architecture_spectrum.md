# 第十八章 产品比较：不要用一张总分表掩盖架构差异

> 资料截面：2026-08-27。本章比较公开能力与系统边界，不把不同 benchmark、任务分布或厂商自报指标合并为脱离场景的总分。

产品比较的第一原则是比较“系统在特定任务、预算和环境中的行为”，而不是给品牌排一个脱离场景的总名次。模型、Harness、工具、sandbox、任务合同和 verifier 共同决定结果；任一变量不同，都只能支持系统对系统结论，不能直接推出模型强弱。

## 1. 五种代表性重心

| 系统 | 公开架构重心 | 最自然的接入面 | 主要优势 | 主要集成风险 |
|---|---|---|---|---|
| Claude Code | loop + lifecycle extensions | Agent SDK / CLI | hooks、skills、subagent、MCP 组合成熟 | 配置与扩展供应链复杂；业务完成需外置 |
| Codex | protocolized core | App Server / SDK / exec | 双向事件、线程生命周期、多产品复用 | JSON-RPC lite 适配与版本兼容；不可把 turn 当 task |
| Cursor | IDE-native harness | IDE / cloud agent | 动态上下文、模型特化、在线产品信号 | 专有内部选择器难独立审计；云端出网风险 |
| DeepSeek Harness | reversible plugin graph | profile / bundle / SDK | 运行时可组合、可 patch、适合实验 | developer preview；配置图与插件供应链治理重 |
| OpenHands | Agent/Runtime split | event/runtime API | 开源可观测、执行环境可替换 | 自运维隔离、镜像、durability 的成本高 |

表中的事实分别来自各产品官方资料；它描述的是 2026-08-27 截面，不是永久能力清单。[Claude loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)、[Codex App Server](https://openai.com/index/unlocking-the-codex-harness/)、[Cursor harness](https://cursor.com/blog/continually-improving-agent-harness)、[dsh architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)、[OpenHands runtime](https://docs.openhands.dev/openhands/usage/architecture/runtime)

## 2. 统一评价坐标

建议用六个坐标替代总分：

1. **任务匹配度**：真实任务族的完成率与失败成本；
2. **控制力**：身份、权限、网络、审批、取消和版本是否可由平台掌握；
3. **证据性**：能否导出动作、观察、artifact、策略决定与 verifier 结果；
4. **耐久性**：中断、重试、恢复和外部副作用对账能力；
5. **可替换性**：任务与证据契约是否独立于供应商消息格式；
6. **运营经济性**：端到端成本、时延、人工介入和平台维护成本。

每项都要在相同 completion contract、workspace snapshot、权限和预算下多 trial 测量（见第十二章）。GitHub stars、营销 benchmark 和一次成功 demo 最多用于候选发现，不能作为企业选型证据。

## 3. 协议统一的限度

可以统一的是可观察语义：Task、Action、Observation、Artifact、Approval、Checkpoint、VerificationResult。不能强制统一的是每个模型内部 reasoning、原生 tool shape、上下文压缩策略和产品交互。Codex 官方也指出，跨提供方协议容易收敛到共同子集，从而难以表达更丰富的 provider-specific session 和 tool 语义。[App Server](https://openai.com/index/unlocking-the-codex-harness/)

因此 adapter 应“双轨保存”：向上输出 canonical event，向下保留原始 payload 与版本。若某产品支持 fork 而统一层没有，就以 capability negotiation 暴露，不要静默丢弃；若某产品无法导出关键证据，则降低其可自动提交的风险等级。

## 4. 常见失效比较

最常见的错误是给每个产品不同模型、不同时间和不同权限，然后比较最终通过率。另一个错误是只比较 token 单价，却忽略失败重试、人工接管、环境冷启动与错误提交。第三个错误是把厂商内部指标当共同口径，例如 Cursor 的 Keep Rate 与测试通过率衡量的不是同一对象。

一个可审计的 POC 应发布完整配置矩阵：

```yaml
comparison:
  task_suite: repo-maintenance-v3
  workspace_snapshot: fixed
  trials_per_case: 5
  budgets: {wall_minutes: 30, model_usd: 8}
  permissions: code-medium-v4
  verifier: clean-room-v6
  report_slices: [task_type, repo_size, risk, runtime, model]
```

## 5. 组合战略

多数企业不需要挑选唯一赢家。更稳妥的结构是：供应商/开源 Agent 负责高变化的决策循环，企业控制面拥有 task、identity、policy、workspace、evidence、eval 和 commit authority。低风险 IDE 工作可直接使用 Cursor 或 Claude Code；需要深度嵌入的产品可接 App Server；需要研究可变 Harness 可使用 dsh；需要掌握执行环境实现可研究 OpenHands。

这一比较的最终结论不是“哪个最好”，而是哪些边界必须由企业拥有。第二十六至二十九章将把这些产品差异转成可迁移的控制面和分阶段路线图。

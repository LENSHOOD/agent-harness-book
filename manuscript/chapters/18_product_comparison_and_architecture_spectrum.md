# 第十八章 产品比较：不要用一张总分表掩盖架构差异

> 资料截面：2026-08-27。本章比较公开能力与系统边界，不把不同 benchmark、任务分布或厂商自报指标合并为脱离场景的总分。

产品比较的第一原则是先比较“系统在特定任务、预算和环境中的行为”，再讨论品牌排名。品牌排行如果脱离具体场景，通常不可靠。模型（model）、Harness、工具、sandbox、任务合同（completion contract）和 verifier（验证器）都会共同影响结果。只要有任意变量变化，结论就只能支持“某个系统组合在哪种场景更适配”的判断，不能直接推出模型强弱。

## 1. 五种代表性重心

| 系统 | 公开架构重心 | 最自然的接入面 | 主要优势 | 主要集成风险 |
|---|---|---|---|---|
| Claude Code | loop + lifecycle extensions | Agent SDK / CLI | hooks、skills、subagent、MCP 组合成熟 | 配置与扩展供应链复杂；业务完成需外置 |
| Codex | protocolized core | App Server / SDK / exec | 双向事件、线程生命周期、多产品复用 | JSON-RPC lite 适配与版本兼容；不可把 turn 当 task |
| Cursor | IDE-native harness | IDE / cloud agent | 动态上下文、模型特化、在线产品信号 | 专有内部选择器难独立审计；云端出网风险 |
| DeepSeek Harness | reversible plugin graph | profile / bundle / SDK | 运行时可组合、可 patch、适合实验 | developer preview；配置图与插件供应链治理重 |
| OpenHands | Agent/Runtime split | event/runtime API | 开源可观测、执行环境可替换 | 自运维隔离、镜像、durability 的成本高 |

表中的事实分别来自各产品官方资料；它描述的是 2026-08-27 截面，不是永久能力清单。

[Claude loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)、[Codex App Server](https://openai.com/index/unlocking-the-codex-harness/)、[Cursor harness](https://cursor.com/blog/continually-improving-agent-harness)、[dsh architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)、[OpenHands runtime](https://docs.openhands.dev/openhands/usage/architecture/runtime)

## 2. 统一评价坐标

建议用六个坐标替代总分，避免把复杂系统压成单一数字：

1. **任务匹配度**：真实任务族的完成率与失败成本；
2. **控制力**：身份、权限、网络、审批、取消和版本是否可由平台掌握；
3. **证据性**：能否导出动作、观察、artifact、策略决定与 verifier 结果；
4. **耐久性**：中断、重试、恢复和外部副作用对账能力；
5. **可替换性**：任务与证据契约是否独立于供应商消息格式；
6. **运营经济性**：端到端成本、时延、人工介入和平台维护成本。

每项都要在相同 completion contract（任务完成契约）、workspace snapshot（工作区快照）、权限和预算下做多次 trial（试运行）测量，方法见第十二章。GitHub stars、营销 benchmark 和一次成功 demo 可以用于候选发现，但它们最多只能作为起始线索，不能直接作为企业选型证据。

## 3. 协议统一的限度

可以统一的是可观察语义，即 Task、Action、Observation、Artifact、Approval、Checkpoint、VerificationResult。不能强制统一的是每个模型内部 reasoning（推理过程）、原生 tool shape（工具形态）、上下文压缩策略和产品交互方式。Codex 官方也强调，跨提供方协议容易收敛到共同子集，从而难以表达更丰富的 provider-specific session（供应商特定会话语义）和 tool 语义。[App Server](https://openai.com/index/unlocking-the-codex-harness/)

因此 adapter（适配器）应采用“双轨保存”。一条向上输出 canonical event（规范事件），另一条向下保留原始 payload（载荷）与版本。若某产品支持 fork 而统一层没有对应表达，就要通过 capability negotiation（能力协商）暴露出来，不要静默丢弃。若某产品无法导出关键证据，则应降低其可自动提交的风险等级。

## 4. 常见失效比较

最常见的错误是给每个产品配不同模型、不同时间窗和不同权限，再直接比较最终通过率。另一个错误是只比较 token 单价，却忽略失败重试、人工接管、环境冷启动与错误提交成本。第三个错误是把厂商内部指标当作共同口径来比，例如 Cursor 的 Keep Rate 与测试通过率衡量的不是同一对象。

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

多数企业不需要挑选唯一赢家。更稳妥的结构通常是供应商或开源 Agent 负责高变化的决策循环。企业控制面则保留 task（任务）、identity（身份）、policy（策略）、workspace（工作区）、evidence（证据）、eval（评估）与 commit authority（提交权限）。

低风险 IDE 工作可直接使用 Cursor 或 Claude Code。需要深度嵌入的平台可接 App Server。需要研究可变 Harness 的团队可使用 dsh。若要掌握执行环境实现细节，可选择 OpenHands。

这一比较的最终结论不是“哪个最好”，而是哪些边界必须由企业自己拥有。第二十六至二十九章将把这些产品差异转成可迁移的控制面设计，以及可执行的分阶段路线图。

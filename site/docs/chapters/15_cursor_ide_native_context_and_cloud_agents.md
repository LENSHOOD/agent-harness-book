# 第十五章 Cursor：IDE 原生上下文与云端 Agent

> 资料截面：2026-08-27。Cursor 的实现并非完全开源，本章区分官方披露与本书的架构归纳。

Cursor 的差异化不是“也能调用 shell”，而是把编辑器状态、代码检索、终端、模型选择和远程执行组织成连续体验。它展示了 Harness 的另一条路线：不是先设计通用 runtime 再接 UI，而是从开发者工作流反向塑造上下文与工具。

## 1. 动态上下文发现

Cursor 把较少信息静态塞入 prompt（提示语输入），让 Agent 按需检索更多上下文。官方列出的做法包括：把长工具输出写入文件、把历史会话作为可搜索文件、按需加载 skill、把 MCP（Model Context Protocol）工具描述同步为目录，以及把集成终端输出映射为文件。[Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery) 这里的核心抽象不是“文件万能”。其要点是把大对象拆成有地址的外部状态。模型先看索引，再决定读取哪一部分内容。

官方 A/B 测试（同一任务对比两套配置）报告称，在确实调用 MCP 工具的 run（运行实例）中，按需发现工具描述使总 Agent token 减少 46.9%。报告还指出结果会随已安装 MCP 的数量高度变化。[Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery) 这项结果属于厂商内部实验，不能外推成所有 Harness 的固定收益。更合适的用法是当作可复现实验假设，比较静态注入与目录发现条件下的 token、工具选择正确率和任务成功率。

动态发现也有失效边界。若索引命名错误、文件过期，或 Agent 不知道该搜索什么，重要信息就会从“上下文噪声”变成“不可发现状态”。因此需要测量 context recall（上下文召回率）：完成任务所需的权威资料中，有多少在决策前被读取。这个指标不能被 token 下降替代，需配合任务成功率看（见第七章）。

## 2. Model-specific Harness

Cursor 公开说明会按模型及版本定制 prompt（提示语）和工具格式。例如，不同模型在训练中熟悉的编辑动作不同。若用不熟悉的格式，推理成本会上升，错误更容易发生。模型切换时，Harness 也会切换到对应 profile，但新模型仍要消费前一个模型产生的历史上下文。[Harness evolution](https://cursor.com/blog/continually-improving-agent-harness) 这说明“模型无关 canonical action（标准动作语义）”与“模型面向的 tool view（工具视图）”应分成两层：平台内部语义保持稳定，模型看到的名称、schema（数据结构定义）、示例和返回压缩可以按 profile 编译。

一个反例是为跨模型统一而强制所有模型使用同一编辑工具。接口看起来更整齐，但成功率和 token 可能下降。另一个极端是每个模型都有完全私有的 action（动作）语义，此时 trace（决策链路追踪）和 eval（评测）无法比较。更稳妥的边界是共享效果语义，同时允许表现形式变化（见第八章）。

## 3. 在线信号与离线评测

Cursor 披露其同时使用公开和内部 benchmark（基准测试）、在线 A/B、时延、token 效率、工具错误、cache hit（缓存命中率），以及代码在一段时间后仍被保留的 Keep Rate（留存率）。[Harness evolution](https://cursor.com/blog/continually-improving-agent-harness) 其中 Keep Rate 比“用户点击接受”更接近长期效用，但仍不是正确性的充分条件。用户可能没发现缺陷，而代码也可能因项目中止被保留。企业应把行为信号与确定性测试、事故记录和人工抽检组合，而不是让单一指标驱动进化决策（见第十九、二十四章）。

## 4. 从前台审批到云端自治

Cursor Background Agents（后台 Agent）在隔离的 Ubuntu 机器中异步运行。它们默认可联网、可安装包并自动执行终端命令。官方安全说明明确提示这会带来 prompt injection（提示词注入）和数据外泄风险。[Background Agents](https://docs.cursor.com/background-agent) 本地前台 Agent 默认对敏感动作要求人工批准。远程后台执行则需要更强的环境、网络和凭证控制。[Agent security](https://docs.cursor.com/agent/security)

这揭示了一个重要规律：交互模式变化会直接改变威胁模型。人坐在 IDE 前并不等于每一步都被可靠审查。无人值守云端也不应把所有命令都设为自动批准。平台需要按运行模式选择 policy profile（策略配置文件），并把出网 allowlist（白名单）、仓库权限、secret 注入和最大运行时长设成独立硬边界。

## 5. Hooks 与企业控制点

Cursor hooks 通过 stdio JSON 在 Agent 生命周期前后运行。它们可观察、可阻断，也可修改部分行为，并支持项目、用户和企业层配置。[Hooks](https://docs.cursor.com/hooks) 这类点位适合接入格式化、PII（个人身份信息）/secret 扫描、SQL 写入门禁和审计。
但要注意：某些事件是 fire-and-forget（发送即忘），云端早期只读探索阶段也不运行全部 hooks。集成方必须逐事件确认是否可阻断，不能因为“支持 hooks”就认为已具备完整策略控制。

```text
IDE state → context index → model-specific tool view
         → local or cloud execution → diff/terminal feedback
         → online signal + offline eval → harness release
```

## 6. 设计判断

Cursor 最可迁移的经验是：上下文应可发现、工具应按模型适配、产品反馈应进入 Harness 评测。其局限在于专有实现使企业难以独立验证内部选择器和压缩器。平台接入时应优先获取结构化事件、workspace revision（工作区版本）、diff（差异）、命令结果和策略决定。若只能获得 UI 结果，就应将其定位为开发者工具，而不是企业任务运行时的唯一事实源。

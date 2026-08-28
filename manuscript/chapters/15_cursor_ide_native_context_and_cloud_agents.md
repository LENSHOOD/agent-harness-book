# 第十五章 Cursor：IDE 原生上下文与云端 Agent

> 资料截面：2026-08-27。Cursor 的实现并非完全开源，本章区分官方披露与本书的架构归纳。

Cursor 的差异化不是“也能调用 shell”，而是把编辑器状态、代码检索、终端、模型选择和远程执行组织成连续体验。它展示了 Harness 的另一条路线：不是先设计通用 runtime 再接 UI，而是从开发者工作流反向塑造上下文与工具。

## 1. 动态上下文发现

Cursor 把较少信息静态塞入 prompt，让 Agent 按需检索更多上下文。官方列出的做法包括：把长工具输出写入文件、把历史会话作为可搜索文件、按需加载 skill、把 MCP 工具描述同步为目录，以及把集成终端输出映射为文件。[Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery) 这里的核心抽象不是“文件万能”，而是把大对象变成带地址的外部状态，模型先看索引，再决定读取哪一部分。

官方 A/B 测试报告称，在确实调用 MCP 工具的 run 中，按需发现工具描述使总 Agent token 减少 46.9%，同时指出结果随已安装 MCP 数量高度变化。[Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery) 这是厂商内部实验，不能外推成所有 Harness 的固定收益；它更适合作为一个可复现实验假设：比较静态注入与目录发现时的 token、工具选择正确率和任务成功率。

动态发现也有失效边界。若索引命名差、文件过期或 Agent 不知道应搜索什么，重要信息可能从“上下文噪声”变成“不可发现状态”。因此需要测量 context recall：完成任务所需的权威资料中，有多少在决策前被读取；不能只看 token 下降（见第七章）。

## 2. Model-specific Harness

Cursor 公开说明会按模型及版本定制 prompt 和工具格式。例如不同模型训练时熟悉的编辑动作不同，使用不熟悉的格式会增加推理和错误；中途切换模型时，Harness 也随之切换，但新模型仍要消费前一个模型产生的历史。[Harness evolution](https://cursor.com/blog/continually-improving-agent-harness) 这说明“模型无关 canonical action”与“模型面向的 tool view”应是两层：平台内部语义稳定，模型看到的名称、schema、示例和返回压缩可按 profile 编译。

反例是为了跨模型统一而强制所有模型使用同一编辑工具。接口表面更整齐，实际成功率和 token 可能下降。另一个极端是每个模型拥有完全私有的 action 语义，使 trace 和 eval 无法比较。正确边界是共享效果语义、允许表现形式变化（见第八章）。

## 3. 在线信号与离线评测

Cursor 披露其同时使用公开/内部 benchmark、在线 A/B、时延、token 效率、工具错误、cache hit，以及代码在一段时间后仍被保留的 Keep Rate。[Harness evolution](https://cursor.com/blog/continually-improving-agent-harness) Keep Rate 比“用户点击接受”更接近长期效用，但仍不是正确性的充分条件：用户可能没发现缺陷，代码也可能因项目中止而保留。企业应把行为信号与确定性测试、事故和人工抽检组合，而不是让单一代理指标驱动进化（见第十九、二十四章）。

## 4. 从前台审批到云端自治

Cursor Background Agents 在隔离的 Ubuntu 机器中异步运行，默认可联网、可安装包并自动执行终端命令；官方安全说明明确提示这会带来 prompt injection 和数据外泄风险。[Background Agents](https://docs.cursor.com/background-agent) 本地前台 Agent 默认对敏感动作要求人工批准，而远程后台执行需要更强的环境、网络和凭证控制。[Agent security](https://docs.cursor.com/agent/security)

这揭示了一个重要规律：交互模式变化会改变威胁模型。人在 IDE 前并不等于每一步都可靠审查；无人值守云端也不应简单地把所有命令设为自动批准。平台需要按运行模式选择 policy profile，并将出网 allowlist、仓库权限、secret 注入和最大运行时长设为独立硬边界。

## 5. Hooks 与企业控制点

Cursor hooks 通过 stdio JSON 在 Agent 生命周期前后运行，可观察、阻断或修改部分行为，并支持项目、用户和企业层配置。[Hooks](https://docs.cursor.com/hooks) hooks 很适合接入格式化、PII/secret 扫描、SQL 写入门和审计。但某些事件是 fire-and-forget，云端早期只读探索阶段也不运行全部 hooks；集成方必须逐事件确认是否可阻断，不能因“支持 hooks”就推断获得完整策略控制。

```text
IDE state → context index → model-specific tool view
         → local or cloud execution → diff/terminal feedback
         → online signal + offline eval → harness release
```

## 6. 设计判断

Cursor 最可迁移的经验是：上下文应可发现、工具应适配模型、产品反馈应进入 Harness 评测。其局限是专有实现使企业难以独立验证内部选择器和压缩器。平台接入时应优先获取结构化事件、workspace revision、diff、命令结果和策略决定；若只能获得 UI 结果，就把它定位为开发者工具，而不是企业任务运行时的唯一事实源。

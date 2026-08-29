# 第十三章 Claude Code：薄循环、厚运行时

> 资料截面：2026-08-27。产品行为会持续变化；本章只把官方文档公开的行为视为事实，未公开内部实现均标为架构推断。

Claude Code 最值得研究的不是某条提示词，而是它把一个极薄的“模型—工具—观察”循环包在了较厚的会话、权限、上下文和扩展系统里。Claude Agent SDK 的官方说明把循环写得很直接：接收 prompt，模型产生文本或工具调用，SDK 执行工具并回传结果，直到模型不再请求工具，最后产生带 token、费用和 session id 的结果消息。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 这与第六章的耐久状态机并不矛盾：前者描述一次存活进程里的控制逻辑，后者描述企业平台必须补上的崩溃恢复和副作用语义。

## 1. 可观察的系统分层

从公开接口可确认的结构可以整理为四层：

| 层 | 公开能力 | 平台集成时应保留的边界 |
|---|---|---|
| 会话层 | session、resume、消息流、成本和结果 | 平台 task id 不等同于 Claude session id |
| 决策层 | 模型、effort、turn/budget、自动压缩 | 供应商“停止”不等同于业务完成 |
| 能力层 | 内置工具、MCP、skills、subagents | 工具可见性不等同于工具授权 |
| 控制层 | permission mode、hooks、sandbox | hook 是策略执行点之一，不是唯一安全边界 |

官方把 Claude Code 的扩展面概括为 `CLAUDE.md`、Skills、subagents、hooks、MCP、plugins 和 agent teams。[扩展总览](https://code.claude.com/docs/en/features-overview) 这些机制处在循环的不同位置：规则提供持续上下文，skill 提供按需程序知识，subagent 以独立上下文执行，hook 在生命周期事件上运行，MCP 引入外部能力。把它们都翻译成“再加一段 prompt”会丢失最关键的时机、权限和隔离语义。

## 2. 上下文不是一段无限增长的聊天

Claude Code 会把 system prompt、工具定义、消息与工具结果放入上下文，并在接近上限时压缩。subagent 之所以同时有能力和成本价值，是因为它从新上下文开始，只把最终结果返回父会话，而不是把全部子轨迹复制回来。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 这印证了第七章的结论：上下文管理是一项有损编译工作，压缩摘要不能成为任务状态和完成证据的唯一载体。

一个常见失效场景是：主 Agent 把测试失败委派给子 Agent，子 Agent 返回“已修复”，但没有返回失败命令、工作区版本和实际 diff。主 Agent 的上下文变小了，证据也一起消失了。正确做法是让 artifact 和 verification result 进入平台证据面，文本总结只承担导航作用（见第十章）。

## 3. Hook 是可编程生命周期，不是万能策略层

官方 SDK 暴露 `PreToolUse`、`PostToolUse`、`Stop`、`SubagentStart/Stop`、`PreCompact` 等事件。`PreToolUse` 可以在执行前拒绝工具调用，`Stop` 可以校验终止结果；hook 运行在应用进程而非模型上下文里。[Hooks](https://code.claude.com/docs/en/hooks-guide) 因此它适合做格式校验、审计、阻断和上下文注入。

但 hook 有三个边界。第一，只有进入该生命周期的动作才会被拦截；旁路进程或共享凭证仍需执行环境控制。第二，多个配置层的 hook 需要明确合并顺序和失败策略。第三，用 LLM hook 判断高风险动作，仍然只是概率策略，不能替代确定性授权。企业集成应让平台 policy engine 保持最终权威，并把 Claude hook 当作靠近运行时的适配器。

## 4. Permission、sandbox 与凭证必须拆开

Anthropic 公开说明 Claude Code 的 sandbox 通过操作系统级文件与网络边界减少逐命令批准，并报告其内部使用中 permission prompts 减少 84%。这是供应商自报数据，实验环境和统计窗口不足以支持跨产品外推。[Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing) 更重要的设计不是该数字，而是“边界内自动、越界审批”：读写范围和网络目的地先受隔离约束，策略再决定具体动作是否需要批准。

平台仍要把认证与授权分开。能够以用户账号登录 Claude 服务，不代表该进程可以读取任意仓库、调用生产 API 或把数据发送到任意 MCP server。短期凭证应由平台在工具提交时注入，不应进入模型上下文；这与第九章的 capability lease 和 credential broker 相呼应。

## 5. 企业集成剖面

推荐把 Claude Agent SDK/CLI 放在 runtime adapter 之后：平台创建任务合同、租户身份和隔离工作区，adapter 启动 session 并把消息、工具调用、审批请求和结果映射成 canonical event。平台在外部执行 completion gate，并保存原始供应商事件引用。

```yaml
runtime_profile:
  provider: anthropic-claude-code
  version: pinned
  permission_mode: policy_mediated
  workspace: isolated
  network: allowlist
  completion_authority: external_verifier
  export:
    - session_id
    - tool_events
    - cost
    - artifacts
```

不要解析彩色终端输出，也不要让一次 Claude session 成为业务任务的唯一主键。CLI 适合人工交互和低耦合接入；SDK 适合需要结构化事件和生命周期控制的平台。若所需能力只在 CLI 暴露，应把它明确标记为兼容性债务。

## 6. 设计判断

Claude Code 的长处是把模型行为嵌入一个丰富、可扩展的开发者运行时；代价是扩展点很多，配置来源和供应链随之增大。对自研 Harness 最可迁移的原则有三条：循环保持简单；上下文、工具和控制面分离；扩展必须挂在有语义的生命周期上。最不可迁移的做法是复制某一版本的隐藏提示词，因为它既不稳定，也不能替代环境、权限和验证架构。

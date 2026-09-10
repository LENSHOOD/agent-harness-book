# 第十三章 Claude Code：薄循环、厚运行时

> 资料截面：2026-08-27。产品行为会持续变化；本章只把官方文档公开的行为视为事实，未公开内部实现均标为架构推断。

Claude Code 最值得研究的，不是一条“万能提示词”，而是它把一条很薄的“模型—工具—观察”循环，放在更厚的会话、权限、上下文和扩展系统里。Claude Agent SDK 的官方说明写得很直接：接收 prompt，模型输出文本或工具调用，SDK 执行工具并回传结果，直到模型不再请求工具，最后返回带 token、费用和 session id 的结果消息。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 这与第六章的耐久状态机不冲突：前者描述单个生命周期内的控制逻辑，后者描述企业平台必须补齐的崩溃恢复和副作用语义。

## 1. 可观察的系统分层

从公开接口可确认的结构可以整理为四层：

| 层 | 公开能力 | 平台集成时应保留的边界 |
|---|---|---|
| 会话层 | session、resume、消息流、成本和结果 | 平台 task id 不等同于 Claude session id |
| 决策层 | 模型、effort、turn/budget、自动压缩 | 供应商“停止”不等同于业务完成 |
| 能力层 | 内置工具、MCP、skills、subagents | 工具可见性不等同于工具授权 |
| 控制层 | permission mode、hooks、sandbox | hook 是策略执行点之一，不是唯一安全边界 |

官方把 Claude Code 的扩展面归纳为 `CLAUDE.md`、Skills、subagents、hooks、MCP、plugins 和 agent teams。[扩展总览](https://code.claude.com/docs/en/features-overview) 这些机制分别在循环里承担不同位置：规则负责持续上下文，skill 提供按需程序知识，subagent 以独立上下文执行，hook 在生命周期事件点运行，MCP 引入外部能力。若把它们都变成“再加一段 prompt”，最容易丢掉时机控制、权限边界和隔离语义。

## 2. 上下文不是一段无限增长的聊天

Claude Code 会把 system prompt、工具定义、消息与工具结果放入上下文，并在接近上限时压缩。subagent 的优势在于同时兼顾能力和成本，因为它从新上下文起步，只返回最终结果给父会话，而不是把全部子轨迹复制回来。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 这和第七章的结论一致：上下文管理是“有损编译”，压缩摘要不能当作任务状态和完成证据的唯一载体。

常见失效场景是：主 Agent 把测试失败委派给子 Agent，子 Agent 回“已修复”，却没回失败命令、工作区版本和实际 diff。主 Agent 的上下文随即变小，证据也跟着丢了。正确做法是让 artifact 和 verification result 进入平台证据面，文本总结只负责导航（见第十章）。

## 3. Hook 是可编程生命周期，不是万能策略层

官方 SDK 暴露 `PreToolUse`、`PostToolUse`、`Stop`、`SubagentStart/Stop`、`PreCompact` 等事件。`PreToolUse` 可在执行前拒绝工具调用，`Stop` 可校验终止结果；hook 在应用进程运行，而不是模型上下文里。[Hooks](https://code.claude.com/docs/en/hooks-guide) 因此它更适合做格式校验、审计、阻断和上下文注入。

hook 也有三个边界。第一，只有经过该生命周期的动作才会被拦截，旁路进程或共享凭证仍需环境控制。第二，多个配置层的 hook 要明确合并顺序和失败策略。第三，用 LLM hook 判定高风险动作，仍然是概率策略，不能替代确定性授权。企业集成时应让平台 policy engine 保持最终权威，把 Claude hook 当作贴近运行时的适配器。

## 4. Permission、sandbox 与凭证必须拆开

Anthropic 公开说明 Claude Code 的 sandbox 通过操作系统级文件与网络边界减少逐命令批准，并披露其内部场景中 permission prompts 减少了 84%。这是供应商自报数据，实验环境和统计窗口不足以支持跨产品外推。[Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing) 更关键的设计不是这个数字，而是“边界内自动、越界审批”：先用隔离约束读写范围和网络目的地，再由策略决定具体动作是否需要批准。

平台仍要把认证与授权分离。能用用户账号登录 Claude 服务，不代表进程就能读取任意仓库、调用生产 API，或向任意 MCP server 发送数据。短期凭证应在工具提交时由平台注入，不应进入模型上下文；这与第九章的 capability lease 和 credential broker 对齐。

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

不要解析彩色终端输出，也不要让一次 Claude session 变成业务任务的唯一主键。CLI 更适合人工交互和低耦合接入；SDK 更适合需要结构化事件和生命周期控制的平台。若关键能力只在 CLI 侧可见，应明确标注为兼容性债务。

## 6. 设计判断

Claude Code 的长处是把模型行为放到一个丰富且可扩展的开发者运行时里；代价是扩展点很多，配置来源和供应链也随之变复杂。对自研 Harness 可迁移的原则有三条：保持循环简洁；分离上下文、工具和控制面；把扩展挂在有语义的生命周期节点上。最不该迁移的方法是复制某个版本的隐藏提示词，因为它既不稳定，也不能替代环境、权限和验证架构。

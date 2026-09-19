# 第十三章 Claude Code：薄循环、厚运行时

> 资料截面：2026-09-19。Claude Code、Claude Agent SDK、Claude Managed Agents 与 Messages API 是不同接入面。本章依据已存档的官方文档与工程说明；托管内部实现属于厂商披露，未经过本书源码审计或端到端测试。

Claude Code 把“模型—工具—观察”循环放在会话、权限、上下文和扩展系统里。Claude Agent SDK 的官方说明描述了接收输入、执行模型请求的工具、回传结果，直到模型不再请求工具，最后返回带 token、费用和 session id 的结果消息的过程。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 本章把“薄循环、厚运行时”作为作者的架构归纳，不把它当作源码分层或性能结论。

## 1. 先选接入面，再讨论运行时

下表归纳公开产品面；接入建议是作者判断。不能因为它们都使用 Claude，就假定配置文件、事件名或恢复机制相同。

| 接入面 | 公开能力与运行责任 | 证据边界与集成判断 |
|---|---|---|
| Claude Code / CLI | 开发者交互、工具、会话及本机扩展 | 根据公开行为集成；本轮没有可据以审计完整内部实现的源码证据 |
| Claude Agent SDK | 在应用中控制 Agent 循环、消息流与生命周期 | 应用负责所部署进程与工作区；SDK 接口不能代替对底层运行时的审计 |
| Claude Managed Agents | 托管循环、持久 session、工具与执行环境接口 | 通过服务接口接入；内部恢复与存储语义以厂商说明为依据 |
| Claude Messages API | 模型请求、工具调用内容及显式压缩等接口 | 使用它自行组装循环，不会自动获得上述托管会话系统 |

Claude Code 的扩展面包括 `CLAUDE.md`、Skills、subagents、hooks、MCP、plugins 和 agent teams：规则提供持续上下文，skill 提供按需知识，子代理承接独立工作，hook 在生命周期节点运行，MCP 接入外部能力。[扩展总览](https://code.claude.com/docs/en/features-overview) Managed Agents 则把 session 日志、调用模型与路由工具的 Harness、执行代码的 sandbox 分开。这项架构说明发表于 2026 年 4 月 8 日，是本轮补收的既有材料，不能写成 9 月新架构。[Managed Agents 架构](https://www.anthropic.com/engineering/managed-agents)

## 2. 上下文不是一段无限增长的聊天

Claude Code 会把系统提示、工具定义、消息与工具结果放入上下文，并在接近上限时压缩。子代理用独立上下文承接工作、向父会话返回结果，可以减少父窗口负担。[Agent loop](https://code.claude.com/docs/en/agent-sdk/agent-loop) 但整个任务的费用取决于重复探索、并发数量与交接内容；父窗口变小不等于总 token 或延迟下降。

2026 年 9 月 14 日发布说明增加的是 **Messages API 的按需压缩 beta**：请求带顶层 `compaction` 参数及 `compact-2026-09-04` beta header，返回签名的 compaction block，后续请求用它替换此前消息，也可保留近期原文。这不能直接写成 Claude Code 的 CLI 选项或 Managed Agents 的同名接口。签名提供供应商定义的完整性边界，不证明摘要没有遗漏业务限制。[Claude Platform 发布说明](https://docs.anthropic.com/en/release-notes/api)

## 3. 九月配置与权限变化属于哪个产品

9 月 3 日，`ant` CLI 1.30.0 增加 `ant apply`：从仓库文件创建或更新 agents、environments、skills、memory stores 和 deployments，先展示计划供批准，再写入 `claude-lock.json`，使以后操作定位同一批资源。9 月 10 日，1.32.0 增加 `ant beta:sessions connect`，可跟随 Managed Agents 会话、发消息并批准或拒绝待处理调用。这些是 Claude Platform 的管理入口，不是 `claude` CLI 的配置别名。[Claude Platform 发布说明](https://docs.anthropic.com/en/release-notes/api)

同日 Managed Agents 的权限策略增加 `auto`：服务端逐次评估 Agent 或 MCP 工具调用，选择执行、拒绝或暂停等待批准；`agent.tool_use` 和 `agent.mcp_tool_use` 事件在 `evaluated_permission` 外增加 `evaluation`。集成方因此可记录“怎样作出决定”，但自动评估不等于企业已授权任何目标或数据范围。[Claude Platform 发布说明](https://docs.anthropic.com/en/release-notes/api)

Claude Code 的 hooks 是另一条控制路径，例如工具前后、停止及压缩前的生命周期处理。[Hooks](https://code.claude.com/docs/en/hooks-guide) hook 命令由宿主执行，SDK 回调由应用侧执行，不能把它们当成模型上下文里的文字。作者建议对插件更新做 hook 清单差异审查，记录执行身份、命令与权限变化；高风险变更重新审批，撤销时同时停止在途执行。工作区沙箱未必覆盖这些宿主动作，工具调用的审批记录也不能替代 hook 自身的审计。

## 4. 托管恢复的一条事件剖面

Managed Agents 的工程文章给出两种不同失败路径。下列顺序是对其架构的转述，函数名是文章中的接口示意，不是本书实际发送的 API 报文：[Managed Agents 架构](https://www.anthropic.com/engineering/managed-agents)

```text
工具执行环境退出 → Harness 收到工具错误 → 模型决定是否重试
                                      → 必要时重新 provision 环境
Harness 自身退出 → 新实例 wake(sessionId) → getSession(id)
                                      → 从已保存事件恢复
```

这项分离使执行容器故障不必带走会话日志，但不能推出外部动作恰好执行一次。若第三方写入已生效、工具响应却丢失，恢复日志仍可能不足以确定写入结果；此时应按第六章的不确定提交规则回读对账，而非直接重发。文章也描述凭证放在沙箱之外、MCP 经代理访问凭证库的设计；它是特定托管架构的披露，不能自动归到本地 Claude Code。

Claude Code 的 OS 级文件与网络 sandbox 另有官方说明，其内部场景中权限提示减少 84% 是供应商自报结果，不能外推成跨产品收益或安全指标。[Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

## 5. 企业集成剖面

若选择自行部署 SDK/CLI，作者建议由适配器管理进程、工作区和原始事件；若选择 Managed Agents，则另建服务适配器，映射资源版本、会话事件及逐调用权限评估，不能沿用本地进程假设。以下是**本书自定义平台契约**，需由自建适配器解析和转换，不能直接交给 Claude CLI、Agent SDK 或 `ant apply`；值均为示意。

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

`policy_mediated` 和 `external_verifier` 是本书的平台取值，不是厂商原生模式。接入时须逐项证明原生消息能映射到哪些字段；不能导出的审批或产物证据应标为缺失，并缩小自动执行范围。平台任务与会话的关系、业务验收规则统一见第十八章。

## 6. 设计判断

这一组产品让集成者可以选择自行运营循环，或采购会话与循环管理服务。作者的采用判断取决于已有应用、权限边界与运维能力：需要自定义生命周期时评估 SDK，需要托管恢复时评估 Managed Agents，并分别测量恢复缺口、权限决定可追踪性和费用。公开接口支持这些架构假设，还不足以证明某条路线普遍更便宜或更可靠。

# 第十三章 Claude Code：薄循环、厚运行时

> 资料截面与实际访问日期：2026-10-29。公开源码基线为 [Claude Agent SDK Python `0.2.174`](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/pyproject.toml#L7)、commit `27858cbba9ecee26a06a90b8d39d3b5596121d11`；网页快照哈希见本轮研究记录。SDK 源码可解释宿主接口，不能据此宣称审计了闭源 Claude Code 核心。本章是文档与源码研究，未运行产品端到端实验。

Claude Code 的架构重点，在于把模型选择下一步的循环放进一个持续管理上下文、工具执行和会话状态的 Harness。官方将工作概括为收集上下文、采取行动、验证结果；每次工具返回的新信息都可能改变下一步，而不必预先列出完整工作流。[运行原理](https://code.claude.com/docs/en/how-claude-code-works) “薄循环、厚运行时”是本书对这种职责分配的归纳，不是厂商公布的内部模块名。

## 1. 整体架构与职责边界：谁拥有循环

Claude Code CLI 面向交互开发；Agent SDK 把同一套工具、循环和上下文管理提供给 Python／TypeScript 应用，由应用运营进程。Client SDK 则直接调用 Claude API，工具循环由调用方或其 tool runner 驱动。Managed Agents 是另一个托管 Harness 接入面，不能把它的远程 session、sandbox 和管理接口当作本地 CLI 的内部结构。[接入面比较](https://code.claude.com/docs/en/agent-sdk/overview)

公开 Python SDK 给出了可核查的边界：`SubprocessCLITransport` 构造带 `--output-format stream-json` 的命令，以 stdin/stdout 管道启动 Claude Code binary，并传入工作目录和环境。另一侧的 `Query` 处理 `can_use_tool`、`hook_callback`、`mcp_message` 控制请求，把应用回调结果写回管道。这解释了“作为库使用”的含义：应用握有控制接口，循环仍由 Claude Code 运行时驱动。[进程传输源码](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/src/claude_agent_sdk/_internal/transport/subprocess_cli.py#L570)、[控制协议源码](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/src/claude_agent_sdk/_internal/query.py#L577)

下面是依据上述接口作出的作者抽象，表示职责和信息流，不表示闭源程序的类或线程布局。

```text
用户 / 业务应用
      | 任务、选项、后续输入
CLI 界面 / Agent SDK 宿主
      | 输入与控制请求             ^ 消息流、结果、会话 ID
Claude Code 运行时 <--------------> Claude 模型服务
      | 上下文组装、循环、工具许可       模型请求工具 / 生成回答
      +--> 内置 Read / Edit / Bash --> 工作区与命令结果
      +--> MCP 分派 --> 外部服务器 / SDK 进程内 handler
      +--> Agent --> 子代理上下文 --> 最终报告
      +--> 本地会话 JSONL；可选 SessionStore 镜像
宿主 hooks / 权限回调 <-----------> 运行时控制协议
```

对应第五章，模型负责提出动作，Harness 负责使动作成为受控调用，环境承受读写，反馈返回下一轮。选用 SDK 可以复用这一运行机制；应用仍须决定工作区归属、运行身份、任务验收和外部系统的事务边界。这是架构取舍，而不是把业务应用缩减成一个提示词入口。

## 2. Agent loop 与恢复：消息流不是业务事务

一次 SDK 调用先接收提示词、系统指令、工具定义和历史，通常产生 `system/init` 元数据；模型输出 `assistant` 消息中的 `tool_use`，运行时执行工具，再以 `user` 消息中的工具结果供下一次推理使用。循环持续到模型不再请求工具，随后产生 `ResultMessage`。因此宿主消费消息流时，不必为每个 `Read` 或 `Bash` 自行实现“调用模型—执行工具—再调用模型”。[循环与消息生命周期](https://code.claude.com/docs/en/agent-sdk/agent-loop)

工具拒绝会作为观察返回模型，使其换路或解释受阻；结束也可能来自 `maxTurns`、`maxBudgetUsd` 或执行错误。宿主应读取 `success`、`error_max_turns` 等 result subtype，而不能只看有没有最后一段文字。预算在模型响应到达后核算，故触及上限的那次响应仍可能使估算费用越过阈值；这是一道运行预算门，不是逐 token 的硬额度锁。[工具拒绝、预算与结果](https://code.claude.com/docs/en/agent-sdk/agent-loop)

TypeScript 流式接口还提供 `interrupt()` 请求中断查询；已经排队的用户消息可能在中断后继续执行，因此宿主需要分别管理当前执行与待处理输入，而不能把一次中断当成整个会话的取消。[中断及队列语义](https://code.claude.com/docs/en/agent-sdk/typescript#sdkcontrolinterruptresponse)

持久化首先保存对话。CLI 将消息、工具调用和结果写入本地 JSONL；SDK 的 `resume` 延续会话，fork 建立另一条会话历史。文件检查点是另一套机制：启用后备份 `Write`、`Edit`、`NotebookEdit` 所修改的文件，`rewindFiles()` 回退文件却不回退对话；不能把 Bash 修改、外部 API 写入或所有子代理编辑视为同样受到保护。[会话](https://code.claude.com/docs/en/agent-sdk/sessions)、[文件检查点](https://code.claude.com/docs/en/agent-sdk/file-checkpointing)

跨主机恢复可以接入 `SessionStore` 的 `append/load`。其数据路径是“子进程先写本地，SDK 再镜像到自有存储”，镜像失败可发出 `mirror_error` 并继续运行；文件检查点不能与该存储选项同时启用。[外部会话存储](https://code.claude.com/docs/en/agent-sdk/session-storage) 对应第六章，这些机制分别恢复“先前讨论了什么”和“部分文件曾是什么样”，并未建立第三方写入的恰好一次语义。若工单已经创建而响应丢失，应用仍应凭业务操作标识回读，而不是因会话可以恢复就重新提交。

## 3. 上下文与会话：压缩、缓存、记忆各做什么

运行时每轮组装的是模型当次可见的信息。历史消息、读入文件、命令输出和工具 schema 都消耗窗口；磁盘上的整个仓库并不会因为可访问就全部进入模型。`CLAUDE.md` 承载人写的持续说明，auto memory 保存 Claude 积累的经验，两者都作为上下文使用，不能代替执行权限。[上下文组成](https://code.claude.com/docs/en/agent-sdk/agent-loop#the-context-window)、[指令与记忆](https://code.claude.com/docs/en/memory)

SDK 与 CLI 的装配起点也有差别：SDK 不设置 `systemPrompt` 时使用最小提示，选择 `claude_code` preset 才采用 CLI 的系统提示；`CLAUDE.md` 则由 `settingSources` 控制，与是否采用 preset 分开。当前文档中的默认 `query()` 会读取文件配置，显式选择来源可以收窄用户与项目配置的影响，但 managed policy 和全局配置另有规则。[系统提示](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)、[配置加载](https://code.claude.com/docs/en/agent-sdk/claude-code-features) 这使应用能够分别决定“通用行为”和“项目知识”，也要求部署配置成为可复现的任务输入。

接近窗口上限时，自动 compaction 用摘要替代旧历史，并在 SDK 流中发出 `compact_boundary`；`PreCompact` 可以在压缩前处理归档，`/compact` 可主动触发。摘要保留关键决定，但早期细节可能丢失。[自动压缩](https://code.claude.com/docs/en/agent-sdk/agent-loop#automatic-compaction) 依照第七章，压缩是在有限窗口内选择继续工作所需的状态；原始会话日志与当前上下文因此不应被当作同一份资料。

Prompt cache 解决的是重复计算。Claude Code 将稳定内容放在请求前部、把新交互追加在后，模型服务复用精确匹配的前缀；它不是按文件独立缓存，也不替模型保存跨请求记忆。压缩会另发总结请求，并使后续请求的对话层前缀改变；系统和项目层能否继续命中，取决于内容是否保持一致。[Claude Code 缓存](https://code.claude.com/docs/en/prompt-caching)、[API 前缀语义](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) 因而一次主动压缩可以换来较短的后续上下文，同时付出总结与重建缓存的成本；不能把“token 变少”直接等同于“本轮更便宜”。

## 4. 工具、MCP 与扩展：从可发现能力到执行结果

内置 `Read/Edit/Write` 处理文件，`Glob/Grep` 提供检索，`Bash` 执行命令。模型选择工具和参数，运行时处理执行与回传；多个工具也不是一律并行，公开契约允许只读工具并发，而修改状态的工具按序执行。自定义工具默认按序，`readOnlyHint` 才表达可并发的只读意图。[工具执行](https://code.claude.com/docs/en/agent-sdk/agent-loop#tool-execution) 这让模型看到的能力接口与实际调度相分离，对应第八章的 ACI：工具不仅要能被选择，还要有稳定的结果和错误形式。

MCP 的路径从服务器注册开始：`mcpServers` 可以描述本地 stdio 进程、远程 HTTP/SSE 服务或 SDK server；工具使用 `mcp__<server>__<tool>` 名称。发现工具不意味着立即把全部 schema 填满上下文，当前 tool search 默认延迟加载定义，模型需要时再找出相应能力。[MCP 注册、命名与发现](https://code.claude.com/docs/en/agent-sdk/mcp) 这样减少的是无关工具描述的常驻成本，真正调用时仍须获得定义、完成许可和收集返回值。

SDK 自定义工具把名称、描述、输入 schema 与 handler 组合，经 `createSdkMcpServer`／`create_sdk_mcp_server` 注册。handler 在应用进程中运行，返回 `content`，还可返回结构化结果或 `isError`；公开 Python 分派器将运行时送来的 `mcp_message` 路由到相应 server，再把响应写回。[自定义工具](https://code.claude.com/docs/en/agent-sdk/custom-tools)、[MCP 控制分派](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/src/claude_agent_sdk/_internal/query.py#L656) 这里的“进程内”指应用 handler 所在位置，不表示模型服务直接执行 Python 函数。

扩展还会改变循环的不同位置。Skill 的描述先被发现，正文按需进入上下文；hooks 则按事件和 matcher 运行代码，例如 `PreToolUse` 在动作前检查参数，`PostToolUse` 记录结果，`PreCompact` 处理摘要前状态。SDK 回调在宿主执行，配置中的 command hook 运行命令，不能把 hook 当成要求模型自觉遵守的一段说明。[按需上下文](https://code.claude.com/docs/en/how-claude-code-works#manage-context-with-skills-and-subagents)、[hooks 分派](https://code.claude.com/docs/en/agent-sdk/hooks) 作者据此把扩展分成“补知识”和“改变控制路径”两类，以便判断它究竟增加上下文，还是引入新的执行主体。

Plugin 将 skills、agents、hooks 和 MCP servers 打包，SDK 可按本地路径加载。[扩展包装](https://code.claude.com/docs/en/agent-sdk/overview) 因此审查一个插件时，应沿这些组件各自的路径判断它改变了什么；安装一个包并不会使其中的知识文件与可执行 hook 获得相同的信任等级。

## 5. 权限、沙箱与凭证：批准动作与限制能力

工具请求先要回答“是否获准执行”。SDK 文档的基本求值顺序是 hooks、deny 规则、ask 规则、permission mode、allow 规则，最后才是 `canUseTool`；各模式和扩展另有例外。`PreToolUse` 可以直接拒绝，但它返回 allow 也不能跳过后续 deny/ask。应用回调接收工具名和输入，返回允许、修改后的输入或拒绝理由。[权限求值](https://code.claude.com/docs/en/agent-sdk/permissions)、[回调协议源码](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/src/claude_agent_sdk/_internal/query.py#L586)

这条顺序解释了两个不同接口的用途：`allowedTools` 是预批准集合，不是“除此之外工具不存在”的白名单；已被规则或模式批准的调用通常不进入 `canUseTool`。若应用要在每次工具调用前核验业务范围，应使用相应 `PreToolUse` hook；若要在模型面前收窄能力，应配置工具集合或移除工具。[规则与回调边界](https://code.claude.com/docs/en/agent-sdk/permissions#allow-and-deny-rules) 作者的设计判断是把常见安全读操作做成确定规则，把需要业务裁决的动作留给回调，避免审批 UI 承担所有运行时策略。

获准之后还要回答“进程能触及什么”。内置 Bash sandbox 通过操作系统限制 shell 命令及其子进程的文件与网络访问：macOS 使用 Seatbelt，Linux／WSL2 使用 bubblewrap，网络通过代理检查目标主机。但 `Read/Edit/Write`、本地 MCP 服务器与 command hooks 不在这层 shell 沙箱内；前者使用工具权限，后者运行于宿主环境。[沙箱覆盖范围](https://code.claude.com/docs/en/sandboxing) 对应第九章，权限控制调用入口，隔离约束实际执行，两者要共同覆盖应用选用的路径。

凭证也必须按所在位置理解。MCP 配置可把凭证放入 server 环境或 HTTP headers；Bash sandbox 的 `credentials` 可显式禁止读取文件、移除环境变量，也可配置占位符与代理注入，但没有默认覆盖所有秘密的内置 deny 清单。[MCP 认证](https://code.claude.com/docs/en/agent-sdk/mcp#authentication)、[凭证保护](https://code.claude.com/docs/en/sandboxing#protect-credentials) 若要求整个 SDK 应用、hooks 和工具都处于同一隔离边界，官方部署指南提供容器／虚拟机与外置凭证代理的组合思路。[安全部署](https://code.claude.com/docs/en/agent-sdk/secure-deployment) 这些部署责任不能从 Managed Agents 的凭证库设计推导为本地默认能力。

## 6. 子智能体与委派：隔离的是哪一份状态

通过 `agents` 定义 `AgentDefinition`，应用为角色配置 description、prompt、tools 等；主模型通过 `Agent` 工具委派。普通子代理从自己的系统提示、委派 prompt、工具定义和项目说明启动，不携带父对话历史。因此父代理必须把任务所需的文件位置、错误信息和已作决定写入委派输入。[定义与继承](https://code.claude.com/docs/en/agent-sdk/subagents#what-subagents-inherit) 对应第十一章，这个输入就是一份最小工作契约，不能只写“继续刚才的工作”。

fork 是另一种起点：它复制当前对话再分支；官方文档注明 Claude Code `v2.1.302` 起可以由 `Agent` 的 `subagent_type: "fork"` 发起。普通子代理适合过滤无关历史，fork 适合需要已有推导的分支，两者之后的工具过程都可与父上下文分开。[fork 子代理](https://code.claude.com/docs/en/agent-sdk/subagents#forked-subagents)、[上下文管理](https://code.claude.com/docs/en/how-claude-code-works#manage-context-with-skills-and-subagents) 这种上下文隔离本身没有承诺独立操作系统身份、独占工作区或新的凭证边界；作者建议把需要并发写入的文件归属明确放进委派契约。

回收结果时，父代理收到的是子代理最终报告，可能再总结后交给用户；完整子轨迹保存在独立文件，SDK 事件可以用 `parent_tool_use_id` 关联委派。后台工作通过稍后的完成通知进入主会话，权限提示也在主会话处理。[报告与轨迹](https://code.claude.com/docs/en/agent-sdk/subagents)、[后台执行](https://code.claude.com/docs/en/sub-agents#tools-permissions-and-results-of-background-subagents) 因而“工具日志不占父窗口”与“宿主拿不到工具日志”是两回事；报告压缩了模型交接内容，观测链仍可保留细节。

当前接口允许子代理继续委派，并提供深度、并发与费用限制；TypeScript `stopTask(taskId)` 可停止后台任务。[委派上限](https://code.claude.com/docs/en/agent-sdk/subagents#cap-subagent-depth-concurrency-and-spend)、[任务控制](https://code.claude.com/docs/en/agent-sdk/typescript#query-object) 取消传播则须按具体接口验证：本章固定的 Python 源码在权限和 hook 回调中仍传入 `signal=None`，不能假定所有语言接口都有完整的取消信号链，更不能把停止任务解释成撤回已完成的外部写入。[回调信号源码](https://github.com/anthropics/claude-agent-sdk-python/blob/27858cbba9ecee26a06a90b8d39d3b5596121d11/src/claude_agent_sdk/_internal/query.py#L593)

## 7. 验证与可观测性：从循环结束到可验收产物

Claude 可以在循环中运行测试，把错误输出变成下一轮修改依据；`Stop` hook 也能阻止结束，让代理继续工作。[验证循环](https://code.claude.com/docs/en/how-claude-code-works#the-agentic-loop)、[Stop 事件](https://code.claude.com/docs/en/hooks#stop) 但第十章要求区分“运行时正常结束”与“业务验收通过”。本书建议在任务入口就定义验收命令与产物，再由独立验证步骤检查补丁和测试记录。hook 是插入检查的机会，不会凭空知道业务正确性，也不能让已经发生的外部副作用消失。

运行中，宿主可以记录 assistant/tool/result 消息、压缩边界、子代理关联和权限决定；Claude Code 还可通过 OpenTelemetry 导出指标、事件及可选 traces，工具参数和内容的导出受配置控制。[消息流](https://code.claude.com/docs/en/agent-sdk/agent-loop#message-types)、[可观测性](https://code.claude.com/docs/en/monitoring-usage) 对应第十二章，作者建议用任务 ID 连接 session、工具调用和最终产物，把“模型为什么继续工作”与“平台为什么接受结果”分别保存，避免只留下自然语言总结。

核算同样需要辨别统计边界：同一次模型响应可能拆成多条消息，使用量应按 message ID 去重；result 的 `usage` 只覆盖主循环，全树统计使用 `modelUsage`／`model_usage`。`total_cost_usd` 是客户端价格表计算的估算，不是权威账单。[费用统计](https://code.claude.com/docs/en/agent-sdk/cost-tracking)、[结果字段](https://code.claude.com/docs/en/agent-sdk/agent-loop#handle-the-result) 这样才能比较“主窗口更短”是否真的抵消了额外子代理请求，而不把上下文整理效果误报为总成本收益。

## 8. 一次任务穿过架构：修复登录回归

下面是作者设计的接入示例，不是实测记录。任务是“修复过期会话导致的登录失败，交付补丁和回归测试，不部署”。应用先建立隔离工作区，固定 SDK 与 binary 版本，选择编码用 system preset、项目配置来源和运行预算，并把验收目标作为任务输入。对应的提示、配置来源和预算均有独立接口，应该在一次任务的运行记录中共同保存。[提示装配](https://code.claude.com/docs/en/agent-sdk/modifying-system-prompts)、[循环控制](https://code.claude.com/docs/en/agent-sdk/agent-loop#control-how-the-loop-runs)

模型先请求读取失败测试与认证代码。运行时完成许可、执行读取、回传内容；若委派只读审查，父代理给出具体路径和失败信息，子代理只交回发现及证据位置。主代理再决定修改并运行测试。若需要读取缺陷工单，MCP 将工单服务的工具定义带入调用路径；本例只开放读取业务记录的工具，不把写工单权限附带授予。[工具循环](https://code.claude.com/docs/en/agent-sdk/agent-loop#tool-execution)、[子代理输入](https://code.claude.com/docs/en/agent-sdk/subagents#what-subagents-inherit)、[MCP 权限](https://code.claude.com/docs/en/agent-sdk/mcp#allow-mcp-tools)

长时间排查后，自动压缩让主窗口保留当前假设和关键决定；缓存复用尚未改变的前缀。测试再次失败就把输出送回循环，而不是把失败本身直接认定为整个任务结束。[压缩与反馈](https://code.claude.com/docs/en/agent-sdk/agent-loop)、[缓存重建](https://code.claude.com/docs/en/prompt-caching#compacting-the-conversation) 本例的工程要求是让测试结果指向具体工作区版本，并把失败日志留在产物存储，摘要只承担定位作用。

若宿主中断，应用先确认日志与工作区仍可用，再选择 resume；如果用了外部 SessionStore，还要检查是否发生镜像失败。测试通过后，平台重新验证补丁、汇总授权与工具记录，再把任务标记为可交付。[恢复边界](https://code.claude.com/docs/en/agent-sdk/session-storage) 最终取舍是：SDK 复用了成熟的代理循环，却仍由应用运营进程、持久存储和验证门；需要购买托管循环时另行评估 Managed Agents，而不是在本地适配器里混入其 `wake/getSession` 架构假设。[托管边界](https://code.claude.com/docs/en/agent-sdk/overview)、[Managed Agents 架构](https://www.anthropic.com/research/managed-agents)

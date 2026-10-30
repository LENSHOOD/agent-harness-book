# 第十八章 pi-mono：小核心怎样长成可组合的运行时

> 资料截面：2026-10-29。本章沿用读者熟悉的 pi-mono 名称；原仓库已迁至 `earendil-works/pi`。以下以稳定版 **v1.4.0、commit `4a080252f06caf63a525d7873c5d94d3c23887e0`** 为准，不把早期版本的取舍当成永久特性。[发布记录](https://github.com/earendil-works/pi/releases/tag/v1.4.0)

Pi 值得研究的地方，是它把“循环本身”“编码会话”和“工作方式”分成了可以分别使用和替换的部分。只需要一个调用模型与工具的循环，可以使用 Agent Core；需要会话、上下文压缩和扩展发现，可以使用 Coding Agent SDK；需要终端交互，再使用 CLI。下面按第二篇的同一组问题，追踪这些部分怎样一起完成任务。[包划分](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/README.md)、[SDK](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)

## 1. 整体架构：循环、会话和界面分别负责什么

对应第五章，先区分四个主要组件。`pi-ai` 统一不同模型供应商的消息、工具调用和流式响应；`pi-agent-core` 的 `Agent` 管理一次运行的状态和循环；`pi-coding-agent` 的 `AgentSession` 在循环外管理编码任务所需的会话、压缩、资源和扩展；`pi-tui` 提供终端呈现。它们是包和职责的划分，并不意味着每层都运行在独立进程。[仓库说明](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/README.md)、[会话工厂源码](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/src/core/sdk.ts)

下面是依据这些接口整理的架构图。图中连线表示调用或数据依赖，不代表安全隔离：

```text
终端 CLI / JSONL RPC 客户端 / 嵌入 SDK 的应用
                       |
                 AgentSession
          +------------+-------------+
          |            |             |
    SessionManager  ResourceLoader  扩展运行环境
    会话树与当前分支  指令/skills等   工具与生命周期处理器
          |            |             |
          +------ 当前请求上下文 ------+
                       |
                Agent / agent loop
                 /             \
          pi-ai 模型适配      工具执行接口
               |             /       \
           模型服务      本机文件/进程   MCP 服务等
```

`createAgentSession()` 负责把这些对象装配起来。`SessionManager` 持有持久化或内存中的会话记录；`DefaultResourceLoader` 找到指令、skills、模板和扩展；`AgentSession` 再协调当前模型、可用工具和运行状态。宿主可以替换这些依赖，因而“沿用 Pi 的循环”不必等于“照搬 Pi 的终端产品”。[SDK 的可替换边界](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)

这里的小核心是一种职责选择。完整企业系统仍需要身份、隔离、任务验收和运营设施；只引用 `pi-agent-core` 不会自动获得 Coding Agent 的全部会话能力，更不会获得持久业务工作流。仓库中的其他包也不能仅凭名称就视为这条 CLI 调用链的必经组件。

## 2. Agent loop：工具反馈和用户追加输入怎样推进循环

对应第六章，Pi 的低层循环有两层推进条件：内层处理模型响应、工具调用和 steering 输入，外层在一次工作原本可以结束时检查 follow-up。steering 用来调整正在进行的工作，follow-up 用来排在当前工作之后；两者不只是界面上不同颜色的消息，而是不同的调度时机。[循环源码](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/agent/src/agent-loop.ts)、[SDK 输入语义](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)

一次正常工具轮次可以这样阅读：循环先整理当前消息和工具声明，调用模型，接收完整 assistant 消息，再校验并执行其中的工具调用；工具结果成为 `toolResult` 消息，进入下一次模型请求。下一轮开始前，上层还可以更新上下文和模型配置。源码同时有并行与顺序工具执行路径，不能把早期版本的执行顺序当成所有版本的固定行为。[请求、调度与工具分派](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/agent/src/agent-loop.ts)

停止条件比“模型没有调用工具”更细。排队输入或上层继续决定可能产生下一轮；相反，整批工具都明确给出终止提示时，可以跳过自动追问。若模型响应因输出长度截断，哪怕拼出的工具参数看起来是合法 JSON，也不执行这些调用，而是反馈错误；错误或中止响应则结束本次低层运行。这些分支让不完整输出不会直接变成动作。[同一固定版本的停止与截断分支](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/agent/src/agent-loop.ts)

恢复由上层会话补充。`agent_end` 只说明一次低层运行结束，其后仍可能发生自动重试、压缩恢复或队列工作；外部应用要判断 Pi 是否还会自动继续，应观察 `agent_settled`。但即使会话已经静止，也不能推导先前的文件修改或远端写入已撤销。这里分别对应第六章的运行终态和副作用对账，不能用一个结束事件代替两者。[RPC 生命周期](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/rpc.md)

## 3. 上下文与会话：完整记录和当前请求不是同一个对象

对应第七章，Pi 用两个转换边界隔开内部消息和模型输入。`transformContext` 可以修剪或补充本次要看的内容；`convertToLlm` 再把内部消息转换为模型能接受的格式，例如滤掉只供界面使用的消息。这允许会话保留更多信息，同时控制本次请求实际发送什么。转换函数是否保留原数据还取决于实现，不能把可插拔接口当成自动保证。[模型调用边界源码](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/agent/src/agent-loop.ts)

会话的权威记录由 `SessionManager` 管理。除首行会话头外，JSONL 会话条目通过 `id` 和 `parentId` 组成树，当前叶节点确定活动分支。会话头保存会话级元数据，其 `id` 不是条目树的节点 ID。回到旧分支不需要删除其他分支；生成模型上下文时，管理器选择当前路径并应用压缩记录。系统指令和工具声明的变化也以消息保存，恢复时可以重建当时的有效配置。直接替换内存中的消息数组，并不等于替换持久会话。[会话格式](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/session-format.md)、[SessionManager 的权威性](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)

压缩会选取较早的上下文生成摘要，追加带 `summary` 和 `firstKeptEntryId` 的记录，再用摘要及保留的近期消息构造下一次请求。原始记录仍然存在。这解决“上下文窗口装不下”的问题；切换分支时的 branch summary 则解决“新分支需要知道另一条路径上做过什么”的问题。两者都使用摘要，但触发原因不同，也都不保证摘要保留了所有细节。[压缩与分支摘要](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/compaction.md)

skills 采用按需读取：先提供名称和说明，需要时再读取 `SKILL.md`，避免把所有工作指南一次塞进请求。文档也明确承认模型可能漏读相关 skill，必要时应显式指定。因此，skills 是组织经验的载体，加载机制本身不是自动学习或正确选择的证明。[Skills](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/skills.md)

## 4. 工具、MCP 与扩展：小接口怎样容纳大工具集

对应第八章，CLI 默认启用 `read`、`bash`、`edit`、`write`。模型看见工具声明后生成调用，循环对参数做校验，再把执行结果送回模型。扩展可以注册工具，也可以在调用前后处理事件。嵌套调用通过 `ctx.executeTool()` 复用工具校验和事件处理，事件带 `parentToolCallId`；嵌套结果先返回给调用它的工具，并不会全部自动塞入模型转录。这使复合工具有机会筛选结果，而不只是把更多输出搬进上下文。[CLI 工具](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/cli.md)、[扩展与嵌套工具](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/extensions.md)

**在本章版本中，Pi 已经有内建 MCP 支持。** 它连接 stdio 或 Streamable HTTP 服务，把服务工具注册到本地工具体系。工具可以直接声明给模型，也可以先隐藏详细定义，等 `tool_search` 找到后再声明，或由 `codemode` 脚本发现、组合调用。完全隐藏的工具则不可达。这几种模式对应第八章的选择：让常用工具容易调用，让大工具集不必全部占据每次请求。[MCP 连接与工具暴露](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/mcp.md)

这里还要分清产品装配与库默认值。CLI 把 MCP、`codemode` 和 `tool_search` 作为内建扩展加载；使用 SDK 创建会话时，需要宿主显式加入相应扩展工厂并绑定扩展生命周期。只写一句“Pi 支持 MCP”，不足以指导企业嵌入，旧文章中一句“Pi 没有 MCP”也已经不能描述这个版本。[SDK 的 MCP 装配要求](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)

工具暴露方式不等于授权。一个 MCP 工具即使未直接声明，也可能通过间接机制调用；工具的只读、幂等或破坏性 annotations 也只是服务方提供的提示。平台要限制实际访问范围，应检查最终执行路径和凭证，而不是只检查模型最初看见的工具列表。[MCP 暴露语义](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/mcp.md)、[工具 annotations](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/extensions.md)

## 5. 权限、沙箱与凭证：项目可信不等于操作受限

对应第九章，Pi 默认以启动它的操作系统用户权限运行，没有内建的逐工具审批体系或覆盖文件、进程、网络、凭证的强制权限系统。`cwd` 是工作位置，不是路径边界；模型、扩展和子进程能影响什么，要看外部赋予它们的权限。[安全说明](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/security.md)

Project trust 解决的是另一个问题：是否允许项目提供的扩展、MCP 配置等资源在启动时被加载。它不能限制启动后的工具访问；拒绝项目可信也不意味着目录内容不再影响模型，例如上下文指令文件仍可能被读取。这是一道资源加载决定，不能替代命令级授权或执行隔离。[Project trust 的具体边界](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/security.md)

官方区分两种隔离方式：把整个 Pi 进程放进受限环境，或者只把部分工具执行转到隔离环境。后一种做法留下主进程及其他扩展在外部运行，保护范围更窄。企业采用时应据此画出实际进程和凭证分布，再决定文件挂载、出网与身份限制；不能因为一个 bash 工具进了容器，就说所有扩展都被隔离。[运行方式与保护范围](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/security.md)

MCP 的认证还有自己的生命周期，例如 HTTP OAuth 令牌按服务身份保存与刷新。它让 Pi 能代表用户访问服务，并没有替企业定义业务授权规则。结合本机模型凭证、MCP 凭证和扩展代码，接入方需要明确哪些秘密存在主进程，哪些只留在外部代理中。[MCP OAuth](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/mcp.md)

## 6. 子智能体与委派：扩展示例如何复用同一个核心

对应第十一章，Pi 默认核心没有把一套多智能体组织方式固定下来。官方仓库提供的 subagent 是可安装扩展示例：父会话调用一个工具，扩展再启动独立 `pi` 子进程，交给它专门的提示、工具和模型配置。每个子进程有自己的上下文窗口；这和直接在同一个会话里加一段“现在扮演审阅者”的指令不同。[项目取舍](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/README.md)、[Subagent 示例](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/examples/extensions/subagent/README.md)

示例支持单任务、并行任务和链式任务。链式模式按顺序运行任务，并用后一步任务模板中的 `{previous}` 显式注入前一步最终文本；它不自动继承完整历史。并行模式分别收集执行进度、用量和最终文本，再作为父工具结果返回。取消也通过扩展传递给子进程。由此可以看到，委派并不神秘：它复用现有运行时，额外实现任务输入、调度、结果收集和取消传播。[示例的模式与输出约定](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/examples/extensions/subagent/README.md)

独立上下文和独立进程都不自动产生独立权限。如果子进程仍共享同一账户、目录和凭证，它仍可能影响相同资源；父工具收到了失败信息，也不意味着子进程已经做过的修改被撤销。官方示例足以解释组合方式，企业任务系统还要补上工作区隔离、总预算、产物身份以及外部写入核对。这些是本书的接入建议，不能倒写成示例已经提供的保证。

## 7. 验证与可观测性：事件帮助看见过程，不能替任务验收

对应第十和第十二章，低层 Agent 发出运行、轮次、消息和工具事件，上层会话补充压缩、重试与最终静止事件。SDK 可以直接订阅；RPC 则在标准输出中提供 JSONL 响应和事件，诊断走标准错误。命令响应按请求 ID 关联，异步会话事件反映运行进展，因此“prompt 请求成功”与“任务完成”是两个不同事实。[SDK 事件](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md)、[RPC 记录与生命周期](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/rpc.md)

一个修复任务仍要回答：测试是否覆盖原始故障，测试是否针对最终工作区运行，最终交付的修改是否就是被测试的修改。Pi 的事件和会话记录提供核对材料，业务验收规则需要宿主另行规定。只看到一条“测试通过”的模型回复，不足以得出这些结论。

本书对 **真实的 Pi 1.4.0 Agent Core** 做了九项本地检查：工具结果回传、请求上下文过滤、非法参数拒绝、截断调用拒绝、工具异常反馈、follow-up 调度、混合终止结果、整批终止结果和模型中止路径，全部通过。模型端使用确定性响应替身，工具只做内存运算；测试没有调用收费模型、远端 MCP 或真实子智能体，也没有证明沙箱强度、摘要质量或完整 SDK 恢复正确。复现入口位于仓库 `examples/pi-core/`，它验证的是循环机制，不是产品整体效果。

## 8. 一次修复任务如何穿过这些组件

设想用户要求修复一个日期换算错误。以下是依据上述接口组织的教学流程，并非另一份已执行的模型轨迹：宿主先选择工作区与受限执行环境，创建 `AgentSession`，由资源加载器提供项目指令；模型通过 `read` 找到相关代码，再调用工具修改和测试；工具结果进入下一轮请求，模型据此继续修复或解释结果。

如果用户此时追加“先不要修改接口”，steering 在规定的轮次边界进入上下文；如果说“完成后再解释兼容性”，follow-up 等当前工作可结束时再启动下一轮。若调查时间很长，`SessionManager` 保留完整会话树，压缩机制减少下次请求携带的旧内容。若安装了审阅者扩展，父任务还能委派一个独立会话，但平台仍须决定它看到哪个产物、能否修改工作区以及谁接受最终结果。

整个路径说明了 Pi 的设计取舍：把频繁复用的循环、消息、会话和扩展接口做清楚，把具体团队如何工作留给外层组合。它适合需要研究和控制这些接缝的团队；相应代价是平台必须自己承担没有内建的治理责任。接入深度应与团队愿意长期维护的责任匹配，而不是只按代码行数或功能清单判断是否“简单”。

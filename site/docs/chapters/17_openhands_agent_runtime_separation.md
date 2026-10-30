# 第十七章 OpenHands：Agent 与执行 Runtime 分离

> 本章访问日期：2026-10-29。分析基线为 Software Agent SDK `1.49.2`、commit `d128a786ee2ee570eb23ff5862ec148b43cfad0b`；应用层另固定 Agent Canvas `1.20.0`、commit `9737f713616a1e452f822c2967f0e2c8bf2dc308`。这不是访问日最新版声明，也不表示两者依赖版本相同：后者的 TypeScript client 依赖实际为 `1.49.1`。本章静态阅读源码，未部署容器或运行模型任务。[SDK 职责](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/README.md)、[Canvas 固定依赖](https://github.com/OpenHands/OpenHands/blob/9737f713616a1e452f822c2967f0e2c8bf2dc308/package.json)

## 1. 整体架构与职责边界：配置、会话与执行位置分别建模

理解 OpenHands，应先区分四个对象。`Agent` 描述模型、工具和上下文处理能力；`Conversation` 拥有一次会话的消息、执行状态与运行入口；`Workspace` 描述工作发生的位置；Agent Server 将会话能力暴露为 REST/WebSocket 服务。Canvas 消费 SDK 的 TypeScript client 提供产品界面，调度和 webhook 等自动化生命周期另由 automation 仓库负责，不能把它们都归入一个“Agent 大脑”。[仓库责任](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/README.md#repository-boundaries)、[会话工厂](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py)

`Conversation(..., workspace=...)` 根据 workspace 类型创建 `LocalConversation` 或 `RemoteConversation`。本地路径在当前执行环境驱动 Agent；远程路径由客户端发送会话请求，Agent 在远端 Server 上运行。因此，远程会话并非必然是“模型循环留在笔记本，只把 shell 送进容器”。调用者控制会话的接口与循环实际驻留的位置必须分别定位。[工厂选择](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py)、[远程客户端](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/remote_conversation.py)

下图为作者对固定版的归纳。LocalConversation 是控制循环的具体承载者；Docker mode 再把每个会话的服务放入独立容器，控制面负责供给与转发，容器内仍运行本地会话逻辑。这种嵌套使会话协议能够跨部署位置复用。[Docker 会话路由](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/routers.py)、[容器供给](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/registry.py)

```text
Canvas / Python client / automation caller
               |
        Conversation API
          /           \
 LocalConversation   RemoteConversation -- HTTP / WebSocket
          |                                 |
          |                       Agent Server control plane
          |                                 |
          |                   local mode / per-conversation container
          |                                 |
          +---------------------- LocalConversation
                                           |
                         ConversationState + EventLog
                                  |        ^
                              Agent.step   |
                                  |        |
                           LLM -> Action -> ToolExecutor
                                           |
                                      Observation
                         工具在所属 workspace 环境中执行
```

历史 `0.62.0` 中的 `EventStream → Runtime → ActionExecutor` 属于另一套实现。旧 Runtime 通过 HTTP 交付动作并返回 observation，可用于理解决策与执行分离的历史思路，但不应拿旧类名替代上图的 SDK 会话对象。[历史 Runtime 契约](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/README.md)

## 2. Agent loop 与恢复：由 Conversation 驱动 Agent 的单步

调用者先 `send_message()`，再调用 `run()` 或异步 `arun()`。`LocalConversation` 初始化插件与 Agent，循环检查执行状态、卡住检测、预算和迭代上限，再调用 `Agent.step`。Agent 负责“一步如何决策”，Conversation 负责“何时再走一步”。完成状态还可交给 Stop hook 检查，反馈可能促使会话继续，因而循环终止不是单看模型输出了一段告别文字。[循环所有者](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)

一个普通 step 读取 `state.view`，经 condenser 准备模型消息，调用 LLM，并将响应区分为工具调用、文本等路径。工具调用解析并验证为 `ActionEvent`，执行器产生 observation，再封装为 `ObservationEvent`。下一步看到的是更新后的会话视图。若有等待确认的未配对动作，step 先执行这些动作，而不是重新请求模型生成一份相似命令，这使“批准既有动作”与“再规划一次”分开。[单步与动作转换](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/agent.py)

确认模式下，第一次 run 可以停在 `WAITING_FOR_CONFIRMATION`；再次 run 表示隐式确认并执行 pending actions，拒绝则应走 `reject_pending_actions`。因此，接入端的“继续”按钮具有实际授权含义，不能当成任意网络重试。上下文超限时，Agent 只有在配置的 condenser 支持请求式压缩时才进入相应恢复路径，否则显式报错，不保证所有失败都会自行修复。[确认与恢复](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)、[上下文错误处理](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/agent.py)

取消也有粒度。`pause()` 在 step 之间生效；`interrupt()` 可取消正在运行的异步 task，先设置 cancellation token，再触发异步取消；同步 run 路径回退为 pause。中断后，未得到 observation 的工具调用可补入合成错误，保持模型消息结构完整。这种“修复历史配对”没有撤销已经写入的文件、外部请求或已启动进程；第六章的不确定提交问题仍需具体执行器和外部系统处理。[暂停、中断与孤立动作](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)

## 3. 上下文与会话：原始事件、模型视图和长期记忆各有位置

`ConversationState` 保存 Agent、workspace、执行状态、秘密注册表及 EventLog；活动分支的 `View` 是可重建派生值。配置 `persistence_dir` 才有对应文件存储，未配置则使用内存存储；恢复时会核对 Agent 与已存工具配置。会话身份、执行配置和事件不能只靠一段对话文本替代，否则可能在恢复时连接到不同能力集合。[状态与恢复](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/state.py)

`AgentContext` 负责提示扩展：仓库指令、运行环境、会话附加规则和 skills 在这里汇集。项目 skills 与 `AGENTS.md` 由 LocalConversation 在知道 workspace 后延迟加载；`load_project_skills`、`load_memory` 等开关不能写成无条件默认开启。记忆功能读取用户及工作区的 `MEMORY.md` 索引，索引内容每个会话从磁盘重新解析，不作为整个会话状态反复序列化。这使第七章讨论的指令、历史与跨会话知识具有不同更新周期。[上下文及记忆归属](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/context/agent_context.py)

并非所有 Event 都送给模型。`View` 仅纳入 `LLMConvertibleEvent`，并按顺序应用 `Condensation`；暂停与内部状态记录保留在日志，却不进入模型输入。它还维护允许修改消息的位置，避免压缩切断工具请求与结果的结构关系。于是审计能够查看发生过什么，而模型可以只看适合下一次推理的内容。[视图投影](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/context/view/view.py)

`LLMSummarizingCondenser` 可使用独立 LLM 摘要，按事件数量、token 压力或显式压缩请求触发，保留指定开头及近期内容。摘要模型与决策模型不必相同，token 阈值还应尊重决策模型的输入限制。这是上下文预算策略，而非证明信息没有损失的记忆机制；接入者应将关键验收条件保存在可重新读取的文件或结构化任务定义中，后半句属于作者建议。[摘要器实现](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/context/condenser/llm_summarizing_condenser.py)

这也解释了为什么“恢复聊天”与“恢复执行”不能合并成一个按钮的表面含义。模型视图能够从记录重新计算，并不保证当前工作目录里的文件仍与记录一致；摘要保留了任务目标，也不证明测试产物仍然存在。作者建议在跨进程恢复的重要任务里同时核对事件、工作副本与产物，让模型读到的是可验证的当前事实，而不只是先前描述的状态。这是对状态分层的应用判断，不是 SDK 额外承诺的文件回滚功能。

## 4. 工具、MCP 与扩展：配置可以传输，执行器在运行处物化

`Tool(name, params)` 是工具配置，Agent 初始化时找到注册的工具类并调用创建逻辑，得到具体 `ToolDefinition` 与 executor。动作和观察分别有 schema，模型只看到工具声明，实际调用由执行器负责；TerminalTool、FileEditorTool 等因此能在同一循环中提供不同环境能力。远程传输配置与在 Server 中创建资源，是理解 SDK 可部署性的关键。[工具初始化](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/base.py)、[执行与观察](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/agent.py)

并行执行由 `ParallelToolExecutor` 管理，它使用每 Agent 的并发限制与资源锁，把触及相同声明资源的调用串行化。锁有效的前提是工具正确实现 `declared_resources()`；不同执行器实例又有各自的锁，不能推断两个子会话同时编辑同一文件会自动互斥。并发调度降低等待，资源声明则维护可预测性，二者共同决定工具作者承担的契约。[并发和资源锁](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/parallel_executor.py)

MCP 工具经 `MCPToolDefinition/MCPToolExecutor` 进入同一工具体系，再通过 MCPClient 发给服务器，返回普通 observation。连接丢失时，执行器可以在调用前尝试重连；已经关闭的客户端不会被偷偷复活。参数中的秘密引用由 conversation 的 SecretRegistry 展开，不读取任意宿主环境变量。这条适配链解决了调用形状，外部服务实际写入的幂等性仍不是工具 schema 能保证的。[MCP 执行器](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/mcp/tool.py)

插件是另一层组合单位，可打包 skills、hooks、MCP 配置、agent 定义和 commands；`ResolvedPluginSource` 记录实际取得的 commit，避免暂停后继续时漂移到分支新版本。这里的扩展把提示知识、事件处理与外部能力组织成可加载资源，不应简单等同于新增一个函数工具；来源固定也只是可复现条件，不是插件安全证明。[插件组成](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/plugin/plugin.py)、[固定插件来源](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/plugin/types.py)

## 5. 权限、沙箱与凭证：批准动作与隔离执行分别配置

`AlwaysConfirm`、`NeverConfirm`、`ConfirmRisky` 决定一个动作是否需要确认；后者可以按风险阈值处理未知风险。与 dsh 的 `never` 不同，OpenHands 的 `NeverConfirm` 意味着不要求确认，并不禁止执行。风险分析与确认策略共同影响是否停下来等待用户，但它们不会自行建立文件系统或网络隔离。[确认策略](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/security/confirmation_policy.py)

执行隔离要看部署。Agent Server 本身是服务接口，普通 local mode 不因“Server”这个名字就得到容器；每会话 Docker mode 则由控制面创建容器，挂入该会话的记录、持久目录和 workspace，设置运行 UID/GID、去掉 capabilities，并启用 no-new-privileges；内存、CPU、PID 限额另有配置。这些是固定代码可检查的措施，不能省略镜像、挂载、网络与宿主 Docker 权限检查而宣称多租户隔离已验证。[Docker 启动参数](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/registry.py)

容器身份也属于恢复状态。`RuntimeProvisioningStore` 保存 conversation ID、API key、加密 key 与 workspace 路径，要求控制面配置 `OH_SECRET_KEY`，拒绝会话身份不匹配或重绑工作区。重连的目标应由持久身份重建，而不是临时发现一个同名目录后继续。Server 的会话 API key 认证是可配置的，部署者仍要明确服务暴露范围。[身份供给](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py)、[服务认证](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/README.md)

业务凭证由 SecretRegistry 管理，在执行时解析并对已知值做输出遮罩，流式遮罩还考虑秘密被拆到相邻 chunk 的情况。profile 的 `secret_refs` 则定义哪些保存的秘密可暴露：`null` 为全部，空列表为没有，非空列表为按名过滤。作者据此建议先限定注入范围，再考虑日志脱敏；遮罩已知字符串不能证明生成代码无法通过编码或网络泄露秘密。[秘密注册表](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/secret_registry.py)、[profile 范围](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/profiles/agent_profile.py)

## 6. 子智能体与委派：一项 task 对应一个子 Conversation

固定版的 `TaskToolSet` 提供阻塞式 `task` 工具。模型提交任务提示、`subagent_type` 和可选 resume ID，TaskExecutor 转交 TaskManager，最终返回含 task ID、状态与内容的 TaskObservation。子 Agent 类型由注册的 factory 决定，既可以是专门探索代码的配置，也可以是调用者自定义工具与指令的配置；工具定义中的旧 `max_turns` 字段已经弃用并被忽略。[Task 工具契约](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/definition.py)

TaskManager 创建新的 LocalConversation，共享父 workspace 路径，复制父 LLM 配置但重置独立计量，将子任务提示作为新消息发送，并按 agent 定义或父会话确定预算与迭代限制。这里没有复制父完整历史的步骤，也没有为每个 task 自动创建容器或操作系统身份。子任务结束后释放活对象，保留与 task 对应的会话记录；只有 FINISHED 算完成，卡住、暂停或限额终止返回错误和可用的部分结果。[创建与回收](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/manager.py)

这条实现有两个容易误读的边界。其一，resume 用进程内 task 映射找到落盘 conversation，不能据此保证进程重启后 task 索引自动恢复；父会话不持久化时，临时任务目录在 manager 关闭时会清理。其二，子策略可由定义覆写，否则继承父确认策略，但没有配置 `confirmation_handler` 时，manager 会继续执行等待确认的子动作，不能仅凭“继承”声称有人审。[恢复及确认处理](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/manager.py)

取消责任也必须沿具体实现追踪：此 TaskManager 走同步子会话 run，已检查的 start/run 路径没有把父 cancellation token 下传。因此不能将父异步 interrupt 的保证扩大为全部子进程或子会话同时停止。第十一章的委派契约在这里应包含任务范围、共享工作区冲突、确认处理器以及显式的子任务停机验证，后者是作者提出的接入要求。[同步任务路径](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/manager.py)

## 7. 验证与可观测性：存储顺序不等于业务恰好一次

LocalConversation 将默认持久化回调放在调用者回调之前：事件追加失败，后续订阅发布不应先行。终端 visualizer 可以更早显示，不能把所有 UI 输出都当成落盘证明。这个 persist-before-publish 顺序减少了“订阅者看到但事件没存下”的窗口，却没有把文件写入、外部 API 与会话事件合成事务。存储后通知前退出时，应补读事件，而非重新执行同一业务动作。[回调次序](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)

Agent Server 的 session socket 又区分 durable、transient、delta 和同步等 envelope，不能把每条 socket 消息都当持久 Event。它通过有界发送队列处理慢消费者，必要时断开连接，并支持按 `after_seq` 恢复持久事件流。这是服务提供的通道契约；具体客户端使用哪条 socket 路由仍应核对，不能把新 session 协议自动套给所有客户端。[session socket](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/session_socket.py)

观测还有不同目的。SDK 的 Laminar/OpenTelemetry 集成可关联 conversation、工具调用与委派 trace；Server 文档另区分产品 analytics、完整 completion logging 和 tracing，前者默认关闭，不能把三者的数据范围混写。持久事件用来恢复事实，trace 用来找耗时，测试结果用来判断工作是否正确，三类证据互相补充。[trace 集成](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/observability/laminar.py)、[数据采集分类](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/README.md)

本书没有执行容器回收、存储故障、重启或秘密泄露实验。作者建议将这些作为部署验收：重连后核对会话与工作区身份；事件补取按原生身份去重；取消后查看资源实况；业务提交缺少结果时回读外部状态。源码支持提出这些检查，但不能替代运行环境中的验证结论。

## 8. 一次任务穿过架构：修复仓库中的解析错误

设想用户要求“修复配置解析器处理空输入的错误，并证明已有行为未退化”。以下是作者构造的任务走查，不是已运行示例。接入端选择 Agent 的模型、TerminalTool、FileEditorTool 与 TaskToolSet，把仓库放到指定 workspace，再创建远程 conversation。若使用每会话 Docker mode，控制面解析配置、建立持久身份、启动容器，最后把会话创建请求转发到容器中的 Agent Server。[工具配置](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/agent/base.py)、[容器创建顺序](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/routers.py)

任务消息进入会话，项目指令按启用的 AgentContext 规则加载；Agent 从当前 View 请求模型，模型调用文件工具定位解析入口。一个 task 可以让子 Agent 独立追踪调用者和相关测试，只返回位置与发现；父 Agent 根据回收的 observation 修改代码，再用终端执行测试。共享 workspace 意味着子任务可以读到同一工作副本，也意味着并行写入需要另行安排；作者在此建议让探索子任务只读，集中修改责任。[上下文装配](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/context/agent_context.py)、[子任务运行](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/manager.py)

若测试命令需要确认，Conversation 停在待批动作，用户批准后继续该动作；若用户中断，应该检查命令是否仍运行、文件是否已改变，而非重建一份“干净的成功故事”。最终交付应关联实际 diff、测试命令与退出结果，并说明未覆盖的情况。模型的完成状态可以结束循环，验收证据是否充分仍由任务要求决定。[运行与确认边界](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/impl/local_conversation.py)

如果探索任务第一次返回“缺少某个失败样本”，父 Agent 可以带着更具体的问题按 task ID 继续子会话，复用其已保存上下文；如果工具集合或子 Agent 定义发生变化，则不能绕过会话恢复的一致性检查。这里选择继续已有子任务，目的是保留调查过程；选择新建任务，则是刻意切断旧背景。两种选择需要由任务语义决定，不宜仅按哪个调用更方便。[任务恢复](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-tools/openhands/tools/task/manager.py)、[恢复校验](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/state.py)

这一结构的接入价值在于可以分别控制 Agent 能力、会话协议和执行环境。小型本地工作流可以直接持有 LocalConversation；服务化系统则需要维护会话存储、身份、镜像与容器生命周期。作者的选择标准是组织是否需要并能承担这些控制点，而非仅凭“开源”推断完全离线、自动安全或必然更低成本；模型数据去向与隔离效果都应按实际配置评价。

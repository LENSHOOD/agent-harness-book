# 第十四章 OpenAI Codex：协议化的 Agent Core

> 本次查阅日期：2026-10-29。内部实现继续采用 Rust 0.155.1，固定提交 `be2951ea34f0d295ed0becf97079f92fa5f6950e`，不声称它是当前最新版；官方网页按本次访问日期引用。本章分析公开的本地 Harness，不用客户端源码推断托管 Agents API 的服务端实现。[版本定义](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/Cargo.toml)

## 1. 整体架构与职责边界：协议包住的是运行时

理解 Codex，应先把“界面上的聊天”拆成三个层次：产品决定用户正在处理什么业务；Harness 决定如何把任务持续运行下去；模型决定下一步输出消息还是调用工具。官方对平台化的解释正是复用 agent loop，让应用继续拥有业务上下文、工具和控制界面。App Server 是进入这个运行时的双向接入面，不是循环本身。[平台说明](https://developers.openai.com/blog/codex-as-a-platform)

在固定源码中，`ThreadManager` 持有 `ThreadId → CodexThread` 映射，并通过 `ThreadStore` 管理存储；`CodexThread` 包装一个 `Session` 及其操作、事件端点。真正的运行状态在 `Session`：历史与配置状态、活动 turn、待处理输入以及执行所需的服务。这样的分工允许客户端更换界面，同时让会话状态归运行时管理。[线程管理](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/thread_manager.rs)、[线程包装](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/codex_thread.rs)、[Session](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/session.rs)

下面是作者依据这些组件绘制的职责图；箭头表示主要调用与回传关系，不表示每条路径都跨进程。

```text
产品客户端：业务对象、交互、审批呈现
        | 请求 / 通知 / 服务端反向请求
        v
App Server -> ThreadManager -> CodexThread
                                   |
                  Session + SessionIo
                  |                |
             run_turn          ThreadStore
                  |          历史、检查点、设置
       +----------+-----------+
       |                      |
 ModelClient              ToolRouter / ToolRegistry
 模型请求与响应                 |
       ^              +-------+---------+
       |              |                 |
       +-- 工具结果 -- 执行 runtime     MCP / 宿主工具
                      |
              审批 + SandboxManager

AgentControl：同一根任务树内的子代理注册、通信与生命周期
```

App Server 把这种执行活动投影为 `Thread / Turn / Item`：线程包含多轮请求，一轮请求包含消息、命令、文件变化等 item。stdio 使用按行分帧的 JSON，消息省略 `jsonrpc` 字段；还允许服务端反向请求审批。协议因此既承载内容，也承载控制权的交接。[协议与对象](https://developers.openai.com/codex/app-server)

接入层并非可互换的名称。这个固定版本的 TypeScript Codex SDK 通过子进程封装 `codex exec` 的 JSON 输出；本次查阅的官方文档则明确 Python Codex SDK 控制本地 App Server。应分别核验语言实现，不能把它们等同于通用 Agents SDK，或把某个 SDK 的能力自动移植到另一个 SDK。[TypeScript 执行封装](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/sdk/typescript/src/exec.ts)、[Codex SDK](https://developers.openai.com/codex/sdk)

## 2. Agent loop 与恢复：一轮请求可以包含多次采样

对应第六章，Codex 的 turn 不是一次模型 HTTP 请求。`SessionIo` 以提交队列接收操作，以事件队列输出进展；`run_turn` 为一次模型采样捕获 `StepContext`，使上下文、公布给模型的工具以及随后调用工具时使用的设置共享同一请求视图。这样可以避免配置刷新后，模型看到的能力与执行器实际采用的能力相互错位。[队列端点](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/mod.rs)、[循环与请求快照](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs)

每次采样从当前历史构造输入，收到工具调用后执行并纳入后续采样；循环同时检查模型是否需要继续、用户是否追加输入、是否达到上下文预算。没有后续工作时才进入停止路径，Stop hook 仍可能要求继续处理。这里的设计动机是让“继续、等待还是结束”成为宿主状态机的判断，而不是只看模型刚刚说了“完成”。[run_turn](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs)

失败恢复也有层次。采样代码区分不可重试错误、上下文超限与使用额度问题；流式连接错误走重试状态、退避和满足条件时的传输回退，部分连接重试行为还受 feature 配置控制。它恢复的是模型请求链路，不能由此推出数据库写入或远程工单创建具有“恰好一次”语义。[采样错误处理](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs)、[流重试](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/responses_retry.rs)

中断处理活动任务、取消信号与排队输入，终态事件后还有显式的历史刷新屏障；恢复则从 rollout 中选取仍有效的压缩检查点及后续记录，重建历史和设置基线。其恢复单位是可持久化的会话状态，不是一个暂停在任意指令上的操作系统进程快照。[任务结束与中断](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tasks/mod.rs)、[历史重建](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/rollout_reconstruction.rs)

## 3. 上下文与会话：模型窗口、宿主事实和记忆各有归属

对应第七章，输入不是把聊天记录拼接后直接发送。`AGENTS.md` 加载器沿项目根到当前目录收集项目指令，支持 `AGENTS.override.md`，并受项目可信状态与字节预算约束；`run_turn` 再记录环境和设置变化，使用当前步骤对应的上下文构造请求。因此目录、权限或工具变化也是会话需要表达的事实。[项目指令装配](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs)、[上下文更新](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs)

`ContextManager` 保存有序的 `ResponseItemEnvelope`、token 信息、用于差异更新的上下文基线，以及独立于模型窗口的 `retained_context`。工具输出进入历史时可按截断策略缩短；`for_prompt` 再把历史转换成模型请求输入。这解释了为什么界面上可见的记录、落盘的记录和某次实际送给模型的内容不能被当作同一份数据。[ContextManager](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs)

压缩改变工作窗口，却不应替用户改写授权。源码专门用 `replace_compacted` 保留这条边界；本地压缩路径生成摘要、保留一定用户消息，并根据发生在轮前还是轮中决定何时补回初始上下文。轮中的上下文注入还要保持摘要所在的相对位置；远程压缩则由 provider 能力选择另一条路径。压缩由此是一项上下文重建操作，而不只是删除旧文本。[压缩替换](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/context_manager/history.rs)、[本地压缩](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact.rs)、[路径选择](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/session/turn.rs)

跨会话记忆又是另一条流水线。该版本的设计文档描述：在记忆功能开启、非临时根会话且有状态库等条件满足时，后台先从合格 rollout 抽取结构化记忆，再持有全局阶段锁汇总共享记忆材料。第一阶段可并行，第二阶段串行，是为了避免多个任务同时改写同一记忆工作区。它有启动条件、筛选规则和失败重试，不等于每条消息都会永久保存为可靠知识。[记忆流水线](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/memories/README.md)

## 4. 工具、MCP 与扩展：声明能力和执行能力必须对齐

对应第八章，`ToolRouter` 同时持有模型可见的工具规格与 `ToolRegistry`；它把模型响应解析为含名称、调用 ID 和 payload 的工具调用，并查询工具是否允许并行。`ToolRegistry` 再按名称找到 runtime、检查载荷类型、执行 hooks 和处理结果。设计重点在于，一份最终工具计划同时确定“模型能请求什么”和“宿主能执行什么”。[工具路由](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs)、[注册与分派](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/registry.rs)

MCP 接入在这个边界上增加适配。客户端初始化时协商能力并列举工具；`McpHandler` 把 `ToolInfo` 转成模型工具规格，再把调用送入 MCP 调用路径。结果经工具输出路径回到历史，模型才能据此继续。只读提示等元数据还可能影响并行许可，因此服务端声明不仅是帮助文本，也参与调度决策。[MCP 初始化与发现](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/codex-mcp/src/rmcp_client.rs)、[McpHandler](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs)

扩展不只有 MCP。`DynamicToolHandler` 接受线程提供的工具规格，并在调用时向宿主请求结果；技能扩展则负责目录、选择、provider 和指令注入。前者增加动作入口，后者增加任务知识与操作方法，两者可以组合，但技能文字本身并没有创建新的隔离执行器。[动态工具](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/dynamic.rs)、[技能扩展](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/ext/skills/src/lib.rs)

工具 hook 也有明确时间边界：前置 hook 可以阻止调用，后置 hook 拒绝的是已经返回的结果，不能撤销此前完成的动作。对企业工具而言，这意味着拒绝不可信结果与阻止业务写入必须放在不同位置，不能用一个“验证失败”状态含混地覆盖两者。[分派与 hook 边界](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/registry.rs)

工具数量增长时，还要区分“已经注册”与“本轮直接公开”。路由器可识别延迟发现的工具，动态工具也保存 `Direct / Deferred` 暴露方式；模型不必在每轮都看到所有工具的完整定义。作者将这一设计理解为上下文预算与能力发现之间的折中：缩小初始工具目录，同时保持发现后的调用仍落到同一注册表，不让搜索结果成为绕过执行校验的新入口。[可见性判断](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/router.rs)、[动态工具暴露方式](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/dynamic.rs)

## 5. 权限、沙箱与凭证：决定能否做，与限制如何做

对应第九章，审批策略回答“此动作是否需要进一步许可”，沙箱回答“执行时实际允许访问什么”。官方文档将两者明确区分；源码中的 `ToolOrchestrator` 把审批要求、首次沙箱选择、执行尝试和失败后的升级路径集中起来。工具被判为禁止时直接返回拒绝，不能把所有沙箱失败都解释成应该自动提权。[审批与隔离](https://learn.chatgpt.com/docs/agent-approvals-security)、[ToolOrchestrator](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs)

`SandboxManager` 进一步把抽象权限、命令、工作目录和网络设置变成执行请求。固定版本的后端类型包括 `MacosSeatbelt`、`LinuxSeccomp` 和 `WindowsRestrictedToken`，具体选择还取决于平台与启用条件。共同权限模型让上层表达工作区访问范围，平台实现负责落到系统机制；这并不证明各平台拥有完全相同的隔离效果。[沙箱转换与平台选择](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/sandboxing/src/manager.rs)

执行隔离也不能替远程业务系统认证。MCP 是另一条服务调用路径，宿主动态工具又把执行交回应用；企业接入时，应在这些服务端检查租户、资源和动作权限，而不能把本机文件沙箱当成远程数据库的权限模型。这是由调用边界导出的架构要求。[MCP 调用适配](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs)、[宿主动态工具](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/dynamic.rs)

登录凭证有单独存储职责：`AuthCredentialsStoreMode` 可以选择文件、系统 keyring、自动选择或临时存储，文件后端涉及 `auth.json`。因此“模型不直接处理密钥”与“本机没有持久凭证”是两个不同命题；部署时应把凭证存储方式作为运行环境配置，而不是写进任务提示词。[凭证后端](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/login/src/auth/storage.rs)

## 6. 子智能体与委派：子线程共享控制面，各自运行循环

对应第十一章，Codex 的子代理是受管理的线程，而不是给同一条历史加一个角色标签。`AgentControl` 在同一根任务树内共享注册表、执行限额和预算，并持有指向线程管理器的弱引用；这种设计把父子关系放在控制面，同时避免管理器与会话互相持有强引用形成生命周期环。[AgentControl](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agent/control.rs)

以该版本 V1 路径为例，`spawn_agent` 接受任务输入，可选择 `fork_context`，记录父线程、父 turn、根 turn 和环境选择，并检查派生深度。创建时会应用角色和模型设置，再继承当前审批策略、工作目录与权限配置。由此可以把上下文隔开，却不能把“另一个线程”推导为“另一个文件系统”或“另一套业务账号”；需要文件隔离时，工作区仍须显式安排。[创建路径](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs)、[运行时设置继承](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_common.rs)

结果回收依赖状态订阅。V1 `wait` 返回代理状态和超时信息；`AgentStatus` 又从开始、完成、错误和中断事件推导，完成状态可以携带最终消息。`Interrupted` 在这里不属于普通的最终完成状态，等待超时也不表示子任务已经失败。父代理因此需要区分“现在没有结果”与“已经得到终态结果”。[等待](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents/wait.rs)、[状态推导](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agent/status.rs)

取消同样分层：`interrupt_agent` 向指定线程发送中断操作；关闭路径则记录关闭关系，并关闭从内存派生树可达的活跃后代。这是会话树生命周期管理，不是文件写入或外部服务的事务回滚。固定源码还包含 V2 委派工具实现，所以上述 V1 名称是具体路径说明，不是所有版本唯一不变的公开契约。[指定线程中断](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agent/control.rs)、[关闭树](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agent/control/legacy.rs)、[V2 创建实现](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents_v2/spawn.rs)

## 7. 验证与可观测性：看到执行，不等于证明正确

对应第十、十二章，App Server 提供 `item/started`、`item/agentMessage/delta`、`item/completed` 和 `turn/completed` 等事件；中断请求的精确名称是 `turn/interrupt`。事件中的关联标识让客户端把文本、工具和终态归回同一执行过程，但完成通知还需要读取状态，不能仅凭方法名标记业务成功。[固定协议枚举](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs)、[生命周期](https://developers.openai.com/codex/app-server)

运行时还提供工具分派 trace，并按配置构造 OpenTelemetry exporter；这些机制可以帮助定位哪次调用失败、耗时或经历重试，却不会替代回归测试和业务不变量验证。平台应把工具输出、代码差异、测试结果与业务任务关联，尤其在重连后保留尚未确认的动作状态。[工具 trace](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/tool_dispatch_trace.rs)、[遥测初始化](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/otel_init.rs)

本章的运行证据仍限于历史局部探测：2026-09-19 的本机 0.142.5 两套生成 schema 及离线方法、字段和源码对照共 58 项符合预期；三次自施受限启动都在 `initialize` 响应前以 exit 1 报 `Operation not permitted`，具体拒绝路径与系统调用未知。没有发送 `initialized`、`thread/start`、`turn/start` 或模型请求，正常握手、取消与模型流均未端到端验证，也不能据此认定产品不可用。原始材料在研究目录 `review_20260919/vendor_probe/codex/`；本轮只核对文档与源码，没有把阅读源码记成实跑成功。

## 8. 一次任务如何穿过架构：修复导出遗漏

设想用户要求：“修复订单导出跨页遗漏，增加回归测试，并说明是否影响已有数据。”下面是作者设计的架构走查，不是已完成的产品实验。业务应用先提供订单模块位置、失败样本和验收条件，再把任务交给线程；`thread/start` 建立会话，`turn/start` 开始工作，客户端持续消费 item 事件。这让业务对象留在应用层，执行过程进入 Harness。[线程与 turn 接口](https://developers.openai.com/codex/app-server)

进入 core 后，项目指令、环境与当前历史形成步骤上下文；模型可以通过工具读取实现，再把“核对分页边界条件”委派给子线程。若父线程改代码、子线程只读分析，应用应事先约定文件职责；上下文分开本身不会防止同目录写入冲突。这个例子利用了线程派生与环境继承机制，但读写职责是作者建议的任务组织方式。[指令加载](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/agents_md.rs)、[子线程创建](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs)

假如需要查询内部字段定义，应用可通过 MCP 暴露只读查询；模型拿到查询结果后选择补丁和测试动作。命令执行经过工具分派与审批、沙箱路径，结果再次进入历史。若安装缺失依赖需要网络权限，应先让权限机制做出决定；拒绝后应调整方案或报告缺失条件，而不是把一次失败无限重放。[MCP 工具](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/handlers/mcp.rs)、[执行编排](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/tools/orchestrator.rs)

任务拉长时，压缩保住继续推理所需的窗口；应用还应把验收条件和测试材料存为可再次读取的工件。最终答复应说明复现样本、修复差异、回归结果及数据影响依据，平台再以独立检查决定是否接受。后一项是本书的验收设计：运行时会话结束不能代替业务证明，摘要也不能成为唯一证据库。[上下文压缩机制](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/core/src/compact.rs)

接入取舍由此变得具体：批处理任务可选 `codex exec` 或适合该语言的 Codex SDK；需要长会话、中途控制、审批与细粒度进展的产品更适合直接接 App Server。复用循环会减少应用自行实现状态机的工作，同时让应用必须认真维护协议版本、工具权限和结果验收。可复用的是执行机制，业务完成标准仍需应用定义。[官方接入层选择](https://developers.openai.com/blog/codex-as-a-platform)

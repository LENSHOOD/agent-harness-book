# 第十六章 DeepSeek Harness：可组合、可逆的运行时

> 本章访问日期：2026-10-29。沿用已固定的 `dsh-v0.1.6-alpha.2`、commit `ddefc45fbc7f8e46dd73185e68295696d1297887`，不声称它是访问日最新版。以下是该版本公开文档与源码的架构分析，没有运行上游程序或验证安全隔离。[固定版架构](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md)

## 1. 整体架构与职责边界：运行的是一棵插件树

dsh 把模型适配器、工具注册表、会话日志和默认 Agent 循环都放入 Cordis 插件体系。插件向共享 Context 注册服务、类型化事件和随生命周期释放的效果；替换循环或文件系统提供者，不必另造一个应用入口。这里的“可逆”首先指注册关系与受管理资源可以撤销，并不意味着插件已经造成的业务写入会倒退。[组件与扩展机制](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#cordis)

实际启动树由 profile 组装：按顺序加载 bundle，再应用 profile、home 与命令行 patch。按 id 命中的 patch 替换整份 config，不能按深合并理解。`dsh-base` 提供常用基础能力，Web、SDK、headless 等 bundle 再增加交互载体；`sdk-minimal` 则持有自己的完整小型树。因而“同样使用 dsh”并不证明两次任务拥有相同的工具、策略或持久化组件。[组合与启动](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#profiles-and-bundles)

下图为作者依照服务归属绘制的调用关系。它对应第五章的职责分解：Host 承载控制与服务，执行后端承载代码运行，Session 承载可重建事实；三个位置不能因为都叫 runtime 而混在一起。[核心服务及能力接口](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#core-packages)

```text
profile + ordered bundles + patches
                 |
        Cordis Host / shared Context
                 |
Web / SDK --> ctx.agents --> AgentLoop <----> ctx.sessions
                               |              事件日志
                    ctx.systemPrompt          |
                               |        deriveMessages()
                            ctx.llm <----------+
                               |
                            ctx.tools
                     /         |          \
                文件/命令      MCP      run_code / PTC
                   |           |             |
          fs/subprocess    外部服务器   独立 Node 进程
                   \_________________________/
                         所选执行世界与策略
```

能力替换进一步分成 Service Definition、Service Provider 和 Consumer：接口定义约束提供者，工具等消费者只调用接口。例如文件系统与子进程提供者需要属于同一个执行世界，切换到远端时才能让文件路径与命令操作同一对象。这里可组合的单位是有明确输入输出与生命周期的能力，不是任意把几个插件名堆在配置里。[能力接口](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#capability-seams)

一个作者构造的反例是：底层工具配置包含超时和策略，上层 patch 只写超时，却误以为其他字段仍会继承。由整份替换规则可知，应检查最终解析树，而不只检查新写的几行。配置组合既提供自由度，也把“本次到底运行了什么”变成可复现性的一部分。[覆盖规则](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#profiles-and-bundles)

## 2. Agent loop 与恢复：把请求、尝试和回合分开

`ctx.agents` 提供创建与恢复入口，`AgentLoop` 是可替换的默认驱动。创建阶段先完成 scoped setup 和串行 `agent/created` 初始化，随后才处理队列。调用者持有的 `AgentHandle` 负责最终释放：停止循环、等待退出、注销 Agent、移除内存会话，再拆除其作用域。这使“已构造对象”“已准备执行”“已完成释放”成为不同边界。[创建与所有权](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/core.md#creation-and-ownership)

一次 `followup` 把消息排入下一回合；`steer` 面向最近的步骤边界；`inject` 只加入上下文，不唤醒空闲驱动。一个 turn 可以有多个 step，每个 step 包含一次模型请求及其工具调用。驱动认领输入，组装提示和工具 schema，经 `agent/pre-step`、请求准备后，把被接受的输入写入日志，从日志冻结模型历史，接收响应、执行工具，再判断是否还欠一次模型请求。工具结果因此是下一步推理的正式输入，而非 UI 旁边的临时显示。[输入契约](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/core.md#the-agent-handle)、[步骤顺序](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#turn-flow)

一次请求也不等于一次成功回答。成功内容落为 `assistant/message`；已结算的失败、重试、取消尝试落为 `assistant/attempt`，后者留作日志而不污染模型历史。重试不重做提示组装和 `pre-step`。实时 `agent/assistant-stream` 的 chunk 是进程内消息，完整紧凑流到结算时才嵌入持久事件；此前硬退出可能丢失这一尝试的完整流。[尝试与持久化](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#session-log)

`cancel` 中断当前活动，默认清除待处理输入，`keepInbox` 可保留它；`whenIdle` 等待整个 Agent 静止，不是某条消息的完成凭证。第六章的恢复问题在这里有了具体落点：应先检查日志中哪个 turn、step、attempt 已结算，再决定继续什么；不能把界面停止刷新当作命令已被撤销。[取消与静止](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/core.md#the-agent-handle)

请求接纳还有一个细节：循环先经 `agent/request` 与 `prepareCall()` 确定真正的模型路由和能力，再提交系统提示及被接受的用户消息；准备期间取消，不会把尚未进入模型调用的输入冒充成已发送历史。随后派生并冻结请求，同时保持取消信号有效。作者据此将它理解为“记录已经接纳的事实”，而不是“用户一提交，就假设模型已经读过”。[请求准备与接纳](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#turn-flow)

## 3. 上下文与会话：日志保存事实，投影决定模型看见什么

`ctx.systemPrompt` 汇集有序 `PromptSection` 和工具声明，循环把渲染结果记录为 `system/message`。变化频繁的 `PromptContext` 则以持久 user-role 快照进入历史，在内容改变或被压缩移除后更新。系统指令和运行状态分别入账，既能解释请求来自哪里，也能避免每次状态变化都重写提示前缀。[提示组装](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/system-prompt.md)

工作区知识由具体贡献者提供。例如 `dsh-agent-instructions` 将全局与项目 `AGENTS.md`、`CLAUDE.md` 等文件按由宽到窄的顺序注入，受字节预算约束；成功的文件读写可发现深层指令，恢复会话时重新核对基线。它不持续监听所有外部编辑，也不通过猜测任意 shell 命令来发现目录变化。此处可借鉴的设计是：指令来源、发现时点与注入消息都有归属，而非把工作区当成模型天然知道的背景。[工作区指令](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/context/agent-instructions/README.md)

日志保留的内容多于当前模型上下文。`deriveMessages()` 从追加式事件推导可见历史；压缩作为可选 `ctx.compaction` 能力，在日志中记录 start、summary、end，再用带 `surfaceOp: replace` 的 `user/message` 替换模型视图中的一段内容。旧事件不因视图替换而消失。锁最后才释放，崩溃留下未闭合 start 可以被检测；压缩提交和持久化仍可能分别失败，不能视为无损记忆或绝对事务。[压缩协议](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/compaction.md)

恢复还涉及存储格式。JSONL provider 选择最高的规范 generation，沿相邻版本链迁移；只读打开不发布新文件，写打开则验证并排他发布新版本，旧 generation 保留。未来版本被拒绝，普通未封口尾部的修复仍由 handle 消费者承担。这样把第七章的“重建会话”分成了物理记录恢复与模型视图重建两件事。[会话存储与迁移](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#session-log)

自动压缩通常发生在下一步请求派生之前；确认的上下文溢出也可经请求错误处理触发恢复。后端可以先裁剪工具结果再决定是否需要摘要，只有可见表面实际推进才返回相应重试动作，避免对同一超限请求无意义地循环。压缩边界保护工具调用与结果配对，却不一定保留整个 turn，因而一轮很长的工作也能逐段缩减。[压力与溢出恢复](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/compaction.md)

## 4. 工具、MCP 与扩展：统一分派，分别拥有执行

工具作者用 `defineTool` 声明参数、输出和执行函数，注册到 `ctx.tools` 后参与提示组装。模型调用先成为 `tool/call`，再经过 `tools/pre-execute`、只能收紧的 guards、`tools/execute` 和 `tools/post-execute`；最终内容约束及结果观察完成后，循环记录 `tool/result`。这种分层把工具业务逻辑与审批、拦截、结果规范化分开，也让普通工具错误能够作为结果返回给下一步。[注册契约](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/core/tools/README.md)、[分派管线](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-execution-pipeline.md)

PTC（程序化工具调用）改变模型组织工具的方式：native 模式展示各工具，ptc 模式展示 `run_code` 和生成的 SDK，也可同时提供两者。模型写一段 TypeScript，在一个程序内处理返回数据并调用绑定函数；桥接子调用仍走同一注册表和审批管线，带父调用关联并记录 `tool/ptc-dispatch`。中间绑定值不逐项进入模型历史，外层结果才返回，这解释了 PTC 为什么适合多次查询后的程序化筛选。[工具呈现](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/core/tools/README.md)、[PTC 返回路径](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md)

MCP 则解决工具来自哪里。每个 opt-in 客户端插件持有一个服务器连接，将发现的工具注册到调用者可见的 scope；stdio 与 Streamable HTTP 使用官方 SDK 协商。资源工具按服务器名查询，服务端指令进入有来源的提示段，断线或列表刷新失败有各自生命周期。此固定版不支持 MCP prompt templates、elicitation、task-based execution 和资源订阅，不能从“支持 MCP”推出协议能力全集。[MCP 适配边界](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/mcp.md)

运行时“演化”具体发生在插件组合上。Creator 先用 `cordis_inspect_list/query` 读取准确 API，再通过 Plugin Manager 安装持久 bundle；安装后的 Host 代码在宿主进程执行。当前 Creator 流程不能与旧的临时动态定义流程混写，程序及浏览器消费者使用的动态 runner 也并未因此消失。扩展改变工具与界面供给，并不等于模型参数发生训练。[只读发现](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/tool-cordis/README.md)、[持久插件管理](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md)

## 5. 权限、沙箱与凭证：三个问题，三条边界

`ctx.approval` 回答“这个动作是否获准”。只有 `allowed-once` 是许可，拒绝、取消、无人应答都不放行；每次请求有配对的 `approval/asked` 与 `approval/decided` 日志。尤其要读准策略名：dsh 的 `never` 表示永不询问、所有需要询问的动作一律拒绝，不是自动批准；一次批准也不永久改变会话权限。[审批契约](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/approval.md)

`ctx.sandbox` 回答“执行时允许产生哪些文件效应”。`read-only`、`workspace-write` 交给平台后端，`danger-full-access` 绕过限制；Linux、macOS、Windows 的实现与完整度不同，必须保留 `full/partial` 报告。该 mode 词汇本身不覆盖网络与进程可见性。凭证另由 `ctx.credentials` 保存与解析：配置携带引用，模型适配器每次请求重新取值，便于轮换；这不是沙箱替你管理凭证生命周期。[沙箱语义](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/sandbox.md)、[凭证服务](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/credentials.md)

PTC 后端先解析执行世界中的 Node 与 bootstrap，经 sandbox 包装 argv，再由 subprocess 启动独立进程。Host 管策略、期限和绑定分派，子进程计算程序；直接 Node API 仍可用，程序可见环境被清空，请求受限模式而后端不可用时失败。与之不同，动态 Host runner 的 `node:vm` 明确不是安全 containment，宿主 realm helper 仍可能成为逃逸路径，已安装插件同样不能靠工作区沙箱隔离。[PTC 启动](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md)、[Host 信任边界](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/cordis-host-runner/src/sandbox.ts)

PTC 默认期限为 120000 毫秒、上限 600000 毫秒，包含等待审批与子工具的时间，清理可使返回更晚。V8 heap cap 不限制整棵进程树内存，也没有进程树 CPU 计量；fallback 平台逃离管理范围的后代可能残留。输出上限只保留可容纳部分，绑定通道限额不限制 Host 绑定内部的全部分配；每次程序均为一次性执行，不提供跨调用状态或实时结果流。这些边界应与“独立进程”同时理解。[PTC 已知限制](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md#known-limitations-and-deferred-work)

## 6. 子智能体与委派：上下文继承不等于权限继承

`ctx.subagents` 是可选能力注册表，可同时容纳进程内、ACP 或其他产品后端。调用先核对 provider 是否支持模型覆写、结构化输出、深度、工具过滤和人格；不支持的请求在启动前拒绝。进程内 `spawn` 创建空历史子会话，`fork` 则取得父会话已完成 turn 的一次性快照，不含正在执行的 turn，后来父消息也不会自动同步。[能力协商](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/subagent.md)、[spawn](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/subagent/subagent-spawn-in-process/README.md)、[fork](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/subagent/subagent-fork-in-process/README.md)

两者共享宿主进程及相关服务，子 Agent 拥有新 scope；完整父工具限制和 authority 不被自动复制，工具过滤须在子创建窗口明确施加。一次性委派等待子任务自己的最终输出，取消、拒绝或截断成为错误结果，收集后释放 handle。因此“子会话独立”解释的是上下文和生命周期，不能自动解释为独立操作系统身份或更小的权限。[进程内子任务的所有权](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/subagent/subagent-spawn-in-process/README.md)

这不等于完全不继承策略：`captureDelegatedPolicyOverrides` 在第一次异步等待前捕获父会话显式 sandbox override，以及 Auto 或 Full access 的 preset 身份；父侧存在审批服务时，子审批策略钉为 `never`。新子会话在 fork seed 之后记录这些覆盖，冷恢复读取子日志。Auto 子调用仍逐次独立评审，不能将父任务的许可扩写成所有子动作的通行证。[委派策略捕获](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/subagent.md)

可继续的子任务又多一层：持久 child Session 可被多次激活，同一时刻至多一个 Activation，队列仍由 Agent inbox 统一拥有。接收消息之后，调用者后续取消不再撤销已接收回合；`interrupt` 只中断当前活动，保留未认领队列和已发布后代，且不等待完全静止。管理器整体卸载才执行向下取消、子先于父释放。最终 flush 失败会记录错误后继续释放，所以稍后恢复仍可能读到缺失或陈旧状态。[Activation 与取消范围](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/subagent.md#continuable-children-and-activations)

## 7. 验证与可观测性：区分事实日志、实时流与报告副本

会话事件用于重建请求与结果，`agent/*` 用于观察当前活动，能力事件用于在工具和文件系统等接缝处插入策略。PTC 子调用已有原生追踪，审批已有配对记录，不能笼统称为“平台必须从零补齐审计”。作者建议沿 Session、turn、step、attempt 与工具调用标识关联一次任务，而不是仅记录最后一句回答。[事件分工](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md#events)、[工具结果路径](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-execution-pipeline.md)

遥测不是另一份同等可靠的会话库。`session-telemetry` 将有序副本非阻塞交给 backend，cursor 只表示已经交出，不表示送达；崩溃可丢队列。默认没有内建脱敏规则，文件或命令输出夹带的秘密可能原样离开进程。需要可靠审计或共享 collector 时，应分别设计投递保存与脱敏规则，不能借用本地会话持久化的保证。[遥测交付边界](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/session/session-telemetry/README.md)

第十章的验证还要求回答“工作做对了吗”。运行事件可以证明调用及结果流转，却不能独自证明外部系统已处于期望状态。以下任务中的成功探针、独立测试和外部回读是作者建议；本章只做了固定源码交叉阅读，没有把文档中的失败处理当成已执行的故障注入。

对第十二章而言，这种分工也提示一种有效的诊断顺序：先从会话日志确认输入和输出，再看 attempt 解释失败请求，最后用实时事件或遥测定位延迟。若反过来仅用 collector 中“没有看到记录”断言动作未执行，就把报告丢失与执行失败混为一谈。这是作者根据上述持久化和尽力投递契约提出的排查方法，尚需实际故障实验检验。

## 8. 一次任务穿过架构：接入一个 MCP 查询能力

设想用户要求“把指定 MCP 服务接入当前 profile，确认能查询，再整理结果”。这是作者按官方 Creator 教程扩展的示例。Agent 先检查运行时 API，写一个包含 `dsh-mcp-client` 配置的 bundle，再调用 Plugin Manager 安装；HMR 启用时，新连接发现工具并注册到 `ctx.tools`，下次提示组装即可包含它。官方教程要求同时看到 `application: applied` 和成功的 ping，`restart-required` 仅说明配置已保存。[官方接入路径](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/user/develop/practice/dynamic-cordis.md)

随后可以直接调用查询工具，也可以让 PTC 执行一组查询并筛选返回数据；两种呈现都走工具权限和记录路径。若把结果解释委派给 spawn 子 Agent，应传入自足任务，并显式配置其工具范围；这些是调用者组合上的选择，不能靠父会话的限制自动推导。[PTC 管线](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-execution-pipeline.md)、[子作用域](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/subagent/subagent-spawn-in-process/README.md)

安装与演化的失败必须按阶段解释：pnpm 或 bundle 校验失败，恢复的是 `package.json` 和 lockfile，下载物、日志与构建脚本批准可能保留；安装成功后启用失败不撤销安装；删除按取消选择、卸载、移除依赖推进，失败保留已完成修改而不自动重新启用。构建脚本批准与普通工具批准分开，服务校验包名却不验证对话中的授权陈述。普通 HMR 保留成功兄弟项，不提供整批回滚；初始启动 required entry 失败才有另一套整应用清理规则。[管理失败语义](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md#failure-behavior)、[启动与 HMR](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/app-boot/README.md)

由此，作者的接入取舍是把 profile 当成需要版本管理的运行配置，把插件安装当成宿主代码变更，把查询结果当成需要业务验证的数据。dsh 的组合接口使这些控制点可检查、可替换；收益来自能精确改变哪一层，代价则是必须清楚谁拥有状态、谁清理资源，以及所谓“可逆”究竟止于何处。

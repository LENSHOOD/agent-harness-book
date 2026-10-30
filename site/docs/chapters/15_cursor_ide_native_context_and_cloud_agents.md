# 第十五章 Cursor：IDE 原生上下文与云端 Agent

> 资料访问日期：2026-10-29。本章依据官方文档与工程文章重建公开架构，不代表对闭源实现的源码审计。网页截面以证据账本中的内容 SHA-256 固定；未取得产品源码 commit。文中标明日期的历史能力保留原版本含义，示例为作者推演，未经产品端到端实跑。

## 1. 整体架构与职责边界：从编辑器进入执行系统

理解 Cursor，先把“在哪里交互”“在哪里组织模型输入”“在哪里执行工具”分开。IDE 提供工作区与会话入口；官方披露，初始上下文会包含操作系统、Git 状态、当前及最近查看的文件，更多信息由 Agent 动态获取。[Harness 工程说明](https://cursor.com/blog/continually-improving-agent-harness) 最终提示组装发生在 Cursor 后端，即使用户自带模型 API key，请求仍经过该后端。[数据使用说明](https://cursor.com/data-use) 因而“本地 Agent”主要说明工作环境的位置，不能解释为整套服务都在笔记本内运行。

下面按第五章的职责边界画出功能分区。这是作者根据公开契约归纳的图，不是内部进程图；“上下文服务”也不是声称存在某个同名内部类。索引链路来自官方索引文章，云端循环与 worker 的分工来自自管机器文档。[索引架构](https://cursor.com/blog/secure-codebase-indexing)、[自管机器](https://cursor.com/docs/cloud-agent/self-hosted)

```text
用户 <-> IDE / Agents Window / Web
          | 任务、规则、工作区线索
          v
Cursor 服务：提示组装、模型适配 Harness <-> 模型
          ^             | 工具请求
          |             v
上下文索引/检索     工具执行位置
  ^    |           +-- 本地工作区：文件、终端
  |    +-> 相关片段 +-- Cursor 云端 VM：仓库、依赖、测试
代码变化           +-- 自管 worker：企业机器上的工具
                              |
                  工具结果、diff、日志 -> 下一轮模型输入
```

托管 Cloud Agent 在独立 VM 中获得克隆仓库、依赖和运行环境；自管模式把文件编辑、终端、本地 MCP 等执行交给 worker，循环、推理与规划仍由 Cursor 承担。[Cloud Agents](https://cursor.com/docs/cloud-agent)、[Self-Hosted Machines](https://cursor.com/docs/cloud-agent/self-hosted) 这套分工的价值，在作者看来，是让同一种任务交互连接不同算力与开发环境；它的代价是上下文、会话和工作副本不再天然位于同一处。

## 2. Agent loop 与恢复：模型决策，应用执行

对应第六章，一轮工作可以抽象为“组装输入—模型提出工具及参数—应用执行—结果进入上下文—再次决策”。Cursor 的教学文档明确把执行责任放在应用一侧，模型依据返回结果继续对话；Agent 则把多次工具调用组织为搜索、修改、测试和纠错的循环。[Tool Calling](https://cursor.com/learn/tool-calling)、[Agents](https://cursor.com/learn/agents) 这解释了为什么测试输出是一轮新的输入：模型必须看见实际失败，才能选择补丁或更换方法，不能由“已经调用测试”直接推导任务完成。

这个循环还有模型适配层。Cursor 披露，它会针对模型及版本定制提示与工具格式，例如适配模型训练时熟悉的 patch 或字符串替换；中途换模型时也切换相应 Harness，同时提示新模型不要调用旧历史中已不可用的工具。[模型适配与会话切换](https://cursor.com/blog/continually-improving-agent-harness) 作者据此区分两种稳定性：文件最终如何变化可以保持一致，而模型眼中的动作格式不必相同。恢复旧会话因此也包含工具语境的衔接。

恢复要按状态对象理解。IDE checkpoint 在重大修改前保存文件快照，存于本地且独立于 Git；恢复会回退文件，却不会移除对话消息。[Checkpoints](https://cursor.com/docs/agent/overview#checkpoints) 所以恢复后可能出现“对话说补丁已完成，磁盘却回到补丁前”的状态，后续应重新读取文件。官方还区分排队消息与在下一次工具调用边界送达的运行中指令，后者保留正在执行的动作。[运行中引导](https://cursor.com/docs/agent/overview#steer-a-running-agent)

停止也有可观察契约：loop 结束时，`stop` hook 收到 `completed`、`aborted` 或 `error`；它还可以返回 `followup_message`，自动提交下一条用户消息，开始后续迭代。[停止事件](https://cursor.com/docs/hooks#stop) 因此应区分一轮结束、会话结束和任务验收，不能把任一停止事件直接记为业务成功。

云端另有持久化边界：会话状态、元数据和产物保存到 Cursor 管理的存储，以便审查和恢复；VM 则会按生命周期休眠、回收。[云端运行生命周期](https://cursor.com/docs/cloud-agent/security#how-cloud-agents-work) 这支持“继续一次工作”的产品契约，却没有公开逐条工具调用的事务重放、恰好一次执行或所有取消副作用的保证，本章不补写这类内部机制。

## 3. 上下文与会话：索引、指令、历史各有载体

第七章所说的上下文选择，在这里首先体现为增量索引。客户端构造文件与目录哈希组成的 Merkle tree，与服务端比较，只同步变化分支；变化文件被切成语法块，再转换为 embedding，并按块内容缓存。[首次索引流程](https://cursor.com/blog/secure-codebase-indexing) 这解决的是代码变化后怎样维护可搜索表示：不必每轮把整库重新塞进提示，也不必对未变内容重复计算。检索负责缩小候选范围，Agent 随后仍要读取与任务相关的代码。

索引复用也有边界。官方介绍的新工作区加速方案，会在同一用户或团队的索引中寻找相似版本；客户端提交的内容证明用于过滤搜索结果，无法证明本地持有的文件会被过滤。[索引复用与访问证明](https://cursor.com/blog/secure-codebase-indexing#proving-access) 这里应关注“候选索引”和“当前工作副本”的差异，而不能把复用索引理解为向新成员开放整个团队代码。

指令由另一条路径进入模型。Project Rules 存在 `.cursor/rules/*.mdc`，通过 `alwaysApply`、文件模式、描述相关性或手工引用决定何时加入；应用后的规则内容位于模型上下文开头。规则里引用文件只提供查找线索，并不自动展开文件全文。[Rules](https://cursor.com/docs/rules) 作者建议把必须持续生效的短约束放在规则正文，把大体量范例留在可读取文件中：前者保证任务方向，后者控制输入体积。

长会话则依靠压缩与重新发现相互补充。Cursor 在上下文达到限制时生成摘要，并向 Agent 提供历史文件引用，必要时可搜索被摘要丢失的细节；长 shell/MCP 输出写入文件，集成终端输出也映射到文件系统，供按需读取。[动态上下文发现](https://cursor.com/blog/dynamic-context-discovery) 设计动机不是无限扩大窗口，而是让大对象在窗口之外仍有地址。摘要负责继续工作所需的短状态，历史文件承担追溯，两者不能互相替代。

“记忆”还要区分版本与作用域。Cursor 1.0 在 2025-06-04 将 Memories 作为 beta 发布，说明其按个人、按项目保存对话事实并供未来引用；这是历史契约，本轮未核实同名能力在现行客户端的可用范围。[1.0 发布记录](https://cursor.com/changelog/1-0) 当前 Projects 文档则明确描述一组跨云端与本地机器同步的共享文件，持续积累研究、产物及工作约定。[Project 共享上下文](https://cursor.com/docs/agent/projects#shared-context) 规则是可审阅的行为指令，摘要服务当前会话，历史支持追溯，共享文件服务跨任务知识；把它们分开，才能判断一条过时结论应在哪里修订。

## 4. 工具、MCP 与扩展：从可发现描述到实际调用

第八章的工具链可分成接入、发现、分派与返回。Cursor 通过项目级 `.cursor/mcp.json` 或用户级同名配置接入 MCP server，支持 stdio、SSE 和 Streamable HTTP；前者由本机启动进程，后两者连接服务端点并可使用 OAuth。[MCP 接入](https://cursor.com/docs/mcp#how-it-works) 这些配置确定连接对象和认证材料，工具描述再告诉模型何时、如何调用，不能仅凭名称就赋予模型执行能力。

Cursor 的工程文章说明，MCP 工具描述会同步为按 server 分组的目录，模型先看到少量静态线索，任务需要时再读取说明；Skills 同样以名称、描述引导按需加载详细指令与附带文件。[工具与技能的动态发现](https://cursor.com/blog/dynamic-context-discovery) 这种设计把发现成本延后到真正需要的位置，也要求描述足够准确：不可发现的能力，即使已连接，也可能始终不会进入决策。

模型选定工具后，由客户端的协议集成把调用交给 server，响应再回到会话；界面可展开参数与结果，失败调用会标记错误供重试和查日志。[MCP 使用与故障处理](https://cursor.com/docs/mcp#using-mcp-in-chat) 需要改变循环行为时，hooks 提供另一种扩展面：它们是阶段性启动的进程，通过 stdio 双向 JSON 接收事件并返回观察、修改或阻断结果。[Hooks](https://cursor.com/docs/hooks) 因此，Skill 扩展工作方法，MCP 扩展外部动作，hook 接入执行时序；三者在架构中承担不同职责。

## 5. 权限、沙箱与凭证：批准动作不等于限制进程

对应第九章，本地 Run Modes 决定调用是否自动放行。Auto-review 先处理 allowlist，其他 shell 命令尽可能在沙箱运行，不能使用沙箱的调用交给后端分类器审查；MCP 与 Fetch 也参与审查。分类器拒绝后，Agent 可换方法或请求人工批准，官方明确说明分类器不是安全边界。[Run Modes](https://cursor.com/docs/agent/security/run-modes#how-auto-review-works)

执行隔离是另一层。`permissions.json` 调整自动批准与审查策略，`sandbox.json` 限制沙箱内的文件路径和网络访问；macOS 使用 Seatbelt，Linux 使用 Landlock 与 seccomp，Linux 环境不满足所需条件时回退到命令审批。[沙箱配置与平台实现](https://cursor.com/docs/agent/security/run-modes#sandboxing) 这使“允许跑测试”和“测试进程能读哪些文件、访问哪些网络”成为两个可分别配置的问题，而不是一次点击替代所有边界。

Cloud Agents 不使用本地 Run Modes，其专用机器允许自主执行工具，无需每一步都等待批准。[云端审批区别](https://cursor.com/docs/agent/security/run-modes) 凭证也有分层：Environment Variable 对 Agent 可见；Runtime Secret 仍注入环境变量，但在工具结果、转录和提交等位置脱敏；Build Secret 只供构建过程使用。[Secrets & Network](https://cursor.com/docs/cloud-agent/security-network#secret-protection) 脱敏因此是输出保护，不能解释为进程没有拿到凭证。

需要临时身份时，云端机器可通过本地 socket 申请 Cursor 签发的短期 OIDC JWT，外部服务验证签名与声明后授权；该身份属于整个运行，能访问 socket 的进程均可申请，并非每个 subagent 独占的身份。[OIDC 信任模型](https://cursor.com/docs/cloud-agent/identity#trust-model) 云端 MCP 登录态也与本机分开保存，退出本地登录不会自动退出云端。[MCP 认证边界](https://cursor.com/docs/mcp)

自管 worker 进一步把执行地点与数据流分开：完整 checkout 留在企业机器，但文件内容、终端输出、diff、截图和 MCP 结果会按任务需要回传；`agent worker start` 使用出站 HTTPS 长连接接收工具调用。[自管数据流](https://cursor.com/docs/cloud-agent/self-hosted#what-leaves-your-network) 选择它是为了接近内部服务或特殊硬件，不能据此推导推理和会话数据也完全留在内网。

## 6. 子智能体与委派：上下文隔离、环境隔离、调度分层

第十一章的委派首先发生在模型上下文之间。普通 subagent 从干净窗口开始，由父 Agent 在提示里给足信息；前台执行等待结果，后台执行立即返回，完成后把最终消息交给父 Agent。内建 Explore 和 Browser 用来吸收搜索、DOM 与截图等大量中间内容；自定义定义位于 `.cursor/agents/`，可指定模型和只读权限。[Subagents](https://cursor.com/docs/subagents) 这里最直接的收益，是让父会话保留决策所需结果，而不承担全部探索轨迹。

上下文独立不等于磁盘独立。普通 subagent 默认共享父工作副本；要求隔离时才使用独立 worktree 或云端环境。Cloud subagent 有自己的 VM 与分支，并使用团队配置的云端 MCP，而非直接继承本地 MCP 会话。[隔离副本与云端子智能体](https://cursor.com/docs/subagents#isolated-project-copies) 同样，后台 subagent 可按返回的 agent ID 恢复，父 Agent 可读取其输出了解进度；但公开材料不足以证明父任务取消会原子撤销所有后代已发生的外部动作。[恢复与状态](https://cursor.com/docs/subagents#resuming-subagents)

worker 则是执行资源，不是另一个独立规划者。Team Pool 是路由与等待队列，由 worker 领取会话，一台机器服务一个 Agent；My Machines 可让多个 Agent 共用一台机器，扩缩容量由企业自己的 controller 管理。[Worker、Pool 与 Controller](https://cursor.com/docs/cloud-agent/self-hosted#how-it-works) 因而并行度有两个来源：子任务拆分增加决策分支，更多 worker 或 VM 增加可同时执行的环境。

Projects 再把组织尺度扩大：coordinator 负责规划与委派，自身不写代码，并通过共享文件和 subscriptions 维持跨任务工作。[Projects](https://cursor.com/docs/agent/projects) 作者将其理解为三层组合：父子 Agent 交换任务结果，worker 提供执行地点，Project 保存持续工作的关系与知识。评估并行方案时应分别检查这三层，不能把多开几个云端任务等同于已经具备统一协调与结果合并。

## 7. 验证与可观测性：可回看过程，仍须验证结果

第十、十二章关注的验证，在 Cursor 中依赖完整开发环境。云端环境可预装依赖、配置启动方式，使 Agent 能构建、测试并操作修改后的软件；仪表盘显示该运行使用的 environment 与 Build，帮助解释“为什么同一补丁在另一环境失败”。[云端环境](https://cursor.com/docs/cloud-agent#environments) 云端还提供会话日志，以及通过 Cursor Cloud MCP 读取转录、运行事件、环境详情和 setup 日志的诊断能力。[云端可审计性](https://cursor.com/docs/cloud-agent/security#auditability)

hooks 能把观察点接到工具、编辑、压缩与子 Agent 生命周期，但覆盖范围取决于运行面：云端只执行命令型 hook，早期只读探索阶段不运行；自管 worker 的 sessionStart/sessionEnd 对应领取、释放会话。[Hooks 运行面](https://cursor.com/docs/hooks#cloud-agent-support) 命令 hook 以 2 退出可阻断，其他非零退出通常放行；权限 hook 以 0 退出却返回非法 JSON 或 schema 时另有阻断规则。[Hook 返回契约](https://cursor.com/docs/hooks#command-based-hooks) 因此，收集到若干事件不能证明所有调用均经过同一关卡。

Cursor 自身还将公开及内部基准、在线 A/B、工具错误、时延、token 效率、缓存命中和代码 Keep Rate 组合使用。[Harness 评测](https://cursor.com/blog/continually-improving-agent-harness) 作者的判断是，这些信号适合发现质量变化，但“代码仍被保留”并不证明业务正确。企业自己的验证链仍应把补丁、测试命令、真实结果与验收要求关联起来；子 Agent 的完成消息可以触发检查，不能替代检查。

## 8. 一次任务穿过架构：修复跨前后端的权限错误

设想用户在 IDE 中提出：“修复订单详情页对过期权限的处理，补回归测试，保留现有接口。”这是作者构造的架构走查，未实际运行。第一步应把验收条件和相关文件附给任务，使上下文选择有明确目标；IDE 工作区线索及按范围应用的规则，为后续搜索提供起点。[初始上下文](https://cursor.com/blog/continually-improving-agent-harness)、[规则作用域](https://cursor.com/docs/rules) 随后利用索引寻找鉴权入口、页面错误分支与测试，再读取当前代码核对，避免只凭名称相似就开始修改。[代码索引](https://cursor.com/blog/secure-codebase-indexing)

第二步可委派 Explore 查清后端返回契约，父 Agent 保留实现责任。该选择利用子上下文过滤探索输出的能力；若再让另一个 subagent 同时修改测试，则应明确文件所有权，或请求独立环境，因为默认工作副本是共享的。[委派与隔离](https://cursor.com/docs/subagents) 作者建议回传路径、接口约束及复现条件，而不仅是一句“已找到问题”，这样父 Agent 才能把子任务结论变成可检查的补丁依据。

第三步由模型提出编辑和测试调用，应用执行并回传失败信息，循环继续修复；日志过长时通过文件检索相关段落，而不是把丢失细节的摘要当作完整证据。[工具循环](https://cursor.com/learn/tool-calling)、[长输出处理](https://cursor.com/blog/dynamic-context-discovery) 若测试需要内部鉴权服务，可选择接近服务的自管 worker；若只需标准依赖和可公开访问的测试资源，托管 VM 能提供预备好的环境。两条路径都必须依据真实网络与凭证范围选择。[执行地点](https://cursor.com/docs/cloud-agent/self-hosted)、[托管环境](https://cursor.com/docs/cloud-agent)

最后把 diff、接口行为和回归结果一起交给审阅者。云端流程支持保存产物并以分支、PR 交接；这些是验证材料的载体，实际是否满足用户要求仍要由测试和审查决定。[云端交接](https://cursor.com/docs/cloud-agent/security#how-cloud-agents-work) 这次走查展示的取舍是：IDE 提供低成本的交互与现场线索，动态上下文控制输入负担，委派把探索移出主窗口，远程环境让测试接近所需资源。接入企业平台时，应保留这些职责之间的连接，尤其是任务标识、环境版本、测试结果和交接产物之间的对应关系。

> 研究注：原章的厂商 A/B 数字、Projects 发布时的 beta 状态及核验限制移入本轮 `cursor_disposition.md`。证据账本保存短引文、定位和来源截面；本章未把厂商指标当作独立效果复现，也未运行官方示例脚本。

# Harness 小书：历史、原理与中文文体独立深审

审阅日期：2026-09-19。审阅基线：`a1ed264462d9b61c260c1dc417243303bfc60b66`。项目根目录：`/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822`。下列 `file:line` 均相对于此根目录，行号对应本次读取的正文；旧稿引文另标 Git revision。

## 审阅范围与结论边界

已逐行完整阅读指定的 19 个文件，共 2,801 行，包括序言、第一至十二章、两篇导言、附录 B/C/D 和研究章程。随后只读检查上一轮改写报告、内容守恒脚本、最小 claim 账本、来源登记表，以及 `3b658c6 → a1ed264` 的相关 Git 差异。

本次没有联网、创建或控制浏览器，没有运行书中案例、公式或伪代码，没有修改正文、构建产物、其他代理的文件，也没有提交或发布。唯一写入文件为本报告。采用 planning-with-files 的阶段记录方法，但覆盖记录与发现均收在本文件，遵守用户的单文件写入限制。工作目录、项目及已检查的上级目录未找到 `RTK.md`，未假定其内容。

结论：上一轮“数字、链接、代码块守恒”确实能检查一部分机械改动，但不足以证明技术含义守恒。本次从真实 Git 差异中确认了新增的术语误释、指标漏译、评测用途改变和部署要求增强。正文也保留了若干早于改写的原理冲突。建议先处置下列 P1，再修复影响读者理解和实现的 P2；不把本报告视为发布批准。

严重性定义：P1 是可能诱导越权、重复副作用、错误完成，或使审校门禁产生错误放行结论的问题；P2 是影响论证、实验有效性、术语或可实现性的错误；P3 是局部措辞、重复和索引维护问题。“待运行验证”表示仅完成静态审阅，不代表已证明真实产品存在漏洞。“待主代理来源复核”表示现有本地证据不足，不代表断言为假。

## 逐文件覆盖矩阵

| 文件 | 完整阅读范围 | 本次检查重点与结论 | 对应发现 |
|---|---:|---|---|
| `manuscript/chapters/00_preface.md` | 1–26 | 乘法隐喻在首次出现处没有明示；能力边界与第三章口号需对齐 | R21、R25 |
| `manuscript/chapters/01_from_control_loop_to_agent_runtime.md` | 1–217 | 史实与现代类比之间存在谱系越界；早期四类沉淀位置与后文四层进化未映射 | R20、R22、R24 |
| `manuscript/chapters/02_the_autonomous_agent_boom.md` | 1–232 | 原型与后续产品有区分，但历史机制来源未固定；设计建议多于可检验历史证据 | R08、R20、R23 |
| `manuscript/chapters/03_interface_is_part_of_intelligence.md` | 1–150 | ACI 定义正确；能力上限措辞过宽；结尾跳过第四章 | R05、R21、R23 |
| `manuscript/chapters/04_the_coding_agent_turn.md` | 1–64 | 正确提醒环境、测试与预算混杂；重复段落和跨章重复削弱转折 | R08、R23 |
| `manuscript/chapters/05_system_model_and_responsibility_boundaries.md` | 1–217 | 概念模型有非数学限定；六层依赖、治理边界和“证明”阶梯不一致 | R09、R13、R21、R25 |
| `manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md` | 1–249 | 取消竞态、不确定提交解释有价值；拒绝分支、重试前提及 turn/task 混用需修 | R01、R03、R10、R16、R28 |
| `manuscript/chapters/07_context_cache_compaction_and_memory.md` | 1–240 | 权威状态与上下文分离清楚；压缩验收时点、缓存更新及“读模型”仍易误导 | R18、R19、R24、R25、R28 |
| `manuscript/chapters/08_tools_aci_mcp_and_code_mode.md` | 1–263 | 新增错误 ACI 全称、precision/recall 漏译；协议与授权管线可作正确对照 | R01、R05、R11、R25 |
| `manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md` | 1–261 | 四种安全机制区分清楚；缩权与组合安全的保证、R0 示例需限缩 | R13、R14、R27 |
| `manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md` | 1–266 | 目标/不变量/检查区分正确；完成门伪代码与该原则冲突；隐藏集反馈边界未闭合 | R01、R02、R07、R10、R13、R23、R24、R28、V03 |
| `manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md` | 1–296 | 有成本反例与合并重验；多数票、方差解释、权限来源和轨迹结构存在过度断言 | R11、R12、R14、R15、R16、R24、R25、V04 |
| `manuscript/chapters/12_observability_traces_and_eval_operations.md` | 1–118 | validation 用途被改错；示例事件的真实性、引用证明力和存储要求需收紧 | R06、R08、R09、R17、R24、V05 |
| `manuscript/parts/01_history.md` | 1–5 | ACI 新增全称错误；篇内问题链清楚 | R05、R20 |
| `manuscript/parts/02_principles.md` | 1–5 | 绝对必要条件写得过宽；完成契约的译法弱化了含义 | R10、R25 |
| `manuscript/appendices/B_architecture_review_checklist.md` | 1–68 | 证据驱动方向正确；“关键项”、不可逆动作补偿和回滚的判据不够可判定 | R27 |
| `manuscript/appendices/C_glossary.md` | 1–39 | ACI 定义正确；held-out/sealed 合并、平面关系及中译不统一 | R05、R07、R09、R25 |
| `manuscript/appendices/D_concept_index.md` | 1–42 | 多数定位可用；Agent/Workflow 首次集中定义、遗漏执行单位及重复提示需修 | R26、R28 |
| `research/planning/00_research_charter.md` | 1–43 | 章程对证据、边界、替代方案及指标的要求高于当前门禁实际覆盖 | R04、R08、R22、R24 |

## 最优先的十项

| 顺位 | 等级 / 编号 | 需要解决的具体问题 | 主要位置 |
|---:|---|---|---|
| 1 | P1 / R01，待运行验证 | 两段参考伪代码没有显式拒绝分支，`DENY` 可能落入执行或提交路径 | 第六章:214；第十章:204 |
| 2 | P1 / R02，待运行验证 | 外部动作确认提交即进入 `VERIFIED_COMPLETE`，缺少提交后的业务目标检查 | 第十章:168 |
| 3 | P1 / R03 | 把“可补偿”列为安全重试的充分替代条件，混淆补偿与幂等 | 第六章:112 |
| 4 | P1 / R04 | 上轮机械守恒检查被扩大解释为技术含义守恒，真实差异已提供反例 | 旧改写报告:7、25；守恒脚本:58 |
| 5 | P2 / R05 | ACI 出现 Computer、Context、Control 三种互相冲突的全称 | 历史导言:3；第八章:3 |
| 6 | P2 / R06 | validation set 被从“选择候选”改成“选样本” | 第十二章:104 |
| 7 | P2 / R07 | 泛称 held-out 与密封终测合并，修复反馈和最终泛化证据的边界不清 | 第十章:198、212；附录 C:33 |
| 8 | P2 / R08 | 最小 25 条 claim 的通过不能覆盖章程要求的全部事实；若干核心来源仍未核验 | 研究章程:35；来源账本:36、41、55、61 |
| 9 | P2 / R09 | 六层“只依赖下层”与执行时授权、状态记录的跨层职责冲突 | 第五章:188、196；第十二章:19 |
| 10 | P2 / R10 | turn 结束、取消和任务验收混用，结尾“停止必须经过完成契约”范围过大 | 第六章:24、249；第十章:5 |

## 详细发现与可直接采用的修法

### R01 — P1：授权拒绝没有被参考伪代码明确封闭（待运行验证；旧稿遗留）

- 位置：`manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:214`、`:215`、`:217`、`:218`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:204`、`:205`、`:208`。对照 `manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:89` 与 `manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:213`。
- 原文短摘：`if decision.requires_human ... else: execute_with_effect_ledger(action)`；`if decision.requires_approval ... commit_idempotently(snapshot, decision.capability)`。
- 问题：正文明确有 `ALLOW`、`DENY`、审批与附约束放行，但代码只判断“是否要审批”。按字面实现，拒绝且无需审批也会进入 else/后续提交。底层函数可能另做拒绝检查，但本章没有把这列为前置条件，读者不能靠猜测隐藏实现补齐安全边界。这两段代码在 `3b658c6` 中已相同，不能归因于 9 月中文改写。
- 推荐修法：明确枚举拒绝、等待审批、附条件允许、允许和未知决定；仅后两种在约束落实、授权仍有效时执行。审批恢复时重新核对动作参数、资源版本与权限；未知决定默认不执行。教学代码要显式表现这条分支，不把它藏在“安全执行”函数名中。
- 交给运行代理：构造 `DENY + requires_human=false` / `DENY + requires_approval=false` 的策略结果，统计 executor/commit 调用次数；验收应为零。再测过期授权与未落实附加约束。此处未运行，也未声称供应商产品实际越权。

### R02 — P1：提交成功不等于任务完成（待运行验证；状态机问题）

- 位置：`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:20`、`:168`、`:169`、`:209`。
- 原文短摘：前文说“外部提交可能成功而业务目标实际未达到”，状态图却写 `effect confirmed → VERIFIED_COMPLETE`。
- 问题：若合同只要求创建某记录，回读确认记录可能足够；若合同要求“部署后服务健康”或“目标方收到消息”，提交 API 的成功只是一项中间事实。图中没有区分提交前检查和提交后检查；`reconcile_and_attest` 的命名也未明确承担后置业务验收。
- 推荐替代段落：

> 提交确认只说明目标系统接受了动作。若完成契约还包含提交后的业务条件，系统应回读目标状态并执行这些检查，通过后才标记任务完成。无法确认提交结果时进入对账；已确认提交但业务检查失败时记录“已提交、未完成”，按契约补偿或升级。对于只要求保存交付物的任务，持久化确认本身可以是最后一项检查。

- 交给运行代理：模拟“发布接口返回成功，但健康检查失败”，要求最终状态不是 `VERIFIED_COMPLETE`，并保留已发生副作用。另测只读报告任务无需强造业务提交。

### R03 — P1：补偿不是安全重试的充分条件（原理文字问题）

- 位置：`manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:112`、`:117`、`:118`；同章 `:135`、`:137`。
- 原文短摘：“安全重试要求工具满足以下至少一种语义”包含“有明确 compensation，可撤销重复效果”和“转人工 reconciliation”。
- 问题：前项把补偿能力写成允许盲重试的替代条件，后项则根本不是工具的重试语义。重复扣款即使能退款，也可能暂时占用资金、触发通知或产生费用；原动作状态不明时，补偿对象和次数也不一定可判定。这与同章“先向下游查询”的论证冲突。
- 推荐替代段落：

> 自动重试写动作前，应确认操作天然幂等、下游按同一幂等键去重，或能用可靠证据确认前次未生效且不再可能生效。若结果未知，先对账；无法确认时暂停并交由有权主体处理。补偿用于处理已确认发生的错误效果，本身也可能失败，不能据此把未知提交当作可以直接重放。

- 验收建议：运行代理用“已扣款、回执丢失、补偿服务不可用”的故障组合检查恢复策略；本报告只提出反例与应有行为。

### R04 — P1：机械守恒被误当成技术含义守恒（已用本地差异确认）

- 位置：`research/audits/plain_language_rewrite_20260910.md:7`、`:13`、`:25`、`:27`–`:31`、`:53`；`publishing/scripts/check_plain_language_integrity.py:58`–`:65`。
- 原文短摘：“同时保留原有技术含义、事实边界”；门禁实际为 `headings_exact`、`urls_exact`、`code_blocks_exact`、`numbers_exact` 和字数比例。
- 问题：这些检查不比较术语含义、谓词、否定、模态、范围、因果、适用条件、指标分母和角色权限。长句统计甚至只输出、不参与 `passed`。新增中文解释恰好能在数字、链接和代码块全不变时改变语义。R05、R06、R11、R09 的实际差异已推翻“机械检查通过足以证明含义不变”的推论；并不否认机械检查本身的用途。
- 推荐替代审计结论：

> 本轮机器检查确认标题、链接、代码块、部分数字表达及篇幅满足既定守恒条件。这些结果不覆盖自然语言的语义等价性，不能单独证明技术含义和事实边界不变。经人工逐项复核术语、限定语、指标、授权条件和跨章一致性后，才可另行给出语义审校结论。已发现的误释及其修订应作为公开勘误保留。

- 推荐门禁：机械守恒与语义复核分别出结果；对“首次译名、新增全称、可能/必须、候选/样本、分开/分库”等差异要求逐条核对；参考伪代码即便没有改动，也不能沿用未做运行验证的安全结论。详见后面的专项审计表。

### R05 — P2：ACI 被扩展为三个不同概念（9 月改写新增）

- 位置：`manuscript/parts/01_history.md:3`；`manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:3`；正确对照 `manuscript/chapters/03_interface_is_part_of_intelligence.md:48`、`manuscript/appendices/C_glossary.md:17`。
- 原文短摘：导言为“Agent-Context Interface”；第八章为“Agent Control Interface，Agent 控制接口”；第三章与术语表为“Agent-Computer Interface”。
- 问题：这不是中英文风格差异，而是给同一缩写引入“上下文接口”“控制接口”“计算环境接口”三种对象。`3b658c6` 的导言和第八章只写 ACI，两种错误全称都由本轮改写新增。
- 推荐替换：导言统一为“第三章说明 ACI（Agent-Computer Interface，即 Agent 与计算环境之间的动作和观察接口）为何会影响任务表现”；第八章可直接用“设计良好的 ACI 能让模型更容易观察环境、执行动作并根据错误反馈修正操作”。术语表保留一处权威全称，不在后文另造展开。

### R06 — P2：validation set 被改成用于选择样本（9 月改写新增）

- 位置：`manuscript/chapters/12_observability_traces_and_eval_operations.md:104`；旧稿 `3b658c6` 同文件 `:104`。
- 原文短摘：现稿“用于选样本的是 validation set”；旧稿“用于选择候选的是 validation set”。
- 问题：评测集在这里用于比较候选模型、Harness 或配置；“选样本”把被选择的对象换成了评测样本，容易引导读者根据结果挑选试题，污染比较口径。不是简化同义表达。
- 推荐替代段落：

> 开发集用于调试和查错；验证集用于比较并选择候选模型、Harness 或配置；密封测试集只在预定时机做独立终测。已经频繁用于调试的题目可以进入回归集，但不能继续作为未接触样本证明泛化。集合应分开管理、声明用途并记录访问，不能按候选表现临时挑题。


### R07 — P2：held-out 与 sealed test 混为同义词，反馈边界不清

- 位置：`manuscript/appendices/C_glossary.md:33`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:198`、`:200`、`:212`、`:258`；`manuscript/chapters/12_observability_traces_and_eval_operations.md:104`、`:106`。
- 原文短摘：“Held-out / sealed test”；“回传‘最小诊断’……又不泄露 held-out 内容”。
- 问题：标签不可见不等于没有信息泄漏。多轮通过/失败、最小诊断及由此选择变体，都可能把隐藏检查变成优化信号。第十章允许边查边修，附录却将 held-out 和只在预定时机使用的 sealed test 合并；读者无法知道哪一组允许修复反馈，哪一组承担最终独立结论。
- 推荐替代段落：

> 本书将“保留集”作为未直接用于生成或训练的宽泛称呼；其中，用于比较候选或提供修复诊断的集合承担验证集职责，不能同时充当独立终测。密封测试集由独立服务在预定时机评估，反馈粒度和访问次数事先固定。最小诊断可以减少泄漏，但不能保证零泄漏；一旦用于自适应修复，应记录暴露并重新界定该集合的用途。

- 修法：附录拆成两个条目；完成门注明修复用的 checks 属于哪一集。运行代理只需验证访问/反馈和退役规则，不把“隐藏标签未直接返回”当作独立性证明。

### R08 — P2：证据门禁覆盖范围小于章程，历史材料未达到已声明的核验程度

- 位置：`research/planning/00_research_charter.md:30`–`:35`；`research/evidence/README.md:3`、`:7`、`:11`；`research/evidence/claims_v2.jsonl:1`–`:25`；`research/evidence/sources.jsonl:36`、`:37`、`:41`、`:43`、`:55`、`:61`。
- 原文短摘：章程要求“所有事实主张进入 claim ledger”；README 则称当前账本为“最小可信账本”，来源有“37 条已核验、47 条未核验”。
- 问题：25/25 承重 claim 的 `supported` 不是全部正文事实均获支持。BabyAGI 原始循环、Aider repository map、CodeAct、MCP 授权和 Verified 建集数字在正文承担论证，但相应来源登记仍标 `unverified`，访问日期及版本为空；其中 BabyAGI 使用可变化的 `main` 链接。另，第十二章全部显式外链都指向同一篇厂商文章，未满足章程要求的两类来源。已有本地 evidence 摘要不能替代可复查版本和原始定位。
- 正文实例：`manuscript/chapters/02_the_autonomous_agent_boom.md:12`、`:43`–`:58`；`manuscript/chapters/03_interface_is_part_of_intelligence.md:11`、`:34`、`:75`；`manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:102`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:82`。
- 推荐修法：由主代理复核并固定这些来源的版本/日期、关键原句与具体 claim，不再只检查 URL 是否已登记。对历史章节补一个具体版本中的失败轨迹或代码位置；若暂时无法核验，标为待核验材料并收回“全事实覆盖”的总括结论。不要求本轮审阅者联网。
- 推荐替代审计表述：“已核验最小账本中的 25 条承重主张；其余正文事实与 47 条未核验来源尚需逐条处置，不能由该通过率推断全书事实已完成核验。”

### R09 — P2：责任边界被写成不成立的线性依赖和物理部署要求

- 位置：`manuscript/chapters/05_system_model_and_responsibility_boundaries.md:120`、`:124`、`:188`–`:196`；`manuscript/appendices/C_glossary.md:14`–`:16`；`manuscript/chapters/12_observability_traces_and_eval_operations.md:19`。
- 原文短摘：“每层只依赖下层稳定契约”；图中 Governance 是 L3、Execution 是 L2；“日志、审计和模型上下文要分库分层保存”。
- 问题：执行层需要在提交时校验治理层发放的授权并记录运行事实；若严格按图只能依赖下层，就需要调用上层或私自复制治理语义。控制面“不进入每一步”也没有区分策略管理与请求时策略执行。附录又出现证据面和进化面，却没有说明它们与三平面是包含关系还是另一视角。第十二章把旧稿“分开保存”改成“分库”，把逻辑隔离加强成物理部署要求，与第五章允许单体实现的边界不符。
- 推荐替代段落：

> 这六项是职责分区，不是严格的自上而下调用栈。策略由控制面管理，执行请求通过受信任的授权接口取得并校验受限凭证；状态与证据通过统一接口记录。早期可以在同一进程或数据库中实现，但必须分清访问权限、数据所有权和保留规则。是否拆成独立服务或数据库，应由隔离、规模和故障恢复要求决定。

- 修法：给六层图补授权、状态和审计交互；区分 policy administration 与 enforcement；明确证据面/进化面是后文进一步拆分的职责，而非悄然替换原三平面。

### R10 — P2：结束一轮、停止执行和完成任务没有贯穿统一

- 位置：`manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:13`、`:24`–`:47`、`:51`、`:62`、`:249`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:5`；`manuscript/parts/02_principles.md:5`。
- 原文短摘：“一个可运行的 turn 至少包含这些状态”；“停止流程必须经过外部完成契约”；“没有独立的 CompletionContract……就无法评价”。
- 问题：一次 turn 可以因提问、拒绝或取消正常结束，而业务任务仍在等待；第六章图却直接用 `VERIFYING → COMPLETED` 作为 turn 的完整状态。结尾把所有停止都接到完成门，会使紧急取消也像必须等业务验收。完成契约是一种推荐的显式实现，不是所有评价活动成立的逻辑必要条件；简短问答也不需要独立验收服务。
- 推荐替代段落：

> 运行状态与任务状态应分别记录。一轮交互可以结束、取消或等待用户，此时任务仍可能未完成；用户取消时应立即停止继续派发，并处理在途动作，而不等待成功验收。只有要将任务标记为已完成时，才按该任务的验收规则检查。简单问答可以使用轻量规则，高风险写入则需要独立检查与提交授权。显式完成契约有助于把这些规则版本化。

- 修法：状态图标注 `turn_status` 与 `task_status` 的关系，给“提问结束一轮但任务待回复”“用户取消但已有副作用待对账”各一个示例。

### R11 — P2：指标和 trial 的新增译注改变了比较对象

- 位置：`manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:219`；`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:294`。
- 原文短摘：“tool selection precision/recall（工具选择召回率）”；“multi trial baseline（多次单模型试跑基线）”。
- 问题：第一处漏掉 precision，读者可能只优化多选工具的召回而忽视误选；第二处把重复试跑额外限定成“单模型”，混淆单 Agent、模型种类和试跑次数三个不同维度。两处括号都是 9 月新增，旧稿英文中没有这些含义。
- 推荐替换：“工具选择的精确率与召回率：选中的工具有多少合适，应该选中的工具有多少被选中”；“用同成本的单 Agent 基线和重复试跑结果评估多 Agent 的增量收益，并分别说明每组使用的模型及预算”。补一个必须同时记录误选与漏选的工具路由例子即可，不需要整章增加术语表。

### R12 — P2：把两次方差解释结果写成份额拆分，并过早推出原因

- 位置：`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:29`–`:31`；本地证据 `research/evidence/evidence.jsonl:65`、`research/evidence/claims_v2.jsonl:24`。
- 原文短摘：“共同解释了 95% 的性能方差，其中 token 使用本身占 80%”；“这支持了……主要在扩大……预算”。
- 问题：本地保存的原文是三因素解释 95%、token 单项解释 80%；“其中……占”容易读成联合结果的可加份额。方差解释来自观察分析，不能直接证明 token 增加导致收益，也不能证明多 Agent 的结构没有独立作用。原文后面提出同预算对照是正确方向，应让它限制前面的结论。
- 推荐替代段落：

> Anthropic 报告，在其研究系统分析中，三项因素联合解释了 95% 的性能方差，单独使用 token 用量也能解释 80%。这提示计算预算可能是重要关联因素，但不能把两项结果当作可相加的贡献份额，也不能据此确定因果。要判断多 Agent 是否优于单 Agent，还需在相同任务、模型和预算下做对照。厂商报告的约 4 倍和 15 倍 token 用量仅描述其特定系统，不是通用成本比例。

- 来源边界：此处依据仓库已有证据文字做语义核对，未重新访问厂商文章；具体实验口径由主代理核查。

### R13 — P2：确定性机制、签名与“证明正确”被放在同一强度阶梯

- 位置：`manuscript/chapters/05_system_model_and_responsibility_boundaries.md:150`–`:165`；`manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:26`–`:34`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:5`、`:44`。
- 原文短摘：“系统保证不会违反”；“证明：external verification / signed audit”；“任务完成是环境中的客观事实”。
- 问题：访问控制、隔离、结果验证、审计签名解决不同问题，不能按一个从弱到强的序列互相替代。签名可以证明某主体签过某记录，不能证明业务事实正确；DLP 也不是完整的保密证明。开放式建议、文体任务的完成还包含人的判断，不全是目标环境可回读事实。第十章第 44 行关于检查不完备的限定更准确，应成为全书统一口径。
- 推荐替代段落：

> 提示帮助模型理解约束；授权和隔离在给定配置与威胁模型下限制它能触及的资源；独立验证检查已定义的验收条件；签名和审计帮助确认记录的来源与完整性。这几种机制需要组合使用。它们各有覆盖范围，不能由“记录签过名”推断“任务目标已正确实现”。对含主观判断的任务，完成契约还应指定有权作出判断的人或服务。

### R14 — P2：权限衰减与专业角色授权、组合风险之间缺少边界

- 位置：`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:112`、`:200`–`:204`、`:239`；`manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:145`–`:146`。
- 原文短摘：“子能力应是父能力的子集”；“这样……也能防止多个低风险动作叠加成高风险结果”。
- 问题：子集规则适用于父主体向下转授自己的权限；专业 worker 若通过独立身份获得域内授权，manager 本身未必应拥有该数据的直接读取权，需要区分执行权和委派权。缩权及父级复核也不会自动防止组合泄漏，第十一章第 204 行恰好给出了反例。
- 推荐替代段落：

> 父 Agent 转授自身权限时，子 Agent 的资源范围、动作与期限不得超出允许转授的范围。若专家角色需要独立授权，应由可信策略服务核验其身份、任务用途和调用者的委派权，不能让模型自行授予。单次授权之外，还要检查子结果的来源、可传递范围和后续用途；否则分别合法的读取与公开写入仍可能组合成泄漏。

- 修法：给 delegation contract 标明 `execution authority` 与 `delegation authority` 的区别；删去第九章“这样就能防止组合风险”的充分保证。

### R15 — P2：多数投票的必要条件被写错

- 位置：`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:172`。
- 原文短摘：“多数票只有在错误近似独立时才有价值”。
- 问题：近似独立不是多数票产生收益的必要条件；存在相关错误时仍可能有收益。反过来，独立也不足以保证投票有益，还要考虑单个判断者能力、类别分布和聚合规则。这句话容易把“错误相关性值得测量”写成错误的统计定理。
- 推荐替换：

> 多数票是否有益，取决于各判断者的准确性、错误相关性和聚合规则。共用模型与上下文可能让错误高度相关，削弱投票收益。应在相同预算下实测聚合结果，不能把人数或意见一致直接当作独立证据。

- 验证边界：未做数值实验；若运行代理补演示，应同时覆盖相关但有增益、独立但低质量，以及完全重复输出三种情形。

### R16 — P2：单 Agent 的轨迹也可能是部分有序图

- 位置：`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:208`；对照 `manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:190` 与 `manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:171`。
- 原文短摘：“单 Agent 的 trace（追踪）是序列，multi Agent 的 trace 是部分有序图”。
- 问题：单 Agent 可以并行调用工具、接收取消或异步任务事件；书中前文已经允许这些行为。因此是并发与依赖决定事件偏序，并非 Agent 个数。若按此句实现，单 Agent 系统可能丢失工具之间的真实因果关系。
- 推荐替换：“纯串行循环的轨迹可以显示为序列；只要出现并行工具、异步任务或多 Agent 协作，就应记录部分有序的因果图。展示顺序可以线性化，但不能用显示顺序代替执行依赖。”

### R17 — P2：“真实事件”没有可追溯实跑来源，ID 被误说成证明

- 位置：`manuscript/chapters/12_observability_traces_and_eval_operations.md:66`、`:68`、`:72`–`:88`、`:92`。
- 原文短摘：“一条可关联的真实事件”；`artifact:sha256:11ad...`；“policy id 证明当时依赖的规则”。
- 问题：这里实际提供的是含截断 hash 的最小示例，没有对应 run 记录或可定位原始日志，不能据此宣称真实实跑。一个 ID 只是关联键；只有它指向受保护的决定记录，并绑定动作、输入、策略版本与执行结果，才构成可复查证据。不能让“有形似生产的 JSON”替代证据。
- 推荐替换：标题改为“一条工具完成事件的示例”；补“以下为教学示意，ID 与哈希已简化，不是本书实跑记录”。将解释改为“policy id 用于关联当时的策略决定；要证明执行遵循该决定，还应保留受保护的决定记录及其与动作、执行身份和资源版本的绑定”。
- 若本轮案例实跑产生真实事件，由运行代理另提供运行入口、日期、环境、完整原始记录位置和脱敏说明，再考虑升级为“真实事件”。

### R18 — P2：压缩后的不变量不能只在压缩前检查

- 位置：`manuscript/chapters/07_context_cache_compaction_and_memory.md:115`、`:209`、`:234`。
- 原文短摘：“压缩前要跑 continuity checks：目标是否保持、权限是否保持……”；“压缩前后复跑同一任务是否行为保持”。
- 问题：压缩前只能提取基线，不能证明尚未生成的摘要保留了目标与引用；第 234 行要求前后连续性测试更准确。另外旧稿要求从压缩前后两个状态执行“同一后续任务”，现稿变成“复跑同一任务”，可能误导为从头重做，漏掉任务中途恢复缺陷。
- 推荐替代段落：

> 压缩前从权威任务状态提取必须保留的目标、权限、未完成项和证据引用；压缩后逐项对照新上下文并检查引用可读取，失败则回退或重建。行为测试应从同一个中间检查点分叉，让未压缩与压缩后的上下文继续执行相同后续步骤，观察差异，而不是把整个任务从头重跑。

- 验证交接：由运行代理验证“摘要漏掉一项审批限制”“引用失效”“原始状态保留但模型看不到”的中途恢复样例。

### R19 — P2：缓存优化被写成统一的正确更新方法

- 位置：`manuscript/chapters/07_context_cache_compaction_and_memory.md:82`、`:95`；对照同章 `:45`。
- 原文短摘：“正确做法是保留旧前缀并新增状态更新”。
- 问题：这适合能被追加状态明确替代的内容，却不是所有变更的通用规则。旧高优先级指令、工具 schema 或执行环境发生不兼容变化时，仅追加一条较低优先级消息，可能让模型继续遵循旧说明；策略层拦住越权也不能消除模型反复提出无效动作的问题。前文已正确强调先解决冲突，应保留该例外。
- 推荐替换：“对支持追加更新且语义不冲突的状态，优先追加，以复用稳定前缀。若旧规则、工具 schema 或环境说明已失效，应重建相应上下文并接受缓存失效。权限变更始终在执行层即时生效，不能等待模型理解更新。”

### R20 — P2：历史类比被写成未经证明的直接谱系

- 位置：`manuscript/chapters/01_from_control_loop_to_agent_runtime.md:87`、`:111`–`:113`、`:209`–`:213`；`manuscript/chapters/02_the_autonomous_agent_boom.md:78`–`:103`；`manuscript/parts/01_history.md:3`。
- 原文短摘：“分层的早期来源”；“与 Contract Net……一脉相承”；“这就是 Harness 成为独立层的原因”。
- 问题：BDI 和 Contract Net 能提供结构上的解释框架，但本地引用没有展示现代 coding agent 直接沿用这些设计的传承证据。“发现相似物”与“证明来源”需要不同证据。第二章对抽象泄漏、调试反弹及 runtime 转向的叙述也缺少具体版本中的故障实例，读起来像从今天原则倒推历史必然性。
- 推荐替代段落：

> BDI 提供了一个有用的比较框架：观察、目标与执行承诺应分别维护。现代 Harness 出现了相似的状态管理问题，但本章没有证据证明其设计直接继承自 BDI。Contract Net 的松耦合协商也有助于理解今天的委派成本；worktree 和容器解决的是共享可变状态与执行隔离，两者不能仅凭结构相似就认定为同一条技术传承。

- 修法：按“原工作解决什么—原文/代码能证明什么—今天的类比—类比在哪里失效”组织每段；给 AutoGPT/BabyAGI/LangChain 各选一个固定版本的具体机制与失败条件，由主代理补证。不必把所有历史节点都扩成产品说明书。

### R21 — P2：模型能力上限、系统表现与乘法隐喻混在一起

- 位置：`manuscript/chapters/00_preface.md:14`–`:22`；`manuscript/chapters/03_interface_is_part_of_intelligence.md:7`；`manuscript/chapters/05_system_model_and_responsibility_boundaries.md:1`、`:12`。
- 原文短摘：“全书的核心公式”；“模型能力不是系统能力的固定上限”；“优秀 Harness 不能让模型解决超出其理解边界的问题”。
- 问题：第五章明确“不是精确数学关系”，因此不应把乘式本身误报成计算错误；问题在首次出现的序言没有该限定。“裸模型单次调用成绩”“带工具和搜索的系统表现”“模型理论能力边界”也未区分，导致第三章看似取消上限，第五章又声明不可超越。读者无法知道哪个说法可用实验检验。
- 推荐替代段落：

> 同一模型在单次问答中的成绩，不能直接当作带工具、环境反馈和多次尝试的系统上限。Harness 可以改变可利用的信息和计算过程，但是否改善某类任务仍需实测。本书用乘法提醒读者各环节会互相制约，不把四项视为可直接相乘的量，也不据此宣称存在已测得的通用能力上界。

- 修法：序言即加入“设计隐喻，非定量公式”；第五章标题中的 Agent 与正文 Agent System Capability、术语表中 Agent 的角色定义对齐。定量问题仅列入运行验证清单，不进行本次审阅者的计算实验。

### R22 — P2：第一章的“四层”并非研究章程的四层进化

- 位置：`manuscript/chapters/01_from_control_loop_to_agent_runtime.md:183`–`:190`；`research/planning/00_research_charter.md:5`；`manuscript/chapters/00_preface.md:12`；`manuscript/appendices/D_concept_index.md:34`。
- 原文短摘：第一章表列“模型权重、运行时记忆、外部技能、当前任务轨迹”，随后称“后面的‘进化篇’将沿着这四层展开”；章程却是“任务内、跨任务、Harness 和模型四层”。
- 问题：前者按成果保存在哪里分类，后者按优化对象与生命周期分类，不是一一对应。技能既可能是跨任务经验资产，也可能是 Harness 配置的一部分，不能用相同“四层”名称暗示已经统一。
- 推荐替代段落：

> 这张表先按能力保存在哪里区分路线，并不等同于后文的四层进化模型。后文按优化对象与生命周期展开：当前任务中的尝试与修复属于任务内进化；经验和技能的跨任务复用属于跨任务进化；上下文、工具和工作流的配置变更属于 Harness 进化；权重更新属于模型进化。同一技能的生成、使用与发布可能跨越这些层次，需要分别治理。

### R23 — P2 / P3：章节衔接和重复没有因改写而解决

- P2 位置：`manuscript/chapters/03_interface_is_part_of_intelligence.md:150`。原文短摘：“下一篇将不再按时间讲故事”。问题：第三章后仍有第四章，提前宣布进入原理篇。推荐替换：“下一章转向真实仓库与产品运行时，再由原理篇系统展开这些责任。”
- P3 位置：`manuscript/chapters/04_the_coding_agent_turn.md:7` 与 `:19`。原文短摘：两次连续解释“软件任务并非天然简单”，两次列依赖、隐藏约束、并发、外部服务和测试。Git 差异显示 9 月把后段内容又添进了前段。修法：第 7 行只保留仓库提供的四种条件，第 19 行保留一次限制与反馈闭环的解释。
- P2 结构位置：`manuscript/chapters/04_the_coding_agent_turn.md:35`–`:43` 与 `manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:80`–`:88` 重述 Verified 老化；`manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:154`–`:168` 与第七章 `:97`–`:117` 重列压缩保护项；第一章 `:97`–`:109`、第二章 `:142`–`:151` 与第十一章多处重复委派收益与成本。
- 推荐修法：历史篇只保留转折和一项代表证据；第六章讲压缩发生在哪个状态转移，第七章拥有压缩内容与质量测试的完整说明；第十章拥有 benchmark 治理的完整流程。保留跨章短提醒，但每次提醒应增加一个不同的设计问题，而不再重复同一清单。

### R24 — P2：仍是翻译与清单堆叠，缺少读者可跟随的因果演示

- 位置：`manuscript/chapters/01_from_control_loop_to_agent_runtime.md:163`；`manuscript/chapters/07_context_cache_compaction_and_memory.md:225`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:262`；`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:294`；`manuscript/chapters/12_observability_traces_and_eval_operations.md:7`。
- 原文短摘：“Context compiler 是读模型”；“一个可投入生产的完成子系统至少应具备……”；一段内“第一……第十……”；第十二章一句列出十余种带英文括号的事件。
- 问题：“读模型”容易被读成模型调用，在这里实为从状态生成的只读投影；加一个中文括号没有说明对象怎样工作。多项清单仍不交代先做哪项、为什么需要、失败后怎样变更状态。章程要求适用条件、替代方案和可验证指标，但多数建议停留在“必须有”。短句增加和字数增加都不能证明已经可教。
- 推荐替代段落（第七章）：

> 上下文编译器只读取任务状态，生成给模型看的视图。模型说“测试通过”时，它不能据此改写任务数据库；只有测试工具的结果经校验后，系统才能记录这项事实。后续摘要可以删掉详细日志，但必须保留测试结果和原始日志的位置。

- 推荐替代段落（完成门教学示例）：

> 假设 Agent 修复一个仓库问题。它先提交补丁；验收服务在固定提交和依赖版本上运行测试，再把结果绑定到补丁哈希。若 Agent 随后又改了文件，旧测试不能继续为新补丁作证。若测试通过但合并权限已过期，任务应等待重新授权。读者可以据此检查：当前证据证明的是哪个版本，下一步是否仍有权执行。

- 修法：第六至十二章共用同一个任务、相同 ID 与术语，每章只增加一个故障和一项可观察状态变化；把长清单降为示例后的核对表。第十一章第 294 行拆成“何时拆分、如何隔离、如何合并验证”三组，保留全部技术要求。新示例在实际跑过前必须标注教学示例。

### R25 — P2：全书术语表没有真正控制新增中文译名

- 位置：`manuscript/parts/02_principles.md:5`；`manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:213`；`manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:5`、`:22`；`manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:85`、`:172`、`:208`；`manuscript/chapters/12_observability_traces_and_eval_operations.md:7`；`manuscript/appendices/C_glossary.md:5`、`:15`、`:20`–`:26`、`:32`。
- 原文短摘：CompletionContract 译成“完成定义”；Harness 突然译成“托管执行系统”；artifact 在“产物／制品／工件”之间切换；effect 为“副作用／效果／外部作用”；capability 仅译“能力”；provenance 为“来源／血缘”。
- 问题：部分同义表达只是编辑一致性问题，但“完成定义”省略合同中的权限、预算和变更权；capability 的授权含义与模型能力混在一起；model policy 与 authorization policy 也都叫“策略”。这些恰好是本书强调应区分的边界。第十章还大量给 Agent、SWE-bench 这类普通名词加反引号，与邻章风格断裂。
- 推荐统一口径：

| 英文 | 正文推荐用语 | 需要保留的区别 |
|---|---|---|
| Harness | 首次解释为“组织模型、工具与环境执行任务的运行和治理机制”，之后保留 Harness | 不暗示必须由外部服务托管 |
| CompletionContract | 完成契约 | 包含验收、证据、权限、预算、变更和停止规则 |
| Artifact | 产物；交付语境可用“交付物” | 与已发生的外部副作用区分 |
| Effect / Effect Ledger | 外部副作用／副作用账本 | “副作用”包括预期外部状态变更，不只指坏结果 |
| Capability lease | 临时授权／能力租约（首次解释） | 不等于模型解题能力 |
| Model policy / authorization policy | 决策策略／授权策略 | 区分概率决策与允许执行的边界 |
| Provenance / lineage | 来源记录／版本沿袭关系 | 前者回答证据来自哪里，后者回答版本怎样演变 |
| Verifier | 验证器 | 与可主观评分的 judge、组织审批人分别定义 |

- 修法：先让正文和附录采用同一表，再审校所有新括号；只给代码符号、字段和字面值加反引号。不要为了汉化而把不同技术概念压成同一个中文名词。

### R26 — P3：概念索引的定位和完整性未跟随教学路径

- 位置：`manuscript/appendices/D_concept_index.md:8`、`:10`–`:13`、`:21`；对照 `manuscript/chapters/02_the_autonomous_agent_boom.md:73`、`manuscript/chapters/05_system_model_and_responsibility_boundaries.md:99`–`:116`、`manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:7`–`:20`。
- 原文短摘：Agent / Workflow 的“首次集中定义”为“第二、五章”。
- 问题：第二章使用 workflow 并举固定工作流的例子，没有集中定义其与 Agent 的本体边界；完整关系在第五章。索引又没有纳入第六章为幂等与归因专门定义的 Thread/Turn/Step/Attempt，读者查关键执行单位反而找不到。
- 修法：将 Agent / Workflow 的集中定义定位到第五章，第二章列作先行例子；添加 Thread/Turn/Step/Attempt → 第六章。将“首次出现”“首次集中定义”“主要展开”分别维护，避免以出现英文词就算完成定义。表格其他未超出本次范围的后篇定位不在此作未读先判。

### R27 — P2：架构评审表的判定规则仍有不明确之处

- 位置：`manuscript/appendices/B_architecture_review_checklist.md:3`、`:28`、`:46`、`:64`–`:68`；`manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:218`–`:224`。
- 原文短摘：“任何 R3/R4 动作只要关键项不通过”；“有幂等键”；“kill/restart 演练无状态丢失和重复 effect”；“回滚任一项不通过时，直接阻断”。
- 问题：表未标出哪些是哪些风险等级的关键项；列出的行为有的需要业务幂等，有的只能对账或人工处置。“回滚”也没有区分撤回软件版本和逆转外部动作。已发送邮件、已执行资金转移等动作未必能回滚，不能既列为 R3/R4 示例，又用未定义的“回滚通过”作统一必要条件。零丢失/零重复需要说明故障模型与判定窗口，不能被理解为有限测试已证明无限可靠。R0“读取公开资料，记录即可”也忽略了载入不可信内容后对后续工具的影响。
- 推荐修法：每项补 `适用风险/关键项标记/故障与重试范围/验收证据/不适用理由/责任人`。副作用项允许明确的“下游幂等”“可靠对账后决定”“禁止自动重放”策略；不可逆动作要求事前授权、限额、提交回读、后续处置，而不是伪称可回滚。版本发布另列回滚演练，不与业务补偿混用。
- 推荐替代判据：

> 在列明的崩溃点、并发重试次数和下游行为条件下，演练未出现违反任务不变量的重复提交；未知结果均进入对账或人工处置。对不可逆动作，检查预防、限额、回读和事故处置证据；对可回滚的软件发布，另检查版本回退证据。评审结论只在此范围内有效。

### R28 — P3：几处可直接修正的措辞与重复

| 精确位置 | 原文短摘 | 问题与建议 |
|---|---|---|
| `manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:135` | “它不确定提交状态” | 主语指向模糊、中文不通顺。改为“这时提交结果未知，必须回读下游状态或进入人工对账”。 |
| `manuscript/chapters/07_context_cache_compaction_and_memory.md:5` | 枚举六类材料后称“五类内容” | 与随后按存储职责列的五类不是同一分类。改为“这些材料的信任等级、生命周期和更新权限不同”，再引出后文五类。 |
| `manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:262` | “visible 与 held-out 棋离” | 错字应为“隔离”；结合 R07 明确哪类检查用于修复、哪类用于终测。 |
| `manuscript/appendices/D_concept_index.md:3`、`:42` | 两次要求同步索引、术语表和机器契约 | 首尾重复，保留一次即可。 |
| `manuscript/chapters/12_observability_traces_and_eval_operations.md:100` | “可却被采样策略系统性删除” | 去掉多余的“可”，改为“却被采样策略系统性删除”。 |

## 专项审计：数字／链接相同是否意味着技术含义不变

不成立。以下不是虚构的测试句，而是 `git diff 3b658c6 a1ed264` 中已发生的变化。旧审计称此批改写 41/41 通过机械检查；本次只静态阅读脚本和核对差异，没有重新运行该脚本，也没有据此替其他代理作运行验收。

| 当前精确位置 | `3b658c6` 旧表达 | `a1ed264` 新表达 | 改变了什么；为什么机械检查抓不到 |
|---|---|---|---|
| `manuscript/parts/01_history.md:3` | “把 ACI 确立为能力的一部分” | 新增“ACI（Agent-Context Interface）” | 首次展开变成错误概念；无数字、URL 或代码块变化。 |
| `manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:3` | “一个设计良好的 ACI” | 新增“Agent Control Interface，Agent 控制接口” | 同一术语又产生另一错误全称；守恒脚本没有术语字典或语义比较。 |
| `manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:219` | `tool selection precision/recall` | 新增“工具选择召回率” | 两个指标被译成一个，英文仍在，因此数字和 URL 完全可以相同。 |
| `manuscript/chapters/12_observability_traces_and_eval_operations.md:104` | “用于选择候选的是 validation set” | “用于选样本的是 validation set” | 选择对象改变，评测流程随之改变；这是动宾语义，不在机械检查范围内。 |
| `manuscript/chapters/12_observability_traces_and_eval_operations.md:19` | “日志、审计和模型上下文应分开保存” | “要分库分层保存” | 从逻辑隔离加强到物理存储拓扑要求；字数变化很小。 |
| `manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:294` | `multi trial baseline` | 新增“多次单模型试跑基线” | 给重复试跑增加了模型数量限制，混淆比较轴。 |
| `manuscript/chapters/07_context_cache_compaction_and_memory.md:209` | “压缩前后执行同一后续任务” | “压缩前后复跑同一任务” | 从同一检查点继续，变成可能从头重跑；检查对象的生命周期改变。 |
| `manuscript/chapters/07_context_cache_compaction_and_memory.md:192` | “都采用……按需发现的方向” | “都采用……按需发现” | 删除方向性限定，使表述更像确定实现事实；是否有证据支撑需主代理复核，不能由链接相同认定等价。 |

旧审计还有两个具体边界：

1. `publishing/scripts/check_plain_language_integrity.py:17` 采用正则抽取部分数字表达，并不保留数字所修饰的对象、总体、条件和因果关系。即使每个数字都被抽到了，也仍可能把“样本中的比例”改成“总体中的比例”。第十一章 95%/80% 的问题说明，数值不变时，关系词仍会改变解释。
2. 同脚本 `:31`–`:41` 的长句统计以标点和换行切分，并排除表格等内容；`:58`–`:65` 的通过判定没有长句或术语准确性条件。因此“长句减少”“字数增长”至多是表达变化指标，不能证明读者理解成本降低，更不能证明技术正确。

建议新的审校单元不是“文件数字清单”，而是“主张及其限定”。每次改写至少核对：主体、对象、条件、量词、否定、可能/必须、比较基线、版本日期、数字分母、证据类别、授权主体及状态转移。对于新中文译注，逐项回到本书术语表和原始来源。对于代码，即使逐字未改，也应保留“未运行验证”的状态，而不是自动继承“可用”结论。

## 公式与伪代码：交给运行代理的验证清单

本节只记录假设、待验证问题和期望行为；没有在本次审阅中运行或计算。R01/R02 是主要静态疑点，其他项是需要防止教学示例被误用的边界，并不一概判为已证实错误。

| 编号 | 优先级 / 位置 | 需要验证的条件 | 合格判据或处置 |
|---|---|---|---|
| V01 | P1；第六章 `:214`–`:218`；第十章 `:204`–`:209` | DENY 无审批、未知决定、附条件允许但约束未落实；审批后过期或资源变化 | executor/commit 不被调用；若底层函数负责拒绝，必须把该前置条件写回教学契约，不能用补好的实现证明原文已完整。 |
| V02 | P1；第十章 `:168`–`:173` | 提交成功但业务检查失败；提交结果未知；无需外部业务提交的只读任务 | 分别进入“已提交未完成”、对账、轻量完成路径，不把提交回执统一映射为完成。 |
| V03 | P2，适用条件核验；第十章 `:94`–`:101` | `pass@k = 1-(1-p)^k` 和 `pass^k = p^k` 已有“独立近似”限定；进一步区分每任务固定 p、任务难度不同、相关试跑和有限样本估计 | 不把全任务平均 p 直接代入并当作真实集合指标；区分理想概率公式与有限 n 次试跑的经验估计。当前文本不足以据此判定公式本身错误。 |
| V04 | P2；第十一章 `:94`–`:109`、`:255`–`:279` | 契约字段 `allowed_tools/capability_scope` 与函数使用 `spec.tools/spec.resources` 的映射；`ttl=spec.deadline` 的相对时长/绝对时间；spawn 失败与取消时预算租约回收 | 运行前先显式声明字段转换和时间单位；验证权限不扩大、租约可释放、不遗留子进程。把适配假设与原文分开记录。 |
| V05 | P2；第十二章 `:98` | 轨迹完整率只以“已结束 run”为分母时，永久悬挂或崩溃后未记终止的 run 是否被漏掉；按生命周期合法删除的 artifact 如何处理 | 至少另报已创建、进行中、超时未闭合与已终止任务的对账，明确评估窗口及保留期；不能让缺失终止事件反而提高完整率。 |
| V06 | P2，非定量式边界；序言 `:17`、第五章 `:9`、第十一章 `:44`–`:55` | 系统能力乘式与 DelegationValue 被读者误当可直接代数计算 | 正文写清是设计启发式，变量没有共同量纲或测量定义，不能直接算收益、排序或得出概率保证。若需数值案例，另定义指标和实验，不能拿隐喻公式假装已验证。 |

额外交接：R03 的补偿/重试反例、R15 的投票边界和 R18 的压缩连续性可由运行代理纳入反例集。不能为了让测试通过，先在实现里补入原文没有的拒绝门、后置验收或原子租约，再把结果记作“原伪代码正确”。应报告原样解释、必要假设、失败轨迹和修订后的行为。

## 文体与可教学性的具体处置顺序

1. 先修含义：ACI、validation、precision/recall、trial、临时授权和完成契约，统一到术语表。不是先做全局英文替换。
2. 再修因果：按“原型带来什么—具体失败在哪里—需要新增哪条运行保证”压实历史；把“直接来源”改为有证据的谱系或明确的现代类比。
3. 原理篇保留共同任务：每章呈现一个正常分支与一个失败分支，让读者看到任务状态、授权和证据怎样变化。把清单放在已经解释过的机制后面。
4. 最后做中文编辑：删同章和相邻章的无增量重复；减少每个英文词重复加括号；给“读模型”“版本 witness”“高熵判断”解释实际对象和操作；拆长并列段而不删限定条件。
5. 复核时分开回答“更好读了吗”“意思变了吗”“技术论证有依据吗”“样例确实跑过了吗”。四项不能互相代签通过。

## 已检查但不应误报的问题

- 第五章第 12 行和第十一章第 55 行已注明概念公式不是精确数学关系；本报告不把没有量纲的隐喻当作已经算错的公式，问题是首次引入和使用边界不一致。
- 第十章第 84 行明确把 59.4% 限定在 138 个不稳定失败样本，未将其直接写成全部 Verified 任务的缺陷率；这一限定应保留。相关来源真实性由联网代理另核。
- 第三章第 111 行已明确 Event Stream 不等于严格事件溯源；第九章第 196 行、第十二章第 118 行也正确区分可观测证据与模型私有思维链。无需以“缺少内部推理”为由否定其审计设计。
- 第十章第 44、62 行承认测试与检查不完备；第十一章多处要求同成本比较、保留冲突和合并后重验。修订应把这些准确限定贯彻到相冲突的口号、图和伪代码，不是删掉现有反方边界。
- 本报告没有给全书泛泛评分，也没有把来源未核验写成“内容必假”，没有把静态伪代码疑点写成“已复现产品漏洞”。

## 完成记录

- 指定 19 个文件均已完整阅读；截断的首次工具输出已另行补读，不以搜索命中替代全文审阅。
- 逐文件矩阵、28 项编号发现、真实前后差异专项审计及 6 项公式/伪代码验证交接已写入本文件。
- 旧稿与新稿归因已区分：ACI、validation、precision/recall、trial 译注和分库要求是 9 月改写新增；两处授权伪代码的缺口早于该次改写。
- 仅写入本报告；其余修改、来源复核、运行验证与发布决策留给既定分工。

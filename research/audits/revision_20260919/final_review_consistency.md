# 合并稿跨章一致性与产品整合只读复审

审阅日期：2026-09-19。对象为并行修订中的工作树，不是已提交发布版。本文仅列交付时仍存在的问题；不重复上一轮已修问题，不把正在补齐的引用元数据算作稿件 Bug。

## 结论

发现 **7 项现存问题：1 项 P1、6 项 P2**。最需要先处理的是授权决定的字段与枚举未贯通：按正文与附录直接组合，合法决定可能被拒绝或无法读取。其余集中在验证反馈用途、委派权限例外、历史产品边界、两处统计口径和索引层号。

本次复审未发现仍将“版本粘性高于紧急撤销”或“外部提交确认直接等于业务完成”作为跨章通用规则的明确残留。发布元数据的资料截面与管理层摘要也未继承上轮“体系闭合、全书无遗留”式总判定。下面只列需要继续改动的具体位置，不据此宣称全稿已无其他问题。

优先级口径：P1＝按书中统一契约直接组合会使关键执行流程失效；P2＝局部定义、适用条件或交叉引用不一致，会误导实现或测量。未发现本轮证据足以判定的 P0。

## FC01｜P1｜PolicyDecision 的字段和枚举在主循环、委派与附录之间断开

**现存位置：**

- [第9章:88](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:88>) 把附条件允许命名为 `ALLOW_WITH_CONSTRAINTS`。
- [第11章:267](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:267>) 使用 `decision.kind` 并接受 `ALLOW_WITH_CONSTRAINTS`；下一行也读取 `decision.kind`。
- 统一定义却是 [附录A:30](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/A_core_contracts_and_pseudocode.md:30>) 的 `decision` 字段，以及 [附录E:69](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:69>)、[附录E:72](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:72>) 的 `CONSTRAINED_ALLOW`。[第6章:230](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:230>) 和 [第10章:217](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:217>) 也使用这一套。

**为什么需要修：** 第11章没有声明返回另一种委派决定类型，也没有把它转换为附录契约的适配步骤。若策略服务按统一字段返回 `{decision: "ALLOW", ...}`，委派代码读取不到 `kind`；附条件允许又同时有枚举不匹配。取缺失字段会报错或得到未知值，具体依语言而定，但都不能据此启动已获准子任务。反向采用第9章枚举，则不在附录E允许集合中。这是本文作者契约的不一致，不是厂商接口差异。

**建议：** 统一为 `decision.decision` 与 `CONSTRAINED_ALLOW`，同步第9章及第11章两个分支；若确实需要独立的 `DelegationDecision`，应显式定义并提供映射，不能隐式假定相同。加一项跨章契约核对：规范化 ALLOW 可启动，附条件允许在约束落实后可启动，DENY/待批准/未知均不启动。

**只读核对：** 从附录E的 `$defs.PolicyDecision` 解析实际枚举；`ALLOW_WITH_CONSTRAINTS` 不在其中，规范对象没有 `kind`。本轮只比较字段与枚举，没有执行供应商或生产策略服务。

## FC02｜P2｜第6章仍把验证失败默认送回修复，缺少封存终测的用途分支

**现存位置：** [第6章:70](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:70>) 写“若验证失败，系统应把结构化差异……返还给 Agent”；[第6章:182](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:182>) 将 Verification failure 的默认策略写成进入 repair loop；[第6章:252](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:252>) 开始的完成检查分支到257行追加反馈，但没有说明 `repairable` 必须受数据用途约束。

**与何处不一致：** [第10章:236](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:236>)、[第12章:110](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/12_observability_traces_and_eval_operations.md:110>) 和 [第24章:61](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:61>) 已要求封存终测反馈不得继续用于同一批候选的修复与选择；需要诊断时要记录降级，并重建独立终测证据。

**为什么需要修：** 第6章是通用控制流入口，读者可能按“失败可修＋还有预算”直接回传终测差异，而忽略数据用途。这里不能断言实际实现必然泄漏，因为 helper 可以额外限制；问题是正文的无条件建议与后文条件规则不一致，且控制流未明确这一前提。

**建议：** 将70行和默认策略限定为开发检查或获准反馈的验证集；在 `repairable` 的定义中加入用途、实验族反馈余额和反馈可见主体。封存失败返回停止或独立重设计，不进入当前候选的诊断循环；经授权降级材料后开启新的确认流程。附录B若同步压缩该规则，应明确隔离既限制改写，也限制候选及其可执行代码读取终测资产，不能只写“不可改裁判”。

## FC03｜P2｜企业架构将权限衰减写成无条件规则，丢失独立专家授权的例外

**现存位置：** [第26章:65](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:65>)：“委派后的权限不得超过父任务权限，并继续按子任务收窄。”

**与何处不一致：** [第9章:132](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:132>)、[第11章:115](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:115>)、[附录B:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/B_architecture_review_checklist.md:41>) 和 [管理层摘要:51](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/executive_brief.md:51>) 区分了父主体转授与专家用独立身份取得执行权。前者需要衰减，后者由可信主体分别验证执行权、调用者委派权和用途。

**为什么需要修：** 按26章字面实现，调度者必须先拥有专家的全部域内权限才能委派；这与前文“manager 不必直接读取专家可访问数据”的隔离设计冲突。它可能逼迫团队给父代理扩大权限，或拒绝原本被独立授权的任务。

**建议：** 改为“转授父主体权限时不得超过其可转授范围；专家的独立执行权须由可信策略服务另行签发，并核验调用者委派权、用途及结果信息流”。无需给父模型同等直接读取权限。保持提交前撤销检查等后续规则不变。

## FC04｜P2｜历史篇仍把旧 OpenHands 结构写成未限定的现行架构与隔离保证

**现存位置：** [第3章:91](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:91>) 直接写“OpenHands 将系统拆成……Agent、Event Stream、Runtime”；[第3章:107](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:107>) 又写 Docker Runtime 的结构“把任意代码执行放入独立安全域”。

**与何处不一致：** [第17章:9](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:9>) 把 EventStream/Runtime/ActionExecutor 锚定为历史0.62.0结构；[第17章:17](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:17>) 说明当前SDK分离早已发生，[第17章:32](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:32>)、[第17章:55](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:55>) 则强调自管或容器模式本身不证明安全隔离。

**为什么需要修：** 放在历史篇足以提示年代，却仍未告诉读者此图对应哪个实现；后面的“独立安全域”又把部署与配置条件写成结构自带的保证。产品篇已精确拆开历史与当前模式，原理来源若不跟上，读者会把旧Runtime契约用于当前SDK，并高估隔离。

**建议：** 在91行或图前标“本节依据早期论文／历史0.62.0实现，当前SDK与Agent Server见第17章”，沿用书内已有固定证据即可，不需新研究。107行改为“提供分离执行环境的部署接口；实际隔离取决于容器、挂载、网络和凭证配置”，避免从客户端—服务器结构推出安全结论。

## FC05｜P2｜上下文指标把 precision 和 noise rate 合成了方向相反的一项

**现存位置：** [第7章:207](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/07_context_cache_compaction_and_memory.md:207>) 的表格将 `Precision/noise` 定义为“注入内容中无关比例”。

**与何处不一致：** [第8章:221](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/08_tools_aci_mcp_and_code_mode.md:221>) 将精确率解释为选中项中合适项的比例；[第21章:50](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:50>) 则以正确适用激活事件作 precision 分子。虽然测量对象不同，precision 的方向都应是“合适占全部”，无关比例是噪声率。

**为什么需要修：** 读者按表格把无关内容从20%优化到10%，如果仍称 precision，就会得到“精确率下降而质量改善”的反向指标。斜杠没有给出两者的换算或共同分母。

**建议：** 拆为“上下文精确率＝经独立标注的相关注入单元／全部注入单元”和“噪声率＝无关注入单元／全部注入单元”，并预定单元是片段、token还是证据项。只有采用同一单位且相关/无关完备互斥时，两者才互补；不要与事件级技能激活精度混算。

## FC06｜P2｜管理层摘要把失败与重试费用放到了“分母”

**现存位置：** [管理层摘要:75](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/executive_brief.md:75>)：“失败、未激活和重试的成本也不能从分母中悄悄消失。”

**与何处不一致：** [第19章:81](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:81>) 的单位可信完成成本是总费用／可信完成数；[第29章:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:59>) 更明确写“重试和失败消耗必须进入分子”。成功率的分母则是全部预分配合格任务或运行。

**为什么需要修：** 这不是费用是否遗漏的问题，而是将两个不同指标的单位混合：成本不能加入任务计数分母。摘要面向决策者，宜直接保留准确口径。

**建议替换：** “失败、未激活和无返回的合格试验保留在主要成功率分母；生成、验证、失败重试和人工处置费用全部计入成本分子。重试不增加独立样本数。”

## FC07｜P2｜概念索引仍使用已废弃的成熟度层号

**现存位置：** [附录D:43](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/D_concept_index.md:43>) 仍列“L0–L4 成熟度”。

**与何处不一致：** [第28章:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:11>) 起的表使用M0—M4，[第28章:17](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:17>) 明确说明改名是为了避免与19章L1—L4进化对象混淆。

**建议：** 索引改为“M0—M4 成熟度能力”，并保持“四层进化对象”另行索引。检查摘要、目录和检索标签是否还沿用旧成熟度字母，但无需为了统一把架构层或工具层的其他局部L编号一并改写。

## 资料截面、摘要与产品整合的核验边界

[book_structure.json:4](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/publishing/book_structure.json:4>) 的 `sourceCutoff` 当前为 `2026-09-19`；与 [序言:24](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/00_preface.md:24>) 的“原始截面＋本轮增量”说明，以及管理层摘要的日期相符。没有据此要求全书所有历史事实必须在9月新发布，也没有把尚未补齐的旧引用版次列为稿件缺陷。

管理层摘要目前区分候选验收、外部提交与业务完成，说明自管执行不等于全部数据本地化，限定新研究和本地fixture的证据范围，保留撤权优先以及统计不显著不等于非劣的界限。本次未见“全面闭合”“已验证生产可靠性”一类继承结论；摘要需改的是FC06所列现存口径错误。

产品篇已经按具体接入面比较，并声明没有统一实测排名。除FC04的历史篇落点外，本轮没有把未补元数据、单纯翻译同义词或不同厂商原生对象名当作新增稿件Bug。未重新审查负责进化章节的公式、状态机和论文本身，只引用其已定义边界作跨章对照。

## 阅读范围与只读核验

- 通读第0—18章、第25—29章、附录B/C/D、管理层摘要；检查 `publishing/book_structure.json` 的资料截面，并补读其他篇导言。为确认FC01，仅补读附录A/E相关契约；进化篇只作定向交叉引用。
- 问题依据是当前文件内容与具体段落，不继承旧评审“未解决”状态。部分读取输出截断后分段补读；产品长URL的显示省略不影响正文语义核对，未将来源元数据缺口加入问题表。
- 内存解析附录E并对比PolicyDecision字段/枚举；没有执行会写报告或出版产物的检查脚本，没有进行Schema全套回归、供应商调用或论文复现。
- 29个重点文件和发布元数据的有序“相对路径:SHA-256”列表，用换行连接且无末尾换行，整体摘要为 `182ee0d9e42b5be9d0160f05fe3dbf65f4a65b264b7dcecf9f2cedc2f8703495`。工作树仍可能被主代理后续修改；问题应按这里的文字和定位确认，不能把本报告当作之后版本的自动结论。
- 唯一新增文件是本报告。没有编辑正文、ledger或其他审计记录，没有提交，没有联网。

## Recheck｜2026-09-19｜仅复核 FC01—FC07 修订

本节追加在初始报告之后。上文的问题描述、优先级、定位与首次快照全部保留，作为发现记录；它们不再代表本节所审修订后的未解决清单。

**结论：7/7 项文稿修订通过针对性静态复核。** 本轮仅检查主代理对 FC01—FC07 的对应修改及必要的契约对照，没有展开新一轮泛审，也没有把新引用入账进度列为问题。

| 编号 | 修订后落点 | Recheck 结论 |
|---|---|---|
| FC01 | [第9章:88](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/09_permissions_sandbox_credentials_and_supply_chain.md:88>)；[第11章:267](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/11_multi_agent_delegation_and_collaboration_topologies.md:267>)；[附录E:72](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:72>) | 通过。第9章枚举已统一为 `CONSTRAINED_ALLOW`，第11章判断与返回均读取 `decision.decision`，与第6、10章及附录A/E一致；约束落实仍在启动子任务之前。原字段及枚举错配已消除。 |
| FC02 | [第6章:70](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:70>)、[第6章:182](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:182>)、[第6章:255](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:255>)、[第6章:260](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:260>)；[第10章:204](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:204>)；[附录A:98](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/A_core_contracts_and_pseudocode.md:98>) | 通过。文字与默认策略已按数据用途分流；三处修复入口均先检查 `feedback_allowed`。第6章明确其核对数据用途、实验族反馈余额和接收主体，封存终测固定为否；降级材料后另建独立终测证据。这里确认文稿与控制流意图一致，不代替字段及负例单测。 |
| FC03 | [第26章:65](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:65>) | 通过。父权限转授与专家独立执行身份已分开；后者由可信策略服务签发，并核对委派权、用途和结果信息流，不赋予父模型对专家全部数据的读取权。 |
| FC04 | [第3章:91](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:91>)、[第3章:107](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:107>) | 通过。旧图明确属于早期论文与历史0.62.0实现，当前SDK/Agent Server转引第17章；Docker执行分离改为有部署前提的能力，不再由客户端—服务器结构直接推出安全域保证。未新增外部事实核验。 |
| FC05 | [第7章:207](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/07_context_cache_compaction_and_memory.md:207>)、[第7章:216](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/07_context_cache_compaction_and_memory.md:216>) | 通过。相关比例与无关比例已拆成 precision 和 noise rate；补明统计单元，以及两者互补所需的完备、互斥条件，并与技能激活事件精度区分。 |
| FC06 | [管理层摘要:75](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/executive_brief.md:75>) | 通过。失败、未激活及无返回的合格试验留在成功率分母；生成、验证、重试和人工费用进入成本分子；明确重试不增加独立样本数。 |
| FC07 | [附录D:43](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/D_concept_index.md:43>) | 通过。索引已改为“M0—M4 成熟度能力”，不再与L1—L4进化对象混用。 |

本轮检查限于上述文稿差异及11个相关源文件。没有执行单元测试、Schema全套回归或生产行为测试；字段定义与相应允许、拒绝、终测反馈负例由单测代理接续。本节不据静态复核宣布运行验证完成或全稿无其他问题。

追加前初始报告为16,764字节，SHA-256为 `66029eccd323146ff0506685716c8b9bb91fba8e1795d8eab440e936ffa93de0`；追加后按该字节前缀核验初始记录未变。本轮唯一写入是本报告末尾的recheck，未编辑正文、ledger或测试，未联网、未提交。

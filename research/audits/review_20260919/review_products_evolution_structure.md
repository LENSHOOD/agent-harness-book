# Harness 小书：产品、进化、实践与全书结构独立审阅

审阅日期：2026-09-19。审阅快照：Git HEAD `a1ed264462d9b61c260c1dc417243303bfc60b66`。本报告只评价本地材料，不代表完成了产品最新事实或论文原文的网络复核。

## 结论与范围

书稿已经有清楚的工程立场：运行时提出候选，外部系统负责授权、验证和提交；产品篇也主动限制了厂商指标的外推。这些是应该保留的优点。但“体系闭合、工程可落地、表述边界明确”的旧结论过满。当前仍有会影响实验结论、数据保密和实现正确性的漏洞，建议先修订本报告的 P1 项，再称为可照做的参考设计。

已逐行完整阅读用户指定的 25 个文件：第 13—30 章、第三至第五篇导言、研究章程、两份旧审核和 25 条 claims_v2 记录。第 1—11 章仅用于全书字数统计、目录结构和相关段落交叉核对；没有把它们计为本次完整内容审阅。为核对接口和术语，补读附录 A、C、E 及第 12 章，并抽查本地 evidence、校验脚本。全程离线，未使用浏览器、未调用产品、未运行构建或会写其他报告的旧审计程序；仅用 apply_patch 写本文件。

方法借用了 deep-research 的逐主张核对、证据边界和反向质疑，但按本次授权限定为本地文稿审阅。没有把“supported”字段当作原文复核结果，也没有为了符合技能模板生成额外文件。工作区引用的 RTK.md 在当前目录、逐级父目录及书稿文件清单中未找到，因此未臆造其中规则。

优先级：P1＝会误导核心结论、控制边界或照做实现，下一轮定稿前必须处理；P2＝限制可复核性、可执行性或结构与表达质量，应在编辑轮处理；P3＝轻微文字问题，本报告不单独堆列。没有发现足以在本次离线文稿审阅中判为 P0 的事项。下面的问题按确定错误、实现缺口与待外部复核分别说明，不把缺少证据直接判成事实为假。

## 最重要的十项

| 顺序 | 编号 / 优先级 | 关键问题 | 建议处理 |
|---|---|---|---|
| 1 | R01 / P1 | 零观测违规、非劣与显著性缺少可计算判据 | 给出估计对象、独立样本单位、差值区间、非劣界和多重选择规则 |
| 2 | R02 / P1 | 基础设施重试及未激活 trial 的计分边界不一致 | 分开端到端结果与机制诊断，保留全部分配样本及重试成本 |
| 3 | R03 / P1 | 四层数据隔离缺少跨实验反馈预算和统一污染传播规则 | 将开发、选型、封存测试、线上反馈分域；测试使用后不能无限复用 |
| 4 | R04 / P1 | 消融“证明必要条件”，2×2 单元格被称为主效应 | 改为条件效应、差分与交互估计，保留不确定性 |
| 5 | R05 / P1 | 数据案例过滤小群体后仍要求分组总额对平；20 人阈值被当成匿名性检查 | 拆开内部全量对账与披露聚合，增加组合查询风险边界 |
| 6 | R06 / P1 | 修复案例补丁命令漏未跟踪文件，展示的检查未跑在封存产物上 | 给出候选封存、干净环境应用和冻结验证的完整序列 |
| 7 | R07 / P1 | SDD 反例的状态改动与预期失败不相符 | 分别构造越界修改、改账单与继续入队三个独立负例 |
| 8 | R08 / P1 | 版本粘性与紧急撤销冲突，未定义撤销的优先级 | 冻结可复现输入，同时对每次动作重验最新撤销状态 |
| 9 | R09 / P1 | 25 条承重 claim 的机器通过被放大为全书闭合 | 公布覆盖缺口，撤回“无 P1/P2 遗留”作为当前质量结论的用法 |
| 10 | R19 / P1 | 参考架构 SLO 将候选验证通过当成业务完成 | 按合同区分产物交付与外部提交，并把回读确认纳入完成终点 |

共发现 28 项：10 项 P1、18 项 P2。字数审核错误列为 R10/P2：当前去 fence 为 67,636 字，进化篇为 14,279 字，占 21.112%，达到章程比例；旧审核的数值与口径仍须更正。

## 字数与结构实测

### 统计口径

为能与旧审核比较，中文字符定义固定为 Unicode U+3400—U+9FFF，每个字符计 1；不计英文、数字、标点和空格。这是“中文字符数”，不是分词词数，也不是中英文混排页面的全部可见字数。计入标题、表格及链接中文标签；不移除这些内容。

“去 fence”使用旧检查器同类表达式 `r"```.*?```"`、DOTALL，移除三反引号围栏及内容。当前源稿代码围栏均采用这一形式。统计范围是 manuscript/chapters、parts、appendices 内 41 个 Markdown 源文件，不重复计算 site、合订稿、参考文献、研究记录和本报告。篇章占比的分子只含该篇章节，导言单列。

| 范围 | 含 fence 中文字符 | 去 fence 中文字符 | 去 fence / 全书 67,636 |
|---|---:|---:|---:|
| 序 | 391 | 391 | 0.578% |
| 历史：1—4 章 | 10,671 | 10,299 | 15.227% |
| 原理：5—12 章 | 23,079 | 22,318 | 32.997% |
| 产品：13—18 章 | 7,265 | 7,265 | 10.741% |
| 进化：19—24 章 | 14,424 | 14,279 | 21.112% |
| 实践：25—30 章 | 8,348 | 8,333 | 12.320% |
| 五篇导言 | 1,077 | 1,077 | 1.592% |
| 五个附录 | 3,674 | 3,674 | 5.432% |
| 合计 | **68,929** | **67,636** | **100%** |

纯 1—30 章、不含序/导言/附录的去 fence 分母为 62,494，进化篇占 22.849%。把第四篇导言也算进进化篇、分母仍取全部 41 文件时，为 14,485 / 67,636＝21.416%。三个口径都满足章程“约 20%—25%”，不可据此再要求为了达标注水。

旧审核 [research/audits/quality_audit.md:12](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:12>) 写“去除 fenced code 后……68,929”；[research/audits/quality_audit.md:13](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:13>) 写“13,558……20.949%”。前者其实是含 fence 数，后者不是当前进化篇数，而且 13,558 / 68,929＝19.670%，并非 20.949%。实际差额为 1,293 个 fence 内中文字符。旧审核声明适用的 `04ddae644751d1abff63a5ac931744b3fd68f27a` 与当前 HEAD，按上述口径结果完全相同，不能把错误解释为后来正文改变。

作为混排体量补充，41 文件非空白 Unicode 字符（仍包含 Markdown 标记、英文、数字、URL）为含 fence 149,563、去 fence 118,675；它们也不能叫“中文字数”。第 25 章仅有 1,487 个去 fence 中文字符，却有 12 个代码块、135 行围栏内部内容；连同围栏行占 159 / 246＝64.63%。第 27 章围栏及内部内容占 61 / 119＝51.26%。所以实践篇不宜只按中文数量判短，但应核查大量示例是否真正连通。

### 指定文件逐项覆盖矩阵

下表每个文件均已全文读取。章节的两个数依次为含 fence / 去 fence 中文字符；“claim”只计账本 chapter 字段的挂接数量，不代表逐句事实覆盖。第 18、25—30 章未挂账本条目，不等于它们所有设计建议都必须有事实引文。

| 文件定位 | 中文字符 | claim | 本轮重点及问题号 |
|---|---:|---:|---|
| [manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:1>) | 1,335 / 1,335 | 2 | SDK/CLI 边界、84% 限定、合成配置；R11、R12 |
| [manuscript/chapters/14_openai_codex_protocolized_agent_core.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/14_openai_codex_protocolized_agent_core.md:1>) | 1,121 / 1,121 | 2 | 协议示意、状态映射、适配器责任；R11、R12 |
| [manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:1>) | 1,391 / 1,391 | 2 | A/B 定义、46.9% 边界、指标解释；R12、R13、R16 |
| [manuscript/chapters/16_deepseek_harness_composable_runtime.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/16_deepseek_harness_composable_runtime.md:1>) | 1,292 / 1,292 | 2 | 可逆注册/业务副作用、preview 定位；R11、R12、R21 |
| [manuscript/chapters/17_openhands_agent_runtime_separation.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:1>) | 1,008 / 1,008 | 1 | Agent/Runtime 与隔离边界、重复讲解；R12、R21、R25 |
| [manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:1>) | 1,118 / 1,118 | 0 | 比较口径、配置公平性、六轴缺实测；R11、R12、R23 |
| [manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:1>) | 2,722 / 2,586 | 1 | 四层本体、H=0、因果措辞；R01、R04、R14 |
| [manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:1>) | 2,116 / 2,116 | 1 | 失败计分、搜索伪码、反馈隔离；R02、R03、R15 |
| [manuscript/chapters/21_cross_task_memory_skills_and_experience.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:1>) | 2,351 / 2,351 | 2 | L2 指标、状态机、撤销、经验复用；R03、R08、R16、R17 |
| [manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:1>) | 2,240 / 2,240 | 2 | 激活门、NLE 释义、风险表面；R01、R02、R13、R14 |
| [manuscript/chapters/23_model_evolution_from_trajectories.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:1>) | 2,014 / 2,014 | 1 | 2×2、训练数据、模型归因、删除；R03、R04、R14、R18 |
| [manuscript/chapters/24_governed_evolution_loop.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:1>) | 2,981 / 2,972 | 1 | 独立评价、重复使用测试、粘性、跨层阶梯；R01—R03、R08、R14、R16 |
| [manuscript/chapters/25_three_end_to_end_cases.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:1>) | 1,502 / 1,487 | 0 | 三例逐段检查；R02、R03、R05、R06、R24 |
| [manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:1>) | 1,313 / 1,313 | 0 | 六层到信任边界、完成 SLO；R08、R19—R21 |
| [manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:1>) | 1,410 / 1,410 | 0 | SDD 负例、验证执行范围、字段映射；R07、R24、R26 |
| [manuscript/chapters/28_maturity_model_and_build_vs_buy.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:1>) | 1,155 / 1,155 | 0 | 成熟度绝对化、分级与采购经济性；R22、R23、R26 |
| [manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:1>) | 1,617 / 1,617 | 0 | 阶段依赖、精确重建承诺与迁移成本；R08、R20、R23、R25 |
| [manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:1>) | 1,351 / 1,351 | 0 | 预测与必然判断、重复结论；R25—R27 |
| [manuscript/parts/03_products.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/parts/03_products.md:1>) | 197 / 197 | — | “同一组问题”和事实/推断区分的兑现；R11、R12 |
| [manuscript/parts/04_evolution.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/parts/04_evolution.md:1>) | 206 / 206 | — | 模板兑现、四层同一闭环的边界；R01—R04、R14 |
| [manuscript/parts/05_practice.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/parts/05_practice.md:1>) | 228 / 228 | — | “可落地方案”“机器可读实例”的承诺；R06、R07、R24 |
| [research/planning/00_research_charter.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:1>) | — | — | 6—10 万字、比例、证据与反方约束；R09、R10、R28 |
| [research/audits/quality_audit.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:1>) | — | — | 数值、通过结论、已知边界互相核对；R09、R10 |
| [research/audits/plain_language_rewrite_20260910.md:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/plain_language_rewrite_20260910.md:1>) | — | — | 可读性与技术语义守恒并非同一检查；R09、R10、R13、R26 |
| [research/evidence/claims_v2.jsonl:1](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/evidence/claims_v2.jsonl:1>) | — | 25 条 | 完整逐条阅读，挂章统计，支撑范围；R09、R13、R28 |

## 核心问题与具体改写

### R01｜P1｜统计门禁尚不能支撑“证明改得更好”

定位与短摘：[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:55](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:55>)，“H=0、关键切片非劣……U 的置信区间满足……门槛”；[manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:16>)，“显著改善”；[manuscript/chapters/24_governed_evolution_loop.md:22](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:22>)，“trial 数量……停止规则”；[manuscript/chapters/25_three_end_to_end_cases.md:208](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:208>)，“比较主要指标置信区间”。

问题不是完全没提统计，而是读者无法从这些字段算出可复核的晋级决定。需要的是候选相对基线的差值区间，不能只看 U 的区间；“没发现下降”不是非劣证明。多候选筛选、多切片和持续查看结果会改变错误发现概率。同一任务重复多次不能一概按独立任务处理。H=0 可以是观察到严重违规即拒绝的硬门，但不能推出真实违规率为零。

建议改写：“在预先定义的目标任务分布上，估计候选与基线的配对效用差 ΔU，并按任务或同源任务簇估计不确定性。主要指标下界须超过预注册的最小有意义增益；关键切片的非劣下界须高于 −δ。严重违规一经观察即拒绝；零观测违规只表明本样本未发现，须同时报告暴露次数与风险上界。多候选选择和提前停止采用预注册校正或独立确认集。”

补一张含任务数、每任务次数、效应尺度、最小增益、非劣界、置信水平、分组方法、选择/停止规则的实例表。作为纯数学示例，假设 240 次独立同分布二项暴露、零违规，则单侧 95% 上界为 1−0.05^(1/240)≈1.24%，不是 0；这不是对本书虚构实验的真实安全估计。成本指标在可信完成数为零时，应标为不可估计/无穷，而不能漏报候选。

### R02｜P1｜基础设施失败与激活门可能造成选择偏差

定位与短摘：[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:59>)，“retry outside candidate score”；[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:92](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:92>)，“不算候选能力”；[manuscript/chapters/24_governed_evolution_loop.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:41>)，“仍失败则保留在分母”；[manuscript/chapters/25_three_end_to_end_cases.md:202](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:202>)，“preflight(valid + activated)”；[manuscript/chapters/25_three_end_to_end_cases.md:218](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:218>)，“eligible_trials: 240, activated: 228”。

第 24、25 章保留失败分母的方向正确，但第 20 章的文字给出了无条件剔除的另一种读法。候选也可能引发资源耗尽、连接超时等“基础设施故障”，归类不能由候选自己决定。激活适合解释机制，不适合事后从主效用样本中剔除未激活任务；后者可能只剩下更容易任务。现有证据包不交代另外 12 个 trial 的结果。

建议改写：“主要报告按预先分配的全部合格任务计分，不因是否激活或是否成功返回而改变分母。独立控制面确认的外部故障可按同一预算规则重试，原始失败、重试结果和全部成本均保留。机制分析另报激活子集，并明确它不是总体因果效果。”

preflight 只应检查构建合法性和机制能否在专用探针中触发；正式运行的 activation 是诊断事件。样例补出 allocated、completed、unactivated、timeout、infrastructure、retried、exhausted，并说明每个任务/attempt 的关联与终态。更长重试预算不能隐含成为候选优势。

### R03｜P1｜“候选看不到测试”未闭合四层数据隔离

定位与短摘：[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:51](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:51>)，“不能把 held-out 测试全文交给 Agent”；[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:34](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:34>)，“held-out reuse eval”；[manuscript/chapters/23_model_evolution_from_trajectories.md:77](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:77>)，“split by task lineage”；[manuscript/chapters/24_governed_evolution_loop.md:39](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:39>)，“只读隔离”；[manuscript/chapters/25_three_end_to_end_cases.md:204](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:204>)，“one sealed-test evaluation”；补充 [manuscript/chapters/12_observability_traces_and_eval_operations.md:104](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/12_observability_traces_and_eval_operations.md:104>)、[manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:212](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:212>)。

书稿已讲数据分层、按 lineage 切分和最小诊断，不能再批成“完全没有隔离”。剩下的缺口是跨候选/跨轮次的访问预算与污染传播：每个候选各看一次同一个 sealed set，仍可能形成适应性过拟合；即使只返回 pass/fail，持续查询也能泄露选择信息。L1 修复产生的 lesson、L2 检索、L3 提案和 L4 训练如果沿用同一失败反馈，没有统一登记该资产已暴露给谁。“只读”防改写，不等于防读取；候选提交的可执行代码也须纳入威胁边界，不能只禁止生成 Agent 访问。

建议改写：“开发集允许诊断与修复；选择集用于候选比较并记录累计使用；封存测试服务只评估预先锁定的最终 bundle，返回预注册粒度结果。对同一封存集的再次使用必须登记实验族、反馈可见主体和累计查询预算；已用于调试或经验提炼的样本降级，派生 lesson/skill/训练样本继承暴露标签。”

进一步列清 evaluator、运行候选代码的沙箱、evolver、registry 与训练作业的读写矩阵。候选代码不应与评价资产共享可读取目录/凭证；结果回传也须控信息量。最终封存失败后的“再改再测”不能仍宣称同一批数据未参与选择。

### R04｜P1｜消融和 2×2 的因果解释不准确

定位与短摘：[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:86](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:86>)，“消融能证明某组件是必要条件”；[manuscript/chapters/23_model_evolution_from_trajectories.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:41>)、[manuscript/chapters/23_model_evolution_from_trajectories.md:42](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:42>) 将两个单元格命名为“Harness 主效应”“模型主效应”；[manuscript/chapters/23_model_evolution_from_trajectories.md:44](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:44>)，“只在新 Harness 上改善，说明存在交互”。

四个格子是四组结果，不是效应本身。只有在给定结果尺度上做差才能定义效应；单格“有显著性”与另格“无显著性”也不等于两格效应显著不同。消融后的变差可能包含移除造成的接口破坏、其他组件适配不足和交互，不能普遍证明必要条件。

建议改写：“消融估计在指定系统组合中移除组件造成的变化；结果只支持该条件下的贡献假设。设 y00、y01、y10、y11 分别为四个组合的效用，旧模型下 Harness 效应为 y01−y00，新模型下为 y11−y10；交互为 I=(y11−y10)−(y01−y00)。预先固定效用尺度，给出差值与交互的不确定性，不能把四格点估计直接写成因果结论。”

将表头改为“旧/新组合的观测结果”，另列效应公式。如果要报告平均主效应，再说明对两模型/两 Harness 的加权方式。模型×Harness 能说明测试组合的差异，不能证明所有可能 Harness 下都存在不可消除的模型内因。

### R05｜P1｜经营分析案例的抑制、对账与匿名性不相容

定位与短摘：[manuscript/chapters/25_three_end_to_end_cases.md:108](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:108>)，“k_anonymity_20”；[manuscript/chapters/25_three_end_to_end_cases.md:124](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:124>)，“HAVING COUNT(DISTINCT account_id) >= 20”；[manuscript/chapters/25_three_end_to_end_cases.md:129](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:129>)，“分组汇总与财务总额在允许误差内”；[manuscript/chapters/25_three_end_to_end_cases.md:154](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:154>)，“delta_cny: 0.02”。

HAVING 会删除真实收入，不是舍入误差。例如 A 组 20 人、收入 100，B 组 19 人、收入 95，披露结果只剩 100，财务全量是 195。本轮用 SQLite 内存表复算了这个反例，只验证分组抑制逻辑，没有冒充运行原 SQL 方言。正文没有声明 verifier 是否另拿全量汇总，读者按展示查询实现就无法得到所示对账结论。跨月份抑制还会改变可见人群，净收入变化可能只是披露范围变化。

另外，单个聚合单元人数≥20，只是最低人数阈值，不能单独证明 k 匿名或防止重叠查询差分泄露。两个均达阈值、仅相差一人的查询仍可暴露个体贡献。

建议改写：“内部授权验证器在同一快照上核对未抑制总额；对外报告只使用经过披露策略处理的聚合。总额、公开分组与受限残差分别存证；若残差或合并小组本身可反推敏感值，则不发布。月间对比同时报告披露覆盖变化，不能把被抑制数值当作零。”

把检查名改为 min_group_size_20，并明确它不是完整匿名化保证。补充查询组合审查、互补抑制/披露预算等适用控制，由组织选择具体方案。注明 SQL 所属方言与 snapshot/时区/退款空值语义；不需要把方言示意伪装成所有数据库通用 SQL。

### R06｜P1｜“可执行检查”没有验证同一份完整候选

定位与短摘：[manuscript/chapters/25_three_end_to_end_cases.md:51](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:51>)，“封存……clean checkout 重跑”；[manuscript/chapters/25_three_end_to_end_cases.md:54](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:54>)，“git diff --binary 8f31b6e”；[manuscript/chapters/25_three_end_to_end_cases.md:56](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:56>)，“pytest -q tests/time”；[manuscript/chapters/25_three_end_to_end_cases.md:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:59>)，“可执行检查”。

展示命令只从当前工作树导出 tracked diff，再在当前目录跑测试。它不会自动包含新增、尚未跟踪的测试或源文件，也没有展示在干净目录应用 sealed patch。读者可能在包含新增文件的脏工作树里通过测试，但交付补丁缺文件。补丁、changed_files 与验证结果之间没有在示例中完成绑定。另一个缺口是允许修改 tests/time，却没有明确 pass-to-pass 使用不可由候选删改的基线检查；禁止删除测试不等于禁止削弱断言。

建议改写：“以下片段仅说明补丁导出，不构成完成验证。控制面在专用候选工作区收集经审核的新文件、修改、删除、模式及二进制变化，拒绝越界路径；封存候选后，在固定基线的新工作区应用并核对树摘要，再运行版本固定的独立验收集。Agent 新增测试可作为证据补充，不能替换基线验收。”

补出从输入 revision 到 patch/tree hash、应用后 revision、验证器版本、命令及退出码的连续记录。教学示例可保留假 hash，但须明确占位与预期失败；不能把当前三条命令称作完整验证。此问题是静态命令语义审查，未执行任何工作区写入命令。

### R07｜P1｜SDD 反例不能推出“两项检查都失败”

定位与短摘：[manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:65](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:65>)，检查“取消状态不入队……账单表前后 hash”；[manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:86](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:86>)，“把取消状态改回 active，scope_guard 与 invoice_integrity 都失败”“提醒不再出现”。

把取消状态改成 active 并不自然导致提醒消失，反而可能继续入队。修改 src/billing/state.py 必定触发所列路径越界，但不必然改变账单表：是否调用该代码、是否产生持久化、表 hash 覆盖什么均未说明。用这个负例解释独立不变量会让读者实现错误测试。

建议换成三个独立负例：“候选只越界修改 src/billing/state.py，即使结果正确，scope_guard 也失败；候选为停止提醒而更新账单记录，invoice_integrity 失败；候选保留取消订阅的入队行为，sealed_cancelled_slice 失败。任一必需检查失败都不得合并。”

再明确 verifier 使用固定、临时测试数据库；database_write 禁止的是执行 Agent 的生产动作，不应误伤验证器准备 fixture。对账单 hash 要规定稳定排序、排除无关时间戳、比较对象和检查时点。提供一条通过轨迹与三条负例的实际/预期结果，才能支撑“完整实例”的标题。

### R08｜P1｜紧急撤销必须优先于版本粘性

定位与短摘：[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63>)，“让旧条目停止新的激活”；[manuscript/chapters/23_model_evolution_from_trajectories.md:99](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:99>)，“在途 task 的版本粘性”；[manuscript/chapters/24_governed_evolution_loop.md:45](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:45>)，“不能在长任务中途静默切换……memory snapshot”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:42](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:42>)，“capability lease……TTL”；[manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:59>)，“撤销旧凭证”。

这些设计各自合理，但组合后缺少优先级：长期任务已加载有害 skill、权限已被撤销时，不能因版本粘性继续使用旧授权；只停止“新的激活”也不会清除已在上下文里的危险指令。第 24 章提到按风险暂停/取消，是正确方向，但没有把紧急撤销定义为每次动作的强制约束。

建议改写：“版本粘性固定模型、工具视图和证据输入，用于复现；授权按动作执行时的有效租约和最新撤销状态重验。撤销优先于粘性。被撤销 skill/凭证关联的在途任务先暂停，禁止新增副作用，回收 capability，重建上下文或以新 attempt 恢复；已提交效果另行对账。”

补一条演练：长任务在候选生成后、commit 前收到 revoke，旧证据仍可审计，但提交必须拒绝。不能把“曾获批准”当作永久执行许可，也不能声称从 registry 删除一行便解决了所有在途污染。

### R09｜P1｜旧审计有局部边界说明，但总体判定越界

定位与短摘：[research/planning/00_research_charter.md:35](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:35>)，“所有事实主张进入 claim ledger”；[research/audits/quality_audit.md:24](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:24>)，“25/25……supported”；[research/audits/quality_audit.md:48](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:48>)，“无 P0/P1/P2 遗留”；[research/audits/quality_audit.md:52](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:52>)，“承重主张子集”；[research/audits/quality_audit.md:60](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:60>)，“体系闭合、工程可落地”；[research/audits/plain_language_rewrite_20260910.md:7](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/plain_language_rewrite_20260910.md:7>)，“保留原有技术含义”。

账本实际只有 25 条，13—17 章共 9 条，19—24 章共 8 条；产品安全和协议细节远多于这些条目。25/25 只能说明入账项的状态，不是全书事实的分母。旧审核第 52 行已坦白子集边界，这是优点，但不能同时据其宣称体系无遗漏。校验脚本 [publishing/scripts/audit_claim_ledger.py:140](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/publishing/scripts/audit_claim_ledger.py:140>)—[publishing/scripts/audit_claim_ledger.py:176](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/publishing/scripts/audit_claim_ledger.py:176>) 检查字段、引用与作者填写的 supported 状态，没有判断证据是否真正蕴含正文每个分句。

例如 C009（[research/evidence/claims_v2.jsonl:9](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/evidence/claims_v2.jsonl:9>)）包含“JSON-RPC-lite/JSONL”，绑定的本地证据 [research/evidence/evidence.jsonl:22](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/evidence/evidence.jsonl:22>) 只写 bidirectional JSON-RPC API 与 conversation primitives，未包含 lite/header/JSONL 细节。这不能证明正文事实错误，却能证明本地证据摘录不足以独立复核全部子主张。C021（[research/evidence/claims_v2.jsonl:21](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/evidence/claims_v2.jsonl:21>)）及 [research/evidence/evidence.jsonl:8](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/evidence/evidence.jsonl:8>) 均未提供 NLE 的中文展开，不能替正文新增解释背书。

建议将旧总判定改为：“构建、引用关系及已登记承重主张的形式检查通过；未完成逐句事实、统计方法与案例可执行性全覆盖。本轮仍有独立内容审阅待办。”按事实单元建立“正文位置—原子主张—原文摘录—版本—支撑程度”映射，允许 partial/待核验，不要为通过测试把所有状态写 supported。

本报告不把历史评审当时的结论全盘否定，也不声称已重新审过所有旧处置；它指出的是：现存材料中的具体漏项足以否定把旧“关闭”状态直接继承为当前质量保证。

### R10｜P2｜字数门通过，但旧审核的计算证据不成立

定位与短摘：[research/audits/quality_audit.md:12](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:12>)—[research/audits/quality_audit.md:13](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:13>)；[research/audits/plain_language_rewrite_20260910.md:18](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/plain_language_rewrite_20260910.md:18>)，“去 fenced code 后……68,929”；[publishing/scripts/check_plain_language_integrity.py:55](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/publishing/scripts/check_plain_language_integrity.py:55>)—[publishing/scripts/check_plain_language_integrity.py:56](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/publishing/scripts/check_plain_language_integrity.py:56>)。

检查器对 old/new 原文直接数中文，长度比检查并未先去 fence；只有长句检查另去 fence。因此旧报告把含 fence 的统计标成去 fence。当前 19—24 章也不是 13,558 字。上文已给出当前版与旧审计声明版本的双重复算，不是拿新稿数字推翻旧稿。

建议统一改为：“正文源 41 文件，含代码块 68,929 个中文字符，去代码块 67,636 个；19—24 章去代码块 14,279 个，占 21.112%。”同时声明是否计入导言/附录，并让审计数字由同一次计算导出。删除“超过 20.8% 因此不再贴线”这类先满足审稿阈值的叙述，保留章程约束与可复核公式即可。

### R11｜P2｜产品原生接口与作者平台契约没有逐例标清

定位与短摘：[manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:43](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:43>)—[manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:49](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:49>)，“runtime_profile……permission_mode: policy_mediated”；[manuscript/chapters/14_openai_codex_protocolized_agent_core.md:12](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/14_openai_codex_protocolized_agent_core.md:12>)—[manuscript/chapters/14_openai_codex_protocolized_agent_core.md:14](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/14_openai_codex_protocolized_agent_core.md:14>)，事件方法名示意；[manuscript/chapters/16_deepseek_harness_composable_runtime.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/16_deepseek_harness_composable_runtime.md:41>)，“签名的 bundle……导出……approval”；[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:54](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:54>)，POC report_slices。

第 13 章说“推荐”，因此不能指控它明确冒充官方配置；但在官方能力的连续叙述中紧接 YAML，没有写明字段属于谁、由谁解析，很容易被复制到原生产品配置里。第 14 章 text 示例也没注明名称是否精确协议标识。第 16 章把安全要求写得清楚，却未区分上游原生可提供与 adapter 需补建部分。

建议每个片段前标明“厂商原生、指定版本验证过的配置”或“本书自定义平台契约，不能直接交给厂商 CLI/SDK”。事件示意如非逐字协议，就改成自然语言事件或明确“方法名以该版本协议为准”。增加原生能力→平台映射→缺失能力→降级方式四列。

产品章节更新、当前方法名与接口是否存在由主代理联网核验；本报告不凭记忆更换方法名，也不推断 2026-08-27 之后的产品变化。

### R12｜P2｜架构重心和采用建议不应被整表归为“官方事实”

定位与短摘：[manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:22](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/13_claude_code_thin_loop_thick_runtime.md:22>)，“优势在于同时兼顾能力和成本”；[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:11>)，“组合成熟”；[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:15>)，“成本高”；[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:17](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:17>)，“表中的事实分别来自各产品官方资料”；[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:61](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:61>)，按产品直接分配采用场景；[manuscript/parts/03_products.md:3](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/parts/03_products.md:3>)，“五种架构重心”。

公开扩展面、协议或源代码可以支持架构描述，不能独自证明“成熟”“成本高”或普遍适配某类组织。这些是作者根据实现特性作的判断。subagent 节省父上下文不必然减少端到端 token、延迟或重复工作。六轴比较提出了测量方法，却没有逐产品的同条件结果，不能暗示已经实证比较优劣。

建议改写：“前两列为官方公开接口的归纳；优势、风险和采用场景为作者工程判断，尚未在同一任务矩阵下验证。子 Agent 可减少父会话上下文，但总成本取决于子任务数量、重复探索和结果交接。”把“成熟/成本高”改成可观测条件，例如扩展面数量、部署责任、缺失证据与必须补测的故障类型。

给每个产品保留一个独有失败轨迹或事件剖面；共通的 task≠session、外置 verifier 等原则集中在第 18 章引用即可。不要为填产品榜补造分数。

### R13｜P2｜中文解释引入新技术含义，旧完整性检查抓不到

定位与短摘：[manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:45](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:45>)，“NLE（非语言增强任务）”；[manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:11>)，“A/B 测试（同一任务对比两套配置）”；[manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:19](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:19>)，“成功率和 token 可能下降”；[research/audits/plain_language_rewrite_20260910.md:13](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/plain_language_rewrite_20260910.md:13>)，“只改表达”。

NLE 的该中文展开不在本地 C021 和对应证据中，现有材料无法支持；在主代理复核原文前应撤下括注，而不是用常识猜新的全称。A/B 测试也不等于同一任务配对重跑；随机分组对照和同任务配对设计需分别说明。句中“成功率和 token 可能下降”把成功率下降与 token 消耗下降并列为代价，指标方向含混。

建议分别改成：“在 NLE 环境上没有观察到改善（全称与任务性质按原文补证）”；“官方报告一项 A/B 对照实验；本章未复核随机化单位、配对方式和统计窗口”；“成功率可能下降，token 消耗可能上升，具体取舍需按模型和任务验证。”

同样避免将“确定性失败”解释为“可归因到明确错误”（[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:53](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:53>)）：可重复性与根因已知是两个维度。可改为“固定版本和输入下稳定复现的失败；其根因仍待诊断”。这些都说明标题、链接、数字不变不能保证技术语义不变。

### R14｜P2｜四层分类存在重叠，后文又把它写成升级阶梯

定位与短摘：[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:12](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:12>)，“skill、策略统计”；[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:13](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:13>)，“prompt……router”；[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:11>)，“检索权重”；[manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:5](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:5>)，“retriever……model profile”；[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:74](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:74>)，“不是线性升级阶梯”；[manuscript/chapters/24_governed_evolution_loop.md:111](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:111>)，“升级到下一层之前，必须证明”；[manuscript/chapters/23_model_evolution_from_trajectories.md:103](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:103>)，“只有……才……model-intrinsic”。

skill 本身可含 prompt 和脚本，检索权重既可能是经验统计也可能是 Harness 代码；model adapter 也可能指工具适配器或训练参数。若没有按发布单元划界，同一变化可以挂多个层并重复归因。第 24 章的“必须先证明上一层不行”又与第 19 章非阶梯立场冲突；有明确单位 schema 缺陷时，没有必要先发布 L2 文本补丁。

建议补一条分类规则：“按本次主要发布对象标记层级，跨对象改变标为复合变更；L2 发布条目/经验库快照，L3 发布检索与执行规则代码/配置，L4 发布可学习参数。检索数据与检索算法分别记录。”将“必须升级”改为“优先比较影响面、证据可得性和全生命周期成本，可直接选择最小有效机制”。

“model-intrinsic candidate”只能是已测范围内未解释的模型相关残差，不能写成排除了所有环境/接口方案；部署压缩和蒸馏也可能因成本目标值得做，不必等到缺陷绝对无法由 Harness 修复。

### R15｜P2｜任务内搜索伪代码缺少推进与预算消耗语义

定位与短摘：[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:31](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:31>)，“best-of-N……才构成搜索”；[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:36](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:36>)—[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:44](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:44>)，frontier/budget 循环；[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:64](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:64>)，ΔF；[manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:115](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/20_within_task_evolution_search_reflection_and_repair.md:115>)，“没有……预测……只是随机重试”。

伪代码只初始化 frontier，没有显式弹出节点、加入后继、扣除候选/验证预算、处理空候选与全部失败；若助手函数没有隐藏副作用，无法保证终止。抽象伪代码可以省实现，却不该省书中强调的安全停止条件。同一 prompt 的随机采样加外部选择器也是有效候选搜索，显式假设是提高可解释性的策略，不是定义上的必要条件。

建议改写：“每轮弹出一个待评估状态，执行前预留生成、执行和验证预算；把有增益的后继入队；达到预算、深度或无进展上限即返回已验证候选，若不存在则明确失败/升级。best-of-N 可以从相同提示随机采样；需测量候选相关性和选择器质量，不能假定增加 N 必然有效。”

ΔF 只用于固定检查集合的诊断进展；检查未运行、被跳过、换了版本或少量严重失败出现时不能靠计数改善晋级。建议同时记录 resolved/new/unexecuted，并保留检查严重度。

### R16｜P2｜经验指标混用条目、任务和激活事件，且误用 precision

定位与短摘：[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:43](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:43>)，“被检索且导致……占已启用条目的比例”；[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:81](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:81>)，“activation precision”；[manuscript/chapters/24_governed_evolution_loop.md:122](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:122>)，“activation precision 很低，因为大量任务根本看不到该字段”；[manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:13](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md:13>)，“context recall”。

“没有机会看到字段”反映资格/覆盖或召回问题，不足以说明激活精度低。正确激活 10 次、另有 90 次根本不适用时，precision 可以是 100%。有害检索率若分母取 registry 已启用条目数，闲置条目越多指标反而越好；“导致失败”又预设了尚未完成的因果归因。context recall 还需要独立标注“任务必需资料”，不能由 Agent 用自己读过的资料定义分母。

建议固定口径：“激活精度＝正确适用的激活事件 / 全部激活事件；激活召回＝正确激活的合格机会 / 全部合格机会；风险关联率＝激活后出现指定违规的任务 / 激活任务。”只有对照证据足够时才写 causal lift。第 24 章改成“候选在需要 timeout 字段的任务中触发不足”或“在无关任务中过度触发”，分别对应召回与精度；不可混写。

### R17｜P2｜Memory 状态链将隔离与正常晋级混成必经步骤

定位与短摘：[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:69](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:69>)，“candidate → quarantined → validated → active → deprecated → revoked/expired”；[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:71](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:71>)，“安全扫描可使其进入 quarantine”。

文字定义说 quarantined 表示发现问题而暂停，但箭头把所有候选都先判成异常，也把 revoked 放在 deprecated 之后，弱化了从 active 立即撤销的路径。批准 validated/active 的责任边界也没有明确。可以保留状态名，但不应以单链代表完整生命周期。

建议改成：“正常路径为 candidate→validated→active→deprecated；任何未终止状态遇到安全/来源问题可转 quarantined，修复并复验后才回到候选路径；任何已发布条目可立即 revoked，TTL 到期转 expired。deprecated 停止新激活，但 revoked 还须处理在途使用与派生项。”

给每条转换列触发者、证据、准入条件、是否影响在途任务。不同状态对应不同撤销强度，与 R08 的动作前重验连接。

### R18｜P2｜模型数据 lineage 没有完成删除与派生资产治理

定位与短摘：[manuscript/chapters/23_model_evolution_from_trajectories.md:23](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:23>)，“哪些步骤对成功有因果贡献”；[manuscript/chapters/23_model_evolution_from_trajectories.md:48](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:48>)，“为了满足删除……lineage”；[manuscript/chapters/23_model_evolution_from_trajectories.md:69](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:69>)，“占位引用”；[manuscript/chapters/23_model_evolution_from_trajectories.md:99](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:99>)，“保留候选轨迹”；[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63>)，物理清除与审计证明。

lineage 使受影响资产可定位，不等于已从训练后的权重、蒸馏模型、缓存和派生 skill 中删除信息。占位引用若可由训练执行器解引用，也不能当作脱敏完成。事故保留和最小留存可能冲突，需要指定访问与保留责任，而不是一律“继续保存”。

建议改写：“数据删除请求先沿 lineage 定位原始轨迹、训练快照、派生资产和已发布模型；分别执行物理清除、撤销使用、隔离或重新训练等经组织批准的处置，并记录仍无法消除的影响。可追踪不等于模型已遗忘。”这是一项工程边界说明，不替代法律结论。

“因果贡献”标签应改为“证据支持的贡献假设”，允许未知、环境故障和多重原因。仅凭最终成功或模型回看轨迹，无法给每个步骤补出可靠因果真值。

### R19｜P1｜参考架构把验证通过与业务完成重新混在一起

定位与短摘：[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:54](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:54>)，“Verifier……commit controller 再执行”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:64](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:64>)，“通过独立 completion gate 的任务/合格任务”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:70](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:70>)，“从合同冻结到完成门通过”；对照 [manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:169](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md:169>)，“effect confirmed → VERIFIED_COMPLETE”。

第 26 章先验证再提交的顺序正确，但可信完成率与完成时延停在提交之前，和第 10 章状态机不一致。对于发送、部署和付款类合同，候选通过检查后仍可能在提交时被拒绝、超时或未生效；此时记作完成会系统性高估成功。仅交付待审补丁的合同可在产物验收处终止，但必须由合同明定，不能泛化。

建议改写：“候选验证通过率与业务可信完成率分开统计。后者的终点由合同定义：仅交付产物时为验收通过；包含外部提交时，须完成授权重验、幂等提交与权威结果回读。完成时延使用同一个终点。”

证据包还应绑定实际提交的内容、目标和授权状态；审批后的产物或目标版本变化必须重新验证。将 R06 的代码案例、R07 的验收例子与第 10 章状态机串成同一条 trace，避免每章重新定义“完成”。

### R20｜P2｜SLO 的观察窗口、暴露量和不可重建结果未定义

定位与短摘：[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:65](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:65>)，“后续证伪/总完成”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:67](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:67>)，“恢复尝试”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:70](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:70>)，“P95 完成时延”；[manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:28](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:28>)，“任一完成任务都可从输入 revision 重建 artifact”；对照 [manuscript/chapters/12_observability_traces_and_eval_operations.md:56](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/12_observability_traces_and_eval_operations.md:56>)，“并不总能完整重放”。

刚完成的任务还没有足够时间暴露缺陷，不能与已观察一个月的任务直接混算错误完成率。只看恢复尝试会漏掉无法启动恢复的故障。P95 只取已完成任务会漏掉取消和超时。第三方模型/外部系统也未必能重放出逐字相同结果，第 29 章“任一……重建”比第 12 章自己的边界更绝对。

建议改写：“按任务完成批次和固定观察窗回标错误完成率，同时报尚未成熟样本；恢复分母从全部应恢复中断事件起算，另报未尝试原因；完成时延同时列成功、失败、超时与取消数量。”把“重建 artifact”拆为“取回封存产物并验证 hash”“重跑确定性检查”“在条件允许时重放生成过程”。这三种能力不能用一个 rebuild success 混计。

第 26 章表实际上先定义测量口径，尚未给目标、窗口和误差预算；标题可写“七类 SLI 与 SLO 设定方法”，保留当前不提供通用阈值的克制。

### R21｜P2｜三平面、双平面与六层参考架构缺少映射

定位与短摘：[manuscript/chapters/05_system_model_and_responsibility_boundaries.md:120](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/05_system_model_and_responsibility_boundaries.md:120>)，“三个逻辑平面”；[manuscript/chapters/24_governed_evolution_loop.md:10](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:10>)，“governance plane”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:11>)—[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:15>)，“Control/Evidence/Evolution Plane”；[manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:20](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:20>)，“同一进程”；[manuscript/appendices/C_glossary.md:16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/C_glossary.md:16>)，Evolution Plane 定义。

这些视角可以共存，并非自相矛盾；缺的是部件归属及信任矩阵。第 24 章把 evaluator、eval registry、release controller 放在候选不可写域，第 26 章又把 mutation/experiment/release 合画一层。按服务名部署的人可能把提案器与发布权授予同一个身份。OpenHands 的 Runtime 则是执行环境，Codex core/SDK 的 runtime 是决策运行组件，在多 Runtime 架构里尤其应区分。

建议增加映射表：“mutation worker 属演化功能层、候选信任域；experiment service/eval registry/release controller 属演化功能层、治理信任域；verifier 属证据功能层、独立评价信任域；vendor Agent 属运行层、受限执行主体。”声明层是职责，平面是管理/数据路径，信任域由身份、读写权限和发布权决定。

图上标出 proposal、signed release、raw evidence 与 release approval 的单向边界；每个产品 adapter 明确连接的是 Agent Runtime 还是 Execution Runtime。保留小团队可以同进程的建议，同时要求高风险场景用可验证的隔离机制实现逻辑边界。

### R22｜P2｜成熟度模型把产品复杂度和组织控制成熟度捆在一起

定位与短摘：[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:5](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:5>)，“只要……没有独立完成门……低成熟度”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:14](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:14>)，“多 runtime”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:19](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:19>)，“所有低等级硬条件”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:21](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:21>)，“敏感动作需批准”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:25](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:25>)，“供应商版本可固定”；对照 [manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:88](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/26_next_generation_enterprise_harness_architecture.md:88>)，单一低风险 Agent 的简化架构。

成熟度是有用的作者模型，但单一 Runtime、只读任务、托管不可固定版本服务，不应不加适用条件就与缺乏治理等价。人工批准和策略授权也应区分；“敏感动作需批准”未说明已授权的受限批量动作是否每次要人点按钮。第 19 章进化层 L1—L4 与本章成熟度 L0—L4 重名，会让“升级到 L4”含义不清。

建议改写：“本表是按任务风险使用的参考控制模型，不能作为供应商排名或组织认证。每项回答有证据、缺失或不适用；不适用须给出范围和等效控制。支持多个 Runtime 是可替换性的一种验证方式，不是成熟的必要条件。”对不能固定供应商版本的部署，要求变更检测、兼容门和自治范围限制，而不是假装已经固定。

将成熟度改记 M0—M4，进化层保留 L1—L4。安全、可靠性、完成验证、评测与替换能力可分别画像；受控进化是可选能力，不是所有只读/低风险系统必须追求的最高荣誉。

### R23｜P2｜Build-vs-Buy 的结论比经济证据走得远

定位与短摘：[manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:59>)，“多数企业……更稳妥”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:39](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:39>)，“只有当任务规模足够大……”；[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:41>)，“总成本模型应包含”；[manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:15>)，“兼容成本超预算”。

列成本项是好的开始，但没有统计窗口、任务量、固定成本摊销、双运行迁移成本和人工介入价值，读者仍不能算出什么时候该买、该建或保持现状。任务量小但现有产品完全不满足离线、延迟或特殊执行环境约束时，自建轻量运行时也可能是合理选择，所以“规模足够大”不应是绝对必要条件。

建议将采用结论改成适用假设：“在现成产品覆盖关键边界、接入和退出成本可控的前提下，优先购买高变化组件；关键约束没有可采购方案时，比较受限自研、确定性流程和人工方案。”

补一个明确标为虚构的 12 个月工作表示例：固定建设/迁移成本＋任务量×单次模型/计算/复核成本＋维护与风险损失；对任务量、介入比例、供应商价格变化做敏感性分析。退出条件写成预算/质量阈值的字段，而不是替所有企业指定一个数。

### R24｜P2｜案例、平台对象和附录 Schema 缺少显式转换

定位与短摘：[manuscript/chapters/25_three_end_to_end_cases.md:17](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:17>)，contract_id；[manuscript/chapters/25_three_end_to_end_cases.md:30](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/25_three_end_to_end_cases.md:30>)，budgets/wall_minutes；[manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:46](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:46>)，task 嵌套；[manuscript/appendices/E_machine_readable_contracts.md:14](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:14>)，Task required；[manuscript/appendices/E_machine_readable_contracts.md:28](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:28>)，wall_seconds；[manuscript/appendices/E_machine_readable_contracts.md:88](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/appendices/E_machine_readable_contracts.md:88>)，EvidencePackage schema_version。

第 25 章样例可解析为 JSON，但第一份对象直接当作附录 Task 输入，会缺 contract_version、risk、task_id、tenant，并出现 allowed_writes、budgets、contract_id、forbidden、task、workspace 等未允许字段。不能仅凭字段不同判它错：它可能本来就是业务合同 DTO。但既然全书许诺统一机器可读契约，就必须展示 DTO→Task/CompletionContract 的映射，而不能让读者猜。三个 EvidencePackage 也未展示如何映射到附录必填骨架。

建议在例子前写：“这是业务输入 DTO，不直接符合附录 E；下表给出编译后的平台对象。”统一 budget 名称和单位，明确 task_id/contract_version/attempt_id、输入 revision、验证器版本的来源。至少让一个规范、任务、候选和证据包实例沿同一套 schema_version 连贯走通。

本轮只进行了 JSON 解析与 required/additional 字段集合核对，没有声称运行完整 JSON Schema 验证器。7 个 JSON 围栏全部可解析，但这不证明语义或跨例兼容。附录 E 已标教学最小子集，应保留此限定。

### R25｜P2｜全书比例合格，重复占掉了应有的案例纵深

定位与短摘：[manuscript/chapters/03_interface_is_part_of_intelligence.md:89](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:89>)—[manuscript/chapters/03_interface_is_part_of_intelligence.md:111](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/03_interface_is_part_of_intelligence.md:111>) 与 [manuscript/chapters/17_openhands_agent_runtime_separation.md:5](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:5>)—[manuscript/chapters/17_openhands_agent_runtime_separation.md:21](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/17_openhands_agent_runtime_separation.md:21>)，OpenHands 分离及事件流不等于耐久；[manuscript/chapters/07_context_cache_compaction_and_memory.md:131](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/07_context_cache_compaction_and_memory.md:131>)—[manuscript/chapters/07_context_cache_compaction_and_memory.md:190](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/07_context_cache_compaction_and_memory.md:190>) 与 [manuscript/chapters/21_cross_task_memory_skills_and_experience.md:23](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:23>)—[manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/21_cross_task_memory_skills_and_experience.md:63>)，记忆类型、写入门和供应链；[manuscript/chapters/23_model_evolution_from_trajectories.md:35](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:35>) 与 [manuscript/chapters/23_model_evolution_from_trajectories.md:101](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/23_model_evolution_from_trajectories.md:101>)，两次完整讲 Model×Harness；[manuscript/chapters/24_governed_evolution_loop.md:71](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/24_governed_evolution_loop.md:71>)，“到此闭合”后又有七节；[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:45](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:45>)—[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:47](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:47>)，总结再次重复治理主张。

原则复现有教学价值，不能凡重复都删。但后半书反复申明“外置完成、版本化、独立评价、不可随意自改”，新增的实例结果却很少。进化六章共有 68 个二级小节，统一模板后又不断追加预算、边界、成本和末尾总结，阅读感像一组审稿补丁。实践篇代码体量大，却未提供任何一个有确定输入、输出和失败结果的完整教学闭环。

建议划清章节责任：第 3 章讲历史意义，第 17 章讲一次事件传输/取消失败；第 7 章讲存储与上下文，第 21 章讲条目如何被验证、发布和撤销；第 23 章只保留一次 2×2，另一节改为带数字结果的分析；第 24 章把“闭合”结句移到最后，并将重复的 7—13 节合入前面的治理流程。

优先把删掉的重复篇幅在同篇内置换为：一张 trial 表、一次晋级失败、一次 memory 撤销传播、一次 bundle 回滚。不要机械压缩进化篇到章程比例以下，也不需要为了“原创重点”继续堆概念。全书结构应从“每章都说原则”变成“原理定义、产品限定、进化测量、实践贯通”。

### R26｜P2｜“说人话”改写仍大量夹注，部分中文生硬

定位与短摘：[manuscript/chapters/28_maturity_model_and_build_vs_buy.md:35](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/28_maturity_model_and_build_vs_buy.md:35>)，“runtime（运行时）abstraction（抽象层）”；[manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:59](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md:59>)，一句内连续 attempt/runtime/evidence/artifact/effect 夹注；[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:98](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:98>)，“value-of-information（价值信息）”；[manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/19_evolution_is_an_engineering_control_loop.md:41>)，“held-out vault（留置金库）”；[manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:93](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/22_harness_evolution_prompts_tools_context_and_workflows.md:93>)，“effect ledger（影响账本）”；[research/audits/plain_language_rewrite_20260910.md:12](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/plain_language_rewrite_20260910.md:12>)，“第 25、26 章……足够清楚”。

同一段不断重复英文与中文括注，读者得两次解析同一意思。“留置金库”“价值信息”“材料性”并不比技术英文直白。artifact 被译为产物、成果、制品、工件；effect 又出现副作用、效果、效应、影响，读者难判断是不是不同对象。旧审核对 25、26 章“不必改”的判断也漏掉长串英文职责名和契约命名的不连贯。

可直接改写的三个句段：

> 原 runtime（运行时）abstraction（抽象层）改为“运行时适配层”。企业应掌握任务合同、身份映射、业务策略、领域验证、证据与发布权；这些能力可以采购实现，但配置、数据和替换权须由企业控制。

> 原第 29 章迁移演练段改为：“每个主要版本至少做一次退出演练：暂停新任务，导出未完成任务及已封存产物，确认外部动作的状态，再撤销旧凭证。替代运行时可重新执行或从受支持的检查点恢复，但不能重发已完成动作。”

> 原第 19 章相关解释改为：“先判断新增信息是否值得实验成本。记录基线损失、预期改善、实验费用和停止日期；风险或收益不清时，先做探索，不承诺生产收益。”

建立单一术语表：artifact＝产物，effect＝外部状态变更/副作用（按已定义含义），lineage＝来源与派生关系，held-out＝留出集，sealed test＝封存测试集；“held-out”和“sealed”也不要直接写成完全同义（见 R03）。英文只在首次定义、必要区分和协议字段中保留。短句数量下降不能替代逐段自然中文审校。

### R27｜P2｜展望中的推断仍有“必然发生”的语气

定位与短摘：[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:5](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:5>)，“未来 Harness 会更像……”；[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:9](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:9>)，“性能前沿来自……”；[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:11](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:11>)，“如果只追求模型无关，就会牺牲效果”；[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:29](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:29>)，“自动晋级范围会扩大”；[manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:41](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md:41>)，“三条路径会长期共存”。

章首标为作者推导是好的，但绝对句仍将条件性预测包装成结论。“模型无关”在第 18 章指可观察语义，在这里又指强制工具表现相同；不区分就会把正确的可移植设计一并贬低。三条未来路径也可能因监管、商业或技术约束发生转向。

建议改写：“若长期任务、工具种类和治理需求继续增加，Harness 可能承担更多类似操作系统的职责。统一任务和证据语义并不要求统一所有模型工具格式；强制相同格式可能影响特定模型表现，应实测。”三条未来路径加上观察信号与反证条件，如迁移成本、独立验证覆盖、自动晋级事故率；自动化扩大以这些条件成立为前提。

产品近期更新和 2026 年预印本的新结论仍由主代理处理；本报告没有据当前日期补造任何新趋势事实。

### R28｜P2｜章程的证据门槛与实际写法未正式对齐

定位与短摘：[research/planning/00_research_charter.md:9](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:9>)，“关键判断提供反方论证”；[research/planning/00_research_charter.md:30](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:30>)，“至少……两类来源”；[research/planning/00_research_charter.md:31](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:31>)，“三个相互独立的来源簇”；[research/planning/00_research_charter.md:34](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/planning/00_research_charter.md:34>)，“每个设计建议……适用条件、替代方案和……指标”；[research/audits/quality_audit.md:52](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/quality_audit.md:52>)，“承重主张子集”。

产品篇第 13—16 章主要采用同厂商文档、文章和仓库，它们不因 URL 不同就成为独立验证簇。实践篇声明作者参考设计，因此没有逐建议的外部研究是可以接受的，但与章程“每个建议”强门槛有差距。反例多在批判坏做法，较少认真呈现对本书主张的强替代：只用单一托管系统、先改确定性工作流、暂不建设统一控制面可能何时更优。

建议按主张类型调整章程并留变更记录：原生功能用版本固定的一手资料；效能结论要求有对照方法和适用范围；作者参考设计要求可运行教学例、失败反例及成本替代；预测明确不确定性。不要为了凑三来源把同一厂商不同页面当成三份独立证据。

产品章节的真实效果比较若暂未完成，就写“待验证的架构假设”。保留强设计立场，同时明确它在何种预算、风险和团队规模下不值得采用。

## 四层闭环专项验收矩阵

四层九字段模板在第 20—23 章形式上完整；缺口主要是字段之间的执行关系，不能因为表格填满就认定闭合。

| 层 | 已形成的机制 | 仍缺的可复核闭合 | 最小新增实例 |
|---|---|---|---|
| L1 任务内 | 分支、外部验证、有界修复、候选经验出口 | frontier/预算推进、故障计分、修复反馈污染、终态语义；R02、R03、R15 | 固定输入下两个失败分支、一个通过分支，列全部成本与停止原因 |
| L2 跨任务 | 写入门、scope/TTL、对照、撤销关系 | activation 分母、状态分支、在途撤销、测试反馈不得再进经验库；R03、R08、R16、R17 | 同一 skill 的发布与否对照，以及撤销影响缓存/任务/派生项的完整记录 |
| L3 Harness | 可变表面、冻结评价、激活、bundle/canary | 多候选选择统计、跨轮测试预算、权限变更界线、完整回退；R01—R04、R08、R14 | 一张包括未激活/超时样本的候选表，演示不晋级与回滚 |
| L4 模型 | 轨迹许可、lineage 切分、训练路线、2×2 | 真实效应估计、贡献标签不确定性、训练后删除边界；R04、R14、R18 | 四组合数值结果、组间差值与交互区间，绑定数据/模型/配置版本 |

建议把数据隔离落成下表，而非再次增写一句“必须隔离”：

| 数据域 | 可见者及用途 | 允许反馈 | 禁止转用/失效处理 |
|---|---|---|---|
| 开发/修复集 | 执行 Agent、evolver；诊断与提案 | 可定位失败的诊断 | 不再宣称未见泛化 |
| 候选选择集 | 评测服务；按协议选择候选 | 预注册的聚合与诊断 | 记录每次使用，控制对它的长期过拟合 |
| 最终封存测试 | 独立评测服务；确认已冻结 bundle | 预注册粒度、受限次数 | 不得直接转入 lesson、L3 提案或 L4 训练；暴露则降级并换测试 |
| 线上/canary 反馈 | 运营、安全、独立分析主体 | 带权限和保留期的事件 | 按任务/租户分流；候选不可改记录与分母；经验提炼需另过写入门 |

上述机制区分“数据未给模型看”与“数据未影响候选选择”。它不承诺有限测试能够证明永远安全，也不要求所有低风险任务都使用与模型训练相同的治理成本。

## 旧审核漏项与应保留的优点

| 旧判定 | 本次能够确定的漏项 | 应如何更正 |
|---|---|---|
| 字数与比例已核实 | 含/去 fence 混用、进化篇分子陈旧、比例算术不一致；R10 | 保留“达到章程区间”，替换数字及方法 |
| 全文保留技术含义 | NLE 括注无本地支撑、A/B 解释过窄、token 方向含混；R13 | 单独做术语和指标语义复审，不能只比机器敏感串 |
| 第 25、26 章已经清楚 | 补丁/验证不连通、抑制与对账矛盾、完成终点不一致；R05、R06、R19 | 对每个案例做输入—动作—结果—拒绝路径推演 |
| 四层“闭合” | 选择偏差、评价反馈累积、撤销与粘性优先级未闭合；R01—R04、R08 | 增加带数字的实验与故障演练 |
| 无 P1/P2 遗留、可落地 | 表示当时已登记问题的处置状态，不能涵盖未发现问题；R09 | 重新开启内容审阅待办，按具体证据逐项关闭 |

应保留：84% 和 46.9% 的厂商边界；preview 的版本不稳定提示；第 16 章对插件可逆与现实副作用的区分；第 17 章对容器/开源不等于完备安全的提醒；第 19、24 章对治理可独立更新的限定；第 25—30 章“作者参考设计”的章首标记；第 28 章“控制不等于全部自写”的澄清。这些内容无需因本次审阅而推翻。

## 修订顺序与验收方式

先修 R01—R08、R19 的机制与案例，再处理账本与旧审核结论。把一份真实可解析的教学任务、候选、验证结果、发布/拒绝记录连成完整链；记录全部 trial 和版本，给出一次按预注册规则“不晋级”的计算。这里的“可执行”可以是语言无关契约加最小受控实现，不要求搭建完整平台。

随后由主代理联网复核产品版本、精确协议名、NLE 等研究术语和原始实验方法。离线报告给出核验点，不代替原文查证。最后完成术语统一与重复合并；同一概念只在一处定义，后续章节用具体差异与交叉引用承接。字数重新从源稿计算，不能把构建成功或已登记 claim 的 PASS 作为内容通过证据。

## 方法与可复核记录

1. 必读 25 文件全部使用带行号输出通读；较长输出出现截断时，针对必读缺失部分单独重读。未把检索命中当成全文阅读。
2. 中文字数对当前源文件与旧审核声明的 Git 版本各算一次，结果一致。没有修改、格式化或构建任何正文。
3. 所有 JSON 示例在内存中解析：共 7 块均可解析。额外对第 25 章第一份对象与附录 E 的 required/properties 作集合比较；没有宣称这等于完整语义验证。
4. SQL 反例只用 SQLite `:memory:` 重现 GROUP BY/HAVING 的抑制影响；未执行正文的仓库命令，也未连接数据库。
5. 阅读了旧审计脚本后未执行：其中 audit_claim_ledger.py 虽不改账本，仍在第 256 行写另一份审计报告，不符合本次“只写指定报告”约束。
6. 未核验外部引用原文、产品实际行为、PDF 排版、站点构建和当前产品发布时间；第 1—11 章不在本次完整内容审阅声明内。外部证据真伪由主代理承担。
7. 必读 25 文件的有序“相对路径:文件 SHA-256”列表（以换行连接、末尾无换行）整体 SHA-256：`c26efae07ecc3626e998b107a93456d236e21c8b39a47f185c116e72bc1eeea5`。这固定本报告行号依据，不包括本报告或其他代理生成的文件。

以下只读命令可复算字数，不生成文件。与旧检查器保持同一字符范围及三反引号围栏规则；若未来引入四反引号或其他 Markdown 容器，应升级为相应解析器后再比较。

~~~python
from pathlib import Path
import re

fence = re.compile(r"```.*?```", re.S)
def han(text):
    return sum(0x3400 <= ord(c) <= 0x9FFF for c in text)

paths = sorted(
    p for folder in ("chapters", "parts", "appendices")
    for p in Path("manuscript", folder).glob("*.md")
)
rows = []
for p in paths:
    text = p.read_text()
    rows.append((p, han(text), han(fence.sub("", text))))
    print(p, rows[-1][1], rows[-1][2])
total = sum(r[2] for r in rows)
evolution = sum(
    r[2] for r in rows
    if r[0].parent.name == "chapters"
    and 19 <= int(r[0].name[:2]) <= 24
)
print("files", len(rows))
print("with_fences", sum(r[1] for r in rows))
print("without_fences", total)
print("evolution", evolution, evolution / total * 100)
~~~

交付前已检查 179 处文件行号链接，目标均存在且行号有效；25 个必读文件均进入覆盖矩阵；R01—R28 编号连续。源材料的整体 SHA-256 与读取时一致，Git 对正文及指定研究源文件没有显示改动。这些检查只验证本报告的定位和交付完整性，不替代上述内容审阅。

本次唯一交付是本报告；报告中的改写均为建议，没有回写正文、账本、旧审核或发布文件。

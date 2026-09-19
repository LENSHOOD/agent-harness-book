# 实践篇修订处置记录（2026-09-19）

## 范围与工作安排

授权分支：`codex/research-revision-20260919`。正文只写 `manuscript/chapters/25-29*.md` 与 `manuscript/parts/05_practice.md`，另写本记录；所有变更使用 apply_patch。不提交、不联网、不生成 site/artifacts，不修改 examples 和第6/10章、附录A/E。

按 planning-with-files 的记录方式在本文件集中保留计划、发现和验证结果；用户限定的写入范围优先，不另建计划文件。工作区及逐级父目录未找到所引用的 RTK.md；不臆造其内容。

1. 已完成：读取原章、产品/进化/结构审阅、示例执行报告、增量研究报告；核对附录E字段与第五章三平面定义。
2. 已完成：按 R05—R08、R19—R26 修订实践篇，同时承接固定分母、测试隔离等相关问题。
3. 已完成：正文结构、H1、结构化示例、字段映射、费用算术和本代理写入范围检查；只读核对公共入口的实现与另一代理已有运行证据。
4. 已完成：按主代理补充说明统一Task/Attempt/ToolTry及第10章完成状态；分别保留成品交付与业务提交两类任务分母。最终全书案例运行和发布由主代理整合执行，本代理不生成运行产物。

## 已确认的边界

- 旧 `git diff` 漏 untracked，当前工作区通过不能证明封存 patch 通过；原7位 commit、生产仓库与482回归数不是公共案例运行前置或实测结果。
- 内部全量对账必须先于披露抑制；20账户阈值不是 k 匿名证明；公开总额和分组也可能泄漏小组残差。
- 原SQL是BigQuery方言，历史读取受至多7天窗口约束；长期复现依赖当时物化/归档的数据快照。本轮没有原引擎、真实数仓或供应商端到端执行证据。
- 第27章修改订阅状态不能推出账单表变化；需要独立构造 scope、invoice、取消订阅入队和削弱测试四类负例。
- 所有 trial 保留在分配分母；脚本化样本用于检查 gate，不是模型效能或统计收益证据。
- 公共入口约定为 `python examples/run_examples.py`，由其他代理实现；本代理不写 examples。

## 逐项处置与验证

问题编号均指 [产品、进化、实践与结构审阅](../review_20260919/review_products_evolution_structure.md)，执行事实另参考 [示例执行报告](../review_20260919/report_examples_execution.md)，架构增量来自 [研究报告](../review_20260919/research_report.md)。下表的“已修订”只表示本写入范围内的正文已落实，不替其他章节或供应商实测宣布全局关闭。

| 问题 | 处置落点 | 已完成的修订与证据边界 |
|---|---|---|
| R05 | 第25章案例二，第1—4节 | SQL明确BigQuery方言，改用物化快照；说明至多7天历史窗口及无法事后补造快照。写明事件去重、NULL退款/收入/账户、月初日期和汇率前提；内部全量对账先于披露，最低人数不等于k匿名证明，禁止公开可反推小组的总额/残差与错误日志。未执行BigQuery。 |
| R06 | 第25章导语、案例一第1—4节 | 公共入口取代不可运行的三行原命令；原7位提交、生产源码不存在与482示意数均明示。补齐冻结写入、untracked清单、私有索引、补丁/树/文件摘要、干净应用、同树检查、固定独立验收、运行后复核及管道退出码。漏新文件和封存后漂移作为独立负例。 |
| R07 | 第27章第3.2—3.3节 | 四个独立负例：仅越界、仅改账单、仅错误入队、仅抑制测试；分别对应scope、invoice、cancelled slice、immutable suite。删除“只改active即两项必失败”的推断，表格明确为预注册预期。补临时数据库、生产写禁令边界、规范序列化和入队时状态检查。 |
| R08 | 第25章案例三、第26章第3节、第29章第8节 | 当前授权、撤销与取消状态优先于版本粘性；暂停在途任务、撤能力、隔离污染上下文、对账已提交效果；旧已撤销组合不能成为机械回滚目标。增加候选已验收、提交前revoke的拒绝演练。 |
| R19 | 第25章案例二及共用骨架、第26章第5—6节、第27章第6节、第29章第2节 | Task.checks映射为完整合同pre_commit_checks，提交后post_commit_checks单列。effect confirmed只进入VERIFYING_POSTCONDITIONS；失败/未知为COMMITTED_BUT_UNVERIFIED。成品交付无需强造external commit。N_deliverable与N_business_commit分别统计，未验收提交留分母、不进分子。 |
| R20 | 第26章第5—6节、第29章第2节 | 区分SLI与SLO；明确任务批次、观察期、未成熟样本、全部应恢复中断事件分母、已完成者P95的条件性及未完成数量。取回封存产物、重跑确定性检查、重放生成过程分开，不承诺任意模型结果逐字重建。 |
| R21 | 第26章第1—2节、第29章第1节 | 六层/三平面/信任域映射表；候选生成、独立评价和发布权分开。明确Agent Runtime与Execution Runtime，增加循环、会话、凭证、工具、业务验收五项责任表。自管执行不等于全数据自留。 |
| R22 | 第28章第1—2节 | M0—M4避免与进化L1—L4重名；有证据/缺失/不适用三态，不适用需责任人及等效控制。多运行时与受控进化非成熟必需条件；不能固定托管版本时使用变更检测、兼容门和降级。 |
| R23 | 第28章第3—5节、第29章第5、7—8节 | 采购建议改为有条件选择，保留受限自建、确定性流程、人工替代。虚构12个月表拆分固定投入、订阅、模型、执行、验证、复核、维护、安全、风险、双运行和退出；计算192,000/358,800元及任务量/复核/价格敏感性。退出以任务/产物/外部动作/凭证证据验收。 |
| R24 | 第25章合同与证据包、第27章第3.1节 | 标明领域输入并非Task/厂商配置；给出来源→Task/CompletionContract/路径策略/证据包映射，秒与动作计数语义明确。提供通过当前附录E校验的Task实例；证据包模板覆盖当前E骨架，保持INCONCLUSIVE和占位引用，不冒充真实证据。 |
| R25 | 第25—29章及实践篇导语 | 以候选协议、披露反例、trial表、四负例、费用表和退出时序替代重复结句；原理状态引用第6/10章，不另造runtime安全实现。公共案例和作者设计的覆盖边界单列。 |
| R26 | 第25—29章及实践篇导语 | 减少逐词中英夹注，统一产物、外部状态变更、任务执行尝试等用语；保留必要协议字段和首次术语定义。5个章H1与导语原开头标题完全保留。 |
| 相关R01—R03、R11、R28 | 第25章案例三、第26章接口、第28—29章替代选择 | 主要指标保留全部分配trial；ToolTry/Attempt重试不增加实验分母；激活另报；固定数据域及跨轮访问，反馈用于修复后不再称未见。配对差值/非劣/多重选择和成本作条件说明，脚本只验证gate。接口明确为本书草图，无供应商效能承诺。 |

## 与主代理的对象和完成语义对齐

- `Task → Attempt → Action → ToolTry` 分别是任务、任务执行尝试、逻辑动作与工具单次尝试。身份字段使用 `task_id`、`attempt_id`、`action_id`，同一工具动作重试保留幂等身份，不另计任务成功。
- 第27章编译Task使用附录E现有字段，不擅自扩展根schema。`checks`经适配器解析为完整CompletionContract的`pre_commit_checks`，`post_commit_checks`由被引用的完整合同承载。
- 两类完成分母在入口固定：成品交付以验收及交付结束；业务提交须确认副作用并通过后置检查。不能把失败提交改记为交付成功。合同修订保留原分类与历史事件。

## 本代理实际验证

1. `git diff --check`对六个正文文件通过；本代理所有写操作均为apply_patch，目标只有这六个正文文件与本记录。共享工作区的其他变更由并行代理产生，未回退、改写或提交。
2. 只读Python检查：5个章H1和导语原开头标题保持；代码围栏闭合；4段JSON、4段YAML解析通过，拒绝重复key；1段bash经`bash -n`通过。1段SQL和9段text按示意保留，没有将解析当作运行证明。
3. 第27章编译Task实际通过当前附录E的Draft202012Validator；6个检查ID与验收清单一致，均为`required: true`。第25章证据包覆盖当前E全部骨架字段，包括lineage里的model_version/harness_bundle；此项只是字段完整性，不是schema或证据真实性证明。
4. 第29章10项费用逐列求和，结果为192,000元与358,800元；两倍任务量得到252,000元与423,600元。复核率增加10个百分点的24,000元增量及模型单价翻倍增量与原假设一致。
5. 只读运行当前检查器，无`--report`，关闭字节码写入：`PYTHONPATH=research/audits/review_20260919/execution/deps .venv/bin/python -B publishing/scripts/check_examples.py`。结果为`exit_code: 0, checks: 99, failures: []`。本命令复用本机审计依赖，无联网安装，不生成报告或缓存；它不是完整案例执行。
6. 本地Markdown链接目标存在；公共`examples/run_examples.py`与README均已由另一代理落地。只读检查确认Git/DST、SQLite与30条脚本化trial的范围符合正文约定。

## 公共入口运行证据与发布交接

另一代理已有运行`examples/runs/20260919T110753Z_bx3h9dxw/summary.json`显示58项测试、0失败、0错误、0跳过，退出0。该入口定义0为正例通过且预期坏候选被拒绝，不能改写历史审计的失败含义。本代理没有执行入口、创建运行目录或修改examples。

对照该次`source_manifest.json`，第25、26、27章在上述运行后因主代理补充的身份/完成语义而继续修订。因此58项结果只属于当时版本，不能直接宣称覆盖本次最终全文。主代理发布前应以最终合并文本重新运行公共入口；本代理对最新文本执行的99项结构/schema门已通过。第27章原生产make/pytest流程、四负例的完整真实业务实现、BigQuery原引擎、供应商端到端、真实模型收益、站点和出版物均不在本代理实测声明内。

## 本轮交付正文SHA-256

| 文件 | SHA-256 |
|---|---|
| manuscript/chapters/25_three_end_to_end_cases.md | ce76210e8b76be6f699a7e4f33238aa223d9f7a60322d84205976418dd6b7570 |
| manuscript/chapters/26_next_generation_enterprise_harness_architecture.md | cf7149f3f8b9ad5d1ff0bbdcf763d0688d7af56bba26a6324b8717ac681b4e01 |
| manuscript/chapters/27_agent_sdd_specification_driven_delivery.md | 37a459d21f7acaaa9c8d1eb3428d5102168fedb8bd2376346f31e1c7f7e6a228 |
| manuscript/chapters/28_maturity_model_and_build_vs_buy.md | 4ef3e641745fd938435002e20ad66e2d94402d4fa741475c9402357fc9f5dae8 |
| manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md | f1eebfd2e153a1b2cc670d50eec04c8ede6767c4b6c964aa7f27b715ca1d865a |
| manuscript/parts/05_practice.md | 2a3f1c1be35cfbed90b9ec36792b3c06b490368ac792708f24e68d38e12b680f |

本代理交付止于上述正文与处置记录，未提交、联网、发布或生成site/artifacts。

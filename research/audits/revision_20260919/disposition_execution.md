# 2026-09-19 执行审计处置

**出版构建前最后一轮（第1/20章说明更新后冻结稿）**：`.venv/bin/python -B examples/run_examples.py`，运行目录`examples/runs/20260919T121551Z_0owvt091`，summary为该目录的`summary.json`及`summary.md`。156项pytest通过（3.42秒）、107项当前稿检查通过，exit 0；运行期间源码不变，128个产物hash全部一致，新source manifest已收录更新后的正文。案例Python代码相对前次运行没有变化，现冻结；未增加测试或修改实现。前次`20260919T120748Z_9weg7cx0`及下文早期运行均保留，以本次为本地发布交接结果。未修改正文或全局ledger，未提交推送。

本文件仅覆盖当前参考案例、机器可读契约与核心控制流。当前入口为 `python examples/run_examples.py`；独立稿件检查入口为 `python publishing/scripts/check_examples.py`。依赖固定在 `requirements-examples.txt`，无个人绝对 uv 缓存依赖。

参考实现使用真实本地 Git、SQLite、Python/pytest；模型输出和进化 trial 是确定性 fixture。它不是商业 Agent 复现、真实模型能力实验或生产安全认证。下列“已修”只指说明的当前协议/参考测试边界，不宣称已修复某供应商产品。

## 新旧证据分离

- 历史正式运行：`research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov`，172 探针，126 PASS / 46 FAIL，exit 1。正式 run 未覆写；441 个产物 hash 逐个复核一致。
- 历史 `run_all.py` 现在将来源固定为 `a1ed264462d9b61c260c1dc417243303bfc60b66` 的独立 checkout，B编号/行号只对应该版本。只改该入口和README以冻结来源；本轮未重跑历史正式审计。新门不用B编号或旧代码块位置。
- 当前首轮：`examples/runs/20260919T110753Z_bx3h9dxw`，58 pytest测试、99结构/schema/协议检查通过，exit 0。
- 中间运行：`examples/runs/20260919T111359Z_1ra5uk31`，55通过/6失败，exit 1，完整保留。失败原因是并行新稿将租户来源改为`trusted_tenant_for_attempt`，测试替身未同步；补齐后单独运行检查器已恢复通过。没有把失败改成通过，也没有改写该次证据。
- 首次交付复核：`examples/runs/20260919T111950Z_cf1_bbmi`，61 pytest测试通过（1.98秒）、99结构/schema/协议检查通过，exit 0。它早于独立review的组合路径发现，不能继承为后续修订已通过。另有独立干净Git子进程内28项DST合同测试通过，硬编码和漏helper负例分别按预期失败。
- 第1/11/20章与第6章反馈门补测：`examples/runs/additional_flow_20260919_XLd6Qt`，56项通过。独立review修复与追加控制流定向证据：`examples/runs/final_review_targeted_20260919_R6Ct87`，140项通过（1.79秒）；当时实际schema/结构检查107项通过。后续统一入口的最终证据另记，不覆盖前述目录。
- **独立review修复后最终统一入口**：`.venv/bin/python -B examples/run_examples.py`，`examples/runs/20260919T120045Z_ifofsdtt`，156项pytest通过（2.91秒）、107项当前稿检查通过，exit 0。运行前后源码一致；随后逐项核对产物hash及当前源码无漂移，历史正式441项hash仍一致。未重复全跑历史审计。

当前 exit 0 的含义是“正例通过，坏候选按预期被拒绝”；exit 1 是真实回归/环境或依赖错误。历史 exit 1 仍表示旧失败探针，含义不变。

## 46 项历史失败逐项处置

| # | 历史失败探针（原名） | 处置 | 当前证据或教学边界 |
|---|---|---|---|
| 1 | Task_empty_check_string_rejected | 已修 | 直接抽取附录E；checks空串、纯空白反例均拒绝，其他Task数组项同测 |
| 2 | Task_unknown_budget_field_rejected | 已修 | 实际schema拒绝budget未知字段与负金额 |
| 3 | Definitions_root_rejects_invalid_0 | 已修 | 根明确ref Action；null被拒绝 |
| 4 | Definitions_root_rejects_invalid_1 | 已修 | 空对象被根ref拒绝 |
| 5 | Definitions_root_rejects_invalid_2 | 已修 | 任意字符串被根ref拒绝 |
| 6 | Definitions_root_rejects_invalid_3 | 已修 | 数组被根ref拒绝；其他defs以各自ref验证 |
| 7 | Irreversible_requires_idempotency_key | 已修 | 所有非NONE写操作须含非空normalized_args_ref和idempotency_key；仅形状检查不证明去重 |
| 8 | Action_empty_id_rejected | 已修 | Action字符串标识逐项空串/纯空白反例 |
| 9 | Constrained_allow_requires_constraints | 已修 | CONSTRAINED_ALLOW须非空constraints；另测审批request id要求 |
| 10 | bash_original_directly_runnable | 已修当前入口 | 新入口真实创建独立repo、源码和测试；不再依赖缺失的8f31b6e，未声称旧命令可运行 |
| 11 | bash_with_pytest_source_tests_exist | 已修当前入口 | requirements固定pytest；tests/src实际提供，干净apply执行28项DST合同测试 |
| 12 | bash_pipeline_propagates_git_failure | 已修当前入口 | Git子进程逐个检查退出码，无管道掩盖；坏patch/import失败单列，外层要求被拒绝 |
| 13 | SQL_raw_SQLite | 不适用：方言差异 | 新案例是独立SQLite物化快照模型，不据此判断BigQuery原SQL有效性或宣称原引擎执行 |
| 14 | SQL_suppressed_groups_reconcile_to_finance_without_bridge | 已修 | 全量可核算口径5050先对账，再披露4100；950仅内部合成证据，公共输出不带总额/残差 |
| 15 | SQL_DUPLICATE_money_not_doubled | 已修限定口径 | 精确重复去重，事件冲突版本拒绝；不是COUNT DISTINCT账户代替金额去重 |
| 16 | SQL_NULL_refund_preserves_100_revenue | 已修限定口径 | 明示NULL refund=0并用COALESCE；非真实业务默认口径批准 |
| 17 | SQL_NULL_account_excludes_money | 已修限定口径 | 无法识别account的行隔离，不混入收入或k人数 |
| 18 | SQL_k_gate_guarantees_numeric_revenue | 已修限定口径 | NULL revenue隔离；全NULL组不被当作有效数值分组；k门仍非完整隐私保证 |
| 19 | A_approval_first_observation_defined | 已修并执行当前原文 | 审批持久化后立即return；第一动作审批时不追加observation |
| 20 | A_approval_does_not_reuse_prior_observation | 已修并执行当前原文 | ALLOW后接审批只保留前一次observation，暂停动作不复用旧值 |
| 21 | CH6_DENY | 已修并执行当前原文 | DENY及未知决定零execute；runtime单独测试零目标效果 |
| 22 | CH6_approval_batch | 已修并执行当前原文 | 审批return中止批次；runtime重启仍暂停，批准后以当前policy重授权 |
| 23 | CH6_cancel_in_batch | 已修并执行当前原文 | 每动作前refresh取消；runtime目标执行期间取消后不派发下一动作 |
| 24 | CH10_DENY_zero_commit | 已修并执行当前原文 | DENY/未知决定BLOCKED，不调用提交helper |
| 25 | A_lost_response_exception_normalized | 已修 | 原文字面执行ExecutionError分支；SQLite目标已提交但回执丢失时runtime捕获异常 |
| 26 | A_lost_response_marks_unknown | 已修 | 持久UNKNOWN、重启NEEDS_RECONCILIATION；新稿UNKNOWN停止继续循环 |
| 27 | A_stale_lookup_setup_timeout | 已修限定helper | 原文新lookup_or_unknown不可用返回PENDING；runtime对账lookup异常保留UNKNOWN；无真实网络栈验证 |
| 28 | A_retry_with_stale_lookup_exactly_once | 已修保守策略 | 旧EXECUTING/UNKNOWN遇陈旧/无证据/ABSENT均不重放；确认COMMITTED才回填 |
| 29 | A_concurrent_lookup_then_execute_exactly_once | 已修限定目标能力 | 12并发调用只一次claim和预算消耗；两个独立控制库对同一SQLite目标依靠原子唯一键+args绑定产生一次效果 |
| 30 | A_recover_terminal_cancelled_does_not_resume | 已修并执行当前原文 | recovery终态直接返回并释放lease；runtime重启/批准/提交均不恢复CANCELLED；未知效果先CANCELLING |
| 31 | B014_injected_tool_fault_unhandled | 教学限制已实测 | 当前第1章原文工具/模型异常仍向外传播，但finally结算已执行；不伪称已实现完整恢复或吞异常成功 |
| 32 | B014_static_budget_source_terminates | 已修并执行当前原文 | max_steps有界循环在静态预算替身下也终止；动态预算不足则在下次模型前向外抛宿主停止信号 |
| 33 | B078_injected_child_timeout_unhandled | 已修限定helper | 第11章原文字面捕获child超时/取消，返回FAILED_WITH_EVIDENCE并走finally；真实进程树后端仍未验证 |
| 34 | B078_timeout_releases_unused_reservation_in_source | 已修限定helper | 实测已停止child计费2/预留4并归还2；清理未闭合时保留全部预留、返回RECONCILIATION_REQUIRED |
| 35 | B091_mid_batch_budget_exhaustion_graceful_return | 已修并执行当前原文 | paid在执行或验证中途拒绝新预留，搜索返回budget_exhausted；已执行未验证的候选不得入合格集 |
| 36 | B091_outer_budget_guard_prevents_batch_overspend | 已修限定延迟操作契约 | 每次实际生成/执行/验证前均有对应RESERVE，耗尽无新派发；propose/run/check必须只构造Operation描述 |
| 37 | B091_injected_verifier_fault_unhandled | 已修并执行当前原文 | verifier故障由HostActionError退出，finally保守计费；完整性/UNKNOWN另转隔离，不能携已有好候选假完成 |
| 38 | B091_static_frontier_budget_source_terminates | 已修并执行当前原文 | 原文pop/visited及深度/展开/无进展上限实际执行；空生成、重复状态、自循环均有确定停止路径 |
| 39 | R02_confirmed_effect_failed_health_not_verified_complete | 已修并执行当前原文 | 第10章COMMITTED且postcondition失败返回COMMITTED_BUT_UNVERIFIED；runtime分离effect与业务验收 |
| 40 | CH6_compensation_alone_safe_retry_when_receipt_lost | 已修 | UNKNOWN保留，不因可补偿而重放；实际负例证明目标只一次；不声称实现真实补偿 |
| 41 | CH27_claim_scope_and_invoice_both_fail_from_source_edit | 已修表述；保留教学限制 | 第27章拆开scope、invoice、行为、套件抑制；明确源文件改解释不必改账单。本轮未运行原生产项目 |
| 42 | DST_baseline_visible_contract | 有意负例保留 | 原24小时算法仍错；当前回归要求它在DST日期被拒绝 |
| 43 | DST_overfit_hidden | 有意负例保留 | 原硬编码两日期仍通过可见两项，却在邻年/其他时区/半小时transition合同失败；失败stdout保留 |
| 44 | git_raw_diff_captures_untracked_required_newfile | 已修并保留反例 | 显式列出untracked并stage许可路径；旧diff遗漏helper的patch在独立干净repo失败 |
| 45 | git_sealed_patch_and_tested_input_are_same | 已修 | 只从封存patch在独立repo应用，tree/hash一致；封存后工作区改动不影响验证输入 |
| 46 | evolution_completed_only_ranking_truthful | 有意反例已纳入门 | 18/20表面90%实际18/30=60%；缺失/重复/额外ID或分母20均拒绝；超时和未激活trial不从分母删除 |

## 关键限定与新增回归

1. 30 trial是10任务×3重复的脚本化结果：基线24/30、候选28/30、关键切片失败canary29/30。冻结evaluator、activation、SQLite持久化终测单次访问、旧任务版本固定和全bundle回滚均实际测试；没有统计/模型能力外推。
2. Git参考的公开28条合同测试涵盖2025–2027邻年、Berlin、UTC/Shanghai、Lord Howe半小时变化、两个fold及连续半开区间；不验证跳过整日或午夜歧义时区，也不冒充原482项生产回归。
3. SQL合成88行明示NULL、重复、月初日期和有效区间口径。公共披露文件与仅内部合成对账文件分开；发布全量真实财务残差可能泄漏小群体，本例不授予这种披露权限。
4. 附录A当前租户绑定由可信`Attempt`读取，测试故意提供一个不可信Action.tenant字段并确认未被采用。schema非空键只是身份表达；目标库原子唯一约束+args比较才是本例去重保证。
5. 核心函数按稳定唯一名称抽取；第1/20章和A匿名循环按唯一语句包装。最小语法翻译表及helper前提见`examples/tests/HELPER_CONTRACTS.md`，没有增删原文分支。字面分支通过不等于真实IAM、签名、租约fencing、网络或OS取消经过验证。
6. 写入仅在授权examples/、requirements-examples.txt、check_examples.py、本说明及历史入口/README；未提交推送，未修改manuscript/site/全局ledger。其他代理的并行更改不属于本执行代理产物。

## 独立review F01–F07及反馈门处置

已完整读取`final_review_runtime.md`，先把F01/F03/F04/F06公共方法反例写成失败测试：7项按报告症状失败，3项“其他未决记录仍不能完成”对照通过，然后修实现。没有将旧错误输出改成新的正确预期。F02/F05/F07正文由主代理修改，本执行代理不改正文。

| 项 | 当前修复与实测范围 |
|---|---|
| F01 | 新key在任一UNKNOWN存在时不授权/不创建intent/不扣预算，重启同样暂停；默认EXECUTING阻断顺序新动作。明确独立且目标footprint不重叠的并发可在UNKNOWN发生前准入，UNKNOWN之后仍一律暂停。嵌套两种结果完成顺序验证全账本归并保持NEEDS_RECONCILIATION，不被另一个COMMITTED覆盖 |
| F02 | 连接当前底层commit_effect_safely和两个当前上层循环，lease忙/lookup不可用各自产生PENDING；保存原动作与观察后WAITING_FOR_EFFECT，第二intent及目标请求均为零。不是仅检查helper返回常量 |
| F03 | submit与reconcile回写共享带旧状态条件的更新，只允许EXECUTING/UNKNOWN被结算；COMMITTED不可被迟到UNKNOWN降级，返回实际持久状态。在lookup回调中安排“旧对账读完→新对账确认→complete→旧回写”，另测迟到submit timeout，均保留COMMITTED/COMPLETE |
| F04 | 同key也必须同action_id；未批准/已批准两种状态下换身份均在授权前拒绝。恢复用持久payload重建原Action，不能把旧approved标志交给新Action |
| F05 | 实际附录E wire先经PolicyDecoder验证，内部才默认reason_code与省略constraints；四种合法最小实例实际驱动附录A。非法reason字段、空constraints、缺审批/约束、未知枚举均拒绝。第6/10章也接同一适配器；没有便利reason属性绕过schema |
| F06 | DENIED保留无效果审计历史，不要求它成为COMMITTED；必须至少一个实际COMMITTED、非空可信检查全部True，且其余只可为DENIED。未知/执行/审批/预算失败仍不能完成；若合同把拒绝视为硬失败，检查明确False仍阻断 |
| F07 | 主代理已收紧Task四个身份字段；检查器逐项以真实schema拒绝空串和空格/制表/换行组合，无静态grep替代实例验证 |
| FC01 | 第11章真实PolicyDecision实例通过实际schema后使用decision.decision/CONSTRAINED_ALLOW运行；只对刻意schema非法未知枚举另测原文防御分支 |
| FC02 | 第6章/A/第10章各测开发反馈允许、密封终测禁止，兼测反馈余额/主体/修复预算边界。diagnostics sink刻意无第二道guard，保证原文漏判就会泄漏并失败。密封终测失败且repairable时仍不生成后续模型诊断或REPAIRING输出 |

新增第1章9场景、第11章委派14+合并7场景、第20章19场景。第1章宿主暂停/取消向外传播，搜索暂停/取消经HostActionError停止；不冒称持久恢复。第20章helper必须返回延迟Operation，这一前提在测试契约和证据中明示。所有原文hash与最小转换文本随最终统一入口保留。

正文交接已闭合：主代理更新第1章实跑范围说明，并在第20章明确Operation延迟构造、获得ticket后派发及普通函数需传闭包的条件。本轮最终运行已捕获这些正文的新hash；本代理未修改正文。

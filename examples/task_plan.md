# 当前参考案例修订计划

写入范围：examples/、requirements-examples.txt、publishing/scripts/check_examples.py、指定 disposition；历史 run_all.py/README 仅固定来源版本。

1. 核对历史 46 项失败、当前协议及 fixture 来源（complete）。
2. 实现 Git/DST、SQLite、确定性 evolution 与安全 runtime（complete）。
3. 建立当前稿结构/schema/稳定函数控制流回归门（complete）。
4. 实跑保留新证据；逐项处置历史失败并核对写入边界（complete）。
5. 补第1/11/20章当前原文字面控制流与helper契约（complete）。
6. 按新增授权处理独立review F01–F07、三处终测反馈门与PENDING连接；最后跑统一入口存证（complete）。

当前稿与其他代理并行修改；不得使用历史 B 编号绑定当前稿。新门 exit 0 表示正例通过且负例拒绝，exit 1 表示回归。历史审计含义不变。

## 错误记录

- 初始查询 examples/ 尚不存在；将在授权范围内创建。
- 工作区及各级父目录未找到所引用 RTK.md；沿用已提供的工具/编辑约束。
- 新稿将附录A预算结算helper更名为settle_action_budget_from_meter；首次字面控制流9项中8通过、1因替身旧名失败。已按实际新稿替身接口调整，未改正文控制流。
- 完整入口首轮58测试+99检查通过并存证。补充取消/UNKNOWN/异常结算后再次运行时，新稿增添trusted_tenant_for_attempt，6个控制流替身缺接口而失败；失败运行20260919T111359Z_1ra5uk31完整保留，补接口后定向复核再总跑。
- 补第1/11/20章首次定向运行49项：37通过、12个delegate替身失败；正文并行统一为PolicyDecision.decision/CONSTRAINED_ALLOW，已同步，未改原文分支。新增第6章feedback_allowed密封终测反例。
- 独立review的公共方法回归先红：F01/F03/F04/F06共7项复现原症状；3项保守完成对照原本通过。修实现后定向140项通过（1.79秒），实际稿件检查107项通过。新增授权要求再运行最终统一入口，覆盖先前“不重复总跑”的默认安排。

最终：20260919T111950Z_cf1_bbmi，61测试+99检查通过，exit0；历史441产物hash不变，46旧FAIL逐项覆盖。未提交/推送。

后续独立review修复最终：20260919T120045Z_ifofsdtt，156测试+107检查通过，exit0。最新产物hash及源码核对一致，历史441产物不变。只写授权范围，未提交/推送。

出版交接最终：20260919T120748Z_9weg7cx0，当前冻结稿1轮总跑156测试+107检查通过，exit0；128产物hash一致。无新实现变更或扩展测试，工作完成。

第1/20章说明更新后最终交接：20260919T121551Z_0owvt091，156测试+107检查通过，exit0；128产物hash一致，已记录正文新hash，Python代码无变化。代码冻结，交主代理本地发布。

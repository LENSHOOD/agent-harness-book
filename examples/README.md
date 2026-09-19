# 当前可执行参考案例

这是书稿的本地可执行参考模型和回归门，**不是商业 Agent 复现、真实模型能力实验或生产安全认证**。没有供应商/API调用、外部消息、业务提交、Git commit、推送或部署。SQLite“目标系统”只写本次测试数据库。

在仓库根目录使用 Python 3.11+、Git 及系统 IANA 时区数据：

```bash
python -m venv examples/.venv
examples/.venv/bin/python -m pip install -r requirements-examples.txt
examples/.venv/bin/python examples/run_examples.py
```

激活上述环境后，统一入口是 `python examples/run_examples.py`。Windows 使用 `examples\.venv\Scripts\python.exe`；没有系统时区库时，另装并记录合适的 `tzdata` 版本。脚本使用运行它的 Python，不读取个人 uv 缓存，不修改书稿或旧审计。CI 直接安装根目录 `requirements-examples.txt` 后执行入口即可。jsonschema 4.26.0 / PyYAML 6.0.3 / pytest 9.1.1 均实际使用，时区文件和环境版本会记录到证据中。

每次在 `examples/runs/<UTC timestamp>_<random>/` 创建新证据目录，旧目录从不覆盖。可用 `--output-dir <parent>` 指定新的运行目录父级。`summary.json/md`、JUnit `tests.xml`、命令 stdout/stderr、源文件 hash、SQLite 数据库、补丁和 `artifact_hashes.json` 一并保留。exit 0 = 正例通过且坏候选被预期拒绝；exit 1 = 回归、依赖或环境失败。历史入口 `research/audits/review_20260919/execution/run_all.py` 仍以 exit 1 表示历史失败探针，不纳入当前 CI 入口。

## 覆盖范围

| 案例 | 实际执行 | 前提和限制 |
|---|---|---|
| Git / DST | 独立临时仓库、真实 index/tree；显式追踪新 helper；封存带 hash 的 patch；另一干净仓库 `git apply --index`；28 条日期/相邻区间/fold 合同断言 | 只定义当地民用日对应半开 UTC 区间；2025–2027 New York、Berlin、Lord Howe 半小时 transition、UTC、Shanghai。未覆盖历史整日跳过或午夜歧义，也不是完整支付合同 |
| 坏 Git 候选 | 硬编码两日期的旧算法通过可见日期，但完整合同失败；漏掉 untracked helper 的 patch 在干净环境 import 失败；工作区后改不改变封存输入 | 这些预期失败在子日志明确保留；外层门要求它们失败，不能静默省略 |
| SQLite | 88 行合成历史，物化固定 2026-08-03 02:00 UTC snapshot；精确重复去重、冲突版本拒绝；先全口径对账再披露 | NULL refund=0；未知 revenue/account 与非月初日期隔离。金额为已换算整数 CNY；不是 BigQuery 原引擎或真实财务口径授权 |
| 披露 | 完整内部口径 5050，允许披露 4100，受限残差 950；k=19 抑制、k=20 保留 | 公共结果不带全量总额/残差，避免直接相减暴露单个小组。本仓库内完整数据仅因全是合成 fixture 才可保留；k 门不等于完整匿名化保证 |
| Evolution | 10任务×3重复的30条确定性 trial；24/30基线、18/30分母作弊、28/30候选、29/30但关键切片失败的canary | 超时保留分母及两次重试成本；不声称统计显著性、因果收益或真实模型优化 |
| 进化门 | evaluator冻结、注册ID完整、activation、终测单次访问（SQLite持久化）、旧任务版本固定、关键切片失败回滚完整bundle | 本地治理模型，没有真实流量/模型/训练，也没有对抗性OS级评估隔离 |
| 安全runtime | DENY零执行；持久审批暂停并重新授权；args/tenant/target绑定；回执丢失UNKNOWN；无证据/陈旧证据不重放；并发预算与执行去重；取消终态；COMMITTED需单独验收 | 目标库主键+参数比较在同一事务内提供原子幂等；仅有key或本地账本不够。无真实IAM、签名、网络、租约fencing或进程树取消 |
| 当前稿控制流 | 按唯一函数名/语句抽取第1/6/10/11/20章及附录A，运行原文分支；包含低层PENDING→上层暂停连接、真实PolicyDecision wire→schema→adapter→控制流、三处终测反馈门 | 最小语法翻译及逐项helper前提见[测试契约](tests/HELPER_CONTRACTS.md)。不重排分支；源码hash、转换文本与结果保存。1000行事件watchdog是审计保护，不冒充正文预算逻辑 |

`python publishing/scripts/check_examples.py` 独立解析全稿 JSON/YAML fence（拒绝重复key）、独立结构文件，直接校验附录E实际schema及正反实例。消息根必须显式 `$ref` Action，PolicyDecision/Observation使用同份defs的各自ref；也检查参考入口并执行当前核心函数字面控制流测试。完整入口已经跑这些测试，因此调用检查器时显式传`--skip-flow-tests`避免重复。YAML字段说明只做格式解析，不宣称证据包具有完整schema或可信签名。

## 来源、许可与复现边界

代码由本项目本次修订创建。DST语义/坏候选与SQL合成数据设计改编自项目自身 `research/audits/review_20260919/execution/fixtures/`、`sql_case.py`；进化案例改编自同目录 `evolution_case.py`。这些是此前审计创建的fixture，不是从商业产品源码、用户数据或第三方benchmark复制的材料。当前入口没有运行时依赖旧审计目录。

本目录沿用项目著作权/授权安排，未额外授予一份新的开源许可证；不能把本次项目内复用解释为第三方或商业源码的再许可。Python、Git、SQLite、jsonschema、PyYAML、pytest及系统时区数据库分别遵循各自分发许可。本项目未打包它们的源码、二进制或个人缓存。

测试文件是公开、可信参考验证器，不叫从未参与选型的秘密终测。`FinalTest`只演示已冻结候选的一次终测访问记账。代码与结果不证明供应商接口、BigQuery时间旅行、跨租户权限、跨机器恰好一次、真实杀进程恢复、补偿正确性或完整生产安全。取消会阻止继续调度；未知效果使任务保持CANCELLING，回读确认后才收敛为CANCELLED；已发生效果不会被取消字段抹除。Runtime只实现ALLOW/DENY/REQUIRE_APPROVAL，其余策略值拒绝并报错；CONSTRAINED_ALLOW的schema与正文分支另由检查器验证。验收结果由可信测试端提供，不模拟独立生产verifier服务。

Runtime默认顺序准入：已有EXECUTING时新动作返回PENDING，任一UNKNOWN使任何新key暂停且不扣预算。预算并发测试由可信宿主显式声明`independent=True`，且目标footprint不同；它不允许越过UNKNOWN，也不是自动依赖分析。状态从全账本归并，迟到submit/对账以条件写入保留已确认COMMITTED。审批恢复必须沿用原action_id和封存payload。

完成合同要求非空可信检查全部通过、至少一个实际COMMITTED，且没有未决/未完成记录。DENIED是已结束的无效果提案，保留审计但不要求它后来也提交；若拒绝本身违反业务硬约束，可信检查应明确失败。UNKNOWN、EXECUTING、审批和预算失败不因已有一个成功效果而被忽略。

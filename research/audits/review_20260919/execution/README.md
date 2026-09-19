# 全书示例离线执行审计

本目录是历史失败审计。入口现固定读取 Git `a1ed264462d9b61c260c1dc417243303bfc60b66` 的独立 checkout，B 编号、原文 hash 和行号只对应该版本，不再从当前修订稿抽取。每次新运行的 `historical_source_pin.json` 记录固定来源；环境探测仍读取本仓库原有 `.venv`。原正式运行 `20260919T102120Z_30xh1oov` 及其他旧结果均保留，未覆写或重新归类。

当前修订稿的可移植参考入口是仓库根目录 `python examples/run_examples.py`，依赖为 `requirements-examples.txt`；当前回归门 exit 0 表示正例通过且负例按预期被拒绝。两个入口目标与退出码不同，不能用当前全绿结果改写下面的历史 FAIL。历史执行脚本其余依赖方式与限制仍按下文保留。

从任意工作目录一条命令运行：

```bash
bash '/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/run.sh'
```

退出码 1 表示反例/失败探针已如实复现，不是全绿；2 表示审计程序错误或新结果偏离已登记预期；0 才表示没有失败探针。不要把 exit 1 自动改为成功，也不要把它解释为脚本无法运行。

默认使用书稿已有 `.venv/bin/python`（本次 CPython 3.13.13）。只从本机现有 uv 缓存复制已安装依赖到本目录 `deps/`，不联网、不改原 `.venv` 或 requirements。精确版本在 `requirements-audit.lock.txt`，每个依赖文件的来源与 SHA-256 在 `dependency_manifest.json`。`bootstrap.py` 会校验已有副本；删除可重建 deps 后仍可从记录的本机缓存重建，但脚本不会删除任何数据。若将材料迁移到另一台机器，需要兼容的 Python/原生扩展及这些离线依赖，不能声称已有跨平台镜像复现。

每次运行生成新的 `runs/<UTC timestamp>_<random>/`，不覆盖以前的运行。入口 `latest_run.json` 指向最近一次；固定报告引用的正式运行是 `20260919T102120Z_30xh1oov`。该次 172 个探针中 126 PASS / 46 FAIL；失败包括25个P1、14个P2、6个故障注入和1个SQLite DIALECT_MISMATCH；方言不匹配不表示原SQL错误，不能转换成一个“全书通过率”。

主要证据：`inventory.json`（120块原文/位置/hash），`coverage.md/json`（完整逐块矩阵），`results.json`、`failures.json`、`summary.json`、`environment.json`、`stdout.log`、`stderr.log`、`commands/`，以及 SQLite 数据库、原样/适配 SQL、候选补丁。`artifact_hashes.json` 固定运行产物；主 stdout/stderr 在汇总输出后才关闭，不放进该 manifest，内容完整保留。

`safety_models.py` 从原 fence 做最小语法翻译，实际编译运行；原控制流与补正实现分开。所有 helper 的缺省行为和反例适用条件在报告说明。`additional_counterexamples.py` 补充静态审阅 R01/R02/R03 与第27章检查独立性。供应商/模型提供者是预先定义的确定性 stub；无模型/API付费调用，无外部消息、生产变更、PR或发布。

`remaining_pseudocode.py` 补齐 B014/B078/B091，21个场景/25个探针，保留原控制流并逐项声明helper契约。正常、异常、取消/冲突和预算终止实际执行；不进展的循环由外部240源行事件/2秒watchdog标为AUDIT_ABORTED，绝不冒充原程序自行终止。8段控制流伪代码均已有受控翻译；23结构化片段运行语义仍未验证。覆盖类别为设计示意93、仅schema2、未验证23、可运行代码2。

主代理提供的BigQuery官方文档支持FOR SYSTEM_TIME AS OF；本次仅离线读取其抓取材料，无BigQuery账号执行。Aug3固定as-of截至Sep19已47天，超过7天回溯窗口，长期复跑须物化/归档快照；SQLite探针只标DIALECT_MISMATCH。

`fixtures/` 是用 apply_patch 创建并保留的审计用源码，不是书稿原有测试。Git 案例使用真实 index 和 tree，不创建 commit；原 bash 专用目录从书稿本地 clone，缺少 `8f31b6e`、`src/time/`、`tests/time/` 的情况原样保留。补充的 DST repo 与其完全分离。

本目录 `.gitignore` 只排除 `deps/`、`bin/`、Python/pytest缓存和整套生成工作区。`fixtures/pytest-wrapper.sh` 保留，运行时复制为被忽略的 `bin/pytest`；manifest、脚本、JSON、日志、补丁、SQLite证据仍可进入后续版本管理。没有删除任何目录。

验证最新证据、逐块矩阵，以及与上一完成运行共有探针的结果是否一致（新增探针、severity重分类单列）：

```bash
'/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/.venv/bin/python' -B '/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/verify_artifacts.py'
```

首次试跑 `20260919T095015Z_z5_rc699` 有一个审计自身手算预期错误（迟到快照的重复行也同时失效，实际1700而非误填1790），保留原始失败和错误退出2。后续修正的是审计预期，书稿/原查询不变；旧版147探针运行均留档。本轮新增部分先定向检查，然后只总跑一次；原有147项判决未变，新增25项，SQLite项只作方言重分类，未重复跑旧版全套多轮。

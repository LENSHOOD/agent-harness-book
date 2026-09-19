# 案例实跑审计计划

写范围仅本 execution/ 目录及上一级 report_examples_execution.md；不改正文、不联网、不提交发布。

1. [完成] 全 manuscript fenced block 原文清点、行号、SHA-256、分类及环境探测（41 markdown / 120 blocks）。
2. [完成] 25 JSON/YAML 原样解析；2 schema 元校验、44 正反实例。
3. [完成] 原样 bash/SQL 失败保留；SQLite 88 行与独立手算。
4. [完成] 附录 A/第 6/10 章忠实/补正模拟，exceptions/race/cancel 反例。
5. [完成] 三案例首跑；git 真 index/tree，不创建任何 commit。
6. [完成] 用户新增 R01/R02/R03、补偿、untracked/TOCTOU、27章独立检查与歧义探针全部实跑；局部gitignore就绪；正式报告、覆盖矩阵及复现核验完成。

原则：模拟不等于供应商端到端；设计图不冒充可执行；捕获 exceptions 必须记录完整 traceback；原样与补正分栏；每次运行使用新目录保留历史。

已知环境问题：书稿 .venv 无 pip。优先检查已安装解释器/依赖，若确需安装仅局部目录，不改 requirements。

审计自身错误：首次 SQLite later 手算预期1790遗漏重复行也在同刻 valid_to 到期，应1840-50-90=1700。首次失败保留 run 20260919T095015Z_z5_rc699，后续只改审计预期，不改被审稿件。bundled runtime 也无所需包，后从本机 uv 已安装缓存复制12个发行版至 execution/deps（10MB）。

正式结果：20260919T095940Z_b_il6ikt，147探针=109 PASS/38 FAIL（25 P1、10 P2、3 INJECTED），无未解释结果或审计异常。最后两次语义结果一致，437产物hash与120矩阵行核验通过。报告35个文件链接全部存在。正文/requirements无改动；无提交、发布、删除、外部调用。

## 用户追加：剩余控制流实跑

7. [完成] B014/B078/B091最小忠实翻译，21场景/25探针；逐helper契约与外部watchdog，保留17PASS/8FAIL。
8. [完成] 定向检查后仅一次总跑：20260919T102120Z_30xh1oov，172探针126PASS/46FAIL（25P1、14P2、6INJECTED、1DIALECT_MISMATCH）。报告/README/矩阵更新；23结构化示例仍只解析，8个控制流伪代码均有受控执行。

BigQuery：离线读取主代理已抓取的官方Query syntax，确认FOR SYSTEM_TIME AS OF文档支持和7天限制；Aug3到Sep19相隔47日，长期复跑需要物化/归档。无账号/原引擎执行。验证共有147判决未变，SQL项仅severity重分类；新增25项单列；120矩阵行与441产物hash核验通过。

# 实跑进度

2026-09-19：读完附录 A、E 和第 6/25 章相关内容；核查 requirements、现有审计计划和写入边界。未找到 RTK.md；.venv/bin/python -m pip list 报 No module named pip（原始 stdout 位于会话，后续环境 JSON 会重新记录）。

首跑 20260919T095015Z_z5_rc699：135 checks，101 PASS/34 FAIL；exit2 因 SQL later 手算自身错误，非被审 SQL 新缺陷。完整 logs/results 保留。原 bash exit127，提供pytest后exit4；pipeline exit0掩盖git128。JSON/YAML25/25解析成功；schemas元校验通过但根$defs不约束实例等缺口复现。DST overfit visible5/5，hidden1/17；修复后visible5/5、hidden17/17。

用户增补已加入：第10章状态图提交确认但health失败；第6章回执丢失+补偿故障；第25章untracked新文件和sealed/tested输入漂移；第27章只声明歧义探针，不声称原始实现失败；2x2与预算校准明确未运行。

读取两个静态review后补上products R07的正确目标：不仅时间语义，还实际比较scope/invoice独立性，提供一正三负SQLite fixture。history健康项正式命名对齐R02。

运行历史：20260919T095546Z_0c07awoi 为145检查/108PASS37FAIL；新增第27章检查独立性后20260919T095835Z_3_7n258_为147检查109PASS38FAIL；用户要求局部gitignore并保留manifest后20260919T095940Z_b_il6ikt为相同147结果。后两次exit1均无审计程序异常。所有运行保持可追溯。

交付：report_examples_execution.md、README、完整120行覆盖矩阵、所有原始JSON/YAML与schema反例、SQLite库/fixture、真实Git patch、命令stdout/stderr、环境及依赖manifest、38FAIL完整反例、verification.json。核查35文件链接无缺失；437产物hash和120行矩阵核验无差异；所需依赖/临时仓库忽略规则生效，必要证据未被忽略。误写命令日志序号042的只读定位失败后，以commands.json的name字段作为权威索引；没有影响任何执行结果。

追加执行：用apply_patch创建remaining_pseudocode.py，仅读原fence做语法翻译，明确每个helper；定向probe在probes/remaining_jcv_pjoj保留25个检查及异常，然后仅一次完整总跑20260919T102120Z_30xh1oov。21场景覆盖B014 normal/zero/exhausted/invalid/error/static；B078 normal/assert/budget/timeout/cancel/provenance/unverified/conflict/parent gate；B091 normal/zero/strict budget/account-only/verifier fault/static。定向后细化B078 unused reservation预期为2（总额3减使用1），不退还已消耗成本，原流程实际仍1。

本次最终172探针126PASS/46FAIL，其中25P1、14P2、6INJECTED、1DIALECT_MISMATCH。新增25，旧147判决未变，无程序异常/未解释结果。外部watchdog拦下B014与B091不推进场景并标AUDIT_ABORTED，不把中止记成原程序安全退出。报告/README数字、最终run链接、120矩阵已更新；verify_artifacts核对441产物hash、原147共有结果与忽略规则通过。

按用户新增资料，读取主代理retrieval/bigquery-time-travel.json的.text419–440及hash；只作官方文档核验转述，未联网、无BigQuery账号执行。FOR SYSTEM_TIME语法受支持；固定Aug3截至Sep19超7日窗口，需要长期物化/归档。SQLite项从P2改为DIALECT_MISMATCH；历史run不回写。

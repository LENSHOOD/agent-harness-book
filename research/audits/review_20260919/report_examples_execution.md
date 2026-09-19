# 全书案例与示例实际执行审计（2026-09-19）

本次完成全书 fenced code 盘点和授权范围内的离线执行验证，不能据此声称“全书案例均可直接运行”或“供应商端到端已验证”。

正式运行：`20260919T102120Z_30xh1oov`，源码基线 `a1ed264462d9b61c260c1dc417243303bfc60b66`。41 个 Markdown 文件、120 个代码块全部进入矩阵。172 个检查探针得到 **126 PASS、46 FAIL**，其中 25 个 P1 失败探针、14 个 P2 失败探针、6 个故意注入的失败，以及 1 个 DIALECT_MISMATCH（SQLite 方言不匹配，不是原 SQL 错误）。探针不是独立缺陷数，重复验证同一问题不得重复计为新问题；这些数字也不是全书或模型的成功率。最新运行没有审计程序异常或未解释结果，退出码仍为 1，以保留失败结论。

[完整结果 JSON](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/results.json>) · [所有失败及反例](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/failures.json>) · [逐块覆盖矩阵](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/coverage.md>) · [运行 stdout](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/stdout.log>) · [环境版本](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/environment.json>) · [复现一致性核对](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/verification.json>)

## 1. 复现入口与证据边界

从任意目录执行：

```bash
bash '/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/run.sh'
```

退出码：0＝无失败探针；1＝发现/故障反例已复现；2＝审计程序异常或结果偏离登记预期。不要把 1 改写成“全绿”。每次创建新的 `execution/runs/<timestamp>_<suffix>/`，并更新 [latest_run.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/latest_run.json>)，不覆盖历史运行。

[README](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/README.md>) 说明依赖重建和证据核验；[run_all.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/run_all.py>) 编排全部检查；[inventory.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/inventory.py>) 提取原始代码块；[依赖清单](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/requirements-audit.lock.txt>) 与 [逐文件依赖 manifest](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/dependency_manifest.json>) 记录版本、来源和 SHA-256。

本机环境为 CPython 3.13.13、SQLite 3.50.4、Apple Git 2.54.0、bash 3.2.57；实际使用 jsonschema 4.26.0、PyYAML 6.0.3、pytest 9.1.1。书稿原 `.venv` 没有 pip/jsonschema/PyYAML/pytest。本次从本机已有 uv 缓存复制 12 个发行版到局部 `deps/`，不联网安装或研究，不改原 `.venv` 和 requirements。Python 网络连接被显式禁止；子进程仅运行本地 git/bash/pytest。原生依赖与时区文件版本/hash 已登记，但没有声称跨平台容器复现。

书稿与 requirements 在每次运行前后 hash 一致，最终 Git 检查没有这两类文件的改动。没有新增 Git commit、提交 PR、push、发布或外部写入。真实 Git 教学仓库使用 index/tree 作为基线，避免以创建 commit 违反“不提交”的限制。

[局部 .gitignore](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/.gitignore>) 排除 `deps/`、`bin/`、Python/pytest 缓存及整套生成工作区；保留审计脚本、手写 fixture、manifest、JSON、日志、补丁与 SQLite 证据。启动器从保留的 `fixtures/pytest-wrapper.sh` 自动重建。没有删除任何用户数据或临时目录。

本次使用 planning-with-files 记录进度；记录仅写在授权的 execution 目录。它没有引入额外批准门，也没有改写其他审阅者的报告。

## 2. 全书覆盖分母

[inventory.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/inventory.json>) 包含每块完整原文、ID、file、开 fence 行、内容行、结束行、language、classification、字节数与 SHA-256。hash 按原始 UTF-8 内容字节计算，保留换行，不含围栏；编号按路径及出现顺序生成 B001–B120。扫描 manuscript 下全部文本文件，另登记 3 个 DOT/3 个 PNG 资产；资产不被冒充 fenced code。

| 语言 | 块数 | 实际动作 |
|---|---:|---|
| text | 93 | 8块有控制流伪代码全部做限定helper契约的忠实翻译；其余85块图/公式/结构定义不强行凑成程序 |
| JSON | 11 | 全部原样解析；其中附录 E 两块进一步用真实 validator 校验 |
| YAML | 14 | 全部原样解析；不改占位符，不擅自发明业务 schema |
| bash | 1 | 专用原书 fixture 原样尝试，保留失败与逐行退出码 |
| SQL | 1 | SQLite 原样结果为DIALECT_MISMATCH；实际执行适配与补正查询；原引擎未执行 |
| 合计 | 120 | 逐块矩阵无缺项 |

矩阵使用互斥的四类主覆盖口径：

| 主覆盖类别 | 块数 | 不能误读为 |
|---|---:|---|
| 可运行代码 | 2 | 原样通过；bash缺fixture/依赖，SQL与SQLite方言不匹配，适配结果单列 |
| 设计示意 | 93 | 全部生产可执行；含原90项及本轮补齐的3段控制流模拟，原始代码仍是示意 |
| 仅 schema 验证 | 2 | 业务正确、权限正确、证据真实 |
| 未验证 | 23 | 完全没检查；23块结构化示例原样解析成功，运行语义仍未验证 |

B014（第1章最小循环）、B078（第11章委派/合并）、B091（第20章frontier搜索）已在本轮补做忠实翻译，见4.1节。第27章 YAML 中的 `make typecheck`、`pytest tests/reminders` 没有配套原工程，未冒充执行成功。附录 B/C/D、第28–30章及5个篇导言没有代码块，共11个文件，在文件清单中明确登记为零。

全量矩阵见 [coverage.md](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/coverage.md>)，机器可读版本见 [coverage.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/coverage.json>)。矩阵逐块列出检查名、模型类型、PASS/FAIL 和限制；有模拟引用不代表原 JSON/YAML 可运行。

## 3. JSON/YAML 与附录 E：格式通过不等于约束完整

25/25 JSON/YAML 原文解析成功。JSON 拒绝重复键和非标准 NaN/Infinity；YAML 使用 PyYAML SafeLoader 并增加重复键检查，没有替换任何 `required`、`PASS|FAIL|INCONCLUSIVE` 或假 hash。PyYAML 的日期解析语义属于该解析器，未声明与所有 YAML 版本完全一致。

附录 E 两份 JSON Schema 都通过 `Draft202012Validator.check_schema` 的 Draft 2020-12 元 schema 校验。实例校验实际调用 `iter_errors`，无网络解析。共44个合成正反实例探针，35项预期得到满足、9项暴露保护缺口；另有2项元 schema 检查通过。

关键结果：

- B007 根对象只有 `$defs`，没有应用 `$ref`/type/组合约束。直接用其根验证 `{}`、`null`、字符串和数字，四者全部被接受。它是合法的定义集合；P1 指“直接拿根当 Action 验证器”的集成风险，不是 validator 或 Draft 2020-12 的错误。
- 明确使用 `#/$defs/Action`、`PolicyDecision`、`Observation` 后，所列必填字段、错误枚举等负例正确拒绝。
- Task 接受 `checks:[""]` 和未知预算字段 `wall_minutes`；Action 接受空 action_id、不可逆动作无幂等键；CONSTRAINED_ALLOW 接受无 constraints。这5个 P2 探针显示最小教学子集没有这些语义约束，不推断生产系统必定不安全。
- 第25章3个 JSON 原对象均不能直接作为附录 E Task 实例：领域合同/evidence 与 Task 协议字段不同。结果保留在 cross_contract_compatibility，作为“需要显式适配”的观察，不把不同对象类型判为错误 JSON。
- 附录 E YAML 是证据包骨架，没有给出 JSON Schema；只能认定解析成功，不能认定 hash、审批人或证据真实。

原始证据见 [structured.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/structured.json>)、[schemas.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/schemas.json>)。

## 4. 安全伪代码：忠实翻译与补正模型分开

[safety_models.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/safety_models.py>) 从原 fence 读取内容，在内存中做最小语法转换后 compile/exec：为语言无关函数补 `def`，为附录 A 顶层循环包函数；第10章的 `results=[]` 替换为支持原文方法的 Results 容器。没有在忠实控制流里补 DENY 分支、隐式 continue、异常捕获或原子锁。每个转换后的文本保存在对应 `Bxxx_translation.txt`。

策略、模型和执行器 helper 是明确的最小 deterministic doubles；例如 suspend/continue helper 采用“返回调用者”的实现。若真实实现规定这些函数不返回、executor 另行校验 capability，部分反例会被该额外契约拦住。报告验证的是原示意代码没有封闭这些条件，绝不声称供应商产品发生越权。

| 原文位置 / 对应静态审阅 | 忠实执行结果 | 需要明确的边界 |
|---|---|---|
| 附录 A B002，DENY | executor 调用0次，PASS | 原显式 DENY 分支有效 |
| 附录 A B002，审批首轮 | UnboundLocalError，observation 未赋值 | 外部响应返回后要显式转移/生成本轮 observation |
| 附录 A B002，先 ALLOW 再审批 | 两次追加同一 action 的旧 observation | 局部变量跨轮残留也可静默污染事件 |
| 第6章 B037，history R01 | DENY、requires_human=false 时 executor调用1次 | 拒绝不等于无需审批 |
| 第10章 B069，history R01 | 实际运行一项 PASS 的前置检查后，DENY仍commit 1次 | 只判断 requires_approval 不足以允许提交 |
| 第6章 B037，审批 batch | suspend helper返回后下一动作仍执行1次 | 暂停应有不返回/退出批次契约 |
| 第6章 B037，batch内取消 | 首动作触发取消后第二动作仍执行，共2次 | 循环顶端一次取消检查不足以保护每个动作 |
| 附录 A B003，顺序重复 | 强一致lookup下执行1次，PASS | 强一致、唯一键可查是实测前提 |
| 附录 A B003，提交成功后回执丢失 | TimeoutError向外传播；ledger留在EXECUTING | 原函数只处理返回“不确定”对象，未处理抛异常 |
| 附录 A B003，返回不确定对象 | 正确标UNKNOWN_EFFECT，PASS | 与抛异常路径不能混为一谈 |
| 附录 A B003，丢回执后强一致查询恢复 | 不重复执行，PASS | 查询能可靠回读已提交效果 |
| 附录 A B003，查询暂不可见后重试 | 实际调用2次 | 不可见不一定意味着未提交 |
| 附录 A B003，两个线程lookup后竞争 | barrier保证均先查无结果，实际执行2次 | insert_if_absent不是执行权/下游原子幂等 |
| 附录 A B004，取消 | 子任务取消→终止→撤证→对账→静止终态，顺序PASS | 仅验证状态模拟，非真实OS进程树 |
| 附录 A B004，恢复已CANCELLED任务 | 调用recover后回到RUNNING | 入口或resume helper需终态保护 |

完整异常名称、消息、traceback 和 effect 记录见 [safety.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/safety.json>) 与 [failures.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/failures.json>)。并发 worker 的异常通过 future.result 回传；不吞掉异常把它算通过。

补正模型另列 `corrected_simulation`：显式 DENY/未知决定拦截，审批恢复重新核对撤权与取消；SQLite target 用唯一键提交，ledger 绑定参数；回执丢失记录 UNKNOWN_EFFECT，查询不可用时暂停，重试前对账；相同 key 不同参数拒绝；取消保留已提交效果且不恢复终态。这些通过只证明补正模型在本地注入下的行为。下游原子去重是假设，不是单靠本地账本就能保证远端 exactly-once。

## 4.1. 补齐 B014 / B078 / B091：原控制流、明确 helper、有限执行

[remaining_pseudocode.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/remaining_pseudocode.py>) 对三块原文做最小语法翻译后实际compile/exec。B014与B091只加函数外壳；B078只把function改def，并将三条语言无关assert转换成Python谓词。没有往源循环插入预算扣减、break、异常捕获、finally或重试。转换文本分别保存为 B014_translation.txt、B078_translation.txt、B091_translation.txt。

[完整新增结果](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/remaining_pseudocode.json>) 逐场景记录 helper_contracts、输入预算、调用轨迹、正常返回或完整exception/traceback，共21个场景、25个探针（17 PASS、8 FAIL）。原有90个设计示意没有为了覆盖数字而额外强行执行；本轮只补这3段真正的控制流。

| 代码块 | 正常路径的明确helper契约与实跑 | 故障/终止路径的实跑 |
|---|---|---|
| B014 第1章最小loop | budget_available只读remaining>0；model每次调用扣1；validate拒绝非read；execute返回42；第二次model返回final。预算2下1次工具观察、2次模型调用后正常返回 | 零预算不调用模型；预算用尽自然退出并返回None；无效tool在execute前ValueError；工具OSError原样传播、无重试或伪造observation。model不扣预算时，在外部watchdog上限内未自行终止 |
| B078 第11章delegate/integrate | bounded用有限目标谓词；attenuate取权限交集/最短TTL；reserve显式预留；child最多一个有限操作；验证schema/producer和子任务检查；reject_unverified_or_expired必须抛异常拒绝，不能只返回false；正常合并后再过父级gate | 空验收/预算不足在spawn前拒绝；child取消、坏provenance、未通过的子结果均不合并；conflict返回RESOLUTION_REQUIRED；子通过但父gate失败返回BLOCKED。child timeout向外传播，原流程未结算未用预留预算 |
| B091 第20章frontier | select明确pop当前节点；候选为有限3项；execute逐候选检查并扣预算；verifier给hard gate与效用/成本；retain维护独立结果集合；best只选hard-pass或返回NEEDS_ESCALATION。实际排除高分但hard-fail候选，选择better | 零预算不执行分支并升级；预算1时严格execute在第2分支抛BudgetExhausted，原流程未走最终return；仅记账不拦截时3个分支仍全跑，预算1→−2；verifier异常原样传播、无伪造score；静态budget加不出队select在watchdog上限内未终止 |

正常helper自身有限；外部审计另以240个源程序line事件/2秒上限保护可能不进展的循环。B014弱契约场景记录40次模型调用后为AUDIT_ABORTED，B091弱契约场景记录30次分支执行后为AUDIT_ABORTED。**这是审计器截断，不是原程序实现了安全终止，也不把watchdog当作补正后的通过。**

新增5个P2失败对应明确的条件性契约缺口：B014预算没有推进；B078失败后未结算unused reservation；B091批次内严格预算异常没有终态返回、只记账时透支、预算/frontier均不推进时未终止。B078示例中父预算3、预留2、helper记录使用1，结算后可用额应2，实际仍1；这不是要求退还已使用成本。若scheduler本来承担自动结算/租约回收，该P2前提应由该helper契约关闭。

3个额外FAIL是主动注入的工具、child、verifier异常，标INJECTED，证明异常没有被吞掉；其传播不自动等于书稿新增P1。B014原文本来就明确不是企业Harness。本轮不将这些最小模型的表现外推到供应商、真实subagent、OS隔离或已校准预算阈值。

## 5. 静态 R02/R03 与第27章：已经实际构造反例

[additional_counterexamples.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/additional_counterexamples.py>) 和 [运行结果](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/additional_counterexamples.json>) 分别给出：

1. history R02，第10章 B068（169行）：从原状态图提取 `effect confirmed → VERIFIED_COMPLETE` 边。模拟部署实际把目标改为新版本，回执confirmed，但读回health=false；忠实图仍进入 VERIFIED_COMPLETE。前提是完成合同包含部署后健康；若合同仅要求保存记录，不能据此判错。补正模型进入 COMMITTED_BUT_UNHEALTHY 并保留已提交副作用，不伪称回滚完成。
2. history R03，第6章112–118行：按“至少一种”把已定义compensation作为重试准入。第一次真实本地SQLite写入10元后抛TimeoutError；再次写入10元；补偿函数抛ConnectionError。数据库保留两笔、总额20元，预期单次10元不成立。补偿操作存在不意味着它可用或必成功。补正分支停止于RECONCILE_OR_ESCALATE，不重放、不声称已退款。这是对文字条件的最小翻译，不冒充原书提供过支付实现。
3. products R07，第27章86行：建立真实SQLite subscriptions与invoices两表，用排序后的账单记录计算SHA-256。只将取消状态的解释改为active并登记越界路径 `src/billing/state.py`，scope_guard失败，但invoice_integrity通过；提醒队列反而有1项。账单hash前后同为 `a5d9f3b0aa737813c380731636858b197c19e46b34d4804c97a327b6726150b9`。因此原文“两项检查都失败”不是必然结果；必须另补修改账单的持久化操作或数据耦合。这里反驳的是文字蕴含关系，没有声称不存在的原实现运行失败。

第27章独立正负例的实际结果：

| 审计fixture | scope_guard | invoice_integrity | cancelled_slice | 队列数 |
|---|---|---|---|---:|
| 正常取消过滤 | PASS | PASS | PASS | 0 |
| 越界状态解释改active | FAIL | PASS | FAIL | 1 |
| 明确额外写账单 | PASS | FAIL | PASS | 0 |
| 允许目录内错误入队 | PASS | PASS | FAIL | 1 |

另测“筛选后、入队前取消”：固定筛选快照解释与入队时实时状态解释给出不同判决。该探针只说明需要定义时间语义；不能靠补上实时/原子条件，再声称原始案例已经有该条件。原书无 billing-api 源码，原有 make/pytest验收仍是未验证。

## 6. 第25章案例一：原 bash 和真实 Git/DST 案例

### 原样执行

B104原样通过stdin交给bash，工作区为本地独立clone，未补 commit、src/time 或 tests/time。

- `8f31b6e` 不存在，git cat-file退出128。
- 原执行PATH下pytest不存在，整块退出127。
- 只提供本审计真实pytest依赖后重新执行同一原文，pytest因找不到tests/time退出4，未添加测试。
- 原文三行单独执行的退出码是128、0、4。第二行git失败却被sort的0掩盖；candidate.patch与changed-files.txt均可成为0字节文件。添加pipefail的对照运行退出128。

这证明缺失环境/源码的事实，以及管道错误传播问题，不能说原书三条命令可直接运行。见 [original_bash.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/original_bash.json>) 及 commands中的原样stdout/stderr。

### 审计另建的可运行案例

预先定义的stub依次提供“硬编码可见日期”的候选和按本地民用日求UTC端点的修复。真实git diff生成patch，hash封存后在独立干净目录git apply，再用真实pytest执行。没有LLM供应商调用，也没有真实支付服务、日期库升级或PR。

| 阶段 | 两条DST目标 | 普通日回归 | 隐藏/变形测试 |
|---|---:|---:|---:|
| 合成故障基线 | 0/2 | 3/3 | 未作为初始通过声明 |
| 硬编码候选 | 2/2 | 3/3 | 1/17；16项失败 |
| 补正候选 | 2/2 | 3/3 | 17/17 |

隐藏测试包含邻近年份、Berlin、Lord Howe半小时DST、连续窗口无缺口/重叠、fall-back两个fold。这里假设扣款窗是一个当地民用日对应的半开UTC区间；原书没有详细支付业务口径，故不能外推到所有账务语义。没有复现示例中的482条回归；只做AST语法检查，没有冒充项目lint或secret scan。目录隔离是逻辑隔离，同一OS用户不是安全vault。

补正patch SHA-256：`8753abb0c54b24705cabc60490a910cf421e18bee1888e08b27831446789bc39`；基线Git tree：`8aa3892ed5a4b578b19d11742c9c33893d782951`。见 [repository_case.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/repository_case.json>)、[修复补丁](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/repaired.patch>)。

products R06的两个追加实跑：

- 新增未跟踪 `window_helpers.py`，工作区5项测试全过；原git diff导出的patch只有tracked导入变更，干净apply后pytest退出2，ModuleNotFoundError。新文件没有被悄悄stage以掩盖问题。
- 先封存硬编码候选，再把工作区改成补正代码，工作区22项测试通过；封存patch与之前独立验证的硬编码patch完全相同，隐藏测试仍失败。source hash明确不同。该反例有“封存后发生修改”这一条件，证明三行shell本身没有绑定输入；正文要求的clean checkout协议能够抓住它。

## 7. 第25章案例二：真实 SQL 与手算

B107在SQLite原样执行报 `OperationalError: near "SYSTEM_TIME": syntax error`。该项明确标为 **DIALECT_MISMATCH**，表示SQLite不支持这段BigQuery时间旅行语法，不据此声称原SQL错误，也不再计为P2缺陷。

主代理已核验[BigQuery官方Query syntax](https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#for_system_time_as_of)，本执行代理只读取其[本地抓取材料](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/bigquery-time-travel.json>)，未另行联网。`.text`第419行起支持FOR SYSTEM_TIME AS OF，第437–440行规定timestamp不能在未来或早于当前超过7天。抓取文件SHA-256为 `736dd157d5fd309f64b600eb2a9af7730b2edb18198dca9db336de62428125f4`，来源和读取结果已写入sql.json的bigquery_documentation。

书中固定2026-08-03 as-of到本次2026-09-19相隔47个日历日，超出7天窗口。因此直接依赖标准time travel的原查询不能在本审计日重新访问该历史版本；长期复跑必须预先物化或归档快照并记录对应数据版本。该判断是官方文档约束与固定日期的推导，**没有实际BigQuery账号或原引擎查询执行**，不能升级为“原引擎验证通过/失败”。

适配层仅去掉时间旅行子句和DATE字面量关键字；通过真实attached `semantic` 数据库中的view实现固定as-of。版本区间为UTC文本 `valid_from <= snapshot < valid_to`，开放终点为NULL。聚合、减法、COUNT DISTINCT、HAVING保持原样。原查询、适配查询和补正查询分别保存。

数据集88行，包括20/19账户组、精确重复事件、NULL refund/revenue/account_id、CN/US、5月/6月/7月/8月/月末日期，以及在snapshot瞬间和后来生效的退款回填。货币使用已换算的整数CNY，不验证汇率转换或小数舍入。month要求规范化为月初日期；若存实际交易日，原IN过滤会漏掉7月31日，这必须作为semantic model前提。

| 固定快照2026-08-03 02:00 UTC的分组 | 可手算原查询金额 | distinct账户 | 披露 |
|---|---:|---:|---|
| 6月GD pro | 20×90＝1800 | 20 | 是 |
| 7月GD pro | 18×90＋80＋NULL＋重复90＋匿名50＋NULL＝1840 | 21 | 是 |
| 7月SH basic | 20×25＝500 | 20 | 是 |
| 7月BJ basic | 19×50＝950 | 19 | 否 |

披露合计4140、未抑制合计5090，相差950。products R05已通过真实SQL复现；若财务总额包含全部分组，就必须在抑制前对账，并显式说明受限残差/披露覆盖，不能拿被抑制数当零或舍入差。该950不应直接成为真实公开数据的披露建议。

其他反例：

- 重复事件贡献90两次，但账户只算一次；COUNT DISTINCT不去重金额。P1前提是上游可能含无效重复；若semantic view已有唯一性保证，该前提应写明。
- NULL refund使100−NULL变NULL，SUM忽略该行。如果业务把NULL解释为0，原查询会漏100；原文未规定NULL口径，P1是条件性口径风险。
- NULL account仍贡献50元，却不计人数；全NULL收入的20人组可通过HAVING而金额仍NULL。这2项为P2边界观察。
- 7月GD在01:59:59、02:00:00、03:00:00分别为1850、1840、1700。最后变化是退款−50和重复旧版本到期−90共同造成，不能只报−50。
- 模拟gateway对不同snapshot真实抛错且执行查询数为0；固定snapshot路径执行1次，产出预期结果。

补正查询单列假设：按event/version去重、NULL退款视0、排除无法识别账户、NULL收入隔离待处理。补正7月GD＝18×90＋80＋100＝1800，披露总额4100，完整口径5050，仍需950抑制桥接。这不是替原查询悄悄修正后宣称成功，也没有自动获得业务负责人对这些口径的批准。

证据：[SQL结果与假设](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/sql.json>)、[88行fixture](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/sql_fixture_rows.json>)、[原SQL](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/sql_raw.sql>)、[SQLite适配](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/sql_sqlite_adapted.sql>)、[补正SQL](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/sql_corrective_assumptions.sql>)、[实际semantic数据库](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/semantic.sqlite>)。财务叙述审核、真实IAM、FX、parquet发布和完整匿名化保证未验证。

## 8. 第25章案例三：受控进化 gate

[evolution_case.py](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/evolution_case.py>) 实际运行可信评估逻辑、冻结字段检查、激活检查、分母完整性、sealed访问次数以及发布/回滚状态机。数据是预先生成的10任务×3重复＝30条deterministic stub输出，不是模型能力实验。原始每条trial、失败重试次数和成本单位保存在 [evolution_trials.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T102120Z_30xh1oov/evolution_trials.json>)。

| 候选 | 成功/预注册分母 | 完成试次口径 | 后果 |
|---|---|---|---|
| baseline | 24/30＝80% | 24/30＝80% | 基线 |
| 分母作弊候选 | 18/30＝60% | 18/20＝90% | 忽略10次最终TIMEOUT会制造“提升” |
| 合成候选 | 28/30＝93.33% | 28/30 | 仅通过预注册的玩具非回退gate |
| 合成canary | 29/30＝96.67% | 29/30 | critical切片出现1次失败，仍触发回滚 |

10个超时trial已标重试2次仍失败，保留全部分母；删除其日志后，gate通过预注册trial ID发现缺项并拒绝。修改冻结evaluator、缺少activation、第二次访问sealed test均被拒绝。未激活trial不从主分母删除。

release controller先拒绝作弊候选，再进行模拟shadow/canary；在途任务保持旧bundle。发生关键切片退化后停止新候选流量，并回到完整 `harness-42/model-12/memory-87/policy-9/evaluator-5`。这是内存控制面模拟，没有部署或真实生产流量。

Wilson区间在JSON内仅作算术输出：脚本化重复任务不满足拿它推断真实模型效能的前提。未运行2×2 Model×Harness真实实验，未估计交互/主效应，未校准预算/成本阈值，未证明统计显著性、生产安全率或因果收益。任何阈值只是本模拟的规则。书中240/228和5%生产canary没有被当成实测数据。

## 9. 所有失败探针索引

以下表覆盖正式运行46项FAIL。完整输入、输出、traceback和severity见 failures.json；P1是需优先修正的条件/控制流/表述风险。INJECTED表示主动故障注入（含验证器检出或原流程传播异常），不是额外的书稿漏洞。DIALECT_MISMATCH单列兼容性结果，不计原SQL缺陷。

| 等级 | FAIL检查名（同问题可有多个探针） | 数量 |
|---|---|---:|
| P2 | Task_empty_check_string_rejected；Task_unknown_budget_field_rejected | 2 |
| P1 | Definitions_root_rejects_invalid_0 / _1 / _2 / _3 | 4 |
| P2 | Irreversible_requires_idempotency_key；Action_empty_id_rejected；Constrained_allow_requires_constraints | 3 |
| P2 | bash_original_directly_runnable；bash_with_pytest_source_tests_exist | 2 |
| P1 | bash_pipeline_propagates_git_failure | 1 |
| DIALECT_MISMATCH | SQL_raw_SQLite（SQLite不支持，非原SQL错误） | 1 |
| P1 | SQL_suppressed_groups_reconcile_to_finance_without_bridge；SQL_DUPLICATE_money_not_doubled；SQL_NULL_refund_preserves_100_revenue | 3 |
| P2 | SQL_NULL_account_excludes_money；SQL_k_gate_guarantees_numeric_revenue | 2 |
| P1 | A_approval_first_observation_defined；A_approval_does_not_reuse_prior_observation | 2 |
| P1 | CH6_DENY；CH6_approval_batch；CH6_cancel_in_batch；CH10_DENY_zero_commit | 4 |
| P1 | A_lost_response_exception_normalized；A_lost_response_marks_unknown；A_stale_lookup_setup_timeout；A_retry_with_stale_lookup_exactly_once；A_concurrent_lookup_then_execute_exactly_once | 5 |
| P1 | A_recover_terminal_cancelled_does_not_resume | 1 |
| P1 | R02_confirmed_effect_failed_health_not_verified_complete；CH6_compensation_alone_safe_retry_when_receipt_lost | 2 |
| P1 | CH27_claim_scope_and_invoice_both_fail_from_source_edit | 1 |
| P1 | git_raw_diff_captures_untracked_required_newfile；git_sealed_patch_and_tested_input_are_same | 2 |
| INJECTED | DST_baseline_visible_contract；DST_overfit_hidden；evolution_completed_only_ranking_truthful | 3 |
| P2 | B014_static_budget_source_terminates | 1 |
| P2 | B078_timeout_releases_unused_reservation_in_source | 1 |
| P2 | B091_mid_batch_budget_exhaustion_graceful_return；B091_outer_budget_guard_prevents_batch_overspend；B091_static_frontier_budget_source_terminates | 3 |
| INJECTED | B014_injected_tool_fault_unhandled；B078_injected_child_timeout_unhandled；B091_injected_verifier_fault_unhandled | 3 |
| 合计 | 25个P1＋14个P2＋6个注入失败＋1个方言不匹配 | 46 |

## 10. 复现质量与未覆盖范围

本轮先只定向执行新增部分，然后按要求仅进行1次完整总跑。与上一版20260919T095940Z_b_il6ikt相比，原有147条检查的名称/状态/模型/来源未变；SQL_raw_SQLite仅severity从P2改为DIALECT_MISMATCH，核验文件显式登记。新增25项不被跨运行比较冒充重复验证。既有SQL快照结果、进化指标、Git候选hash与判决一致。附加证据核验检查了120行矩阵和441个产物hash，并确认应忽略的生成依赖已忽略、必要证据未被忽略；[verification.json](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/verification.json>) 的mismatches为空。程序自身日志、子命令stdout/stderr和失败异常都保留。

首跑 `20260919T095015Z_z5_rc699` 有一项审计自身手算错误：将后来快照预期写成1790，漏掉重复行同刻到期的−90，实际应1700。该次以exit2保留；后续只修审计预期，未改原查询/正文。第二轮曾把新增健康探针命名为R03，正式运行已按静态报告改为R02。早期环境探测还发现bundled runtime同样缺依赖，最终使用本机缓存；没有隐去这些过程问题。

未验证项包括：23个结构化片段的运行语义、供应商真实模型/API/协议、BigQuery原引擎执行、原生产仓库与数仓、真实审批主体/签名/租户隔离、操作系统进程树取消、服务重启和真实杀进程恢复、streaming重连、compaction、模型/工具升级迁移、MCP运行和多Agent orphan处理、金融业务口径、全文经验性/产品事实、2×2效果及生产发布。正文的设计图和接口草图不应因本次有限模拟被升级为生产就绪实现。

建议优先修订拒绝/审批分支、未知副作用和并发提交、提交后的业务验收、补偿准入条件；其次补全候选封存/新文件/干净验证协议，明确SQL语义前提与抑制对账，并改正第27章“两检查都失败”的断言。本文只交付执行证据与修改建议，没有修改书稿。

# 执行审计发现

- 附录 A 审批分支返回后未赋 observation；需验证首轮未定义、后续轮次复用旧 observation。
- 第 6 章 loop 只区分 requires_human，DENY 若为 false 将落到 execute；需忠实模拟验证。
- 第 25 章 SQL 含 FOR SYSTEM_TIME AS OF、TIMESTAMP/DATE 字面量，不能假定 SQLite 原样支持。
- 第 25 章 bash 引用虚构 commit 8f31b6e 及 tests/time；原样 fixture 不得补这些对象以伪装开箱运行。
- 附录 E 第二块只有 $defs，须分别校验根 schema 及明确选中的各 $defs。
- 现有顶层 audit 计划由其他工作拥有，本任务不修改。

## 已实测结论

- 120 fences，41 markdown，11无代码文件；25 JSON/YAML解析PASS；2元schema PASS，44实例探针中9保护缺口（含根$defs接受任意实例）。
- 忠实翻译复现DENY落执行/提交、审批undefined/旧observation、batch取消与审批漏停、回执丢失留EXECUTING、lookup/execute并发双写、cancelled可被resume。
- 静态history R02：confirmed但health=false仍VERIFIED_COMPLETE；R03：SQLite重复扣款20元，补偿服务ConnectionError；P1反例均附具体适用条件。
- 原bash确无revision/code/tests；git|sort掩盖失败；untracked依赖未入patch导致clean pytest退出2；patch/test输入漂移复现。
- SQL原样SQLite语法失败。88行适配原语义：披露4140、全量5090、抑制950；NULL与重复风险为显式条件性探针。
- 第27章仅改状态解释：scope FAIL、invoice hash PASS、取消提醒仍入队；“两项都失败”须额外持久化假设。实时取消TOCTOU探针只报歧义。
- 最终运行147探针109 PASS/38 FAIL。最后两次147个判决、SQL快照、进化指标、patch结果一致；不是模型性能复现。
- deps/bin和生成完整仓库已局部ignore，依赖manifest与必要结果日志保留；无正文变动。

## 追加三段控制流后的最新结论

- B014：动态预算正常终止/零预算零动作；工具异常未被吞；无预算推进时外部watchdog中止（非原循环终止）。
- B078：缩权、预留、子/父验证、冲突和取消分支实跑；timeout原样传播，在本helper无自动结算契约下unused reservation未释放。实际使用1不应被退还。
- B091：pop frontier +逐分支预算契约下正常选hard-pass候选；仅记账预算1→-2；严格helper阻止透支但异常越出循环；不推进的helper组合触发审计watchdog。
- 本轮21场景25新增探针，17PASS/8FAIL（5P2契约缺口+3注入故障）。最终总跑一次，172=126PASS+46FAIL；源控制流未补break/try/finally/预算扣减。
- 主代理BigQuery官方抓取在.text419/440确认语法与7日回溯限制；SQLite失败只标DIALECT_MISMATCH。Aug3→Sep19为47日，需物化/归档快照。无原引擎实跑。
- 120矩阵：设计示意93（含全部8段有控制流伪代码受控翻译）、仅schema2、运行语义未验证23、可运行代码2。已有147判决与SQL/Git/进化结果无变化；25新增单列。

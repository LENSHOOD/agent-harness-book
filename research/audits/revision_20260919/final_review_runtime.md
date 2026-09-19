# 独立合并前运行时审查（2026-09-19）

结论：当前快照暂不放行。发现2项P1、5项P2，均有本地可复现输入或确定的实例校验结果。现有99项结构/schema检查仍通过，直接调用的19个现有正文控制流测试案例与23个现有runtime顺序测试案例也通过；这些通过没有覆盖下面的组合路径。没有修改任何正文、examples、测试或发布脚本，唯一写入是本报告。

审查采用review技能的控制流、枚举传播、竞态和反例核验方法。按用户授权覆盖9个指定文件，另外只读测试fixture入口。未运行技能的自动修复、联网、额外日志或外部代理调用。实践篇不在本轮修改或自审范围内。

## 发现

### F01｜P1｜UNKNOWN后可以用新key继续同一任务，并把待对账状态覆盖掉

置信度10/10。定位：`examples/src/runtime.py:119`、`:127`、`:160`、`:174`，以及`:224`的任务状态归并。对照第6章第116行“无法确认时暂停并升级”及附录A第86行的未知结果停止分支。

实跑原Runtime方法：第一个Action已在Target提交，故意丢回执，返回UNKNOWN，任务变为NEEDS_RECONCILIATION；直接提交同一任务的第二个Action，仅更换action_id与key，仍返回COMMITTED。结果是两个外部效果、spent=2、账本为`[UNKNOWN, COMMITTED]`，任务却变成VERIFYING。

```text
submit(a1, ALLOW, lose_receipt=True) → UNKNOWN
submit(a2 with new key, ALLOW)       → COMMITTED
task: NEEDS_RECONCILIATION → VERIFYING
ledger: [UNKNOWN, COMMITTED]; target effects: 2
```

这不是同键重试重复执行的问题，目标库去重仍有效。缺口在于同一任务已应暂停，却能通过新的逻辑动作入口继续写入；后一动作的结果还掩盖了待对账状态。若以后明确支持独立动作继续运行，需要依赖关系和局部暂停合同；当前单任务参考模型没有这样的判定。

最小修法：在submit的同一控制库事务内，允许查询已有动作结果，但对新动作检查未解决的UNKNOWN/EXECUTING记录并停止调度；至少UNKNOWN不能仅靠task.state过滤，因为该字段已可能被其他结果覆盖。任务状态按整个账本中的未决动作归并，不能仅用最近完成的一个动作设置VERIFYING。若需要保留当前“多个独立动作并行”的教学测试，明确并行准入与UNKNOWN后的暂停边界，不必取消原子预算测试。

为什么测试漏：`test_stale_or_missing_reconciliation_evidence_never_replays`只重交同一个action/key；`batch`遇UNKNOWN会break，但公开的submit入口仍可单独调用。新增回归应在丢回执后提交不同key，断言Target仍只有原效果、预算不增加、任务仍待对账；重启后同样检查。

### F02｜P1｜底层新增PENDING，两个上层循环只阻断UNKNOWN_EFFECT

置信度9/10。定位：附录A第119—120、131—132行会返回PENDING；同附录第86—88行、第6章第244—246行只判断UNKNOWN_EFFECT。第10章第222—223行已经同时处理两者，说明PENDING确属正常协议结果。

已把当前第6章run_turn和当前附录A的commit_effect_safely真实提取、编译并接在一起。helper约定为：第一个effect被另一执行者持有，`try_claim_effect`返回None；第二个动作允许执行；模型第一轮给出这两个顺序动作、下一轮停止。未改两个函数内部控制流，得到：

```text
OBSERVATION:first:PENDING
TARGET_EXECUTE:second
OBSERVATION:second:OK
return: TURN_STOPPED
```

附录A循环单独接收同样的PENDING，也继续请求并提交了下一动作。对于“第一步结果成立才能做第二步”的顺序任务，这会在前置效果未确认时执行后续写入。此发现不要求停止另一个已获授权的在途请求，也不声称目标幂等失效；要求的是本地调用者不能把PENDING当成可继续推进顺序工作的普通结果。

最小修法：两个循环都在PENDING时返回明确的等待/对账状态，并保存待处理动作；UNKNOWN_EFFECT仍进入对账。若确需继续无依赖动作，应显式检查依赖，而不是默认continue。恢复不能把PENDING直接解释为安全重试。

为什么测试漏：第6章的`effect_mode`只有ok/unknown/exception；附录循环只覆盖ALLOW、DENY、审批。低层commit测试虽覆盖查询不可用→PENDING，却没有把该结果送回上层。增加两段真实抽取函数的连接测试，比再补一个只检查helper返回值的断言有效。

### F03｜P2｜迟到对账会把已确认账本倒写成UNKNOWN，任务仍为COMPLETE

置信度10/10。定位：`examples/src/runtime.py:200`—`:221`，尤其`:218`无条件更新；`:225`—`:227`保留终态，导致任务与账本脱节。

可复现的确定性交错：先制造UNKNOWN；对账者A取得陈旧结果后尚未写库，对账者B已从权威目标确认COMMITTED，随后完成检查将任务置COMPLETE；A再写入自己的UNKNOWN。最终原方法返回：

```text
B reconcile: COMMITTED
B complete: COMPLETE
A late reconcile: UNKNOWN
final task: COMPLETE; final ledger: UNKNOWN; target effects: 1
```

复现用lookup回调嵌套另一次reconcile精确安排合法交错，不靠睡眠，也没有手写SQL强改状态。现有每个事务本身仍原子，但查询发生在事务外，旧观察结果没有版本约束。没有复现重复付款；复现的是已确认事实被覆盖及“完成必须无未知效果”的不变量破坏。

最小修法：对账回写时重读行，COMMITTED结果不因迟到或非权威查询降级；使用版本/CAS或带旧状态条件的更新，竞争失败后返回实际持久状态。其他异步结果回写也应遵守同一单调规则，并在同一事务内归并任务状态。

为什么测试漏：现有并发测试覆盖多个submit抢同一key及预算竞争；对账测试都是串行。增加“慢旧对账／快确认对账／完成”的交错，断言账本保持COMMITTED、迟到调用返回当前权威状态且不推翻完成证据。

### F04｜P2｜旧批准能被不同action_id沿用，执行身份与账本身份不一致

置信度10/10。定位：`examples/src/runtime.py:121`—`:135`、`:147`—`:148`、`:178`—`:189`。对照附录A第104行及第6章第260行要求批准绑定原action_id。

实跑：a1申请审批并获得批准；随后保留key、参数、租户、资源与费用，只将action_id改成`new-action`再submit。策略收到`("new-action", approved=True)`，Target执行成功；账本action_id及payload仍是a1。没有增加金额、改变资源或跨租户，因此不将其夸大成权限扩大，但它确实打破“恢复原待执行动作”的身份绑定，并使审计记录错配。

最小修法：审批恢复时要求调用者action_id等于持久行的action_id，并从封存payload恢复原动作；ToolTry继续沿用这个身份。若允许新action_id作为同一逻辑操作的别名，需要明确别名映射，不能静默继承旧approved标志。已完成效果的只读去重查询与待审批动作恢复可分别处理。

为什么测试漏：`test_runtime_key_and_action_identity_are_bound`的changed集合含args/target/tenant/cost/key，唯独没有action_id，而且在COMMITTED后才测；审批绑定测试只改变参数。补“批准后换action_id”和“未批准时换action_id”两例。

### F05｜P2｜附录E合法的PolicyDecision直接进入附录A会异常，现有double绕过了字段约束

置信度10/10。定位：附录A第73行读取`decision.reason`，第80行无条件读取`decision.constraints`；附录E第66—80行只定义可选reason_code和constraints。`test_manuscript_flow.py:112`的double总是额外注入`reason`及空constraints，而`check_examples.py:131`—`:133`接受没有这两个字段的ALLOW/DENY。

以下两个实例均实际通过当前PolicyDecision schema；按字段直接解码为SimpleNamespace后，调用当前附录A循环：

```json
{"action_id":"a1","decision":"DENY","policy_version":"p1"}
```

返回`AttributeError: ... no attribute 'reason'`，拒绝Observation未落下。

```json
{"action_id":"a1","decision":"ALLOW","policy_version":"p1"}
```

返回`AttributeError: ... no attribute 'constraints'`，合法允许动作未执行。即使DENY补上`reason_code`也不会创建`reason`。若将测试double当wire实例验证，它多出的reason会被additionalProperties拒绝，空constraints又违反minProperties=1。

这不是DENY越权执行；两例均未执行Target。问题是本书声称字段一致、却没有给出所需内部对象适配/default约定，合法消息不能沿示例控制流走通。

最小修法：循环使用reason_code并为省略原因提供稳定默认；普通ALLOW的内部constraints可归一化为空对象，但CONSTRAINED_ALLOW必须保留非空限制与可执行性检查。可以由显式适配器提供这些默认属性，不必把默认字段强塞回wire schema。关键是让测试先校验真实PolicyDecision字典，再经同一适配路径运行，覆盖缺省字段。

为什么测试漏：结构测试与控制流测试各用一套对象，前者只证明wire实例合法，后者使用不符合该wire schema的便利属性。属于跨层集成缺口；本轮新增additionalProperties/minProperties限制使旧便利double更不能代表合法消息。

### F06｜P2｜一次DENIED永久污染完成门，即使后续合法结果已满足合同

置信度9/10。定位：`examples/src/runtime.py:196`允许DENIED后继续batch，`:258`—`:259`却要求所有历史ledger行都是COMMITTED。

实跑先拒绝a1，后用允许的a2完成业务效果，并给出最终结果及后置健康检查True：

```text
submit(a1, DENY)       → DENIED
submit(a2, ALLOW)      → COMMITTED
complete(all True)    → VERIFICATION_FAILED
ledger: [DENIED, COMMITTED]; target effects: 1
```

这是完成假阴性，不是越权或错误放行。若参考模型刻意定义“任一历史提案被拒绝则整个任务永不可成功”，应明示这种严格合同并解释为何batch继续；目前正文将策略拒绝作为可反馈和调整方案的普通结果，读者会合理期待合法替代方案可完成。

最小修法：完成门分别检查必需业务结果、未决效果和历史拒绝。保留DENIED审计记录，但不要要求拒绝提案最终也产生COMMITTED；在当前受限例子中，可以允许已经结束且未执行的拒绝记录存在，同时继续阻断UNKNOWN/EXECUTING/待审批，保留非空必需检查和已达成所需效果的条件。不要简单删掉拒绝行，也不要把所有失败行一律忽略。

为什么测试漏：`test_deny_never_commits`只检查零副作用，`test_committed_is_not_business_complete`只从无拒绝的干净账本开始。增加先拒绝、再合法完成的组合测试，并由合同明确拒绝是否自身触发不可豁免硬门。

### F07｜P2｜Task身份字段仍接受纯空白；元schema及现有实例检查全部通过

置信度10/10。定位：附录E第16—18、34行；`publishing/scripts/check_examples.py:103`—`:104`。

把合法Task的task_id、tenant、contract_version、commit_authority分别替换为`" \t\n"`，当前Draft202012Validator对4个实例全部返回True。它们只有minLength=1，没有同文件Action/PolicyDecision所用的非空白pattern。没有据此推断鉴权可被绕过；确定的是协议入口会接受无法作为有效标识的值。

最小修法：4处身份字符串加入与其他ID相同的`pattern: "\\S"`，实例负例同时覆盖空串和纯空白。若平台另有规范化步骤，应明确在schema检查之前执行并拒绝归一化后的空值。此项为旧约束残留，不是本次新引入的字段；本轮收紧字符串约束时没有补齐。

为什么测试漏：Task身份只测`""`；同检查器对Action已经同时测空串与`"  "`。`check_schema`只验证schema本身合法，不会替应用补上这条约束。

## 实际验证方法与边界

使用本地CPython 3.13.13及已有审计依赖，以`-B`关闭字节码写入；没有联网安装。SQLite探针使用URI共享内存数据库和保活连接，原Runtime、Target、transaction方法与SQL不变，只把connect的存储位置切成内存。上述迟到对账按确定性嵌套调用安排两个调用者的交错，没有模拟真实跨进程崩溃。

从当前fence通过`examples/src/manuscript.py`提取并编译函数，只有工具原有的声明语法转换；额外探针没有修改原控制流。所有evidence回调都指向内存字典，不写JSON或临时测试库。

| 已执行检查 | 结果与限制 |
|---|---|
| 原`check_examples.check()` | 99项，exit_code=0、failures为空；包括实际根$ref、子类型$ref、元schema和正反实例验证。没有调用会启动落盘fixture的CLI main。 |
| 原`test_manuscript_flow.py`测试函数及parametrize案例 | 19/19直接调用通过，内部pytest.raises等断言保留；不是重新跑完整pytest runner。证据仅在内存。 |
| 原`test_runtime.py`顺序测试函数及参数案例 | 23/23直接调用通过；model fixture按原函数创建，数据库转为内存。 |
| 3个原并发测试 | 已读源码，本轮未重跑：同键12worker、两个控制库、并发预算。避免把共享内存的锁行为冒充文件数据库或额外生成磁盘证据。 |
| 新反例 | F01/F03/F04/F06调用原Runtime得到所列结果；F02连接原抽取函数；F05实际校验合法策略实例后送入原循环；F07实际校验4个空白身份实例。 |

未发现原“DENY仍执行”、审批分支复用上一轮observation、COMMITTED直接等同业务完成、根schema仅有$defs导致任意对象通过等旧缺陷仍按原路径存在。对应控制流和测试现在已显式处理：第6章第227—235行、附录A第69—75行、第10章第222—230行、附录E第47行。此确认不取消上面新组合反例。

以下不作为缺陷计数：

- Runtime明确是一个控制库对应一个任务的教学模型；没有完整Task/Attempt多租户协议或分布式租约fencing，不据此要求生产实现。正文Task/Attempt/Action命名与ToolTry含义已对齐，F04只针对实际批准身份错配。
- Target的唯一key与参数比较在同一事务内，确有原子去重；本地账本与Target非同一事务也是已说明的模型前提。
- 取消不能撤回已发送的效果、恢复采用保守对账、ABSENT不自动重发，均是已说明的边界，不算功能缺失。
- `mark_executing_if_owned`、`resume_from_reconciled_state`、提交时撤权检查等helper的生产实现未给出；正文已经声明必要的条件写入/授权职责，本轮不因函数名存在就推断这些保证已实现，也不把未实现生产后端反过来算漏洞。
- 第10章`verify_target_state`抛异常的路径、完成门与取消的真实后端竞争未在现有double中实测。是否由helper归一化需明确，但没有仅凭可注入一个任意异常就新增P1。正文已承诺的显式返回路径与未实现后端分别评价。

## 最小复现入口：内存Runtime

在仓库根目录的示例依赖环境中，将下面Python送入`python -B -`即可，不建立文件。它复现F01、F03、F04、F06；每个case使用独立共享内存库，Target仍是另一数据库。

```python
import sys, sqlite3
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
sys.path.insert(0, str(Path("examples").resolve()))
from src.runtime import Runtime, Target, Action

connect = sqlite3.connect
keepers = []
def model(label):
    paths = [f"file:review-{label}-{k}?mode=memory&cache=shared"
             for k in ("control", "target")]
    keepers.extend(connect(p, uri=True) for p in paths)
    return Runtime(paths[0], Target(paths[1]))

ALLOW = lambda *_: "ALLOW"
APPROVAL = lambda a, approved: "ALLOW" if approved else "REQUIRE_APPROVAL"
a = Action("a1", "key1", "account/one", {"amount": 7})
b = replace(a, action_id="a2", key="key2")
with patch("src.runtime.sqlite3.connect",
           side_effect=lambda *a, **kw: connect(*a, **dict(kw, uri=True))):
    r = model("unknown")
    print("F01", r.submit(a, ALLOW, lose_receipt=True), r.submit(b, ALLOW),
          r.snapshot()["task"]["state"], r.target.count())

    r = model("late")
    r.submit(a, ALLOW, lose_receipt=True)
    original = r.target.lookup
    def lookup(action, mode="fresh"):
        old = original(action, "stale" if mode == "slow" else mode)
        if mode == "slow":
            assert r.reconcile(action, "fresh") == "COMMITTED"
            assert r.complete({"health": True}) == "COMPLETE"
        return old
    r.target.lookup = lookup
    print("F03", r.reconcile(a, "slow"), r.snapshot()["task"]["state"],
          r.snapshot()["ledger"][0]["status"])

    r = model("approval")
    r.submit(a, APPROVAL)
    r.approve(a.key, a.binding)
    print("F04", r.submit(replace(a, action_id="new-action"), APPROVAL),
          r.snapshot()["ledger"][0]["action_id"])

    r = model("denied")
    print("F06", r.submit(a, lambda *_: "DENY"), r.submit(b, ALLOW),
          r.complete({"contract_final_result": True, "health": True}))
for connection in keepers:
    connection.close()
```

本快照预期输出：

```text
F01 UNKNOWN COMMITTED VERIFYING 2
F03 UNKNOWN COMPLETE UNKNOWN
F04 COMMITTED a1
F06 DENIED COMMITTED VERIFICATION_FAILED
```

## 发布门建议与快照

先处理F01、F02，并补连接/组合路径回归，再处理其余已复现缺口。F06可以通过明确且合理的教学合同限制处置，不能在没有解释的情况下把完成假阴性记成通过。重跑应针对最终代码及最终fence，不继承旧99项或上一轮58项的通过数字。本报告不给生产就绪或供应商安全背书。

审查快照SHA-256如下。并行修改若改变这些文件，须复核受影响发现与行号，而不能直接继承本结论。

交付前再次核对9份源码，摘要均未改变；直接执行本报告内存复现代码，退出0，四行输出与所列结果逐字一致。这里的退出0表示成功复现缺陷，不是发布门通过。

| 文件 | SHA-256 |
|---|---|
| manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md | 4dd7a9f77cfcaac13896fea9a7139cbb4bf834910a161927a413dac07b5f1cdb |
| manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md | c18bd31b8c7e2308593312d4dd52de37317b268e1b5d4fc5a3b4fcb1b2314907 |
| manuscript/appendices/A_core_contracts_and_pseudocode.md | 20056c256bd4f2fc629f6999512c62351c73aaa52fc0486c1f9bc981aadf8193 |
| manuscript/appendices/E_machine_readable_contracts.md | 72be64fc0651084d05e63729f111a809b5f120a93f0ff1fe6a6202f23c2bc679 |
| examples/src/runtime.py | 7b766cdaa06f31ea2a9ab0698873612777840cee1ab0bbd1f4880e416eee69df |
| examples/src/manuscript.py | 6af970ec7b8422bc5bbefe7497ce5305cfc93ef322a8a4396bf220e6cb1c06e0 |
| examples/tests/test_runtime.py | ec31b4074e88fa899c5080028f62f307a96084586bc74eedec4ff4efbde76238 |
| examples/tests/test_manuscript_flow.py | 48e15c9f699712b1dfcef2231eb3b8078a08e4ecef1a9985dad52e1e830eeb43 |
| publishing/scripts/check_examples.py | 27d3821a9c59c6f95f45071ed7427e3af3e170d7af4c48d26dedd3df813d5c26 |

## Recheck：F01—F07定向关闭复核（2026-09-19）

最新结论：F01—F07在当前教学协议与本地参考实现范围内全部关闭。本节更新前文首次审查的“暂不放行”结论，首次发现、旧源码摘要与旧反例输出原样保留。当前复核没有发现这些修复仍留下需要阻断的实质缺口；这只解除本报告七项问题的阻断，不替代主代理最终全套测试或发布验收。

本轮按用户要求只复核这七项修复及对应测试。读取`disposition_execution.md`第79行起的处置说明后，核对当前实现和断言，没有仅凭处置说明或另一代理的通过数字关闭问题。新增读取`examples/src/policy.py`与`examples/tests/test_runtime_review_regressions.py`是因为它们直接承载F05及F01/F03/F04/F06修复，未扩展到新审查范围。

### 逐项判定

| 项目 | 当前修复落点 | 本轮核验结果 |
|---|---|---|
| F01｜关闭 | `runtime.py:129`—`:138`、`:246`—`:263` | 新动作在UNKNOWN存在时，于授权、intent创建和预算消耗前停止。已有EXECUTING默认返回PENDING；显式独立且目标不重叠的调用仅允许在UNKNOWN出现前准入。状态从全账本归并。`test_F01_unknown_blocks_new_key_and_preserves_budget`的重启/不重启两例、顺序PENDING一例、两个在途完成顺序均通过，UNKNOWN未被另一COMMITTED掩盖。 |
| F02｜关闭 | 第6章`:244`—`:247`、附录A`:86`—`:89`；`test_manuscript_flow.py:484` | 两个上层循环收到PENDING均立即返回WAITING_FOR_EFFECT，UNKNOWN_EFFECT仍对账。连接当前底层函数和当前上层函数的4例覆盖两种上层×lease忙/lookup不可用；保存第一动作及观察，第二intent与目标执行均未发生。抽取器没有为这些测试额外重写原分支。 |
| F03｜关闭 | `runtime.py:187`、`:232`、`:238`—`:243` | submit与reconcile共用条件写回；只有EXECUTING/UNKNOWN可被结算，迟到结果不能把COMMITTED降级，且返回重新读取的持久状态。原“旧对账读完→新对账确认→complete→旧写回”及“确认完成后迟到submit抛超时”两种交错均通过，保留COMMITTED/COMPLETE。 |
| F04｜关闭 | `runtime.py:123`—`:125`、`:144`—`:146` | 同key要求同action_id，恢复从持久payload重建原动作。未批准/已批准时替换action_id均在策略调用前被拒绝；获批原动作仍能正常恢复。没有通过放宽原断言来接纳身份别名。 |
| F05｜关闭 | 第6章`:226`、第10章`:213`、附录A`:66`、`:73`；`policy.py:7`—`:18` | 三处均调用wire适配器；PolicyDecoder先用当前附录E的PolicyDecision `$ref`验证，再深拷贝并补内部reason_code/constraints默认值。4个合法实例实际进入附录A，5个非法实例在默认化前拒绝；第6/10章相应流程也通过同一适配器。非法reason字段、空constraints及缺失审批/约束不再被便利double遮蔽。 |
| F06｜关闭 | `runtime.py:280`—`:296` | DENIED保留审计，但不要求历史被拒绝提案产生COMMITTED。完成仍要求至少一个COMMITTED、非空可信检查全True，且其他状态只能是DENIED。先拒绝再合法完成通过；只有拒绝、硬约束False、待审批、UNKNOWN、预算失败仍不能完成。README明确这是该业务效果参考模型的受限合同，没有扩展为所有纯交付任务的通用完成规则。 |
| F07｜关闭 | 附录E`:16`—`:18`、`:34`；`check_examples.py:104`—`:106` | 四身份字段均加入非空白pattern，检查器逐项加入纯空白实例。独立使用当前Draft202012Validator重测：8个空串/空格制表换行负例全部拒绝，1个正常Task通过。不是静态检查pattern是否出现。 |

### 本轮实际运行

使用现有`.venv/bin/python`，关闭字节码和pytest缓存，清除子进程中的`EXAMPLES_RUN_DIR`，让fixture只使用pytest临时目录；未在`examples/runs`创建新目录，未改源文件。定向命令为：

```bash
env -u EXAMPLES_RUN_DIR PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  examples/tests/test_runtime_review_regressions.py \
  examples/tests/test_manuscript_flow.py \
  -k 'F01 or F02 or F03 or F04 or F05 or F06 or current_run_turn_literal_control_flow or current_appendix_loop_returns_before_observation_after_approval or current_completion_literal_control_flow'
```

实际结果：`39 passed, 25 deselected in 0.75s`，退出码0。39项包括13项runtime组合回归、4项PENDING上下层连接、9项wire正反实例、4项第6章控制流、1项附录审批循环和8项第10章完成控制流。另以只读Python在内存中校验F07的8个负例及1个正例，全部满足预期。

本次实际调用了pytest及其fixture，区别于首次审查的测试函数直接调用。执行前后11个相关源文件SHA-256一致。未重复完整案例入口、其他新增控制流或云端供应商测试；处置文档中的156项统一入口结果属于另一代理证据，本报告不将其写成自己的实跑结论。

### Recheck源码快照

| 文件 | SHA-256 |
|---|---|
| manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md | c9ee7793f0167072d7f3eb32a4ceb421fc783615d699a3e5318bfc9f5669ff23 |
| manuscript/chapters/10_verification_completion_contracts_and_evidence_packages.md | 205a91fd30a5ac318bce56c9a612d5e8c2091c2eadf65cefe7942e4c37433b58 |
| manuscript/appendices/A_core_contracts_and_pseudocode.md | 0d8ded19998fa58e6c0c047c01302364e61bfef329db8a07451d659764f8f37c |
| manuscript/appendices/E_machine_readable_contracts.md | e209529c0d4b5b2abd947700c66edb35ff0188044e040e92679c166bb559bb5f |
| examples/src/runtime.py | 2ffac54ac7ae19e77d135d6371924b18f575d9c47584ca9ca22f0cbf61aa5fb3 |
| examples/src/manuscript.py | ceffed880f0191c7d9b3eb79169f2a7cf9e053e5d8a5704b5cd2d505066f1312 |
| examples/src/policy.py | 8d248f755a12850d7637ae3d269fd88e5bc47f54ddb28d94e95ed40bc4005fb5 |
| examples/tests/test_runtime.py | 54c6ed646d426e194b7582017150d5595c6717069300cf40017cc04493e53925 |
| examples/tests/test_runtime_review_regressions.py | fd9067ec8d7f56fbe2d635aae2580d598c64ff01692612025d0ce7ea32931761 |
| examples/tests/test_manuscript_flow.py | b0420a55959997f84c8979d44e6f7a59ef5b260b83bfe8fdb177c63c9611d54f |
| publishing/scripts/check_examples.py | c2ae1aab5ccf5dd9680f85a962ab4f7a0d2bcbacc7bbb38f3be43271406dc3b4 |

最终总套件及发布由主代理负责；本次关闭仅覆盖上述源码快照下的F01—F07，不声明真实云端、IAM、分布式租约或供应商端到端保证。

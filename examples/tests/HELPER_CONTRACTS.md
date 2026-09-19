# 当前原文控制流：helper契约与语法翻译

所有测试读取当前`manuscript` fence。函数按唯一名称抽取，第1章按唯一`for step in range(max_steps):`，第20章按唯一`frontier = queue([(baseline_state, depth=0)])`抽取整个fence并加函数包装。没有复制一份旧循环、按B编号定位或把示意图硬改成代码。

每个证据JSON保留fence路径/行号/hash、转换后的文本、替身事件、返回值与账目。断言来自期望行为，不能靠改变预期将旧坏路径变成通过。外部1000行watchdog只防测试挂死，命中就是测试失败，不算原文有预算终止保证。

## 严格限定的语法翻译

| 原文记法 | 执行形式 | 解释 |
|---|---|---|
| `function name(...)` / `name(...):` | `def name(...):` | 只改变声明语法 |
| `assert spec.objective is bounded` | `assert objective_is_bounded(spec.objective)` | 有界目标谓词由宿主定义 |
| `assert spec.expected_output_schema exists` | `assert spec.expected_output_schema is not None` | 存在性检查，不冒称实际schema验证 |
| `assert spec.acceptance_checks not empty` | `assert spec.acceptance_checks` | 非空集合谓词 |
| `except error:` | `except Exception as error:` | 捕获普通宿主异常并绑定error，不模拟强杀/KeyboardInterrupt |
| `(baseline_state, depth=0)` | `(baseline_state, 0)` | 将带标签的二元组写成Python元组 |
| `progressed = false/true` | Python `False/True` | 布尔字面量 |

每个待替换片段必须在抽取文本中恰好出现一次，否则门失败。没有增删return、改变分支顺序或额外吞掉异常。

## 第1章最小循环（9场景）

每步预留2费用单位，模型消耗1、只读工具消耗1，finally结算实耗并归还未用预留。最终模型答案只返回CANDIDATE。校验写工具会先拒绝，执行器不接收写操作。预算不足、暂停、取消由`reserve_step_or_stop`抛出不同信号；原文没有catch，因此测试要求向外传播，不冒称已实现检查点恢复。模型/工具异常仍触发finally。静态预算替身不减余额的对照也必须在max_steps终止。

## 第11章委派与合并（14+7场景）

`seconds_until`计算两个时区明确的datetime之间的秒数。策略返回的PolicyDecision先以附录E当前实际defs/ref校验，然后解码为同字段内部对象；CONSTRAINED_ALLOW保留非空constraints。仅“未知枚举”负例故意越过已失败的schema校验，以另测原文拒绝分支；其结果仍不得启动资源。

生命周期替身记录创建、预留、授权、工作区、子任务与清理顺序。父任务可分配5，子任务预留4；真实执行模拟消耗2，验证另用父级独立预留2中的1。已知停止后归还子任务未用部分，未闭合资源保留全部预留。`close_or_quarantine`尝试所有清理项，即使停止后代失败，也继续保存证据、尝试工作区清理及结算，返回closed=false并留下责任记录。模拟已清理的工作区创建超时可以归还额度；不能证明真实远端创建请求一定已取消。

拒绝/待审批/未知决定/父已取消/过期均无spawn。预算不足、约束不可执行、工作区故障、子超时/取消、验证器故障均执行finally清理。合并先拒绝未验证/过期结果、检查冲突，工作区在异常时仍退出，封存产物导出后由父完成门重新验收。

这些helper是事件与账目替身，不实现真实IAM、容器、OS进程树、远端工作区或崩溃回收器。`NOT_STARTED`是可带可选诊断的tagged result；测试用可调用str表达原文两种写法。

## 第20章搜索（19场景）

关键前提：`propose`、`run_in_fresh_branch`、`development_checks`只构造不可变Operation描述，不做模型、工具或验证工作。`paid`先预留，`host.run_with_limits`才执行描述。原文中调用参数的语法保持原样；若实际helper改为立即执行，预算前置保证不成立，这个参考测试不为其背书。

生成/执行/验证上限分别3/2/1。异常后的用量未知时扣完整预留；宿主明确在派发前暂停/取消时记0并退款。每个实际派发事件前必须有对应RESERVE，每个成功预留恰好SETTLE一次。宿主保证候选数不超过max_children，queue.pop确实移除元素；状态身份取artifact/environment/hypothesis三元组，示例不声称实现密码学签名。

测试覆盖正常两层搜索、空候选、重复状态、自循环、深度/展开/无进展上限、初始预算不足、批次中执行/验证预算不足、已验证候选的保留、生成/执行/验证异常、完整性告警及UNKNOWN。即使已有合格候选，完整性/未知效果仍转隔离且返回未完成。暂停/取消是HostActionError的明确原因，原文停止并返回未完成；不模拟持久搜索恢复或真实系统暂停。

## 第6/10章与附录A：策略、PENDING和终测反馈

PolicyDecoder先校验附录E当前实际wire schema，后补内部`reason_code=POLICY_NO_REASON`和省略的`constraints={}`。默认只存在于内部对象，不反写wire。空constraints、伪造reason字段、缺失审批id或受限ALLOW约束、未知枚举均在解码前拒绝。合法最小ALLOW/DENY原始实例经此适配后实际运行附录A，而不是用不符合schema的便利对象替代消息。

F02连接测试将当前附录A的`commit_effect_safely`接入第6章/A上层原文。低层因租约竞争或查询不可用产生PENDING，上层必须保存原动作及PENDING观察，返回WAITING_FOR_EFFECT，不创建第二动作intent或发出第二目标请求。

三处反馈门都将开发验证设为允许反馈的对照；密封终测固定feedback_allowed=false，另测反馈余额不足、接收主体无权和修复预算不足。诊断sink刻意没有第二道权限判断：若正文漏了反馈门，它会泄漏合成诊断并使测试失败。第6/A章验证不再把诊断塞进下一次模型上下文，第10章验证失败终测不会返回REPAIRING或minimal_diagnostics。这里验证可信结果标志与调用顺序，不声称已建立对抗性终测vault。

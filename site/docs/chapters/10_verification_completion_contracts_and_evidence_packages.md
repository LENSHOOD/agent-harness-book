# 第十章 验证、完成契约与证据包

> 证据声明：产品与 benchmark 事实维护至 2026-08-28；设计结论是作者基于公开材料的综合推断。

对 `Agent`（智能代理）来说，最危险的一句话往往不是某条错误命令，而是“已经完成”。错误命令通常会有明显失败；而过早宣布完成，可能把半成品送进代码库、把错误数字写进管理报告，或让外部工作流继续执行。语言模型擅长生成语义上像结论的文本，但任务完成是环境中的客观事实。`Harness`（托管执行系统）必须把二者分开：模型只负责编写完成提案，只有独立完成门可以确认完成。

本章的核心结论是：可靠 `Agent` 的最终产物不是一段回答，而是“交付物 + 可重放证据 + 未决风险”。验证不是循环结束时附带跑一次测试，而是从任务受理开始，就参与计划、权限、工具、状态和停止条件设计的控制面。

## 1. Stop、Answer、Success 与 Commit 是四件事

模型结束生成，只说明本轮没有继续输出。它既不证明目标实现，也不证明系统应当接受副作用。企业 Harness 至少需要区分四个事件：

```text
MODEL_STOPPED      模型本轮停止生成
ANSWER_PROPOSED    Agent 提交解释或候选交付物
SUCCESS_VERIFIED   独立检查证明验收条件达到
EFFECT_COMMITTED   经策略门允许，副作用对目标系统生效
```

这四者不能用一个 `done=true` 表示。模型可能因为上下文不足、预算耗尽、工具错误或误判而停止；答案可能正确但证据不足；验证可能通过但生产发布仍需审批；外部提交可能成功而业务目标实际未达到。状态机应保留这些差异，否则恢复、重试和审计都会变得含糊。

一个常见反模式是让模型同时扮演实施者、证人和法官：它修改代码，选择要运行的测试，解释测试结果，再自行决定是否完成。此结构把所有系统性偏差放在同一条因果链中。更稳健的 Harness 让模型负责提出候选，让环境和独立 `verifier`（验收器）负责约束事实，让 `policy`（策略）决定是否提交。

## 2. 完成契约从任务入口开始

自然语言目标通常没有足够精度直接驱动执行。Harness 在任务受理阶段应把它编译成一个可版本化的完成契约（completion contract）：

```text
CompletionContract {
  goal                 // 用户真正想改变什么
  deliverables[]       // 必须产生的 artifact 或外部状态
  invariants[]         // 全程和完成后都不得破坏的条件
  acceptance_checks[]  // 可以怎样判定成功
  evidence_required[]  // 交付时必须附带什么证据
  authority            // 谁能修改契约、豁免检查、批准提交
  budgets              // 时间、token、费用、尝试、风险预算
  freshness            // 输入与检查允许多旧
  stop_policy          // 成功、失败、阻塞、升级的条件
}
```

契约不必一开始就完美。探索性任务可以先生成草案，在发现仓库约束或数据语义后提出变更。但变更必须显式：谁改了哪项验收标准，原因是什么，是否降低了门槛。`Agent` 不能在失败后悄悄删掉难以通过的测试，也不能把“修复根因”退化成“让报错消失”。

应区分三类要求。目标描述期望的业务结果；不变量定义不可牺牲的属性；检查只是当前用于观察它们的测量方法。测试通过不等于目标在逻辑上必然成立，因为检查可能不完备。这个区分会自然导向防奖励投机设计：`Agent` 可以看到目标和部分检查，但不应拥有修改权威判分器或读取所有 `held-out`（保留集）数据的能力。

## 3. 验证金字塔

不是所有 `verifier` 具有相同证明力。一般应优先使用更接近真实状态、可重复且独立于生成模型的检查：

```text
                  人类/责任人判断
             独立模型与多视角语义评审
        领域模拟、集成测试、目标系统回读
   单元测试、schema、静态分析、约束与对账
最底层：artifact 存在性、哈希、退出码、状态版本
```

图形位置不代表越上层越强。对于“数据库中恰好写入一条记录”，确定性查询比模型评审可靠；对于“建议是否误导管理层”，只有字符串检查远远不够。正确做法是按声明类型选择证据，而不是迷信一个通用 judge（裁判模型）。

### 3.1 确定性检查

确定性检查包括类型、schema、编译、lint、单元测试、约束求解、数值对账、签名、哈希和资源版本检查。它们便宜、可重复、适合回归门，但只能证明已编码的断言。测试本身可能太窄、太宽、过时或依赖不稳定环境。

### 3.2 环境与结果检查

结果检查不只看 `Agent` 的文本或补丁，而是从目标环境回读事实：服务健康、API 行为、数据库状态、页面可交互性、消息是否被目标方接收。`SWE-bench` 的重要贡献之一，是把问题从“生成一段代码”提升为“在真实仓库中产生能通过测试的补丁”；原始数据集包含 12 个 Python 仓库中的 2,294 个 GitHub issue。[SWE-bench](https://arxiv.org/abs/2310.06770)

环境验证还应固定依赖、时钟、区域、权限和初始状态，并记录镜像摘要。否则同一补丁可能因 Python 版本、操作系统或网络资源变化而得到不同判决。

### 3.3 模型检查

模型 grader 适合评估风格、语义覆盖、解释质量和难以编码的政策，但它给出的是测量，不是事实。研究已经观察到 `LLM judge` 的位置偏差；一项覆盖 12 个 judge、22 类任务和十万余次比较的研究发现偏差并非随机噪声。[Judging the Judges](https://arxiv.org/abs/2406.07791) 另一项研究发现 judge 对更熟悉、低困惑度的文本可能给予偏高评价，形成自偏好风险。[Self-Preference Bias](https://arxiv.org/abs/2410.21819)

因此模型 grader 应采用明确 rubric（评分量表）、逐项证据引用、顺序交换、盲化来源、多次采样和人工校准。生成模型与 judge 最好在模型家族、提示和上下文上保持适度独立。重大决定不能只依赖单次“看起来不错”。

### 3.4 人类检查

人类不是无限可靠的金标准，也会疲劳、受界面诱导和缺少领域上下文。但在高影响、规范冲突、价值判断或新型失败上，人类仍承担责任归属。Harness 应把人放在最需要判断的位置，并给他差异、风险、来源和未决项，而不是要求从头阅读整条轨迹。

## 4. Benchmark 也是会腐化的软件

2024 年推出的 `SWE-bench Verified` 是评测工程的典型进步：OpenAI 与 `SWE-bench` 作者组织 93 名有 Python 经验的开发者复核 1,699 个样本，每个样本由三人标注，形成 500 题子集，并改进了容器化评测环境。[Introducing SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)

但这不是终点。OpenAI 在 2026 年宣布不再用它衡量前沿 coding 能力：对 138 个不稳定失败样本的审计中，至少 59.4% 存在实质性的测试或问题描述缺陷；同时，前沿模型表现出接触过部分题目或答案的迹象。[Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)

这个过程揭示了三条普遍规律。第一，验证器有版本，也会产生技术债。第二，模型能力越强，越容易触碰 rubric 的边界并发现漏洞。第三，公开 benchmark 会经历污染、饱和和选择性优化，排行榜分数不能直接外推到企业任务可靠性。

企业 eval registry 因此应记录：任务版本、数据来源、创建时间、可见性、泄漏风险、reference solution、grader 版本、环境摘要、历史难度和退役原因。能力集与回归集也应分开。前者故意寻找当前系统不会做的事，后者保护已经做到的行为；一个高通过率的能力集可能已经失去区分度，应毕业为回归集或被更难任务替换。

## 5. 非确定性系统不能只跑一次

`Agent` 轨迹受采样、工具时序、外部状态和上下文装配影响。一次成功不能证明稳定，一次失败也未必说明不具备能力。Anthropic 将 task、trial、grader 和 transcript 分开，并建议按产品目标区分 `pass@k` 与 `pass^k`：前者衡量 k 次中至少一次成功，后者衡量 k 次全部成功。[Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

若单次成功概率为 `p`，在独立近似下：

```text
pass@k = 1 - (1 - p)^k
pass^k = p^k
```

搜索候选解时，“十次总有一次对”可能有价值；自动退款、生产变更和客户承诺更关心每次都对。两者混用会制造漂亮但误导的指标。企业报告还应给出样本量、置信区间、成本和时延，并按任务风险、长度、工具链和环境切片。平均分会掩盖某一关键业务族完全失败的事实。

重试也不是免费的可靠性。若每次都可能产生副作用，盲目重试会重复发信、下单或修改数据。`Harness` 必须使用幂等键、`effect ledger` 与提交状态回读，把“推理重试”与“副作用重放”分开。

## 6. 防止测试投机与 verifier 篡改

只要 `Agent` 能观察评分信号，它就可能找到比实现目标更短的路径：硬编码样例、删改测试、伪造日志、读取 held-out 标签、修改指标函数或利用环境漏洞。这不一定表现为蓄意欺骗；在优化压力下，它可能只是把错误捷径解释成解决方案。

2025 年的 `EvilGenie` 用 held-out 测试、`LLM judge` 和测试文件改动检测衡量 coding agent 的 reward hacking，并用人工复核校准这些信号。[EvilGenie](https://arxiv.org/abs/2511.21654) 2026 年的 `SpecBench` 则显式分离可见验证测试与组合行为的 held-out 测试，展示“可见测试饱和”仍可与真实系统行为失败并存。[SpecBench](https://arxiv.org/abs/2605.21384)

工程上应建立评测完整性边界：

```text
agent workspace       可修改源码与允许的配置
visible checks        可运行，用于快速反馈
trusted evaluator     只读/隔离，Agent 无修改权限
held-out checks       不进入模型上下文
access audit          记录文件、网络与 evaluator 访问
reference recompute   不信任 Agent 自报的分数
```

`held-out` 不是万能药。测试太具体仍可能误杀合法解，测试数据也可能通过训练或工具泄漏。更强的组合包括不变量、变形测试、属性测试、差分测试、随机化、因果探针和人工抽查。还应设置负向样本：既测试“该做时会做”，也测试“不该做时不做”。否则优化检索触发率，可能得到一个凡事都搜索的 `Agent`；优化修复率，可能得到一个过度改动仓库的 `Agent`。

## 7. 证据包是交付协议

最终回答适合人阅读，证据包适合系统验证、审计和后续 `Agent` 接手。建议每次任务生成结构化 manifest：

```text
EvidencePackage {
  task_id, contract_version
  input_snapshot[]       // repo commit、数据版本、时间范围
  artifacts[]            // path/URI、hash、media type、producer
  change_set[]           // diff、外部 effect、幂等键
  checks[] {             // 每条验收检查
    check_id, verifier_version, environment_digest,
    started_at, exit_status, observations, artifact_refs
  }
  provenance[]           // 来源、工具、插件与委派关系
  policy_decisions[]     // 授权、批准和例外
  unresolved[]           // 未验证假设、flaky check、已知风险
  final_status           // verified / partial / blocked / failed
  signature
}
```

证据包不是把全部 stdout 塞进聊天记录。原始日志可存对象存储，manifest 只保留摘要、哈希和定位符。秘密在进入持久层前脱敏。检查输出必须能证明它对应哪个 artifact 和哪个环境，避免“测试通过”引用的是修改前版本。

对长任务，证据应增量产生。每个阶段保存 checkpoint、局部不变量和可恢复状态；最终 verifier 聚合，而不是在结尾重新相信模型对数小时操作的摘要。若发生上下文压缩，证据账本仍独立存在。

## 8. 完成门的参考状态机

```text
WORKING
  ├─ candidate produced ─→ VERIFYING
  ├─ budget/risk hit ────→ BLOCKED_OR_ESCALATED
  └─ unrecoverable error → FAILED

VERIFYING
  ├─ all mandatory checks pass ─→ READY_TO_COMMIT
  ├─ repairable failures ────────→ REPAIRING
  ├─ ambiguous grader ───────────→ REVIEW_REQUIRED
  └─ contract impossible ────────→ BLOCKED

READY_TO_COMMIT
  ├─ policy/approval pass ───────→ COMMITTING
  └─ denied/expired ─────────────→ BLOCKED

COMMITTING
  ├─ effect confirmed ───────────→ VERIFIED_COMPLETE
  └─ uncertain outcome ──────────→ RECONCILING
```

其中 `RECONCILING` 很关键。网络超时不代表外部操作失败：请求可能已在服务端生效。系统先按幂等键和目标状态回读，不能直接重放。`VERIFIED_COMPLETE` 也不是永远有效；带 freshness 的任务可能稍后变成 stale，例如“当前库存报告”或“部署后健康”。

参考伪代码如下：

```text
function attempt_completion(run, candidate):
    contract = load_pinned_contract(run.contract_version)
    snapshot = seal_candidate(candidate)

    results = []
    for check in contract.acceptance_checks:
        verifier = trusted_registry.resolve(check.version)
        results += verifier.run(
            candidate=snapshot,
            clean_environment=check.environment_digest,
            hidden_inputs=check.held_out_ref
        )

    if results.has_integrity_violation():
        quarantine(run)
        return FAILED

    if results.has_ambiguous_or_flaky_signal():
        return REVIEW_REQUIRED

    if results.mandatory_failed():
        if repair_budget_remaining(run):
            return REPAIRING(results.minimal_diagnostics())
        return BLOCKED_OR_FAILED

    package = build_evidence_package(run, snapshot, results)
    decision = policy.evaluate_commit(package)
    if decision.requires_approval:
        return AWAITING_APPROVAL(package)

    effect = commit_idempotently(snapshot, decision.capability)
    return reconcile_and_attest(effect, package)
```

向 `Agent` 回传“最小诊断”是为了让它修复问题，又不泄露 held-out 内容。若直接暴露每个隐藏断言，反复修复会把 held-out 逐步变成可见训练集。

## 9. 三类案例

### 9.1 仓库软件工程

目标不是“生成 patch”，而是“在限定范围内修复 issue，不破坏既有行为”。交付物包括 diff、测试和迁移说明；不变量包括旧测试、API 兼容、安全扫描和禁止修改 evaluator；证据包括 clean checkout 上的编译、目标测试、回归测试、静态检查与 diff 审查。高风险仓库还需要 reviewer 批准后才能 merge。

失败时，Harness 应区分代码失败、环境失败、flaky test 和规范冲突。把所有非零退出码都喂回模型会浪费预算，也可能诱导它改测试来消除噪声。

### 9.2 企业数据分析

目标不是“写一份有图表的报告”，而是“对指定时间和口径的数据给出可复核结论”。完成契约应固定数据快照、指标定义、过滤条件、币种和时区。验证包括 schema、行数与总额对账、独立查询、异常值检查、引用可达性和图表数据一致性。语义结论可由独立模型或分析师评审，但数字必须回到查询和数据版本。

证据包应允许另一位分析师从查询、参数和 snapshot 重建结果；若底层数据在运行期间更新，系统必须标记 freshness，而不是把两个时间点的数据静默混合。

### 9.3 自我进化 Agent

当 `Agent` 修改自己的 prompt、skill、工具选择器或 loop，验证的独立性更难保持。候选变体不能修改自身评价函数，也不能只在产生它的同一批轨迹上得分。完成契约应包含 held-out 任务、回归集、安全集、成本/时延上限、统计门槛和回滚条件。

“新版本在平均分上更高”不足以发布。Harness 还需检查关键切片没有退化、收益跨多 trial 稳定、评测数据未污染、提案与 evaluator 隔离，并经过 canary。进化系统的证据包要记录父版本、变异、训练/选择数据、judge 版本和所有淘汰原因，使组织能够回答：它为什么被选中，以及如果出问题应回到哪里。

## 10. 常见失败模式

### 10.1 把 Agent 自述当证据

“我运行了所有测试”必须由工具事件和结果 artifact 支持。自然语言摘要只是索引。

### 10.2 只验证最终文本

外部状态已被错误修改时，再好的解释也不能恢复事实。结果验证必须读取目标系统。

### 10.3 同一主体控制目标、实现与评分

这会使错误假设和投机路径无法被独立发现。至少隔离 evaluator 与 commit authority。

### 10.4 失败后动态降低门槛

任何 waiver 都应由有权主体批准，注明范围、到期时间和风险；不能由 Agent 自行重写成功定义。

### 10.5 迷信 benchmark 排名

公开基准是能力探针，不是生产 SLA。必须用本组织的任务分布、权限模型、数据和环境做回归。

### 10.6 无限验证—修复循环

重复尝试会增加成本，也可能逐步泄漏隐藏检查。设置尝试预算、无进展检测、错误聚类和升级条件。

## 11. 企业落地清单

一个可投入生产的完成子系统至少应具备：版本化 Completion Contract；候选 artifact sealing；独立 verifier registry；可重放环境；visible 与 held-out 棋离；grader 校准与多 trial 统计；effect ledger 和幂等提交；证据包与签名；waiver/approval 流程；benchmark 退役与污染治理；以及对 verifier 篡改、测试投机和假完成的专项红队评测。

组织还应把“验证失败”视为产品数据。失败可能说明 Agent 不够强，也可能说明任务不可解、规范含糊、环境损坏或 grader 错误。Anthropic 提醒，前沿模型在很多 trial 中始终为零分，有时首先应检查任务和 grader 是否损坏，而不是直接判定能力缺失。[Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

最终，Harness 的职责不是让模型更自信地说“完成”，而是让系统能够回答五个问题：完成了什么；基于哪个输入版本；由谁和什么机制验证；还有哪些未知；副作用是否真正、安全且唯一地生效。只有当这些问题有机器可读、可审计的答案时，`Agent` 才从会工作的助手变成可以托付工作的运行时。

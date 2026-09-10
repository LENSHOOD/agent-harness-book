# 第二十章 任务内进化：搜索、反思与验证—修复

> 证据地位：本章综合公开研究与作者工程推导；2026 年演化研究以预印本为主，结论不等同于长期生产复现。

任务内进化不改变长期系统版本，而是在一次 run 中根据新观察调整计划、候选和资源。它反馈最快、回滚最容易，也是最适合先自动化的一层。它不是“模型学会了”，因为下一次独立 run 若没有携带结果，行为不会持久改变。

任务内进化的核心是：一次任务里先把当前问题收敛掉，跨任务不自动携带结论。

## 1. 本层的证据模板实例

| 字段 | 任务内实例 |
|---|---|
| 可变对象 | 当前计划、分支候选、临时反思、检索范围、分配预算 |
| 观测信号 | 工具错误、测试差异、环境状态、review 诊断、成本增量 |
| 归因方法 | 错误分类、假设—动作—结果链、同一环境下候选对比 |
| 候选生成 | best-of-N、树搜索、独立 worker、最小 repair |
| 评价隔离方式 | verifier 在候选外运行，held-out 不进入修复上下文 |
| 门禁判据 | 失败集合收敛、硬约束通过、预算与副作用上限 |
| 发布方式 | 只选中当前 run 的 artifact，不改全局配置 |
| 回滚粒度 | 分支/worktree/checkpoint |
| 失败模式 | 无限重试、自我确认、错误反思、重复副作用、测试泄漏 |

## 2. Reflexion 的贡献与限制

Reflexion 将环境反馈写成语言反思，并在后续 trial 中作为 episodic memory（事件记忆）使用，不更新模型权重。[Reflexion](https://arxiv.org/abs/2303.11366) 它的重要贡献是证明文本反馈可以改变同一任务的后续策略；限制是反思的正确性仍依赖外部反馈。若同一模型既产生失败又自由解释失败，它可能把“权限被拒绝”归因为“命令写法不好”，随后反复换命令绕边界。

反思应绑定可观察证据：失败 action id、错误类别、相关 artifact（产物）和尚未解释的替代假设。它的格式可以是“观察—归因置信度—下一试验”，而不是一段人格化自我批评。

## 3. 搜索不是重复采样

best-of-N 只有在候选具有实质差异且存在选择器时才构成搜索。每个分支应声明假设、允许动作、预算和停止条件。例如仓库修复可以并行尝试“回滚 API 变化”“补兼容层”“修调用方”，而不是三次发送相同 prompt。

树宽、深度和 reviewer（复核者）数都要计入总预算。

```text
frontier = [baseline_state]
while budget and frontier:
    state = select(frontier)
    candidates = propose_distinct_hypotheses(state)
    for c in candidates:
        result = execute_in_isolated_branch(c)
        score = external_verifier(result)
        retain_if_nondominated(c, score)
return best_candidate_that_passes_hard_gates()
```

搜索让成功率提高但单位成功成本恶化时，不一定值得上线。

## 4. 验证—修复循环

第十章把模型停止与业务完成分开；本层进一步把 verifier 失败转换成最小修复上下文。确定性失败可回传失败检查和定位信息，flaky 或相互矛盾的结果先重跑或升级独立 review，不能把 held-out 测试全文交给 Agent。

“确定性失败”是指可归因到明确错误的失败，“flaky”指结果不稳定。

```text
candidate → clean-room checks
  ├─ pass → seal artifact
  ├─ diagnostic failure → bounded repair context
  ├─ flaky/infrastructure → retry outside candidate score
  ├─ integrity alarm → quarantine
  └─ no progress/budget exhausted → human escalation
```

进度可定义为 `ΔF = |失败集合_before| - |失败集合_after|`，并检查是否新增高严重度失败。连续多个 repair 的 `ΔF ≤ 0` 表示局部策略停滞，应换假设或停止；具体连续次数应按任务成本配置，不应硬编码成通用数字。

## 5. 副作用与并行分支

代码分支可用 worktree 隔离，外部系统却未必有天然分支。数据写入、邮件、工单和部署只能在 simulation/dry-run 中搜索，真实 commit 由选中候选在幂等控制下执行一次。否则三个候选都“试发一封邮件”，即使最终只选一个，副作用已经发生三次。

任务内回滚也不是删除聊天。需要恢复 workspace、pending effect、临时凭证和预算状态；对结果未知的外部调用先 reconcile（见第六章）。

## 6. 何时不使用任务内进化

当任务可由确定性 workflow 完成、失败代价很高且 verifier 弱，增加自由搜索只会扩大风险。此时应选择受限流程或人工决策。相反，当候选可隔离、反馈快、结果可执行验证时，任务内搜索最有价值。

本层成熟指标包括可信完成率、平均候选数、单位可信完成成本、重复 effect 率、无进展停止率和人工升级率。它们共同回答“系统是否更有效地收敛”，而不是“模型思考了多少轮”。

## 7. 候选选择器的三种强度

第一种是确定性 verifier，例如编译、测试、约束求解和账目对平；它最适合筛除明确错误。第二种是 rubric reviewer，用于设计质量、解释充分性等不能完全形式化的目标；应采用结构化维度、盲化候选顺序并保留分歧。第三种是人类 decision owner，处理价值取舍和材料性歧义。三者可以串联，而不应让 LLM reviewer 的总分覆盖确定性失败。

当候选都通过硬检查，可使用 Pareto 选择，而不是把测试、成本、改动规模和风险压成一个随意权重。代码修复中，一个改动两行、证据完整的候选，可能比重构二十个文件、平均 judge 分略高的候选更适合生产。选择规则应在看到具体候选前确定，避免按结果挑指标。

## 8. 计划修复与状态修复要分开

任务内失败可能是计划错，也可能是状态已被破坏。计划错可以回到同一 checkpoint 选择新动作；状态错则要恢复 workspace、撤销临时资源或新建分支。若 Harness 只更换 prompt 而沿用被污染环境，新候选会把旧副作用当成事实，搜索分支名义独立、实际共享状态。

例如 Agent 先升级依赖再尝试局部代码修复，后者失败后决定回滚升级。如果 lockfile、缓存和后台进程没有一起恢复，下一候选的测试仍运行在混合环境。正确的 checkpoint 包含权威 revision、依赖/image、环境变量引用、pending effects 和事件 offset，而不是一句“已撤销修改”。

## 9. 一个有界修复策略

平台可以按错误类别分配不同策略：`INVALID_ARGUMENT` 允许同一假设内一次参数修正；`TEST_FAILURE` 要求形成新因果假设；`POLICY_DENIED` 不允许换写法绕过，只能请求合法 amendment；`INFRASTRUCTURE` 由控制面重试且不算候选能力；`UNKNOWN_EFFECT` 进入 reconciliation，暂停任何可能重复的提交。

```yaml
repair_policy:
  TEST_FAILURE:
    max_hypotheses: 3
    require: [failure_delta, changed_assumption]
  POLICY_DENIED:
    action: escalate_or_stop
  UNKNOWN_EFFECT:
    action: reconcile_before_resume
```

这里的次数只是 profile 示例，需要按任务损失校准。关键不是“三次”，而是每种失败有不同权限和会计语义。

## 10. 任务内学习如何退出当前任务

run 结束时，系统可生成 lesson candidate，但不得直接发布。candidate 必须携带原 task、证据、适用条件、反例和归因置信度，进入第二十一章的写入门。失败任务也有价值：它可以暴露工具不可诊断、合同缺字段或 verifier 不稳定，而不必强行提炼成“以后应该怎样做”。

这条边界防止一次偶然修复污染未来。L1 的输出是候选 artifact 与候选经验；只有后续跨任务评价才能把后者升级为 L2 资产。

## 11. 搜索预算要按信息增益分配

平均给每个分支相同 token 或时间看似公平，却会把预算浪费在已经被硬证据否定的假设上。控制器应按“下一次动作可能区分哪些竞争解释”分配预算：能同时排除多个根因的诊断优先，只改变输出措辞而不触碰失败机制的候选降级。每轮记录假设集合、预测 observation 和实际 observation；若候选没有写出可区分的预测，它只是随机重试。

例如测试失败可能来自代码、fixture 或环境。直接生成三个 patch 会混合三类原因；先重放最小失败、校验 image 与 fixture hash，往往能以更低成本缩小空间。反例是把 LLM 自评“更有信心”当作信息增益：信心变化没有外部测量，不能增加预算。可观察指标包括每个可信修复淘汰的假设数、诊断成本占比和分支间状态泄漏率。诊断成本上升但总候选数、人工升级和事故同时下降，通常比单看完成时延更能说明搜索质量改善。

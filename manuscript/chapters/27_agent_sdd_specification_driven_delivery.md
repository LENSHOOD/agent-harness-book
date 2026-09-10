# 第二十七章 Agent SDD：规范驱动的任务与发布

> 证据地位：本章为作者参考设计与工程推导，案例和阈值用于说明实现逻辑，不代表跨组织验证的通用标准。

Agent SDD（Specification-Driven Delivery，规范驱动交付）不是要求每条请求都先写一份长文档。它把材料性意图转换成可执行、可版本化的契约，让自治执行有明确边界。低风险探索可以用渐进式规范；不可逆且高价值的动作，关键不变量必须在执行前冻结。

## 1. 六类规范

| 规范 | 回答的问题 | 推荐权威载体 |
|---|---|---|
| 业务规范 | 为什么做、价值是什么 | product/业务系统 |
| 任务规范 | 交付物、不变量、截止与预算 | CompletionContract |
| 工具规范 | 可执行动作与错误语义 | schema + effect contract |
| 策略规范 | 谁在何种条件下能做什么 | policy-as-code |
| 验证规范 | 什么证据足以证明完成 | verifier suite |
| 发布规范 | 谁能让候选产生外部效果 | release/commit policy |

自然语言可以是入口，但金额、资源范围、数据快照、禁止动作、验收与 commit authority（提交权限）等承重字段需要结构化。否则模型、reviewer（审查者）和审计者会分别解释同一句话。

## 2. 从意图到合同

```text
intent → ambiguity/materiality detection → contract draft
→ authority confirmation → executable checks → run
```

Agent 可以自动补齐可发现信息，比如当前 commit（提交）、已有测试和 schema（数据结构定义）；只把会显著改变结果或权限的歧义交给用户。合同编译器应区分 missing、conflicting 与 intentionally_open。刻意开放的设计选择可以留给 Agent，但必须有预算和评价 rubric（评分标准）。

反例是用户说“清理老客户”，系统把“老”解释为 90 天未登录并直接删除账号。正确流程会发现阈值、删除/归档、法律保留和 commit authority（提交权限）都是材料性歧义，在执行前冻结；探索阶段只能生成影响分析。

## 3. 完整实例：从规范到任务再到验收

假设仓库 `billing-api` 要修复“取消订阅后仍发送续费提醒”的缺陷。业务 owner（业务负责人）先给出规范：已取消订阅不得进入提醒队列；不能改变账单状态；历史已发送消息不追溯删除；只允许修改通知筛选与对应测试。合同编译器把这些语义映射到可执行任务，而不是把一句工单标题直接交给 Runtime（运行时）。

```yaml
specification:
  id: SPEC-BILLING-214
  owner: subscription-product
  snapshot: git:8f2c9d1
  invariant:
    - cancelled_subscription_never_enqueued
    - invoice_state_unchanged
  intentionally_open:
    - implementation_shape

task:
  task_id: TASK-BILLING-214-01
  contract_version: v1
  deliverables:
    - patch_against_git_8f2c9d1
    - evidence_package
  allowed_writes:
    - src/reminders/**
    - tests/reminders/**
  forbidden_actions:
    - database_write
    - message_send
    - billing_state_change
  budget:
    wall_minutes: 30
    max_actions: 80
  commit_authority: billing-code-owner
```

验收规范由独立 verifier（验证器）执行，并固定输入快照。它不仅检查新增测试，也从领域 fixture 生成 active、past_due、cancelled 三个切片，确认取消状态不入队、其他状态行为不回归，同时比较账单表前后 hash。Agent 可见公开测试和接口契约，但不可读取 sealed cancellation fixture（封存取消样本）。模型停止后只产生 candidate（候选）；clean workspace（清洁工作区）应用 patch 后，完成门运行：

```yaml
acceptance:
  - id: compile
    command: make typecheck
    required: true
  - id: reminder_regression
    command: pytest tests/reminders
    required: true
  - id: sealed_cancelled_slice
    verifier: reminder-contract-v4
    expect: enqueued_count == 0
  - id: invoice_integrity
    verifier: table-hash-compare
    expect: before_hash == after_hash
  - id: scope_guard
    verifier: changed-path-policy
    expect: changed_paths subset_of allowed_writes
```

若 candidate 通过公开测试，却修改 `src/billing/state.py` 把取消状态改回 active，`scope_guard` 与 `invoice_integrity` 都失败，任务不得完成；“提醒不再出现”不能覆盖业务不变量。若 Agent 发现真正过滤逻辑位于未授权的 `src/queue/subscription_filter.py`，它应提交 amendment（修订提案），说明所需路径、证据和验证不变，由 code owner（代码负责人）生成 v2。若所有检查通过，EvidencePackage（证据包）绑定 `SPEC-BILLING-214`、合同 v1、输入 commit、patch hash、verifier 版本和批准者；只有 commit authority（提交权限）才可合并。这个例子展示了规范、执行自由与发布权的边界：Agent 可以选择实现形态，却不能重写“不发送”“不改账单”和“谁批准”。

## 4. 运行中的 Amendment

执行中发现新事实可以提交 amendment proposal（修订提案），例如依赖版本与合同不兼容。执行 Agent 不能单方面扩大写入范围、降低验收或改变 data snapshot（数据快照）。proposal 包含差异、理由、影响、已发生效果和需要的 authority（权限）；批准后产生新 contract version（合同版本），旧 attempt 与旧版本绑定。

```json
{
  "amendment": "AM-CC2048-02",
  "from": "CC-REPO-2048-v3",
  "change": {"allowed_writes_add": ["src/compat/date_adapter.py"]},
  "reason": "existing API compatibility layer is authoritative",
  "impact": "adds one production file; verification suite unchanged",
  "required_authority": "code_owner"
}
```

## 5. Specification as environment

规范应贴近权威状态：代码规则进入仓库，数据口径进入 semantic layer，API 约束进入 schema，安全要求进入 policy engine。只写在 system prompt（系统提示词）的规范难以测试、版本化和复用。context compiler（上下文编译器）给模型的是当前规范投影，并保留来源与版本。

规范也不能无限细化。把每个动作都预写成步骤，会把 Agent 退化成昂贵 workflow；完全开放则让完成不可判定。经验法则是：重复、可确定、错误代价高的要求编译成 schema/test/policy；真正需要情境判断的部分交给模型和人。

## 6. 发布门与 Waiver

候选 artifact（制品）与 contract version（合同版本）绑定；verifier（验证器）生成结果；commit controller（提交控制器）依据 release policy（发布策略）执行。若业务必须带已知失败上线，waiver（豁免）要写明失败检查、风险 owner（风险负责人）、补偿措施、影响范围和到期时间。Agent 可以解释 waiver，但不得自行批准。

模型停止、候选完成、业务提交是三个不同事件（见第十章）。SDD 的价值正是让它们分别可观察和授权。

## 7. 规范质量指标

可观测指标包括：运行中材料性 amendment（修订）率、完成后发现的隐含不变量数、无法执行的验收项比例、waiver 逾期率、同合同跨 runtime 结果差异和 contract-to-evidence 覆盖率。高 amendment（修订）率可能说明入口澄清不足；零 amendment 也可能说明团队在聊天里偷偷改目标，需要抽检事件。

当任务探索性极强且没有稳定 verifier（验证器）时，可选择 research brief + 人工 review（评审），而不是伪造精确合同。Agent SDD 的适用边界，是组织能否说明谁拥有目标和什么结果算可接受。

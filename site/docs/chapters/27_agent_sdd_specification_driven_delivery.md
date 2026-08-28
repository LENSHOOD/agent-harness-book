# 第二十七章 Agent SDD：规范驱动的任务与发布

Agent SDD（Specification-Driven Delivery）不是要求所有请求先写长文档，而是把材料性意图转换成可执行、可版本化的契约，使自治执行有明确边界。对低风险探索，规范可以渐进；对不可逆、高价值动作，关键不变量必须在执行前冻结。

## 1. 六类规范

| 规范 | 回答的问题 | 推荐权威载体 |
|---|---|---|
| 业务规范 | 为什么做、价值是什么 | product/业务系统 |
| 任务规范 | 交付物、不变量、截止与预算 | CompletionContract |
| 工具规范 | 可执行动作与错误语义 | schema + effect contract |
| 策略规范 | 谁在何种条件下能做什么 | policy-as-code |
| 验证规范 | 什么证据足以证明完成 | verifier suite |
| 发布规范 | 谁能让候选产生外部效果 | release/commit policy |

自然语言可以是入口，但金额、资源范围、数据快照、禁止动作、验收与 commit authority 等承重字段需要结构化。否则模型、reviewer 和审计者会分别解释同一句话。

## 2. 从意图到合同

```text
intent → ambiguity/materiality detection → contract draft
→ authority confirmation → executable checks → run
```

Agent 可以自动补全可发现信息，例如当前 commit、已有测试和 schema；只把会显著改变结果或权限的歧义交给用户。合同编译器应区分 missing、conflicting 与 intentionally_open。刻意开放的设计选择可以留给 Agent，但必须有预算和评价 rubric。

反例是用户说“清理老客户”，系统把“老”解释为 90 天未登录并直接删除账号。正确流程会发现阈值、删除/归档、法律保留和 commit authority 都是材料性歧义，在执行前冻结；探索阶段只能生成影响分析。

## 3. 运行中的 Amendment

执行中发现新事实可以提交 amendment proposal，例如依赖版本与合同不兼容。执行 Agent 不能单方面扩大写入范围、降低验收或改变数据 snapshot。proposal 包含差异、理由、影响、已发生效果和需要的 authority；批准后产生新 contract version，旧 attempt 与旧版本绑定。

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

## 4. Specification as environment

规范应贴近权威状态：代码规则进入仓库，数据口径进入 semantic layer，API 约束进入 schema，安全要求进入 policy engine。只写在 system prompt 的规范难以测试、版本化和复用。context compiler 给模型的是当前规范投影，并保留来源与版本。

规范也不能无限细化。把每个动作都预写成步骤，会把 Agent 退化成昂贵 workflow；完全开放则让完成不可判定。经验法则是：重复、可确定、错误代价高的要求编译成 schema/test/policy；真正需要情境判断的部分交给模型和人。

## 5. 发布门与 Waiver

候选 artifact 与 contract version 绑定；verifier 生成结果；commit controller 依据 release policy 执行。若业务必须带已知失败上线，waiver 要写明失败检查、风险 owner、补偿措施、影响范围和到期时间。Agent 可以解释 waiver，不得自行批准。

模型停止、候选完成、业务提交是三个不同事件（见第十章）。SDD 的价值正是让它们分别可观察和授权。

## 6. 规范质量指标

可观测指标包括：运行中材料性 amendment 率、完成后发现的隐含不变量数、无法执行的验收项比例、waiver 逾期率、同合同跨 runtime 结果差异和 contract-to-evidence 覆盖率。高 amendment 率可能说明入口澄清不足；零 amendment 也可能说明团队在聊天里偷偷改目标，需要抽检事件。

当任务探索性极强且没有稳定 verifier 时，可选择 research brief + 人工 review，而不是伪造精确合同。Agent SDD 的适用边界，是组织能否说明谁拥有目标和什么结果算可接受。

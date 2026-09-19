# 第二十七章 Agent SDD：规范驱动的任务与发布

> 证据地位：本章为作者参考设计与工程推导，案例和阈值用于说明实现逻辑，不代表跨组织验证的通用标准。

Agent SDD（Specification-Driven Delivery，规范驱动交付）把影响结果与权限的意图转换成可执行、可版本化的合同。低风险探索可以逐步明确要求；涉及不可逆或高价值动作时，必须先固定关键不变量。文档长度不是目标，执行者、验证者和批准者对“可以做什么、怎样算完成”有一致理解才是。

## 1. 六类规范

| 规范 | 回答的问题 | 推荐权威载体 |
|---|---|---|
| 业务规范 | 为什么做、价值是什么 | product/业务系统 |
| 任务规范 | 交付物、不变量、截止与预算 | CompletionContract |
| 工具规范 | 可执行动作与错误语义 | schema + effect contract |
| 策略规范 | 谁在何种条件下能做什么 | policy-as-code |
| 验证规范 | 什么证据足以证明完成 | verifier suite |
| 发布规范 | 谁能让候选产生外部效果 | release/commit policy |

自然语言可以是入口，但金额、资源范围、数据快照、禁止动作、验收项与提交权限需要结构化，否则模型、审阅者和审计者可能分别解释同一句话。

## 2. 从意图到合同

```text
intent → ambiguity/materiality detection → contract draft
→ authority confirmation → executable checks → run
```

Agent 可以查明当前提交、已有测试和数据结构，把会显著改变结果或权限的歧义交给目标负责人。合同编译器应区分信息缺失、要求冲突和有意开放的选择；实现形态可以开放，预算和评价标准仍需明确。

例如“清理老客户”并未说明多久算老、采用归档还是删除、哪些记录必须保留，以及谁批准。系统应先生成影响分析，在这些条件明确前不能自行选择90天并删除账号。

## 3. 教学实例：从规范到任务再到验收

假设仓库 `billing-api` 要修复“取消订阅后仍发送续费提醒”的缺陷。业务负责人规定：在入队提交时已经取消的订阅不得入队，账单记录保持不变，历史已发送消息不追溯删除，只允许修改通知筛选与对应测试。若筛选后发生取消，入队服务需用同一事务或版本条件确认当前状态；只在初次筛选时读取一次状态不能满足这份合同。

本书没有该生产仓库。下面的 YAML、`make typecheck` 和 `pytest tests/reminders` 都是自定义工程契约示意，须由真实项目提供实现，不能在本书仓库直接运行并宣称业务通过。原7位提交 `8f2c9d1` 是教学占位；实际输入必须解析为本次验证可读取的完整版本。

```yaml
specification:
  id: SPEC-BILLING-214
  owner: subscription-product
  snapshot: "git:<resolved-full-oid>"
  invariant:
    - cancelled_at_enqueue_commit_never_enqueued
    - invoice_state_unchanged
  intentionally_open:
    - implementation_shape

task:
  task_id: TASK-BILLING-214-01
  contract_version: v1
  deliverables:
    - sealed_patch_against_input_revision
    - evidence_package
  allowed_writes:
    - src/reminders/**
    - tests/reminders/**
  forbidden_actions:
    - production_database_write
    - production_message_send
    - billing_state_change
    - delete_or_weaken_tests
  budget:
    wall_seconds: 1800
    max_actions: 80
  commit_authority: billing-code-owner
```

### 3.1 合同怎样映射到平台对象

上面的 `specification` 与 `task` 是业务输入包，不直接符合附录 E 的 Task schema，也不是供应商配置。适配器先验证业务输入，再编译平台 Task、权限策略和完成合同，保留源字段到目标字段的映射。不能为了通过 Task 的 `additionalProperties: false` 而悄悄丢弃写入范围。

| 业务输入 | 平台映射与责任 |
|---|---|
| `specification.id`、`owner` | 进入有版本的规范对象；Task 的 `input_refs` 引用它，负责人身份由控制面核实 |
| `task.task_id`、合同版本 | 映射到 Task 的 `task_id`、`contract_version`；第二十五章的 `contract_id` 由登记表解析成不可变合同版本引用 |
| 租户、风险 | 从已认证调用者和风险策略取得 Task 的 `tenant`、`risk`，不由模型自行填高权限值 |
| `snapshot` 或第二十五章的 `workspace.commit` | 解析完整输入版本，写入 `input_refs`；证据包 `inputs` 另绑定清单及内容摘要 |
| `invariant`、交付物、禁止动作 | 分别编译为 `invariants`、`deliverables`、`forbidden_actions`，并生成可执行策略 |
| `allowed_writes` | 写入绑定合同版本的路径策略，Task引用该策略；租约与 `scope_guard` 同时执行 |
| 验收表 | Task 的 `checks` 使用稳定的候选检查ID，适配器解析为完整CompletionContract的 `pre_commit_checks`；命令与验证器版本在只读套件登记。业务提交另有 `post_commit_checks`，附录E的最小Task未展开此字段，不能直接追加到根对象 |
| `budget` | 使用 `wall_seconds`、`model_usd`、`max_actions`；旧 `wall_minutes` 乘60。旧工具调用上限不直接等同所有动作上限，须明确计数语义后转换 |
| `commit_authority` | 映射到提交责任主体，实际动作仍校验当前授权；字段值本身不是批准 |
| 运行与候选 | 控制面生成任务执行尝试的 `attempt_id`，每个逻辑动作有 `action_id`，工具重试另记ToolTry；证据包记录运行时版本、候选URI/摘要、验证器与环境、批准和最终提交 |

以下是编译后的教学 Task；所有输入引用仍是占位。适配器通过 schema 登记表选择 `task/v1` 验证，证据包使用 `evidence-package/v1`。这两个版本标识属于不同对象，不能把证据包字段直接加进不允许扩展属性的 Task 根对象。

```json
{
  "task_id": "TASK-BILLING-214-01",
  "tenant": "teaching-tenant",
  "contract_version": "CC-BILLING-214-v1",
  "risk": "R2",
  "input_refs": [
    "spec:SPEC-BILLING-214-v1",
    "git:<resolved-full-oid>",
    "policy:reminder-write-scope-v1",
    "suite:reminder-contract-v4"
  ],
  "deliverables": ["sealed_patch", "evidence_package"],
  "invariants": ["cancelled_at_enqueue_commit_never_enqueued", "invoice_state_unchanged"],
  "forbidden_actions": ["production_database_write", "production_message_send", "billing_state_change", "delete_or_weaken_tests"],
  "checks": ["compile", "reminder_regression", "sealed_cancelled_slice", "invoice_integrity", "scope_guard", "immutable_suite_guard"],
  "budget": {"wall_seconds": 1800, "max_actions": 80},
  "commit_authority": "billing-code-owner"
}
```

租户、风险和ID均为教学值。输入包、Task、候选与证据包须沿同一个 `task_id`、合同版本和输入版本连通；附录 E 的结构校验只检查形状，引用是否存在、权限是否有效和证据是否支持完成仍需独立检查。

### 3.2 固定验收与数据库权限

验证器在临时测试数据库中准备 active、past_due、cancelled 等固定样本，并测试“筛选后取消、入队前重验”的时序。执行 Agent 无生产写权限，不意味着验证器不能创建临时 fixture。候选测试只能访问隔离数据库和假消息出口，绝不能获得生产凭证。

账单完整性以调用提醒逻辑之前和之后的同一张 fixture 表比较：按固定主键排序，对合同指定的全部账单业务字段作规范序列化再求摘要，包括金额、状态和有业务意义的时间字段。只能排除预先声明的非业务元数据，不能临时忽略被候选修改的列。检查在 fixture 准备完成后取基线，执行候选后取终值，并同时检查表行数和键集合。

候选按第二十五章协议封存，在干净环境应用同一补丁后运行下列验收。公开测试可给开发反馈，封存验收由独立主体控制；删除、跳过或削弱公开测试也不能替代固定验收集。

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
    required: true
  - id: invoice_integrity
    verifier: table-hash-compare
    expect: before_hash == after_hash
    required: true
  - id: scope_guard
    verifier: changed-path-policy
    expect: changed_paths subset_of allowed_writes
    required: true
  - id: immutable_suite_guard
    verifier: frozen-suite-manifest
    expect: required_checks_unchanged_and_executed_without_suppression
    required: true
```

### 3.3 四个独立负例

从一个仅修复筛选且保留验收集的通过候选出发，每次只注入一种变化。下表是应预注册的预期结果，不宣称本书已经运行原生产项目。每列测量不同不变量，不能互相替代。

| 注入变化 | `scope_guard` | `invoice_integrity` | `sealed_cancelled_slice` | `immutable_suite_guard` |
|---|---|---|---|---|
| 无注入：授权目录内修复筛选，账单与测试不变 | PASS | PASS | PASS | PASS |
| 仅越界：另在 `src/billing/state.py` 加无行为影响的修改 | FAIL | PASS | PASS | PASS |
| 仅改账单：在允许的提醒代码中更新 fixture 账单，取消过滤仍正确 | PASS | FAIL | PASS | PASS |
| 仅保留错误入队：取消订阅仍进入提醒队列，账单不变 | PASS | PASS | FAIL | PASS |
| 仅抑制测试：业务修复正确，但删除、跳过或削弱必需测试（suppressed tests） | PASS | PASS | PASS | FAIL |

这些PASS是各隔离探针在其前提下的预期，并非发现一项FAIL后还必须执行危险代码。实际放行采用任一必需检查失败即阻断；未执行的检查明确标为未运行，不能填PASS。测试抑制负例还要求独立套件保持完整，候选工作区报告的“全绿”无权缩小验证分母。

原稿把“取消状态改回active”写成scope与invoice两项必失败，混淆了代码路径和持久化数据。越界编辑会使scope检查失败，但只改变状态解释、不写账单表时，invoice检查可以通过；提醒反而可能继续入队。上述四个负例分别构造路径越界、账单变化、行为错误和测试抑制，避免靠一个含混场景推断多个失败。

若真实过滤逻辑在未授权的 `src/queue/subscription_filter.py`，执行者应提交合同修订提案，说明路径、理由和不变的验收要求，由代码负责人批准新版本。通过检查后，证据包绑定规范、合同、输入、候选摘要和验证器；本例任务只交付补丁，合并另需提交授权。若合同本身要求合并，还要回读远端合并结果并完成所约定的后置检查。

## 4. 运行中的合同修订

执行中发现依赖与合同不兼容等新事实，可以提交修订提案。提案记录差异、理由、影响、已经发生的外部变更和所需批准；执行 Agent 不能自行扩大写入范围、降低验收或更换数据快照。批准后产生新合同版本，旧尝试继续绑定旧版，其迟到结果不自动获得新授权；后续执行从新版本开始，并对已发生副作用对账。

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

## 5. 规范怎样进入执行环境

规范应贴近权威状态：代码规则进入仓库，数据口径进入语义层，接口约束进入数据结构，安全要求进入策略引擎。上下文编译器给模型当前规范的必要部分，并保留来源与版本；只写在系统提示词中的要求难以独立执行和验证。

重复、可确定且错误代价高的要求适合编译为检查或策略。如果全部步骤已能稳定编码，直接采用确定性工作流通常更容易验收；真正需要情境判断的部分再留给模型与人。

## 6. 发布门与豁免

候选产物、合同版本和验证结果一同进入发布门；提交前再次核对授权、产物与目标版本。业务确需带已知失败上线时，豁免记录失败检查、风险负责人、补救措施、影响范围和到期时间；不可豁免的硬约束仍然阻断。Agent 可以起草说明，不能自行批准，也不能用豁免覆盖已经撤销的权限。

模型停止、候选 `checks` 通过、外部提交确认和 `post_commit_checks` 通过是不同事件。提交确认后进入 `VERIFYING_POSTCONDITIONS`，后置检查失败或未知为 `COMMITTED_BUT_UNVERIFIED`。纯成品交付合同在验收并交付后结束，不强造外部提交。第二十六章据此分别记录两类任务的完成率分母和时延。

## 7. 规范质量指标

可观察运行中的重要合同修订率、验收项未执行比例、完成后发现的不变量缺口、豁免逾期率，以及合同字段到证据的覆盖。每项说明统计窗口和分母；修订少未必表示入口清楚，也可能是团队在聊天中改了目标却未登记。

探索性任务可以采用研究简报与人工评审，将完成条件定义为资料与分析交付，并明确结论尚未验证。规范驱动交付的适用前提，是组织能说明谁拥有目标、允许哪些动作，以及什么证据足以接受结果。

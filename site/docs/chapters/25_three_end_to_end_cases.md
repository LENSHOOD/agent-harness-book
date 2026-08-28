# 第二十五章 三个贯穿案例：从意图到可验证结果

本章不试图给出某种语言的完整框架，而是用三个领域说明同一 Harness 骨架怎样落地。每个案例都回答六个问题：任务合同是什么，Agent 获得什么权力，真实副作用在哪里提交，完成由谁判定，证据怎样复建，故障时在哪里停止。

## 案例一：仓库级软件修复

### 1. 任务与合同

场景：支付服务升级日期库后，夏令时边界测试失败。Agent 可以修改 `src/time/` 与对应测试，不允许改账务规则、删除测试或联网发布；目标是生成待审 PR，而不是自行合并。

```json
{
  "contract_id": "CC-REPO-2048-v3",
  "task": "修复 DST 边界下的重复扣款时间窗计算",
  "workspace": {"repo": "payments", "commit": "8f31b6e"},
  "allowed_writes": ["src/time/**", "tests/time/**"],
  "forbidden": ["delete_tests", "change_ledger_rules", "push", "deploy"],
  "deliverables": ["git_patch", "change_explanation", "verification_results"],
  "checks": [
    "tests/time/test_dst.py::test_fall_back_window",
    "tests/time/test_dst.py::test_spring_forward_window",
    "pytest tests/time",
    "lint",
    "no_pass_to_pass_regression"
  ],
  "budgets": {"wall_minutes": 30, "model_usd": 8, "max_tool_calls": 120},
  "commit_authority": "human_code_owner"
}
```

控制面验证合同和 caller authority，创建固定 commit 的 worktree，签发只能读取仓库、写允许目录的 lease。runtime adapter 可以选择 Claude Code、Codex 或自研 Agent；无论选择谁，平台都收集 canonical Action/Observation，并保留供应商原始事件引用。

### 2. 执行与验证序列

```text
User → Control: submit contract
Control → Workspace: create worktree@8f31b6e
Control → Runtime: start(task, lease, budget)
Runtime ↔ Workspace: search/edit/test
Runtime → Control: candidate patch + self-report
Control → Verifier: clean checkout + apply sealed patch
Verifier → Control: checks + hashes + logs
Control → Reviewer: diff + contract + evidence
Reviewer → Git host: create PR (human merge remains)
```

Agent 在工作区执行测试只是反馈，不是完成证明。提交候选后，平台对 patch 做 hash 并封存，在无 Agent 写权限的 clean checkout 重跑 fail-to-pass、pass-to-pass、lint、secret scan 和允许目录检查。reviewer 只接收任务、diff 与证据，避免被长聊天中的自信叙述锚定。

```bash
git diff --binary 8f31b6e > candidate.patch
git diff --name-only 8f31b6e | sort > changed-files.txt
pytest -q tests/time
```

这些命令是案例中的可执行检查，不要求平台由 shell 实现。实际系统需把退出码、stdout/stderr artifact、环境 image 和依赖锁 hash 一并记录。

### 3. EvidencePackage

```yaml
evidence_package:
  id: EP-REPO-2048-A3
  contract: CC-REPO-2048-v3
  input_revision: git:8f31b6e
  runtime: codex-app-server@pinned-2026w34
  harness_profile: code-medium-v4
  candidate:
    patch: artifact:sha256:4b2a...
    changed_files: [src/time/window.py, tests/time/test_dst.py]
  verification:
    environment: image:sha256:91c7...
    results:
      - {check: fail_to_pass, status: pass, log: artifact:sha256:a11e...}
      - {check: pass_to_pass, status: pass, total: 482, log: artifact:sha256:b71d...}
      - {check: allowed_write_scope, status: pass}
  policy:
    decisions: artifact:sha256:29fd...
    denied_actions: 0
  final_authority: human_code_owner
```

### 4. 失败演练：visible test 投机

注入故障：Agent 发现测试使用固定日期，直接对该日期写特例。两条目标测试通过，但新增的 metamorphic test 在相邻年份失败。clean-room verifier 返回 `SPEC_GAP`，而不是把失败全文和 hidden fixture 发给 Agent；它只说明“不变量：任意有 DST 的年份都应保持同一扣款窗语义”。允许一次有界 repair。若第二候选仍只对特例打补丁，系统停止并升级领域 reviewer。

人工介入点不是“Agent 看起来困惑”时，而是合同出现材料性歧义或修复不再收敛时。失败轨迹被标为 specification/verification gap，进入回归集，但不能自动写成全局 skill。

## 案例二：企业经营分析

### 1. 任务与口径

场景：生成 2026 年 7 月中国区订阅净收入变化分析。风险不在代码合并，而在指标口径、快照一致性和敏感数据泄漏。任务合同固定 semantic metric、数据 snapshot、币种、允许维度和交付格式。

```json
{
  "contract_id": "CC-DATA-771-v5",
  "metric": "net_subscription_revenue_v4",
  "period": ["2026-07-01", "2026-08-01"],
  "comparison": "previous_month",
  "currency": "CNY_at_monthly_finance_rate",
  "snapshot": "warehouse:2026-08-03T02:00:00Z",
  "allowed_dimensions": ["province", "plan", "channel"],
  "prohibited_fields": ["email", "phone", "account_name", "raw_payment_token"],
  "deliverables": ["analysis.md", "aggregates.parquet", "query_bundle", "evidence.yaml"],
  "checks": ["metric_definition", "snapshot_consistency", "total_reconciliation", "k_anonymity_20"],
  "commit_authority": "finance_analytics_owner"
}
```

Planner 可以拆分取数、对账、解释和反证，worker 使用只读、短期、绑定 snapshot 的凭证。模型只看到聚合结果；查询由 data gateway 解析、应用 row/column policy 后执行。SQL 是 artifact，不把 warehouse credential 放入 prompt。

```sql
SELECT month, province, plan,
       SUM(recognized_revenue_cny - refunds_cny) AS net_revenue_cny,
       COUNT(DISTINCT account_id) AS accounts
FROM semantic.subscription_revenue_v4
FOR SYSTEM_TIME AS OF TIMESTAMP '2026-08-03 02:00:00+00:00'
WHERE region = 'CN'
  AND month IN (DATE '2026-06-01', DATE '2026-07-01')
GROUP BY month, province, plan
HAVING COUNT(DISTINCT account_id) >= 20;
```

### 2. 双重验证

数字验证与文字验证分开。确定性 verifier 检查查询只引用批准 semantic model、所有 artifact 使用同一 snapshot、分组汇总与财务总额在允许误差内、低基数组被抑制。解释 reviewer 检查“相关”是否被写成“因果”、是否遗漏反证、每个数字能否追溯到 aggregate cell。

```text
metric contract → policy-rewritten SQL → snapshot query
       ├─ aggregate artifact → deterministic reconciliation
       └─ narrative draft   → claim-to-cell linkage + reviewer
both pass → analyst approval → publish report
```

建议对账误差使用业务货币精度和已知舍入规则，而不是给所有指标设置统一百分比。健康指标包括 snapshot mismatch rate、unlinked numeric claim rate、suppression violations、rebuild success 和分析师实质修改率。

### 3. EvidencePackage

```yaml
evidence_package:
  id: EP-DATA-771-R2
  contract: CC-DATA-771-v5
  semantic_model: net_subscription_revenue_v4
  snapshot: warehouse:2026-08-03T02:00:00Z
  query_bundle: artifact:sha256:77ac...
  aggregates: artifact:sha256:19be...
  narrative: artifact:sha256:ae20...
  verification:
    metric_definition: pass
    snapshot_consistency: pass
    finance_reconciliation: {status: pass, delta_cny: "0.02"}
    low_count_suppression: pass
    numeric_claim_links: {linked: 37, unlinked: 0}
  approvals: [data_owner, finance_analytics_owner]
```

### 4. 失败演练：快照漂移

注入故障：第一次查询后，上游退款表完成迟到回填；Agent 的第二条查询若使用“latest”，会把两个快照混在一份报告里。gateway 发现 query snapshot 与合同不一致，返回 `SNAPSHOT_STALE_OR_MISMATCH`。系统不能偷偷刷新部分表，而应暂停、告知任务 owner 两个选择：保持原快照并标注 freshness，或批准合同 amendment 后从头重建全部 artifact。

如果 owner 选择新快照，旧 EvidencePackage 标为 superseded，不覆盖原文件；所有数字和叙述重新生成。人工介入点是改变权威数据截面，因为这会改变问题本身，而不是普通查询语法错误。

## 案例三：自我进化 Harness

### 1. 失败归因与实验合同

场景：平台观测到安装多个 MCP server 后，`wrong_tool` 错误上升。不能直接让生产 Agent 改写 tool catalog。Observability 先按模型、任务族、工具数量和错误类别聚类，形成假设“静态 schema 数量过多导致选择病理”。

```yaml
evolution_contract:
  id: EVO-TOOL-93-v2
  baseline: harness-42
  mutable_surface: tool_catalog_presentation
  frozen:
    - model
    - task_suite
    - sandbox_image
    - policy_root
    - evaluator
    - sealed_test
  candidates:
    - grouped_dynamic_discovery
    - concise_descriptions
    - task_scoped_allowlist
  primary_metric: verified_task_success
  diagnostics: [wrong_tool_rate, catalog_lookup_activation, tokens, latency]
  hard_gates: [security_non_regression, critical_slice_non_regression]
  release: shadow_then_low_risk_canary
```

Mutation workers 在独立分支生成候选。每个候选必须含 activation beacon；未实际触发新机制的 trial 不能作为因果证据。Evaluator 隔离运行多 trial，基础设施失败按预注册规则重试，仍失败计入分母而不是丢弃。

### 2. 选择与发布

```text
production traces (read-only)
  → pathology cluster + human-confirmed hypothesis
  → isolated candidate generation
  → preflight(valid + activated)
  → train/eval selection
  → one sealed-test evaluation
  → shadow → canary → promote/rollback
```

选择不是“最高均分即胜”。先检查安全与关键切片硬门，再比较主要指标置信区间和单位成功成本；多个非劣候选可按模型 profile 保留。release controller 发布完整 bundle，并让正在运行的 task 保持版本粘性。

### 3. EvidencePackage 与 lineage

```json
{
  "evidence_package": "EP-EVO-93-C7",
  "parent": "harness-42",
  "candidate": "grouped-dynamic-discovery-r4",
  "mutation_hash": "sha256:09cd...",
  "activation": {"eligible_trials": 240, "activated": 228},
  "evaluation": {
    "report": "artifact:sha256:f810...",
    "sealed_test_accessed_once": true,
    "security_gate": "pass",
    "critical_slices": "non_inferior"
  },
  "release": {"mode": "canary", "slice": "code-low-risk-5pct"},
  "rollback_bundle": "harness-42+model-12+memory-87",
  "approver": "runtime-release-owner"
}
```

### 4. 失败演练：通过修改分母“进步”

注入故障：某候选导致困难任务更常 timeout，而统计脚本只对完成 trial 求平均，分数看似提高。完整性门发现候选组 missingness 与基线显著不同，拒绝 credit；基础设施重跑仍 timeout 的 trial 计为失败。由于候选没有生产写权限，不会改动 evaluator 或删除日志。

第二个停止点在 canary：若总体成功率上升但一个高风险工具切片的错误率恶化，release controller 自动停止新流量并回滚 bundle。是否重新设计候选由人和 evolver共同决定，但生产 Agent 没有自我晋级权。这正是第二十四章“最大可信学习率”的具体实现。

## 三个案例的共用骨架

```text
intent → versioned contract → identity/workspace → runtime
→ observable actions/effects → sealed candidate
→ independent verification → approval/commit
→ evidence + telemetry → eval/evolution
```

三例的差异在工具、权威状态和风险，骨架相同。代码案例的权威状态是固定 commit，数据案例是 semantic model 与 snapshot，进化案例是冻结实验协议。平台化价值来自复用 task、identity、policy、evidence、trace 和 release，而不是迫使所有 Agent 共享一种内部思考方式。

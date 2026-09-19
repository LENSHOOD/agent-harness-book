# 实跑摘要

```json
{
  "run_dir": "/Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/execution/runs/20260919T095940Z_b_il6ikt",
  "blocks": 120,
  "markdown_files": 41,
  "zero_block_markdown_files": [
    "manuscript/appendices/B_architecture_review_checklist.md",
    "manuscript/appendices/C_glossary.md",
    "manuscript/appendices/D_concept_index.md",
    "manuscript/chapters/28_maturity_model_and_build_vs_buy.md",
    "manuscript/chapters/29_from_vendor_agents_to_owned_runtime.md",
    "manuscript/chapters/30_outlook_harness_os_and_evolving_agent_organizations.md",
    "manuscript/parts/01_history.md",
    "manuscript/parts/02_principles.md",
    "manuscript/parts/03_products.md",
    "manuscript/parts/04_evolution.md",
    "manuscript/parts/05_practice.md"
  ],
  "language_counts": {
    "text": 93,
    "json": 11,
    "yaml": 14,
    "bash": 1,
    "sql": 1
  },
  "coverage_categories": {
    "设计示意": 90,
    "仅schema验证": 2,
    "未验证": 26,
    "可运行代码": 2
  },
  "check_counts": {
    "PASS": 109,
    "FAIL": 38
  },
  "failure_severities": {
    "P2": 10,
    "P1": 25,
    "INJECTED": 3
  },
  "unexpected_results": [],
  "audit_errors": [],
  "exit_code_semantics": {
    "0": "no failing probes",
    "1": "findings/negative fixtures reproduced; read report",
    "2": "audit implementation error or unexpected result"
  },
  "exit_code": 1
}
```

## 所有失败探针

- P2 `Task_empty_check_string_rejected` — schema_only; sources=['B006']; 完整反例见 failures.json
- P2 `Task_unknown_budget_field_rejected` — schema_only; sources=['B006']; 完整反例见 failures.json
- P1 `Definitions_root_rejects_invalid_0` — schema_only; sources=['B007']; 完整反例见 failures.json
- P1 `Definitions_root_rejects_invalid_1` — schema_only; sources=['B007']; 完整反例见 failures.json
- P1 `Definitions_root_rejects_invalid_2` — schema_only; sources=['B007']; 完整反例见 failures.json
- P1 `Definitions_root_rejects_invalid_3` — schema_only; sources=['B007']; 完整反例见 failures.json
- P2 `Irreversible_requires_idempotency_key` — schema_only; sources=['B007']; 完整反例见 failures.json
- P2 `Action_empty_id_rejected` — schema_only; sources=['B007']; 完整反例见 failures.json
- P2 `Constrained_allow_requires_constraints` — schema_only; sources=['B007']; 完整反例见 failures.json
- P2 `bash_original_directly_runnable` — original; sources=['B104']; 完整反例见 failures.json
- P2 `bash_with_pytest_source_tests_exist` — original_with_audit_dependency; sources=['B104']; 完整反例见 failures.json
- P1 `bash_pipeline_propagates_git_failure` — original; sources=['B104']; 完整反例见 failures.json
- P2 `SQL_raw_SQLite` — original; sources=['B107']; 完整反例见 failures.json
- P1 `SQL_suppressed_groups_reconcile_to_finance_without_bridge` — dialect_adapter; sources=['B107']; 完整反例见 failures.json
- P1 `SQL_DUPLICATE_money_not_doubled` — dialect_adapter; sources=['B107']; 完整反例见 failures.json
- P1 `SQL_NULL_refund_preserves_100_revenue` — dialect_adapter; sources=['B107']; 完整反例见 failures.json
- P2 `SQL_NULL_account_excludes_money` — dialect_adapter; sources=['B107']; 完整反例见 failures.json
- P2 `SQL_k_gate_guarantees_numeric_revenue` — dialect_adapter; sources=['B107']; 完整反例见 failures.json
- P1 `A_approval_first_observation_defined` — faithful_simulation; sources=['B002']; 完整反例见 failures.json
- P1 `A_approval_does_not_reuse_prior_observation` — faithful_simulation; sources=['B002']; 完整反例见 failures.json
- P1 `CH6_DENY` — faithful_simulation; sources=['B037']; 完整反例见 failures.json
- P1 `CH6_approval_batch` — faithful_simulation; sources=['B037']; 完整反例见 failures.json
- P1 `CH6_cancel_in_batch` — faithful_simulation; sources=['B037']; 完整反例见 failures.json
- P1 `CH10_DENY_zero_commit` — faithful_simulation; sources=['B069']; 完整反例见 failures.json
- P1 `A_lost_response_exception_normalized` — faithful_simulation; sources=['B003']; 完整反例见 failures.json
- P1 `A_lost_response_marks_unknown` — faithful_simulation; sources=['B003']; 完整反例见 failures.json
- P1 `A_stale_lookup_setup_timeout` — faithful_simulation; sources=['B003']; 完整反例见 failures.json
- P1 `A_retry_with_stale_lookup_exactly_once` — faithful_simulation; sources=['B003']; 完整反例见 failures.json
- P1 `A_concurrent_lookup_then_execute_exactly_once` — faithful_simulation; sources=['B003']; 完整反例见 failures.json
- P1 `A_recover_terminal_cancelled_does_not_resume` — faithful_simulation; sources=['B004']; 完整反例见 failures.json
- P1 `R02_confirmed_effect_failed_health_not_verified_complete` — faithful_state_graph_translation; sources=['B068']; 完整反例见 failures.json
- P1 `CH6_compensation_alone_safe_retry_when_receipt_lost` — faithful_prose_translation; sources=['manuscript/chapters/06_agent_loop_as_a_durable_state_machine.md:112-118']; 完整反例见 failures.json
- P1 `CH27_claim_scope_and_invoice_both_fail_from_source_edit` — faithful_prose_countermodel; sources=['B118', 'B119', 'manuscript/chapters/27_agent_sdd_specification_driven_delivery.md:86']; 完整反例见 failures.json
- INJECTED `DST_baseline_visible_contract` — audit_created_fixture; sources=['B102', 'B103']; 完整反例见 failures.json
- INJECTED `DST_overfit_hidden` — deterministic_stub; sources=['B102', 'B103']; 完整反例见 failures.json
- P1 `git_raw_diff_captures_untracked_required_newfile` — faithful_protocol_fixture; sources=['B104']; 完整反例见 failures.json
- P1 `git_sealed_patch_and_tested_input_are_same` — faithful_protocol_fixture; sources=['B104']; 完整反例见 failures.json
- INJECTED `evolution_completed_only_ranking_truthful` — injected_bad_evaluator; sources=['B110', 'B111', 'B112']; 完整反例见 failures.json

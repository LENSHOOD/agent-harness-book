# Evidence registry 状态

本目录保存来源、证据与原子承重 claim。`claims_v2.jsonl` 是发布门禁使用的最小可信账本；`claims.jsonl` 是旧版段落级迁移存量，不参与严格事实门禁。

<!-- registry-status: total=84 verified=37 unverified=47 -->

当前 registry 共 84 条来源：37 条已核验、47 条未核验。审计脚本会把本行上方的机器可读状态标记与 `sources.jsonl` 实际数量比较；新增、升级或降级来源时必须同步更新，避免 backlog 声明漂移。

截至 2026-08-28，`claims_v2.jsonl` 引用的全部来源均已重新访问，填写 `accessed_at`、`version_or_commit` 与 `metadata_status=verified`。这些来源包含论文版本、官方文档网页快照和官方仓库 commit。`audit_claim_ledger.py` 会拒绝承重 claim 引用未核验来源。

47 条未核验来源是早期宽口径研究存量，其 `accessed_at` 与 `version_or_commit` 留空表示待核验。它们可以继续作为检索线索，但在升级为新的承重事实前，必须补齐元数据、claim 级 evidence 与正文限定。全部 37 条 `metadata_status=verified` 来源都必须同时具备访问日期与版本或快照；审计器会拒绝“只有 verified 标签、没有可重建定位”的记录。

`source_type` 已收敛为受控枚举：`academic_paper`、`official_documentation`、`official_article`、`official_repository`、`platform_metadata`。新增类型需先修改审计器的允许集合并说明必要性。

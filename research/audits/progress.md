# Harness 小书研究与写作进度

更新时间：2026-08-28
状态：**peer review 系统性修订完成，研究版发布门禁通过。**

## 已完成

- 完成苏格拉底式需求对齐、研究章程、来源地图与五篇结构。
- 完成序言、30 章、5 个篇导言与 5 个附录。
- 重写产品篇：Claude Code、Codex、Cursor、DeepSeek Harness/Cordis、OpenHands 和横向选型框架。
- 重写进化篇：任务内、跨任务记忆/技能、Harness、模型四层进化及统一治理闭环；篇幅达到全书 20.005%。
- 重写实践篇：三个端到端案例、企业参考架构、Agent SDD、成熟度自评、供应商接入到自研迁移和展望。
- 冻结 Agent System / Harness / Agent Runtime / Execution Runtime / Control-Evidence Services 本体，并建立概念索引。
- 建立 `claims_v2.jsonl` 原子承重 claim 账本与只读完整性审计；当前 24/24 为 supported。
- 修复 PDF 可复现生成、站点同步清理、GitHub Actions 门禁和 PDF 下载路径。
- 完成完整版与管理层版 PDF 的首中末页视觉抽查。

## 当前规模

- 61,975 个中文正文字符（去 fenced code）。
- 进化篇 12,398 字，占 20.005%。
- 84 个登记来源、69 条持久化 evidence、24 条原子承重 claim。
- 25 个 JSON/YAML/SQL/Bash/Python/Mermaid 等机器可读或可执行载体代码块。
- 完整版 137 页；管理层版 14 页；均为 A4。

## 发布门禁

```bash
.venv/bin/python publishing/scripts/audit_claim_ledger.py
.venv/bin/python publishing/scripts/build_book.py
.venv/bin/python publishing/scripts/render_publications.py
.venv/bin/python publishing/scripts/prepare_site.py
npm --prefix site run docs:build
```

上述命令已在 2026-08-28 按顺序运行并通过。详细结果见 `quality_audit.md` 与 `peer_review_disposition_20260828.md`。

## 后续维护原则

- 产品事实按日期/版本表达，变更时同步更新 source、evidence 与 claim。
- 厂商口径、研究结果、作者推导和设计建议保持显式区分。
- 自我进化主张必须说明可变对象、观测信号、归因、评价隔离、门禁、发布与回滚。
- 网页与 PDF 只从 `manuscript/` 和构建脚本生成，不直接编辑派生产物。
- 每次公开更新至少通过 claim audit、站点构建和 PDF 抽样视觉验收。

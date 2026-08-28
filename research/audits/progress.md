# Harness 小书研究与写作进度

更新时间：2026-08-28
状态：**第五轮闭环验收完成；研究版发布门无遗留项，评审系列关闭。**

## 已完成

- 完成苏格拉底式需求对齐、研究章程、来源地图与五篇结构。
- 完成序言、30 章、5 个篇导言与 5 个附录。
- 重写产品篇：Claude Code、Codex、Cursor、DeepSeek Harness/Cordis、OpenHands 和横向选型框架。
- 重写进化篇：任务内、跨任务记忆/技能、Harness、模型四层进化及统一治理闭环；新增跨层升级/降层判据，篇幅达到全书 20.949%。
- 重写实践篇：三个端到端案例、企业参考架构、Agent SDD、成熟度自评、供应商接入到自研迁移和展望。
- 冻结 Agent System / Harness / Agent Runtime / Execution Runtime / Control-Evidence Services 本体，并建立概念索引。
- 建立 `claims_v2.jsonl` 原子承重 claim 账本与只读完整性审计；当前 25/25 为 supported，28 个承重来源元数据完整。
- 建立 30 章单一标题源与结构审计；修复 PDF 书签层级、图片渲染和代码实体显示。
- 修复 PDF 可复现生成、站点资源同步、GitHub Actions 门禁及 GitHub Pages 下载路径。
- 在第 5、19、25 章加入三张承重关系图，并完成完整版与管理层版关键页视觉抽查。
- 第 27 章补完整规范→任务→验收实例；第 29 章补六阶段进入、退出与回退条件。
- 完成第四轮逐项验收：补齐第 18 章资料截面，精确区分 Pi 连续原句与非连续拼接引文，并将发布、产品巡检、外部盲审和导航短标题规则制度化。
- 将最终质量审计绑定到不可变内容 commit，而不是会移动的分支名。
- 第五轮独立记录复测第四轮全部处置并确认闭环；该轮没有新增正文问题，因此不制造无依据的内容改动。

## 当前规模

- 64,719 个中文正文字符（去 fenced code）。
- 进化篇 13,558 字，占 20.949%。
- 84 个登记来源（37 verified、47 unverified backlog）、71 条持久化 evidence、25 条原子承重 claim。
- 27 个非 text 机器可读或运维载体代码块：YAML 14、JSON 11、Bash 1、SQL 1；另有 3 张带 Graphviz 源文件的关系图。
- 完整版 135 页；管理层版 14 页；均为 A4。

## 发布门禁

```bash
.venv/bin/python publishing/scripts/audit_claim_ledger.py
.venv/bin/python publishing/scripts/check_book_structure.py
.venv/bin/python publishing/scripts/build_book.py
.venv/bin/python publishing/scripts/render_publications.py
.venv/bin/python publishing/scripts/prepare_site.py
npm --prefix site run docs:build
```

上述命令已在 2026-08-28 按顺序运行并通过。详细结果见 `quality_audit.md`、四份处置报告与 `审阅记录_第五轮闭环_20260828.md`。

## 后续维护原则

- 产品事实按日期/版本表达，变更时同步更新 source、evidence 与 claim。
- 厂商口径、研究结果、作者推导和设计建议保持显式区分。
- 自我进化主张必须说明可变对象、观测信号、归因、评价隔离、门禁、发布与回滚。
- 网页与 PDF 只从 `manuscript/` 和构建脚本生成，不直接编辑派生产物。
- 每次公开更新至少通过 claim audit、站点构建和 PDF 抽样视觉验收。
- 正式 1.0 前执行外部盲审；产品章节按月巡检，资料截面超过 45 天时发布前强制复核。

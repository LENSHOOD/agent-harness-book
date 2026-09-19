# Agent Harness 小书：项目导航

这是《Agent Harness：从执行脚手架到自我进化系统》的研究、写作与发布工作区。

- 在线阅读：https://lenshood.github.io/agent-harness-book/
- GitHub 仓库：https://github.com/LENSHOOD/agent-harness-book

## 目录说明

| 目录 | 用途 | 是否为正文/发布必需 |
| --- | --- | --- |
| `manuscript/` | 小书的唯一正文源，包括篇导言、章节、附录和正文资源 | 是 |
| `examples/` | 可运行参考实现、合成数据、正反测试与本地运行证据 | 是，案例验证入口 |
| `research/` | 研究过程资产：规划、笔记、证据账本与质量审计 | 是，支持溯源与修订 |
| `publishing/` | 出版流水线：构建脚本、可交付文件和临时校验产物 | 是 |
| `site/` | VitePress 在线阅读前端，由根目录仓库统一管理 | 是 |
| `.venv/` | 本机 Python 依赖环境，不属于书稿内容 | 仅本地构建需要 |

### `manuscript/`

- `chapters/`：序章及第 1—30 章 Markdown 源稿。
- `parts/`：五篇的篇级导言，说明章节依赖与本篇产出。
- `appendices/`：附录源稿。
- `assets/`：正文引用的图片、图表及其可再生源文件。
- `executive_brief.md`：管理层精简版的源稿；出版目录中的同名文件由构建脚本生成。

### `examples/`

- `src/`：Git/DST修复、SQLite分析、进化门禁和安全状态模型。
- `tests/`：正常路径、拒绝、回执丢失、重复提交、坏候选等回归检查。
- `run_examples.py`：统一执行入口，输出退出码、源码hash、日志和结果；不调用收费模型或真实业务系统。
- `runs/`：按时间保存的合成测试证据。详细环境和边界见该目录的README。

### `research/`

- `planning/`：研究章程、目录演进、核心论点、来源地图和专项证据复核。
- `notes/`：分轮次的检索与综合笔记。
- `evidence/`：`sources.jsonl`、`evidence.jsonl`、人工标注的 `claims_v2.jsonl` 和运行清单，构成可机读证据链；`claims.jsonl` 是旧版段落级账本，仅作迁移参考。
- `audits/`：进度记录与质量审计结果。
- `maintenance/`：产品事实巡检、版本发布和外部盲审的维护制度。

2026-09-19原始审阅位于`audits/review_20260919/`，修订处置与发布验收位于`audits/revision_20260919/`。公开证据包含短摘、URL、固定版本、hash与运行结果；网页全文缓存、上游仓库批量源码、生成schema副本和本机运行时数据库保留为本地缓存，不上传。`public_evidence_index.json`保留相应抓取定位和摘要。

### `publishing/`

- `scripts/`：合并书稿、审计 claim ledger、渲染出版物、同步网站内容的脚本。
- `artifacts/`：完整书稿和决策者精简版的 Markdown、HTML、PDF 成品。
- `work/`：PDF 页面渲染和文本抽取等临时校验产物，可按需重建。

### `site/`

这是 VitePress 在线阅读前端。它与书稿、研究资料和出版流水线由根目录的同一个 Git 仓库管理；GitHub Actions 只构建并发布该子目录。正文修改应先发生在 `manuscript/`，再通过同步脚本复制到网站，避免形成两个正文源。

## 常用命令

在本目录执行：

```bash
.venv/bin/python -m pip install -r requirements.txt -r requirements-examples.txt
.venv/bin/python examples/run_examples.py
.venv/bin/python publishing/scripts/audit_claim_ledger.py
.venv/bin/python publishing/scripts/check_book_structure.py
.venv/bin/python publishing/scripts/build_book.py
.venv/bin/python publishing/scripts/render_publications.py
.venv/bin/python publishing/scripts/prepare_site.py
npm --prefix site run docs:build
```

尚无Python环境时先运行`python3 -m venv .venv`。也可以按`examples/README.md`为示例单独建环境；脚本没有个人uv缓存依赖。

推荐顺序是：修改源稿与示例 → 案例回归及证据/结构检查 → 构建合订稿 → 渲染出版物 → 同步站点 → 构建网站。PR运行检查但不部署，合并到main后自动发布GitHub Pages。

## 文件职责原则

1. 正文只在 `manuscript/` 编辑。
2. 新来源与论据进入 `research/evidence/`，研究过程记录进入 `research/notes/`。
3. 生成文件进入 `publishing/artifacts/`，临时检查文件进入 `publishing/work/`。
4. `site/` 只承担在线呈现，根目录 `.github/workflows/` 负责自动部署。

## 审查状态

2026-09-19进行了增量研究、逐章复审和实际案例验证，并据此修订正文。此前关于“技术含义守恒”和字数的过度结论已经公开勘误；历史评审关闭不代表后续版本没有问题。当前验收结果见`research/audits/quality_audit.md`及本轮处置报告。

来源登记检查、语义复核、示例执行和出版构建分别报告。原子账本覆盖核心主张子集；示例是明确条件下的本地参考，不代表商业Agent、真实模型矩阵或生产安全认证。正式1.0仍须完成外部盲审与产品事实巡检，制度见`research/maintenance/`。

# Agent Harness 小书：项目导航

这是《Agent Harness：从执行脚手架到自我进化系统》的研究、写作与发布工作区。

- 在线阅读：https://lenshood.github.io/agent-harness-book/
- GitHub 仓库：https://github.com/LENSHOOD/agent-harness-book

## 目录说明

| 目录 | 用途 | 是否为正文/发布必需 |
| --- | --- | --- |
| `manuscript/` | 小书的唯一正文源，包括篇导言、章节、附录和正文资源 | 是 |
| `research/` | 研究过程资产：规划、笔记、证据账本与质量审计 | 是，支持溯源与修订 |
| `publishing/` | 出版流水线：构建脚本、可交付文件和临时校验产物 | 是 |
| `site/` | VitePress 在线阅读前端，由根目录仓库统一管理 | 是 |
| `.venv/` | 本机 Python 依赖环境，不属于书稿内容 | 仅本地构建需要 |

### `manuscript/`

- `chapters/`：序章及第 1—30 章 Markdown 源稿。
- `parts/`：五篇的篇级导言，说明章节依赖与本篇产出。
- `appendices/`：附录源稿。
- `assets/`：正文引用的图片、图表及其可再生源文件。

### `research/`

- `planning/`：研究章程、目录演进、核心论点、来源地图和专项证据复核。
- `notes/`：分轮次的检索与综合笔记。
- `evidence/`：`sources.jsonl`、`evidence.jsonl`、人工标注的 `claims_v2.jsonl` 和运行清单，构成可机读证据链；`claims.jsonl` 是旧版段落级账本，仅作迁移参考。
- `audits/`：进度记录与质量审计结果。
- `maintenance/`：产品事实巡检、版本发布和外部盲审的维护制度。

### `publishing/`

- `scripts/`：合并书稿、审计 claim ledger、渲染出版物、同步网站内容的脚本。
- `artifacts/`：完整书稿和决策者精简版的 Markdown、HTML、PDF 成品。
- `work/`：PDF 页面渲染和文本抽取等临时校验产物，可按需重建。

### `site/`

这是 VitePress 在线阅读前端。它与书稿、研究资料和出版流水线由根目录的同一个 Git 仓库管理；GitHub Actions 只构建并发布该子目录。正文修改应先发生在 `manuscript/`，再通过同步脚本复制到网站，避免形成两个正文源。

## 常用命令

在本目录执行：

```bash
.venv/bin/python publishing/scripts/build_book.py
.venv/bin/python publishing/scripts/render_publications.py
.venv/bin/python publishing/scripts/audit_claim_ledger.py
.venv/bin/python publishing/scripts/prepare_site.py
npm --prefix site run docs:build
```

推荐顺序是：修改 `manuscript/` → 构建合订稿 → 渲染出版物 → 同步 `site/` → 构建网站。

## 文件职责原则

1. 正文只在 `manuscript/` 编辑。
2. 新来源与论据进入 `research/evidence/`，研究过程记录进入 `research/notes/`。
3. 生成文件进入 `publishing/artifacts/`，临时检查文件进入 `publishing/work/`。
4. `site/` 只承担在线呈现，根目录 `.github/workflows/` 负责自动部署。

## 审查状态

截至 2026-08-28，本评审系列已由第五份独立审阅记录确认闭环：研究版发布门无 P0/P1/P2 遗留，产品、进化和实践篇完成系统性重写，证据账本迁移到原子 claim 只读校验，PDF/站点流水线可复现。五份审阅文档、四份处置报告和机器校验报告位于 `research/audits/`；正式 1.0 前的外部盲审与产品事实巡检要求见 `research/maintenance/`。

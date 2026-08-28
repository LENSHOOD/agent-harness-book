# 最终质量审计

审计日期：2026-08-28

适用版本：`codex/peer-review-revision` 分支本轮修订稿

结论：**通过研究版发布门禁；不等同于同行评议学术出版。**

## 1. 交付完整性

- 1 篇序、30 章正文、5 个篇导言、5 个附录、研究方法与完整参考文献均已纳入统一构建。
- 去除 fenced code 后，`manuscript/chapters + parts + appendices` 共 64,677 个中文正文字符，达到研究章程 6–10 万字下限。
- 第 19–24 章“进化篇”共 13,558 个中文正文字符，占上述口径 20.963%，超过 20.8% 的评审缓冲要求，不再贴线达标。
- 产品篇覆盖 Claude Code、Codex、Cursor、DeepSeek Harness/Cordis、OpenHands，并使用统一六轴比较与企业接入风险分析。
- 实践篇包含三个端到端案例、完整合同/证据包实例、失败演练、企业 SLO、SDD、成熟度自评与迁移退出判据。
- 附录 A–E 分别提供安全核心契约、可判定检查表、冻结术语本体、概念索引与机器可读 schema。

## 2. 事实与证据

- 来源 registry：84 条；持久化 evidence：71 条；`claims_v2.jsonl`：25 条人工定义的原子承重 claim；正文外部链接：69 条。
- 25 条承重 claim 使用的 28 个来源已全部填写访问日期、版本或 commit，并标记为 `verified`；来源类型收敛为 academic paper、official documentation、official article、official repository、platform metadata 五类。其余未核验来源明确作为历史存量，不冒充承重证据。
- 原子 claim 分为 `historical_fact`、`research_result`、`vendor_claim`，全部绑定具体 source/evidence；厂商数字标出供应商口径，2026 年演化研究标出预印本边界。
- `audit_claim_ledger.py` 已改为只读校验：不再根据 URL 自动推断事实类型，也不写回账本；同时校验 claim/source/evidence 引用完整性、严格类型支撑状态、正文链接登记与含括号 DOI 解析。
- 本轮运行结果：`PASS`，25/25 原子承重 claim 为 `supported`，无未登记正文链接。
- 旧 `claims.jsonl` 保留为迁移审计材料，不再作为发布门禁的事实账本。

## 3. 构建与发布

- 依赖由 `requirements.txt` 固定；PDF 由 ReportLab 直接从合并 Markdown 生成，不再依赖本机缺失的 GObject/WeasyPrint 运行时。
- `prepare_site.py` 会先清理并重新同步 chapters、parts、appendices、assets 和下载文件，避免网页与 PDF 版本漂移。
- `publishing/book_structure.json` 是 30 章标题的单一来源；构建脚本和 VitePress 侧边栏共同读取，CI 另以 `check_book_structure.py` 校验源稿 H1。
- GitHub Actions 依次执行 claim audit、结构审计、合并书稿、生成 PDF、同步站点和 VitePress 构建；本地以同样顺序复现通过。
- VitePress 构建完成；最终 dist 的错误 `/downloads/` 链接为 0，45 处完整版入口均为 `/agent-harness-book/downloads/agent_harness_book.pdf`。CI 在构建产物上设置正反双向门禁。

## 4. PDF 验收

- 完整版：135 页，A4，1,012,021 bytes；文本可提取 257,525 字符，无替换字符或空白页。
- 管理层版：14 页，A4，67,652 bytes。
- PDF 书签含 5 个篇节点和 30 个章节点；篇层级为 0，所有章层级为 1，章节已正确嵌套。
- 第 5、19、25 章三张 Graphviz 关系图已进入网页与 PDF；JSON/YAML 中的引号以最终 PDF 抽查确认未被渲染为 HTML 实体。
- Latin 封面字体以 ReportLab 自带 TrueType 字体嵌入，避免默认未嵌入 Helvetica 在部分渲染器中不可见。
- 抽查完整版封面、目录、表格/代码页、进化篇新增页、参考文献末页，以及管理层版首末页；未发现裁切、重叠、黑块、缺字或不可见标题。

## 5. Peer review 处置

前两轮逐条判断见 `peer_review_disposition_20260828.md`，第三轮判断与修复见 `peer_review_disposition_round3_20260828.md`。第三轮 12 项均有可复现依据并已落实；旧处置报告的 D-1 至 D-5 失实/漏报已在原报告文末公开勘误，未静默改写历史记录。

## 6. 已知边界

- 25 条原子 claim 是承重主张子集，不代表逐句学术事实核查；设计推导、规范性建议与非承重背景材料仍依赖正文限定和内联来源。
- 产品能力以 2026-08-28 为资料截面，供应商功能、协议与安全边界会继续变化。
- Self-Harness、GSME、Living-Harness、HSI 等 2026 年材料在本截面仍以预印本为主，缺少长期生产复现。
- 厂商内部指标不外推为行业总体；未公开实现只作为推断或集成假设表达。
- 对外发布后仍建议邀请独立领域专家做一次盲审，尤其核查安全、训练数据治理和产品版本更新。

## 7. 最终判定

本修订稿已经满足“真实可追溯、结构完整、体系闭合、工程可落地、表述边界明确、发布可复现”的研究版要求。它可以进入公开阅读和同行反馈阶段；后续变更应继续由 claim audit、站点构建和 PDF 视觉抽查共同把关。

# 《Agent Harness》全量质量审查报告

审查日期：2026-08-23  
审查基线：`main@e57a958`  
审查范围：`manuscript/`、`research/evidence/`、`publishing/`、`site/`、GitHub Pages 线上版本  
审查方式：正文与证据账本静态分析、重点事实全网复核、四个独立视角复审、本地构建、线上链接与移动端读者旅程测试

## 1. 最终判定

状态：**DONE_WITH_CONCERNS，不建议把当前版本标记为“事实审查通过”或“正式定稿”。**

当前稿已经具备一本 Harness 技术书的主干，尤其是第 5—11 章对系统模型、状态机、上下文、工具、安全、验证和多 Agent 的讨论。但它仍呈现“前半部接近成稿，后半部接近扩展提纲”的不均衡状态。更严重的是，现有 claim ledger 不能证明正文事实获得 claim-level 支持；核心术语在跨章使用时存在边界冲突；公开站点有 PDF 下载断链和网页/PDF 版本漂移风险。

| 质量门 | 评分 | 判定 | 主要原因 |
| --- | ---: | --- | --- |
| 真实性与可审计性 | 4.0/10 | 不通过 | claim 非原子化、自动分类错误、75/75 来源元数据未验证 |
| 完整性 | 6.0/10 | 有条件不通过 | 章节齐全，但产品、进化、企业实践和展望明显提纲化 |
| 体系化 | 6.5/10 | 有条件不通过 | 原理篇较强，核心本体、贯穿案例和后半部闭环不足 |
| 无歧义与可实现性 | 7.2/10 | 有条件不通过 | Agent/Harness/Runtime/Memory 边界漂移，部分伪代码不具崩溃安全性 |
| 网站与发布工程 | 6.4/10 | 有条件不通过 | 阅读主路径可用，下载断链、PDF不可复现、CI门禁不足 |
| 综合出版成熟度 | **6.0/10** | **大修后复审** | 可作为公开测试稿，不应作为已完成的权威参考书 |

## 2. 审查基线与可量化结果

- 正文：序章加 30 章、3 个附录。
- 登记来源：75。
- 持久化 evidence：69。
- claim 单元：222。
- 有 source 的 claim：69/222，31.1%。
- 有 evidence ID 的 claim：68/222，30.6%。
- `supported`：4/222，1.8%。
- `partial`：36/222，16.2%。
- `needs_review`：29/222，13.1%。
- `unsupported`：153/222，68.9%。
- 至少两个来源的 claim：11/222，5.0%。
- 至少三个来源的 claim：2/222，0.9%。
- 75 个来源的 `metadata_status` 全部为 `unverified`。
- 31 个章节中有 9 个没有外部链接。
- 线上站点主体、章节、搜索、移动导航和 sitemap 可用；两个公开 PDF 入口指向错误根路径。

这些数字不能解释为“30.6% 的事实已验证”。当前 claim 与 evidence 的关联算法会把同一来源的全部 evidence 自动绑定给引用该来源的整节内容，因此真实的语义支持率只会更低。

## 3. P0：阻止定稿的问题

### P0-1 Claim ledger 的分类规则无效

位置：`publishing/scripts/audit_claim_ledger.py:25`

当前逻辑：

```python
c['claim_type'] = 'factual' if sids else 'synthesis'
```

这等价于“段落中有 URL 就是事实，没有 URL 就是作者综合”。事实与综合是语义属性，不是排版属性。大量无链接段落仍包含产品能力、历史结论、经验性因果和安全效果，却被排除在事实硬门之外。

修订要求：将 claim 类型改为受控枚举：`fact`、`vendor_claim`、`research_result`、`inference`、`recommendation`、`forecast`；分类必须基于命题语义。

### P0-2 Evidence 不是 claim-level 绑定

位置：`publishing/scripts/audit_claim_ledger.py:24`

当前脚本只要发现 claim 引用了某来源，就把该来源下所有 evidence 全部附给 claim。这会制造错误支持关系。一个来源的 A 段不能自动支持正文中引用同一来源的 B 命题。

修订要求：每条原子 claim 显式选择 evidence span，记录 locator、支持方向、entailment 判定、复核人和复核日期。

### P0-3 Claim 单元不是原子命题

`claims.jsonl` 的首条记录同时包含 STRIPS 历史事实、coding agent 类比、经典规划假设、ReAct 解释和设计建议。单个来源不可能支持整组异质命题，也无法形成有意义的 `supported/partial` 判定。

修订要求：一个 claim 只表达一个可证伪命题。事实、推断和建议必须拆开。

### P0-4 来源无法重建时间截面

75/75 来源元数据未验证。很多 GitHub URL 指向可变化的 `main/master`，产品网页也没有保存发布日期、访问日期、版本或内容 hash。因此“事实截至 2026-08-22”目前只是声明，不是可复现快照。

修订要求：

1. 论文核对 DOI/arXiv 元数据并区分预印本与同行评审。
2. GitHub 来源固定 commit SHA 和文件行号。
3. 动态网页记录发布日期、访问日期、页面标题和内容 hash；必要时保存归档。
4. 统一来源类型枚举，单列 `publication_status` 和 `vendor_reported`。

### P0-5 全书核心本体存在冲突

序言和术语表倾向于把环境、反馈、安全和验证整体纳入 Harness；第 5 章则明确把 `Model × Harness × Environment × Feedback` 分开。这个冲突会向产品比较、参考架构和成熟度模型传播。

修订要求：冻结唯一顶层本体：

```text
Agent System
├── Agent Core：基于模型选择下一动作的决策组件
├── Harness：上下文、循环、动作协议、状态、策略、验证编排与可观测
├── Environment：仓库、文件、浏览器、数据库、SaaS、CI 与人类组织
└── Feedback：观察、测试、评价、审批和业务结果

Harness
├── Agent Runtime：loop、context、session、delegation
├── Execution Runtime：进程、文件、浏览器、网络副作用
└── Control/Evidence services：policy、identity、trace、verifier、commit gate
```

正文避免无修饰地使用 `Runtime`；必须写明 `Agent Runtime`、`Execution Runtime` 或 `Harness Runtime`。

## 4. P1：高优先级内容问题

### P1-1 第 3、4 章重复

第 3 章已经讨论 Aider、SWE-agent、CodeAct、OpenHands 和 benchmark，第 4 章再次按近似顺序重复。第 5 章还保留“第四章将在历史资料补齐后撰写”的过时状态说明。

建议：保留第 3 章作为 ACI/接口工程史；把第 4 章重写为“代码仓库为何成为第一个高价值、可执行、可验证的 Agent 环境”，删除重复产品介绍，并解释 coding 经验如何迁移到浏览器、数据和业务系统。

### P1-2 后半部篇幅和论证成熟度断崖式下降

第 6—11 章多数达到 4,600—9,700 个非空白字符；第 13—18 章多数只有 1,200—1,700；第 19—24 章多数不足 1,200；第 25—30 章除第 26 章外多在 740—1,100。章节标题完整不等于内容完整。

优先扩充：第 12 章可观测性、第 18 章产品比较、第 20—24 章四层进化、第 25 章贯穿案例、第 26—29 章企业运营、第 30 章可证伪展望。

### P1-3 四层进化有分类，缺统一证据模板

四层模型是全书有价值的原创框架，但当前各章主要是机制摘要。建议四层统一采用：可变对象、不可变根信任、反馈周期、数据要求、评价方法、正案例、失败案例、最小实现、晋级门、回滚和验收指标。

新增研究应至少覆盖并明确标注为 2026 年预印本的 Self-Harness、Living-Harness、GSME、HSI、AHE，以及对“harness 能更新”和“模型能从更新中获益”的解耦研究。新论文只能支持研究方向，不能被表述为生产共识。

### P1-4 三个案例没有真正贯穿

软件工程、企业数据分析和自我进化案例在第 25 章才集中出现。建议在第 5 章冻结三份 task contract，在第 6—12 章各加入同一对象的切片，最终在第 25 章形成三条完整轨迹：

```text
Intent → Contract → Context → Action → Policy → Effect
       → Verification → Commit → Learning / Rollback
```

每条轨迹必须包含失败分支、人工升级点、崩溃恢复和 evidence package。

### P1-5 产品比较不能支持企业选择

第 18 章当前矩阵主要是产品定位。需要拆成：

1. 公开能力事实矩阵，每个单元格带官方来源或 `not documented`。
2. 架构取舍矩阵，明确哪些是作者推断。
3. 企业适配矩阵：身份、权限、resume/cancel、trace 导出、verifier、多租户、数据驻留、协议兼容、SLA、模型替换、退出成本和 eval 接口。

“五者共同收敛”应改成带时间截面和证据范围的作者归纳，不能暗示五个产品均已具备完整能力集合。

### P1-6 案例外部效度局限

五个主案例都属于 coding agent 或通用 agent runtime。若书名保持通用 Harness，应补浏览器/computer-use、企业工作流、数据分析或高风险人在环场景。也可以把范围明确收窄为“以 coding agent 为主要样本的企业 Harness 设计”。

### P1-7 企业篇缺少运营系统

参考架构有组件，但缺 RACI、SLO、容量与成本、事故响应、数据驻留与删除、供应商尽调、POC 上线门、退出演练、人工介入率和 ROI。成熟度模型应为每一级增加必备能力、退出条件、禁止动作、组织责任、指标和典型事故。

## 5. P1：高风险事实与表达

以下命题需要优先逐条复核或降级措辞：

1. `manuscript/chapters/18_product_comparison_and_architecture_spectrum.md:32`：五产品“共同收敛”到完整能力集合。
2. 同文件第 18 行：Pi 不内置多项能力，且来源账本存在两个 Pi 仓库身份。
3. `06_agent_loop_as_a_durable_state_machine.md:196`：Codex 使用 worktree 隔离不同线程，未区分 App、CLI 和云形态。
4. `14_openai_codex_protocolized_agent_core.md:9`：App Server 已统一暴露给 CLI、IDE、桌面和其他客户端，可能混淆“已接入”“可接入”和“计划迁移”。
5. `07_context_cache_compaction_and_memory.md:96`：Claude 与 Codex compaction 事实混在同一 claim，只绑定 Claude 来源。
6. `09_permissions_sandbox_credentials_and_supply_chain.md:34`：84% permission prompt 降幅应明确为 Anthropic 内部、厂商报告数据。
7. `11_multi_agent_delegation_and_collaboration_topologies.md:29`：95%、80%、4×、15× 来自特定厂商系统与 BrowseComp，不能外推为普遍规律。
8. 同文件第 37 行：“低价值任务无法覆盖 10 倍级成本”应改为条件性建议或给成本模型。
9. `17_openhands_agent_runtime_separation.md:9`：Event Stream “允许重放与插入策略”需要代码或官方 API 证据，否则只能写成架构可能性。
10. 第 23 章模型进化没有外部引用，却包含大量训练方法和风险事实。
11. `08_tools_aci_mcp_and_code_mode.md:121`：大量工具 schema 降低选择准确率，需要限定模型、规模和厂商观察范围。
12. 同文件第 104 行：MCP Authorization 的 MUST、SHOULD 和安全指南被合并成同一强制集合。
13. `20_within_task_evolution_search_reflection_and_repair.md:7`：Reflexion “证明”应改为“在论文所测任务中展示”。
14. `30_outlook_harness_os_and_evolving_agent_organizations.md`：预测应明确条件、时间尺度和反方情景。

## 6. 无歧义与伪代码审查

术语一致性综合评分为 72/100。最弱项为 Runtime 55、Memory 60、Agent 66、Skill 68。

### 必须修正的伪代码

- `appendices/A_core_contracts_and_pseudocode.md:14`：先 `executor.commit()` 后 `ledger.append()`，崩溃时会产生正文强调的未知提交窗口；Action 也没有 idempotency key。必须先持久化 effect intent，再提交并记录 receipt，恢复时查询或对账。
- 同文件第 8、31 行：`event_offset` 与 `checkpoint.offset` 字段不一致，且没有说明 replay 边界是否包含 offset。
- `06_agent_loop_as_a_durable_state_machine.md:216`：`current_state` 未定义；审批挂起后没有明确返回、恢复和重新授权语义。
- `10_verification_completion_contracts_and_evidence_packages.md:182`：`results += verifier.run(...)` 返回类型不明；审批持久化和过期后重验缺失。
- `11_multi_agent_delegation_and_collaboration_topologies.md:255`：`ttl=spec.deadline` 混淆绝对时间与持续时间；异常路径没有撤销 lease/capability 和清理 workspace。

## 7. 网站、设计与发布流水线

### P1-8 两个 PDF 入口线上 404

站点 `base` 是 `/agent-harness-book/`，但导航和首页 CTA 使用 `/downloads/...` 根域路径。实际错误 URL：

```text
https://lenshood.github.io/downloads/agent_harness_book.pdf
```

正确文件位于：

```text
https://lenshood.github.io/agent-harness-book/downloads/agent_harness_book.pdf
```

### P1-9 网页和 PDF 可能来自不同版本

CI 运行 `prepare_site.py` 和 VitePress 构建，却不重建完整书稿与 PDF。修改 `manuscript/` 后，网页会更新，复制到下载区的已提交 PDF 可能仍是旧稿。

### P2 发布工程问题

- `manuscript/` 是唯一正文源目前只是约定，CI 没有同步后 `git diff --exit-code` 门禁。
- `prepare_site.py` 不清除已经从源稿删除的旧章节，可能部署幽灵页面。
- PDF 无仓库内完整生成命令、Python lock、渲染器和字体环境，无法在新机器确定性重建。
- VitePress 构建链报告 2 个中危、1 个高危开发依赖漏洞；静态产物无生产依赖漏洞。
- CI 没有 base-aware 内链、外链、可访问性、生成物漂移和 PDF/正文一致性检查。
- GitHub Actions 使用浮动 major tag，较高完整性场景应锁 SHA。

### 设计与可访问性

- 375px 移动端无横向溢出，导航、搜索和翻章可用。
- 正文被缩到 15px，并全局使用 `word-break: break-all`；建议至少 16px 并改为 `overflow-wrap:anywhere`。
- CTA、代码复制和标题锚点的部分点击区域小于 44×44px。
- 移动目录一次展示 30 章和附录，建议默认只展开当前篇。
- 站点视觉清晰但接近 VitePress 默认主题，品牌辨识度一般。这是改进项，不是发布阻塞项。

## 8. 本轮全网增量复核

本轮以官方文档和原始论文为优先来源，确认以下增量：

- Claude Agent SDK 官方文档明确公开 agent loop、工具执行和 compaction 边界，并提醒 compaction 可能丢失早期细节：https://code.claude.com/docs/en/agent-sdk/agent-loop
- OpenAI 对 Codex 的安全说明继续把 sandbox 与 approval policy 视为不同控制层：https://openai.com/index/running-codex-safely/
- Cursor 当前 Cloud Agents 文档公开独立分支、source control 接入和多类 hooks：https://cursor.com/docs/cloud-agent
- LangGraph 官方当前明确区分 Deep Agents（harness）、LangChain（framework）和 LangGraph（runtime）：https://docs.langchain.com/oss/python/concepts/products
- Living-Harness 是 2026-07 预印本，报告在特定交互环境中获得提升，不构成生产成熟证明：https://arxiv.org/abs/2607.26598
- Gated Semantic Quality-Diversity 强调提案与确定性 credit 分离以及 sealed test：https://arxiv.org/abs/2607.13683
- Hierarchical Self-Improvement 是 2026-08 新预印本，需要在书中标明新近、未独立复现：https://arxiv.org/abs/2608.08466
- Harness Updating Is Not Harness Benefit 直接指出“能产生 harness 更新”与“能从更新获益”需要解耦：https://arxiv.org/abs/2605.30621
- Agentic Harness Engineering 把 component、experience、decision observability 作为进化闭环，但其 benchmark 结果仍需外部复现：https://arxiv.org/abs/2604.25850

这些新材料总体支持本书“提案者与评价者分离、held-out、回滚、可观测”方向，但也要求降低“已经可自主进化”的语气。

## 9. 推荐修订顺序

### Wave 0：立即修复发布断点

1. 修复 PDF base path。
2. 清理过时章节状态说明。
3. 给 CI 增加站点最终 URL 断链检查。

### Wave 1：冻结本体和证据系统

1. 重写术语表并冻结 Agent Core、Agent System、Harness、Agent Runtime、Execution Runtime、Environment、Feedback、State、Memory、Skill。
2. 重做 atomic claim schema 和 extractor。
3. 逐条绑定 evidence span，验证 75 个来源元数据。
4. 产品来源固定版本和时间快照。

### Wave 2：修复书稿结构

1. 重构第 3、4 章。
2. 扩写第 12、18、20—25 章。
3. 用三个统一案例贯穿第 5—12 章。
4. 把企业篇扩展为架构加运营手册。

### Wave 3：逐项事实复核

优先处理第 5 节列出的 14 个高风险命题，再覆盖所有事实、厂商数据和研究结果。任何研究结果必须同时记录任务、模型、基线、样本、指标、限制和出版状态。

### Wave 4：修复实现与出版工程

1. 修正附录和正文伪代码。
2. 建立可复现的 PDF 构建环境。
3. 明确生成文件策略并加入漂移检查。
4. 增加链接、a11y、依赖和版本一致性门禁。

## 10. 复审验收门

满足以下条件后才能标记为“正式定稿候选”：

- 所有事实命题原子化，类型不再由 URL 存在性推断。
- 100% factual/vendor/research claims 绑定具体 evidence span。
- 核心架构和定量命题至少两类独立来源；无法做到时显式标记单来源限制。
- 100% 来源元数据验证；动态产品文档具备版本或可重建快照。
- Agent/Harness/Runtime/Environment/Feedback 的包含关系在正文、术语表和架构图一致。
- 第 12、18、20—29 章不再是提纲式短章，并形成论点—证据—设计—案例—验收闭环。
- 三个贯穿案例覆盖成功、失败、审批、恢复、验证、提交和学习。
- 所有伪代码通过状态、类型、幂等、崩溃恢复和资源清理审查。
- 网站无内部 404；网页、PDF 和执行摘要标记相同 commit/content hash。
- 全新环境可按仓库说明重建 Markdown、HTML、PDF 和 VitePress 站点。
- CI 包含生成物漂移、base-aware 链接、可访问性、依赖和出版一致性检查。

## 11. 已通过的部分

- 第 5—11 章已形成较强的生产级 Harness 原理骨架。
- 四层进化分类本身清楚，治理方向与最新研究的主要风险意识一致。
- 产品章节普遍带时间截面提醒，没有直接声称 DSH 已实现可信自主进化。
- 站点 38 个 HTML 页面均可构建，章节导航、搜索、移动菜单、深色模式和语义主体可用。
- 62 个正文唯一外部 URL 的自动检查没有确认除解析误报外的实际 404；OpenAI/Microsoft 返回的 403 属于自动访问限制，不能判为断链。
- 研究仓库结构清晰，正文、证据、出版和网站职责已经分离。

## 12. 结论

这部书已经有值得保留的中心思想和工程模型，但现有“最终质量审计”结论过于乐观。最准确的状态应是：**公开测试稿，结构主干完成，事实账本和后半部内容仍需大修。**

下一轮不应先做表面润色，而应依次完成“本体冻结 → atomic evidence ledger → 后半部扩写 → 高风险事实复核 → 出版流水线门禁”。完成后再进行一次独立事实审查、技术同行评审和读者试读。

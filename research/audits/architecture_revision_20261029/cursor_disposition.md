# Cursor 架构重写处置说明

访问与核验日期：2026-10-29。章节基线：仓库 commit `11be2fecb5212aca11a1a76b40bd328568f0b8b2` 下的第十五章；这不是 Cursor 产品源码 commit。

## 交付与范围

只修改 `manuscript/chapters/15_cursor_ide_native_context_and_cloud_agents.md`，保持第一标题与编号不变。正文为八个共同小节，约 4,390 个汉字，采用文本架构图；没有新可执行示例。未改共享来源登记、结构、其他章节或发布产物，未提交、推送或部署。浏览器只使用 ego-browser、TaskSpace 153、p4，未创建或结束 TaskSpace。

采用 deep-research 的证据先落盘、区分文档事实与作者归纳、逐来源复核方法；按共享写作合同交付书稿而非独立咨询报告。未追加其他 agent。没有执行上游代码。Ego Lite 提示有新版本，本轮未升级，指定会话保持可用。

## 来源与捕获映射

`cursor_sources.jsonl` 是机器可读清单：`source_url` 是去掉 Markdown 后缀的正文引用 URL，`retrieval_url` 是实际抓取入口，`cache` 是仓库相对捕获路径，`sha256_retrieved_text` 是捕获内容的 SHA-256，另含 HTTP 状态、版本与访问日期。缓存均位于被 Git 忽略的 `publishing/work/architecture_20261029/cursor/`；文件序列化可能补一个末尾换行，哈希核验已考虑该差异。

共记录 25 个入口，其中 22 个成功、3 个旧路径 404。正文的 19 个不同来源 URL（忽略锚点）均同时匹配来源清单与 `cursor_evidence.jsonl`；未匹配 URL：**无**。证据账本含 38 条记录，每条包含用户指定的全部字段；同来源累计英文短引文均少于 25 词。正文采用紧邻链接，长文原文仅存忽略缓存，不作为跟踪文件重发布。

官方文档没有产品源码 commit 或不可变文档版本；本轮固定的是所取文本内容哈希，不能把它称为上游不可变发布版本。历史资料单独保留文章日期：动态上下文 2026-01-06，代码索引 2026-01-27，Harness 工程 2026-04-30，自管机器 2026-09-02，数据使用页标记更新于 2026-09-03，Memories 为 Cursor 1.0／2025-06-04 发布记录。

成功抓取的来源如下（实际入口及完整哈希见清单）：

- [Rules](https://cursor.com/docs/rules)
- [Cursor Agent](https://cursor.com/docs/agent/overview)
- [Run Modes](https://cursor.com/docs/agent/security/run-modes)
- [Model Context Protocol (MCP)](https://cursor.com/docs/mcp)
- [Cloud Agents](https://cursor.com/docs/cloud-agent)
- [Subagents](https://cursor.com/docs/subagents)
- [@ mentions and context](https://cursor.com/help/customization/context)
- [Cloud Agent security overview](https://cursor.com/docs/cloud-agent/security)
- [Self-Hosted Machines](https://cursor.com/docs/cloud-agent/self-hosted)
- [Projects](https://cursor.com/docs/agent/projects)
- [Dynamic context discovery](https://cursor.com/blog/dynamic-context-discovery)
- [Continually improving our agent harness](https://cursor.com/blog/continually-improving-agent-harness)
- [Tool Calling](https://cursor.com/learn/tool-calling)
- [Security](https://cursor.com/security)
- [Run cloud agents on machines you manage](https://cursor.com/blog/self-hosted-machines)
- [Hooks](https://cursor.com/docs/hooks)
- [Secrets & Network](https://cursor.com/docs/cloud-agent/security-network)
- [OIDC tokens](https://cursor.com/docs/cloud-agent/identity)
- [Data Use & Privacy Overview](https://cursor.com/data-use)
- [Securely indexing large codebases](https://cursor.com/blog/secure-codebase-indexing)
- [Agents](https://cursor.com/learn/agents)
- [Cursor 1.0 release notes](https://cursor.com/changelog/1-0)

旧路径尝试失败如下，不据此推导产品能力不存在：

- https://cursor.com/docs/context/codebase-indexing.md — HTTP 404
- https://cursor.com/docs/context/memories.md — HTTP 404
- https://cursor.com/docs/context/summarization.md — HTTP 404

## 旧稿处置与证据缺口

- 保留动态上下文、按模型定制工具、自管 worker 不迁移云端循环，以及 hooks 运行面／失败处理的已验证边界，改为架构说明中的具体机制。
- 厂商动态上下文 A/B 报告：在实际调用 MCP 的运行中，总 Agent token 下降 46.9%，并随已安装 MCP 数量有很大差异。该数字保留在证据 cursor-015；未复核随机化单位、同任务配对、统计窗口或实际完成质量，不作为普遍收益承诺。
- 原稿的 Projects beta 结论限定于 2026-09-10 发布、2026-09-19 抓取的历史截面。原来源登记在 `research/audits/review_20260919/sources.jsonl`，source_id `b28194f531afc390`，当时内容哈希 `a642780bee0ce8a79b734553bca8646e826eecb862839a77736b4b5fc5a66eea`。本轮改引现行 Projects 文档，未把旧 beta 身份推广为当前状态。
- Memories 的现行可用范围尚未核实；正文只叙述 1.0 发布记录。当前 Rules、摘要／历史文件、Project 共享文件分别解释，不虚构统一记忆引擎。
- 索引选择器、摘要压缩器、云端调度器与内部类未开放审计；图中的服务是职责归纳。没有获得逐调用事务重放、恰好一次执行或父任务取消后代副作用的保证。
- 普通 subagent 默认共享工作副本，独立上下文不等于独立 VM 或身份；云端子任务与自管 worker 分别依据公开契约解释。未实测权限、OIDC、MCP 登录态、hook 覆盖和恢复行为。
- 官方材料属于同一厂商来源群，不能视为多个独立效果验证。Keep Rate 与 token 效率保留其测量含义，不充当正确性或企业适配度证明。

## 已完成验证

本地只读校验通过：八个小节、原首标题、4,000–6,000 汉字目标、JSONL 字段与日期、38 条短引文原文匹配、全部捕获哈希匹配、正文 URL 的双账本覆盖、无 Mermaid／占位符／字面转义反引号，`git diff --check` 无错误。

通过 p4 再次请求正文引用的 19 个官方 HTML 页面，全部 HTTP 200，并核对锚点。两个页面未暴露所引用的锚点，已退回经过验证的页面 URL；其余保留锚点均匹配。没有运行会改写共享发布文件的全书构建，整书编号与发布集成由父任务处理；上述验证是资料与章节结构核验，不是 Cursor 端到端产品实验。

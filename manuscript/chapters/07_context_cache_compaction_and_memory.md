# 第七章 上下文、缓存、压缩与记忆

> 本章状态：正文初稿 v0.1。

模型在一次推理中只能依据当前上下文行动。对 Harness 而言，“记住一切”并不是目标；目标是在正确时刻，把可信、相关、足够且成本可接受的信息放到模型可见位置，同时保留原始事实以供重新发现。

上下文系统最常见的设计错误，是把对话历史、任务状态、知识检索、用户偏好、长期经验和可执行技能都塞进一个名为 memory 的容器。它们的信任等级、生命周期和更新权限完全不同。

## 1. 五种必须分开的信息

```text
Working Context   当前模型请求实际看见的内容
Conversation Log  用户、模型、工具交互的原始历史
Canonical State   任务、约束、执行与副作用的权威状态
Long-term Memory  跨会话复用的事实、偏好和经验
Skills/Artifacts  可执行程序、流程、模板和文档资产
```

Working Context 是临时编译产物，可以被压缩和重排；Conversation Log 用于审计、恢复和重新发现；Canonical State 不应依赖模型摘要保持正确；Long-term Memory 必须有来源与失效策略；Skills 则需要版本、权限和供应链治理。

如果把这五类混在一起，压缩可能删除任务约束，模型写入的猜测可能变成“长期事实”，删除聊天记录可能意外删除审计状态，而一条未经审查的 memory 甚至可能在未来会话中持续注入恶意指令。

## 2. Context Assembly 是一次编译

每次模型调用前，Harness 应从多个来源编译上下文：

```text
Context = compile(
  system_contract,
  policy_view,
  task_state,
  recent_events,
  retrieved_knowledge,
  active_skills,
  tool_catalog,
  environment_snapshot,
  token_budget
)
```

“编译”意味着过程可重复、可观测、可测试。每个片段应记录来源、版本、token 数、选择理由和可见性。出现错误时，工程师能够回答模型究竟看见了哪一版规则、哪些文件、哪些记忆，而不是只保存最终 prompt 文本。

Context compiler 还应处理冲突优先级。组织策略、项目规则、用户本轮要求、旧记忆发生冲突时，不能依赖它们在 prompt 中的偶然位置决定结果。平台应先在确定性层识别冲突，再向模型呈现明确、最小的有效约束。

## 3. 长窗口不是无限注意力

“Lost in the Middle”研究发现，长上下文模型对信息位置敏感，相关内容位于中部时性能可能显著下降。[Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/)

这不意味着所有现代模型都以相同程度失败，但它推翻了“只要窗口放得下，就等于模型能同等利用”的假设。长上下文还带来成本、延迟、缓存失效和互相矛盾信息增加。

上下文设计因此需要四种预算：

- 容量预算：窗口最多容纳多少；
- 注意力预算：模型能否稳定利用；
- 经济预算：输入与 cache read 成本；
- 变化预算：哪些片段变动会破坏前缀缓存。

相关性不是唯一排序信号。任务契约和安全约束即使语义上不接近当前动作，也必须保留；最近错误可能比历史上更相似的成功案例更重要；已经失效的记忆即使高度相似也应排除。

## 4. 静态上下文与动态发现

静态上下文每次调用都加载，适合短小、稳定、高频使用的信息，例如当前目录、关键任务契约和少量项目规则。动态上下文由模型通过文件、搜索或工具按需获取，适合大型、低频或快速变化的信息。

Cursor 公开描述了从大量静态注入转向动态发现的路径：长工具输出写入文件，摘要后保留历史文件引用，MCP 工具描述按需读取，终端输出同步到文件系统供 grep。[Dynamic Context Discovery](https://cursor.com/blog/dynamic-context-discovery)

文件在这里不是万能答案，而是简单、可寻址、可分页、可搜索的外部存储抽象。它让 payload 不必永久占据 prompt，也让模型能重新读取原始证据。

一个实用策略是：

```text
Always-on: 任务契约、关键策略、当前状态摘要
Index:     文件地图、技能目录、工具目录、记忆索引
On-demand: 原始文件、日志、历史、完整工具 schema
Pinned:    本轮验证所需证据与未解决错误
```

## 5. Prompt Cache 是架构约束

缓存命中通常要求请求拥有相同前缀。Codex 公开说明，工具顺序变化、模型变化、沙箱或工作目录变化都可能导致 cache miss，因此尽量保持静态内容在前，并把中途配置变化追加成新消息，而不是修改旧前缀。[Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

这意味着 context assembly 不仅优化语义，也优化布局稳定性：

```text
[stable system + stable tools + stable project rules]
[session history with append-only changes]
[latest dynamic observations]
[current user request]
```

工具目录来自动态 MCP 时，必须稳定排序并谨慎处理 `tools/list_changed`。否则一次无关的工具发现变化可能让长会话失去缓存收益。

缓存不能影响正确性。Harness 不应为了 cache hit 隐瞒已变化的权限或环境；正确做法是保留旧前缀并追加明确的状态更新，同时在确定性策略层立即生效。

## 6. Compaction 是有损编译，不是删除旧消息

当上下文逼近阈值，Harness 可将旧历史压缩为结构化摘要。Claude Code 会发出 compaction boundary；Codex 使用服务端 compact 结果替换较长输入。Claude Code 还会在压缩后重新注入系统 prompt、根级项目规则和 auto memory，而路径规则需要在再次读取相关文件后恢复。[Claude Context Window](https://code.claude.com/docs/en/context-window)

压缩摘要至少应包含：

```text
Goal and acceptance criteria
Confirmed constraints and approvals
Observed facts with source pointers
Workspace/environment changes
Decisions and rationale
Failed attempts and why
Open questions and blockers
Active plan and next action
Pointers to raw history/artifacts
```

压缩前后应运行 continuity checks：目标是否保持、权限是否保持、未完成项是否保持、关键 artifact 是否仍可定位。对于高风险任务，可把 compaction 当成 checkpoint，生成 hash 和差异报告。

反复压缩摘要会累积失真。建议始终从原始事件和 canonical state 生成新摘要，而不是只压缩上一次摘要；若成本不允许，至少保留可回源引用并定期重建。

## 7. MemGPT 与分层记忆

MemGPT 借鉴操作系统分层存储，让模型在有限主上下文与外部存储之间移动信息，并使用中断管理控制流。[MemGPT](https://arxiv.org/abs/2310.08560)

这个类比很有启发，但要谨慎：模型并不是可靠的操作系统内核。让模型完全决定什么写入、保留和淘汰，可能放大偏差。企业实现通常需要策略与模型协作：

- 模型提出候选记忆及理由；
- 确定性层校验来源、作用域和敏感等级；
- 高风险或共享记忆进入人工审批；
- 检索时同时考虑相关性、时效、可信度和权限；
- 使用反馈更新 memory utility，而不是只按访问频率保留。

## 8. 记忆类型与写入权限

| 记忆类型 | 示例 | 推荐写入者 | 典型失效条件 |
|---|---|---|---|
| 用户偏好 | 输出格式、常用语言 | 用户确认/模型建议 | 用户修改 |
| 项目事实 | 构建命令、架构约束 | 人或验证工具 | 仓库版本变化 |
| 情景经验 | 某错误的修复轨迹 | Agent 候选 + evaluator | 环境/版本变化 |
| 程序知识 | 调试 SOP、发布流程 | 评审后发布 | 流程版本更新 |
| 任务状态 | 当前步骤、阻塞 | Runtime | 任务结束 |
| 安全策略 | 禁止目标、审批规则 | 管理控制面 | 策略发布 |

安全策略不应作为普通 memory 由模型改写；任务状态也不应通过语义检索恢复。不同类型必须进入不同 store 和权限域。

Claude Code 明确说明 CLAUDE.md 与 auto memory 都只是上下文，不是强制配置。[Claude Memory](https://code.claude.com/docs/en/memory) 这一区分很重要：即使组织规则写进项目文件，真正的访问限制仍应由策略、IAM 和沙箱执行。

## 9. Memory Poisoning 与程序漂移

长期记忆会跨任务影响行为，因此攻击者只需让 Agent 写入一条恶意或错误经验，就可能在未来重复触发。风险包括：

- 把外部文档中的指令写成项目规则；
- 把一次偶然成功升级为普遍流程；
- 记住过期凭证位置或敏感数据；
- 通过共享 memory 影响其他租户或角色；
- 多次自动总结后产生程序漂移。

防护需要 provenance、scope、TTL、review state、author identity、supporting evidence 和 rollback。共享范围越大，晋级门槛越高。

```text
episode note → candidate lesson → evaluated skill → reviewed org standard
```

不能从一次轨迹直接跳到组织级规则。

## 10. 检索不是只有向量相似度

推荐使用多阶段检索：

1. 按租户、项目、身份、时间和类型做硬过滤；
2. 用关键词、图关系和向量召回候选；
3. 按相关性、可信度、时效、成本和风险重排；
4. 去重并识别冲突；
5. 以带来源标签的片段进入上下文；
6. 记录是否被使用以及结果反馈。

检索结果应被标记为“外部证据”而非系统指令。来自网页或文档的 prompt injection 不能因为被向量库召回就获得更高指令优先级。

## 11. Skills 不是 Memory 的别名

Skill 通常包含可执行或程序化知识：说明、脚本、模板、工具依赖和资产。它比一条自然语言记忆具有更大能力，也有更高供应链风险。

Skill 应具备：

- manifest 与版本；
- 触发条件与能力声明；
- 所需工具、网络和文件权限；
- 安装来源、签名或审核记录；
- 测试与兼容矩阵；
- 执行时的最小权限；
- 退役和回滚策略。

技能正文可以按需加载，避免所有技能永久占据上下文。Claude Code 与 Cursor 都采用短描述常驻、完整内容按需发现的方向。

## 12. Context Quality 的评价

上下文系统不能只测 token 节省。至少需要这些指标：

| 指标 | 含义 |
|---|---|
| Recall of required evidence | 必需信息是否被选中 |
| Precision/noise | 注入内容中无关比例 |
| Constraint retention | 压缩后约束是否保持 |
| Provenance coverage | 事实是否可回源 |
| Cache hit rate | 稳定前缀复用程度 |
| Context latency/cost | 装配和推理代价 |
| Memory usefulness | 召回后是否提升任务结果 |
| Poisoning rate | 不可信内容晋级比例 |

还应做 counterfactual eval：移除某段上下文，结果是否变化；交换位置，模型是否受位置偏差；注入冲突信息，Harness 是否识别；压缩前后执行同一后续任务，行为是否保持。

## 13. 推荐的上下文架构

```text
Raw Event Log ───────────────┐
Canonical Task State ────────┤
Project Knowledge / Rules ───┤
Memory Stores ───────────────┼→ Context Compiler → Model View
Skill & Tool Catalog ────────┤        │
Environment Index ───────────┤        ├→ token/cost manifest
Policy View ─────────────────┘        └→ provenance manifest

Large payloads → Artifact Store ← pointers in model view
```

Context compiler 是读模型，不是权威写路径。模型输出的“我已经完成 X”不能直接修改 canonical state；它必须经工具或 verifier 产生事实事件。

## 14. 最小验收清单

- 能解释每段上下文为何被选中；
- 原始历史与模型摘要分离；
- canonical state 不依赖摘要；
- 不同 memory 类型有独立作用域和写入权限；
- 大 payload 可外置并按需读取；
- compaction 前后有连续性测试；
- 动态工具和技能目录稳定排序并可按需发现；
- memory 有 provenance、TTL、撤销和晋级流程；
- 外部内容不能提升为系统指令；
- context 策略在不同模型上单独评估。

本章的核心结论是：上下文窗口是模型的工作集，不是系统数据库；Memory 是经过治理的跨时复用机制，不是聊天历史的别名。下一章将进入工具层，讨论 Action schema、错误协议、MCP、CLI、Code Mode 与能力发现如何共同构成 Agent 的“可行动世界”。

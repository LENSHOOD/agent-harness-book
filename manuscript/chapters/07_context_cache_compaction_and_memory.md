# 第七章 上下文、缓存、压缩与记忆

模型每轮推理只拿到当前上下文来行动。对 Harness 来说，目标不是“记住一切”。更关键的是，在正确时刻把可信、相关、成本可接受的信息放进模型可见范围，同时把原始事实留好，方便后续复用和核验。

上下文系统常见的问题是把对话历史、任务状态、知识检索、用户偏好、长期经验和可执行技能都塞进一个“memory”里。五类内容的信任等级、生命周期、更新权限完全不同。

## 1. 五种必须分开的信息

```text
Working Context   当前模型请求实际看见的内容
Conversation Log  用户、模型、工具交互的原始历史
Canonical State   任务、约束、执行与副作用的权威状态
Long-term Memory  跨会话复用的事实、偏好和经验
Skills/Artifacts  可执行程序、流程、模板和文档资产
```

Working Context 是临时编译产物，可以压缩和重排。
Conversation Log 用于审计、恢复和重放。
Canonical State 不能依赖模型摘要保持正确。
Long-term Memory 要有来源和失效规则。
Skills 要有版本、权限治理和供应链管理。

如果五类混在一起，压缩可能删掉任务约束。模型写入的猜测可能被误当长期事实。删聊天记录可能顺手删掉审计状态。未经审查的 memory 甚至可能在未来会话里反复注入恶意指令。

## 2. Context Assembly 是一次编译

每次模型调用前，Harness 都要把上下文从多源编译成可用输入：

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

“编译”意味着过程可重复、可观测、可测试。每段上下文都要记录来源、版本、token 数、选择理由和可见性。出现问题时，工程师才知道模型到底看见了哪版规则、哪些文件、哪些记忆，而不是只留下一段最终 prompt。

Context compiler 还要处理冲突优先级。组织策略、项目规则、用户本轮要求和旧 memory 如果冲突，不能指望它们在 prompt 中的顺序决定结果。确定性层应先判断冲突，再把明确且最小的约束给模型。

## 3. 长窗口不是无限注意力

“Lost in the Middle” 研究显示，长上下文模型对信息位置敏感。相关内容位于中间时，模型的表现可能显著下降。[Lost in the Middle](https://aclanthology.org/2024.tacl-1.9/)

这不代表所有现代模型都会同样失效，但它否定了“只要能放下就能等同理解”的假设。长上下文还带来成本上升、延迟增加、缓存失效和矛盾信息增多。

因此上下文要用四类预算管理：

- 容量预算：窗口最多能放多少；
- 注意力预算：模型能否稳定利用；
- 经济预算：输入与 cache read 成本；
- 变化预算：哪些片段变化会破坏前缀缓存。

相关性不是唯一排序依据。任务目标和安全约束即便语义上看似不接近当前动作，也必须保留。最近错误有时比历史成功案例更重要。已失效记忆再相似也要排除。

## 4. 静态上下文与动态发现

静态上下文每次调用都加载，适合短小稳定、重复高的信息，例如当前目录、关键任务契约、少量项目规则。
动态上下文按需加载，适合大体量、变动快或低频的信息，比如文件、搜索结果、工具查询。

Cursor 描述了从“批量静态注入”向“动态发现”的路径：把长工具输出写入文件，保留文件引用，MCP 描述按需读取，终端输出同步文件系统供 grep。[Dynamic Context Discovery](https://cursor.com/blog/dynamic-context-discovery)

文件在本章里不是万能解法，而是一个清晰、可寻址、可分页、可检索的外部存储。这样可以避免 payload 永久占满 prompt，同时支持模型按需重读原始证据。

常用策略是：

```text
Always-on: 任务契约、关键策略、当前状态摘要
Index:     文件地图、技能目录、工具目录、记忆索引
On-demand: 原始文件、日志、历史、完整工具 schema
Pinned:    本轮验证所需证据与未解决错误
```

## 5. Prompt Cache 是架构约束

缓存命中通常要有相同前缀。Codex 公开说明，工具顺序变化、模型变化、沙箱变化或工作目录变化都可能使 cache miss；因此应尽量把静态内容放前面，并把中途配置变化作为新消息追加，不要修改旧前缀。[Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

所以 context assembly 既要兼顾语义，也要兼顾布局稳定。

```text
[stable system + stable tools + stable project rules]
[session history with append-only changes]
[latest dynamic observations]
[current user request]
```

工具目录来自动态 MCP 时要稳定排序，并谨慎处理 `tools/list_changed`。一次不相关工具发现变化，就可能打掉整段长会话缓存收益。

缓存必须不影响正确性。为提高命中率而隐瞒变更权限或环境是不允许的。正确做法是保留旧前缀并新增状态更新，同时在确定性策略层立刻生效。

## 6. Compaction 是有损编译，不是删除旧消息

上下文接近阈值时，Harness 可把旧历史压缩成结构化摘要。Claude Code 会发 compaction boundary；Codex 的服务端 compact 用更短输入替代旧 input。Claude Code 之后会重新注入系统 prompt、根级项目规则和 auto memory，但路径细节仍需再次读取相关文件恢复。[Claude Context Window](https://code.claude.com/docs/en/context-window)

压缩摘要至少包含：

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

压缩前要跑 continuity checks：目标是否保持、权限是否保持、未完成项是否保持、关键 artifact 是否仍可定位。高风险任务可把 compaction 作为 checkpoint，生成 hash 和差异报告。

反复压缩会积累失真。应尽量从原始事件和 canonical state 重建新摘要，不要只基于上一次摘要叠加。若成本限制，至少要保留可回源引用并定期重建。

## 7. MemGPT 与分层记忆

MemGPT 借鉴操作系统分层存储思路，让模型在有限主上下文和外部存储之间移动，并用中断机制控制流转。[MemGPT](https://arxiv.org/abs/2310.08560)

这个类比有价值，但不能把模型当内核。让模型自己完全决定写入、保留、淘汰，会放大偏差。企业实现通常应让策略层与模型协作：

- 模型提议候选记忆和理由；
- 确定性层校验来源、作用域和敏感等级；
- 高风险或共享记忆进人工审批；
- 检索时同时看相关性、时效、可信度和权限；
- 以反馈更新 memory utility，而不是只按访问频率。

## 8. 记忆类型与写入权限

| 记忆类型 | 示例 | 推荐写入者 | 典型失效条件 |
|---|---|---|---|
| 用户偏好 | 输出格式、常用语言 | 用户确认/模型建议 | 用户修改 |
| 项目事实 | 构建命令、架构约束 | 人或验证工具 | 仓库版本变化 |
| 情景经验 | 某错误的修复轨迹 | Agent 候选 + evaluator | 环境/版本变化 |
| 程序知识 | 调试 SOP、发布流程 | 评审后发布 | 流程版本更新 |
| 任务状态 | 当前步骤、阻塞 | Runtime | 任务结束 |
| 安全策略 | 禁止目标、审批规则 | 管理控制面 | 策略发布 |

安全策略不能当普通 memory 让模型改写；任务状态也不能靠语义检索恢复。
不同类型必须进不同 store 和权限域。

Claude Code 明确说明 CLAUDE.md 与 auto memory 只是上下文，不是强制配置。[Claude Memory](https://code.claude.com/docs/en/memory) 这点很重要：项目文件里写规则后，真正的访问控制仍应由策略、IAM 和沙箱执行。

## 9. Memory Poisoning 与程序漂移

长期记忆会持续影响未来行为。攻击者只要让 Agent 写入一次恶意或错误经验，就可能反复触发偏差。常见风险有：

- 把外部文档命令误写成项目规则；
- 将一次偶然修复错误地上升为通用流程；
- 记下过期凭证位置或敏感数据；
- 通过共享 memory 影响其他租户或角色；
- 多次自动总结后形成程序漂移。

需要的防护是 provenance、scope、TTL、review state、author identity、supporting evidence 和 rollback。共享范围越大，晋级门槛应越高。

```text
episode note → candidate lesson → evaluated skill → reviewed org standard
```

不能从一次轨迹直接升级为组织级规则。

## 10. 检索不是只有向量相似度

推荐采用多阶段检索：

1. 按租户、项目、身份、时间和类型先做硬过滤；
2. 用关键词、图关系和向量召回候选；
3. 按相关性、可信度、时效、成本和风险重排；
4. 去重并识别冲突；
5. 以带来源标签片段入上下文；
6. 记录是否被使用及结果反馈。

检索结果要被标记为“外部证据”，不是系统指令。网页或文档里的 prompt injection 不该因为检索命中而直接升指令优先级。

## 11. Skills 不是 Memory 的别名

Skill 通常包含可执行或程序化知识：说明、脚本、模板、工具依赖和资产。它比自然语言 memory 具备更高能力，但供应链风险也更高。

Skill 至少应有：

- manifest 与版本；
- 触发条件与能力声明；
- 所需工具、网络和文件权限；
- 安装来源、签名或审核记录；
- 测试与兼容矩阵；
- 执行时最小权限；
- 退役和回滚策略。

技能正文可按需加载，避免永久占据全部上下文。Claude Code 与 Cursor 都采用短描述常驻、完整内容按需发现。

## 12. Context Quality 的评价

上下文质量不能只看 token 省钱。至少看这些指标：

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

还要做 counterfactual eval：移除某段上下文后结果是否变；交换位置后是否受位置偏差；注入冲突信息后 Harness 是否识别；压缩前后复跑同一任务是否行为保持。

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

Context compiler 是读模型，而不是权威写路径。模型输出的“我已经完成 X”不能直接改 canonical state；必须经过工具或 verifier 产出事实事件。

## 14. 最小验收清单

- 能解释每段上下文入选原因；
- 原始历史和模型摘要分离；
- canonical state 不依赖摘要；
- 不同 memory 类型有独立作用域和写入权限；
- 大 payload 可外置并按需读取；
- compaction 前后有连续性测试；
- 动态工具和技能目录稳定排序并可按需发现；
- memory 有 provenance、TTL、撤销和晋级流程；
- 外部内容不能直接提升为系统指令；
- context 策略在不同模型上单独评估。

本章结论是：上下文窗口是模型工作集，不是系统数据库。Memory 是经过治理后的跨时复用机制，不是聊天历史的同义词。下一章将讨论工具层：Action schema、错误协议、MCP、CLI、Code Mode 与能力发现如何共同定义 Agent 的“可行动世界”。

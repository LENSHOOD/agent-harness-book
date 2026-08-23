# 第十五章 Cursor：IDE 原生上下文与云 Agent

> 产品快照截至 2026-08-22；厂商使用数据只作为其用户群观察，不外推全行业。

Cursor 的代表性在于把 Harness 嵌入开发者交互面：编辑器状态、选择区、诊断、终端和代码索引成为上下文来源；同一产品又向云端长任务和隔离 VM 延伸。它展示了 Harness 不只是后台 runtime，也是人与 Agent 共享注意力和控制权的界面。

## 1. 动态上下文发现

Cursor 公开描述其从大量静态上下文与强约束，转向由模型主动发现所需信息。长工具结果可以写入文件，模型按需读取；工具 schema 可以动态发现；终端状态也可通过统一文件式接口访问。[Dynamic Context Discovery](https://cursor.com/blog/dynamic-context-discovery)

这与“最小充分工作集”原则一致：不要预判并注入全部内容，而要提供廉价导航、搜索与回读。但动态发现增加工具轮次，若索引、文件命名或错误反馈差，模型会在探索中浪费预算。

## 2. Harness 与模型共同适配

Cursor 明确讨论了不同模型需要不同工具描述、约束和交互设计，并通过线上与离线评测持续改进 Harness。[Continually Improving Our Agent Harness](https://cursor.com/blog/continually-improving-agent-harness) 这反驳“一套系统提示适配所有模型”的设想。

企业 provider abstraction 因而不应只统一 API。Canonical action contract 可以稳定，但 model-facing tool view、上下文布局和错误呈现需要按模型 profile 编译。可移植性发生在控制面，性能优化发生在适配层。

## 3. 云 Agent 的环境工程

Cursor 对 cloud agents 的总结强调预构建环境、VM checkpoint/restore/fork 和专用 computer-use 能力。[Cloud Agent Lessons](https://cursor.com/blog/cloud-agent-lessons) 长任务的速度很大程度取决于环境启动、依赖缓存和可恢复性，而不只是生成速度。

Checkpoint 还支持从同一状态派生多个候选，但必须区分环境快照与任务真相：外部服务仍会变化，凭证与租约可能过期，恢复后需重新验证策略和 freshness。

## 4. IDE 人机协作的优势与风险

IDE 内 Agent 能显示 diff、引用诊断并让开发者随时接管，适合高频、局部和互动式任务。风险是隐式上下文过多：打开文件、剪贴板、终端和索引可能包含敏感数据；频繁自动接纳可能降低审查质量；本地与云端的权限边界也容易被界面统一感掩盖。

产品指标如自动接纳率、工具调用深度和上下文规模能展示趋势，但不能直接代表正确率。接受可能来自信任、疲劳或低风险任务。企业评估仍需以合并后缺陷、返工和交付周期为准。

## 5. 架构启示

Cursor 提供三条可迁移经验：交互面本身是 Harness 的一部分；模型 profile 应控制上下文和工具适配；云 Agent 的竞争力来自环境基础设施。企业平台若只提供一个聊天框和通用 API，即使模型相同，也难复制 IDE 原生 Agent 的能力。

# 第八章 工具、ACI、MCP 与 Code Mode

> 本章状态：正文初稿 v0.1。

工具决定 Agent 可以对世界提出哪些动作。一个模型即使理解了任务，如果只有模糊、冗余或危险的工具，也会表现得像能力不足；反过来，一个设计良好的 ACI 可以把复杂环境转化成模型容易观察、操作和修复的界面。

企业平台不应从“接入多少工具”衡量成熟度，而应从动作语义是否稳定、权限是否清晰、结果是否可验证、失败是否可恢复来衡量。

## 1. Tool Definition 只是起点

典型工具包含：

```text
name
description
input_schema
output_schema
side_effect_class
permission_requirements
timeout/retry policy
version
```

多数模型 API 只要求前三项，但企业 Harness 需要后面的运行时元数据。否则策略层无法知道工具是否只读，重试器不知道是否幂等，观测系统不知道怎样脱敏，兼容层不知道 schema 是否已变化。

建议把工具拆为两层：

```text
Model-facing Tool View     为具体模型优化的名字、说明与 schema
Canonical Action Contract 平台内部稳定的动作类型、语义和治理元数据
```

模型表面可以因模型族而变化，内部 contract 保持稳定。这样既避免最低公分母接口，也保留统一审计、权限和评估。

## 2. 好工具的十个条件

1. 名称能表达动作和对象；
2. 描述说明何时使用，也说明何时不要使用；
3. 输入 schema 小而明确，避免多种互斥模式挤在一个对象中；
4. 输出同时有模型友好摘要和结构化数据；
5. 错误区分可修复输入错误、策略拒绝和系统故障；
6. 副作用范围可预估；
7. 支持取消、超时和幂等；
8. 结果包含来源、时间和目标标识；
9. 版本变化有兼容策略；
10. 可在真实模型与任务上端到端评估。

工具说明本身属于上下文。长描述会占用 token，短而含糊又导致误用。最佳说明不是完整 API 文档，而是支持正确选择和第一次成功调用的最小契约；复杂细节应按需发现。

## 3. 错误协议是 ACI 的一部分

模型能否自我修复，很大程度取决于错误是否结构化。推荐返回：

```json
{
  "status": "failed",
  "category": "invalid_argument",
  "retryable": false,
  "message": "line_end must be >= line_start",
  "field_errors": [{"path": "line_end", "code": "range"}],
  "suggested_fix": "Use line_end >= 42",
  "effect_committed": false
}
```

协议错误表示客户端/服务器无法通信；工具执行错误表示调用已被理解但业务执行失败。MCP 2025-11-25 变更也明确强调，输入校验错误应作为 Tool Execution Error 返回，以便模型自我修正，而不是作为协议错误。[MCP Changelog](https://modelcontextprotocol.io/specification/2025-11-25/changelog)

`effect_committed` 或等价状态非常关键。若未知，Harness 不应自动重试写动作。

## 4. Tool Result 不应只有字符串

纯文本对模型友好，但对程序、UI 和 evaluator 不友好；巨大 JSON 对程序友好，却可能污染上下文。建议结果分层：

```text
summary            短模型观察
structured_content 可验证字段
artifact_refs      大内容、文件、图像和日志引用
provenance         来源、目标、时间、版本
execution_meta     时延、attempt、request id、effect 状态
```

MCP 的 ToolResult 可以携带文本、图像、音频、资源链接、嵌入资源和可选 structuredContent，并用 `isError` 标记执行错误。[MCP Schema](https://modelcontextprotocol.io/specification/2025-11-25/schema)

模型上下文通常只需要 summary 和少量结构字段；审计与 evaluator 则通过 artifact ref 读取完整结果。

## 5. MCP 解决的是互操作，不是全部 Harness 问题

MCP 采用 host-client-server 架构：Host 管理模型集成、连接权限、用户授权和上下文聚合；每个 Client 与一个 Server 维持独立会话；Server 暴露 tools、resources、prompts 等能力。[MCP Architecture](https://modelcontextprotocol.io/specification/2025-06-18/architecture)

它的重要价值包括：

- 统一能力发现和 JSON-RPC 消息；
- 显式 capability negotiation；
- 本地 stdio 与远程 HTTP server；
- 工具、资源、提示和客户端 sampling/elicitation；
- 独立演化的客户端与服务器生态。

但 MCP 不替 Host 决定：是否批准调用、用哪个身份、是否允许访问某数据、结果如何进入上下文、工具是否幂等、任务是否完成。官方架构也把连接权限、安全策略和用户授权放在 Host。

因此企业平台应把 MCP 看成插件与连接协议，而不是安全边界本身。

## 6. MCP 的安全边界

远程 MCP 授权规范要求 OAuth 2.1、protected resource metadata、资源 audience 绑定，并禁止把收到的 token 直接透传给下游服务，以避免 token misuse 和 confused deputy。[MCP Authorization](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)

即便协议正确实现，平台仍需治理：

- 哪些 Server 可安装；
- Server 发布者与代码供应链是否可信；
- 每个租户和 Agent 可见哪些工具；
- 凭证由谁持有和刷新；
- 工具输出如何分类与脱敏；
- Server instructions 是否含 prompt injection；
- tool list 动态变化是否触发审批和 cache invalidation；
- 本地 stdio Server 是否能访问宿主机秘密。

“MCP Server 在本地运行”不代表安全。它可能继承用户环境变量和文件权限，供应链风险甚至高于受控远程服务。

## 7. Tool Discovery：工具也需要分页

数百个工具 schema 会消耗大量上下文并降低选择准确率。Claude Code 默认延迟加载 MCP 工具，只让名称或类别进入初始上下文，由 Tool Search 找到相关 schema；官方文档给出的经验是，较大工具集适合搜索，少量工具直接加载更快。[Claude Tool Search](https://code.claude.com/docs/en/agent-sdk/tool-search)

Tool discovery 可以类比数据库索引：

```text
Catalog summary → search(query, policy_scope) → candidate tools
→ load exact schemas → model call → invoke
```

检索必须先应用权限过滤，避免向模型泄露不可见工具名称。工具描述要适合搜索：包含业务对象、动作、约束和常用同义词。搜索结果还应考虑 model compatibility、健康状态、延迟和成本。

## 8. CLI：最通用但最难治理的工具总线

Shell 让 Agent 直接复用 git、编译器、数据库客户端和组织已有 CLI。它具有巨大组合性、文档生态和人类可复现性。Pi 的极简设计正是依赖 shell、文件和技能，而不是内置大量专用工具。

CLI 的代价是：参数空间开放、命令可能启动子进程、重定向和管道隐藏真实效果、静态策略难以理解 shell 语义。安全实现至少需要：

- 明确 shell 解析模型，避免对整段字符串做天真前缀匹配；
- 进程组、PTY、stdin、后台进程和超时管理；
- cwd 与可写根限制；
- 网络和可执行文件策略；
- 命令规范化与用户可读审批；
- stdout/stderr 外置、截断和秘密脱敏；
- 退出码与实际效果分离。

高风险业务动作不应只暴露成任意 shell。应提供窄工具，使策略能理解语义，例如 `create_payment_draft` 与 `commit_payment` 分离。

## 9. Native Tool Call 与 Code Mode

Native 模式每次由模型选择一个或多个函数调用，Harness 执行并把结果送回模型。Code Mode 则让模型生成一段程序，在程序内组合多个工具调用，只把提取后的结果返回外层对话。

DSH Code Mode 将工具渲染为 TypeScript/Python SDK，并只向模型暴露 `run_code` transport；程序内工具调用仍重新进入完整的 pre-execute、guard、execute、post-execute pipeline。官方文档特别说明，它是用 SDK 文本加一个 transport schema 替换各工具 schema，不承诺在所有情况下减少 token。[DSH Tools](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/core/tools/README.md)

Code Mode 的优势：

- 多步数据处理留在执行环境，减少模型往返；
- 中间大型结果不进入对话；
- 可表达循环、分支、并行和异常处理；
- 代码比多轮自然语言更容易复现。

风险：

- 一次 `run_code` 内可能发生多个真实副作用；
- 审批 UI 必须解释内部调用，而非只显示外层程序；
- 程序可能动态构造参数，静态预审不完整；
- sandbox、资源限制和秘密隔离要求更高；
- 中间失败与部分提交需要细粒度 ledger。

因此 Code Mode 必须让每个内部 tool call 重新经过策略和审计，不能把 `run_code` 的一次批准视为无限授权。

## 10. 并行工具的调度语义

模型输出多个调用不等于它们可以安全并行。工具定义应声明：

```text
read_set / write_set
side_effect_class
concurrency_group
idempotency_support
ordering_requirements
```

DSH Code Mode 指导独立只读调用可用 `Promise.all`，变更调用按顺序运行。企业调度器还可根据目标系统和租户限流。多个读取如果访问强一致快照可以并行；读后写必须绑定版本 witness，避免 stale observation。

## 11. 工具版本与动态变化

工具 schema、行为或权限变化会影响：模型选择、prompt cache、重放、历史会话恢复和评估可比性。每次 invocation 应记录 tool contract version 与 implementation digest。

兼容变化可以原地升级；破坏性变化应创建新 action version。恢复旧会话时，Harness 可以：

1. 加载兼容旧版本；
2. 运行显式迁移；
3. 重新规划尚未执行的动作；
4. 无法保证时暂停并请求人工。

不能把旧模型生成的参数直接送给含义已变化的新工具。

## 12. Tool Policy 与 Tool Execution 分离

推荐流水线：

```text
model proposal
  → schema validation
  → semantic normalization
  → policy evaluation
  → approval if needed
  → credential binding
  → sandbox/executor dispatch
  → result validation
  → redaction/transformation
  → event + model observation
```

模型不接触实际凭证。Policy 接收 canonical action 与身份/环境状态，返回 allow、deny、require approval 或 require additional constraint。Executor 只接受已授权、带时效和绑定范围的 capability。

## 13. 如何评价工具层

除了任务成功率，还应测：

- tool selection precision/recall；
- 首次参数有效率；
- 自修复成功率；
- 平均工具轮数与上下文成本；
- 错误分类准确率；
- 重复副作用率；
- 未授权调用拦截率与误报率；
- schema 变化后的兼容率；
- 大结果外置后的证据召回率；
- 不同模型对同一 canonical action 的适配差异。

评测应包含 adversarial tools：名字相似、描述冲突、返回 prompt injection、动态改变 tool list、部分成功和超时后提交。

## 14. 企业平台的工具分层

```text
L4 Business Actions  支付、工单、发布、客户数据
L3 Domain Tools      SQL、仓库、观测、文档、浏览器
L2 Generic Compute   shell、Python、文件、HTTP
L1 Protocol Adapters MCP、OpenAPI、CLI、SDK、RPC
L0 Execution Control policy、credential、sandbox、ledger
```

越靠近业务提交，接口越窄、权限越细、验证越强；越靠近通用计算，组合性越高、隔离越强。

## 15. 最小工具契约伪代码

```text
ToolContract {
  id, version, model_views[]
  input_schema, output_schema
  side_effect: NONE | REVERSIBLE | COMMITTING
  idempotency: NATURAL | KEYED | NONE
  required_capabilities[]
  data_classification
  timeout_policy, retry_policy
  concurrency_policy
  result_projection
  verifier
}
```

这个 contract 可以由 MCP、CLI wrapper 或内部 SDK 实现。协议可以多样，运行语义必须统一。

本章结论是：工具不是模型函数列表，而是从概率性意图到真实副作用的受治理动作协议。MCP 提供互操作，CLI 提供组合性，Code Mode 提供程序化编排；Harness 必须在它们之下统一身份、策略、执行、账本和验证。下一章将专门讨论这个信任边界：权限、审批、沙箱、凭证与供应链。

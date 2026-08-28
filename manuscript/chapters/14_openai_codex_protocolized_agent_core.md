# 第十四章 OpenAI Codex：协议化的 Agent Core

> 资料截面：2026-08-27。这里的 Codex 指开源 Codex harness 及其 CLI、SDK、App Server 接入面，不把模型名称与运行时名称混为一谈。

Codex 的关键设计选择，是把同一套核心循环从终端 UI 中抽出，并用稳定事件协议提供给 IDE、桌面和云端客户端。OpenAI 官方把 harness 的职责列为：线程生命周期与持久化、配置与认证、沙箱中的工具执行，以及 MCP/skills 等扩展；这些逻辑位于 Codex core。App Server 则是承载多个 core thread 的长生命周期进程和双向协议层。[App Server](https://openai.com/index/unlocking-the-codex-harness/)

## 1. 从 UI 内核到可嵌入服务

App Server 采用 JSON-RPC 风格的 request、response、notification，但官方特别说明它省略标准 JSON-RPC 2.0 header，并以 JSONL over stdio 分帧，所以更准确的名称是“JSON-RPC lite”，不能假定任意 JSON-RPC 客户端都可无缝兼容。[App Server](https://openai.com/index/unlocking-the-codex-harness/) 一个客户端请求可以产生多个通知；服务器也可以主动发起审批请求并暂停 turn。这种双向、流式、可暂停的协议，比把 Agent 包装成同步 `run(prompt) -> text` 更接近真实交互。

```text
client request: thread/start, turn/start, turn/cancel
server stream: item/start, item/update, item/completed, turn/completed
server request: approval or user input
```

协议化的价值不是“多了一层 RPC”，而是把 UI 迭代周期与 Agent core 分开。官方实践中，有的客户端打包并固定测试过的二进制；有的客户端保持稳定、连接较新的 App Server，并依赖向后兼容协议。[App Server](https://openai.com/index/unlocking-the-codex-harness/) 企业平台也应固定经过认证的 runtime 版本，而不是启动时自动拉取最新版。

## 2. 三种集成面不是同一抽象

| 接入面 | 适合 | 主要局限 |
|---|---|---|
| `codex exec` | 一次性 CI、脚本、清晰退出码 | 难承载丰富的中途交互 |
| Codex SDK | TypeScript 应用内控制本地 Agent | 语言与功能面相对受限 |
| App Server | IDE、桌面、平台级流式集成 | 客户端需实现协议、状态与兼容处理 |

如果平台需要并发 thread、恢复、审批和丰富进度，App Server 是更自然的边界；如果只是夜间批量修复任务，`exec` 更简单。过早统一为一个最小 `Agent.run()` 接口，会把 cancel、approval、fork、artifact 和增量 diff 都压成供应商私有字段，最终只能通过旁路补洞。

## 3. Loop、context 与执行边界

OpenAI 对 agent loop 的公开拆解强调：环境和权限变化作为新消息追加，长会话自动 compaction，并尽量保持可缓存前缀。[Agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) 这说明“上下文是事件投影”比“上下文就是数据库”更准确。平台需要保留 canonical task state 与原始事件，compacted context 只是下一次推理输入（见第七章）。

Codex 的本地执行由操作系统级 sandbox 和 approval policy 约束。公开的 ExecPolicy 允许按命令前缀规则决定 allow、prompt 或 forbidden。[ExecPolicy](https://github.com/openai/codex/blob/main/codex-rs/execpolicy/README.md) 规则匹配适合处理确定性命令边界，但无法理解所有脚本内部副作用。因此 sandbox、网络策略、工作区隔离和凭证代理仍不可省略（见第九章）。

## 4. 并行工作不是共享目录里多开几个进程

Codex 产品使用 Git worktree 隔离并行 Agent 的代码修改。[Codex app](https://openai.com/index/introducing-the-codex-app/) 其可迁移原则是“每个候选拥有独立可回收写集”，而不是必须使用 Git。数据库任务可以使用临时 schema，数据任务可以使用固定快照，基础设施任务可以使用独立 plan。合并之后还要在组合状态重跑验证；单分支通过不证明组合正确。

反例是两个 Agent 分别修改依赖与调用方，各自在独立 worktree 通过局部测试，合并后锁文件冲突或接口不兼容。若平台只收集“两个 Agent 都成功”的文本，就会把协调失败误判为模型失败。真正的完成点在合并后的 completion gate（见第十、十一章）。

## 5. 企业 adapter 的状态模型

平台不应直接把 Codex thread 当作 task。一个 task 可以重试、fork 或切换 runtime；一个 thread 也可能包含多个用户 turn。建议保存如下映射：

```json
{
  "task_id": "TASK-2048",
  "attempt_id": "A-03",
  "runtime": "codex-app-server",
  "runtime_version": "pinned-build",
  "thread_id": "vendor-thread-ref",
  "workspace_revision": "git:8f31...",
  "policy_profile": "code-medium-v4",
  "completion_contract": "cc:v7"
}
```

adapter 要处理协议版本协商、断线重连、重复通知、客户端取消和进程退出。收到 `turn/completed` 只表示该 turn 结束；平台还需收集 artifact、执行独立 verifier，再决定 task 是否完成。健康指标至少包括事件缺口率、审批往返时延、断线恢复成功率和 runtime 版本漂移率。

## 6. 设计判断

Codex 提供的核心启示是：Agent core 应能被多个产品表面复用，协议必须表达长生命周期和双向控制。它的边界也很明确：协议化不自动带来业务幂等、跨供应商语义统一或完成证明。自研平台应借鉴 thread/turn/item 的事件化思想，但在更外层拥有 task、policy、evidence 与 commit authority。

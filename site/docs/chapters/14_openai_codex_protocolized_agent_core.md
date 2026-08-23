# 第十四章 OpenAI Codex：协议化 Agent 核心与工程控制面

> 产品快照截至 2026-08-22。

Codex 展示的是“同一 Harness 核心，多种客户端与执行形态”。公开材料把 agent loop 描述为模型、工具和用户之间的控制器，并解释其如何处理流式事件、工具调用、上下文和循环终止。[Unrolling the Codex Agent Loop](https://openai.com/index/unrolling-the-codex-agent-loop/)

## 1. App Server 是关键边界

Codex App Server 通过双向 JSON-RPC 把核心能力暴露给 CLI、IDE、桌面和其他客户端，使 UI 不必重新实现 agent loop。[Codex App Server](https://openai.com/index/unlocking-the-codex-harness/) 这是一种重要的平台化：会话、审批、工具事件和状态成为协议对象，而不是终端输出解析。

企业自研 Harness 应借鉴“核心只实现一次，客户端通过版本化协议接入”，同时避免把内部模型 provider 细节泄漏到协议。事件要可扩展，未知事件可向前兼容，命令必须有幂等和恢复语义。

## 2. 工作树与并行

Codex 的桌面与云形态强调隔离任务、worktree 和并行 Agent。[Introducing the Codex App](https://openai.com/index/introducing-the-codex-app/) 代码并行的核心不是多开聊天，而是为每个执行者提供独立工作区，再在 Git 边界合并和验证。

Worktree 解决文件覆盖，不解决语义冲突。多个 patch 合并后仍须在干净环境执行系统级测试，并由单一 owner 决定提交。

## 3. 策略层

开源 Codex 包含 sandbox、approval 与 exec policy。ExecPolicy 使用 allow、prompt、forbidden 的命令前缀规则，并允许规则附测试样例。[Codex ExecPolicy](https://github.com/openai/codex/blob/main/codex-rs/execpolicy/README.md) 这说明持久批准应成为可测试的策略代码，而不是模糊的“始终允许”。

企业扩展还需加入身份、资源、数据分类和跨域流动；命令字符串规则只是其中一层。

## 4. Harness Engineering

OpenAI 将自身实践概括为 harness engineering：让仓库结构、测试、文档、日志和工具对 Agent 可读、可操作、可验证。[Harness Engineering](https://openai.com/index/harness-engineering/) 这改变了平台投资方向。提升 Agent 不只是在 prompt 上打补丁，也包括缩短环境反馈回路、提高错误可诊断性、把隐性规范变成可执行检查。

## 5. 取舍与借鉴

Codex 的优势是开源核心、协议化 App Server、工作区隔离和系统策略。风险包括客户端/服务器协议演化、云与本地能力差异、并行任务的成本与合并复杂度，以及模型与 Harness 同厂优化造成的可移植性幻觉。

企业最应借鉴的是控制面与执行面的协议化，而不是照搬工具名称。将 Codex 作为 runtime 时，外部平台继续拥有任务合同、租户身份、数据策略和最终证据；将来自 Codex 的事件映射为 canonical trace，未来即可替换为其他 runtime。

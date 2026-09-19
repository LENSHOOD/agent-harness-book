# 第十四章 OpenAI Codex：协议化的 Agent Core

> 资料截面：2026-09-19。开源 CLI/App Server 以 Rust 0.155.1（9 月 18 日发布）为固定源码点；本地 probe 使用的是 0.142.5。Agents API 是另一个托管接入面，不能用开源客户端源码证明其服务端实现。[0.155.1 发布记录](https://github.com/openai/codex/releases/tag/rust-v0.155.1)

Codex 把核心循环从终端 UI 中抽离，供多个客户端复用。官方将线程生命周期与持久化、配置与认证、沙箱工具执行、MCP/skills 等扩展归入 core；App Server 管理多个 core thread，并提供双向协议。[App Server](https://openai.com/index/unlocking-the-codex-harness/) 这里的“协议化核心”是作者归纳，不意味着每个字段永久稳定，也不意味着 Codex 模型、SDK、App Server 与托管服务是同一对象。

## 1. 从 UI 内核到可嵌入服务

App Server 使用 JSON-RPC 风格的请求、响应与通知。在本文讨论的 stdio 接入中，消息按 JSONL 分帧并省略 `jsonrpc` 字段，不能假定任意标准 JSON-RPC 客户端可以无缝兼容。[App Server](https://openai.com/index/unlocking-the-codex-harness/) 客户端请求可引出多个通知，服务端也可反向请求审批或输入。下面是精确方法名与方向的协议骨架，省略了响应与其他事件，**不是抓取到的运行轨迹**：

```text
client request: initialize
client notification: initialized   (after successful initialize response)
client request: thread/start, turn/start, turn/interrupt
server notification: item/started, item/agentMessage/delta,
                     item/completed, turn/completed
server request: approval or user input   (semantic category, not a method name)
```

`turn/interrupt` 是客户端请求，参数包含 `threadId` 与 `turnId`；`item/started` 是服务端通知，增量按类型区分，例如 `item/agentMessage/delta` 包含 `threadId`、`turnId`、`itemId` 和 `delta`。不存在本书旧稿中的通用 `item/update`。旧稿的 `turn/cancel` 与 `item/start` 也不在所核验的方法枚举内。8 月 27 日基线已使用正确名称，因此这是原稿纠错，不能记为 9 月 API 改名。[基线协议](https://github.com/openai/codex/blob/426fa8cdab4247e5623e9617d531f6917482b947/codex-rs/app-server-protocol/src/protocol/common.rs#L985)、[0.155.1 中断请求](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1056)、[0.155.1 item 通知](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1941)

## 2. 四种接入面与不同运营责任

| 接入面 | 已公开事实 | 作者的接入判断与待核验项 |
|---|---|---|
| `codex exec` | CLI 非交互执行入口 | 适合边界清楚的脚本任务；按版本确认输出与退出语义 |
| Codex SDK | 至少有 TypeScript、Python 接入；Python 0.154.0 于 9 月 10 日发布 | 逐语言确认功能与协议版本，不能假定两者完全对等 |
| App Server | 可自行部署的长生命周期双向协议服务 | 适合中途输入、审批和进度集成；客户端承担重连与兼容处理 |
| Agents API | 9 月 10 日进入 public beta，由 OpenAI 管理会话编排、压缩与恢复 | 采购托管 Harness；工具执行环境可托管或自管，服务限制另行检查 |

Python 0.154.0 的发布说明涉及 typed protocol、ExternalMessage、历史及单 turn 选项。这是已存在 SDK 的版本发布，本轮没有证明 Python SDK 的首次出现日期。[Python SDK 发布记录](https://github.com/openai/codex/releases/tag/python-v0.154.0) Agents API 的公测日期则有正式 changelog 支持，不能把它与本地 SDK 或通用 Agents SDK 混称。[API changelog](https://developers.openai.com/api/docs/changelog)

截至本次存档，Agents API 保留会话状态，只支持美国数据驻留，不支持 Zero Data Retention（ZDR）；选择自托管 sandbox 不会使它具备 ZDR 资格。自管工具执行解决执行位置的问题，并没有把托管编排、推理和会话存储全部迁回企业网络。[Agents API 概览](https://developers.openai.com/api/docs/guides/agents-api/overview)

## 3. 源码边界与九月运行时变化

开源源码可以核对本地 core、App Server 协议与执行策略；它不能证明托管 Agents API 的每个部署细节。官方循环说明描述了环境与权限变化追加进消息、长会话压缩及缓存前缀处理。[Agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) 对适配器而言，重点是升级或恢复后权限是否仍与当前策略一致。

本窗口有三项直接影响集成的变化：0.152.0 改善恢复与压缩中的权限保留；0.153.0 对外部 App Server 断线重连保留草稿和转录，并暂停处理不确定或排队的提交；0.154.0 支持活动会话刷新插件、skills/hooks，MCP OAuth 刷新也不会自动重放被拒调用。这些是具体版本行为，不是“可恢复”三个字可以覆盖的全部语义。[0.152.0](https://github.com/openai/codex/releases/tag/rust-v0.152.0)、[0.153.0](https://github.com/openai/codex/releases/tag/rust-v0.153.0)、[0.154.0](https://github.com/openai/codex/releases/tag/rust-v0.154.0)

## 4. 中断与迟到通知：适配器的失败边界

下面是作者据协议设计的待测故障场景，不是已经完成的产品实验：客户端收到某 item 的文本增量后发送 `turn/interrupt`，但等待响应时连接断开。此时应记录“中断请求已发送、结果未知”，不能立刻显示“所有工具已停”。重连时核对原 thread/turn 与终态，将迟到通知关联回原 item；若断线前已有写入，另外核对写入结果。

这要求适配器保留请求 ID、thread/turn/item 标识、原始通知与接收顺序。`item/completed`、`turn/completed` 的名称本身不是成功状态，应读取相应结果。也不能从协议层中断推导后代进程与外部副作用全部撤销。取消的通用状态规则见第六章；这里独有的问题是双向 RPC 与异步通知如何在重连后归并。

## 5. 企业 adapter 的状态模型

以下是**本书自定义平台映射**，不是 App Server 请求参数，也不能直接交给 CLI/SDK。占位版本需要替换为实际部署标识：

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

原生 thread/turn/item 可映射为平台尝试及事件引用；供应商通知未提供的业务验收结果不能由字段名推断。协议握手、能力协商、取消和进程退出都应按所部署版本测试；不支持的能力明确降级，不能静默模拟成功。

## 6. 本地核验到哪里，结论就到哪里

本轮研究在本机 0.142.5 成功生成默认及 experimental 两套 schema，离线方法集合、必要字段与固定源码对照 **58/58 符合预期**，其中包含证明旧方法名不在枚举中的反例检查。这个分母既不表示旧示例正确，也不表示完整 JSON Schema 验证或端到端测试通过。

三次自施受限启动都在 `initialize` 响应前以 exit 1 退出，错误为 `Operation not permitted`；具体受限路径和系统调用仍未知。未发送 `initialized`、`thread/start`、`turn/start` 或模型请求，也没有观察到错误方法名被线上拒绝的报文。**正常握手未验证，取消与模型流未端到端验证**；不能据此宣布 Codex 不可用。原始记录保存在本书研究材料的 `review_20260919/vendor_probe/codex/`。

作者的设计判断是：双向协议适合承接丰富客户端，托管 API 则把部分运维责任交给供应商。选择哪条接入面，取决于版本控制、数据流、恢复责任和实际任务测量；开源协议检查并不能替代这些验收。

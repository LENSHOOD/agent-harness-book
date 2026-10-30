# Pi 1.4.0 同行核查（只读、限量）

日期：2026-10-29。审查对象为 `manuscript/chapters/18_pi_mono_small_core_composable_session.md`，源代码基线是本地 `publishing/work/architecture_20261029/pi` 的 HEAD `4a080252f06caf63a525d7873c5d94d3c23887e0`（Agent 包 1.4.0）。检查了相关源码/文档、`examples/pi-core/pi-core.test.mjs`、依赖锁文件与已安装包元数据；没有运行测试、模型请求或上游代码，没有修改章节或测试。

结论：2 个可具体修正的表述问题，未发现 core / SDK / CLI 默认装配被混同，也未发现把九项低层替身测试写成完整产品端到端成功。以下行号和判断针对审查时快照。

## 1. [P2] 链式委派不是无条件传递前一步结果

位置：章节第 79 行，“链式模式把前一步结果传给后一步”。

固定实现只将后一步 `task` 中的 `{previous}` 占位符替换成前一步的最终 assistant 文本；没有占位符就不会注入。每一步启动独立子进程，且带 `--no-session`，不是自动接续前一步完整会话。当前一句话会让读者误以为只要选择 chain 模式就会自动拿到上一阶段输出，直接影响多步骤任务的数据流设计。

证据：[chain 的占位符替换](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/examples/extensions/subagent/index.ts#L548)（L554 替换，L594 提取最终文本）；[子进程参数](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/examples/extensions/subagent/index.ts#L298)。该示例 README 的 Tool Modes 表也明确写有 `{previous}`。

建议改成：“链式模式按顺序运行任务，并用后一步任务模板中的 `{previous}` 显式注入前一步最终文本；它不自动继承完整历史。”

## 2. [P3] JSONL 的首行会话头不属于 id/parentId 条目树

位置：章节第 49 行，“JSONL 中每项通过 `id` 和 `parentId` 组成树”。

首行 `SessionHeader` 是会话元数据，有会话 ID，但没有 `parentId`，也不是条目树中的一个节点；只有后续 `SessionEntryBase` 派生项遵循该链接结构。直接按原表述解析每一行，会误把会话 ID 当作条目 ID、给首行寻找不存在的父链接。

证据：[SessionHeader 与 SessionEntryBase 类型](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/src/core/session-manager.ts#L43)；[格式文档的例外](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/session-format.md#L51)。注意以源码为准：文档第 66 行括号中的“no id/parentId”写得过宽，其紧邻 JSON 示例仍含会话级 `id`。

建议改成：“除首行会话头外，JSONL 会话条目通过 `id` 和 `parentId` 组成树。”

## 已核对的正确边界与测试证据限度

- CLI 内建 MCP 支持、SDK 需加入相应扩展工厂并执行 `bindExtensions()`：符合 [SDK 文档 L116](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/sdk.md#L116)。内建扩展“加载”不同于工具“默认激活”；`codemode` 和 `tool_search` 默认 inactive，可由配置或 MCP 自动激活。章节当前用“加载”而未声称默认激活，未判为缺陷。
- 默认 `read / bash / edit / write`、MCP 的 direct/deferred/codemode/hidden 暴露区别、project trust 不构成执行权限边界、子代理属于可安装扩展示例，均与固定文档及所需源码相符。
- `agent_end` 与 `agent_settled` 的区分正确；截断输出不执行工具、`transformContext → convertToLlm`、混合 terminate 批次继续反馈，也与实际 loop 分支相符。
- 测试文件有 9 个 `test()`，直接导入已安装的 `runAgentLoop`，不是在测试中重写一个模拟 loop；锁文件与已安装包均为 `@earendil-works/pi-agent-core@1.4.0`，`pi-ai` 也为 1.4.0。模型传输被 `streamFn` 替换，工具为内存函数，未调用收费模型或实际 SDK/MCP/subagent。接受主任务刚完成的“9 通过”结果，本次没有复跑。
- 九项名称与断言基本相符，但后续编辑不要扩张其分母：L114–119 的“全部 terminate”用例实际只有一个工具调用，并未验证两个以上工具全部终止；L122–126 测试的是 provider 返回 `stopReason: aborted`，没有向真实正在执行的工具发送 AbortSignal；L60–69 的历史保留只证明该过滤函数没有删除传入数组，不能推广到所有自定义 transform。当前正文没有明确作出这些更强保证，故这里记录证据边界，不另计缺陷。
- 未覆盖模型输出质量、真实流式增量、上层 `agent_settled`、持久化/恢复、压缩质量、实际 MCP、子进程取消和 OS 隔离；正文已明确大部分边界。

审查时文件 SHA-256：

| 文件 | SHA-256 |
|---|---|
| pi 章节 | `c2028f7a9a684fa00e2d5dbe13f382d4080dfa1e15f39d701bb5764615816f67` |
| `examples/pi-core/pi-core.test.mjs` | `fb6d4a40fe5e003cf76b138e31750c9d9c6c0b07d9d1601c02333e4790123463` |
| `examples/pi-core/package-lock.json` | `99918a4c19f75a7e2b53b1348fd39a619af6a477f4a0a5305a07049ffd8fc45b` |

另已生成 [codex_sources.jsonl](codex_sources.jsonl)：逐一对应 Codex 正文 37 个不同 URL，其中 33 个固定源码文件有现存 capture 路径和 SHA-256；4 个官网页面此前实际通过 ego-browser 阅读，仅留短引文证据，没有保存整页文件，因此明确标记 `no_full_page_capture_saved` 并给出证据 JSONL 行号，不冒充完整网页快照。本次不重新抓取网页，不更改或清理 TaskSpace 153。

# 产品章节交叉核查（只读、限量）

日期：2026-10-29。阅读第十三章 Claude、第十四章 Codex、第十五章 Cursor、第十六章 dsh、第十八章 Pi、比较章（文件 slug 仍为 `18_product_comparison_and_architecture_spectrum.md`）及执行摘要。OpenHands 在检查时仍为“历史结构保留在历史版本中”等六节旧结构，按任务要求跳过，不评价其未完成稿。未联网扩展研究，未运行上游程序，未修改正文、来源注册表或编号；只新增本报告。

结论：1 项尚需处理的跨章节表述问题。以下行号针对核查时内容；父任务正在整合，适用性应以所引原句是否仍存在为准。

## 1. [P2] 执行摘要把需要平台落实的权限约束写成了通用默认

位置：[执行摘要第 54 行](../../../manuscript/executive_brief.md#四安全控制从具体动作开始)，原句为“委派默认只使用父任务已经获得的权限”。该句没有“应当”或“平台必须保证”的限定，会被读成六个案例共同具备的产品默认，和 Pi 章第 5、6 节所说明的“同 OS 用户权限、子进程不自动缩小权限、宿主承担隔离”不一致。

具体反例来自已固定的 Pi v1.4.0：subagent 示例只在子角色配置了 `agent.tools` 时添加 `--tools`；它没有把父会话工具集合传给子进程，更没有在此路径计算两者交集。因此，父会话只暴露读工具，而子角色不配置 `tools` 时，子进程仍可能使用 CLI 默认编码工具；父任务的工具约束并不会因为发生了委派而自动成为子任务边界。该例说明的是工具范围，不应夸大成操作系统提权漏洞。[固定示例的参数构造](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/examples/extensions/subagent/index.ts#L298)、[固定安全说明](https://github.com/earendil-works/pi/blob/4a080252f06caf63a525d7873c5d94d3c23887e0/packages/coding-agent/docs/security.md#L3)

建议替换为：“企业应将子任务可用权限显式约束在父任务已获授权的范围内，并按产品核验工具过滤、会话权限与执行身份是否真正继承；需要领域专属身份时，由有权主体独立签发。”保留本段的安全设计目标，同时不把它冒充现成产品的统一默认。

## 已检查但不计为新增问题

- **dsh spawn/join**：初次读到比较章第 29 行的“spawn 与 join”，复查时父任务已改为“spawn、fork 及可继续子任务”。固定提交 `ddefc45fbc7f8e46dd73185e68295696d1297887` 的 subsystem 与两个工具 README 未将 `join` 作为这里的通用产品机制；新措辞符合 provider、一次性 result 与 Session/Activation 的区分，不再报告待修项。
- **dsh 权限继承的层次**：不要由“新 flat scope 不复制父工具注册／authority”进一步写成“什么权限都不继承”。同一提交的 `captureDelegatedPolicyOverrides()` 会捕获父会话显式 sandbox override、Auto／Full access preset，并在组合了审批能力时把子审批策略钉为 `never`；不复制的是完整父注册作用域、部署默认值或一次性授权。现有“不能假定自动继承父限制”未作出绝对否认，因此不另外定为错误，但整合时应保留这个区别。[实现](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/subagent/subagent/src/child-agent.ts#L222)、[设计文档](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/subsystems/subagent.md#in-process-backends-permission-depth-and-seed)
- **接入面、沙箱与上下文**：未发现 Claude Code/Agent SDK 被等同于 Managed Agents，Codex 本地 core 被等同于 Agents API，Cursor worker 被等同于云端规划者，或 Pi CLI 的 MCP 装配被无条件移植到 SDK。各章均区分模型上下文、持久记录、执行环境及最终验收。
- **版本截面**：dsh、Codex、Pi 的比较引用分别保持 `0.1.6-alpha.2`、Rust `0.155.1`、`v1.4.0`；Claude 的 Python SDK `0.2.174` 与文档中标出的 binary 功能最低版本分开说明。执行摘要的 Agents API 商业政策段在复查时已明确限定为 2026-09-19 历史截面。未把“未重验”升级为当前事实错误。
- **已有 Pi 同行意见**：`pi_peer_review.md` 已记录链式 `{previous}` 与 JSONL 首行 header 两项，本报告不重复计数，也不在正文直接修复。

本次没有验证产品端到端取消、故障恢复、沙箱强度或模型行为。未开启新浏览器任务，未结束共享 TaskSpace。

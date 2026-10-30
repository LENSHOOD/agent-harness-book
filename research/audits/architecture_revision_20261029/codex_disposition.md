# Codex 架构改写处置记录

访问日期：2026-10-29。独占正文范围：`manuscript/chapters/14_openai_codex_protocolized_agent_core.md`。原 H1、章节号和 slug 保持不变，由父任务统一编号；没有修改共享目录、注册表、结构文件或其他章节，没有 commit、push、部署，也没有启动更多代理。

## 取材与固定基线

- 官网通过 ego-browser CLI，复用 TaskSpace 153 的 p3；没有新建、结束 TaskSpace 或操作其他 worker 页面。已读取 ego-browser 技能并完整运行 `ego-browser skill`；使用官方 OpenAI 文档技能的“先搜索、再打开”顺序，之后按本次任务授权分析 GitHub 源码。
- 公开文档：Codex as a platform、Codex App Server、Codex SDK、Agent approvals & security。完整 URL、短引文及定位全部在 [codex_evidence.jsonl](codex_evidence.jsonl)。
- `https://developers.openai.com/codex/security` 本次访问实际是漏洞扫描产品页，不能当作执行沙箱文档；沿其官方链接改读 `https://learn.chatgpt.com/docs/agent-approvals-security`。前者没有作为正文技术依据。
- 未把官网当前新增能力套到旧源码。源码仍为 `rust-v0.155.1`；`git ls-remote` 确认 annotated tag object 为 `4e21628f9ec9ee656650cd2b62ef92225725b5ac`，peeled commit 为 `be2951ea34f0d295ed0becf97079f92fa5f6950e`；clone HEAD 与 Cargo 工作区版本均符合此基线。本轮没有查询并宣称“最新版本”。
- 仓库缓存仅在被忽略的 `publishing/work/architecture_20261029/codex/source/`。仅获取与阅读源码；没有编译、安装依赖、运行上游脚本或启动模型任务。

固定仓库中实际采用的来源如下；每个文件的完整不可变 URL、具体定位和结论对应 JSONL 的独立记录：

| 范围 | 已读取并引用的文件（相对仓库） |
|---|---|
| 基线与接入 | `codex-rs/Cargo.toml`；`sdk/typescript/src/exec.ts`；`codex-rs/app-server-protocol/src/protocol/common.rs` |
| 核心职责 | `core/src/thread_manager.rs`、`codex_thread.rs`、`session/session.rs`、`session/mod.rs`（以下 core 路径均在 codex-rs 下） |
| 循环与恢复 | `core/src/session/turn.rs`、`responses_retry.rs`、`tasks/mod.rs`、`session/rollout_reconstruction.rs` |
| 上下文与记忆 | `core/src/agents_md.rs`、`context_manager/history.rs`、`compact.rs`；`codex-rs/memories/README.md` |
| 工具与扩展 | `core/src/tools/router.rs`、`registry.rs`、`handlers/mcp.rs`、`handlers/dynamic.rs`；`codex-rs/codex-mcp/src/rmcp_client.rs`；`codex-rs/ext/skills/src/lib.rs` |
| 权限与凭证 | `core/src/tools/orchestrator.rs`；`codex-rs/sandboxing/src/manager.rs`；`codex-rs/login/src/auth/storage.rs` |
| 委派 | `core/src/agent/control.rs`、`agent/control/legacy.rs`、`agent/status.rs`；`core/src/tools/handlers/multi_agents/spawn.rs`、`multi_agents_common.rs`、`multi_agents/wait.rs`、`multi_agents_v2/spawn.rs` |
| 可观测性 | `core/src/tools/tool_dispatch_trace.rs`；`core/src/otel_init.rs` |

## 内容处置

将原章以协议纠错和集成风险为中心的叙述，改为八个共同问题：总体职责、loop/恢复、上下文/会话、工具/MCP/扩展、审批/沙箱/凭证、子代理、验证/可观测性、贯穿任务。图为作者归纳的文本图，不是原厂部署图；订单导出案例是作者设计的走查，未声称实跑。

保留并加强以下边界：固定源码与实时文档分开；Codex SDK 两种语言的执行路线不混同；Agents SDK、托管 Agents API 不冒充开源 core；V1 委派工具名称不当作唯一长期契约；中断、关闭代理树和业务副作用回滚分开；压缩模型窗口不改变用户授权；MCP/宿主工具的远程权限仍由执行端落实。

原章历史审计叙述的处置如下，细节继续由既有原始记录承载，不用本次访问日期为历史结论续期：

- 协议纠错保留正确方法名。旧 `turn/cancel`、`item/start`、`item/update` 错误并非九月改名；8/27 基线 `426fa8cdab4247e5623e9617d531f6917482b947` 与 0.155.1 已交叉核过。原始结论及源码链接见 [九月审计 §4.2](../review_20260919/report_vendor_deltas.md)。
- 0.152.0 恢复/压缩权限保留、0.153.0 外部 App Server 重连草稿和不确定提交、0.154.0 活动会话扩展刷新及 MCP OAuth 不自动重放拒绝调用，保留为九月发布历史，见同一审计 §4.3。本章改讲固定版本机制，不逐版本复述更新日志。
- Python SDK 0.154.0 于 9/10 发布是已有 SDK 的版本发布，不证明首次出现日期。旧章对 Agents API 9/10 public beta、当时美国数据驻留和不支持 ZDR 的描述保留在九月原始研究中；本轮不重查托管服务政策，也不将这些旧限制写成 10/29 现状。
- 旧自定义 adapter JSON 只是平台映射建议，删除正文样例；业务 task 与供应商 thread/turn/item 的关联原则保留在验收和走查中。

## 验证与仍未解决的证据缺口

本轮已完成的机械核验：

- 8 个共同小节，原 H1 完整保留；4,110 个汉字，文本图，无 Mermaid。
- JSONL 共 38 条，八个必需字段齐全，访问日期全部为 2026-10-29。正文 37 个不同 HTTP(S) 引用 URL 全覆盖，零缺失，父任务可直接合并。
- 33 条固定源码引文全部在所固定 checkout 中匹配，所有短引文均不超过 25 个空白分词。其余为四篇官网短引文与一条历史本地 probe 证据。
- 重新取得的固定版 `common.rs` 与九月留存副本 SHA-256 同为 `da72b22e76648ce7549c2ab7677bf828bf4fbe2f44ae73ac8dc1c53651370b47`；不是用新代码替换旧基线。
- 已读取 `local/protocol_test_results.json`，明确为 58/58 离线方法判别与必要字段检查；核对了初始化结果、真实发送记录/说明与 stderr。没有重新运行这些历史测试。
- 对独占文件运行 `git diff --check`。全书构建、编号与在线呈现交由父任务统一完成。

尚缺：正常 App Server 握手、收费模型 turn、真实流式中断/重连、实际沙箱及子代理生命周期的端到端验证。历史三次本机 0.142.5 自施受限启动均在 `initialize` 响应前 exit 1，报 `Operation not permitted`；具体路径与系统调用未知。`initialized`、`thread/start`、`turn/start` 和模型请求均未发送，不能宣称捕获了错误方法名的线上拒绝，不能据此判定产品不可用，也不能把 58 项离线结果当成完整 JSON Schema 或端到端通过。原始目录：[历史 probe](../review_20260919/vendor_probe/codex/)。

Ego Lite 本轮提示可更新（0.6.0.12），没有升级；按共享任务约定保留 TaskSpace 153，由父任务管理结束。

## 父任务补充：官网页面保存

2026-10-29，父任务通过同一 ego-browser TaskSpace 的 p1 补存了四篇官网页面，路径和 SHA-256 已写回 `codex_sources.jsonl`，由本轮证据合并脚本登记。同行核查记录中“四篇官网页面没有整页留存”的描述是该核查时的快照，目前已经补齐。此补存不改变上文运行验证的缺口，也没有把实时文档推广为固定源码能力。

# 官方仓库增量与 Codex 协议核验

核验日：2026-09-19。范围：2026-08-28 起至本次抓取时刻；下文日期统一为 **UTC**。GitHub release 的日期取 `published_at`，源码变更日期取 commit 的 `committer.date`；PR 合并日期另行标明。提交日期、合并日期、发布日不混用。当天尚未发生的更新不在本报告范围内。

仅用 `gh api --method GET` 获取 deepseek-ai/deepseek-harness、openai/codex、OpenHands/OpenHands、OpenHands/software-agent-sdk 的公开数据。没有浏览器操作、依赖安装、第三方安装脚本、收费模型调用或源稿修改。原始返回、命令、UTC 抓取时间和 SHA-256 保存在 `vendor_probe`；规划文件也仅在该目录，未触碰主代理文件。

## 1. 可直接交给主代理的结论

**综合报告引用口径（已收口，不扩展仓库）：**

1. **Codex 原示例明确不匹配真实协议方法枚举。** 在本机 0.142.5 默认和 experimental 两套 schema 中，`turn/cancel`、`item/start`、`item/update` 的成员检查结果全部为 `false`。分别应写成请求 `turn/interrupt`、通知 `item/started`、具体类型的通知（例如 `item/agentMessage/delta`）。8/27 基线和稳定 0.155.1 源码交叉验证一致，因此这是旧稿错误，不是近期改名。58/58 是正例及反例检查均符合预期，**不表示原示例通过**。
2. **没有观察到这些错误名称的线上 JSON-RPC 拒绝报文；正常握手仍未验证。** 前两次自施受限启动及一次增加短路径 mktemp 目录、允许本地 IPC 的重试，都在 initialize 响应前 exit 1，报 `Operation not permitted`。第三次已用本机 `--help` 确认 `--stdio` 合法；日志有文件锁相关回溯，但具体受限路径和拒绝系统调用仍为 **unknown**。`initialized` 与三个错误方法都未发送。不能将此写成“Codex 无法运行”“真实调用得到 -32601”或“取消/流式 turn 端到端实跑失败”；可确认的是生成 schema 与固定源码中的方法名错误。
3. **dsh 隔离变化只发生在 PTC 执行路径，动态 Cordis VM 路径没有这项变化。** 指定旧点 `cd5ef814…` 的 `run_code` 使用 Node worker thread，明确不提供宿主安全隔离；指定新点 `ddefc45…` 使用受平台 sandbox 策略约束的新 Node 子进程。变更 commit `75ed8da3…` 时间为 **2026-09-12 07:03:01 UTC**。另一条动态 Host 路径的 `node:vm sandbox.ts` 两点逐字节相同，源码明确不是 containment，不能写“升级为 VM 安全沙箱”。

日期缺口显式标注：各文档页的独立首发/更新公告日期 **unknown**；上述正确协议名称的首次引入日期 **unknown**（仅证明在核验基线已存在）；动态 Cordis VM 的首次引入日期 **unknown**（仅证明两点已有且关键源码未变）；PTC 子进程变更首次进入哪个发布 tag **unknown**（已定位 9/12 commit，且确认存在于 9/17 发布的 `0.1.6-alpha.2`，未逐个检查所有中间 tag）。已确认的 commit/release 日期仍按下表和正文记录，不以 unknown 覆盖已有证据。

| 优先级 | 定位 | 核实结果 | 性质与建议 |
|---|---|---|---|
| P1 | 第 14 章第 12–13 行 | `turn/cancel`、`item/start`、`item/update` 不在实机 0.142.5 的两套生成 schema，也不在 8/27 基线和最新稳定版源码中。实际接口为 `turn/interrupt`、`item/started` 及按类型区分的 `item/*/delta`。 | 原有示例错误，**不是本窗口 API 改名**。应替换示例并标出请求/通知方向。 |
| P1 | 第 16 章第 29 行 | 动态 Cordis Host 的所谓 VM 是 `node:vm` realm，源码明说不是安全隔离边界；它与 `run_code` 的执行后端是两条不同路径。 | 原来就存在的事实边界，应拆开说明；不能译成或暗示硬件虚拟机级沙箱。 |
| P1 | 第 16 章插件生命周期与配置 | 9/9 撤回事务式 Cordis reload；9/14–16 增加 Plugin Manager、YAML 管理 HMR、Creator 持久插件流程。 | 本窗口明确变更。插件卸载撤销注册不等于整个 reload、包安装或业务副作用可回滚。 |
| P1 | 第 16 章 `run_code` | 9/12 从 Node worker thread 后端改为通过平台 sandbox 执行的独立 Node 进程，并统一 PTC 命名。 | 本窗口明确架构变更，且当前仍是 developer preview / alpha。 |
| P1 | 第 17 章整体版本定位 | 原章 EventStream → Runtime → ActionExecutor 的结构能在旧版 0.62.0 源码定位；OpenHands 1.0.0 在 2025/12 已宣布使用新 SDK。8/27 基线已是 Canvas 与 SDK/Agent Server 分仓。 | 原章缺版本边界；SDK 分离不是 9 月新发布。保留历史结构作为旧版实例，补新架构和本窗口增量。 |

## 2. 版本与不可变定位

本轮 P0 仅用于已证实的线上事故或产品不可用；上述文稿事实/示例错误均按 P1 处理。

“非预发布”仅表示 GitHub `prerelease=false`，不额外推断所有功能已经稳定。Codex 的实验功能和 dsh 的 alpha 标签分别保留。

| 产品/接入面 | 8/27 发布基线 | 抓取时最新对应版本 | 公开发布日期（UTC） | 固定源码 |
|---|---|---|---|---|
| dsh | `0.1.2-alpha.1`，用户给定旧 commit | `0.1.6-alpha.2`，**prerelease=true** | 2026-09-17 13:30:16 | [ddefc45fbc7f8e46dd73185e68295696d1297887](https://github.com/deepseek-ai/deepseek-harness/commit/ddefc45fbc7f8e46dd73185e68295696d1297887)；[release](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.1.6-alpha.2) |
| Codex Rust CLI | `0.150.1`，8/27 | `0.155.1`，非预发布 | 2026-09-18 20:03:04 | [be2951ea34f0d295ed0becf97079f92fa5f6950e](https://github.com/openai/codex/commit/be2951ea34f0d295ed0becf97079f92fa5f6950e)；[release](https://github.com/openai/codex/releases/tag/rust-v0.155.1) |
| Codex 本机二进制 | 不等于书稿截面最新版 | **0.142.5**，本次实跑对象 | 2026-07-01 01:15:44；本机 `--version` 验证版本 | [26de83050b20f7e0ee211b9739e52ae00ce8032a](https://github.com/openai/codex/commit/26de83050b20f7e0ee211b9739e52ae00ce8032a)；[release](https://github.com/openai/codex/releases/tag/rust-v0.142.5) |
| OpenHands / Agent Canvas | `1.16.0`，8/27 | `1.20.0`，非预发布 | 2026-09-17 07:15:18 | [9737f713616a1e452f822c2967f0e2c8bf2dc308](https://github.com/OpenHands/OpenHands/commit/9737f713616a1e452f822c2967f0e2c8bf2dc308)；[release](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0) |
| Software Agent SDK | `1.44.0`，8/27 | `1.49.2`，非预发布 | 2026-09-17 20:46:52 | [d128a786ee2ee570eb23ff5862ec148b43cfad0b](https://github.com/OpenHands/software-agent-sdk/commit/d128a786ee2ee570eb23ff5862ec148b43cfad0b)；[release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2) |

Codex 抓取时还有 `0.156.0-alpha.7`（9/19 04:08:15，`prerelease=true`），不将它写成稳定版。dsh `/releases/latest` 返回 404；已抓到的 release 列表均为 prerelease，README 仍明确写 developer preview 和可能破坏兼容。不能据此把 `0.1.6-alpha.2` 去掉后缀称为稳定 0.1.6。

四个默认分支抓取点分别为 dsh `ddefc45…`、Codex `78245b47af2a7aafcabe025828ceecca69db4df1`、OpenHands `a07364828c8f202e7745c6bce3dcef3915ae7ac1`、SDK `004c674a96d7eeeba70fcefc0e6dfc6a87958d3d`。默认分支不能代替 release；Codex 与 SDK 的关键实现另外取了稳定 tag 对应的源码。

## 3. DeepSeek Harness：新旧实现比对

用户指定旧点 [cd5ef8148158c3a752a658978873241fdf8e2bbc](https://github.com/deepseek-ai/deepseek-harness/commit/cd5ef8148158c3a752a658978873241fdf8e2bbc) 的提交时间为 8/27 16:57:43，对应 `dsh-v0.1.2-alpha.1`；新点对应 `dsh-v0.1.6-alpha.2`。本地已保存两点的 README、architecture、tool-catalog、app-boot、Cordis Loader、动态 runner 等源码和逐文件 diff。

### 3.1 原来已经存在，不能当新发布

- “一切皆插件”、服务/类型事件/可撤销注册，以及 bundle → profile patch → home patch → CLI `--patch` 顺序，两点都有。
- 按 id 匹配的 patch **替换整份 config，不是深合并**，旧文档已经明确。新 Plugin Manager 的 enable 操作会将 bundle 追加到有序列表末尾，因而可能改变优先级；home/调用级 patch 仍高于 profile。
- `run_code`、桥接子工具完整守卫管线、每次子调用的开始/完成事件，旧 tool-catalog 已有。原章提出逐个子调用追踪的方向合理，但不要把实现已经提供的部分全写成尚待自行实现。

固定来源：[旧 architecture](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/architecture.md)、[新 architecture](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md)、[旧 tool catalog](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/tool-catalog.md)。

### 3.2 两条代码执行路径必须分开

| 路径 | 旧点 | 新点 | 结论 |
|---|---|---|---|
| 动态 Cordis 包 Host half | `node:vm`、共享宿主服务 façade；声明 bash-equivalent 信任 | `sandbox.ts` **逐字节未变**，仍使用 `createContext/runInContext` | 这是原来已有的当前能力；没有“9 月新加 VM 安全沙箱”的证据。 |
| 模型 `run_code` / PTC | 每次新建 Node worker thread，`ctx.codeRuntime`；文档明确没有安全隔离 | 每次新建 Node 子进程，`ctx.ptcRuntime`，通过 `fs/subprocess/sandbox/sandboxPolicy`；受限模式缺 backend 时失败 | 9/12 明确变更，不再把旧 worker 与动态 `node:vm` 混写。 |

动态 VM 源码头注释明确：host-realm helper functions 仍是 escape route。`vmTimeoutMs` 约束同步求值部分，不能推导任意异步任务受到完整 CPU/网络/文件隔离。[固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/cordis-host-runner/src/sandbox.ts#L1)。

PTC 的不可变变更证据为 [75ed8da3e0c9103b3b2174b2981b7129e1fba21d](https://github.com/deepseek-ai/deepseek-harness/commit/75ed8da3e0c9103b3b2174b2981b7129e1fba21d)，commit 时间 9/12 07:03:01；随后 [7c9bb5914cedec80e46197a8c894037fcfd12faf](https://github.com/deepseek-ai/deepseek-harness/commit/7c9bb5914cedec80e46197a8c894037fcfd12faf) 在 07:03:04 统一 PTC 包、服务和事件命名。新 catalog 使用 `tool/ptc-dispatch-start` / `tool/ptc-dispatch`，旧版是 `tool/code-dispatch-start` / `tool/code-dispatch`。

新执行预算默认 `timeoutMs=120000`、上限 `600000`，包括等待子工具和审批的经过时间；这是 elapsed deadline，**不是 CPU 计量器**。直接 Node API 仍可使用，实际权限取决于平台 sandbox 与所选 mode；不能声称只允许桥接 capability 或所有平台都提供同等强度隔离。[旧 worker 文档](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/packages/code-runtime/code-runtime-worker-thread/README.md)、[新 PTC Node 文档](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md)。

清理边界也不同：旧 worker 的 `terminate()` 不保证终止程序派生的 OS 进程，旧文档明确需部署层清理；新实现由宿主管理进程范围，在取消、超时及正常结束时清理该范围。但新文档仍明确 V8 heap cap 不等于整个进程树的内存限额，也没有进程树 CPU meter。本轮只做固定源码/文档对照，没有执行逃逸或后代进程清理实验，不把这些源码契约写成实测安全保证。

### 3.3 生命周期、热重载与失败语义

| 确认日期（commit UTC） | 明确变化 | 对原章的影响 |
|---|---|---|
| 9/9 08:20:00 | `AgentLoop` 等待串行 `agent/created` 初始化，完成后才处理排队工作；失败走创建清理。 | 不能只说插件“装上就运行”，启动与清理顺序是契约。[commit](https://github.com/deepseek-ai/deepseek-harness/commit/9b7a8ccc9fabc2e87386acf7f8b0741baf978022) |
| 9/9 09:32:09 | 撤回事务式 Cordis reload。 | 普通 Loader group 保留已成功兄弟项；初始启动另有 required-entry 策略；后续 HMR 不做整批事务回滚。[commit](https://github.com/deepseek-ai/deepseek-harness/commit/e07f41d5fd8ca172287fda0f923b4d1f69c592f3) |
| 9/14 15:09:05 | 增加当前 profile 的 Plugin Manager 服务与 Web controls。 | profile 级持久状态会影响该 profile 下的所有会话；与进程内动态定义不同。[commit](https://github.com/deepseek-ai/deepseek-harness/commit/98b92b683c39fc60771daa774492105c2d3e8076) |
| 9/15 05:01:06 | HMR 生命周期由 YAML 配置管理。 | base 开启 config-only HMR，headless/SDK/ACP 禁用，sdk-minimal 省略；profile patch 可覆盖，不能写死为不可改变的产品属性。[commit](https://github.com/deepseek-ai/deepseek-harness/commit/abd765a6001ff9d9c9772b8b407e0b7f18fe25ab) |
| 9/16 07:39:16 | Creator 改用 Plugin Manager 安装持久插件。 | 新 `tool-cordis` 只保留 inspect 类工具；旧 catalog 的 `cordis_define/run/stop/undefine` 不再是模型工具。程序化/浏览器动态生命周期仍在，不能写成整个 runner 已删除。[commit](https://github.com/deepseek-ai/deepseek-harness/commit/ed32f57f88ef6bba983e30a0b434fe5d77e5773b) |

新 Plugin Manager 的失败语义非常具体：安装失败/取消恢复快照中的 `package.json` 与 `pnpm-lock.yaml`，但下载物、pnpm store、日志以及部分 build approval 状态可保留；remove 失败保留已完成的部分修改。已安装 Host 代码在进程内运行，位于 workspace sandbox 之外；依赖 build-script 批准是另一条边界，服务本身不验证“对话中用户已同意”的真实性。这些都支持书中“注册可撤销不等于业务可回滚”的原则，但要求避免过度承诺安装/热更新的原子性。[固定 Plugin Manager 文档](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md)、[Loader group 源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/vendor/loader/src/config/group.ts)。

### 3.4 与可恢复性相关的额外架构增量

9/1 的 [session migration commit](https://github.com/deepseek-ai/deepseek-harness/commit/d1521ea7838f19a78a9cca7b4a93622d301149bb) 与 [embedded stream v2 commit](https://github.com/deepseek-ai/deepseek-harness/commit/f99b06eaed81d6fe4fc64d44687450e18ef68a67) 改变持久化语义。新 architecture 将 `agent/assistant-stream` 作为进程内瞬态流，把完整紧凑流写入最终 `assistant/message` 或 `assistant/attempt`；settlement 前进程硬退出不留下该次完整 durable attempt stream。历史 session 的迁移使用相邻版本链，写打开发布新的版本文件，不覆盖旧 generation。不能继续用“每个增量 chunk 都已 durable”来概括最新实现。这里报告的是可定位的提交变更，未把文档文件名日期当发布日期。

## 4. Codex：真实本机运行与协议纠错

### 4.1 实跑与限制

可执行文件为 `/opt/homebrew/bin/codex`，链接到 Homebrew Cask 0.142.5。实际运行了：

```text
codex --version
codex app-server generate-json-schema --out <vendor_probe/codex/local/schema>
codex app-server generate-json-schema --experimental --out <vendor_probe/codex/local/schema_experimental>
codex app-server --stdio ...
```

上述操作通过本地 `sandbox-exec` 包裹：前两次写入仅允许 `vendor_probe` 与 `/dev/null`；首次全面拒绝网络，第二次允许本地 IPC、仍拒绝 IP 入站/出站。随后按用户要求做第三次 initialize-only 重试：先调用本机 `codex app-server --help`，明确确认 `--stdio` 等价于 `--listen stdio://`；用 `mktemp -d /private/tmp/codex-vendor-init.XXXXXX` 创建 `/private/tmp/codex-vendor-init.Zm1Lqy`，额外允许该短路径的临时文件、日志和 Unix IPC 写入，`TMPDIR`、`sqlite_home`、`log_dir` 指向该目录，继续拒绝 IP 入站/出站/绑定。三次都未改 `HOME` 或 `CODEX_HOME`，未升级二进制。

- 版本查询和两套 schema 生成：**exit 0**。PATH alias 创建被限制的 warning 已保留，没有妨碍 schema 生成。
- 三次 app-server 启动：均在收到 initialize 响应前报 `Operation not permitted` 并以 exit 1 退出；第三次 backtrace 包含 `<std::fs::File>::try_lock`，但未定位具体路径/系统调用，不能将已剥离符号的回溯当成充分根因证明。**正常握手未验证**；这些是自施限制下的运行结果，不是产品不可用证据。`initialized` 因没有成功响应而没有发送。第三次自然退出，未超时强杀；按用户要求停止继续搭建环境或扩大写权限。
- 未发送 `thread/start`、`turn/start`、工具执行或模型请求。下述 delta 示例是离线 fixture，不是假装抓到的真实模型流。
- 离线方法集合、必要字段以及三份源码对照：**58/58 通过**。这是明确范围的契约检查，不是通用 JSON Schema 验证器，也不是端到端 turn/cancel 测试。环境没有现成 jsonschema/Ajv，因此没有安装依赖或夸大验证范围。

原始输出及输入：[本机结果](vendor_probe/codex/local/probe_results.json)、[第二次受限启动结果](vendor_probe/codex/local_ipc_probe/probe_results.json)、[第三次 initialize-only 结果](vendor_probe/codex/initialize_only/probe_results.json)、[本机帮助输出](vendor_probe/codex/initialize_only/app_server_help.stdout.txt)、[第三次真实发送记录](vendor_probe/codex/initialize_only/requests.sent.jsonl)、[第三次 stderr](vendor_probe/codex/initialize_only/stderr.txt)、[握手请求 fixture](vendor_probe/codex/local/handshake.requests.json)、[测试输入](vendor_probe/codex/local/protocol_test_cases.json)、[58 项结果](vendor_probe/codex/local/protocol_test_results.json)。前两次握手 fixture 列出拟发送的两条消息；实际是否发送以 `probe_results.json` 中的 `initialized_sent` / `only_methods_sent` 为准。第三次直接保存实际发送和接收 JSONL。

### 4.2 第 14 章可采用的协议骨架

| 原示例 | 本次核实接口 | 方向/语义 |
|---|---|---|
| `turn/cancel` | `turn/interrupt` | client request，参数必须包含 `threadId` 和 `turnId` |
| `item/start` | `item/started` | server notification |
| `item/update` | 例如 `item/agentMessage/delta` | server notification；没有统一名为 item/update 的方法；其他 item 类型有各自 delta |
| `item/completed`、`turn/completed` | 名称正确 | server notification；业务完成判定仍需独立验证 |

```text
client request: initialize
client notification: initialized
client request: thread/start, turn/start, turn/interrupt
server notification: item/started, item/agentMessage/delta,
                     item/completed, turn/completed
```

下面只展示离线验证的最小报文形状，ID 为占位值，未向活动任务发送：

```jsonl
{"id":2,"method":"turn/interrupt","params":{"threadId":"audit-thread-placeholder","turnId":"audit-turn-placeholder"}}
{"method":"item/agentMessage/delta","params":{"threadId":"audit-thread-placeholder","turnId":"audit-turn-placeholder","itemId":"audit-item-placeholder","delta":"schema fixture only"}}
```

8/27 基线源码已经使用这些正确名称：[426fa8cdab4247e5623e9617d531f6917482b947 / common.rs](https://github.com/openai/codex/blob/426fa8cdab4247e5623e9617d531f6917482b947/codex-rs/app-server-protocol/src/protocol/common.rs#L985)。当前稳定 0.155.1 仍然如此：[turn/interrupt](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1056)、[item 通知](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1941)。因此应归入“旧稿事实纠错”，不能说 9 月由 cancel 改成 interrupt。

### 4.3 本窗口可确认的产品变化

| 发布日期（UTC） | 版本 / 固定 commit | 与书中架构相关的变化 |
|---|---|---|
| 8/29 | [0.151.0 release](https://github.com/openai/codex/releases/tag/rust-v0.151.0) / [78c290807ce710180111df227df3b7a4fe845452](https://github.com/openai/codex/commit/78c290807ce710180111df227df3b7a4fe845452) | 扩展可检查/替换 MCP 工具结果；项目 marketplace 合并与诊断；修复远程 sandbox/恢复权限及权限变化后陈旧审批的问题。 |
| 9/1 | [0.152.0 release](https://github.com/openai/codex/releases/tag/rust-v0.152.0) / [316795b3cf2a45e90d121d9f46499d4658b2645c](https://github.com/openai/codex/commit/316795b3cf2a45e90d121d9f46499d4658b2645c) | App Server `thread/shellCommand` 可配置更长超时；MCP 单工具 `output_token_limit`；恢复/压缩过程更好保留权限与授权。 |
| 9/3 | [0.153.0 release](https://github.com/openai/codex/releases/tag/rust-v0.153.0) / [41e22fee981a63b3698df7ed36bad393cda24715](https://github.com/openai/codex/commit/41e22fee981a63b3698df7ed36bad393cda24715) | 插件 CLI 管理远程 marketplace；外部 App Server 断线重连保留草稿/转录，对不确定或排队提交暂停处理；审批历史跨恢复/压缩保留。 |
| 9/9 | [0.154.0 release](https://github.com/openai/codex/releases/tag/rust-v0.154.0) / [6b9826e3aa83b1a5947db50f4332cb9c65f1b340](https://github.com/openai/codex/commit/6b9826e3aa83b1a5947db50f4332cb9c65f1b340) | Windows 后台 server/daemon 生命周期和托管更新；活动会话刷新插件、skills/hooks；MCP OAuth 刷新不自动重放遭拒工具调用。worktree 支持明确为 experimental。 |
| 9/17 | [0.155.0 release](https://github.com/openai/codex/releases/tag/rust-v0.155.0) / [f0a1b8f0849d90960bc406b848f32e5a129b0457](https://github.com/openai/codex/commit/f0a1b8f0849d90960bc406b848f32e5a129b0457) | daemon 自动更新计划、显式 update 命令、重启后保存线程/活动 goal 恢复；Python SDK/runtime 发布版本对齐。voice 明确仍 experimental。 |
| 9/18 | [0.155.1 release](https://github.com/openai/codex/releases/tag/rust-v0.155.1) / [be2951ea34f0d295ed0becf97079f92fa5f6950e](https://github.com/openai/codex/commit/be2951ea34f0d295ed0becf97079f92fa5f6950e) | 修复本地 TUI reasoning summary 默认值，避免不支持它的 provider 拒绝请求；不代表协议架构整体重写。 |

第 14 章接入面表格也不宜再仅写 TypeScript SDK：本窗口有 [Python SDK 0.154.0 release](https://github.com/openai/codex/releases/tag/python-v0.154.0)（9/10 19:51:43），包含 typed protocol、ExternalMessage 和历史/单 turn 选项的变更及迁移说明。它是一个已有 SDK 的版本发布；本次没有证明 Python SDK 首次出现日期，不写成“9 月首次新增 Python SDK”。

## 5. OpenHands：旧 Runtime 与新 SDK 的边界

### 5.1 旧结构与迁移日期

旧版 [0.62.0 固定 commit 7fbb48c40679afd674970966b96185657d92a487](https://github.com/OpenHands/OpenHands/commit/7fbb48c40679afd674970966b96185657d92a487) 中，`Runtime` 接收 `EventStream` 并订阅事件；Runtime client 通过 HTTP 将 action 交给 `ActionExecutor`，后者管理 shell/browser/plugins 并返回 observation。第 17 章的架构描述可以落到这个历史实现。[Runtime README](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/README.md)、[base.py](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/base.py)、[ActionExecutor](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/action_execution_server.py)。本次未打开旧文档 URL，不声称其当前是否重定向；版本判断依赖固定源码。

应用 [OpenHands 1.0.0 release](https://github.com/OpenHands/OpenHands/releases/tag/1.0.0) 在 **2025-12-16 16:03:32** 明确宣布使用新 software-agent-sdk，对应 [0cb27a4aa8c2656c37c00a8d52ad574c1c21649b](https://github.com/OpenHands/OpenHands/commit/0cb27a4aa8c2656c37c00a8d52ad574c1c21649b)。SDK 自己的 `1.0.0` release 是 **2025-11-06 17:07:14**，对应 [a612c0a685fa96bc725085ac81c59492d4a88974](https://github.com/OpenHands/software-agent-sdk/commit/a612c0a685fa96bc725085ac81c59492d4a88974)。这两条独立版本线不能混在一起。

8/27 的 [OpenHands README](https://github.com/OpenHands/OpenHands/blob/b50c60c6728e2ce123ccb6e125bee3eb88ac87d1/README.md) 已将本仓库定位为 Agent Canvas，并把 agent、tool、conversation、workspace、events、REST/WebSocket server 契约归给 SDK。这是旧稿漏收的既有结构。9/19 当前 SDK 的 `Conversation` 工厂依据 workspace 选择 LocalConversation 或 RemoteConversation；远程会话连接 Agent Server。[1.49.2 固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py#L34)。

### 5.2 本窗口真实增量

| 首个确认版本 / 发布日 UTC | 变化 | 不可变依据与解释 |
|---|---|---|
| SDK 1.45.0 / 9/7 | TypeScript client 搬入 SDK monorepo；事件先持久化再发布；增加 session socket 的非 Event envelope。 | [client 合并 commit，8/30](https://github.com/OpenHands/software-agent-sdk/commit/704cbe6015e3d59cabe04632175d99df2d448999)、[persist-before-publish，9/2](https://github.com/OpenHands/software-agent-sdk/commit/94fca578b720df758b9bbf8a2639511b303c78e6)、[socket envelope，9/3](https://github.com/OpenHands/software-agent-sdk/commit/2ab274897ac5e2c66b0ba17e9a6d39367b769876)。日期来自已合并 PR 记录，发布见 [1.45.0](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.45.0)。 |
| SDK 1.47.0 / 9/10 | Agent Server 增加 OpenAI Responses gateway；StreamContext 管理 stream identity 与关闭。 | [1.47.0 release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.47.0)、[stream commit](https://github.com/OpenHands/software-agent-sdk/commit/03900b331d575abc8207f2f31536cb3209c19ef4)。协议兼容网关不等于 OpenAI 托管服务。 |
| SDK 1.48.0 / 9/15 | runtime API/client 按 conversation 作用域隔离；增加 Kubernetes AgentSandboxWorkspace；profile secret 范围控制。 | [conversation-scoped runtime commit，9/14](https://github.com/OpenHands/software-agent-sdk/commit/b5c8ab950401996f171b29c076900fa22fc80e21)、[AgentSandboxWorkspace commit，9/14](https://github.com/OpenHands/software-agent-sdk/commit/47cc483742863d381ecaef8c7b131219d348d15c)、[release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.48.0)。未实部署 Kubernetes，不能由发布说明推出多租户隔离已被本次验证。 |
| SDK 1.49.0 / 9/16 | Agent Server 新增 **每会话 Docker 容器 runtime mode**，并发布 python-minimal image。 | [3ff6924d8564b3d47a22a6c7e71377a701ae014f](https://github.com/OpenHands/software-agent-sdk/commit/3ff6924d8564b3d47a22a6c7e71377a701ae014f)，PR 9/16 19:59:06 合并；[release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.0) 21:29:26 发布。旧版已有 Docker Runtime，新增的是新 SDK/Agent Server 的这一模式，不是 Docker 支持首次出现。 |
| SDK 1.49.1 / 9/17 | 修复 Docker conversation metadata route。 | [release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.1)，不能跳过补丁版风险说明而只推荐首发 1.49.0。 |
| SDK 1.49.2 / 9/17 | 修复 Docker catalog 旧会话保留、重复扫描、proxy root path、workspace 创建、删除期间重启；加入 Agent Plugins `mcp.json` loader 和包路径 containment 修复。 | [release](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2)、[固定 provisioning 源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py)。 |
| Canvas 1.20.0 / 9/17 | UI/profile secret 选择、转发 Docker conversation runtime 配置、automation 选择 saved profile。 | [release](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0)；固定 [package.json](https://github.com/OpenHands/OpenHands/blob/9737f713616a1e452f822c2967f0e2c8bf2dc308/package.json) 为 Canvas 1.20.0，TypeScript client 精确依赖 1.49.2，直接证明 UI 与 SDK 版本线不同。 |

原章“决策与执行环境分离”的原则仍成立；需要更换当前实现的名词和版本标识。local agent-server 也不自动代表容器隔离：8/27 README 已明确本机直接运行会有完整文件系统访问。这里是配置与部署模式差异，不是可以从 `Runtime` 类名推出的安全保证。

## 6. 证据、复现与覆盖边界

- `vendor_probe/*/{head,baseline,repo,releases_page_1}.json`：仓库抓取点、8/27 默认分支基线及 release 原始记录；`tags/*.json` 将 release tag 固定到 commit。
- `vendor_probe/dsh/source/{old,new}` 与 `dsh/diffs`：指定两点的文档/关键实现；`history`、`commits` 定位窗口内变更。根 README 除 Citation 外没有实质架构改写，developer preview 警示两点都有。
- `vendor_probe/codex/local`：实机 schema、命令 stdout/stderr、拟发送握手报文、离线 JSON 用例与结果；`local_ipc_probe` 保留第二次受限启动，未覆盖首轮失败证据。
- `vendor_probe/codex/initialize_only`：第三次短路径临时目录重试的本机帮助、沙箱 profile、实际发送/接收 JSONL、stderr 和运行参数；外部临时目录获用户明确授权，仅用于本次 probe，路径记入结果。
- `vendor_probe/openhands/source/legacy_0.62.0` 与 `sdk/source/stable_1.49.2`：旧 Runtime 和新 SDK 的固定实现；`sdk/prs` 保留用于日期区分的 PR 元数据。
- `vendor_probe/evidence_index.json`：最终生成的证据路径、大小与 SHA-256；`verification_summary.json` 汇总机器检查结果。

本轮不是完整仓库安全审计，也没有部署 dsh/OpenHands 或运行其模型任务。GitHub compare 返回 `total_commits=3833`，但只给 300 个文件，不能当完整 diff；本结论来自固定 commit 内容 API、完整未截断 tree、定向路径历史和 release 记录。没有遍历所有 3833 个提交。路径历史用于证明具体变更，不据此声称覆盖所有架构变化。

复现核心离线检查：在仓库根执行 `python3 research/audits/review_20260919/vendor_probe/protocol_contract_checks.py`。重新跑本机受限 probe 使用同目录 `codex_probe.py`；结果仍需按退出码和是否收到 initialize response 判断，不能只看生成了日志文件。

本次只交付报告和证据，不修改第 14/16/17 章、site 镜像稿、部署或研究账本。planning-with-files 用于隔离证据和进度；OpenAI Docs 的一般文档优先次序依用户明确要求改为本机/官方仓库优先。

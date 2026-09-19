# 产品篇修订处置记录（2026-09-19）

分支：`codex/research-revision-20260919`。对应审阅基线：`a1ed264462d9b61c260c1dc417243303bfc60b66`。

本执行仅用 apply_patch 修改 `manuscript/chapters/13—18*.md`、`manuscript/parts/03_products.md` 及本报告。六章 H1、文件名和篇章位置保持；未联网、未提交、未修改全局 ledger、site 或 artifacts。共享工作区存在其他并行修订，不将其计入本执行的修改或验收。

## 输入与方法

完整读取 `review_20260919/report_vendor_deltas.md`、`research_report.md` 与七个原稿文件；读取 `review_products_evolution_structure.md` 中 R11/R12/R13/R16/R21/R23/R25/R26/R28 等相关完整问题及其上下文。补核八份存档官方网页、dsh PTC/动态 Host/Plugin Manager 文档与源码、OpenHands 会话工厂、Codex 已有 probe 记录。未运行供应商模型、容器部署、浏览器或故障注入。

使用 OpenAI Docs 技能的官方来源与边界区分原则；按用户明确“不联网”要求，来源顺序改为已核验的本地官方网页、固定仓库证据和 probe。RTK.md 在当前工作区、逐级父目录及技能/配置目录的定向查找中未找到，未臆造其规则。

网页日期沿用来源标注；GitHub release 日取已核验的 UTC published_at，源码变更日取 commit/合并记录，文档更新时间不当首发日期。当前公开事实、厂商实验、源码契约、作者设计建议和待测故障场景分别标识。

## 问题处置与落点

| 问题/要求 | 本范围处置 | 正文落点与剩余边界 |
|---|---|---|
| R11 原生接口与自定义契约混写 | Claude YAML、Codex JSON、比较 YAML 均标明本书自定义，不能直接交 CLI/SDK；Codex 协议骨架改为真实方法名并区分方向 | 13§5、14§1/5、18§4；dsh 原生→平台→缺口→降级表在16§6 |
| R12 事实表混入效能/采用判断 | 表头分开事实与作者判断；撤下“组合成熟”“成本高”等无同条件证据的结论；子代理不保证总 token 降低 | 13§1/2/6、14§2、18§1/4；六轴全部未测量、不填分数 |
| R13 Cursor A/B 与 token 方向 | A/B 不再定义为同任务配对；未复核随机化单位/窗口；改为成功率可能下降、token 消耗可能上升 | 15§1/2；NLE 等其他篇勘误不在本执行写范围 |
| R16 context recall 分母 | 由独立标注确定所需资料，不能用 Agent 已读集合定义分母 | 15§1；其余记忆指标由相应篇处理 |
| R21 Runtime 与信任域混淆 | 区分 Agent Runtime / Execution Runtime，功能层与信任域不等价 | 16§6、17§2/6、18§3；未修改第24/26章全书映射 |
| R23 无经济数据的 build-vs-buy 判断 | 改为采购覆盖边界/接入退出成本成立时的条件建议；列统计窗口内总成本与敏感性分析，不给虚构产品分数 | 17§6、18§6；无实际采购成本结论 |
| R25 重复挤占产品纵深 | 五产品各有专有事件/失败剖面；共同 task/session/turn 与业务验收原则集中18§5 | Claude双恢复路径、Codex中断重连、Cursor工具回传、dsh部分失败、OpenHands持久化/发布窗口 |
| R26/R28 可读性与证据边界 | 减少重复英文夹注；保留必要协议名；说明同厂商多URL不等于独立效能来源，给采购/自研/确定性/人工替代 | 全篇局部处置，不声称全书表达或证据门已关闭 |
| Claude Managed Agents 与9月更新 | Code、Agent SDK、Managed Agents、Messages API四面分开；补4月架构、9/3 ant apply、9/10 auto及evaluation、9/14显式压缩归属 | 13§1—4；不把 Messages API 压缩写成 Code/Managed Agents 同一接口 |
| Codex协议、语言与Agents API | turn/interrupt、item/started、typed delta；增加Python SDK；Agents API 9/10 public beta及自管执行非ZDR | 14§1—3；开源实现不覆盖托管内部 |
| Codex probe口径 | 保留本机0.142.5、默认/experimental schema生成成功；58/58为离线成员/字段/源码检查；三次initialize前退出，正常握手未验证 | 14§6；不说线上拒绝错误方法、不可用或端到端verified |
| Cursor新执行与组织面 | 自管worker仍云端循环/推理/规划，输出与转录数据流；Projects 9/10 beta、共享文件/协调委派/subscriptions | 15§4/5；长期能力不写成已验证可靠性 |
| dsh隔离与插件变化 | 动态node:vm非containment且两点未变；9/12 PTC改OS sandbox下新进程；Host插件/安装/HMR不承诺全事务 | 16§2—5；保留alpha、清理平台限制、已存在子调用追踪及瞬态流缺口 |
| OpenHands历史与当前版本 | 0.62.0旧结构有固定源码；应用1.0.0已在2025/12迁新SDK；当前Canvas1.20.0/SDK1.49.2分开 | 17§1/2；非9月首次SDK分离 |
| OpenHands新增契约 | persist-before-publish、非Event envelope、conversation作用域与每会话容器，1.49.1/2补丁风险 | 17§3/4；没有部署、多租户隔离、exactly-once实测 |
| 第18章范围 | 保留五主案例，另设Deep Agents/Microsoft Harness与四类交付对象短表，拆托管/自管责任 | 18§1—3；不扩为品牌排名，Microsoft 9/15只标文档更新时间 |

## 新增 URL 与对应事实（49 项）

“新增”按本执行七个正文文件分别相对 Git 基线取差集，再跨文件去重；包括把浮动源码链接替换为固定 commit 的 URL。下表登记全部新增 URL，供主代理汇入全局证据流程；本执行不改全局 ledger。未新增的原章引用仍保留在正文，不将它们冒称本轮新抓取。

网页证据来自 `review_20260919/retrieval/`，对应八个文件为 `anthropic-release-notes.json`、`anthropic-managed-architecture.json`、`openai-api-changelog.json`、`openai-agents-overview.json`、`cursor-self-hosted.json`、`cursor-changelog.json`、`langchain-context-modes.json`、`microsoft-harness.json`。本执行复算八份 text_sha256 均匹配。

仓库版本、提交/合并与 release 关系沿用 `report_vendor_deltas.md` 及其 `vendor_probe/{dsh,codex,openhands,sdk}/` 证据。48 个 URL 在两份研究报告中已有逐字登记；余下当前 dsh tool-catalog URL 由已存档的同 commit 路径映射，capture 记录 GET 成功且 SHA-256 复算匹配：`de6908c430c5470d57ba958f9a6a54005db9d2a50f64f5b7a8ef2e7338db59a8`。没有为补引用联网。

| 编号 | 新增 URL | 章节 | 精确支撑事实与限制 |
|---|---|---|---|
| P01 | [原文或固定源码](https://www.anthropic.com/engineering/managed-agents) | 13、18 | 4 月 8 日已披露 session 持久日志、Harness 与 sandbox 分离；容器故障作为工具错误，Harness 可据日志恢复；沙箱外凭证库与 MCP 代理。不是九月新架构或本书实测。 |
| P02 | [原文或固定源码](https://docs.anthropic.com/en/release-notes/api) | 13 | 9/3 ant CLI 1.30.0 的 ant apply 与 claude-lock.json；9/10 Managed Agents auto 权限、evaluation/evaluated_permission 及 ant 1.32.0 会话连接；9/14 Messages API 显式压缩 beta 与签名 block。各接口归属分开。 |
| P03 | [原文或固定源码](https://github.com/openai/codex/releases/tag/rust-v0.155.1) | 14 | Rust 0.155.1 于 9/18 UTC 发布，是正文固定的当前非预发布版本；不同于本地 0.142.5 probe。 |
| P04 | [原文或固定源码](https://github.com/openai/codex/blob/426fa8cdab4247e5623e9617d531f6917482b947/codex-rs/app-server-protocol/src/protocol/common.rs#L985) | 14 | 8/27 基线已含 turn/interrupt 等正确协议名称，旧稿错误不是本窗口改名。 |
| P05 | [原文或固定源码](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1056) | 14 | 0.155.1 固定 common.rs 中 turn/interrupt 为请求；用于界定真实方法枚举。 |
| P06 | [原文或固定源码](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1941) | 14 | 0.155.1 固定 common.rs 中 item/started、类型化 delta、item/completed 与 turn/completed 通知。 |
| P07 | [原文或固定源码](https://github.com/openai/codex/releases/tag/python-v0.154.0) | 14 | Python SDK 0.154.0 于 9/10 UTC 发布；typed protocol、ExternalMessage、历史及单 turn 选项的版本变化。没有证明 Python SDK 首发日期。 |
| P08 | [原文或固定源码](https://developers.openai.com/api/docs/changelog) | 14 | 9/10 正式记载 Agents API public beta，提供托管 Codex Harness。 |
| P09 | [原文或固定源码](https://developers.openai.com/api/docs/guides/agents-api/overview) | 14、18 | Agents API 管理会话、编排、压缩与恢复；可选托管或自管执行；当前仅美国数据驻留、不支持 ZDR，自管 sandbox 不改变资格。 |
| P10 | [原文或固定源码](https://github.com/openai/codex/releases/tag/rust-v0.152.0) | 14 | 0.152.0 恢复与压缩过程更好保留权限与授权。 |
| P11 | [原文或固定源码](https://github.com/openai/codex/releases/tag/rust-v0.153.0) | 14 | 0.153.0 外部 App Server 断线重连保留草稿/转录，并暂停不确定或排队提交。 |
| P12 | [原文或固定源码](https://github.com/openai/codex/releases/tag/rust-v0.154.0) | 14 | 0.154.0 活动会话刷新插件/skills/hooks；MCP OAuth 刷新不自动重放被拒工具调用。 |
| P13 | [原文或固定源码](https://cursor.com/blog/self-hosted-machines) | 15、18 | 9/2 自管 worker 在企业机器执行命令、编辑文件，通过出站 HTTPS 回传；循环、推理和规划仍在 Cursor 云端，输出可能带代码，转录可能云端处理/存储。 |
| P14 | [原文或固定源码](https://cursor.com/changelog) | 15 | 9/10 Projects beta：协调者规划与委派，跨云端/本机共享文件，subscriptions、事件及周期工作；需要本机测试时可启动本地 Agent。 |
| P15 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.1.6-alpha.2) | 16 | dsh 0.1.6-alpha.2 于 9/17 UTC 发布，prerelease，不去除 alpha 后缀。 |
| P16 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md) | 16、18 | 当前固定架构的插件服务/类型事件/生命周期、配置层次与持久化语义；用于区分公开实现和作者建议。 |
| P17 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/architecture.md) | 16 | 旧点已存在有序 bundle→profile→home→CLI patch；按 id 替换整份 config，不是深合并，非九月新增。 |
| P18 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/9b7a8ccc9fabc2e87386acf7f8b0741baf978022) | 16 | 9/9 串行 agent/created 初始化完成后才处理排队工作，失败清理。 |
| P19 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/e07f41d5fd8ca172287fda0f923b4d1f69c592f3) | 16 | 9/9 撤回事务式 Cordis reload；不能许诺普通 group/HMR 整批回滚。 |
| P20 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/98b92b683c39fc60771daa774492105c2d3e8076) | 16 | 9/14 增加 profile 级 Plugin Manager，管理持久插件及 Web controls。 |
| P21 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/abd765a6001ff9d9c9772b8b407e0b7f18fe25ab) | 16 | 9/15 HMR 生命周期转由 YAML 管理；base 与 headless/SDK/ACP、sdk-minimal 默认配置不同，可被 patch 覆盖。 |
| P22 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/ed32f57f88ef6bba983e30a0b434fe5d77e5773b) | 16 | 9/16 Creator 改走 Plugin Manager 持久安装；旧 cordis_define/run/stop/undefine 不再作为该组模型工具，动态 runner 并非整体删除。 |
| P23 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/75ed8da3e0c9103b3b2174b2981b7129e1fba21d) | 16 | 9/12 PTC 从 worker thread 改为受平台 sandbox 策略约束的独立 Node 进程；首次进入哪个发布 tag 未穷举。 |
| P24 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/7c9bb5914cedec80e46197a8c894037fcfd12faf) | 16 | 9/12 UTC 统一 PTC 包、服务和事件命名，与执行后端改为进程是分别定位的两个提交。 |
| P25 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/cordis-host-runner/src/sandbox.ts#L1) | 16 | 动态 Cordis Host node:vm 源码明说 not containment；宿主 realm helper 是逃逸路径。新旧两点文件逐字节相同。 |
| P26 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/packages/code-runtime/code-runtime-worker-thread/README.md) | 16 | 旧 run_code worker-thread 后端不提供宿主安全隔离；不能与动态 node:vm 混作同一路径。 |
| P27 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md) | 16 | 当前 PTC 新进程、受限模式缺 backend 时失败、Node API 仍可用；elapsed deadline 默认120000/上限600000，heap cap 非进程树内存限额；清理受平台可观察范围限制，未实测。 |
| P28 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md) | 16 | Plugin Manager 安装失败/取消仅恢复 manifest 与 lockfile；启用失败不撤销安装，remove 保留部分修改；下载物/日志/部分构建批准状态可残留；Host 代码在工作区 sandbox 外，服务不验证对话批准真实性。 |
| P29 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/f99b06eaed81d6fe4fc64d44687450e18ef68a67) | 16 | 9/1 embedded stream v2：assistant-stream 为瞬态，最终 message/attempt 保存完整紧凑流；settlement 前硬退出有缺口。 |
| P30 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/d1521ea7838f19a78a9cca7b4a93622d301149bb) | 16 | 9/1 session migration：沿相邻版本迁移，写打开生成新文件而不覆盖旧 generation。 |
| P31 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/tool-catalog.md) | 16 | 旧 tool catalog 已有桥接子工具守卫与逐调用追踪，不能把这些说成尚需平台从零提供。 |
| P32 | [原文或固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-catalog.md) | 16 | 当前工具目录包含 PTC 桥接子调用守卫及 tool/ptc-dispatch-start、tool/ptc-dispatch；已保存同 commit 原文与 capture hash。 |
| P33 | [原文或固定源码](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0) | 17 | Canvas 1.20.0 于 9/17 UTC 发布，含 profile secret 选择、Docker conversation runtime 配置转发与 automation saved profile 选择。 |
| P34 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2) | 17 | SDK 1.49.2 于 9/17 UTC 发布，修复 Docker catalog、重复扫描、proxy root path、workspace 创建及删除期间重启等；与 Canvas 独立版本线。 |
| P35 | [原文或固定源码](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/README.md) | 17 | 0.62.0 历史 Runtime/EventStream/client/ActionExecutor 架构的固定依据，不作为当前 SDK 类图。 |
| P36 | [原文或固定源码](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/action_execution_server.py) | 17 | 0.62.0 ActionExecutor 历史实现管理 shell/browser/plugins 并返回 observation。 |
| P37 | [原文或固定源码](https://github.com/OpenHands/OpenHands/releases/tag/1.0.0) | 17 | 应用 1.0.0 于 2025/12/16 UTC 已宣布采用新 software-agent-sdk；迁移并非九月首发。 |
| P38 | [原文或固定源码](https://github.com/OpenHands/OpenHands/blob/b50c60c6728e2ce123ccb6e125bee3eb88ac87d1/README.md) | 17 | 8/27 README 已将应用仓库定位为 Agent Canvas，并区分 SDK/Agent Server；本机直接运行不自动获得容器隔离。 |
| P39 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py#L34) | 17、18 | SDK 1.49.2 Conversation 工厂依 workspace 选择 LocalConversation 或 RemoteConversation；后者连接远端 Agent Server。 |
| P40 | [原文或固定源码](https://github.com/OpenHands/OpenHands/blob/9737f713616a1e452f822c2967f0e2c8bf2dc308/package.json) | 17 | Canvas 1.20.0 package.json 精确依赖 TypeScript client 1.49.2，证明 UI 与 SDK 版本不同。 |
| P41 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/commit/94fca578b720df758b9bbf8a2639511b303c78e6) | 17 | 9/2 合并的 persist-before-publish 变更：先持久化事件再发布；不代表外部副作用原子提交或恰好一次投递。 |
| P42 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/commit/2ab274897ac5e2c66b0ba17e9a6d39367b769876) | 17 | 9/3 session socket 增加非 Event envelope；不能把每条传输消息当成持久业务事件。 |
| P43 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.45.0) | 17 | 9/7 SDK 1.45.0 发布包含 TypeScript client 迁入、persist-before-publish 与 socket envelope。 |
| P44 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.48.0) | 17 | 9/15 SDK 1.48.0 发布：conversation-scoped runtime API/client、Kubernetes AgentSandboxWorkspace 与 profile secret 范围控制；未部署验证。 |
| P45 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/commit/3ff6924d8564b3d47a22a6c7e71377a701ae014f) | 17 | 9/16 新 SDK/Agent Server 增加 per-conversation Docker containers runtime mode，非 OpenHands 首次支持 Docker。 |
| P46 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.1) | 17 | SDK 1.49.1 修复 Docker conversation metadata route；保留补丁版演进边界。 |
| P47 | [原文或固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py) | 17 | SDK 1.49.2 的 Docker runtime provisioning 固定实现，支撑容器创建/恢复检查点；未声称完整安全审计。 |
| P48 | [原文或固定源码](https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness) | 18 | 9/8 Deep Agents isolated/fork 上下文模式；fork 继承父状态并整理尾部委派调用，适用工作关系与独立审阅需求不同。 |
| P49 | [原文或固定源码](https://learn.microsoft.com/en-us/agent-framework/concepts/harness) | 18 | Microsoft Harness 组合现有 Agent Framework client/context/session/middleware，提供持久化、todo、模式、审批、观测、可选有界循环；9/15 为文档更新时间，非已证实首发日。 |

## 离线复核结果

- 七个正文文件均标记 2026-09-19；六章 H1 及导言标题与基线相同。
- 代码围栏成对，Markdown 表格列数一致；唯一 JSON 配置块可解析。此项只验证结构，不把自定义工作表称为厂商 schema。
- 所有 GitHub blob 引用使用固定 commit，没有 main/master 浮动源码链接。
- 新增 URL 共49项，逐项映射到本表；不把网页地址当作不可变内容，网页版本由本地存档与 hash 固定。
- 八份网页存档 hash、dsh 当前工具目录 capture hash 均复算一致；新旧动态 Host sandbox.ts 逐字节相同。
- 读取历史结果确认 `protocol_test_results.json` 的 total=58、passed=58；`initialize_only/probe_results.json` 的 initialize_success=false、initialized_sent=false、exit_code=1。没有重跑 probe、没有写回任何历史证据。
- 指定正文范围 `git diff --check` 通过。未运行会写 site/artifacts/其他审计报告的构建或发布脚本。

以上仅是本次产品篇编辑与离线一致性复核。供应商端到端执行、隔离强度、跨产品效能/经济性、PDF与站点排版均不在本执行验证范围。全书 R21/R23/R25 等跨篇项只完成产品篇部分，需由主代理合并对应篇章与全局证据后验收。

# 2026-09-19 全局证据整合处置

## 结果与范围

登记来源174、证据195、核心主张71；主张状态：{'supported': 71}。
已核验仅指来源身份、指定版次及本地捕获定位；不等于逐句事实认证、实验复现或产品端到端通过。
本次仅修改research/evidence的sources.jsonl、evidence.jsonl、claims_v2.jsonl、README.md，并按追加授权新增claims_backlog.jsonl；新增整合脚本及本报告。未联网、未创建浏览器、未修改正文/site/artifacts、未提交发布。所有手写编辑用apply_patch，JSONL/README/报告由获授权的机械脚本生成。
使用deep-research的来源身份、证据持久化及主张边界方法；按用户指定文件范围和离线要求，未执行技能中的联网检索或HTML/PDF流程。

## 输入与历史修复

读取当前manuscript目录下全部Markdown引用（含executive_brief.md），共132个不同引用URL；产品处置表49个URL全部入册。合并review_20260919的37来源/证据及非社区窄主张；读入revision_20260919/retrieval当前全部有效原文快照及vendor_probe固定源码/API capture。
原84条source ID保留；其中56条已绑定当前原文或固定源码。原71条evidence ID与文字保留，69条改为legacy_paraphrase，其余逐字验证；原始类型、定位与日期留历史字段。
GSME旧题名钉住v1，v2另建HarnessBank来源，不把旧摘录绑到新题名；同版abs/html别名不拆成独立来源。C009以基线传输文档及当前方法枚举补证；C014区分动态Host node:vm、旧worker及新PTC进程；C015区分历史Runtime和现代SDK；C019采用HarnessBank v2；C021纠正NLE并收窄负结果归因。
MCP2026-07-28单独登记stateless/self-contained request及逐请求version/capabilities；2025-06-18和2025-11-25仍作为有版本前提的历史规范，不改成当前最新。Building effective agents仅作为2024历史材料，页面的过时说明不被删去。
Cursor hooks沿用source ID b1f6985403c6eaa1，raw URL改为cursor.com/cn/docs/hooks；旧docs.cursor.com/hooks保留为身份别名及被拒绝的目录捕获记录。第15章新增窄claim区分云端command-only/早期只读缺口、退出2阻断、其他非零默认放行和权限hook退出0但非法JSON/schema阻断；仅为文档契约，未逐运行面实测。
community来源保留为发现线索，不进入核心主张；harness-survey编号/日期异常仍未解决，D36单独进入claims_backlog.jsonl，disposition=deferred、support_status=needs_review，不篡改成supported也不进入strict core。

## 验证口径

本次直接引文按作品/版次累计的最大英文词数为25，上限25。每条direct_quote都逐字存在于指定capture字段，SHA-256匹配；source_summary使用中文归纳并保存原文上下文定位，不能把摘要标签自动当作语义证明。
验证ID唯一、引用关系、五类source_type、版本URL一致、社区排除、引文总额、原71记录保留，以及来源/证据/主张的定位。检查并不验证论文结果、云端实现、安全强度或全书每句话。
本地Codex probe仍只说明已有58/58离线检查，正常initialize握手未验证；没有重跑probe，也没有覆盖历史失败证据。
本报告列出真实待审项，不为取得PASS改变结论；主代理维护的当前审计器实际只读调用结果由末尾报告。

## 元数据尚未核验的正文URL

| URL | source ID | 当前引用位置 |
|---|---|---|
| 无 | — | — |

## 没有当前原文capture绑定的正文URL

此表包括保留历史metadata verified但本轮不能逐字重核的来源；不因此宣称其内容为假。

| URL | source ID | 当前引用位置 |
|---|---|---|
| 无 | — | — |

## 拒绝用作原文的捕获

挑战页和泛目录保留在原采集目录作为访问记录，不用于metadata升级或内容支撑。历史metadata verified可保留，但不代表本次获得原文。

| URL | 捕获文件 | 原因 |
|---|---|---|
| [来源](https://docs.cursor.com/hooks) | research/audits/revision_20260919/retrieval/core-cursor-hooks.json | documentation_landing_page_not_hooks_content |
| [来源](https://doi.org/10.1016/0004-3702(71)90010-5) | research/audits/revision_20260919/retrieval/core-strips.json | challenge_page_not_source_content |

## 全部核心主张与覆盖状态

supported仅指下列精确限定文本的来源支撑。未支持的旧记录列在同表，避免隐藏覆盖缺口；作者建议、教学数据和预测不因附有URL自动变成事实claim。

| Claim | 章 | 状态 | 精确主张 | evidence ID |
|---|---|---|---|---|
| C001 | 01 | supported | STRIPS将问题求解表述为寻找操作序列，把初始世界模型变成能证明目标公式成立的世界模型。 | b4299630eabe66e7, 192b78b0586da9c8 |
| C002 | 01 | supported | Contract Net通过任务持有节点与潜在执行节点的协商分配分布式问题求解任务。 | 7a50af99b5241538 |
| C003 | 02 | supported | ReAct将推理轨迹与任务动作交替生成，利用外部环境信息更新动作计划。 | 56b6cd2dfc17e623 |
| C004 | 03 | supported | SWE-agent v3研究Agent-Computer Interface，并报告定制接口改善文件编辑、仓库导航及执行测试等能力。 | 5fa5e515322f68c0 |
| C005 | 04 | supported | SWE-bench v3以真实GitHub issue及对应pull request构建仓库级代码修复评测。 | 90ac366e61b7db0a |
| C006 | 04 | supported | OpenAI在2026年说明停止报告SWE-bench Verified分数，主要指出测试拒绝正确解及训练污染问题。 | 4281a77cd5ea341a, 5825dd01ca5e9855, f708029ff2e8fc50 |
| C007 | 13 | supported | Claude Agent SDK嵌入Claude Code的模型—工具结果循环，返回cost/session信息，并在上下文接近上限时自动压缩。 | 6ec8a492446373ac, 77feae58a5fc618c, 6782a6d003e4828d |
| C008 | 13 | supported | Anthropic报告其内部使用中sandboxing使Claude Code权限提示减少84%。 | 373d21a3dd4cc86d |
| C009 | 14 | supported | Codex 8/27基线文档说明stdio用JSONL并省略jsonrpc字段；0.155.1协议枚举采用turn/interrupt请求、item/started及按类型区分的delta通知。 | 68e7851c8aeb8da4, 73110308e93407ba, abcffc9012c38550, 57d5affe9dd7539f, 75fb920f730ead6f |
| C010 | 14 | supported | Codex 0.154.0发布说明提供实验性worktree支持，可为新建或fork会话创建隔离checkout。 | eac63102187e79ed |
| C011 | 15 | supported | Cursor把长输出、会话历史、MCP描述和终端输出外置为文件；其A/B报告实际使用MCP的运行token减少46.9%，幅度随安装数量变化。 | 393bbb76b3e97fb1, 70f6816b1c8b9fc2, daa606e5b3cf2eab, 7165987e489fd588, ce7746508bbd20f6 |
| C012 | 15 | supported | Cursor披露按提供商和模型版本定制提示与工具形式，并用离线评估和在线对照迭代。 | 37c98f2cc1e70dbc, 112ad60509e2dbd9, 48b320c66185c841 |
| C013 | 16 | supported | dsh固定当前README仍声明developer preview及兼容性破坏风险。 | 32e184a20b758a32 |
| C014 | 16 | supported | dsh动态Cordis Host的node:vm不提供containment；旧run_code后端是worker thread，当前PTC改为受所选平台sandbox约束的新Node进程，两条路径不能混写。 | 5b8bd0aaa894383c, 54eeaffed629e8ce, da56ddd63c1e286a, 547694c8c3e0d37c |
| C015 | 17 | supported | OpenHands的EventStream/Runtime/ActionExecutor结构属于0.62.0历史实现；当前SDK1.49.2的Conversation按workspace选择本地会话或连接远端Agent Server的会话。 | a7e7f47e3f9b7d0d, 699a7ccaeca04eae, 590b6f09740b17aa, 55e783c8d7707637 |
| C016 | 20 | supported | Reflexion将反馈转成保存在情景记忆中的语言反思，用于后续trial，不更新模型权重。 | a8623728e7fc195a, fb93916b9675570b |
| C017 | 21 | supported | Voyager组合自动课程、可执行代码技能库与包含环境反馈/执行错误的迭代提示，并复用技能处理新任务。 | 4de0315ac0708647, ac431d2124192328 |
| C018 | 19,22 | supported | Self-Harness v3把Weakness Mining、Harness Proposal和Proposal Validation连成循环，并由作者报告所测模型/任务上的留出改善。 | fea5849e3f360bcb, f8c1035f32c5ed0e |
| C019 | 19,22,30 | supported | 当前正文采用HarnessBank v2：语义基因库按修改位置与失败病理保存/重组机制，提案与确定性评价分工，并以有效性、激活、配对显著性和增益门筛选候选。 | 4c2872e011bbc26c, 99e63c65001142e4 |
| C020 | 21 | supported | Living-Harness v2将轨迹和评价信号写入episodic memory与state graph，用于后续交互；工具与基础上下文保持冻结。 | e34a73230c1d0552 |
| C021 | 22 | supported | HSI在所测冻结模型与BALROG设置中未实质改善NLE；NLE全称NetHack Learning Environment。 | 646139d163e9439f, 9dac409ae4f9f8b8 |
| C022 | 23 | supported | 两篇指定版本研究分别报告LLM评价中的自偏好及位置偏差，结论受所测模型与任务限制。 | 4d5991626827b3f4, 7304844a9b40f6bb |
| C023 | 24 | supported | EvilGenie v2与SpecBench v2分别把编程奖励投机和可见/留出测试表现差距作为评测对象。 | 956f0f5433b33d43, 243a0f275d5a6dcc |
| C024 | 11 | supported | Anthropic报告其BrowseComp分析中三因素解释95%性能方差，token单项解释80%；其数据中Agent与多Agent约用聊天4倍和15倍token。 | 26ba071523783b1f, 83488fc64719bbe6, 020245a826fee87a, 399943a5f9928fe6 |
| C025 | 05,08 | supported | Pi当前README列默认read/write/edit/bash四工具，且将MCP、子代理、权限弹窗、计划模式与后台bash留给扩展或外部组织。 | fd0a817962d7e619, 67db237ef1176f4d, 395ef3ce35ad4538, 4284f146ee022345, dc92d51a1b1da9db, 9ad0a379fbe226d4 |
| R20260919_D01 | 07,14 | supported | OpenAI 在9月10日发布托管Codex harness的Agents API公测。 | r19-e20f01f44c1a8f07 |
| R20260919_D02 | 14,18 | supported | Agents API当前只支持美国数据驻留且不支持ZDR；自托管sandbox不改变该限制。 | r19-4c040aafbfff1a99, c1b8e902587fc4f4 |
| R20260919_D03 | 07,13 | supported | 9月14日Claude Messages API新增按需压缩beta；这不等于Code CLI或Managed Agents同名接口。 | r19-b21a7d9e5de4cce9 |
| R20260919_D04 | 13,18 | supported | 该工程文解释会话存储、harness与沙箱从同容器走向解耦，属于4月旧资料。 | r19-54f3a4786e099f85 |
| R20260919_D05 | 15,18 | supported | Cursor自管机器只迁移执行环境，推理规划仍在云端。 | r19-25cb88972e6a216d |
| R20260919_D06 | 15 | supported | 9月10日Cursor Projects以beta阶段逐步开放。 | r19-a069bf516cf80209 |
| R20260919_D07 | 02,07,11,18 | supported | Deep Agents子代理增加isolated/fork上下文模式；工作者和独立验证者适用条件不同。 | r19-5b710c637810e5d8 |
| R20260919_D08 | 02,18 | supported | Microsoft Harness是既有Agent Framework构件的组合；更新日期不等于首发日期。 | r19-3cbe09e4fca70ad8 |
| R20260919_D09 | 19,22,23,24,30 | supported | HarnessDev的Evolution每个creator–runtime单元只有单条演化轨迹，不能做总体可靠性推断。 | r19-2659e438859ad990 |
| R20260919_D10 | 20,24,30 | supported | HoH在既有coding harness外编排规划、开发、独立评估循环。 | r19-ee8a72dd7ad2e172 |
| R20260919_D11 | 19,21,22,23,30 | supported | JIT-Agent训练生成harness的辅助模型，不能称整个系统完全没有权重训练。 | r19-923af398937fd765 |
| R20260919_D12 | 22,24,30 | supported | HarnessEvolve用已知正确答案生成参考轨迹，企业迁移需要该监督条件。 | r19-85a07af4b06684fd |
| R20260919_D13 | 12,20,22 | supported | 176设置研究的planning/action-space消融只覆盖T4/128k，不能泛化到全部预算。 | r19-59b7cdfeedaed22f |
| R20260919_D14 | 09 | supported | HookPry的攻击前提是控制插件更新与hook配置；不是任意输入均可突破沙箱。 | r19-08fdf168a6984147 |
| R20260919_D15 | 07,09 | supported | MemSecBench把记忆写入、后续使用和选择性清除置于同一生命周期验证。 | r19-630d7f9b2abce2e6 |
| R20260919_D16 |  | supported | ACP v2调整会话/消息生命周期，但当前公告仍标草案；不应默认作为稳定生产协议。 | r19-2898993f75e81d76 |
| R20260919_D17 |  | supported | LangSmith Engine从轨迹问题产出评测与回归样本，另派修复代理，属5月旧实践。 | r19-541bcbcdd5b322fd |
| R20260919_D18 |  | supported | HEART把模式解析放进工具包装内的LLM；接口简化不意味着底层约束消失。 | r19-e4ddeb510143555f |
| R20260919_D19 | 19,30 | supported | RSI五级路线图是综述与初步证据，不是已经达到完全递归进化的证明。 | r19-21affffda0f044b0 |
| R20260919_D20 |  | supported | Show-Harness把语义动作交给具体机器人的解释器落地，提示ACI可扩展到具身领域。 | r19-2f3d36f5cfb098cf |
| R20260919_D21 | 22,30 | supported | Ecdysis通过跨实例失败聚合修改harness，文中training期间任务模型和环境固定。 | r19-74f8426b91643cf2 |
| R20260919_D22 | 20,30 | supported | Colosseum把验证反馈路由到证明依赖中的相应部分，而非只做多数票。 | r19-9b8244d0a546548b |
| R20260919_D23 | 19,22,30 | supported | SoL-Pi效率配置有分数让步，不能把更少token写成无损收益。 | r19-1bfe16339eb924af |
| R20260919_D24 | 19,22 | supported | Self-Harness当前仍v3，未发现本窗口内新版本。 | r19-024c24bea6c2382b |
| R20260919_D25 | 19,21 | supported | Living-Harness当前仍v2，未发现本窗口内新版本。 | r19-b48591a9d15bb976 |
| R20260919_D26 | 19 | supported | 原书GSME名称与严格计量表述对应v1。 | r19-8da39580e6a5a8b1 |
| R20260919_D27 | 19,22 | supported | arXiv:2607.13683v2题名为HarnessBank；v1旧题名GSME与v2来源分开登记。 | r19-3b57c8ec75ebb8ee |
| R20260919_D28 | 22 | supported | NLE不是非语言增强任务，而是NetHack Learning Environment。 | r19-9a5f511731f350bb |
| R20260919_D29 | 22 | supported | HSI实验中的MiniHack/NLE属于roguelike环境，失败不证明一般模型能力的数学上限。 | r19-c8eef2c91094b4e2 |
| R20260919_D30 | 12 | supported | Google主张行为评测与端到端评测互补，并提醒避免固定唯一工具序列。 | r19-19d24805b684c67f |
| R20260919_D31 |  | supported | openJiuwen区分结构可组合与运行时适应；处于上轮截面边界，不强称9月新发。 | r19-fcf07bbe4e87c1a7 |
| R20260919_D37 | 25 | supported | BigQuery支持该时间旅行语法，但不能把数周前的as-of字面量当长期可复现快照。 | r19-611c0216838520fa |
| R20260919_CLAUDE_CONFIG | 13 | supported | 9/3 ant CLI增加ant apply及claude-lock.json资源定位；9/10 Managed Agents增加auto权限逐调用evaluation记录。 | 4ce5066a1de0b759, 4fd9b0c6b3a03967 |
| R20260919_MANAGED_SPLIT | 13,18 | supported | Anthropic在4/8工程文中把持久session、Harness与sandbox分离，分别处理执行环境和Harness失败。 | 30a6e04e270a5226 |
| R20260919_CURSOR_DATA | 15,18 | supported | Cursor自管worker通过出站HTTPS接入云端，工具输出可能含代码回传，转录可能在云端处理和存储。 | dac109fb77ebf014, 6d2e90ad37f82bfa |
| R20260919_CURSOR_PROJECTS | 15 | supported | Projects beta包含协调委派、跨机器共享文件及subscriptions周期/事件工作；持续运行可靠性未实测。 | 54402d12f2f640c0, e310cca5daf544f5, 7a1d9f2c7d26b7b3 |
| R20260919_CURSOR_HOOK_BOUNDARIES | 15 | supported | Cursor文档限定云端只运行命令hook，早期只读探索轮次不运行hook；命令hook退出2阻断，其他非零退出默认放行，而权限hook退出0但返回非法JSON或不合schema时阻断。 | 0e318bead0397315, fa6f7e13d5fde770, ec8006f4d56db729, 4be9907cbc7e220f, 9854aafbc96eccb0 |
| R20260919_DSH_INSTALL | 16 | supported | dsh Plugin Manager安装失败恢复package.json和lockfile，启用/删除等后续阶段可能留下部分修改；Host代码在工作区sandbox之外运行。 | 28b0c8e7ce70ec8f, cbaba3daf18e9872 |
| R20260919_OPENHANDS_PERSIST | 17 | supported | SDK的persist-before-publish变更先持久化事件再发布；非Event socket envelope另行区分。 | 63b129c66d038861, 3d5c6aca49e9e935 |
| R20260919_OPENHANDS_CONTAINER | 17 | supported | 9月新SDK/Agent Server增加每会话Docker容器模式，不代表OpenHands首次具有Docker执行支持。 | b1542125bd620588 |
| R20260919_MCP_STATELESS | 08 | supported | MCP 2026-07-28架构将协议定义为stateless，每次请求自包含并携带协议版本和能力；旧版session描述不能当作最新版。 | 6a0face011f6e4ba |
| R20260919_HARNESSDEV_HOLDOUT | 19,22,24 | supported | HarnessDev演化轨迹内分数用于开发反馈与版本选择；冻结后的630题SWE-Pro留出分数不展示给创建者。 | 8bbf916989f63628 |
| R20260919_HARNESSBANK_GATES | 22 | supported | HarnessBank v2先对采样训练子集做门禁，通过后才完整训练集评价并竞争进入基因库。 | cad5978c7b685332 |
| R20260919_SOLPI_MECHANISMS | 22 | supported | SoL-Pi保留动作合并、压缩时机、大观察句柄化与保留证据的读取压缩四类机制；效率得分与成本须一起评价。 | 16798d42729dd879 |
| R20260919_JIT_FROZEN | 23 | supported | JIT-Agent训练Harness生成器，不能由任务执行模型冻结推断整个系统没有参数训练。 | 822039fff8d6cf9b |
| R20260919_CODEX_PROBE | 14 | supported | 本地Codex0.142.5离线契约检查58/58符合预期，initialize握手未验证；未端到端验证取消或模型流。 | 50aa76ac3fc15f18, 8053a9c579428790 |

## 核心旧主张待补证的具体缺项

capture缺失不表示来源错误；有原文但尚未人工限定支撑范围，也不自动放行。

| Claim | 来源 | 缺项 |
|---|---|---|
| 无旧核心缺项 | — | — |

## Deferred研究线索（非核心）

| ID | 状态 | 原因 |
|---|---|---|
| R20260919_D36 | deferred / needs_review | 研究线索的编号/日期冲突未解决；未用于书稿承重事实。 |

## 产品49项URL登记映射

| URL | source ID | 元数据 |
|---|---|---|
| [原文/固定源码](https://cursor.com/blog/self-hosted-machines) | `ced5db4778ab3467` | verified |
| [原文/固定源码](https://cursor.com/changelog) | `b28194f531afc390` | verified |
| [原文/固定源码](https://developers.openai.com/api/docs/changelog) | `49e8d0577a5e1f9d` | verified |
| [原文/固定源码](https://developers.openai.com/api/docs/guides/agents-api/overview) | `3dffb20e2b3c17ea` | verified |
| [原文/固定源码](https://docs.anthropic.com/en/release-notes/api) | `05e927fb4ffc7d8a` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/README.md) | `9f328b1bcf9beaaf` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/action_execution_server.py) | `58b5b4b35e4531de` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/blob/9737f713616a1e452f822c2967f0e2c8bf2dc308/package.json) | `153a7e3297f6bf2a` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/blob/b50c60c6728e2ce123ccb6e125bee3eb88ac87d1/README.md) | `0ad2eb53dfd88031` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/releases/tag/1.0.0) | `593eb785cbd1c770` | verified |
| [原文/固定源码](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0) | `8dca4f3a034c8ee9` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py) | `c1204654070be025` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py#L34) | `3304a1117f090146` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/commit/2ab274897ac5e2c66b0ba17e9a6d39367b769876) | `57dfb03ee235bf45` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/commit/3ff6924d8564b3d47a22a6c7e71377a701ae014f) | `db6b4e467bf04c28` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/commit/94fca578b720df758b9bbf8a2639511b303c78e6) | `403c95c52f17f0c5` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.45.0) | `0cc1a94368acb2c3` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.48.0) | `bdfc8b695269b27e` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.1) | `a8ea31452a75e37a` | verified |
| [原文/固定源码](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2) | `a6576a5dcb7a1506` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/architecture.md) | `fe96ac496f19ca6b` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/tool-catalog.md) | `7fcdb3477e221f2a` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/packages/code-runtime/code-runtime-worker-thread/README.md) | `2ca3cdc88e5e693b` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md) | `dd269664988e8fc8` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-catalog.md) | `d9b48e75a6a25783` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md) | `15cb6b8ee5a22b58` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/cordis-host-runner/src/sandbox.ts#L1) | `7e758ff8f7a37588` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md) | `d4df8c06adb5f90d` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/75ed8da3e0c9103b3b2174b2981b7129e1fba21d) | `e64d0ca7e38f30f7` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/7c9bb5914cedec80e46197a8c894037fcfd12faf) | `3ddfdcccabfd1a1a` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/98b92b683c39fc60771daa774492105c2d3e8076) | `f4d8acc0591e6275` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/9b7a8ccc9fabc2e87386acf7f8b0741baf978022) | `9933523979a4a065` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/abd765a6001ff9d9c9772b8b407e0b7f18fe25ab) | `36648c12cf87bccb` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/d1521ea7838f19a78a9cca7b4a93622d301149bb) | `7e36460f8dbe5b10` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/e07f41d5fd8ca172287fda0f923b4d1f69c592f3) | `825cc91df1abcf72` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/ed32f57f88ef6bba983e30a0b434fe5d77e5773b) | `5f7669452471c409` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/commit/f99b06eaed81d6fe4fc64d44687450e18ef68a67) | `d2c3c0edb2bbd4b4` | verified |
| [原文/固定源码](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.1.6-alpha.2) | `e14fbfd2d9c10aaa` | verified |
| [原文/固定源码](https://github.com/openai/codex/blob/426fa8cdab4247e5623e9617d531f6917482b947/codex-rs/app-server-protocol/src/protocol/common.rs#L985) | `d760c886a379d662` | verified |
| [原文/固定源码](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1056) | `fb097fa5557b4778` | verified |
| [原文/固定源码](https://github.com/openai/codex/blob/be2951ea34f0d295ed0becf97079f92fa5f6950e/codex-rs/app-server-protocol/src/protocol/common.rs#L1941) | `fb097fa5557b4778` | verified |
| [原文/固定源码](https://github.com/openai/codex/releases/tag/python-v0.154.0) | `94bf6e711cee1f89` | verified |
| [原文/固定源码](https://github.com/openai/codex/releases/tag/rust-v0.152.0) | `3d4e408ad45e6552` | verified |
| [原文/固定源码](https://github.com/openai/codex/releases/tag/rust-v0.153.0) | `a8d513fb104884f5` | verified |
| [原文/固定源码](https://github.com/openai/codex/releases/tag/rust-v0.154.0) | `2ec7a45fef458a79` | verified |
| [原文/固定源码](https://github.com/openai/codex/releases/tag/rust-v0.155.1) | `028ae8f2158c4c5c` | verified |
| [原文/固定源码](https://learn.microsoft.com/en-us/agent-framework/concepts/harness) | `f87f611a4f82f81b` | verified |
| [原文/固定源码](https://www.anthropic.com/engineering/managed-agents) | `8537165d23c701b7` | verified |
| [原文/固定源码](https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness) | `b3d2576e2dbda990` | verified |

## 审计兼容与可复核入口

整合脚本--check检查本次输出与当前输入一致；现有audit_claim_ledger.validate()只读返回错误与警告，不写旧审计报告。真实needs_review仍应导致核心门禁失败，url_aliases按当前审计器核对。应按证据补足或明确范围，不把待审状态批量改为supported。
本次没有自动产生‘全事实通过’结论。元数据升级列表和证据类型可由JSONL字段复核；以下输入摘要固定本次运行实际读取的文件集合。

输入文件数：299；路径与hash排序后摘要：`fd15c4746d2f92e255b3fee11def0072d9e19e4d88299f06ad8ad4473c9259e9`。
capture异常：无。

## 现有审计器实际只读运行结果

调用audit_claim_ledger.validate()，未调用write_report()/main()。

执行状态：completed_read_only。
当前门禁结果：PASS；错误0条，警告0条。

具体错误（保留真实待审状态）：

- 无。

警告：

- 无。

当前审计器报告的未登记正文链接：

- 无。

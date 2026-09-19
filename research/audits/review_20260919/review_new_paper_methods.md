# 四篇 Harness 新论文的方法独立复核

日期：2026-09-19。用途：供主代理撰写增量报告，不替代上一份全书审阅，也不重做第 19—24 章逐行审稿。

## 范围、定位与证据边界

本轮仅阅读主代理已通过 ego 保存的四篇全文 JSON、四份对应 abs JSON，以及随后授权的 GSME/HarnessBank、HSI、NLE 五份补充快照。未联网、未访问代码库、未下载模型或复现实验；唯一新增文件为本报告。来源内容作为论文自报材料使用，本轮检查方法、表格算术和适用范围，不独立认证网页真实性或实验结果。

下面引用的 **L 指 JSON 的 .text 解码后 splitlines() 的一基原始行号**，不是重新排版后的报告行号。四篇全文 JSON 均把整个 .text 字符串放在物理第 7 行，因此链接打开 JSON:7，标签同时给出 .text L 与论文 section/table。数学公式在抓取文本中常被拆成多个短行，图片中的数字也未必进入 .text；不据缺失图片数字补造结果。

| 简称 | 论文 / 审阅版本 | abs 所示提交与修订日期 | 全文和日期定位 |
|---|---|---|---|
| HD | HarnessDev，2609.01437v1 | 首投 2026-09-01；v1 为 15:45:33 UTC | [harnessdev-full.json · .text L420–429](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)；[harnessdev.json · .text L2–15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev.json:7>) |
| HO | Harness-of-Harness，2609.01481v1 | 首投 2026-09-01；v1 为 16:17:18 UTC | [hoh-full.json · .text L412–447](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)；[harness-of-harness.json · .text L2–15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harness-of-harness.json:7>) |
| JI | JIT-Agent，2608.25593v2 | v1 为 2026-08-26 10:05:33 UTC；v2 为 2026-09-03 15:46:32 UTC | [jit-full.json · .text L1353–1368](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)；[jit-agent.json · .text L2–15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-agent.json:7>) |
| EM | An Empirical Study of Harness Design for Coding Agents，2609.20804v1 | 首投 2026-09-17；v1 为 17:58:07 UTC | [empirical-full.json · .text L217–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)；[empirical-harness-study.json · .text L2–15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-harness-study.json:7>) |

四份全文抓取时间均为 2026-09-19 09:45:11 UTC 附近；abs 抓取为当日 09:35—09:44 UTC。抓取日期、投稿日期和版本日期必须分开。尤其 JIT 的 v1 早于书中 8 月 27 日截面，但本次实际审阅的是 9 月 3 日 v2，不能把 v2 结果倒填进旧截面。

## 先纠正四种研究对象的混用

| 论文 | 实际改变什么 | 主要测量单位 | 对书中四层的关系 |
|---|---|---|---|
| HD | 可跨任务复用的 Harness 源代码，区分创建与后续修改 | 冻结 Harness × 执行模型 × 下游任务；进化另有整条版本轨迹 | 直接对应 L3；用于审查第 19、22、24 章的归因与晋级 |
| HO | 固定模型和基础 Harness 下的软件产物、计划与项目证据 | 同一项目的迭代产物 | 主要属于 L1 长任务适应；项目内持久状态不自动等于 L2 跨独立任务经验 |
| JI | 训练一个生成 Harness 的模型；部署时按任务生成代码并可更新经验库 | 生成器 × 执行模型 × 任务 × 生成配置/库版本 | 训练生成器属于 L4；部署生成对象属于 L3，当前任务使用涉及 L1，跨任务库涉及 L2 |
| EM | 人工控制的上下文、计划和动作接口配置 | 固定模型/任务下的条件配置对照 | 为 L3 选择提供证据；没有据此证明自动进化闭环有效 |

证据锚点：HD §3.1、§3.2 [harnessdev-full.json · .text L44–114](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)；HO §3/图3 [hoh-full.json · .text L43–47](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)；JI §4.1、§4.2 [jit-full.json · .text L1204–1349](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)；EM §2/§3.1 [empirical-full.json · .text L36–38](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L238–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。这是按对象与持续范围作的本报告分类，不是四篇作者共同宣称的统一框架。

## 一、HarnessDev：最值得补进“如何知道进化有效”

### 实验到底做了什么

创建阶段用六个 creator 模型、四领域五基准；每个 creator–benchmark 配置独立创建并评测三份 Harness，报告 avg@3。creator 有弱种子和 1—3 个开发样例，交付后冻结。Self-Eval 让创建者模型执行自己写出的 Harness；Unified-Eval 固定 Gemini 3.1 Pro 作执行者。开发环境并不完全相同：GPT-5.5 使用 Codex，其余用 Claude Code。§3.2、§4.1：[harnessdev-full.json · .text L286–316](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L420–429](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

进化阶段有五条 self-runtime 与四条 fixed-Gemini 轨迹，累计 73 个正式版本。每个候选同一 commit 必须完成 SWE-Pro 100 题和 Terminal-Bench 89 题的一对反馈评测；最多十次正式后续配对评测，两次之间可作最多两次固定小样本探针。结束后才对正式版本运行不向创建者反馈的 SWE-Pro 630 题。§3.2、§4.3：[harnessdev-full.json · .text L297–316](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L893–898](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

短引文：**“one trajectory per creator–runtime cell”**（5 词；§6.1，[harnessdev-full.json · .text L1207–1209](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)）。创建阶段三份独立产物与进化阶段单条轨迹不能互相替代。

### 五条最有用的新结论

1. **把“会生成 Harness”与“会维护并改好 Harness”拆成不同能力。** 从种子写出可运行系统并不说明它能依据反馈持续修好系统；创建阶段和进化阶段的实验单位、初始条件与数据访问均不同。第 19 章可据此把“生成候选”与“持续改善”分开定义，第 22 章增加创建、维护、选择三种失败分类。[harnessdev-full.json · .text L108–114](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L286–316](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

2. **反馈集上涨不是最终泛化的可靠代理。** self-runtime 五条最终版本在留出集的增益为 1.43—4.44 个百分点，均值 3.11；固定 Gemini 的四条迁移进化轨迹中只有 Opus 留出集改善，其余三条下降。64 次可比版本切换中，反馈与留出方向一致仅 34 次，9 个最终声明版本仅 2 个碰巧也是留出最优。这些是本次轨迹的描述统计，正适合第 24 章说明为什么“看见分数再选最好”需要独立确认。表6、§4.3：[harnessdev-full.json · .text L933–1053](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1156–1171](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

3. **机制存在、代码可达、实际触发需要分别验收。** 18 个代码 Harness 中 11 个声明 State 类，但只有一个暴露保存接口、一个实现周期 checkpoint；26,679 条记录轨迹里没有 checkpoint 事件。108 个组件实例中 72 个触发、18 个证据不全、18 个未观察到。可给第 22 章 activation 门一个实证理由，但不能把“未触发”直接判成机制永无价值。§4.2：[harnessdev-full.json · .text L835–843](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

4. **换执行模型是兼容性试验，不是 Harness 天然可移植的证明。** 同一 Opus 创建的 Harness 在 SWE-Pro 的均分从 self 的 69.3 降到固定 Gemini 的 33.0；反过来 Qwen 在部分任务提高。协议能运行，并不保证终止规则、步数预算和工具消息配合还有效。第 23 章的 Model×Harness 应报告条件差值，不应给 Harness 打脱离执行模型的绝对分。表3/4、§4.2：[harnessdev-full.json · .text L466–487](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L645–668](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L844–854](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

5. **执行 token 差异很大，质量与 token 并不单调。** MLE-bench 中 GPT-5.5 产物的报告成绩为 19.1、执行 token 为 29.3M，DeepSeek 对应为 19.6、208.4M。这里是每份 Harness 在该基准上的执行用量口径，不是每任务 29.3M/208.4M，也不是全生命周期总成本。第 19 章可用它要求效用与资源并报。图9：[harnessdev-full.json · .text L1545–1551](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)；表3说明：[harnessdev-full.json · .text L626](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

### 五条范围限制

1. **进化没有足够独立重复支撑模型间总体排名。** §6.1 明确每个 creator–runtime cell 只有一条进化轨迹，并有一个未完成主运行配置；尽管文中报告了同 commit 的噪声带，不能将局部重复检查当成多条独立演化轨迹的置信区间。留出仅覆盖 SWE-Pro，不能扩写成跨四领域进化泛化。[harnessdev-full.json · .text L1151–1154](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1205–1209](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

2. **公开人类工程系统是异质参照，不能归因成“AI 造 Harness 超越人类”。** 参照绑定不同执行模型，其中三个分数来自外部报告且未重跑；写作/MLE 接近或超过所选系统，不能证明同执行模型、同预算下生成方式更优。avg@3 的重复也不能消除 creator 开发环境不同的混杂。[harnessdev-full.json · .text L429](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L795–798](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1532–1544](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

3. **execution tokens 明确排除 creator、judge、诊断 probe。** §3.5 排除创建/修改 token，附录 B.4 另明确排除 judge/probe。因此论文的执行效率不能直接支持“进化平台整体省钱”。任务运行内部已记录的重试可能进入 runtime usage，但未完成评测、修复重跑和失败尝试是否全部累计，没有可据本快照确认的端到端成本账。[harnessdev-full.json · .text L409–414](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1547–1551](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

4. **正式轨迹是完整有效评测对的条件样本。** 协议合并同 commit 的基础设施修复，并排除 probes、partial legs、stopped runs 与 invalid instances。这可以作为研究评分协议，但必须另报未完成率与成本，不能直接当生产全分母成功率。“held-out”明定为创建者开发回路未见，并非模型预训练未见；反馈/留出都来自同一公开 SWE-Pro split。[harnessdev-full.json · .text L297–316](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

5. **未触发违规不等于安全认证，代码发布状态亦未核验。** §3.4 是作者对本次代码与记录的审计零发现；伦理段明确容器用于复现而非强安全隔离。附录 C 还用将来时说明种子、审计脚本与拆分将随基准发布。不能把论文的“可检查产物”写成我们已下载、安装和复现成功。[harnessdev-full.json · .text L405–407](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1215–1217](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)、[harnessdev-full.json · .text L1575](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

**落入第 19—24 章的建议：** 第 19 章补“生成质量、维护质量、选择质量”三指标；第 22 章以触发事件而非代码存在证明激活；第 23 章加入固定执行模型的迁移反例；第 24 章区分反馈集最优、预先声明版本和事后留出最优。不要把 3.11 个百分点升级成普适收益。

## 二、Harness-of-Harness：长任务治理案例，不是基础 Harness 自改证据

### 实验到底做了什么

固定同一套模型、基础 Harness、角色定义和运行策略，依次调用 Planner、Developer、QA；Developer 独占产物写权限，QA 检查冻结只读候选，外部基准评价不回传开发闭环。主比较用 Codex+GPT-5.5、OpenCode+DeepSeek-V4-Pro、Pi+MiniMax-M3，分别比较 Vanilla 与 HoH 三轮。GameCraft 抽取 45 题，FrontierSWE 15 题；正文同时报告 ProgramBench，但所读协议附录没有同等完整的样本规模/执行清单。§3、§4.1、附录 B：[hoh-full.json · .text L43–47](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L206–208](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L245–291](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L412–447](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L2480–2499](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

短引文：**“one valid run”**（3 词；附录 B.2，[hoh-full.json · .text L2387](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)）。主报告的任务—条件结果不是同一题重复采样的均值。

### 五条最有用的新结论

1. **长期项目可通过产物状态与证据状态两条通道延续，而不修改基础 Harness。** 计划从当前代码和以前的执行证据生成；证据不足被记成缺口，不能由 Developer 自报成功覆盖。对第 20 章是可操作的长任务收敛实例，对第 21 章是项目记忆的设计启发，但还不是跨独立任务收益实证。§3.3、§3.4：[hoh-full.json · .text L83–196](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L270–291](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

2. **有比“一轮对三轮”更强的对照，但只限特定实验。** GameCraft/Codex 下，同为三次开发 pass，HoH 得 71.52、Vanilla Continuation 得 58.24，差 13.28 分。更有价值的是 HoH 两轮得 64.84、5.67M token，超过 Vanilla 三轮的 58.24、6.33M；按表中数差 6.60 分、token 少约 10.43%。可支持该配置下组织方式的效益，不必只诉诸增加轮数。表2：[hoh-full.json · .text L789–804](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

3. **计划更新、证据回传和产物延续都有条件消融证据。** 在 GameCraft 的 45 题、Codex+GPT-5.5、三轮条件下，冻结计划、去证据、每轮重建相对完整系统分别降低 8.13、6.28、7.85 分；每轮重建还增加 token。适合第 20—21 章说明为何“修复—验证—携带已验证状态”应联合设计。它不是三机制在所有模型上的独立普遍效应。表3：[hoh-full.json · .text L812–850](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

4. **更多轮数可能继续改善，但不单调。** 固定 15 题的十轮实验，最优点在第九轮而非第十轮；70 轮 FPS 案例到截点有 81 个问题、65 个关闭、16 个未解决，17 个问题曾重新打开。第 20、24 章可以据此把重开率、未决项和回退能力列为进度指标，而不是按累计关闭数讲故事。§4.3、§5.2：[hoh-full.json · .text L778–786](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L879–885](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

5. **将日常 QA 与最终评分隔离，能保留修复反馈而不直接暴露隐藏答案。** 开发侧接收本地行为与 QA 证据，隐藏测试、私有评分规则、分数及裁判理由不进入后续迭代；中间版本只在完整运行后评分，不按基准分数选最终产物。第 24 章可借鉴这种权限设计，但其效果仍是作者报告的实施，不是本轮的独立安全验证。附录 A.5/B.2：[hoh-full.json · .text L2330–2387](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

### 五条范围限制

1. **不能把同项目迭代写成“运行时学会持续自我进化”。** 三个角色仍为同一模型的独立调用；角色权限分离降低自报验收问题，但不带来模型错误的统计独立性。基础模型和 Harness 在运行内固定，多配置改善也不是把同一生成 Harness 换执行者的直接迁移试验。[hoh-full.json · .text L47](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L81](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L204–208](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

2. **平均提升 52.25% 与最大 82.86% 不宜原样并列使用。** 摘要称相对增益，不是百分点。本轮按正文九个聚合格的四舍五入值计算，以 FrontierSWE mean reward 为其指标，平均相对增益约 52.28%，接近摘要 52.25%；但 Pi 的 reward 从 0.26 到 0.55，算得约 111.54%，不是最大 82.86%。82.86% 恰与另一个指标 Dominance 从 35% 到 64%的相对提升吻合。也就是说，摘要的平均/最大很可能混用了指标，或缺少汇总说明；目前不能视作同一组量的干净摘要。优先写可复算单格，要求作者/主代理澄清总体口径。[hoh-full.json · .text L18](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L659–756](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L762–766](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

3. **单次生成与任务 bootstrap 的不确定性范围不同。** 每个任务—条件只有一条有效运行；基础设施/传输错误的尝试被替换，非额外重复。GameCraft 95% 区间来自 20,000 次按任务重采样，不是重新生成 20,000 次，更不覆盖同题运行随机性。模型生成没有统一可复现 seed。70 轮 FPS 是单案例，允许人恢复网络/API，并不是无人运维或产品验收全部通过。[hoh-full.json · .text L2383–2437](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L3203–3205](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L863–885](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

4. **pass 相同不等于 token、模型调用数或美元预算相同。** 三 pass 时 HoH 的 8.41M 比 Vanilla 的 6.33M 高约 32.86%；每轮还分三个角色。token 定义是 coding-harness 模型调用的输入/输出，不含 benchmark evaluation，缓存计数随供应商不同。按角色使用同一 Harness 的设计，口径应涵盖经过它调用的 Planner/Developer/QA，但没有逐角色和失败替换尝试的完整拆账。另附录 C.5 FrontierSWE 表24的 HoH@1—3 数值会下降，未明确这些列是单轮增量还是累计；不可据其直接宣称三轮总成本更低。[hoh-full.json · .text L793–804](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L3207–3279](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L4759–4773](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

5. **评价含量与可复现材料有限。** GameCraft 分数混合运行成功门与玩法/美术等评分维度，不等于生产软件全部正确；Dominance 依赖比较池，三轮表的 12 配置池与十轮图的 11 checkpoint 池不同，不能直接拼同一曲线。附录公开材料说明排除了原始运行产物、任务数据等；程序重建部分的详细协议也较薄。没有本地拉取代码和数据验证，不能宣称已完全复现。[hoh-full.json · .text L445–447](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L784–786](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L3088–3205](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L3319–3506](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)、[hoh-full.json · .text L3562–3564](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>)。

**落入第 19—24 章的建议：** 第 19 章先按“改变的软件是什么”分类；第 20 章加入有界增量、候选冻结与重开问题；第 21 章注明项目内证据积累与跨任务学习的区别；第 24 章使用评价隔离实例和匹配开发 pass 的对照。不要将摘要相对增益用作 L3 自改收益。

## 三、JIT-Agent：训练生成器、任务时生成与跨任务库要分开归因

### 实验到底做了什么

以 Qwen3.6-27B 训练 Harness 生成器，底层任务执行模型另行冻结。设计空间包含记忆、计划、动作和能力编排四模块，13 个手写协议化种子。训练依次为教师生成与 SFT/DPO、最多两步成功修复轨迹的监督、以奖励/时延/成本三个通道优化的 Evo-GDPO。部署时生成器参数冻结。§3/§4.1：[jit-full.json · .text L494–556](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L621–795](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L798–1026](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1204–1211](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

静态模式可并行生成 N 个 Harness，选一个执行；流式模式将已完成任务的环境反馈用于经验库更新，使后续任务可检索新参考。主表为九基准、两个重点 backbone；受控 Harness 比较为两个 backbone×三个基准；跨族补充为六个 backbone×四基准，其中 DeepSearchQA 为 100 题子集、其余三个各 50 题。§4.2/§5：[jit-full.json · .text L1213–1349](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1353–1368](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1434–1464](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1572–1595](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

短引文：**“executes only the selected harness”**（5 词；§4.2，[jit-full.json · .text L1219–1221](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)）。不增加环境 rollout 数，不等于不增加生成、选择和修复成本。

### 五条最有用的新结论

1. **可把“构造执行环境”作为模型训练目标。** 生成器学习输出满足协议的可执行模块，而不是给执行者添加一段自然语言建议。这为第 23 章提供不同于“训练任务执行模型”的 L4 路线：训练的是设计/修复 Harness 的模型，下游执行模型可保持不变。因此不能把本论文整体归为纯模型外、无参数更新的自进化。[jit-full.json · .text L78–104](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L623–652](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1362–1364](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

2. **失败生成也可以构成受控训练数据，但应保留失败计分。** 第二阶段收集诊断到修复的轨迹，只保留两轮内恢复可执行者；第三阶段对仍无效的候选赋最低任务奖励，修复时延和成本继续计入。它给第 20、23、24 章一个具体方法：把编译/接口失败变为有界修复监督，同时不让无效候选从评价账消失。[jit-full.json · .text L798–954](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1011–1026](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

3. **与同 backbone 默认配置的改善，比跨模型排行榜更有解释力。** 主表18个匹配模型—基准组合均改善；GLM 的九指标平均由约74.1到81.8，DeepSeek Flash由约66.7到75.5。购物约束匹配率从59.1到83.9是24.8个百分点；旅行综合约束分从62.8到83.0应称增加20.2分，不要一律写“提升20.2%”。九指标包含准确率、F1与评分，平均分是作者的描述性汇总，不是单一任务成功率。表2：[jit-full.json · .text L1354–1360](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1377–1432](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

4. **对照结果呈现质量—成本取舍，不能压成全胜。** 固定 backbone 的六个比较中 JIT 四个性能第一，另两个较最好者低3.1、3.9分；表3的六个 token/API cost 都最低。例：DeepSeek Flash的AgentIF为63.8分、0.097美元，Claude Code为66.9、0.114，明确是省钱但性能略低。第 19、22 章应保留这种 Pareto 表述，尤其成本总口径尚待澄清。表3、§5.3/5.4：[jit-full.json · .text L1451–1510](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1545–1570](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

5. **跨任务积累可以通过 Harness 库而非模型在线更新实现。** 流式模式在完成当前任务后按协议更新库，下一任务再检索；附录图6称三条任务流最终累计准确率高于静态模式，成本/工具调用并非统一增加。第21章可引入“程序化配置经验”的新对象，但应将库版本、任务顺序与参数版本一并记录。正文说明部署参数不变，不代表整套系统状态不变。[jit-full.json · .text L1204–1211](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1223–1349](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L2081–2089](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

### 五条范围限制

1. **训练和评测的数据隔离尚不能由现有描述完整复核。** 训练任务来自已有 agentic benchmarks及合成任务；快照提供三阶段算法，却未找到足够明确的逐数据集数量、去重/同源隔离清单、训练/验证/测试划分、教师及完整超参数和主表采用的候选 N/选择器协议。不能直接称其九基准结果为“训练未见分布上的普遍收益”。这是材料不足，不等于已经证明污染。[jit-full.json · .text L648–652](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L958–1013](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1219–1221](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1353–1368](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

2. **跨模型适配收益不等于冻结产物的直接迁移。** 六模型24个 ReAct 对照说明同一生成体系能在不同 backbone 上产出有用配置，但没有像 HD 那样明确冻结某份生成 Harness，然后只替换执行模型的交叉矩阵。因此 JIT 的积极结果与 HD 的迁移失败并不矛盾，所测对象不同。[jit-full.json · .text L1572–1595](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)；对照 HD §4.2 [harnessdev-full.json · .text L844–854](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>)。

3. **API cost/token 是否含生成器、选择器、验证器和全部重试不清。** 方法明确第三阶段效率度量包含有界修复；这不能自动证明表3每任务 API cost 已包含生成 N 个候选、选择、生成器推理、所有验证/失败尝试。更不包括已证明摊销的训练成本。不能把表中约36%的平均 API 节省，直接改写为企业总成本降低36%。[jit-full.json · .text L1013–1026](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1219–1221](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1434–1435](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1476–1510](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

4. **算法中的 repeated-rollout 均值不是最终实验重复次数。** 训练定义涉及同 seed、重复 rollout，但主结果没有相应给出每格独立生成/执行次数、置信区间及配对显著性方法。流式图的阴影只定义为局部变化，不能当成置信区间；任务顺序及多次打乱后的稳定性亦未见清楚报告。第24章只能称“作者报告的改善”，不能给18/18或24/24附加未经提供的显著性。[jit-full.json · .text L650–769](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1013–1026](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1370–1432](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L2087–2089](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。

5. **协议可执行不等于生产安全，亦未逐组件证明三阶段必要性。** 论文结果支持整个训练/生成体系，不足以分别确认 SFT、修复学习和 Evo-GDPO 的因果贡献；也没有本轮可核验的权限越界、恶意候选或多租户安全结果。正文有代码链接，但本轮没有读取目标仓库、模型权重或发布包；可用性保持未验证。[jit-full.json · .text L78–104](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L556–619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L1602–1604](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)、[jit-full.json · .text L16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>)。快照未见独立 limitations 小节，以上是本报告从方法披露范围推导的限制，不冒充作者原文承认。

**落入第 19—24 章的建议：** 第19章扩展“创建者模型、执行模型、评价器、经验库”身份与版本；第21章放流式经验库；第22章放协议化生成与修复；第23章放训练生成器的跨层路线；第24章要求数据拆分和完整成本账。不要把“执行模型冻结”偷换成“系统没有训练”。

## 四、Empirical Harness Study：最适合补充条件消融，不能推出通用组件排序

### 实验到底做了什么

固定 ReAct 执行循环、权限支持和卡死检测，比较四模型：Nemotron-3的30B/120B/550B，以及Mistral-Medium-3.5-128B。SWE-Bench Verified为500题，Terminal-Bench 2.1为89题；模型本地BF16/SGLang服务，temperature=0，最多300步。上下文策略T0—T4分别为不管理、删旧输出、删旧输出加回查、摘要、先删旧输出再按需摘要且可回查。§2/§3.1：[empirical-full.json · .text L36–38](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L95–128](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L217–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

上下文扫32k/64k/96k/128k；计划开关与bash-only只在T4/128k做。总格数为5×4×4×2＋2×4×2＝176，不是上下文×计划×工具全部组合的全因子实验。计划组件包括指令、首轮提醒、持续注入与update_plan工具；动作接口则同时改变工具、提示、文件状态跟踪和编辑后检查。[empirical-full.json · .text L60–75](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L238–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

短引文：**“Planning and the action space are evaluated only under T4/128k.”**（10词；§3.1，[empirical-full.json · .text L242](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)）。

### 五条最有用的新结论

1. **上下文管理的收益应按窗口约束解释。** 四模型平均、管理策略相对T0的SWE成功率差，从32k的35.7个百分点降到128k的2.7；Terminal从9.5降到2.8。所有管理策略在报告格子里没有overflow失败，T0则随窗口变大而减少。第22章可以把“更聪明地记忆”与“避免被硬窗口截停”拆成两个机制；这组数据更直接支持后者。[empirical-full.json · .text L309–340](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

2. **回查能力未激活，不能据此证明所有记忆或检索无效。** T2相对T1的32个匹配格，15胜14负3平，平均差−0.36个百分点；64个T2/T4配置中36个从未调用recall_event。最有用的工程含义是先观测需要、发现、触发和返回效果，再决定保留这项机制；可直接补进第21、22章的activation和边际成本讨论。[empirical-full.json · .text L350–379](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L1212–1226](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

3. **计划改变终止行为，未必提高强模型成功率。** 在T4/128k，30B在SWE从无计划13.6%到有计划25.2%，增加11.6个百分点，但成本更高。550B则从67.8%到65.8%，下降2个百分点，折算成本从3.31到2.33美元，约低30%；轨迹分析显示主要减少后期反复验证。第20章应写成“按提前放弃/过度验证诊断选计划支架”，而不是总给模型更多计划。表3、§3.2/§4：[empirical-full.json · .text L275–277](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L381–399](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L575–585](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

4. **动作接口偏好随模型和任务反转。** T4/128k下，550B在SWE用bash-only由65.8%到69.4%，增加3.6个百分点且折算成本低；Mistral在SWE却从完整工具68.6%降至bash-only45.4%，Terminal反向由37.08%升至43.82%。这能给第22章“profile而非全局最优”提供具体反例；不是“更大模型都该去掉工具”。表3/4、动作分析：[empirical-full.json · .text L275–277](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L306–308](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L504–557](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

5. **匹配任务与多重比较校正比只报总体均分更可复核。** 作者按每基准的三类比较，使用任务配对的双侧exact McNemar，并以BH控制FDR=0.05，表中区分显著格；Terminal不少差异未达门槛。第24章可借其报告格式，但不应把这种“检测差异”的检验等同于非劣检验。[empirical-full.json · .text L238–253](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L617–619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

### 五条范围限制

1. **planning和动作接口结论只适用于T4/128k，未覆盖所有budget。** 32k—128k四档只用于上下文策略；也未把计划关、bash-only同时全组合起来。不能说176设置已经验证所有组件交互，更不能推导128k观察的成本收益在小窗口仍成立。作者limitations明确承认需全因子研究。[empirical-full.json · .text L238–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

2. **每题每设置一次；temperature=0不等于重复稳定性证据。** 任务配对检验度量本次固定题集的结果差异，不估计多次轨迹生成的波动。Terminal只有89题，多格未显著；未显著不等于等效或非劣。[empirical-full.json · .text L230–244](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

3. **干预是具体实现组合，不能将结果归给单一抽象概念。** 去计划删除整套提示/状态/工具；bash-only也改变文件状态跟踪与自动诊断。T4在soft阈值先删旧输出，T1—T3使用hard阈值，不是只改变模块开关；T4更省不能单独证明摘要算法或“回查”更好。[empirical-full.json · .text L62–75](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L119–128](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

4. **模型规模只是有缺陷的能力代理。** 三种规模属于同族，跨族只有一个模型；训练、工具熟悉度与shell能力也在变。任务仅限代码/终端，SWE部分为Python；不能据此泛化到浏览器、经营分析、真实企业权限或全部未来模型。不开放搜索降低查到修复答案的路径，但不能证明预训练不存在污染。[empirical-full.json · .text L75](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L221–225](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L619](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

5. **成本是价格折算，机制解释是带误差的标注。** 论文将本地推理token按OpenRouter标价折算，并非观测到的部署账单；没有充分拆清摘要调用、事后GPT-5.5轨迹judge、重试和环境成本的总账，不能叫全生命周期TCO。200条轨迹的人类核验分成三个不重叠子集，每条由其中一位标注者处理；高人机一致率不是“三人对每条达成一致”，也不把轨迹阶段标签升级为因果证明。[empirical-full.json · .text L221–236](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L97–109](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)、[empirical-full.json · .text L1057–1077](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-full.json:7>)。

**落入第 19—24 章的建议：** 第19章把任务预算纳入效用前提；第20章把停止/卡死行为作为机制指标；第21章区分存储、召回与实际激活；第22章引入按模型×任务×预算的条件消融；第24章补配对结果、失败分母与多重检验。不要依据这篇就写“计划已经不重要”“记忆无用”或“bash优于结构化工具”。

## 五、跨论文成本和统计口径对照

| 项目 | HD | HO | JI | EM |
|---|---|---|---|---|
| 执行者/创建者 | 创建与执行角色明确分开 | 角色调用相同模型/Harness，不单独训练创建者 | 27B生成器与backbone分开 | 固定执行模型，人工改变配置 |
| 重复单位 | 创建独立产物3份；进化每配置1轨迹 | 每任务—条件1次有效运行 | 训练定义有重复rollout；最终格子重复数未交代清楚 | 每任务—配置1次 |
| 报告成本 | 任务执行token；明确排除creator/judge/probe | Harness模型调用token；排除benchmark评价，缓存依供应商 | 表示每题token/API美元；生成/选择全成本边界待核 | 本地token按API价格折算 |
| 失败/重试 | 只完整有效配对进正式轨迹；成本全计不明 | 基础设施失败替换；被替换成本是否保留不明 | 训练阶段无效候选最低奖励、保留修复成本；主表全口径不明 | 卡死终止明确；基础设施失败与重试总账未充分说明 |
| 不确定性 | 进化无多轨迹总体推断；有局部噪声检查 | 任务bootstrap；不是重复生成区间 | 最终均分无明确CI；流式阴影是局部变化 | 配对McNemar＋BH；不支持从“不显著”直接说非劣 |
| 可迁移性 | 明确替换固定产物执行模型，出现退化 | 三个整体配置可用；未做全部交叉 | 多backbone下生成方案有收益；未证同一产物直接迁移 | 同实现组件在不同模型/任务下效应变化 |

上述各项的原文定位已列于四篇设置及限制条目。统一写法应为“在什么条件、哪个分母、用什么资源口径下观察到何种差值”。不能把执行token、供应商计数、API折算价和训练加部署总成本放进一张共同成本排行榜。

## 六、代码和 Hugging Face 可用性：目前真正知道什么

| 材料 | 这些快照能支持什么 | 不能支持什么 |
|---|---|---|
| HD附录C | 论文表示将发布种子、审计脚本和拆分；[harnessdev-full.json · .text L1575](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessdev-full.json:7>) | 发布已完成、可安装、可跑完评测 |
| HO附录B.9 | 论文描述随投稿的匿名实现包及其排除项；[hoh-full.json · .text L3562–3564](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hoh-full.json:7>) | 外部读者已有完整任务数据、原始轨迹或可复现实验包 |
| JI标题区 | 有作者给出的GitHub代码地址；[jit-full.json · .text L16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/jit-full.json:7>) | 仓库当前非空、权重已发布、许可合适、安装验证成功 |
| EM的abs/full | 当前快照没有确认作者代码仓库内容 | 不能因arXiv出现HF入口便称代码在HF可用 |

特别核查：empirical-harness-study.json 的原始 JSON 第194行指向 HF 通用介绍页，第206行指向 Spaces 通用文档，而非该论文代码/权重仓库。[原始JSON:194](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-harness-study.json:194>)、[原始JSON:206](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/empirical-harness-study.json:206>)。它们是页面通用服务链接。本轮未访问任何HF或GitHub目标，准确状态是“代码可用性未验证”，不是“已公开可用”，也不是“代码一定不存在”。

## 七、给主代理的合并建议与复核记录

最值得写入增量报告的不是“又有四篇证明Harness重要”，而是四种可区分的证据：HD解释进化选择为何容易失真；HO给出长任务证据治理与有界迭代；JI展示训练生成器与经验库的跨层设计；EM给出模型、任务、预算共同决定组件价值的条件消融。

合并时优先保留五个限定：百分点/评分点/相对增益分开；创建者、执行者和judge的资源分开；独立生成、同任务重跑与任务bootstrap分开；生成器能适配新模型与同一Harness直接迁移分开；论文给出地址与代码实际可复现分开。把它们融入第19章证据模板、第22章消融方法和第24章实验报告字段，无需再次扩写一组抽象原则。

本轮实际阅读范围：HD的§3—4、§6.1及附录B—D相关配置；HO的§3—5、附录A.5、B.1—B.7/B.9和C.5；JI的§3—5、结论及附录B流式评估；EM的§2—4、limitations及附录9.2/9.6。公式使用解码文本，未观看图像或执行作者代码；图中的未抽取数据没有补填。HF可用性只检查授权快照中的链接与文字。

正文短英文引文按空白分词计：HD 5词、HO 3词、JI 5词、EM 10词；补充HarnessBank 8词、NLE 5词，各来源合计均未超过25词。其余为本报告中文转述、数据核算、书目/接口名及分析。HD原文的creator–runtime为一个连写词。

交付前核对了157处.text行号引用，均在对应快照范围内；13份授权快照的文本SHA-256全部与JSON保存值一致。六段英文短引文均逐字匹配原文；四篇各有五条结论、五条限制。原始四篇全文的校验记录如下：

| 文件 | .text行数 | SHA-256 |
|---|---:|---|
| harnessdev-full.json | 2,663 | cd857c021a72c38a44f5b93f8ad100d993ba7d2a8ce0b6919dffff9983f9875f |
| hoh-full.json | 5,037 | d65ec9d803a7acf14ace82ebe22346996fec13ca94ff69043cce8e0e9d285581 |
| jit-full.json | 2,134 | e9d7fbc1458c42695bd540f32f5ff2650217dbc48fee33660c096a9ce17ee2f9 |
| empirical-full.json | 1,357 | 66108fe83d9fb2cdb4775abae3666855f3ca9706b0a62678a05fd021bf467286 |

定位复核可在内存中完成：用JSON解析器取得.text，按splitlines()生成原始行数组，以报告一基行号减1索引即可。不需要产生新的抽取文件，也不应把JSON物理第7行误报成论文第7行。

## 附加核正一：GSME的v1与HarnessBank的v2不能混用

用户追加授权后，核对了三份主代理快照：版本固定的v1摘要、当前v2摘要、v2全文。日期与题名能够明确对应：

| 对象 | 版本和日期 | 在材料中的实质定位 |
|---|---|---|
| GSME旧题名 | 2607.13683v1，2026-07-15 10:26:26 UTC | 语义质量—多样性archive，以修改位置×失败病理组织；强调提案与确定性计量分离。[harnessbank-v1.json · .text L2–16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v1.json:7>) |
| HarnessBank当前题名 | 2607.13683v2，2026-07-30 08:41:14 UTC | 显式任务Agent/evolver/确定性评价器/基因库；提出重构、跨单元重组和门控筛选。[gsme-current.json · .text L2–16](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/gsme-current.json:7>)、[harnessbank-v2-full.json · .text L243–247](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>) |

**这不是仅改书目标题。** v2仍保留提案与计量分离、位置×病理的语义索引，旧书这一核心解释没有因此全盘失效；但叙述重心扩展为保存与重组多种机制的基因库，并突出先小样本筛选、再全训练集评价的流程。摘要/引言明确列出有效性、激活、配对显著性与增益四类检查；§3.3又将组合条件组织成门禁逻辑，报告时宜说明所检查的条件，不争论“三门/四门”的名目数量。[harnessbank-v2-full.json · .text L27–51](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)、[harnessbank-v2-full.json · .text L245–247](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)、[harnessbank-v2-full.json · .text L667–708](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)。

**结果范围也变了，不能只改名后沿用旧数字。** v1摘要称封存测试增益9—15.5个百分点、保留86%—147%训练增益；v2主表包含七个领域，但SWE-bench测试仅26题，作者将约5.1个百分点改善标为初步结果，z=0.78，未通过其门槛。其余六个留出结果作者报告通过门槛，主表增益约9.2—15.4个百分点。v2里的“5.1%—15.4%”从表中是成功率之差，写书时应改写为百分点，不能解释为相对增长率。[harnessbank-v1.json · .text L5](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v1.json:7>)、[harnessbank-v2-full.json · .text L1015–1021](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)、[harnessbank-v2-full.json · .text L1024–1076](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)、[harnessbank-v2-full.json · .text L1077–1253](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)、[harnessbank-v2-full.json · .text L1326–1387](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)。主表按三次尝试平均Pass@1，与至少一次成功的Pass@3也不能混用。

**代码状态仍只是一项计划。** v2准确短引文为 **“Our code will be publicly available upon acceptance.”**（8词；[harnessbank-v2-full.json · .text L15](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/harnessbank-v2-full.json:7>)）。不能把它改成代码现已公开、通过独立复现。本轮也没有访问相关仓库。

对旧书与账本的影响：沿用上轮已核对的定位，sources.jsonl:6登记的是v1旧题名、版本字段却为v2；第19章:59、第22章:43及C019仍用GSME解释。主代理有两个合规选择：保留历史GSME叙述并明确钉住v1；或按v2更新题名、方法表述、逐条证据及数字边界。不可把v1文字和v2元数据混成同一份证据；v2早于旧书8月27日资料截面，也不宜把此错配解释为本次9月才发生的新变化。此处沿用上轮账本定位，没有重读或修改旧sources。

可供正文采用的中文句式：

> 这项工作在7月15日的v1以GSME描述语义质量—多样性搜索，7月30日的v2改为HarnessBank，进一步突出基因库、机制重组与分阶段筛选。本书采用v2：作者在六个留出领域报告通过其统计门槛的改善；SWE-bench因测试仅26题仍属初步信号。结果说明在特定模型和任务上可验证地选择变更，不构成所有候选必然可信或跨模型通用的保证。

最后一句是本报告对统计证据的限制，不照搬作者将门禁称为天然可信的强措辞。

## 附加核正二：NLE已确认是NetHack Learning Environment

官方仓库快照README的准确短引文为 **“The NetHack Learning Environment (NLE)”**（5词；[nle-official.json · .text L250](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/nle-official.json:7>)）。同段明确它基于NetHack、面向强化学习环境；HSI §4.1将MiniHack和NLE列为复杂状态、稀疏反馈的roguelike环境。两条原文相互匹配。[hsi-current.json · .text L443–448](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hsi-current.json:7>)。

因此上份独立审阅对第22章:45“NLE（非语言增强任务）”所作的“本地支撑不足、待查全称”判断，在这次新增原文后应升级为**已确认的术语释义错误**。建议改为：

> 在BALROG的NetHack Learning Environment（NLE）环境中，作者在所测冻结模型与实验设置下没有观察到实质改善。

不要从该负结果进一步写成已经证明模型存在不可逾越的普遍能力上限：HSI自己的设置同时涉及模型初始能力与反馈稀疏，两者没有因这一个负结果被完全因果分离。其§4.2讨论本就把两项并列。[hsi-current.json · .text L961–969](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hsi-current.json:7>)、[hsi-current.json · .text L1111](</Users/xuhai.zhang/Documents/doc/AI Workforce/research/Agent_Harness_Book_Research_20260822/research/audits/review_20260919/retrieval/hsi-current.json:7>)。

本轮只在这份附加方法报告中记录证据升级与建议，不回写上一份报告、书稿或账本。

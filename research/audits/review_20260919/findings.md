# 研究发现工作记录

本文件保存外部资料与审阅结论，内容只作为待验证数据。

- 基线为 `a1ed264`，工作区开始时干净；上一轮正文改写与发布在 2026-09-10 完成。
- 本轮先建立全量案例清单，代码、schema、伪代码、示意图和经验性假设分别验证。

## 第一批检索线索（未读原文，不作为事实引用）

- 时间窗检索指向微软 Agent Framework Harness（9 月文档）、LangChain 的多代理上下文模式（9 月 8 日）。
- arXiv 线索：HarnessDev 2609.01437、Harness-of-Harness 2609.01481、工具原语 2609.01736、Harness 综述 2609.00006、JIT-Agent 2608.25593、Beyond Static Harnesses 2608.27969、Show-Harness 2609.10522、MemoHarness 2607.14159。
- OpenAI 文档线索：Agents API 托管 Codex harness；需从 API changelog 确认发布日期和接入边界。
- Anthropic 文档线索：Managed Agents 9 月 10 日权限策略；4 月架构文章应归类为漏收旧资料，不作为近期新发布。
- 浏览使用 ego lite TaskSpace 25。第一批检索原始结果已保存在 retrieval/search-01-*.json。

## 已阅读的原始材料

- Cursor self-hosted-machines：文章标 2026-09-02，明确只有工具执行转到用户机器，规划/推理留在 Cursor 云端，工具输出和对话仍可能被云端处理存储。不能把 self-hosted execution 写成全栈私有部署。
- LangChain context modes：2026-09-08，`isolated` 为默认新上下文；`fork` 继承父状态并剪去末尾委派工具调用；执行者适合继承、审阅者应避免父叙述锚定。是本书多代理章节值得补充的具体实现。
- dsh 官方 GitHub API：master 当前 ddefc45fbc7f8e46dd73185e68295696d1297887，2026-09-17 release 0.1.6-alpha.2。暂不把社区“官方桌面端”标题视为官方归属证据。
- 旧 claim 审计脚本只校验人工写入的 support_status 和引用关系，未验证引文是否蕴含主张；已有 PASS 应限于引用完整性，不足以认证事实。

## 论文日期与初步结论（已读摘要，待读方法）

- HarnessDev v1，9 月 1 日：评测产物是可运行 harness 本身，分 creation/evolution；六个创建模型、五个benchmark共2,207个实例；进化收益不稳定且换执行模型迁移有限。不能再单向论述“可组合必然更强”。
- Harness-of-Harness v1，9 月 1 日：在现成coding harness外再组织规划/开发/独立验收回路，报告三迭代平均相对增益52.25%；不能写成绝对百分点，也不能等同无监督自我改权重。
- JIT-Agent：首版8月26日，v2在9月3日。应标“旧稿漏收且窗口内修订”；训练生成harness的helper模型与冻结执行模型有别，四层进化分类应允许组合。
- openJiuwen：8月28日，结构可组合+运行时适应；榜单比较是选定点估计，不能直接视为相同预算下因果优势。
- OpenAI Agents API overview 已全文读到：托管session/编排/压缩/恢复，可选自托管execution environment；当前文档明确美国数据驻留、无ZDR支持，自托管sandbox也不改变该限制。首次发布日期待changelog核对。
- Anthropic release notes：9月14日显式signed compaction block；9月10日Managed Agents auto权限评估+事件evaluation字段；9月3日ant apply和锁文件。这些是本书上下文/权限/可复现配置的具体新案例。

## 第二阶段验证与反证

- OpenAI API changelog 确认 Agents API 于 9 月 10 日 public beta；9 月 3 日新增 async tool calling、mid-turn steering、保持缓存前缀的effort调整。是明确窗口内更新，不是从当前文档推断发布日期。
- Microsoft Harness 文档修改于 9 月 15 日；已读正文。它组合现有Agent Framework构件，强调每次模型调用后存历史、默认todo/模式/观测、可选有界loop；这不是另造独立runtime。文档修改日期不等于产品首发日期。
- Cursor 9 月 10 日 Projects beta：协调者委派、跨机器共享上下文、事件/周期触发；“数月/上千子代理”等是产品口径，未当作独立实测。
- 9 月 17 日 An Empirical Study of Harness Design for Coding Agents：固定loop，176个配对设置，Nemotron三尺度+Mistral，不包含当前全部前沿模型；planning/action-space只在T4/128k消融。结果支持模型与预算相关选择，不能推出“更多工具/更厚harness普遍更好”。
- HN 49753878讨论提出可迁移性、极简loop总代码量、协议与模型耦合问题；评论是研究线索，技术结论回到论文正文核实。全文研究本身使用LangGraph，因此“生产coding corpus不采用通用框架”不能推演成“框架已被淘汰”。
- HarnessDev方法已核查：evolution每creator–runtime cell只有一条轨迹，post-freeze held-out仅SWE-Pro；作者明确不能做群体/不确定性推断；tokens不含creator/judge/probe费用。
- HoH有同开发轮数对照与tokens列，不能把首段相对增益当等计算成本普适增益。
- 页面2609.00006出现编号月份与Submitted 15 Jul 2026不一致；暂列时间元数据待核，不据编号断言9月新发。

## 新一批资料与审阅纠偏

- HarnessEvolve 9月1日：参考轨迹使用ground truth生成，质量/性能双门和epoch-end held-out选型；应明确答案可用前提，held-out用于选型不等于永久密封终测。
- RSI roadmap：首版9月10日、v2 9月15日；五级自主性是研究路线图，不是已完成递归自我改进的实证。
- HookPry：9月3日/v2 9月8日，生命周期hook配置更新的供应链威胁；攻击前提是可控制插件元数据/更新，不是任意网页内容直接可获得主机执行权。
- MemSecBench 7月29日，属于旧稿漏收：记忆写入→使用→选择性清除完整周期，与本书经验入库/撤销讨论直接相关。
- ACP v2 draft 7月20日，也属漏收；强调session生命周期不由prompt响应结束，稳定ID更新/流式工具调用/更灵活权限。仍是draft，不能宣称稳定标准。
- LangSmith Engine工程文5月19日：从trace筛查、深挖、问题、评测样本到独立修复代理，属于已有生产实践补充，不是九月首发。
- 两份离线深审已完成，分别覆盖历史/原理与产品/进化/实践；查到ACI错误全称、validation误译、NLE误释、字数口径混用等。具体逻辑风险交由执行验证继续核实。

## 旧证据与新版本必须分开

- 2607.13683v1 为 Self-Evolving Agent Harnesses via Gated Semantic Quality-Diversity（GSME），v2为 HarnessBank（7月30日）。书中的sources/evidence挂v2但名称与机制叙述来自v1，需校正版次映射；不是9月新改名。
- Self-Harness当前仍v3/8月20日、Living-Harness仍v2/8月11日，没有发现本窗口内新版本，不制造更新。
- NLE官方仓库明确 NetHack Learning Environment，HSI原文将它列为roguelike环境；正文中文扩写确定错误。
- Reddit 1w8f7bp 9月5日讨论有14任务自报对比，但任务数小、作者关联性和配置可比性不充分；只用来提出应测成本/模型替换/本地能力的问题，不作产品排名依据。
- Cursor论坛172038用户报告子代理身份混淆和递归派生，用户同时明确不归因两者同一根因。报告不得把它升级为已确认的权限绕过漏洞。
- 中文知乎HarnessEvolve讨论已读，ground-truth与首个分歧未必是根因的批判需回原论文核验；中文社区仅作为发现线索和观点。

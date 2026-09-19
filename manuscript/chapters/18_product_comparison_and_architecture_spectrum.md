# 第十八章 产品比较：不要用一张总分表掩盖架构差异

> 资料截面：2026-09-19。本章是架构与接入责任比较。五个主案例没有完成统一任务、模型、预算与权限条件下的实测，六轴均不填分数，也不构成产品排名。

产品选择首先要确定采购或自建的是哪一部分：开发者工具、可嵌入循环、组合框架，还是托管 Harness。随后再比较谁运行循环、谁执行工具、谁保存记录。相同品牌可能同时覆盖多个层次；相同“自管”标签也可能对应完全不同的数据流。

## 1. 五个主案例：公开事实与作者判断分列

第二列归纳已核验的公开文档或固定源码，详情与版本见第十三至十七章；第三列是作者提出的采用条件和待测问题，没有同条件效能结论。

| 主案例 | 公开接入面与源码边界 | 作者的架构判断与首要验证问题 |
|---|---|---|
| Claude Code 及相关 Claude 接入面 | CLI、Agent SDK；Managed Agents 另管持久会话与循环。Messages API 显式压缩又是不同接口；本轮未审计托管内部源码 | 先选择自行运营或托管循环，再测扩展更新、逐调用权限与恢复缺口 |
| OpenAI Codex | 开源 exec、TypeScript/Python SDK、App Server；Agents API 于 9 月 10 日 public beta，托管内部不由开源源码覆盖 | 双向协议适合丰富客户端；托管路线另验数据留存、工具回传和退出成本 |
| Cursor | IDE、云端 VM、自管 worker；Projects 于 9 月 10 日进入 beta；内部循环与上下文选择实现未开放供本轮审计 | 自管执行适合贴近内部构建环境的需求，但前提是接受云端推理及相关数据流 |
| DeepSeek Harness | profile/bundle/SDK 与可检查的插件源码；当前 0.1.6-alpha.2，PTC 使用受平台 sandbox 约束的子进程 | 适合研究配置和运行组件变体；先验证部分失败、Host 插件授权与会话迁移 |
| OpenHands | 历史 0.62.0 Runtime；当前 Canvas 1.20.0、SDK 1.49.2、Agent Server 与执行环境分层，关键源码可定位 | 适合需要控制执行与会话实现的团队；验证事件补取、容器身份和资源回收 |

托管差异见 [Managed Agents 架构](https://www.anthropic.com/engineering/managed-agents)、[Agents API 概览](https://developers.openai.com/api/docs/guides/agents-api/overview)、[Cursor 自管机器](https://cursor.com/blog/self-hosted-machines)。开源边界见 [dsh 固定架构](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md) 与 [OpenHands 固定会话工厂](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py#L34)。这些一手来源可支持功能和契约描述，不能因 URL 多就计作独立效能验证。

## 2. 成品、可嵌入运行时、框架与托管服务

五个主案例不覆盖全部采购对象。下面补入 Deep Agents 和 Microsoft Harness，目的是说明可组合框架仍有独立位置，不把本篇扩成品牌榜单。分类允许重叠：

| 层次 | 示例 | 应比较的交付责任 |
|---|---|---|
| 成品工具与工作入口 | Claude Code、Cursor、OpenHands Canvas | 交互、工作组织、权限管理与产物交接 |
| 可嵌入 Agent 运行时 | Claude Agent SDK、Codex SDK/App Server、dsh、OpenHands SDK | 循环、会话、工具及进程生命周期由谁运营 |
| 组合框架 | Deep Agents、Microsoft Agent Framework Harness | 应用如何组合上下文、持久化、审批、委派和有界循环 |
| 托管 Harness | Claude Managed Agents、OpenAI Agents API、Cursor 云端循环 | 服务商管理哪些运行状态，应用保留哪些执行与数据责任 |

Deep Agents 在 9 月 8 日的说明中提供 `isolated` 和 `fork` 两种子代理上下文模式：前者从任务说明开始，后者继承父状态，把尾部委派调用整理为子代理输入。继续已有调查的执行者可能减少重复读取；独立审阅者则可能更适合隔离上下文，以免继承父代理判断。两种模式都不是天然的费用或质量保证。[Deep Agents 上下文模式](https://www.langchain.com/blog/organizing-context-in-a-multi-agent-harness)

Microsoft Harness 复用 Agent Framework 的 chat client、会话、上下文提供者与中间件，组合每次模型调用后的历史持久化、todo、模式、审批、观测，以及可选的有界循环。它不是替所有应用规定一套最复杂配置。文档的 **2026 年 9 月 15 日是更新时间**，本轮没有据此证明功能首发日期。[Microsoft Harness](https://learn.microsoft.com/en-us/agent-framework/concepts/harness)

## 3. 托管与自管，要按责任拆开

这里把“产生决策并管理会话的组件”称为 **Agent Runtime**，把“实际执行命令、文件与工具操作的环境”称为 **Execution Runtime**。同一系统可以拆开运营二者；“runtime”一词本身不构成安全边界。

| 具体部署路线 | 循环与会话 | 工具执行与凭证 | 必须另查的数据边界 |
|---|---|---|---|
| Claude Managed Agents | 厂商披露将 Harness 与持久日志分离 | 通过执行环境/工具接口访问；工程文描述沙箱外凭证库及代理 | 按所选环境核对事件、工具输出与存储规则，不能套用 Code 本机假设 |
| OpenAI Agents API | OpenAI 管理编排、压缩与恢复 | 可用托管或自管 sandbox，应用接入工具 | 当前仅美国数据驻留、不支持 ZDR；自管 sandbox 不改变此限制 |
| Cursor 云端 Agent + 自管 worker | 循环、推理与规划仍在 Cursor 云端 | 企业机器执行工具，经出站 HTTPS 回传结果 | 代码可能随输出回传，转录可能云端处理及存储 |
| 自行部署 Codex/dsh/OpenHands 等 | 所部署组件由组织运营，持久化依版本配置 | 组织选择执行环境与凭证控制 | 若仍调用外部模型或工具服务，相关数据仍可能出网 |

上表前三行依据上一节所引官方资料；第四行是部署责任的作者归纳，不能替代每个版本的协议检查。业务验收由采用组织依据具体合同指定，可以采购实现或采用人工审阅；它不会仅因执行环境托管就自动消失。

功能层、管理平面与信任域也应分开：插件管理、实验和发布可以同属演化功能，但候选插件不应因此获得评价数据或发布凭证。高风险场景要用身份与读写权限建立隔离；低风险场景可以在较简单的部署内实现受限职责。第十六章的插件图和第十七章的执行容器分别是不同控制点，不能把它们都映射为一个万能 runtime 开关。

## 4. 六个评价坐标，需要六类证据

以下是待执行的比较协议，不是本书已测出的结果。所有产品在这些坐标上的本书分数均为“未测量”。

| 坐标 | 同条件试验应收集什么 |
|---|---|
| 任务匹配度 | 全部分配任务的完成、失败、超时与取消；按任务族和风险切片 |
| 控制力 | 身份、网络、审批、撤销和取消的故障测试记录 |
| 证据性 | 原始动作、结果、产物与权限决定能否完整关联 |
| 耐久性 | 中断后状态恢复、迟到事件处理和不确定副作用对账 |
| 可替换性 | 导出未完成工作与产物后，替代接入面能否承接必要语义 |
| 运营经济性 | 模型、计算、存储、人工复核、重试、维护与迁移费用 |

应固定任务合同、工作区快照、权限和预算，采用多次试运行并披露选择与停止规则（见第十二章）。若产品无法使用同一模型，就比较“模型＋Harness＋环境”的系统组合，不把差异归因给 Harness 单一组件。Cursor Keep Rate、84% 权限提示下降、46.9% token 下降衡量不同对象，均不能填进这张表作为统一分数。

下面是**本书自定义的比较工作表**，由自建评测器解释，不是厂商配置，不能直接交给任何 CLI/SDK；任务集名、版本、次数与预算都是教学占位值：

```yaml
comparison:
  task_suite: repo-maintenance-v3
  workspace_snapshot: fixed
  trials_per_case: 5
  budgets: {wall_minutes: 30, model_usd: 8}
  permissions: code-medium-v4
  verifier: clean-room-v6
  report_slices: [task_type, repo_size, risk, runtime, model]
```

## 5. 共同契约应保留产品差异

平台可以统一 Task、Action、Observation、Artifact、Approval 与验证结果，但应保留原始供应商 payload、版本和身份映射。业务 task、供应商 session/thread、一次 turn 及平台 attempt 的生命周期不同；收到“本轮结束”不能自动标记业务验收通过。这一共同原则由本节集中定义，各案例不再用同一段话代替具体机制。

验收的独立程度由任务风险决定：交付建议可人工审阅，提交代码可用封存产物上的固定检查，外部写入还须授权与结果回读。验证器移到另一进程也不自动独立；它所用数据、身份与可写范围仍需明确（见第十章）。

适配器不能为追求统一丢掉原生语义：Codex 要区分 item 类型及增量，dsh 要区分瞬态流与已落盘 attempt，OpenHands 要区分持久 Event 与 socket envelope。缺少关键能力时应显示“不支持”，降低自动提交范围或更换接入面，不能伪造通用成功事件。

## 6. 有条件的采用与退出

在现成产品覆盖关键边界、接入和退出成本可控时，采购已有组件是值得先测的路线；若离线、特殊执行环境或数据流约束没有可采购方案，也应比较受限自研、确定性工作流与人工处理。任务量大小不是唯一条件，多 Runtime 也不是成熟的必要条件。

作者建议在同一统计窗口计算：

```text
总成本 = 建设与迁移固定成本
       + 任务量 ×（模型、计算、存储及人工复核的单位成本）
       + 维护、失败重试、风险损失与双运行过渡成本
```

单位成本若已包含重试，就不应在后项重复计入。改变任务量、人工介入率和供应商价格做敏感性分析，再预先约定质量下界、费用上限、不可接受的数据流与退出触发条件。本轮没有这组测量，故不宣布某产品最便宜，也不替所有组织指定“买或建”的结论。第二十六至二十九章将沿这些责任与条件展开参考设计。

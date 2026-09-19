# 第九章 权限、沙箱、凭证与供应链

> 适用性声明：本章讨论的是 Harness 工程控制，不替代组织的安全评审、隐私评估或法律合规意见。

Agent 安全需要关心错误怎样变成真实副作用。风险既来自被误导的模型决策，也来自运行时直接执行的插件、脚本与配置。提示注入、目标漂移、工具误用和记忆污染，不能只靠加强系统提示处理。

所以安全架构要默认假设模型会被误导，并把误导后的能力和影响范围设上限。

## 1. 四个不同问题

```text
Authentication  谁在发起任务？
Authorization   此身份可对什么对象做什么？
Approval        此次具体动作是否需要人确认？
Isolation       即使获准执行，进程还能触及什么？
```

把它们混成一个“是否允许工具”开关会出漏洞。用户有仓库写权限，不代表每次 Agent 写入都免审批；用户同意运行测试，不代表脚本可以读 SSH key；容器隔离进程，不代表可以不受控调用云 API token。

## 2. Prompt 不是安全边界

提示可以降低误用频率，但不构成不可绕过的安全边界。
任何关键约束都要落地到确定性机制：

| 意图 | 提示层引导 | 执行层控制 |
|---|---|---|
| 不读主目录秘密 | “不要读取” | 文件系统隔离 |
| 不向外泄露数据 | “不要上传” | egress allowlist/DLP |
| 不改生产 | “只测试” | 独立身份与环境 |
| 删除前询问 | prompt 规则 | commit-time approval |
| 只操作本仓库 | 工具描述 | resource-scoped capability |

模型负责理解意图，策略与执行层在给定配置和威胁模型下限制可执行范围。表中控制也不是完整证明：DLP 可能漏检，隔离取决于挂载、身份和网络配置，审计签名只能帮助确认记录来源与完整性，不能证明业务内容正确。

## 3. 从逐次批准到受控自治

逐条命令弹窗看起来安全，但高频弹窗会产生审批疲劳。
Anthropic 报道，Claude Code 在加入文件系统和网络双重隔离后，内部 permission prompt 减少了 84%。其设计用到了 macOS Seatbelt、Linux bubblewrap 和受控网络代理。
[Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

更稳妥的是先定义安全工作区：区内动作自动放行；越界才申请临时能力。

```text
default sandbox
  ├── read project
  ├── write workspace
  ├── run approved executables
  └── no network

step-up request
  ├── exact extra path/domain
  ├── reason and duration
  ├── one action/session scope
  └── audit + revoke
```

批复的是具体 capability，不是对 Agent 的抽象信任。

## 4. 文件系统与网络必须同时限制

只有文件隔离没有网络限制，Agent 仍可能下载恶意程序或访问内网服务。
只有网络限制没有文件隔离，Agent 仍可能先读取秘密，再等待外泄通道。
Anthropic 明确强调两者都要有。

企业沙箱还要考虑：

- 只读系统镜像与受控可写层；
- `.git`、配置目录和 socket 的特殊处理；
- 设备、IPC、进程、syscall 与资源限制；
- DNS、代理、IP 重绑定与内网地址；
- 子进程继承；
- sandbox teardown 与 artifact 导出。

Sandbox profile 必须版本化，并记录到每次 execution。

## 5. Policy 决策模型

策略输入不应是未解析的自然语言命令，而应尽量标准化：

```text
Subject      user, agent, service identity
Action       canonical tool/action + normalized args
Resource     repo, path, API object, environment
Context      task, tenant, time, risk, prior approvals
Provenance   model, skill, MCP server, originating content
```

输出应是：`ALLOW`、`DENY`、`REQUIRE_APPROVAL`、`CONSTRAINED_ALLOW`。约束可包含只读、路径、域名、行数、金额、TTL 或 dry-run。

策略还要在 commit 阶段重新检查，因为审批之后环境、资源版本、身份状态可能已变化。早先观察和授权不能无限期代表后续副作用合法。

在 TASK2048 的教学情境中，即使用户后来批准合并某个补丁，Agent 随后又修改文件，旧批准也不能自动覆盖新版本。提交前绑定检查失败，就暂停该提交并重新取得适用授权；已发生的分支修改仍保留在任务状态中，不因提交被拒绝而抹去。

## 6. 凭证不进入模型上下文

模型通常只需要知道“可使用 GitHub 工具”，不需要拿到 token。
推荐流程是：

```text
authorized action
  → credential broker
  → short-lived scoped credential
  → isolated executor
  → redact output
```

凭证应绑定目标 resource、动作范围、租户和短 TTL。
日志持久化前需脱敏，避免工具错误把 secret 放入上下文。
对无法细分权限的遗留系统，建议通过代理提供窄业务动作，而不是把管理员 token 给通用 shell。

## 7. Prompt Injection 的系统应对

间接 prompt injection 可能来自网页、issue、文档、代码注释、MCP 输出和 memory。
这些内容应标记为不可信数据，而非和 system instructions 合并。

防御应是组合式的：

1. provenance 与信任标签；
2. 数据/指令通道分离；
3. 最小工具和最小权限；
4. 跨域数据流策略，比如私有仓库内容不得写到公共仓库；
5. 高风险动作 commit-time approval；
6. egress、DLP 和秘密扫描；
7. 事后审计与异常检测；
8. 对抗评估。

即使检测器漏过 injection，sandbox 与 policy 也要把后果压住。
安全目标是把受影响后的行为限制在获准范围，并检查范围内动作的组合后果；能否做到，要用明确攻击前提和执行环境验证。

## 8. 多 Agent 的权限传播

父 Agent 转授自身权限时，不能把全部权限自动传给子 Agent，应签发受限的临时授权。若专家以独立身份取得域内权限，则由可信策略服务检查专家的执行权、任务用途和调用者的委派权；manager 不必因此取得专家可读数据的直接访问权。

```text
delegate(
  task,
  allowed_tools,
  resource_scope,
  budget,
  expiry,
  can_delegate=false
)
```

子 Agent 的结果仍是不可信输入，合并或提交要再经过验证器和授权策略。向下转授权限不得超过可转授范围，但缩权与父级复核并不能解决所有组合风险。例如私有读取与公开写入分别合法，经过共享黑板连接后仍可能泄漏；还需检查结果来源、可传递范围和后续用途。

## 9. MCP 与插件供应链

安装 MCP server、skill 或 DSH plugin，本质上等于给 Harness 增加代码与指令。
风险包括：

- 恶意安装脚本与依赖；
- server descriptions/tool descriptions 的注入；
- 更新后 schema 或行为变化；
- 凭证范围过大；
- 本地 server 继承宿主权限；
- plugin 能修改 loop、policy 或日志。

企业 marketplace 要做到来源验证、版本 pin、SBOM、签名、静态/动态扫描、权限 manifest、隔离测试、发布审批和紧急撤销。
插件的可卸载效果可以帮助清理链路，但不能替代安全验证。
组合性越强，生命周期和所有权保证越关键；DSH 的可卸载 effect 主要是清理结构，不是安全证明。

HookPry v2 将风险定位到模型决策之外：攻击者控制插件元数据、版本和 hook 配置，先提供可信的初始版本，再通过更新增加事件绑定命令。更新被采用且事件发生后，宿主可能直接启动子进程，无需模型再次选择工具。[HookPry v2](https://arxiv.org/html/2609.03884v2) 论文的攻击能力受更新采用、事件发生和子进程权限限制，不等于任意网页都能绕过沙箱，也不能据此断言所有当前版本存在同一漏洞。本书未复现其攻击实验。

因此，本书建议审查更新前后的 hook 清单、触发事件、命令和执行身份；新增执行权要重新授权，宿主与工作区分别隔离，并保留调用审计和紧急撤销。模型工具调用门之外的自动脚本也必须经过受信任的执行边界。卸载插件只能停止后续使用，不能抹去已发生的外部副作用。

## 10. 审批 UX 是安全系统

审批界面要把人能判断的信息完整展示：

- 执行语义动作，而不仅是工具名；
- 目标资源和数据范围；
- 预计副作用与是否可逆；
- Agent 的请求理由；
- 触发审批的策略；
- 临时授权范围与持续时间；
- dry-run/diff；
- 拒绝后的安全替代方案。

“Allow always”必须绑定精确规则，不能把一次命令许可扩展成整个 shell。
Codex exec policy 通过 allow/prompt/forbidden 前缀规则，并支持规则附带测试样例，能把“长期许可”变成可审查策略。[Codex ExecPolicy](https://github.com/openai/codex/blob/main/codex-rs/execpolicy/README.md)

## 11. 审计记录与模型 trace 分离

安全审计不能依赖可压缩或可删除的聊天摘要。每个敏感动作要记录：

```text
who / delegated_by
what canonical action
which resource
why / task reference
policy version and decision
approval identity and scope
credential lease id
sandbox profile
effect outcome and verification
```

模型隐藏推理不是审计必须条件。组织真正需要的是可观测的输入、动作、策略、证据和结果，而不是私有思维链。

## 12. 数据分类与跨域流动

Agent 容易把不同来源数据组合。
应对输入、artifact、memory、tool result 进行分类，并在写出时执行信息流策略。

例如：

```text
PrivateRepo + PublicIssue → deny public write
CustomerPII + ExternalModel → require approved gateway/redaction
ProductionLog + LongTermMemory → aggregate or prohibit
Secret + AnyModelContext → deny
```

这一层比只限制某个工具更强，因为合法读取和合法写入组合后也可能泄密。

## 13. 风险分级

| 等级 | 示例 | 默认控制 |
|---|---|---|
| R0 | 读取公开资料 | 记录来源，按不可信输入处理，限制后续数据流与动作 |
| R1 | 读取项目、写临时区 | workspace sandbox |
| R2 | 修改分支、安装依赖、有限网络 | policy + sandbox |
| R3 | 外部沟通、合并、共享数据写入 | 明确审批 + verifier |
| R4 | 生产、资金、身份、不可逆删除 | 双控制/专用 workflow |

风险由动作、资源、数据、可逆性和环境共同决定，不应只按工具名静态分级。表中 R0 仅表示单次读取的直接影响较低；载入恶意内容后再调用写工具，必须按后续动作重新授权。

R3/R4 中有些动作无法真正回滚，例如已发送消息或已被对方采用的数据。它们应有事前授权、限额、提交回读和事故处置方案；补偿处理已确认的错误效果，不能据此盲重试未知提交。软件版本回退是另一项能力，应单独演练，附录 B 给出判据。

## 14. 安全测试

- 网页、issue、代码注释中的间接 injection；
- 工具描述与返回值 poisoning；
- 私有到公共资源的数据外泄路径；
- shell 管道、重定向、子进程和解释器绕过；
- DNS 重绑定、代理绕过和内网 SSRF；
- memory/skill 持久污染；
- 记忆撤销后，已有上下文、摘要、检索索引和派生技能是否继续传播旧指令；
- 子 Agent 权限升级；
- 审批 replay 与过期授权；
- crash/retry 导致重复提交；
- 恶意插件卸载后的残留 effect。
- 插件更新新增 hook 后，宿主是否在未经重新授权时直接执行命令。

安全评估应在目标 Harness 与隔离的代表性执行环境中进行，并记录版本、攻击前提和故障范围。裸模型拒绝率不能代表系统安全。记忆撤销场景可借鉴 MemSecBench v1 的写入、后续执行和选择性修复流程；第七章讨论如何把这种生命周期检查扩展到派生对象。[MemSecBench v1](https://arxiv.org/abs/2607.27080v1)

## 15. 安全参考边界

```text
Untrusted Context
       ↓ taint/provenance
Model proposes action
       ↓
Schema + semantic normalization
       ↓
Policy decision ─→ Human approval
       ↓
Scoped capability + credential lease
       ↓
OS/VM sandbox + egress proxy
       ↓
Effect ledger + output redaction
       ↓
External verification + audit
```

图中是模型提议动作的路径；生命周期 hook 等宿主触发动作也须接入授权、隔离、账本和审计，不能因为不经过模型就豁免。

自治应在预先定义的授权范围内运行。提示帮助理解意图，策略决定是否允许，沙箱限制接触面，凭证代理提供受限身份；验证检查验收条件，审计保留可复查记录。下一章进一步讨论：哪些证据足以按任务约定判定完成。

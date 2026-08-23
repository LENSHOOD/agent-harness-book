# 第九章 权限、沙箱、凭证与供应链

> 本章状态：正文初稿 v0.1，不替代组织安全评审或合规意见。

Agent 安全的根本难题不是模型偶尔犯错，而是错误决定可以通过工具变成真实副作用。Prompt injection、目标漂移、工具误用和记忆污染无法仅靠“更强系统提示”消除。因此安全架构必须假设模型会被误导，并限制被误导后的能力与爆炸半径。

## 1. 四个不同问题

```text
Authentication  谁在发起任务？
Authorization   此身份可对什么对象做什么？
Approval        此次具体动作是否需要人确认？
Isolation       即使获准执行，进程还能触及什么？
```

把它们混成一个“允许工具”开关会产生漏洞。用户有仓库写权限，不代表 Agent 的每次写入都无需批准；用户批准运行测试，不代表脚本可以读取 SSH key；容器隔离进程，也不自动限制其云 API token。

## 2. Prompt 不是安全边界

提示可以降低误用频率，却不能提供不可绕过保证。任何关键约束都应映射为确定性机制：

| 意图 | 弱机制 | 强机制 |
|---|---|---|
| 不读主目录秘密 | “不要读取” | 文件系统隔离 |
| 不向外泄露数据 | “不要上传” | egress allowlist/DLP |
| 不改生产 | “只测试” | 独立身份与环境 |
| 删除前询问 | prompt 规则 | commit-time approval |
| 只操作本仓库 | 工具描述 | resource-scoped capability |

模型负责理解意图；策略与执行层负责保证边界。

## 3. 从逐次批准到受控自治

逐个命令弹窗看似安全，但高频批准会造成疲劳。Anthropic 报告 Claude Code 引入文件系统与网络双重隔离后，内部 permission prompt 减少 84%；其设计使用 macOS Seatbelt、Linux bubblewrap 和受控网络代理。[Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

更好的模式是：先定义一个安全工作区，区内动作自动运行，越界才请求临时能力。

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

批准的是具体 capability，不是对 Agent 的抽象信任。

## 4. 文件系统与网络必须同时限制

只有文件隔离、没有网络限制时，Agent 仍可能下载恶意程序或访问内部服务；只有网络限制、没有文件隔离时，它可能读取秘密并等待未来外泄通道。Anthropic 明确强调两者结合。

企业沙箱还应考虑：

- 只读系统镜像与受控可写层；
- `.git`、配置目录和 socket 的特殊处理；
- 设备、IPC、进程、syscall 与资源限制；
- DNS、代理、IP 重绑定和内网地址；
- 子进程继承；
- sandbox teardown 与 artifact 导出。

Sandbox profile 必须版本化并记录在每次 execution 中。

## 5. Policy 决策模型

策略输入不应是未经解析的自然语言命令，而应尽量规范化：

```text
Subject      user, agent, service identity
Action       canonical tool/action + normalized args
Resource     repo, path, API object, environment
Context      task, tenant, time, risk, prior approvals
Provenance   model, skill, MCP server, originating content
```

输出：`ALLOW`、`DENY`、`REQUIRE_APPROVAL`、`ALLOW_WITH_CONSTRAINTS`。约束可以是只读、路径、域名、行数、金额、TTL 或 dry-run。

策略应在 commit 时重新检查，因为审批后环境、资源版本或身份状态可能变化。早期观察和授权不能无限期证明稍后的副作用仍合法。

## 6. 凭证不进入模型上下文

模型通常只需要知道“可使用 GitHub 工具”，不需要看到 token。推荐流程：

```text
authorized action
  → credential broker
  → short-lived scoped credential
  → isolated executor
  → redact output
```

凭证绑定目标 resource、动作范围、租户和短 TTL。日志在持久化前脱敏，避免工具错误把 secret 返回上下文。对于无法细分权限的遗留系统，应通过代理提供窄业务动作，而不是把管理员 token 交给通用 shell。

## 7. Prompt Injection 的系统应对

间接 prompt injection 来自网页、issue、文档、代码注释、MCP 输出和记忆。系统应把这些内容标记为不可信数据，而不是与 system instructions 混合。

防御是组合式的：

1. provenance 与信任标签；
2. 数据/指令通道分离；
3. 最小工具和最小权限；
4. 跨域数据流策略，例如私有仓库内容不得写入公共仓库；
5. 高风险动作 commit-time approval；
6. egress、DLP 和秘密扫描；
7. 事后审计与异常检测；
8. 对抗评估。

即使检测器漏过 injection，sandbox 和 policy 也应限制后果。安全目标不是保证模型永不受影响，而是保证受影响后不能越权。

## 8. 多 Agent 的权限传播

父 Agent 能做某事，不代表子 Agent 自动继承全部权限。委派应创建缩小的 capability：

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

子 Agent 的结果是不可信输入；合并或提交仍由父级 verifier 和 policy 检查。防止 delegation chain 逐步扩大权限，也防止多个低风险动作组合成高风险结果。

## 9. MCP 与插件供应链

安装 MCP server、skill 或 DSH plugin 等于向 Harness 增加代码与指令。风险包括：

- 恶意安装脚本和依赖；
- server descriptions/tool descriptions 注入；
- 更新后 schema 或行为变化；
- 凭证范围过大；
- 本地 server 继承宿主权限；
- plugin 能修改 loop、policy 或日志。

企业 marketplace 需要来源验证、版本 pin、SBOM、签名、静态/动态扫描、权限 manifest、隔离测试、发布审批和紧急撤销。插件可组合性越强，生命周期与所有权保证越重要；DSH 的可卸载 effect 解决清理结构，不自动证明插件安全。

## 10. 审批 UX 是安全系统

审批界面应显示人能判断的信息：

- 将执行的语义动作，而非仅工具名；
- 目标资源和数据范围；
- 预计副作用与可逆性；
- Agent 请求理由；
- 触发审批的策略；
- 临时授权范围和持续时间；
- dry-run/diff；
- 拒绝后的安全替代方案。

“Allow always”必须绑定精确规则，不能把一次命令泛化为整个 shell。Codex 的 exec policy 使用 allow/prompt/forbidden 前缀规则并允许规则附带测试样例，是把持久批准变成可审查策略的一种做法。[Codex ExecPolicy](https://github.com/openai/codex/blob/main/codex-rs/execpolicy/README.md)

## 11. 审计记录与模型 trace 分离

安全审计不能依赖可压缩或可删除的聊天摘要。每个敏感动作记录：

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

模型隐藏推理不是审计必要条件。组织需要的是可观测输入、动作、策略、证据和结果，而不是要求保存私有思维链。

## 12. 数据分类与跨域流动

Agent 特别容易把不同来源数据组合。必须对输入、artifact、memory 和 tool result 标记分类，并在写出时执行信息流策略。

例如：

```text
PrivateRepo + PublicIssue → deny public write
CustomerPII + ExternalModel → require approved gateway/redaction
ProductionLog + LongTermMemory → aggregate or prohibit
Secret + AnyModelContext → deny
```

这比只限制单个工具更强，因为合法读取和合法写入组合起来也可能泄密。

## 13. 风险分级

| 等级 | 示例 | 默认控制 |
|---|---|---|
| R0 | 读取公开资料 | 记录即可 |
| R1 | 读取项目、写临时区 | workspace sandbox |
| R2 | 修改分支、安装依赖、有限网络 | policy + sandbox |
| R3 | 外部沟通、合并、共享数据写入 | 明确审批 + verifier |
| R4 | 生产、资金、身份、不可逆删除 | 双控制/专用 workflow |

风险由动作、资源、数据、可逆性和环境共同决定，不应只按工具名静态分类。

## 14. 安全测试

- 网页/issue/代码注释中的间接 injection；
- 工具描述与返回值 poisoning；
- 私有到公共资源的数据外泄路径；
- shell 管道、重定向、子进程和解释器绕过；
- DNS 重绑定、代理绕过和内网 SSRF；
- memory/skill 持久污染；
- 子 Agent 权限升级；
- 审批 replay 与过期授权；
- crash/retry 导致重复提交；
- 恶意插件卸载后的残留 effect。

安全评估必须在真实 Harness 和执行环境中进行，裸模型拒绝率不能代表系统安全。

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

本章结论是：自治来自预先定义的安全自由空间，而不是跳过权限。提示用于指导，策略用于授权，沙箱用于限制，凭证代理用于缩权，审计与验证用于证明发生了什么。下一章将讨论最后一个经常被忽略的边界：Agent 怎样证明任务完成，而不是只生成一个令人信服的完成声明。

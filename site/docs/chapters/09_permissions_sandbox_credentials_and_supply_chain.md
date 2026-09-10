# 第九章 权限、沙箱、凭证与供应链

> 适用性声明：本章讨论的是 Harness 工程控制，不替代组织的安全评审、隐私评估或法律合规意见。

Agent 安全的根本问题不是模型偶尔出错。
真正的风险在于：错误决策会通过工具变成真实副作用。Prompt injection、目标漂移、工具误用、记忆污染不能只靠“更强 system prompt”根治。

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

| 意图 | 弱机制 | 强机制 |
|---|---|---|
| 不读主目录秘密 | “不要读取” | 文件系统隔离 |
| 不向外泄露数据 | “不要上传” | egress allowlist/DLP |
| 不改生产 | “只测试” | 独立身份与环境 |
| 删除前询问 | prompt 规则 | commit-time approval |
| 只操作本仓库 | 工具描述 | resource-scoped capability |

模型负责理解意图；策略与执行层负责真正保证边界。

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

输出应是：`ALLOW`、`DENY`、`REQUIRE_APPROVAL`、`ALLOW_WITH_CONSTRAINTS`。约束可包含只读、路径、域名、行数、金额、TTL 或 dry-run。

策略还要在 commit 阶段重新检查，因为审批之后环境、资源版本、身份状态可能已变化。早先观察和授权不能无限期代表后续副作用合法。

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
安全目标不是模型永不受影响，而是受影响后不能越权。

## 8. 多 Agent 的权限传播

父 Agent 具备的能力不能自动全量传给子 Agent。
委派时应创建缩减后的 capability。

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

子 Agent 的结果仍是不可信输入，合并或提交要再经过父级 verifier 和 policy。
这样可以防止 delegation chain 逐层放大权限，也能防止多个低风险动作叠加成高风险结果。

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
| R0 | 读取公开资料 | 记录即可 |
| R1 | 读取项目、写临时区 | workspace sandbox |
| R2 | 修改分支、安装依赖、有限网络 | policy + sandbox |
| R3 | 外部沟通、合并、共享数据写入 | 明确审批 + verifier |
| R4 | 生产、资金、身份、不可逆删除 | 双控制/专用 workflow |

风险由动作、资源、数据、可逆性和环境共同决定，不应只按工具名静态分级。

## 14. 安全测试

- 网页、issue、代码注释中的间接 injection；
- 工具描述与返回值 poisoning；
- 私有到公共资源的数据外泄路径；
- shell 管道、重定向、子进程和解释器绕过；
- DNS 重绑定、代理绕过和内网 SSRF；
- memory/skill 持久污染；
- 子 Agent 权限升级；
- 审批 replay 与过期授权；
- crash/retry 导致重复提交；
- 恶意插件卸载后的残留 effect。

安全评估必须在真实 Harness 与真实执行环境里做。裸模型拒绝率不能代表系统安全。

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

本章结论是：自治不是跳过权限，而是在预先定义的安全自由空间内运行。提示用于指引；策略用于授权；沙箱用于限制；凭证代理用于缩权；审计与验证用于证明到底发生了什么。下一章讨论下一个常被忽略边界：Agent 如何证明完成，不只生成“看起来完成”。

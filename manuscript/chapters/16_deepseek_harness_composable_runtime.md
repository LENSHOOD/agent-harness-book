# 第十六章 DeepSeek Harness：可组合、可逆的运行时

> 资料截面：2026-08-27。DeepSeek Harness（dsh）官方明确标为 developer preview，并警告会发生破坏兼容性的变化；本章讨论其设计方向，不把当前接口当成稳定企业标准。[官方仓库](https://github.com/deepseek-ai/deepseek-harness)

dsh 的核心问题不只是“又一个 coding agent”。更核心的是，它测试了 Agent Harness 是否可以像组件系统一样装配、替换和演化。它以 Cordis 为基础，把模型 adapter（模型适配器）、工具注册、session log（会话日志）和 agent loop（执行回路）都实现为插件。官方架构文档说明没有需要打补丁的特权核心。插件向共享 context（上下文）注册 service、typed event（类型化事件）和 effect（副作用）。组件卸载时，注册效果随之撤销。[Architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md)

## 1. 空间与时间上的组合

传统插件系统常强调“能加载”这一点。Cordis 更值得关注的是两类约束。第一是空间约束：组件按声明依赖获得服务。第二是时间约束：组件产生的注册和副作用在卸载时可逆。对 Harness 来说，这意味着可替换 tool registry（工具注册表）、model adapter（模型适配器）或 policy plugin（策略插件），而不必永久污染全局单例。

```text
context
 ├─ service dependency graph
 ├─ typed event routes
 ├─ plugin-owned effects
 └─ lifecycle: load → reconcile → unload/rollback
```

但“可逆注册”不等于“可逆现实副作用”。卸载一个发送邮件的插件不会撤回邮件。卸载数据库工具也不会自动回滚已提交事务。外部 effect（外部副作用）仍需第六章的 intent/outcome ledger（意图/结果账本）、幂等键和 reconciliation（对账）。否则开发者会把框架级可逆性误当成业务事务可回滚。

## 2. Profile、bundle 与分层配置

官方说明一个运行中的 dsh 是启动时由有序层组成的插件树。profile（配置画像）会组合多个 bundle（功能包），并叠加用户 patch（补丁）、home patch 和命令行 overlay（覆盖层）。bundle 是 Cordis 配置条目及其挂载代码的分发形式。上层仍可继续 patch。[Architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) 这套结构适合表达“企业基线 + 团队能力包 + 仓库定制 + 单次实验”。

同时它引入了配置优先级风险。同一 tool（工具）可能在不同层被替换，最终运行图可能和任一源文件都不同。企业使用时必须在启动后导出 resolved plugin graph（已解析插件图）、配置来源和 hash；证据包要记录解析后的运行版本，而不只是 profile 名称。

## 3. Code Mode 作为工具压缩

dsh 的工具系统提供 `run_code`。它通过代码运行时桥接多个工具调用，并有专门的动态 Cordis runner（运行器）和 VM sandbox（虚拟机沙箱）。[Tool catalog](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/tool-catalog.md) 设计动机与第八章讨论的 CodeAct/Code Mode 相近：把多步数据变换和工具编排压缩成一次程序化动作，减少 schema（数据结构定义）常驻内存并降低模型往返。

但它并非免费午餐。代码可能形成更大的副作用批次，细粒度审批、trace（追踪）和成本归因更难。动态插件还可能扩大供应链面。合理做法是让代码只访问显式桥接的 capability（能力）、并对每个子调用生成独立 action/effect event（动作/副作用事件），再限制 CPU、内存、网络和执行时长。

## 4. “一切皆插件”的边界

可替换性适用于运行时组件，但不应扩展到根信任。identity root（身份根）、policy root（策略根）、held-out eval（留出集评测）、审计和 release controller（发布控制器）若也由候选插件任意替换，系统就可能通过修改裁判证明自己进步。dsh 是优秀的 evolvable plane（可进化平面）载体，但 governance plane（治理平面）必须在其外部，或至少处于不可变信任域（见第二十四章）。

一个具体失效场景是：候选插件同时改写工具描述和成功统计器。工具选择率可能上升，但原因是统计器把 timeout（超时）排除在分母外。插件图仍然“可组合”，但实验结论仍然无效。因此进化系统要记录 validity（有效性）、activation（激活状态）和 significance（显著性）三类门槛，而不是只比较平均分。

## 5. 企业集成策略

在 developer preview 阶段，更稳妥的定位是研究与受控 profile。做法是固定 commit 和 lockfile，在隔离环境加载经过签名的 bundle，并禁止生产热更新。adapter（适配器）要导出 resolved graph（已解析图）、session event（会话事件）、tool 子调用、approval（审批记录）和 artifact（产物）。兼容性测试应覆盖 profile 启动、插件卸载、失败回滚与旧会话恢复。

| 采用方式 | 适用场景 | 进入生产前的附加条件 |
|---|---|---|
| 研究框架 | 比较 loop、tool、context 变体 | 固定版本与可重复 eval |
| 专用 runtime | 内部低风险自动化 | 插件白名单、隔离、证据导出 |
| 平台核心 | 暂不建议直接押注 preview API | 稳定协议、迁移策略、长期运维承诺 |

## 6. 设计判断

dsh 的原创价值在于把 Harness 从硬编码程序变成可解析、可替换、可撤销的组件图，并把“谁能改变运行时”推到架构中心。它为自我进化提供了可变表面，但并没有自动解决评价独立性、外部副作用和发布治理问题。真正的进化系统仍需把 Cordis 式组合能力与第二十四章的不可变治理平面结合。

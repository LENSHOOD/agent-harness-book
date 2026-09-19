# 第十六章 DeepSeek Harness：可组合、可逆的运行时

> 资料截面：2026-09-19。当前固定点为 `0.1.6-alpha.2`、commit `ddefc45fbc7f8e46dd73185e68295696d1297887`，9 月 17 日发布，仍为 developer preview / prerelease。历史对照点为 `0.1.2-alpha.1`、`cd5ef8148158c3a752a658978873241fdf8e2bbc`。本章核对公开源码与文档，未部署或进行安全逃逸测试。[发布记录](https://github.com/deepseek-ai/deepseek-harness/releases/tag/dsh-v0.1.6-alpha.2)

dsh 以 Cordis 组合模型适配器、工具、会话日志和 Agent 循环。插件注册服务、类型化事件及随生命周期清理的注册效果，因此可在不改特权核心的前提下替换组件。[固定版架构](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md) 这里“可逆”的范围是受框架管理的注册与资源；已经发送的邮件、已提交的数据库写入不随卸载消失。

## 1. 配置树决定实际运行什么

dsh 的接入面包括 profile、bundle、CLI 与 SDK；它们组装的对象是可运行的插件图。配置顺序为有序 bundle，再叠加 profile patch、home patch 与调用级 CLI `--patch`。按 id 匹配的 patch **替换整份 config，而非深合并**。这些在旧点已经存在，不是九月新增。[旧版架构](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/architecture.md)、[当前架构](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/architecture.md)

例如作者构造的配置反例：基线 config 同时设置超时与网络限制，上层按相同 id 只写超时。若集成者误当深合并，就会以为网络限制仍被保留。这个例子不是 dsh 漏洞复现；它说明证据应绑定解析后的配置和来源，而不能只记 profile 名称。新 Plugin Manager 启用 bundle 时会把它追加到有序列表末尾，也可能改变覆盖顺序。

## 2. 生命周期管理没有整批事务保证

九月的关键变化集中在启动与持久管理：

| 日期与固定变更 | 公开行为 | 集成时应处理的边界 |
|---|---|---|
| 9 月 9 日，串行初始化 | AgentLoop 等待 `agent/created` 完成后处理排队工作，失败执行创建清理 | 插件已挂载不等于 Agent 已准备好 |
| 9 月 9 日，撤回事务式 reload | 普通 Loader group 保留已成功的兄弟项，后续 HMR 不做整批回滚 | 初始启动另有 required-entry 策略，不能把所有失败混为一种 |
| 9 月 14—16 日，Plugin Manager / YAML HMR / Creator | 管理当前 profile 的持久插件；HMR 是否启用由 YAML 配置决定 | 变更可影响该 profile 下所有会话，Host 代码不受工作区 sandbox 自动保护 |

对应不可变依据为[串行初始化](https://github.com/deepseek-ai/deepseek-harness/commit/9b7a8ccc9fabc2e87386acf7f8b0741baf978022)、[撤回事务式 reload](https://github.com/deepseek-ai/deepseek-harness/commit/e07f41d5fd8ca172287fda0f923b4d1f69c592f3)、[Plugin Manager](https://github.com/deepseek-ai/deepseek-harness/commit/98b92b683c39fc60771daa774492105c2d3e8076)、[YAML HMR](https://github.com/deepseek-ai/deepseek-harness/commit/abd765a6001ff9d9c9772b8b407e0b7f18fe25ab) 和 [Creator 持久插件流程](https://github.com/deepseek-ai/deepseek-harness/commit/ed32f57f88ef6bba983e30a0b434fe5d77e5773b)。这些日期是提交日期，不是对所有用户的功能上线日期。

当前 base 默认启用 config-only HMR，headless/SDK/ACP 默认禁用，sdk-minimal 省略；profile patch 仍可覆盖。Creator 改为通过 Plugin Manager 安装持久插件，旧模型工具 `cordis_define/run/stop/undefine` 不再作为该组工具提供，但程序化与浏览器动态生命周期仍在。不能据此说整个动态 runner 已删除。

## 3. 两条执行路径，两个信任边界

`run_code`的执行后端与动态插件使用的`node:vm`是两条路径，不能统称为同一种安全沙箱。固定源码支持的区分如下：

| 执行路径 | 历史点 | 当前点 | 可作出的结论 |
|---|---|---|---|
| 动态 Cordis Host | `node:vm` realm | 关键 `sandbox.ts` 逐字节未变 | 源码明确不是 containment；宿主 realm 的 helper 仍可成为逃逸路径 |
| 模型 `run_code` / PTC | 每次创建 Node worker thread，明确不提供宿主安全隔离 | 每次创建独立 Node 进程，经平台 OS sandbox 策略启动 | 隔离强度取决于平台 backend 与 mode；受限模式缺少 backend 时失败 |

9 月 12 日的 [PTC 进程后端变更](https://github.com/deepseek-ai/deepseek-harness/commit/75ed8da3e0c9103b3b2174b2981b7129e1fba21d) 将旧 worker 后端改为子进程；同日另一个提交[统一 PTC 命名](https://github.com/deepseek-ai/deepseek-harness/commit/7c9bb5914cedec80e46197a8c894037fcfd12faf)。变更已进入上述 9 月 17 日版本，本轮没有穷举它首次进入的发布 tag。动态 Host 的 `node:vm` 则没有随之成为安全虚拟机。[动态 Host 源码](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/extensions/cordis-host-runner/src/sandbox.ts#L1)、[旧 worker 文档](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/packages/code-runtime/code-runtime-worker-thread/README.md)

新版 PTC 仍允许直接使用 Node API，文件、网络和子进程访问受所选 OS sandbox 约束；桥接子工具则继续走工具注册表的可见性、审批和日志规则。默认 `timeoutMs=120000`、上限 `600000` 是包括审批与子工具等待的经过时间，不是 CPU 计量；V8 heap cap 也不是整棵进程树的内存上限。宿主管理进程范围，并在取消、超时及正常结束后清理；但 fallback 平台上逃离该范围的后代可能残留。这些是文档和源码契约，未经过本书实测。[PTC Node 文档](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/ptc-runtime/ptc-runtime-node/README.md)

## 4. 一次安装失败会留下什么

Plugin Manager 的恢复范围比“插件可回滚”具体得多。下面依据当前文档整理的是失败语义，不是执行日志：[Plugin Manager 固定版文档](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/packages/boot/plugin-manager/README.md)

```text
快照 package.json / pnpm-lock.yaml → pnpm 安装 → bundle 校验
  安装失败或取消：恢复这两个文件；下载物、日志等可能保留
  安装及校验成功：安装阶段完成 → 按选择启用 bundle
    后续启用失败：不撤销已完成安装，保存状态也可能已改变
删除：取消 bundle 选择 → 卸载注册 → pnpm remove
  任一步失败：停止后续步骤，保留已完成修改，不自动重新启用
```

依赖 build-script 批准另有持久状态，可能在安装失败后保留；服务会校验待批准包名，却不验证“用户已在对话中同意”是否真实。已安装 Host 代码在进程内、工作区 sandbox 外执行。因此作者建议把插件安装授权、依赖构建脚本授权和普通工具授权分别记录，并在失败后检查实际文件与加载状态。这里不能承诺安装、热重载或业务副作用全事务回滚。

## 5. 流式显示与持久会话也有时间差

9 月 1 日的持久化调整把 `agent/assistant-stream` 用作进程内瞬态流，完整紧凑流在最终 `assistant/message` 或 `assistant/attempt` 中保存。settlement 前进程硬退出，不会留下这一尝试的完整 durable stream。历史会话沿相邻版本链迁移，写打开产生新版本文件，不覆盖旧 generation。[流式持久化变更](https://github.com/deepseek-ai/deepseek-harness/commit/f99b06eaed81d6fe4fc64d44687450e18ef68a67)、[会话迁移变更](https://github.com/deepseek-ai/deepseek-harness/commit/d1521ea7838f19a78a9cca7b4a93622d301149bb)

适配器因而需要区分“UI 已显示的增量”与“已经落盘的尝试记录”。桥接工具的逐次开始/完成追踪在旧版已存在，当前 PTC 使用 `tool/ptc-dispatch-start` / `tool/ptc-dispatch`；不要把上游已有事件全部写成企业尚需自建。[旧工具目录](https://github.com/deepseek-ai/deepseek-harness/blob/cd5ef8148158c3a752a658978873241fdf8e2bbc/docs/tool-catalog.md)、[当前工具目录](https://github.com/deepseek-ai/deepseek-harness/blob/ddefc45fbc7f8e46dd73185e68295696d1297887/docs/tool-catalog.md)

## 6. 设计判断与适配责任

dsh 可供观察和修改的源码范围包括组合、加载、执行后端及会话语义，适合检验运行时变体；preview 接口和部署责任仍需进入选择条件。下表是作者建议，不是上游原生保证：

| 原生能力 | 平台映射 | 平台需补建或核验 | 缺失时的降级 |
|---|---|---|---|
| 有序配置与插件生命周期 | 固定运行版本及配置来源 | 导出解析图、hash，审查扩展更新 | 不允许自动变更生产 profile |
| 工具与 PTC 子调用事件 | 动作及结果记录 | 关联审批、产物与外部副作用 | 缺关键证据时转人工处理 |
| Plugin Manager 持久管理 | 安装、启用、删除的分阶段状态 | 包来源/签名策略、实际残留检查 | 隔离 profile，修复后再启用 |
| session migration | 历史记录版本关联 | 旧会话兼容与崩溃窗口测试 | 保留旧 generation，拒绝无证据恢复 |

平台适配器连接的是 Agent 运行组件；PTC 子进程与 OS sandbox 才是代码执行边界。用于实验的可变插件与评价、发布权限应处于不同信任域，这是一项按风险实施的作者设计建议，并非 Cordis 会自动建立的治理能力。功能分层与信任域的共同定义见第十八章及第二十四、二十六章。

# 第十七章 OpenHands：Agent 与执行 Runtime 分离

> 资料截面：2026-09-19。历史 Runtime 以 0.62.0 固定源码说明；当前产品面为 Agent Canvas 1.20.0 与 Software Agent SDK 1.49.2，两条版本线均在 9 月 17 日发布。本轮为源码、文档及发布记录核对，未部署 Docker/Kubernetes 或实跑模型任务。[Canvas 1.20.0](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0)、[SDK 1.49.2](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2)

OpenHands 的决策与执行分离原则仍值得借鉴，但原章把旧类名写成了当前架构。理解现在的接入面，需要区分产品应用、Agent SDK、Agent Server 和执行环境；不能只看到 `Runtime` 就推断它与 Codex core 或 dsh 运行组件承担相同责任。

## 1. 历史结构保留在历史版本中

0.62.0 的 `Runtime` 接收并订阅 `EventStream`，客户端通过 HTTP 把 action 交给 `ActionExecutor`，后者管理 shell、browser 和插件并返回 observation。原章的下列图可以定位到这一历史实现：[旧 Runtime README](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/README.md)、[旧 ActionExecutor](https://github.com/OpenHands/OpenHands/blob/7fbb48c40679afd674970966b96185657d92a487/openhands/runtime/action_execution_server.py)

```text
历史 0.62.0：
Agent → Action → EventStream → Runtime client → ActionExecutor
      ← Observation ←─────────────────────────────────────┘
```

应用 1.0.0 在 **2025 年 12 月 16 日**已宣布使用新的 software-agent-sdk；8 月 27 日 README 也已把应用仓库定位为 Agent Canvas，把 Agent、tool、conversation、workspace、events 及 REST/WebSocket server 契约归给 SDK。因此，“SDK 分离”属于旧稿漏收的结构，不是九月才发生的迁移。[应用 1.0.0 发布说明](https://github.com/OpenHands/OpenHands/releases/tag/1.0.0)、[8 月 27 日 README](https://github.com/OpenHands/OpenHands/blob/b50c60c6728e2ce123ccb6e125bee3eb88ac87d1/README.md)

## 2. 当前应该连接哪一层

下表前两列为固定版本可见的职责归纳；最后一列是作者给适配器的设计建议。

| 接入对象 | 当前公开职责 | 适配器连接的边界 |
|---|---|---|
| Agent Canvas 1.20.0 | 产品 UI、profile 与 automation 等应用组织 | 面向用户的工作入口，不以 UI 版本替代 SDK 版本 |
| Software Agent SDK 1.49.2 | Agent、conversation、workspace、events 与工具契约 | 控制决策循环及会话，保留原生事件 |
| Agent Server | 远程会话的服务接口与运行环境管理 | 通过服务控制会话，另查其执行部署模式 |
| workspace / conversation runtime | 代码与工具实际运行的位置 | 检查文件、网络、凭证、进程和租户边界 |

SDK 的 `Conversation` 工厂根据 workspace 类型创建 `LocalConversation` 或 `RemoteConversation`：前者在本地运行 Agent，后者连接远端 Agent Server。[1.49.2 固定源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-sdk/openhands/sdk/conversation/conversation.py#L34) Canvas 1.20.0 的 `package.json` 精确依赖 TypeScript client 1.49.2，直接说明应用与 SDK 版本不能混写。[Canvas 固定依赖](https://github.com/OpenHands/OpenHands/blob/9737f713616a1e452f822c2967f0e2c8bf2dc308/package.json)

这些源码开放了会话工厂、协议与容器供给等检查点，但本轮并未审计所有实现。自己运行 Agent Server 也不等于自动容器隔离；基线 README 已提示本机直接运行可访问本地文件系统。模型推理的数据流仍取决于所选模型服务，不能由“开源、自管”两个词推出完全离线。

## 3. 事件先保存，再通知订阅者

SDK 1.45.0 于 9 月 7 日发布，包含 9 月 2 日合并的 **persist-before-publish** 变更：先持久化事件，再向订阅者发布。同期迁入 TypeScript client，并加入 session socket 的非 Event envelope；因此不能把每条 socket 消息都当成可重放的持久事件。[持久化顺序变更](https://github.com/OpenHands/software-agent-sdk/commit/94fca578b720df758b9bbf8a2639511b303c78e6)、[socket envelope 变更](https://github.com/OpenHands/software-agent-sdk/commit/2ab274897ac5e2c66b0ba17e9a6d39367b769876)、[1.45.0 发布说明](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.45.0)

下表是作者根据该顺序提出的故障检查，不是本书实测结果：

| 故障窗口 | 应分别观察什么 | 不能直接推出什么 |
|---|---|---|
| 事件持久化失败 | 写入错误、订阅者是否收到通知 | UI 无消息不证明外部动作从未执行 |
| 已持久化，尚未发布时进程退出 | 日志中已有事件，客户端可能尚不可见 | 未收到通知不等于可重发同一动作 |
| 重连后补取事件，又收到迟到通知 | 用原生事件身份核对是否同一记录 | 两次传输不等于两次动作 |
| 收到 session socket 控制 envelope | 按消息类型路由 | 控制消息不能直接计入业务事件回放 |

persist-before-publish 缩小了“订阅者先看见、日志却没有”的窗口，并没有把外部服务写入和日志落盘合成一个事务，也没有自动证明投递恰好一次。若支付、发布或数据库写入已生效而结果尚未保存，仍须回读结果；这是第六章不确定提交问题在该实现中的具体落点。当前版本已经提供持久化能力，不能再笼统写成“进入企业平台必须从零补齐 durable state”。

## 4. 每会话容器是新 SDK 的具体模式

9 月 15 日发布的 SDK 1.48.0 引入按 conversation 作用域隔离的 runtime API/client、Kubernetes `AgentSandboxWorkspace` 和 profile secret 范围控制。9 月 16 日 1.49.0 增加 Agent Server 的 **per-conversation Docker containers** runtime mode。这是新 SDK/Agent Server 的新增模式，不是 OpenHands 首次支持 Docker。[1.48.0 发布说明](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.48.0)、[每会话容器变更](https://github.com/OpenHands/software-agent-sdk/commit/3ff6924d8564b3d47a22a6c7e71377a701ae014f)

紧接着的 1.49.1 修复 Docker conversation metadata route；1.49.2 修复旧会话 catalog 保留、重复扫描、proxy root path、workspace 创建与删除期间重启等问题。Canvas 1.20.0 则转发该容器配置，并更新 profile secret 选择与 automation 的 saved profile 选择。[1.49.1](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.1)、[1.49.2](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.49.2)、[固定 provisioning 源码](https://github.com/OpenHands/software-agent-sdk/blob/d128a786ee2ee570eb23ff5862ec148b43cfad0b/openhands-agent-server/openhands/agent_server/docker_runtime/provisioning.py)、[Canvas 1.20.0](https://github.com/OpenHands/OpenHands/releases/tag/v1.20.0)

因此采用时要同时记录 Canvas、SDK、Agent Server 与镜像版本，检查恢复后会话目录、容器及工作区是否仍指向同一对象。容器的 mount、宿主 socket、网络与凭证配置决定实际隔离；不能从每会话一个容器推出多租户隔离已经验证，更不能把 Docker socket 无限制暴露给生成代码。

## 5. 针对当前结构的运营检查

以下是作者建议的检查项，采集主体是部署与事件服务，不由 Agent 自报：

| 检查 | 应保留的证据 | 失败后的处理 |
|---|---|---|
| 创建与恢复会话 | conversation ID、镜像版本、runtime mode、workspace 标识 | 拒绝在身份或目录错配的环境继续执行 |
| 日志与订阅一致性 | 持久事件、传输通知及最后确认位置 | 补取并去重；不以重发工具调用弥补通知缺口 |
| 取消与容器回收 | 会话终态、容器状态、后代进程与清理结果 | 清理未完成时保持待处理，不冒充已取消干净 |
| profile secret 范围 | 注入对象、权限范围与撤销记录 | 范围不符时停止新动作，轮换或撤销凭证 |

这些检查把“开放可观察”转成待验证的操作条件。源码能显示应当发生的顺序；部署中的故障注入才可检验存储失败、重启和资源泄漏。

## 6. 设计判断

OpenHands 适合作为决策循环、会话服务与执行环境分离的源码案例。是否自运维全栈，应取决于组织是否需要这些控制点，以及镜像、调度、恢复和升级责任能否承担；本轮没有成本数据，不能声称其成本必然高于托管产品。第十八章统一解释 Agent Runtime 与 Execution Runtime 的责任，第二十六章再把它们映射到企业功能层和信任域。

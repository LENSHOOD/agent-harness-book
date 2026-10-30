# OpenHands 章节处置与验证

访问及核对日期：2026-10-29。责任范围仅为第十七章及本目录 `openhands.*` 文件。未修改共享登记表、目录或其他章节；未提交、推送、部署或运行上游代码。证据在正文综合前持久化；按书稿八节合同组织，不生成额外独立报告。

## 基线与取回来源

主体为既有固定 SDK `1.49.2 / d128a786ee2ee570eb23ff5862ec148b43cfad0b`，exact-commit git fetch 取回。Canvas `1.20.0 / 9737f713616a1e452f822c2967f0e2c8bf2dc308` 的 package.json 和历史 Runtime `0.62.0 / 7fbb48c40679afd674970966b96185657d92a487` 的 README 通过不可变 raw URL 取回。未检查最新 release，不把访问日写成产品最新状态。

[openhands.sources.jsonl](openhands.sources.jsonl) 是完整逐项来源清单，含 `source_url`、仓库相对 `capture_path`、`sha256`、字节数、commit、实际访问日、取回方式和正文引用标记。28 个捕获来源均在忽略目录 `publishing/work/architecture_20261029/openhands/`；正文引用 27 项。去掉 `#anchor` 后，未匹配正文 URL 为零。

覆盖来源：SDK README；Conversation 工厂、local/remote 实现及 state；Agent/AgentBase；AgentContext、View、LLMSummarizingCondenser；ParallelToolExecutor；MCP tool；Plugin/ResolvedPluginSource；confirmation policy；Server README、Docker registry/provisioning/routes；SecretRegistry 与 profile；TaskToolSet/TaskManager；session socket；Laminar 集成；Canvas 依赖文件；历史 Runtime。另读 DelegateExecutor 作为对照，不把它当作当前示例的主要委派路径；其证据和捕获仍保留。

## 实质改写与纠正

正文改为 Agent 配置、Conversation 状态、Workspace 与 Server 部署的责任分解，并以一次修复仓库错误的任务走过整个调用链。明确远程 Conversation 的 Agent 循环可以驻留远端；每会话 Docker mode 是控制面供给一个容器内 Agent Server，不能与旧版本仅传 action 的 Runtime 图混写。旧类名仅留历史定位段落，迁移发布时间线不再构成正文主体。

纠正一处既有事实错误：Canvas 1.20.0 固定 package.json 依赖 `@openhands/typescript-client: 1.49.1`，原稿写成 `1.49.2`。源码直接显示两条版本线不可混写。

委派正文使用该基线示例采用的 `TaskToolSet → TaskExecutor → TaskManager → LocalConversation`。保存了关键边界：子会话共享 workspace 而不自动得到独立 OS 身份；task resume 依赖内存映射，不保证进程重启后任务索引恢复；非 FINISHED 返回错误和部分结果；未配 confirmation_handler 会继续等待确认的子动作；此同步 task 路径未见父 cancellation token 下传。旧 DelegateExecutor 也存在无 handler 继续执行的分支，但未用它代替 TaskManager 解释现行示例。

保留并细化原稿的 persist-before-publish、socket envelope 非全部持久 Event、外部动作与日志无联合事务、重连补取去重、容器/工作区/身份错配、凭证范围与取消清理责任。新增本地 visualizer 可先于持久化的具体边界，并注明 Python RemoteConversation 使用何种 socket 路由必须单独核对，未声称所有客户端已切换 session socket。

旧稿关于 1.48 Kubernetes Workspace、1.49 per-conversation Docker 及后续补丁的版本时间线，保留在原 `research/audits/review_20260919/` 审计材料；本轮不重做发行史。正文直接说明固定 1.49.2 代码的实际供给和恢复结构，不把补丁发布日期作为架构说明。历史 0.62 Runtime 只支撑历史对照。

## 已完成验证与缺口

[openhands.validation.json](openhands.validation.json) 记录：4142 个汉字、八个共同小节、32 条证据；首标题与 Git 基线一致；27 个正文来源全部匹配证据及 capture；SHA-256 全匹配；全部短引文在捕获文件中逐项命中，每个来源累计引用不超过 25 个空白分隔词；text 图及围栏检查通过，`git diff --check` 通过。没有原第十八章及以后章节的硬编码引用，无须在这两章追加顺延变更。

未部署 Docker/Kubernetes、调用模型、验证多租户隔离、进行容器回收或事件存储故障注入、实际运行 task 恢复或凭证泄露测试。涉及子任务取消的结论限定于已读的同步 TaskManager 路径，不扩大到所有扩展实现。尚无成本或独立效果评估数据。作者任务走查不是已运行示例，全书生成与部署验证交由父任务。

浏览器按 ego-browser 技能在 TaskSpace 153 的 p5 访问固定 SDK README；未创建/结束共享 TaskSpace，未操作其他页面，未升级 Ego Lite。

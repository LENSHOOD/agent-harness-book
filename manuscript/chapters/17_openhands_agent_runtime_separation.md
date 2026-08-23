# 第十七章 OpenHands：Agent 与 Runtime 分离的开放架构

> 产品快照截至 2026-08-22。

OpenHands 被选为第五主案例，不是因为它一定拥有最大用户规模，而是其开放代码、论文传统和 Agent/Runtime 分离对企业架构最具教学价值。它补足了四个商业产品公开实现透明度不足的问题。

## 1. Action—Observation—Event

OpenHands 用 action 表示 Agent 意图，用 observation 表示环境反馈，并通过事件流连接会话。[OpenHands Paper](https://arxiv.org/abs/2407.16741) 这个协议边界允许替换 Agent 策略、模型和 Runtime，也允许记录、重放与插入策略。

关键不是类名，而是模型不直接操作宿主。Runtime 接收规范化动作，在受控环境执行并返回结构化观察。终端输出、文件变化、浏览器状态和错误都成为事件。

## 2. Runtime 生命周期

OpenHands Runtime 可以运行在 Docker 或远程环境中，负责初始化、执行、文件传输和 teardown。[OpenHands Runtime Architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime) 这把高风险计算面从 Agent server 分离，也为企业替换 Kubernetes、VM 或专用沙箱提供接口。

远程 Runtime 并不自动安全。镜像供应链、网络、凭证、租户隔离和 artifact 导出仍需控制面治理。协议只提供插入控制的机会。

## 3. 开放平台的价值

开放实现允许研究者比较不同 Agent、模型与工具，并在 SWE-bench 等环境中复现。它也暴露生产化成本：事件 schema 演化、Runtime 兼容、部署复杂度、持久化与 UI 都需要持续工程。

OpenHands 的设计比“一个 Python while loop + shell”更适合作为企业参考，是因为它天然支持执行面的独立扩缩、故障隔离和审计。但企业仍需要补充统一身份、策略即代码、证据包和供应商 runtime adapter。

## 4. 与其他案例的互补

Claude Code 展示终端产品与扩展生态，Codex 展示协议化核心与多客户端，Cursor 展示 IDE/云环境，DSH 展示可组合插件树；OpenHands 则把 Agent 与计算 Runtime 的边界公开化。五者共同说明，Harness 不是单一框架，而是一组控制面和数据面职责。

## 5. 企业采用方式

最稳妥的采用不是 fork 全部代码并深度改造，而是把 Runtime protocol、event model 和 workspace lifecycle 作为可替换组件接入。上层平台生成 canonical task，映射为 OpenHands session；下层接收 evidence package，再由企业完成门决定提交。

当未来自研 Agent loop 时，可以保留 Runtime 与控制面，只替换决策策略。这正是开放架构的长期价值。

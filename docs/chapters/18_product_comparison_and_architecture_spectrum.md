# 第十八章 横向比较：不同 Harness 的答案

> 比较快照截至 2026-08-22。矩阵描述公开能力与设计重心，不等同于质量排名。

五个主案例并非五套互斥架构，而是对相同责任作出不同取舍。

| 维度 | Claude Code | Codex | Cursor | DSH | OpenHands |
|---|---|---|---|---|---|
| 主要交互面 | 终端/SDK | CLI、IDE、App、云 | IDE、云 | Runtime/CLI | Web/SDK/研究平台 |
| 核心重心 | 薄 loop、扩展与安全 | 协议化核心、工作树、策略 | 动态上下文、IDE 与 VM | 插件树与生命周期 | Agent/Runtime 分离 |
| 上下文 | 项目规则、压缩、tool search | 会话与 compaction | 动态发现、索引、文件化结果 | 可替换策略 | 事件与观察 |
| 执行隔离 | OS sandbox | sandbox/worktree/cloud | 本地与 cloud VM | sandbox service | Docker/remote Runtime |
| 扩展 | hooks、skills、MCP、subagent | tools、MCP、App Server | MCP、IDE/云能力 | Cordis plugins | Agent/Runtime/tool 扩展 |
| 独特价值 | 开发者终端闭环 | 多客户端控制面 | 交互原生性 | 可变运行时载体 | 开放协议边界 |

## 1. 薄与厚不是优劣

Pi 代表极薄 Harness：少量工具、依赖 shell 和文件、刻意不内置复杂 plan、permission UI 或多 Agent。这提醒我们，功能越多不必然越可靠。相反，企业场景要求身份、审计、策略和恢复，厚控制面又不可避免。

合理分层是：模型面对的动作面保持小而清晰，运行时内部可以很厚。复杂度应服务于确定性边界，而不是把更多抽象暴露给模型。

## 2. 本地与云

本地 Agent 接近开发者环境、启动快、交互自然，但宿主秘密和环境漂移风险高。云 Agent 易隔离、并行和恢复，却有环境准备、数据上传、凭证代理与成本问题。现代产品通常走向混合：控制面统一，本地与云作为不同 execution profile。

## 3. 开放与闭源

开源可验证协议、策略和沙箱实现，闭源产品可能拥有更成熟模型适配和运维数据。企业选择不应只看许可证，而要看可导出的 trace、artifact、策略控制、数据边界、版本可固定性和退出路径。

## 4. 共同收敛

五者正在共同收敛到：持久会话、按需上下文、结构化工具、隔离执行、审批策略、MCP/扩展、多 Agent、可观测和验证。差异逐渐从“有没有工具调用”转向每个层的质量与组合方式。

## 5. 选择原则

交互式个人 coding 优先考虑 IDE/终端体验；后台并行任务重视云工作区和协议；强定制企业平台重视开放 Runtime、策略与事件；进化研究重视可组合配置和评测接口。没有一个产品应同时作为组织的身份源、策略根、证据库和唯一执行 runtime。

因此企业架构的目标不是选出永久赢家，而是定义稳定的 canonical contracts，让五类 runtime 都能被接入、比较和替换。

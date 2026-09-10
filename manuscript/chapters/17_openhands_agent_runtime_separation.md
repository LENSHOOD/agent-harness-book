# 第十七章 OpenHands：Agent 与执行 Runtime 分离

> 资料截面：2026-08-27。OpenHands 是快速演进的开源项目；本章以官方文档和论文描述的稳定边界为准，不承诺具体类名长期不变。

OpenHands 对企业架构最有价值的启示，是明确区分“产生 Action 的 Agent”与“在环境中执行 Action 的 Runtime”。官方 Runtime 架构中，backend 创建 Agent 和 EventStream，Docker 容器内的 Action Executor 初始化 shell、browser 和插件；EventStream 把 Agent 的 Action 送往 Runtime，再把 Observation 返回 Agent。[Runtime architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime)

## 1. Action—Observation 作为系统脊柱

```text
user/task → agent controller → Action → EventStream
                                  ↓
                              Runtime API
                                  ↓
                         shell/browser/files
                                  ↓
             Observation → EventStream → next decision
```

这个边界让模型和执行环境可以独立变化。同一种 Action 语义可以落到本地、Docker 或远程 runtime；同一 runtime 也可服务不同 Agent。OpenHands 论文把平台定位为面向软件开发 Agent 的开放基础设施，而非单一模型 wrapper（模型封装器）。[OpenHands paper](https://arxiv.org/abs/2407.16741)

事件流的价值是统一交互，但不等于天然耐久。若 event（事件）只在内存里、外部动作没有幂等键，进程崩溃仍会产生第六章所述的不确定提交窗口。企业 fork（分支）或二次封装时应逐项验证：事件是否持久化；是否可去重；重放是否会再次执行副作用；取消是否传播到容器进程树。

## 2. Runtime 是能力边界，不只是 Docker 名称

官方文档强调 sandbox（沙箱）带来的安全、一致性、资源控制、隔离和可复现性，并采用 backend—runtime client/server 结构。[Runtime architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime) 但“运行在容器中”本身不能证明安全。容器挂载、宿主 socket、网络、内核能力、secret（密钥）和镜像供应链共同决定真实边界。

一个典型反例是把 Docker socket 挂入 Agent 容器。表面上每个任务都有容器，实际上 Agent 可控制宿主 Docker daemon，隔离边界被绕过。企业 profile（配置画像）应显式声明 mount（挂载）、network（网络）、user namespace（用户命名空间）、resource limit（资源上限）和 credential injection（凭证注入），并通过对抗测试验证，而不是只检查 runtime 类型字符串。

## 3. 开放平台的可替换性

OpenHands 的开放实现适合回答专有产品难以回答的问题：Action/Observation 如何序列化、runtime 如何启动、插件在哪里执行、事件如何流动。它也因此适合作为自研平台的参考实现或兼容测试对象。可替换性应落在契约，而不是 fork 大量内部类。

建议 adapter 只依赖五类稳定语义：启动/恢复会话、流式事件、审批或输入、取消、artifact（产物）收集。原始 OpenHands event 应作为 provenance（溯源）保留。平台把它映射为 canonical Action（标准动作）、Observation（观测）和 Artifact。这个映射见第二十六章。上游 schema（模式）改变时，契约测试应在发布前失败。

## 4. 失败模式与运营负担

开放 runtime 让组织获得控制，也把镜像构建、冷启动、浏览器依赖、资源回收、日志容量和多租户隔离交给自己。需要分别观测：

| 指标 | 含义 | 典型告警 |
|---|---|---|
| runtime provision success | 环境是否成功创建 | 镜像/调度故障突增 |
| action transport gap | Action 是否都有 Observation | 事件缺口或重复 |
| orphan process count | 取消后是否残留进程 | 资源与副作用泄漏 |
| workspace reproducibility | 相同版本能否重建 | 浮动依赖或镜像漂移 |
| tenant boundary violations | 是否发生跨租户访问 | 任何非零即事故 |

这些指标不能由 Agent 自报，必须在 control/execution plane（控制/执行平面）采集。Agent 说“环境坏了”，只是诊断候选。

## 5. 与其他产品的互补关系

OpenHands 不必与 Claude Code 或 Codex 二选一。企业可以借鉴它的 Agent/Runtime 边界，把供应商 Agent 放在隔离工作区里执行，再由外部 evidence plane（证据平面）验证。反过来，如果组织主要需要成熟 IDE 体验和模型特化工具，自行运营 OpenHands 全栈可能得不偿失。

## 6. 设计判断

OpenHands 最可迁移的原则是决策者、事件总线与效果执行者分离。环境实现可替换；Action/Observation 是可观察接口。其风险在于把“开源可见”误当成“生产完备”。进入企业平台仍需补齐 durable state（持久状态）、策略根、凭证代理、completion gate（完成闸门）和版本治理。本章的分离结构将在第二十六章被提升为多 runtime 参考架构。

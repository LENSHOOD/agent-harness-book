# 第十六章 DeepSeek Harness：可组合运行时与进化载体

> 产品快照截至 2026-08-22。DSH 官方仓库仍应按 developer preview 看待。

DeepSeek Harness（DSH）最重要的贡献，不是已经实现了一个可信的自主进化 Agent，而是把 Harness 本身设计成可组合、可替换、可卸载的运行时。它让“运行时结构可以变化”成为一等能力，也因此把自我进化的安全与验证问题推到台前。

## 1. Cordis 插件树

DSH 运行实例建立在 Cordis 插件树上。模型适配、工具、持久化、默认 loop 等都可作为插件装配。[DSH Architecture](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/architecture.md) Cordis 用 context、service dependency、typed event/waterfall 与 effect ownership 管理组件生命周期。[Cordis Primer](https://github.com/deepseek-ai/deepseek-harness/blob/master/docs/cordis-primer.md)

所谓时间可组合性，是组件卸载时能撤销由其注册的 effect；空间可组合性，是组件按依赖和所在 context 激活。相比“启动时注册一堆全局回调”，这种设计更适合长生命周期、热装配和实验变体。

## 2. 分层配置与 scope

DSH 通过 profile、bundle、用户 patch、home patch 和临时 overlay 组合配置，并区分 host scope 与 agent scope。不同会话可拥有不同模型、工具、persona、压缩策略和扩展，同时共享宿主服务。

这给企业平台一个有价值的方向：配置不是一个巨大 JSON，而是带来源、优先级、生命周期和撤销语义的 patch。每个实验变体可以绑定 scope，避免修改污染所有租户。

## 3. Tool Runtime 与 Code Mode

DSH 的工具运行时支持将工具生成 SDK 视图，通过 `run_code` 让模型组合调用；嵌套调用仍回到受控工具管线，只有显式打印或返回的数据进入外层上下文。[DSH Code Mode](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/core/tools/README.md)

这兼具 CodeAct 的表达力与集中 policy enforcement。风险在于生成 SDK、sandbox 和嵌套调用的语义复杂度，必须防止通过解释器、网络或输出通道绕过工具策略。

## 4. 可变不等于会进化

一个可热替换插件的系统只是 evolution substrate。可信进化还需要轨迹采集、失败归因、候选生成、独立评测、统计门禁、canary、回滚和审计。Agent 不能修改给自己评分与授权的根信任。

近期 Self-Harness、Gated Semantic Quality-Diversity、Living-Harness 和 Hierarchical Self-Improvement 等工作分别探索 Harness 候选生成、确定性门禁、经验状态图和层级改进，但仍是快速发展的研究方向。[Self-Harness](https://arxiv.org/abs/2606.09498)

## 5. 企业取舍

DSH 的优点是微内核式组合、生命周期所有权、scope 与配置 patch，适合做可实验的 Agent runtime。风险是抽象学习成本、插件依赖图、动态装配的可预测性和开发预览阶段的稳定性。

企业可借鉴 Cordis 的 effect ownership 与配置 provenance，而不必立即采用整个实现。若把 DSH 接入平台，应把可演化插件域与不可变控制面隔开：身份、策略、evaluator、审计与发布控制器不能由任务内 Agent 自行替换。

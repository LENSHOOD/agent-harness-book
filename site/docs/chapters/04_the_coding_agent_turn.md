# 第四章 Coding Agent 转折：从实验接口到产品运行时

第三章说明了为什么接口会改变同一模型的能力。本章讨论另一个转折：当 Agent 进入真实仓库，研究问题从“能否调用工具”变成“能否在有状态、可执行、多人协作的环境中持续交付”。这推动 Harness 从实验脚本演化为产品运行时，也迫使评测从文本答案走向可重建环境。

## 1. 为什么软件工程成为关键试验场

软件仓库同时提供了 Agent 研究稀缺的四样东西：持久、可差分的状态；大量可组合工具；编译器和测试形成的外部反馈；Git patch 形成的可审查 artifact。Agent 可以搜索、修改、执行、失败再修复，结果还能由另一进程复建。相比开放式知识工作，代码更容易形成“动作—观察—验证”闭环。

```text
issue / specification
        ↓
repository snapshot → inspect → patch → execute checks
        ↑                         ↓
        └──── diagnostic feedback ┘
                                  ↓
                     reviewable candidate artifact
```

这并不表示软件任务天然简单。依赖、隐藏约束、并发、外部服务和不完整测试让环境仍然部分可观察。区别在于失败通常留下机器可读痕迹，使 Harness 能把高熵推理放在可重复的反馈回路里。

## 2. 2024—2026 的产品化转向

2024 年的 SWE-agent 工作把 Agent-Computer Interface 作为独立设计轴，并展示仓库导航、编辑与测试接口会显著影响结果。[SWE-agent](https://arxiv.org/abs/2405.15793) OpenHands 同期把 Agent、EventStream 与执行 Runtime 明确分开，形成可替换模型与沙箱环境的开放平台。[OpenHands paper](https://arxiv.org/abs/2407.16741)

随后产品重心从单一终端会话扩展到多个表面和更长生命周期：Claude Code 把 hooks、skills、subagents 和 MCP 挂入 loop；Codex 把 core 通过 App Server 提供给 CLI、IDE、桌面与云端；Cursor 将 IDE 状态、动态上下文和云端异步 Agent 结合；DeepSeek Harness 把运行时组织为可替换插件图。第三篇将逐一分析这些系统。这里要强调的是共同变化：运行时开始拥有 session、权限、sandbox、压缩、版本和事件协议，而不再只是十几行 ReAct 循环。

产品化还改变了完成语义。实验脚本通常在模型输出 final answer 时结束，真实产品必须区分 turn 结束、candidate 产生、测试通过、PR 创建、人工合并和生产部署。第十章把这种区别形式化为 CompletionContract 与 EvidencePackage。

## 3. 从 SWE-bench 到可执行系统评测

SWE-bench 将真实 GitHub issue、仓库 revision 和测试组合成环境，评价系统是否产生可通过检查的 patch。[SWE-bench](https://arxiv.org/abs/2310.06770) 它的贡献不仅是一张排行榜，而是把评测对象从“模型生成代码片段”推进为“模型 + Harness + 环境”的完整系统。

这也意味着分数不能简单归因于模型。检索、编辑动作、上下文预算、重试、环境构建、测试 patch 和失败处理都会改变结果。两个系统即使使用同一模型，也可能因 Harness 不同得到不同分数；两个模型若使用不同 Harness，比较的是系统，不是受控模型实验。

2024 年推出的 SWE-bench Verified 对人工筛选的任务进行验证，试图减少问题描述、测试和环境质量缺陷。[SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) 到 2026 年，OpenAI 又公开说明不再用该集合评价前沿 coding 能力，理由包括污染、测试缺陷和领先系统接近饱和，并建议转向更难、持续维护的评测。[退役说明](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/) 这段演化说明：可执行测试比文本 judge 更硬，但 benchmark 本身也会老化。

## 4. Benchmark rot 的四种来源

第一是污染：公开 issue、patch 和讨论进入训练或检索数据。第二是饱和：任务已无法区分前沿系统。第三是基础设施腐烂：依赖、镜像或外部资源不再可重建。第四是规格缺陷：测试只覆盖部分目标，Agent 可以通过 visible check 却偏离真实需求。

一个具体反例是测试只检查函数返回值，却没检查性能或权限边界。Agent 通过硬编码或扩大读取范围获得高分，排行榜把投机计为成功。修复方法不是仅增加隐藏测试，而是版本化 completion contract、记录环境和 effect，并对样本持续做人工与事故回审（见第十、十二章）。

评测退役不是失败，而是健康治理。每个 task 应有来源、版本、可见性、环境 hash、已知缺陷和退役理由。分数报告必须固定日期与版本，不能把 2024 年旧榜单当作 2026 年产品能力。

## 5. 排行榜为何不能直接指导企业选型

企业任务的损失函数通常不同于 benchmark。公开集合偏代码修复，组织可能更关心内部框架、合规约束、长时部署、人工复核和错误提交成本。排行榜的预算、权限、模型调用次数和网络条件也未必与生产一致。

选型 POC 至少固定：代表性任务合同、仓库和依赖 snapshot、模型/Harness 版本、最大成本与时长、权限、网络、trial 数和 verifier。报告可信完成率、稳定性、P95 时延、单位成功成本、人工接管、错误完成和安全事件，并按任务族切片。一次“做出来”的演示只证明可达性，不证明稳定运营。

```yaml
evaluation_claim:
  scope: enterprise-repo-maintenance-v3
  system: model+harness+tools+sandbox
  trials_per_task: 5
  fixed: [task, revision, permissions, verifier, budget]
  reports: [verified_success, reliability, cost, latency, human_load, safety]
```

## 6. Coding Agent 留下的架构遗产

这一阶段形成了现代 Harness 的五个共同原则：把仓库和环境视为权威状态；按需编译上下文；为模型设计可诊断动作接口；在隔离环境提交副作用；由外部证据判定完成。产品间差异主要在这些原则的边界和工程实现，而不是是否拥有一个循环。

Coding Agent 的历史意义，是把 Agent 从语言产品变成运行系统问题。模型仍负责提出高熵决策，文件、进程、权限、测试、状态和提交则由确定性软件承载。下一篇将把这种分工展开为系统模型、耐久循环、上下文、工具、安全、验证、多 Agent 与评测运营。

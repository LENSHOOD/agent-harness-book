# 第十二章 可观测性、轨迹与评测运营

> 本章状态：正文初稿 v0.1。

生产 Agent 不能只记录 prompt 与 final answer。真正决定结果的是一次跨模型、工具、环境、策略和人的分布式执行。可观测性的目标不是保存模型私有思维，而是重建可审计的因果链：系统当时看到了什么、采取了什么动作、依据哪个策略、改变了什么状态、用什么证据判断完成。

## 1. 轨迹是事件图

最小事件模型包括 model turn、tool request、policy decision、approval、execution、observation、artifact、checkpoint、delegation、verification 和 effect commit。事件使用稳定 ID、父子关系与 artifact 引用连接。长输出进入对象存储，trace 保存摘要、哈希和 locator。

```text
TraceEvent {
  run_id, span_id, parent_id, type, timestamp
  actor, model, tool, policy_version
  input_refs[], output_refs[]
  state_before, state_after
  cost, latency, status, error_class
}
```

对多 Agent，trace 是部分有序图；对可恢复任务，checkpoint 与 effect ledger 比聊天文本更重要。日志、审计和模型上下文应分开保存：上下文可压缩，运维日志可采样，安全审计则遵循不可篡改和保留策略。

## 2. 指标分四层

业务层衡量任务价值、人工节省和错误损失；任务层衡量完成率、部分完成、升级率和稳定性；运行层衡量 tool call、重试、上下文、成本、关键路径时延；安全层衡量越权请求、审批、注入、数据流违规和恢复。

平均成功率不足以运营。应按任务族、风险、模型、Harness 版本、工具、仓库规模和上下文长度切片，并同时观察 `pass@k` 与 `pass^k`。[Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 一次最佳表现适合探索能力，连续可靠性才接近生产体验。

## 3. 失败分类先于优化

失败至少分为：任务规范、上下文选择、推理计划、工具选择、工具执行、环境、权限、验证器、协调、外部依赖和模型能力。若所有失败都记作 `agent_failed`，团队只能凭直觉改 prompt。

归因应连接“最早可纠正事件”而非最后一个错误。测试失败可能源于错误 patch，也可能源于依赖未安装；过早完成可能源于完成契约缺失，而非模型不认真。允许多标签和置信度，保留人工纠正。

## 4. Eval 是持续运营系统

评测集由生产事故、人工升级、低置信度轨迹、能力边界和安全红队持续补充。Capability eval 探索不会做的任务，regression eval 保护已经会做的任务；高通过率能力题应转为回归题。[Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

每个 task 保存输入快照、reference solution、grader、环境摘要、可见性和退役原因。每次 Harness 变更都与稳定 baseline 做多 trial 对比，报告置信区间、成本和关键切片，而不是只看总分。

## 5. 在线监控与离线评测闭环

```text
production traces
  → privacy filtering
  → failure clustering
  → curated eval candidates
  → independent labeling
  → regression/capability suites
  → candidate harness evaluation
  → canary → production
```

线上反馈不能直接自动成为 prompt 或 memory，否则攻击内容和偶然偏好会固化。采集、筛选、标注和发布之间需要数据治理。用户满意度也不是唯一 reward：Agent 可能通过迎合、隐藏风险或减少必要确认提高短期评分。

## 6. Trace replay 的边界

模型调用和外部世界不完全可重放。可靠 replay 应固定输入、模型快照、采样参数、工具版本和环境镜像；对不可重放 API 使用录制响应或模拟器。Replay 用于定位差异，不应伪装成绝对复现。

隐私与安全同样重要。轨迹可能包含源码、PII、token 和模型生成的恶意内容。进入分析平台前执行分类、脱敏、租户隔离和最小保留；研究者访问 held-out 与生产数据要审计。

## 7. 运营仪表盘

一个有用的仪表盘回答：哪些任务失败最多；失败始于哪个层；哪个版本引入退化；自动完成是否真的减少人工总成本；成本上涨来自模型、上下文还是重试；哪些权限请求最常被拒；哪些 verifier 最不稳定。

最终，可观测性不是为漂亮 trace UI 服务，而是为三个闭环服务：事故恢复、工程归因和受控进化。没有可用轨迹，Harness 只能靠 anecdote 进化；没有独立 eval，轨迹优化又容易变成对历史样本的过拟合。

# 第十二章 可观测性、轨迹与评测运营

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

## 8. 一条可关联的真实事件

事件 schema 应允许大对象外置、敏感字段分级和供应商 payload 双轨保存。下面是工具调用完成事件的最小实例；它记录可观察结果，不保存模型私有思维链。

```json
{
  "event_id": "evt_01J8Z7",
  "run_id": "run_TASK2048_A3",
  "span_id": "tool_017",
  "parent_span_id": "turn_006",
  "type": "tool.completed",
  "timestamp": "2026-08-27T09:31:14.223Z",
  "actor": "runtime:codex",
  "tool": {"canonical": "repo.test", "provider": "exec_command", "version": "4"},
  "policy_decision": "pd_8821",
  "input": {"ref": "artifact:sha256:11ad...", "classification": "internal"},
  "output": {"ref": "artifact:sha256:90bf...", "exit_code": 1},
  "state": {"workspace_before": "git:8f31b6e", "workspace_after": "git:dirty:4e19..."},
  "latency_ms": 18241,
  "cost": {"compute_usd": 0.012},
  "status": "error",
  "error_class": "TEST_FAILURE",
  "vendor_payload_ref": "secure-artifact:sha256:772e..."
}
```

`event_id` 用于去重，parent 建立因果导航，workspace hash 连接状态变化，policy id 证明当时依据的规则。原始输出和供应商 payload 可能含源码或秘密，应放在更严格存储域；普通运营者只看到摘要和 locator。

## 9. Trace 完整性与采样

高流量平台会希望采样，但 effect、policy、approval、checkpoint、verification 和 commit 事件不能像普通 debug log 一样随机丢弃。可按重要性分层：审计骨架全量保留；大输出只保留 hash 与按风险设定的原文；性能 span 可按任务和异常自适应采样。

完整率可定义为 `具有所有必需父事件和 artifact 的 run / 已结束 run`。还要分别测 orphan event、重复 event、不可读取 artifact 和时间顺序异常。若 trace 在最困难任务中更容易缺失，直接分析剩余样本会产生幸存者偏差。

反例是为了降成本只保留成功 run 的完整日志。事故和进化最需要的是失败轨迹，采样策略却系统性删除了它们。更合理的是失败、安全告警、人工接管和未知错误全量保留，普通成功按任务族抽样，同时遵守数据最小化。

## 10. Eval 生命周期与污染控制

一个生产问题进入 eval 前，要经过候选、复现、清洗、标注和 owner 审批。用于调试的 task 属于 development set；用于选择候选的是 validation set；sealed test 只在预定时机使用；已频繁暴露或饱和的 task 转为 regression 或退役。四者不能用同一个“benchmark”目录混放。

每次访问 held-out 都产生审计事件。Agent、evolver 和日常开发者不获得标签或 hidden verifier；评测服务只返回预注册粒度的诊断。若为了修复一个失败把完整 hidden test 发给模型，该样本应降级为 development，不再宣称 held-out 泛化。

## 11. 从指标到行动

每个告警都要关联 owner 和 playbook。未知工具错误突增时，先冻结相关 runtime/profile，检查 provider outage、schema 和版本，再决定回滚；错误完成上升时，优先审查 completion contract 与 verifier，而不是只调 prompt；成本上升要拆解模型请求、上下文、工具重试和人工等待。

仪表盘如果只能显示红色曲线，却不能跳转到代表性 trace、版本差异和受影响任务，就不是运营系统。反过来，trace UI 若可以看见每个 token，却无法回答“哪个版本导致生产错误”，也只是调试玩具。

## 12. 可观测性的边界

更全的日志不总是更安全。源码、客户数据、工具结果和 prompt injection 内容会在 trace 平台形成新的高价值资产。默认采集字段白名单、用途限制、租户隔离、保留期和删除流程必须与 observability 同时设计。对高敏任务，可以只保存结构化 outcome 与加密原文引用，由受控流程临时解密。

可观测性最终服务于责任：谁在什么版本、什么授权和什么环境下做了什么，系统如何知道结果正确，失败后如何恢复。它不应被用来推断或展示模型不可验证的内部心理状态。

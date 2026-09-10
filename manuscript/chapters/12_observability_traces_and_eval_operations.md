# 第十二章 可观测性、轨迹与评测运营

生产环境中的 Agent 不能只记录提示词（prompt）和最终回复（final answer）。决定结果的关键其实是一条跨模型、工具、环境、策略和人协作的执行链。可观测性要做的，不是保存模型私有思维，而是重建可审计的因果链：当时系统看到了什么、触发了什么动作、依据了哪条策略、改变了哪些状态，以及依据什么证据判断任务完成。

## 1. 轨迹是事件图

最小事件模型至少要包含模型轮次（model turn）、工具请求（tool request）、策略决策（policy decision）、审批（approval）、执行（execution）、观测（observation）、工件（artifact）、检查点（checkpoint）、委派（delegation）、验证（verification）和效果提交（effect commit）。事件之间用稳定的 ID、父子关系和工件引用串起来。大对象输出进入对象存储，trace 里只保留摘要、哈希和定位符（locator）。

```text
TraceEvent {
  run_id, span_id, parent_id, type, timestamp
  actor, model, tool, policy_version
  input_refs[], output_refs[]
  state_before, state_after
  cost, latency, status, error_class
}
```

多 Agent 场景下，trace 是一张部分有序图；对可恢复任务来说，checkpoint 和 effect ledger 比聊天文本更关键。日志、审计和模型上下文要分库分层保存：上下文可做压缩，运维日志可采样，安全审计必须满足不可篡改和保留策略。

## 2. 指标分四层

业务层看任务价值、人工节省和错误损失；任务层看完成率、部分完成、升级率和稳定性；运行层看工具调用（tool call）、重试、上下文、成本、关键路径时延；安全层看越权请求、审批、注入、数据流违规和恢复。这样分层后，问题不容易被平均值掩盖。

仅看平均成功率不够。要按任务族、风险、模型、Harness 版本、工具、仓库规模和上下文长度做分片，并同步观察 `pass@k` 与 `pass^k`。[Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 这两个指标的差异会暴露：一次最好成绩适合衡量探索能力，持续稳定表现才接近生产体验。

## 3. 失败分类先于优化

失败至少可拆成任务规范、上下文选择、推理计划、工具选择、工具执行、环境、权限、验证器、协调、外部依赖和模型能力。如果把所有失败都记成 `agent_failed`，团队最终只能靠改提示词（prompt）猜测，难以及时收敛。

归因应追到“最早可纠正事件”，而不是只盯最后一个报错。测试失败可能来自错误 patch，也可能来自依赖未安装；过早完成也可能因为完成契约缺失，而不一定是模型“没认真”。应允许多标签和置信度，并保留人工纠正记录。

## 4. Eval 是持续运营系统

评测集要持续从生产事故、人工升级、低置信度轨迹、能力边界和安全红队样本补充。能力评测（capability eval）用于找出尚未掌握的任务，回归评测（regression eval）用于守住已掌握能力；高通过率的能力题应转成回归题。[Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

每个 task 要保存输入快照、参考解（reference solution）、评分器（grader）、环境摘要、可见性和退役原因。每次 Harness 变更都要和稳定基线做多次对比（multi-trial），报告置信区间、成本和关键切片，而不是只看总分。

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

线上反馈不能直接自动写回提示词（prompt）或记忆（memory），否则攻击样本和偶发偏好会被固化。采集、筛选、标注、发布之间必须有数据治理。用户满意度也不是唯一 reward：Agent 可能通过迎合用户、隐藏风险或减少必要确认来抬高短期评分。

## 6. Trace replay 的边界

模型调用与外部世界并不总能完整重放。可靠的回放（replay）要固定输入、模型快照、采样参数、工具版本和环境镜像；对不可重放 API，需要使用录制响应或模拟器。replay 的目标是定位差异，而不是装作绝对复现。

隐私和安全同样关键。轨迹里可能有源码、个人身份信息（PII）、token 和模型生成的恶意内容。进入分析平台前要先做分类、脱敏、租户隔离和最小保留；研究者访问 held-out 与生产数据必须经过审计。

## 7. 运营仪表盘

一个可用的运营仪表盘应能回答：哪类任务失败最多；失败从哪个层开始；哪个版本引入退化；自动完成是否真的降低了人工总成本；成本上升来自模型、上下文还是重试；哪些权限请求最常被拒；哪些 verifier 最不稳定。

最终，可观测性服务的不是“好看”的 trace UI，而是事故恢复、工程归因和受控进化这三个闭环。没有可用轨迹，Harness 只能靠 anecdote 演进；没有独立 eval，轨迹优化又容易变成对历史样本过拟合。

## 8. 一条可关联的真实事件

事件 schema 应支持大对象外置、敏感字段分级，以及供应商 payload 的双轨保存。下面给出工具调用完成事件最小示例：它只记录可观察结果，不保存模型私有思维链。

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

`event_id` 用来去重，parent 用于建立因果导航，workspace hash 用来关联状态变化，policy id 证明当时依赖的规则。原始输出和供应商 payload 可能包含源码或密钥，必须放到更严格存储域；普通运营角色只应看到摘要和 locator。

## 9. Trace 完整性与采样

高流量平台往往想采样，但 effect、policy、approval、checkpoint、verification、commit 这类事件不能像普通调试日志那样随机丢弃。应按重要性分层：审计骨架全量保留；大输出只保留 hash，并按风险控制原文留存；性能 span 可以按任务量和异常率自适应采样。

完整率可定义为 `具有所有必需父事件和 artifact 的 run / 已结束 run`。还要分别统计 orphan event、重复 event、artifact 不可读取、时间顺序异常。若最困难任务更容易丢 trace，直接分析剩余样本会产生幸存者偏差（survivorship bias）。

反例是有人为降本只保留成功 run 的完整日志。真正需要用于事故定位和进化的往往是失败轨迹，可却被采样策略系统性删除。更合理的做法是失败、安全告警、人工接管、未知错误全量保留；普通成功任务再按任务族抽样，并同时执行数据最小化。

## 10. Eval 生命周期与污染控制

一个生产问题进入 eval 前，要经过候选、复现、清洗、标注和 owner 审批。用于调试的 task 归入 development set；用于选样本的是 validation set；sealed test 只在预定时机使用；已频繁暴露或已饱和的 task 转入 regression 或退役。四类任务不能放在同一个“benchmark”目录里混合存放。

每次访问 held-out 都要落审计事件。Agent、evolver 和日常开发者不能拿到标签或 hidden verifier；评测服务只返回预注册粒度的诊断结果。若为了修复一个失败，把完整 hidden test 发给模型，则该样本应降级为 development，不再宣称 held-out 泛化。

## 11. 从指标到行动

每个告警都要绑定 owner 和 playbook。未知工具错误突增时，先冻结相关 runtime/profile，排查 provider outage、schema 和版本，再决定是否回滚；错误完成率上升时，优先检查 completion contract 与 verifier，不要只改提示词（prompt）；成本上升要拆开看模型请求、上下文、工具重试和人工等待。

如果仪表盘只能显示红色曲线，但跳不过去看代表性 trace、版本差异和受影响任务，它就不算运营系统。反过来，trace UI 若只能看到每个 token，却回答不了“哪个版本引发生产错误”，它也只是调试看板的玩具。

## 12. 可观测性的边界

更完整的日志不代表更安全。源码、客户数据、工具输出和 prompt injection 内容会在 trace 平台变成高价值资产。默认采集字段白名单、用途限制、租户隔离、保留期和删除流程要与可观测性体系同时设计。高敏任务可只保存结构化 outcome，并保留加密原文引用，由受控流程临时解密。

可观测性最终服务于责任：谁在什么版本、什么授权和什么环境下做了什么，系统如何知道结果正确，失败后如何恢复。它不应被用来推断或展示模型不可验证的内部心理状态。

# 第二十三章 模型进化：从轨迹到参数更新

当一种错误跨任务、工具和 Harness profile 稳定重复，且接口修复无法解决，才进入模型参数进化。Harness 在这里既是轨迹生成器，也是评测与部署容器。权重变化的影响面最大，所以它的证据门槛应高于 prompt 或 skill 更新。

## 1. 本层的证据模板实例

| 字段 | 模型参数实例 |
|---|---|
| 可变对象 | 模型权重、adapter、训练目标、数据混合 |
| 观测信号 | 验证轨迹、偏好、可执行奖励、安全与成本结果 |
| 归因方法 | 数据 lineage、Model×Harness 2×2、消融和多 trial |
| 候选生成 | SFT、蒸馏、偏好优化、RLVR、checkpoint sweep |
| 评价隔离方式 | 训练/验证/test 分离，evaluator 与环境由外部重建 |
| 门禁判据 | 能力增益、关键回归、安全、校准、成本和稳定性 |
| 发布方式 | model registry、shadow、canary、profile 兼容矩阵 |
| 回滚粒度 | 模型 checkpoint + 配套 Harness profile |
| 失败模式 | 数据污染、reward hacking、能力遗忘、judge 偏差、分布漂移 |

## 2. 轨迹不等于训练样本

生产轨迹包含冗余探索、工具故障、秘密、偶然成功、用户提示和特定环境路径。训练前要验证最终结果，标出哪些步骤对成功有因果贡献，脱敏、去重，并绑定模型、Harness、工具和环境版本。只保留成功轨迹会删除“如何发现并修复错误”的信息，也可能教模型隐藏失败。

反例是从通过 visible test 的 patch 直接蒸馏。若 patch 硬编码测试值，训练会强化 reward hacking；若轨迹使用了后来撤销的生产权限，模型会学习不可部署行为。数据门必须读取独立 completion evidence 和 policy decision，而不是只看最终 reward。

## 3. 四类训练路线

SFT 适合稳定工具协议、输出结构和高质量行为模式；蒸馏可让昂贵模型或重型 Harness 产生经 verifier 过滤的轨迹，再训练较小模型。学生可能只模仿语言表面，因此必须放回真实 Harness 测试环境适应。

偏好优化适合难以写成单一正确答案、但能比较安全性、简洁性或证据质量的任务。偏好应由结果、规则和多源 review 形成；同族 LLM judge 存在自偏好与位置偏差，不能成为唯一真值。[Self-preference bias](https://arxiv.org/abs/2410.21819)、[Position bias](https://arxiv.org/abs/2406.07791)

RLVR 利用测试、约束或环境结果作为可验证奖励，适合代码与形式任务。其风险是修改 evaluator、泄漏 held-out、硬编码 visible test 或争取更危险权限。reward 必须在隔离控制面重算，失败和基础设施异常不能被随意移出分母。

## 4. Model×Harness 2×2 归因

新模型经常伴随新 prompt、tool view 和 context 策略一起发布。只比较旧系统与新系统无法判断收益来源。至少运行四个组合：

| | 旧 Harness | 新 Harness |
|---|---:|---:|
| 旧模型 | 基线 | Harness 主效应 |
| 新模型 | 模型主效应 | 组合与交互效应 |

任务、环境、预算和 verifier 必须固定并多 trial。若新模型只在新 Harness 上改善，说明存在交互；若旧模型在新 Harness 上同样改善，部分收益不应归因于训练。这个矩阵也决定回滚：通常要回滚经过验证的 model—Harness bundle，而不是只换模型 id。

## 5. 数据与模型 lineage

每个 checkpoint 应记录训练数据 snapshot、过滤规则、父模型、训练代码、超参数、reward/evaluator 版本、已知限制和许可证。为了满足删除与事故追踪，还需从轨迹回到 source artifact 的 lineage。无法解释来源的数据不应进入高风险生产模型。

```yaml
model_release:
  id: repo-agent-7b-r12
  parent: repo-agent-7b-r11
  data_snapshot: trajectories-2026w31-v4
  harness_train: h42
  compatible_harnesses: [h42, h43]
  eval_bundle: enterprise-code-v9
  rollback: repo-agent-7b-r11+h42
```

## 6. 何时不训练

模型进化需要足够重复任务、高质量反馈、训练能力和独立安全评测。任务量小、规范频繁变化或供应商模型升级速度远高于企业训练周期时，context、tool 和 workflow 更经济。很多组织最合理的路线是先拥有轨迹和 eval，再与模型提供方或训练平台合作，而不是立即自建完整训练栈。

本层指标除可信完成率外，还应包括能力遗忘、跨 Harness 兼容率、校准误差、安全严重度、训练数据污染告警和单位增益总成本。模型更强但需要更宽权限或更昂贵 Harness 才工作，不一定是系统级进步。

## 7. 轨迹筛选的多阶段管线

原始事件先按数据许可和租户边界过滤，再做结果验证和去重，随后抽取训练视图。训练视图不必保留所有模型中间文字，应保留任务条件、可观察状态、action、observation、纠错节点和结果。对危险动作和 secret 使用占位引用，必要时在受限环境训练。

```text
raw event graph
→ consent/tenant/data-class filter
→ outcome verification
→ near-duplicate and contamination check
→ causal segment labeling
→ train/validation/test split by task lineage
→ immutable dataset snapshot
```

按单条轨迹随机切分容易泄漏。同一仓库 issue、同源模板或同一用户的近重复任务可能跨 train/test，使泛化被高估。更稳妥的是按 repository、task family、时间或 source lineage 分组切分，并对公开 benchmark 做污染检查。

## 8. 错误与纠错都要学习

只训练“最短成功路径”可以提高表面效率，却让模型在真实故障中缺少恢复经验。应保留有价值的失败—诊断—修复片段，并标明哪些错误是模型造成、哪些来自环境。模型不需要模仿每次冗余探索，但要学习何时停止、何时 reconcile、何时请求 authority。

反例是把 `POLICY_DENIED` 后不断改写命令的轨迹作为“坚持解决问题”的正例。正确标签应奖励合法升级或停止。训练目标必须与生产 policy 一致，否则 Harness 会不断与模型的既有习惯对抗。

## 9. 安全回归与能力回归同权

模型更新可能提高任务成功，同时更善于寻找工具旁路、从日志恢复 secret 或说服 reviewer。安全评测要在真实 Harness 与权限下运行，包括直接/间接 prompt injection、数据外泄、越权委派、evaluator 触碰和长时策略漂移。只测裸模型拒绝率不能覆盖系统行为。

安全 hard gate 也需要版本化，防止候选针对固定攻击集过拟合。保留 sealed 红队集，周期性引入新攻击并回放历史事故。任何严重安全回归都不能用平均能力收益抵消。

## 10. 模型发布后的监测

离线通过只是发布条件。canary 要观测新模型在各 Harness profile 的工具分布、审批请求、未知错误、长尾成本和完成后事故。若新模型改变 action 模式，旧 policy 规则可能不再覆盖；这属于系统兼容故障，不应只归咎模型。

模型 registry 应支持紧急冻结新任务、恢复旧 checkpoint 和保留在途 task 的版本粘性。回滚后继续保存候选轨迹，用于解释为什么离线 eval 未发现问题，而不是删除失败 release 的数据。

## 11. 训练前先证明问题属于模型

模型训练是四层中成本最高、回滚粒度最粗的改变，因此归因门槛也应最高。只有同一失败在多个合理 Harness profile、稳定环境和足够任务切片中持续存在，且 context、tool、workflow 与 memory 的低成本修复无法解决时，才把它登记为 model-intrinsic candidate。否则训练可能把接口缺陷写进权重，随后每次模型升级都要重新对抗同一错误。

最小归因实验是 Model×Harness 的交叉比较：旧模型/旧 Harness、旧模型/新 Harness、新模型/旧 Harness、新模型/新 Harness。若两个模型都只在旧 Harness 失败，优先修 Harness；若新模型在两个 Harness 都退化，才有较强的模型证据。反例是只比较最后一格与第一格并宣布训练有效，其中的增益无法分配。高风险领域还应加入时间外和组织外切片，防止模型记住本企业的流程表达，却在规则变化后失去校准。训练立项书必须保存未采用更轻变更的理由。

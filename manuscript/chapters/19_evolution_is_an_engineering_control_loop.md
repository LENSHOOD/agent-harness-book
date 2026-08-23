# 第十九章 进化不是自我修改：目标函数、数据与治理

Agent 进化常被描述成“它会修改自己”。这种说法隐藏了最重要的问题：谁定义更好，谁提供数据，谁评价候选，谁有权发布，失败如何回滚。工程上，进化是一个受控优化系统，而不是自治主体获得无限写权限。

## 1. 四个层次

本书把进化分为：任务内策略适应；跨任务记忆与 skill；Harness 的 prompt、工具、路由和工作流变化；模型参数变化。越往后影响面越大、反馈越慢、治理成本越高。

```text
task-time repair → memory/skill → harness release → model training
minutes             days           weeks             weeks/months
```

不要用模型训练解决本可由工具 schema 修复的问题，也不要把短期上下文摘要冒充长期学习。

## 2. 优化对象与根信任

系统先声明 mutable surface：哪些 prompt、retriever、tool view、policy 参数、workflow 或 memory 可产生候选。Evaluator、held-out 数据、权限根、审计和 release controller 默认不可由候选修改。

如果 Agent 同时修改实现和评分器，分数上升没有意义。自我进化的第一原则是评价独立性。

## 3. 数据不是天然经验

生产轨迹包含成功、偶然成功、失败、攻击、用户妥协和环境噪声。进入经验库前要脱敏、归因、去重、标注任务分布和结果证据。只学习被用户接受的答案会产生选择偏差；用户可能没有检查。

## 4. 多目标而非单分数

目标至少包含正确性、稳定性、安全、成本、时延、人工负担与可解释性。优化单一通过率容易导致更长轨迹、更多权限或测试投机。采用 Pareto frontier 与硬约束：安全回归不允许被平均收益抵消。

## 5. 最小可信闭环

```text
observe → attribute → propose minimal change
→ isolated multi-trial eval → statistical gate
→ canary → monitor → promote/rollback
```

Self-Harness 等近期工作说明冻结模型时，Harness 改进也可能产生显著收益；但论文结果不等于生产自治许可。[Self-Harness](https://arxiv.org/abs/2606.09498) 组织需要可重放证据和发布治理。

## 6. 能力边界

Harness 可以减少接口摩擦、提供搜索与验证、扩大推理预算，却不能无限补偿模型缺少的知识和推理能力。Hierarchical Self-Improvement 报告的边界性结果提醒：在超出基础能力的任务上，结构优化可能没有提升。[HSI](https://arxiv.org/abs/2608.08466)

进化项目应建立对照：模型升级、Harness 变化、环境变化和数据污染分别测量。否则组织会把供应商模型进步误认为自研 Harness 学会了进化。

# 第二十四章 受控进化闭环：门禁、灰度、回滚与反投机

前三章分别讨论可变对象，本章把它们组成生产闭环。可信进化不是 Agent 在运行时修改自己，而是候选系统在不可变治理框架下接受实验。

## 1. 双平面架构

```text
immutable governance plane
  identity / policy root / eval registry / held-out vault
  release controller / audit / rollback

evolvable plane
  prompts / skills / memory / tool views / workflows
  model profiles / candidate plugins
```

候选平面只能提交 proposal，没有自行晋级权限。治理平面也不接收候选生成的自报分数，而在隔离环境重算。

## 2. 实验协议

每次实验预注册目标、主要指标、硬约束、任务集、trial 数、停止规则和允许风险。基线与候选随机交错运行，减少时间和环境漂移。报告总体与关键切片、置信区间、成本、失败簇和完整性告警。

## 3. 防 Reward Hacking

Evaluator 只读隔离，held-out 不进候选上下文；记录文件与网络访问；Agent 报告分数与可信重算对账；测试文件、metric 代码和数据 hash 纳入 evidence package。EvilGenie 与 SpecBench 说明 visible test 通过并不足以证明真实目标。[EvilGenie](https://arxiv.org/abs/2511.21654)

## 4. Canary 与回滚

发布从 shadow、内部、低风险租户到广泛流量。Canary 采用版本粘性，避免同一任务中途切换。异常触发自动停止新任务，进行中任务按风险完成或暂停。回滚同时恢复 Harness bundle、模型 profile、memory snapshot 和 policy compatibility。

## 5. 组织责任

产品 owner 定义价值，领域专家维护任务，安全团队定义硬门，平台团队维护 runtime，独立评测方管理 held-out，发布责任人批准晋级。小组织可一人多角，但系统权限仍分离。

## 6. 进化账本

保存 lineage：父版本、mutation、数据、评测、选择原因、canary、事故和退役。这样可回答“为何变好”“谁批准”“哪些任务退化”“如何回去”。没有 lineage 的自动优化只是不可审计配置漂移。

成熟系统的目标不是最大更新频率，而是最大可信学习率：每次变化都能从证据中学习，同时把错误候选限制在可恢复的爆炸半径内。

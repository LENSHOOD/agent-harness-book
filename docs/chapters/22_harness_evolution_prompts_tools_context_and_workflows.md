# 第二十二章 Harness 进化：Prompt、工具、上下文与工作流

Harness 进化直接修改模型所处的决策环境，通常比训练模型便宜、上线快。可变对象包括 system instruction、tool schema、上下文选择器、压缩器、router、retry、workflow、sandbox profile 与模型 profile。

## 1. 先归因再变异

工具选择失败可能来自描述、参数、返回噪声或模型能力。盲目追加 prompt 会形成不可维护的规则堆。每个 mutation 应对应失败簇和因果假设，例如“工具目录过大导致选择错误”，候选则是动态 tool discovery，而非泛化提醒。

## 2. 最小变更原则

候选表示为版本化 patch：

```text
HarnessMutation {
  base_version
  target_component
  hypothesis
  patch
  expected_gain
  risk_surface
  eval_plan
}
```

一次只改变尽量少的因素，便于归因和回滚。涉及多个组件的组合优化可在单变量证据后进行。

## 3. 质量多样性

只保留最高平均分候选会收敛到单一策略，并可能牺牲某些任务族。Gated Semantic Quality-Diversity 将候选多样性与确定性门禁结合，强调把生成交给模型、计量和显著性检验交给代码。[Gated Semantic QD](https://arxiv.org/abs/2607.13683)

企业可以维护按任务域、风险和模型区分的多个 Harness profile，而非追求一个全局最优 prompt。

## 4. 四组门禁

正确性门检查能力与回归；安全门检查权限、注入和信息流；运营门检查成本、时延和稳定性；治理门检查可解释性、所有者与回滚。任何硬门失败都不能被平均收益抵消。

## 5. 发布

候选先 shadow，再小流量 canary，随后按切片晋级。运行时记录完整版本组合：模型、prompt、tools、retriever、policy、sandbox 与 evaluator。回滚必须能恢复组合，而不仅是 prompt 文本。

DSH/Cordis 为动态装配提供了优雅载体，但 evolution controller 应在插件树外部。可修改性与评价权分离，是 Harness 进化从 demo 走向生产的分界线。

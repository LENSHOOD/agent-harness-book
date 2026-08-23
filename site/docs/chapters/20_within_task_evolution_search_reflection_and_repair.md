# 第二十章 任务内进化：搜索、反思与验证—修复

任务内进化不改变长期系统版本，而是在一次 run 中根据反馈调整计划、候选和资源。它是最安全、反馈最快的一层，也最容易被误称为“自我学习”。

## 1. Reflexion 的贡献与边界

Reflexion 将失败反馈转成语言记忆，在后续 trial 中影响行为，不更新模型权重。[Reflexion](https://arxiv.org/abs/2303.11366) 它证明文本反馈可形成短期策略改进，但反思是否正确仍依赖 evaluator。让同一模型自由写“教训”可能固化错误归因。

## 2. 搜索不是无限重试

候选搜索可以采用 best-of-N、树搜索、分支工作区或多 Agent 并行。每个分支必须有不同假设、预算和停止条件；重复相同 prompt 只是在采样。选择由外部 verifier 进行，不能按语言自信度。

## 3. 验证—修复循环

```text
candidate → deterministic checks
  ├─ pass → completion gate
  ├─ diagnostic failure → minimal repair context
  ├─ flaky/ambiguous → independent review
  └─ no progress/budget → escalate
```

Harness 只回传修复所需诊断，避免逐轮泄漏 held-out。使用错误签名检测循环；连续两次没有减少失败集合时换假设，而不是继续局部补丁。

## 4. 动态工作流

任务内可以根据风险与不确定性增加搜索、reviewer 或测试，但 runtime 仍执行预算与权限上限。模型可以提议新步骤，不能自行取消强制检查。

## 5. 三类案例

代码 Agent 在独立 worktree 生成多个 patch，由测试和静态分析选；数据 Agent 对异常结论生成替代查询并对账；自进化实验中的候选生成器根据失败簇提出最小 mutation。共同点是变化留在 run scope，结束后不自动污染全局系统。

任务内进化的成熟指标不是“思考轮数”，而是单位成本下错误集合是否收敛、是否避免重复副作用、是否保留可解释的候选淘汰记录。

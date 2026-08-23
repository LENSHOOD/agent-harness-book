# 第二十五章 三个贯穿案例的端到端设计

## 1. 仓库级软件工程

入口把 issue 编译为 completion contract：目标、允许目录、兼容不变量、测试和 PR 证据。控制面创建固定 commit 的 worktree，runtime adapter 启动 Claude Code、Codex 或自研 Agent。Agent 搜索、修改和测试；高风险依赖安装或网络访问经策略门。

候选 patch 被 seal，在 clean workspace 执行 fail-to-pass、pass-to-pass、lint、安全和变更范围检查。独立 reviewer 只看任务、diff 和证据。通过后生成 PR；merge 仍由人或发布策略批准。失败轨迹按上下文、工具、代码、环境或 verifier 归因，进入 eval 候选池。

## 2. 企业数据分析

任务合同固定指标口径、数据快照、时间、币种、允许来源和交付格式。Planner 将取数、对账、解释和反证分解；每个 worker 使用最小权限短期凭证，敏感数据不进入外部模型上下文。

SQL、参数、行数、数据 hash 和图表源成为 artifact。数字由独立查询与总额对账验证，文字结论由 rubric/model/分析师检查。最终 evidence package 能让另一位分析师重建报告。任何 freshness 变化都标记，不静默混合快照。

## 3. 自我进化 Agent

Observability 聚类一段时间的失败，提出“工具目录过大造成选择错误”的归因。Mutation workers 生成动态发现、描述改写和模型 profile 三类候选。Evaluator 在 held-out、回归、安全与成本集上多 trial 运行；候选无权读取标签或修改 evaluator。

统计门选择非劣且显著改善的 profile，先 shadow 后 canary。监控选择错误、任务成功、token 和权限请求。若关键切片退化，release controller 回滚 bundle 并记录 lineage。整个闭环没有让生产 Agent 直接改写自身。

## 4. 共用骨架

```text
intent → contract → identity/workspace → runtime
→ actions/effects → candidate → independent verification
→ approval/commit → evidence → telemetry → eval/evolution
```

三例的差异在工具、数据和风险，骨架相同。平台化价值来自复用任务、身份、策略、证据、trace 和发布，而不是强迫所有 Agent 共享一种内部思考方式。

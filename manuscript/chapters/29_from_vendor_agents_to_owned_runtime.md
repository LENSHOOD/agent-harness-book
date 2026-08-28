# 第二十九章 从接入现有 Agent 到拥有运行时主动权

迁移目标不是“去供应商化”，而是让供应商成为可替换能力组件。平台必须拥有任务定义、权力边界、证据和学习数据；是否自研模型循环是后续经济决策。

## 阶段一：封装而非散接

为 Claude Code、Codex 或其他 Agent 建 adapter，统一 task、attempt、event、artifact、approval 和 cancel。所有调用经过平台身份、workspace 与策略，不允许业务团队在脚本中分散保存长期 token。此阶段不追求抹平所有差异，先双轨保存 canonical event 与原始 payload。

退出条件：能列出每个 runtime 版本、调用者、工作区、费用和外部动作；停止解析彩色终端输出；供应商升级前有契约测试。

## 阶段二：外置完成与证据

把 verifier、EvidencePackage 和 commit authority 放到 runtime 外。先选择一个高频任务族，定义可执行 CompletionContract，在 clean environment 重验 candidate。这样即使更换 Agent，业务正确性与审计不随供应商迁移。

退出条件：模型停止不再直接触发 merge/send/deploy；任一完成任务都可从输入 revision 重建 artifact 和检查；错误完成能回标到 task 与 runtime 版本。

## 阶段三：统一执行面

建立企业 sandbox、tool gateway、credential broker 和 artifact store。供应商 runtime 决定动作，受控工具提交效果；对无法适配的原生功能保留专用 execution profile，并明确降低自治等级。

失效场景是“一半工具走 gateway，一半插件直连 SaaS”。架构图看似统一，最敏感的 secret 和出网反而旁路。应以网络流、secret 发放和外部审计日志验证覆盖率，而不是只数接入工具。

## 阶段四：建立评测与运营基线

从真实任务形成 capability、regression、safety 和 recovery suites，以相同合同、环境和预算比较模型/runtime 的成功、稳定、成本与人工负担。建立第十二、二十六章的 trace 与 SLO；没有基线，自研无法证明价值，供应商切换也无法量化风险。

退出条件：关键任务多 trial；故障注入可重复；报告按任务、风险、模型和 runtime 切片；能执行 Model×Harness 2×2 归因。

## 阶段五：逐层替换

先替换最具企业差异化的 context compiler、tool view、policy adapter 或 workflow，再考虑 loop。每次只改变少数层，保留旧 bundle 与快速回滚。不要同时重写 UI、runtime、sandbox 和 eval，否则任何改善或退化都无法归因。

| 先内化对象 | 何时值得 | 不宜内化的信号 |
|---|---|---|
| Context compiler | 企业知识复杂且可测 recall | 权威数据尚未治理 |
| Tool gateway | 权限/审计是核心要求 | 只有低风险本地工具 |
| Workflow | 任务重复且边界稳定 | 流程仍频繁人工协商 |
| Agent loop | 供应商协议限制关键能力 | 只是希望省少量 token |

## 阶段六：引入受控进化

当 trace、归因、eval、canary 和 rollback 稳定后，才自动生成候选 Harness 变更。发布仍由外部治理平面控制；跨任务 memory 先进入隔离 registry；模型训练是更后的选择。若组织尚不能可靠回滚普通配置，就不应自动进化配置。

## 迁移治理

每阶段维护 capability map、数据出口、供应商依赖、compatibility test 和退场演练。至少每个主要版本演练一次：冻结新任务、导出未完成 attempt、在替代 runtime 重新开始或恢复、重建 evidence、撤销旧凭证。恢复不一定跨 runtime 保留内部思考，但必须保留任务、artifact 和已提交 effect。

最终主动权的判据很简单：供应商暂时不可用或价格变化时，企业是否仍能解释任务状态、保护数据、验证已有结果，并在可控损失下切换。若答案是否定的，即使代码托管在自己账户，也没有真正拥有运行时。

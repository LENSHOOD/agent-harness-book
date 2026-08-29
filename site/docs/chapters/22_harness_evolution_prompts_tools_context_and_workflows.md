# 第二十二章 Harness 进化：从失败病理到版本化变更

> 证据地位：本章综合公开研究与作者工程推导；2026 年演化研究以预印本为主，结论不等同于长期生产复现。

Harness 进化直接修改模型所处的决策环境，通常比训练模型上线快，也最容易陷入“不断追加 prompt”。可变对象包括 system instruction、tool schema、context compiler、retriever、compactor、router、retry、workflow、sandbox profile 和 model profile。只有当变化被版本化、独立评价并可回滚时，才称得上 Harness 进化。

## 1. 本层的证据模板实例

| 字段 | Harness 实例 |
|---|---|
| 可变对象 | prompt、tool view、context、router、workflow、runtime config |
| 观测信号 | 失败簇、工具错误、trace、在线实验、成本与安全告警 |
| 归因方法 | pathology 分类、单变量/消融、Model×Harness 2×2 |
| 候选生成 | 人工假设、evolver Agent、搜索/重组、供应商适配 |
| 评价隔离方式 | 冻结 evaluator/数据/环境，候选不可读取 sealed test |
| 门禁判据 | 激活、有效性、显著改善、关键切片非劣、硬门通过 |
| 发布方式 | shadow、canary、按任务/模型/租户 profile 晋级 |
| 回滚粒度 | 完整 Harness bundle，而非单个 prompt 字符串 |
| 失败模式 | 规则堆、过拟合、未激活补丁、指标投机、组合漂移 |

## 2. 先诊断失败病理

“工具调用失败”可能来自模型选错工具、schema 不清、参数校验缺失、返回噪声、网络故障或权限拒绝。每个 mutation 必须绑定 `where × why`：改哪里，针对什么可观察病理。若工具目录过大导致选择错误，候选可以是动态 tool discovery；若根因是服务 500，追加“请认真选择工具”毫无意义。

一个可审计变更至少包含：base version、目标组件、失败簇、因果假设、patch、预期收益、风险面、激活 beacon、eval plan 和 rollback。一次尽量只改变一个因果因素；组合优化放在单因素证据之后。

```json
{
  "base": "harness-42",
  "target": "tool_catalog.retrieval",
  "pathology": "wrong_tool_when_catalog_gt_80",
  "hypothesis": "static schemas overload selection",
  "mutation": "server-grouped on-demand discovery",
  "activation_beacon": "tool_catalog_lookup",
  "rollback": "harness-42"
}
```

## 3. 研究系统提供了什么证据

Self-Harness 预印本把流程分成 Weakness Mining、Harness Proposal 和 Proposal Validation，并在三个冻结模型上报告 held-out Terminal-Bench-2.0 子集通过率改善。[Self-Harness](https://arxiv.org/abs/2606.09498) 它的重要机制是从模型特定弱点产生最小变更，而不是复用一套万能 prompt。

GSME 预印本进一步把候选生成与 credit 分开：模型诊断并提案，确定性代码拥有采样、计量和显著性检验；候选按 `where × why` 病理进入质量—多样性 archive，并设置 validity、activation 和 significance gate。[GSME](https://arxiv.org/abs/2607.13683) 这比“让另一个模型打分”更接近实验系统，但结论仍受任务集、冻结模型、样本量和实现质量约束。

HSI 预印本允许同一冻结模型分别承担 task harness、evolver 和 meta-evolver，并保留 frozen outer anchor；其在中等难度 BALROG 环境报告收益，同时在超出 backbone 能力的 NLE 上没有改善。[HSI](https://arxiv.org/abs/2608.08466) 这给出两条边界：反馈必须有信息，基础模型必须有能力利用新结构。

## 4. 四组门禁

正确性门检查 capability 与 regression；安全门检查权限、注入、信息流和供应链；运营门检查成本、时延、稳定性与资源；治理门检查 owner、解释、版本、回滚和数据许可。任何硬门失败不能被平均收益抵消。

激活门尤其容易被忽略。候选 prompt 可能从未进入相关上下文，却因随机波动看似提高分数。每次 trial 应记录 mutation 是否被实际加载、相关工具是否被发现、策略分支是否触发；未激活 trial 不能被解释为机制证据。

## 5. Profile 而非全局最优

不同模型对工具格式、上下文与提示敏感度不同，Cursor 的公开实践也按模型版本定制 Harness。[Cursor harness](https://cursor.com/blog/continually-improving-agent-harness) 因此企业更适合维护按任务、风险和模型区分的 profile，而不是追求一个全局最优 prompt。profile 数量也要受控，否则组合爆炸使 eval 覆盖失真。

DeepSeek Harness/Cordis 提供动态装配和可逆插件的载体（见第十六章），但 evolution controller 应位于候选插件树之外。可修改性越强，评价权隔离越重要。

## 6. 何时选择替代方案

如果失败来自确定性 API 约束，直接修 schema、validator 或服务比自动搜索更可靠；如果任务很少且变化慢，人工评审的版本化配置成本更低；只有失败重复、eval 可信、候选空间较大时，自动提案和搜索才产生杠杆。

本层健康指标包括 candidate activation rate、credited gain、关键切片最大回归、rollback rate、实验成本/被采纳变更和变更半衰期。最后一项衡量改进多久后因模型或环境变化失效，防止团队只累计“曾经有效”的补丁。

## 7. 可变表面的风险排序

并非所有 Harness 组件都适合相同自动化。tool description 和检索排序通常只改变模型看到什么，风险相对可控；workflow 可以改变动作顺序和并发；sandbox profile 与 approval policy 直接改变可做什么，风险最高。候选权限应按表面分级：低风险可自动生成并进入 shadow，高风险只能由人提交、由安全套件验证。

同一文本改动也可能跨级。给 tool description 增加示例看似是提示优化，若示例含生产 URL 或教模型绕过批准，就变成数据与权限风险。mutation scanner 应分析引用的数据分类、工具 capability 和潜在外部效果，而不是只按文件路径判定。

## 8. 组合爆炸与交互效应

Prompt、tool view、context compiler、model 和 workflow 之间有交互。单变量改善可能在另一模型上退化，两个独立改善也可能组合后冲突。平台先建立小规模因子实验，找出主要交互，再决定哪些组件必须作为 bundle 一起发布。

例如“更简短的工具描述”和“按需工具发现”单独都减少 token，但组合后索引缺少足够区分信息，wrong-tool 反而上升。若只保存最终平均分，无法定位交互。trace 需要记录每个动态上下文项的来源、选择原因和 token 成本。

## 9. 防止 Prompt Rule Accretion

规则堆积的典型症状是：每次事故都在 system prompt 增加一句“永远不要”，旧规则没有 owner、测试和退役时间，模型面对相互冲突的长指令。治理方法与代码相似：每条承重规则绑定 failure id 和 eval，定期消融；可以由 schema、policy 或工具默认值保证的内容移出 prompt。

建议把 Harness source 分成 invariant、model profile、task profile 与 experiment overlay。invariant 只放跨任务硬语义的模型说明，真正硬约束仍由系统执行；model profile 适配工具和行为；task profile 注入领域做法；overlay 只在实验流量存在。构建产物记录各层来源和冲突解析。

## 10. 从候选到可维护版本

Evolver 生成的 patch 通常只针对局部失败，代码和文字质量未必适合长期维护。进入 release 前还需 normalization：消除重复、补 owner 和注释、生成兼容测试、检查是否改变未声明表面。normalization 后必须重跑评测，因为“语义等价”的重写对模型未必等价。

退役同样重要。模型升级后逐条消融旧补丁；若移除不退化，就删除而不是保留“保险”。Harness evolution 的净产出应是更好的决策环境，而不是增长最快的配置仓库。

## 11. 用可逆性决定发布半径

mutation 风险不仅取决于改了什么，还取决于错误被发现后能否恢复。纯检索排序通常可以按请求回滚；workflow 变更可能留下在途任务；工具权限和外部 effect 可能不可逆。因此 release controller 应为每个 surface 记录 detection latency、rollback latency、在途状态兼容和最大 effect 半径，再决定 shadow、canary 或人工提交。无法给出恢复路径的候选，即使离线收益显著，也只能停在模拟环境。

例如一个新 workflow 将串行审批改为并行，以降低时延。离线任务都通过，但真实环境中两个分支同时预留同一资源，形成双重承诺。只回滚配置不会撤销已生成 reservation；系统还需 effect ledger、冲突检测和补偿流程。这个反例说明“可逆插件”描述的是软件装配，不自动保证业务效果可逆。发布证据应分别证明配置可回退、状态可读取、外部效果可对账；三者缺一，rollback 字段就只是一个版本号。

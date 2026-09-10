# 第二十二章 Harness 进化：从失败病理到版本化变更

> 证据地位：本章综合公开研究与作者工程推导；2026 年演化研究以预印本为主，结论不等同于长期生产复现。

Harness 进化就是直接改模型的决策环境。它通常比训练模型上线快，也最容易陷入“不断追加 prompt”。可变对象包括 system instruction（系统指令）、tool schema（工具结构定义）、context compiler（上下文编译器）、retriever（检索器）和 compactor（压缩器）。还包括 router（路由器）、workflow（工作流）、sandbox profile（沙箱配置）和 model profile（模型配置）。只有当变化被版本化、独立评价并可回滚时，这类改动才叫 Harness 进化。

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

“工具调用失败”可能由多种原因导致：模型选错工具、schema 不清、参数校验缺失、返回噪声、网络故障或权限拒绝。每个 mutation（变更）必须绑定 `where × why`，也就是改哪里、针对哪类可观察病理。若工具目录过大导致选择错误，候选可以是动态 tool discovery（动态工具发现）；若根因是服务返回 500，直接加“请认真选择工具”通常就不对症。

一个可审计变更至少要包含：base version、目标组件、失败簇、因果假设、patch、预期收益、风险面、激活 beacon、eval plan 和 rollback。尽量一次只改变一个因果因素，组合优化应在单因素证据做完后再做。

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

Self-Harness 预印本把流程切成 Weakness Mining、Harness Proposal 和 Proposal Validation。它在三个冻结模型上报告了 held-out Terminal-Bench-2.0 子集的通过率提升。[Self-Harness](https://arxiv.org/abs/2606.09498) 它的关键机制是基于模型的特定弱点产出最小变更，而不是复用一套“万能 prompt”。

GSME 预印本进一步把候选生成与 credit 分离：模型先诊断并提案，确定性代码负责采样、计量和显著性检验。候选按 `where × why` 病理进入质量—多样性 archive，并设置 validity、activation 和 significance gate。[GSME](https://arxiv.org/abs/2607.13683) 这比“只让另一个模型打分”更接近真正的实验系统，但结论仍受任务集、冻结模型、样本量和实现质量约束。

HSI 预印本允许同一冻结模型分别承担 task harness、evolver 和 meta-evolver，并保留 frozen outer anchor（冻结外层锚点）。其在中等难度 BALROG 环境报告了收益，在超出 backbone（主干能力）范围的 NLE（非语言增强任务）上没有改善。[HSI](https://arxiv.org/abs/2608.08466) 这给了两条边界：反馈必须有信息量，基础模型必须具备利用新结构的能力。

## 4. 四组门禁

正确性门要检查 capability 与 regression；安全门要检查权限、注入、信息流和供应链；运营门要检查成本、时延、稳定性与资源；治理门要检查 owner、解释、版本、回滚和数据许可。任何硬门失败都不能被平均收益抵消。

激活门尤其容易被忽略。候选 prompt 可能从未进入相关上下文，但因为随机波动看起来分数变高。每次 trial 应记录 mutation 是否实际加载、相关工具是否被发现、策略分支是否触发；未激活的 trial 不能被解释为机制证据。

## 5. Profile 而非全局最优

不同模型对工具格式、上下文和提示的敏感度不同，Cursor 公开实践也会按模型版本定制 Harness。[Cursor harness](https://cursor.com/blog/continually-improving-agent-harness) 因此，企业更适合维护按任务、风险和模型区分的 profile，而不是追求一个全局最优的 prompt。profile 数量也要受控，否则组合爆炸会导致 eval 覆盖失真。

DeepSeek Harness/Cordis 提供动态装配和可逆插件的载体（见第十六章），但 evolution controller（演化控制器）应在候选插件树之外。可修改性越强，评价权限隔离越重要。

## 6. 何时选择替代方案

如果失败源于确定性 API 约束，直接修 schema、validator 或服务通常比自动搜索更可靠；如果任务量少且变化慢，人工评审带版本化配置的成本更低；只有当失败重复出现、eval（评测）可信且候选空间较大时，自动提案和搜索才有明显杠杆。

本层健康指标包括 candidate activation rate（候选激活率）、credited gain（有效增益）、关键切片最大回归、rollback rate（回滚率）、实验成本/被采纳变更和变更半衰期。最后一项衡量改进多久后因模型或环境变化失效，防止团队只堆积“曾经有效”的补丁。

## 7. 可变表面的风险排序

并非所有 Harness 组件都适合同样程度自动化。tool description 和检索排序通常只改变模型看到什么，风险相对可控；workflow 会改变动作顺序和并发；sandbox profile 与 approval policy 决定模型可以做什么，风险最高。候选权限应按表面分级：低风险可自动生成并进 shadow，高风险只允许人工提交，由安全套件验证。

同一段文本改动也可能跨风险等级。给 tool description 增加示例看似只是提示优化，但如果示例含生产 URL 或教模型绕过批准，它就会变成数据与权限风险。mutation scanner（变更扫描器）应分析引用的数据分类、工具 capability（能力）和潜在外部效果，而不是只按文件路径判定。

## 8. 组合爆炸与交互效应

Prompt、tool view、context compiler、model 和 workflow 之间存在交互。单变量改善在另一模型上可能退化，两个独立改善也可能组合后冲突。平台应先做小规模因子实验，找出主要交互，再决定哪些组件必须作为 bundle 一起发布。

例如“更简短工具描述”和“按需工具发现”单独都能减少 token，但组合后索引缺乏足够区分信息，wrong-tool（选错工具）率反而上升。只看最终平均分，会看不到交互。trace（轨迹）需要记录每个动态上下文项的来源、选择原因和 token 成本。

## 9. 防止 Prompt Rule Accretion

规则堆积的典型症状是：每次事故后都在 system prompt 再加一句“永远不要”，旧规则没有 owner、测试和退役时间，模型面对相互冲突的长指令时就会出问题。治理方法与代码管理类似：每条承重规则都绑定 failure id（故障编号）和 eval，并定期消融；那些可由 schema、policy 或工具默认值保证的内容应移出 prompt。

建议将 Harness source 分成 invariant、model profile、task profile 与 experiment overlay。invariant（不变层）只放跨任务、硬语义的模型说明，真正的硬约束仍由系统执行；model profile 负责工具和行为适配；task profile 注入领域性做法；overlay 只在实验流量下存在。构建产物应记录各层来源与冲突解析。

## 10. 从候选到可维护版本

Evolver 生成的 patch 往往只瞄准局部失败，代码和文字质量未必能直接长期维护。进入 release 前还要做 normalization（标准化）：去重、补 owner（负责人）和注释、补充兼容测试、检查是否改了未声明表面。normalization 后必须重跑评测，因为“语义等价”重写对模型而言未必真等价。

退役同样重要。模型升级后要逐条消融旧补丁；如果移除后不退化，就应该删除而不是留下“保险”。Harness evolution 的净产出应是更好的决策环境，而不是拥有增长最快的配置仓库。

## 11. 用可逆性决定发布半径

mutation 风险不仅看改了什么，还看错误被发现后能否恢复。纯检索排序通常可按请求回滚；workflow 变更可能留下在途任务；工具权限和外部 effect 可能不可逆。release controller（发布控制器）应对每个 surface（变更面）记录 detection latency、rollback latency、在途状态兼容性和最大 effect 半径。系统再根据这些信息决定 shadow、canary 或人工提交。没法提供恢复路径的候选，即便离线收益很高，也只能停在模拟环境。

例如，一个新 workflow 把串行审批改成并行以降低时延。离线任务看起来都通过，但真实环境里两个分支可能同时预留同一资源，形成双重承诺。只回滚配置无法撤销已生成的 reservation（资源保留）；系统还需要 effect ledger（影响账本）、冲突检测和补偿流程。这个反例说明“可逆插件”描述的是软件装配，不代表业务效果天然可逆。发布证据应分别证明配置可回退、状态可读取、外部效果可对账；少了任何一项，rollback 字段就只是写了个版本号。

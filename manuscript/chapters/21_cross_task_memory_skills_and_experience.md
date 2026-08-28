# 第二十一章 跨任务经验化：Memory、Skill 与策略库

跨任务进化把一次 run 的信息带到未来。它比任务内修复更有杠杆，也更容易形成持久污染。核心问题不是“记住更多”，而是哪些经验值得固化、在哪些条件下检索、何时过期、谁能撤销。

## 1. 本层的证据模板实例

| 字段 | 跨任务实例 |
|---|---|
| 可变对象 | 事实/情景 memory、skill、SOP、策略统计、检索权重 |
| 观测信号 | 已验证轨迹、用户纠正、复用效果、冲突与过期事件 |
| 归因方法 | 条目级 provenance、启用/禁用对照、任务切片评测 |
| 候选生成 | 轨迹提炼、人工编写、重复失败聚类、skill 合成 |
| 评价隔离方式 | 候选隔离区、held-out 复用任务、独立安全扫描 |
| 门禁判据 | 可泛化、无秘密、非劣、无冲突、权限 manifest 合格 |
| 发布方式 | 租户/团队/仓库 registry 与分层 rollout |
| 回滚粒度 | 单条 memory、skill 版本、registry snapshot |
| 失败模式 | 陈旧、误检索、租户泄漏、恶意 skill、相关性误作因果 |

## 2. 四类持久对象不能共用一种生命周期

事实记忆保存相对稳定的领域事实；情景记忆保存一次任务、动作和结果；程序记忆以 skill、脚本或 SOP 表达做法；策略统计保存某类选择在某种条件下的效果。四者的验证、访问控制和 TTL 不同，不能都变成无类型向量。

Voyager 展示了把验证过的可执行技能积累并在未来复用的路线，其系统组合自动课程、可执行 skill library 与环境反馈。[Voyager](https://arxiv.org/abs/2305.16291) Living-Harness 则在 2026 年预印本中把交互轨迹转成 episodic procedural memory 和 repair state graph，同时冻结工具和基础上下文。[Living-Harness](https://arxiv.org/abs/2607.26598) 两者支持“程序经验可积累”这一研究方向，不证明自动写入在开放企业数据中天然安全。

## 3. 写入门比检索算法更重要

候选经验先回答五个问题：来源是否可信，结果是否独立验证，因果假设是否合理，是否可跨任务泛化，是否包含秘密或越权步骤。一次成功不足以证明某条做法有效；至少应有相似任务的启用/禁用对照或人工领域审查。

```text
trace → candidate lesson → evidence linkage
→ secret/PII scan → dedupe/conflict
→ held-out reuse eval → approve → publish with scope and TTL
```

一个失效场景是从事故处理中提炼出“遇到权限错误就使用管理员 token”，随后被无关任务检索。即使原轨迹成功，该 skill 也把临时例外固化为常规做法。写入门应保留原授权上下文，并禁止把一次性凭证和 waiver 编译成全局程序知识。

## 4. 检索是策略决策

每条经验至少包含适用范围、前置条件、反例、owner、版本、可信度、TTL 和 provenance。检索除了语义相似，还要按租户、环境、工具版本、数据分类和 freshness 过滤。模型可以在候选之间判断相关性，但硬隔离必须在检索前执行。

评估 memory 不只测 recall。还要测 harmful retrieval rate：被检索且导致硬约束失败的条目占启用条目的比例；stale activation rate：过期或不兼容条目被激活的比例；causal lift：启用相对于禁用对照的可信完成差异。三个指标都需按任务族切片。

## 5. Skill 是供应链包

Skill 可能包含指令、脚本、模板与资源，本质上是可执行依赖。它需要 owner、版本、签名、权限 manifest、测试、变更评审和撤销。自动生成 skill 只能进入候选 registry；运行时根据声明 capability 给它最小权限，不因“是内部 Agent 写的”而信任。

```yaml
skill_manifest:
  id: repo.release-notes
  version: 3.2.1
  owner: dev-platform
  allowed_tools: [repo.read, git.diff]
  network: deny
  data_scope: current_repository
  expires_at: 2027-01-31
  evidence_suite: skill-release-notes-v5
```

## 6. 遗忘、纠错与派生影响

“遗忘”不是从向量库删一行。系统要能定位受影响的缓存、派生 skill、已生成 artifact 和下游 profile。用户纠正应生成 supersedes/revokes 关系，旧条目停止新激活；需要法律删除时，再按数据治理流程物理清除并留下不可含原文的审计证明。

本层最适合在重复、可验证且环境相对稳定的任务上使用。高度一次性的战略判断不宜自动固化。成功标准是未来任务在稳定成本与安全约束下改善，并能证明改善来自哪些经验；memory 条目数量持续增长不是能力指标。

## 7. Memory 的状态机

一条经验不应只有 active/deleted 两态。推荐状态为 `candidate → quarantined → validated → active → deprecated → revoked/expired`。candidate 尚未经过复用验证；quarantined 因秘密、冲突或来源问题暂停；validated 表示证据充分但未必对所有租户发布；deprecated 停止新使用但保留可重建性；revoked 表示已知有害。

状态转换由不同 authority 控制。自动提炼器可以创建 candidate，安全扫描可以 quarantine，registry owner 批准 active，事故响应可紧急 revoke。所有转换带原因和 evidence ref。若系统只允许覆盖内容，后续无法解释历史任务为什么使用了旧规则。

## 8. 冲突不是“取最新”

两条 memory 可能在不同环境都正确。例如旧 API 要求 `v1` header，新区域已迁移 `v2`；简单地按时间取最新会破坏旧区域。冲突处理应先比较 scope、前置条件和权威来源，再决定并存、细分或撤销。对无法判定的冲突，检索器应返回不确定性并触发人工，而不是随机选一条。

事实记忆还要区分 source truth 与 learned summary。法规、价格、组织权限等易变化或高风险事实应在使用时查询权威系统；memory 只保存 locator 和检索方法。把一份旧网页摘要永久嵌入向量库，会让回答流畅但不可纠正。

## 9. 复用实验与负迁移

评估一条 skill 时，任务集应包含目标任务、相邻任务和反例任务。目标集改善但反例集频繁误触发，说明 description 或触发条件过宽。除了平均收益，还应报告 activation precision、未激活时的额外上下文成本、失败严重度和跨模型差异。

一个实用对照是同一模型和 Harness 下，随机交错运行 `registry_without_candidate` 与 `registry_with_candidate`。若 skill 包含脚本，还要固定依赖和 sandbox。仅比较发布前后的线上结果会混入模型升级、季节性任务和其他 memory 变化。

## 10. 经验库的容量与注意力预算

经验越多，检索、冲突和安全扫描成本越高。即使采用按需加载，名称和描述也会占索引与模型注意力。registry 应定期合并重复项、退役低价值项，并测量每条经验的边际激活与收益。长期未激活不一定无用，但需要 owner 重新确认保留理由。

容量治理可以采用“总量配额 + 领域 owner + 自动过期复核”，而不是让向量库无限增长。其目标是提高可用知识密度：被正确激活、产生可验证帮助且能追溯来源的条目，占全部可见条目的比例。

## 11. 记忆收益必须扣除维护债务

一条经验带来的收益不能只按单次 token 节省或成功率提升计算。它还创造版本兼容、权限审查、冲突处理、删除传播和事故响应成本。可以记录 `净经验价值 = 可信完成增量价值 - 检索成本 - 维护成本 - 负迁移期望损失`，并按 owner 与任务族滚动复核。该式不用于跨团队排名，而用于识别“看起来常被调用、实际只是在制造协调”的资产。

一个反例是公共 skill 在十个团队都被激活，因此被认定为核心能力；但九个团队随后覆盖其默认值，且每次模型升级都要重新验证。更好的动作可能是拆成稳定协议 schema 与领域 profile，或把确定性部分下沉到工具服务。经验库的演化方向不总是增加内容，也包括把成熟知识编译成 policy、validator、默认配置或产品接口。只有仍需模型情境判断的部分才应保留为可检索经验，从而缩小不确定性表面。

# 附录 B：可判定的 Harness 架构评审表

使用方法：每项必须附一个可复查 artifact（配置、测试、事件或演练报告），只回答“通过/不通过/不适用”。“不适用”需要风险 owner 说明。任何 R3/R4 动作若关键项不通过，不应进入生产自治。

## 任务与完成

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| 目标是否版本化 | 合同含交付物、不变量、预算、权限、验收和 owner | 目标只在聊天里，运行中静默变化 | 第十、二十七章 |
| 停止是否与完成分离 | runtime stop 产生 candidate；独立 completion gate 决定完成 | final answer 直接触发 merge/send/deploy | 第十章 |
| 是否生成证据包 | 输入、artifact hash、检查、策略和批准可关联 | 只有最终文本或截图 | 第十、二十五章 |
| 外部提交是否独立授权 | commit authority 与执行 Agent 分离 | Agent 自报成功后自动生效 | 第十、二十六章 |

## 上下文与记忆

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| 上下文 provenance 可见 | 每个承重片段有来源、版本、选择原因和 token 成本 | 不知道规则从哪里注入 | 第七章 |
| 压缩不覆盖权威状态 | task、effect、artifact 保存在上下文外 | compaction 后遗忘约束或重复动作 | 第六、七章 |
| Memory 有写入门 | candidate、验证、scope、TTL、owner、撤销齐全 | 一次成功自动写入全局 memory | 第二十一章 |
| 检索先做隔离 | 租户、权限、数据分类在语义检索前过滤 | 相似度搜索跨租户返回内容 | 第七、二十一章 |

## 工具、环境与副作用

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| Action schema 稳定 | 参数、错误分类、版本、截断和 artifact 语义明确 | 全部失败都是字符串 `error` | 第八章 |
| Effect 可对账 | intent 先持久化，有幂等键，未知结果进入 reconcile | timeout 后直接重试发送/支付 | 第六章、附录 A |
| Workspace 可重建 | 输入 revision、image、依赖和初始化可固定 | “在 Agent 那台机器上能过” | 第四、六章 |
| Sandbox 经对抗验证 | 文件、网络、进程、mount、资源和身份都有测试 | 只因使用 Docker 就声称隔离 | 第九、十七章 |

## 权限与供应链

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| 身份、授权、批准分层 | actor identity、capability、decision、approver 可追踪 | 登录成功被当作拥有全部权限 | 第九章 |
| 凭证短期且不进上下文 | broker 在提交时注入 lease，日志做 secret scan | token 出现在 prompt、trace 或 skill | 第九、二十六章 |
| 委派缩权 | 子任务 capability 与预算不超过父任务 | subagent 继承宿主所有 secret | 第十一章 |
| 扩展供应链可撤销 | MCP/skill/plugin 有 owner、版本、权限、签名和 kill switch | 自动更新未审查脚本 | 第九、二十一章 |
| Prompt injection 有系统测试 | 间接注入、数据外泄和跨域 flow 进入 safety suite | 只测试模型口头拒绝 | 第九、二十三章 |

## Durable 与多 Agent

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| 中断可恢复 | kill/restart 演练无状态丢失和重复 effect | worker 崩溃后从头运行 | 第六章 |
| 取消能收敛 | 子进程、子任务、凭证和 pending effect 被处理 | UI 显示取消，后台仍执行 | 第六、十一章 |
| 并行写入隔离 | 分支有独立写集，合并后重验 | 多 Agent 共享目录互相覆盖 | 第十一、十四章 |
| Handoff 有结构化交付 | 目标、已做、artifact、未决、权限和预算齐全 | 只返回“已完成”摘要 | 第十一章 |

## Eval、运营与进化

| 检查项 | 合格判据 | 不合格的典型症状 | 依据 |
|---|---|---|---|
| Eval 集生命周期分开 | development、validation、sealed、regression 有 owner 与访问审计 | hidden test 被用于日常修 prompt | 第十二章 |
| 报告多 trial 与切片 | 固定任务/环境/预算，报告区间、成本和关键切片 | 只报一次最好成绩 | 第十二、十八章 |
| Trace 骨架完整 | policy/effect/checkpoint/verification 全量，artifact 可读取 | 成功有日志、失败无日志 | 第十二章 |
| 候选与裁判隔离 | mutable surface 明确，候选不可写 evaluator/held-out/policy root | Agent 可修改测试或分母 | 第十九、二十四章 |
| 发布可灰度与回滚 | task 版本粘性，bundle shadow/canary，回滚演练成功 | 只会换回 prompt 文件 | 第二十四章 |
| Lineage 可解释 | 父版本、mutation、数据、评测、批准、事故和退役齐全 | 无法回答“为何上线” | 第二十四章 |

## 最终判定

- **阻断**：高风险任务在身份/授权、effect 对账、隔离、完成门、证据或回滚任一项不通过。
- **限域上线**：核心安全项通过，但恢复、评测覆盖或运营证据不足；只允许低风险、可人工提交的任务。
- **生产候选**：所有适用关键项有证据，并完成正常、拒绝、超时、取消、崩溃、恢复和 verifier 失败演练。

评审结果应记录适用范围和到期时间。一个代码只读 Agent 的通过结论不能自动继承给可写生产数据库的 Agent。

# 第二十七章 Agent SDD：规范驱动的任务与发布

Agent SDD（Specification-Driven Delivery）不是要求所有请求先写长文档，而是把关键意图转换成可执行、可版本化的契约，使自治执行有明确边界。

## 1. 规范层级

业务规范描述价值；任务规范定义交付物与不变量；工具契约定义动作；策略规范定义权限；验证规范定义证据；发布规范定义谁能让效果生效。自然语言可作为入口，但最终关键字段应结构化。

## 2. 从意图到合同

Agent 可协助澄清和生成 contract draft，用户只确认高材料性歧义。低风险探索允许渐进完善，高风险任务必须在执行前冻结关键不变量。

```text
intent → ambiguity detection → contract draft
→ authority confirmation → executable checks → run
```

运行中发现新事实可以提出 contract amendment，但不能由执行 Agent 单方面降低验收标准。每次修改保留 diff 和批准者。

## 3. Specification as environment

规范应贴近权威状态：代码规则进入仓库，数据口径进入 semantic layer，API 约束进入 schema，安全要求进入 policy-as-code。只写在 prompt 的规范难以测试和复用。

## 4. 发布门

候选 artifact 与 contract version 绑定；verifier 证明检查结果；waiver 明确风险和到期；commit controller 负责合并、发送或部署。模型停止与发布完全解耦。

## 5. 规范债务

过细规范会把 Agent 退化成昂贵工作流，过粗规范会产生假完成。通过生产失败持续调整边界：把重复、可确定的隐性要求转为 schema、测试或策略，把真正需要判断的部分保留给模型和人。

Agent SDD 的价值是让平台可比较不同模型与 Harness：相同合同、相同环境、相同完成门，差异才可归因。

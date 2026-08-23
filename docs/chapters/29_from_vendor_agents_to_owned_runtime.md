# 第二十九章 从接入现有 Agent 到自研运行时

## 阶段一：封装而非散接

为 Claude Code、Codex 或其他 Agent 建立 adapter，统一 task、event、artifact、approval 和 cancel。所有调用经过平台身份、workspace 与策略，不允许业务团队直接分散保存 token 和脚本。

## 阶段二：外置完成与证据

先把 verifier、evidence package 和 commit authority 放到 runtime 外。这样即使更换 Agent，业务正确性与审计不随供应商迁移。

## 阶段三：统一执行面

建立企业 sandbox、tool gateway、credential broker 和 artifact store。供应商 runtime 只决定动作，不直接持有生产凭证。对无法适配的功能保留专用 execution profile。

## 阶段四：建立评测基线

从真实任务形成 capability、regression 和 safety suites，以相同合同比较不同模型/runtime 的成功、稳定、成本和人工负担。没有基线，自研无法证明价值。

## 阶段五：逐层替换

先替换最具差异化的 context compiler、tool view 或 workflow，再考虑 loop。每次只替换一层，保留 2×2 对照和快速回滚。不要一次重写 UI、runtime、sandbox 和 eval。

## 阶段六：引入受控进化

当 trace、归因和 eval 稳定后，才自动生成候选 Harness 变更。发布仍由外部治理平面控制。模型训练是更后的选择。

## 迁移反模式

直接解析终端彩色输出；把厂商消息结构当领域模型；把供应商“完成”映射为业务成功；共享宿主凭证；无版本地自动更新；只比较 token 价格；在没有 eval 时宣布自研更强。

最终目标不是完全摆脱供应商，而是让供应商成为可替换能力组件。平台拥有任务定义、权力边界、证据和学习数据，才拥有长期架构主动权。

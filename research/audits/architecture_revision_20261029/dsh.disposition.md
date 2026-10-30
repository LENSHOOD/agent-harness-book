# dsh 章节处置与验证

访问及核对日期：2026-10-29。责任范围仅为第十六章及本目录 `dsh.*` 文件。未修改共享登记表、目录或其他章节；未提交、推送、部署或运行上游代码。使用 deep-research 的先保存证据再综合方法，产物格式遵从书稿合同；不套用独立研究报告的章节模板。

## 基线与取回来源

主体沿用 `dsh-v0.1.6-alpha.2 / ddefc45fbc7f8e46dd73185e68295696d1297887`，通过 exact-commit git fetch 重新取回；历史 PTC 对照保留 `dsh-v0.1.2-alpha.1 / cd5ef8148158c3a752a658978873241fdf8e2bbc` 的 worker-thread README，通过不可变 raw URL 取回。未检查最新 release，不将此基线写成 10 月最新版。

已捕获的逐项清单为 [dsh.sources.jsonl](dsh.sources.jsonl)：每条包含 `source_url`、仓库相对 `capture_path`、`sha256`、字节数、commit、实际访问日、获取方式和是否被正文引用。全部 22 项捕获文件位于忽略目录 `publishing/work/architecture_20261029/dsh/`；正文引用其中 21 项。没有未匹配的正文来源 URL，比较时忽略 `#anchor`。

来源覆盖：架构、core、system-prompt、compaction、MCP、sandbox、approval、credentials、subagent 子系统；工具注册与管线；agent-instructions；Node PTC；动态 Host sandbox；Plugin Manager 与 app-boot；Creator 检查工具和接入教程；spawn/fork 两个进程内提供者；session telemetry；历史 worker-thread 文档。额外静态核对了 `packages/subagent/subagent/src/child-agent.ts` 的 `captureDelegatedPolicyOverrides`，正文通过已经捕获的 subagent 子系统页面引用同一契约。

## 实质改写与保留边界

正文由原先版本变更审计改成八节架构解释：插件树与服务归属 → loop/attempt → 日志投影与压缩 → tools/MCP/PTC → 权限与执行边界 → 委派 → 观测 → Creator 接入任务。保留首标题和编号，图为 text，不含 Mermaid；没有原第十八章及以后章节的硬编码引用，故不存在本工作项需要额外顺延的交叉引用。

保留并展开：配置整份替换、创建初始化与清理、初始 required-entry 策略与普通 HMR 非整批回滚、Host `node:vm` 非 containment、PTC 独立进程与平台限制、审批等待计入超时、heap/CPU/进程树与输出边界、安装/启用/删除分阶段残留、build-script 批准持久化且不验证对话授权、stream 结算前崩溃窗口、session generation 迁移保留旧文件、工具子调用已有原生追踪。

补充了旧稿欠缺的上下文、凭证、子会话及遥测设计。交叉审阅后的关键澄清已进入 §6：新 scope 不复制完整父工具限制/authority，但显式 sandbox override 和 Auto/Full access preset 会被捕获；存在审批服务时子审批钉为 `never`。不能把“不复制完整能力”理解成完全不继承策略。continuable 子任务的接收后取消、interrupt 不清后代、最终 flush 失败后仍释放等边界也明确保留。

旧时间线不再支配正文：原稿的九月串行初始化、撤回事务式 reload、PTC 进程迁移和 Creator 改用持久安装，分别落实到相应机制；提交日期、首次进入哪个 tag 等历史问题仍以原 `research/audits/review_20260919/` 证据为准，本轮未重新穷举发布链。旧 worker-thread 不提供安全隔离的结论只属于历史固定点；未把它误写为新版 PTC。base/headless/SDK/ACP 的 HMR 默认值仍可在本轮捕获的架构文档核对，正文不再按日期列功能表。

## 已完成验证与缺口

[dsh.validation.json](dsh.validation.json) 记录静态验证：4331 个汉字、八个共同小节、29 条证据；首标题与 Git 基线一致；全部 21 个正文来源 URL 都有 evidence 和 capture 映射；所有 capture SHA-256 匹配；全部短引文在捕获正文逐项匹配，每个来源累计引文不超过 25 个空白分隔词；代码围栏配对，`git diff --check` 通过。

未进行模型端到端任务、OS sandbox/逃逸实验、崩溃注入、安装失败残留复现、跨版本恢复实验或遥测投递验证。没有对效果、成本、最新版本或多租户安全作保证。示例是作者走查，非实际执行报告；全书构建和父级索引整合留给父任务。

浏览器已按 ego-browser 技能复用 TaskSpace 153 的 p5，访问固定架构页面；未创建/结束 TaskSpace，未操作其他页面。Ego Lite 的升级提示未触发升级。

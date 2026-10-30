# Claude 章节处置与验证记录

实际访问日期：2026-10-29。写入范围仅为第十三章及本目录 `claude_` 前缀文件。第一标题与 slug 保持不变；未修改共享来源注册表、目录、其他章节或出版输出，未提交、推送、部署。浏览器只恢复 TaskSpace 153 的 p2，没有创建或结束 TaskSpace。网页由 ego-browser CLI 获取，GitHub 仓库通过 gh/git 读取；没有执行上游代码。

## 交付与来源映射

- `claude_evidence.jsonl`：宿主架构、控制协议、权限与版本的证据。
- `claude_mechanisms.jsonl`：循环、恢复、上下文、工具、权限、子代理、观测和托管产品边界的证据。
- `claude_sources.jsonl`：正文全部 27 个不同来源 URL 的机器可读映射，忽略 `#anchor`。每项含 `source_url`、实际请求 `fetch_url`、相对与绝对 `capture_path`、SHA-256、版本与访问日期。当前无未匹配 URL。
- 快照与只读源码 checkout：`publishing/work/architecture_20261029/claude/`，属于 ignored 工作缓存。证据 JSONL 只留短摘录，不重新出版整页资料。每个来源的摘录累计不超过 25 个英文词。

公开 Python SDK 固定为 `27858cbba9ecee26a06a90b8d39d3b5596121d11`，`pyproject.toml` 版本 `0.2.174`；这不等于已经验证某一 Claude Code binary。正文描述的 `fork` 功能单独保留官方要求的 `v2.1.302`。官方文档不是不可变版本，故保存抓取内容的 SHA-256；已返回版本头的 Code 文档为 deployment `dpl_AUojGTPodKNPTVaxVPcxnNvkSVqo`，不将此部署标识误写为产品发布版本。

共获取 30 个网页快照（29 个 Markdown、1 个 HTML）。正文使用其中 24 个网页来源及 3 个固定提交中的源码文件，完整清单见映射文件。额外获取但未直接引用的页面为：

- [Checkpointing](https://code.claude.com/docs/en/checkpointing)：`checkpointing.md`，用 SDK 专门页面支持正文的回退语义。
- [Context window](https://code.claude.com/docs/en/context-window)：`context-window.md`，正文采用 loop 与 caching 专页。
- [Costs](https://code.claude.com/docs/en/costs)：`costs.md`，正文采用 SDK cost-tracking。
- [MCP](https://code.claude.com/docs/en/mcp)：`mcp.md`，正文采用 SDK MCP 页面。
- [Hosting](https://code.claude.com/docs/en/agent-sdk/hosting)：`sdk-hosting.md`，正文采用 secure-deployment。
- [User input](https://code.claude.com/docs/en/agent-sdk/user-input)：`agent-sdk-user-input.md`，正文采用 permissions 与固定源码。

## 实质性改写

按共享契约组织八节，以 SDK 宿主 → CLI binary → 模型／工具／存储为主线，加入 ASCII 责任图与“修复登录回归”的作者示例。每段产品技术事实就近链接一手来源；设计判断、集成建议和未实测示例明确区分。deep-research 的方法用于证据先落盘、来源身份固定和逐主张核验；采用用户指定的章节结构，不另造该技能默认的独立咨询报告或 HTML/PDF。

特别纠正三类混用：Agent SDK 并非纯 Messages API client；`canUseTool` 并非所有调用的必经闸门；Bash sandbox 并非包住 hooks、文件工具和 MCP 的统一隔离层。恢复部分增加 SessionStore 的本地先写、尽力镜像和 `mirror_error` 边界。子代理部分区分普通上下文与 fork、主模型所见报告与宿主可见轨迹，以及上下文隔离与 OS 身份隔离。

## 历史材料的去向

原稿基线 Git blob：`a37d46e38686ba3f5e88e391bc2bfa3a31857abd`，资料截面 2026-09-19。下列旧事实不作为十月的新事实，离开正文主线但在此保留其版本归属：

1. 原稿引用 [Platform 发布说明](https://docs.anthropic.com/en/release-notes/api) 的 2026-09-14 Messages API 按需压缩 beta：顶层 `compaction`、`compact-2026-09-04` header、签名 compaction block。它属于 Messages API，不应转换成 Claude Code 参数；本轮没有重验这条历史 release-note。
2. 同一原稿来源中的 `ant` CLI `1.30.0`（09-03）增加 `ant apply` 与 `claude-lock.json`；`1.32.0`（09-10）增加 `ant beta:sessions connect`。Managed Agents 的 `auto` 权限评估及 `agent.tool_use`／`agent.mcp_tool_use` 的 `evaluation` 同属原稿 09-10 截面，未作为本地 Claude Code 的能力描述。本轮没有将旧版命令重新标为最新。
3. Managed Agents 工程文章本轮重新访问，工程 URL 重定向至 [research/managed-agents](https://www.anthropic.com/research/managed-agents)，页面仍标注 2026-04-08。session、harness、sandbox 解耦，`wake/getSession` 恢复和 vault／proxy 凭证边界保留为该托管架构披露；不将其展开为本地 CLI 核心结构，也不推导外部动作恰好一次。
4. 原稿 [Claude Code sandboxing 工程文章](https://www.anthropic.com/engineering/claude-code-sandboxing) 的“权限提示减少 84%”保留为厂商特定内部场景自报，不纳入正文效果结论；本轮没有重做该测量或重验该历史网页。
5. 原稿自定义 `runtime_profile` YAML 中的 `policy_mediated`、`external_verifier` 是作者平台取值，不是产品选项。正文用完整任务路径取代它，避免非原生示意配置掩盖真实 API 边界。

## 已完成的验证与尚存缺口

已完成：八节及首标题检查、正文 4,000–6,000 汉字范围检查、Markdown fence 平衡、仅正文文件的 whitespace 检查；全部 27 个不同正文 URL 都匹配证据记录和快照；27 条证据均可解析、所需字段齐全、访问日期为 2026-10-29；27 个映射 SHA-256 与现存快照一致；全部证据短引可在抓取文件或固定源码中归一化精确匹配。静态检查确认 SDK 包版本、stream-json 命令、stdin/stdout pipes、三个控制请求分支及两个 `signal=None` 回调位置。未导入或运行 SDK、仓库测试和依赖安装脚本。

重要缺口：闭源循环的内部调度、落盘原子性和内部重试实现未审计；公开 SDK 源码不证明每个部署 binary 的行为。SessionStore 的恢复、真实网络取消传播、沙箱覆盖与 MCP 凭证隔离未做端到端故障注入。固定 Python 源码明确尚未给权限／hook 回调接通 abort signal，不能以 TypeScript 接口替它背书。多份官方文档仍属于同一供应商证据，不能证明普遍成本或安全收益。

出版构建、全书编号及统一引用校验交给父任务执行；本 worker 不改共享生成物。浏览器提示可升级，但研究期间没有升级或结束共享 TaskSpace。

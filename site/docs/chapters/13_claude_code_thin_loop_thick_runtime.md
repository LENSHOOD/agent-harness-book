# 第十三章 Claude Code：薄决策环与厚运行时

> 产品快照截至 2026-08-22。只陈述公开文档与可验证行为，不推断未公开内部实现。

Claude Code 最值得借鉴的不是某个系统提示，而是职责布局：核心 loop 保持简单，把能力放在上下文发现、工具、权限、hooks、subagents、skills、MCP、沙箱和可恢复会话中。官方对 Agent SDK loop 的描述接近“收集上下文—采取行动—验证结果—重复”。[Claude Agent Loop](https://code.claude.com/docs/en/agent-sdk/agent-loop)

## 1. 环境优先

Claude Code 在项目中搜索文件、读取指令、修改工作树并运行命令。项目记忆与路径规则把组织知识放回仓库，而不是永久塞进全局 prompt。[Claude Memory](https://code.claude.com/docs/en/memory) Context window 文档还说明，压缩后不同类型启动上下文具有不同再注入行为，意味着“记忆”实际由多层生命周期组成。[Claude Context Window](https://code.claude.com/docs/en/context-window)

设计启示是把上下文当编译产物：稳定前缀、项目规则、当前工作集、工具结果和压缩摘要分别管理。不能把所有内容都称为 memory。

## 2. 工具与扩展

Claude Code 通过内置工具、MCP、skills、hooks 和 subagents 扩展。Tool search 可不把全部工具 schema 预先注入上下文，而是在需要时检索相关定义，以额外发现回合换取持续的上下文节省。[Claude Tool Search](https://code.claude.com/docs/en/agent-sdk/tool-search)

Hooks 适合确定性策略与集成，skills 适合按需加载过程知识，subagents 适合上下文隔离和并行。把三者混为 prompt 插件会失去权限与生命周期边界。

## 3. 权限与沙箱

Claude Code 的安全方向从高频逐命令确认转向安全边界内自治。Anthropic 报告其 sandbox 同时限制文件系统和网络，基于 macOS Seatbelt、Linux bubblewrap 与网络代理，并使内部 permission prompt 减少 84%。[Claude Code Sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)

关键原则是：批准精确 capability，而不是信任抽象 Agent。Prompt 负责解释意图，OS 与代理负责不可绕过的边界。外部 MCP、hook 和 skill 仍是供应链入口，沙箱不替代插件审查。

## 4. 产品取舍

Claude Code 的优势是终端环境贴近工程师真实工作、工具反馈直接、项目约定可版本化，并通过 Agent SDK 把 loop 能力开放给其他应用。它的风险是高度自治 shell 带来的权限面、长会话压缩的信息损失、扩展生态的信任传播，以及产品版本快速变化造成的行为漂移。

Pi 等极简 coding agent 提醒我们：很多能力可以留给 shell 和文件，不必全部内置。Claude Code 的教学价值因此不在“功能越多越好”，而在扩展点如何围绕一个相对薄的循环组织。

## 5. 企业集成方式

企业不应把 Claude Code 的终端 UI 当平台 API。更合理的是将 Agent SDK/受控进程包装成可替换 runtime adapter，由企业控制面提供身份、任务契约、workspace、策略、凭证、trace 和完成门。

```text
enterprise control plane
  → runtime adapter
  → Claude agent session
  → sandbox/tool gateway
  → evidence package
```

平台必须保存供应商无关事件，避免未来自研 runtime 时被 Claude 特有消息格式锁定。Claude 的最终文本只是候选结果，企业 verifier 和 commit authority 仍在外部。

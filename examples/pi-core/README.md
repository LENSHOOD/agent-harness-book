# Pi Agent Core 机制实验

对应第十八章。使用真实的 `@earendil-works/pi-agent-core@1.4.0` 和 `pi-ai@1.4.0`，模型响应由确定性函数提供，工具仅做内存运算。无 API key、付费模型、网络工具或业务副作用。

在 Node.js 22.19 或更高版本中，从仓库根目录运行：

```bash
npm --prefix examples/pi-core ci --ignore-scripts --no-audit --no-fund
npm --prefix examples/pi-core test
```

九项检查覆盖：工具反馈、上下文投影、非法参数、截断工具调用、工具异常、follow-up、混合终止结果、整批终止结果和模型中止。

2026-10-29 本地运行结果：9 通过，0 失败，0 跳过。锁文件固定依赖。对应源码 tag：`v1.4.0`；commit：`4a080252f06caf63a525d7873c5d94d3c23887e0`。这是低层循环行为实验，不覆盖 Coding Agent 的会话落盘、真实压缩、MCP、委派、安全隔离或模型效果。

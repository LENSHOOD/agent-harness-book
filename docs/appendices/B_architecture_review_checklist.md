# 附录 B：Harness 架构评审检查表

## 任务与完成

- 是否有版本化目标、交付物、不变量和验收条件？
- 模型停止是否与业务完成分离？
- 是否从目标环境回读结果并生成 evidence package？

## 上下文与记忆

- 上下文来源、优先级、token 成本与 provenance 是否可见？
- 压缩后哪些状态仍是权威？
- 长期记忆是否有写入门、TTL、纠错和删除？

## 工具与环境

- Action schema、错误分类和输出截断是否稳定？
- 工具副作用是否幂等、可对账？
- workspace、文件、网络、进程和资源是否隔离？

## 权限与安全

- 身份、授权、批准和隔离是否分层？
- 凭证是否短期、窄范围且不进入模型上下文？
- MCP、skill、plugin 是否有版本、签名、权限和撤销？
- 是否测试间接 prompt injection 与跨域数据流？

## Durable 与多 Agent

- 是否有 checkpoint、取消、恢复、reconciliation？
- 委派是否缩权、限预算、结构化交付？
- 并行写入是否隔离，合并后是否重验？

## Eval 与进化

- Capability、regression、安全集是否分开？
- 是否多 trial、报告成本和关键切片？
- 候选是否无法修改 evaluator、held-out 和 policy root？
- 是否 canary、回滚并保存 lineage？

任何 R3/R4 动作若上述关键问题无答案，不应进入生产自治。

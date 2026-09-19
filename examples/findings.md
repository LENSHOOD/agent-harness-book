# 修订发现

- 历史正式运行：review_20260919/execution/runs/20260919T102120Z_30xh1oov，172 探针、46 FAIL；历史失败不能改写为通过。
- 历史 run_all.py 直接从当前 ROOT 抽取正文，需固定 a1ed264 快照，其他脚本和旧结果不改。
- 当前附录 E 初读仍是旧 schema：definitions 根没有 ref；Task checks 空字符串及 budget 未知字段未拒绝。检查器应等待/验证主代理的新稿，不隐式修改正文。
- 新案例是本地参考模型；无供应商调用、部署或真实业务效果证明。
- 当前稿已补齐E实际schema、核心6/10/A分支。本门直接读取当前fence，既不复制schema也不依赖历史B编号。
- 取消存在未确认效果时保持CANCELLING，确认后才能CANCELLED；两个状态都禁止继续派发。
- 历史正式run共441产物hash实测不变；46项逐项处置在指定disposition_execution.md。第1/11/20章非核心宿主仍明确教学限制，不能由当前局部模型推断全实现通过。

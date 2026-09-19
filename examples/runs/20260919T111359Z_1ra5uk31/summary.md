# 当前可执行参考模型运行证据

不是商业 Agent 复现、真实模型实验或生产安全认证。负例被拒绝属于当前回归门成功；历史 FAIL 不改写。

```json
{
  "kind": "executable local reference; NOT vendor replication, real model evaluation, or production safety proof",
  "exit_code": 1,
  "failures": [
    "pytest"
  ],
  "pytest": {
    "tests": 61,
    "failures": 6,
    "errors": 0,
    "skipped": 0
  },
  "exit_semantics": {
    "0": "positives pass and intended negatives rejected",
    "1": "real regression or environment/dependency error"
  },
  "run_directory": "examples/runs/20260919T111359Z_1ra5uk31",
  "historical_audit": "untouched; old exit 1 still means historical failing probes",
  "source_unchanged_during_run": true
}
```

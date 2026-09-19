# Claim Ledger 只读校验报告

> 本报告由 `audit_claim_ledger.py` 生成，只校验登记、元数据与引用关系。supported是逐项审阅结论，不是脚本通过网页访问或URL推断出的事实真值；不代表全文逐句或实验复现验收。

- 结论：PASS
- 登记来源：174
- 证据记录：195
- 原子承重 claim：71
- 已核验承重来源：67
- Registry 状态：unverified=24, verified=150
- 正文外部链接：132
- 来源类型：academic_paper=57, official_article=22, official_documentation=38, official_repository=47, platform_metadata=10
- Claim 类型：factual=1, historical_fact=2, research_result=34, vendor_claim=34
- 支撑状态：supported=71

## 错误

- 无。

## 警告

- 无。

## Claim 明细

| ID | 章节 | 类型 | 状态 | 来源 |
|---|---:|---|---|---:|
| C001 | 01 | historical_fact | supported | 1 |
| C002 | 01 | historical_fact | supported | 1 |
| C003 | 02 | research_result | supported | 1 |
| C004 | 03 | research_result | supported | 1 |
| C005 | 04 | research_result | supported | 1 |
| C006 | 04 | vendor_claim | supported | 1 |
| C007 | 13 | vendor_claim | supported | 1 |
| C008 | 13 | vendor_claim | supported | 1 |
| C009 | 14 | vendor_claim | supported | 2 |
| C010 | 14 | vendor_claim | supported | 1 |
| C011 | 15 | vendor_claim | supported | 1 |
| C012 | 15 | vendor_claim | supported | 1 |
| C013 | 16 | vendor_claim | supported | 1 |
| C014 | 16 | vendor_claim | supported | 3 |
| C015 | 17 | vendor_claim | supported | 2 |
| C016 | 20 | research_result | supported | 1 |
| C017 | 21 | research_result | supported | 1 |
| C018 | 19,22 | research_result | supported | 1 |
| C019 | 19,22,30 | research_result | supported | 1 |
| C020 | 21 | research_result | supported | 1 |
| C021 | 22 | research_result | supported | 2 |
| C022 | 23 | research_result | supported | 2 |
| C023 | 24 | research_result | supported | 2 |
| C024 | 11 | vendor_claim | supported | 1 |
| C025 | 05,08 | vendor_claim | supported | 1 |
| R20260919_D01 | 07,14 | vendor_claim | supported | 1 |
| R20260919_D02 | 14,18 | vendor_claim | supported | 1 |
| R20260919_D03 | 07,13 | vendor_claim | supported | 1 |
| R20260919_D04 | 13,18 | vendor_claim | supported | 1 |
| R20260919_D05 | 15,18 | vendor_claim | supported | 1 |
| R20260919_D06 | 15 | vendor_claim | supported | 1 |
| R20260919_D07 | 02,07,11,18 | vendor_claim | supported | 1 |
| R20260919_D08 | 02,18 | vendor_claim | supported | 1 |
| R20260919_D09 | 19,22,23,24,30 | research_result | supported | 1 |
| R20260919_D10 | 20,24,30 | research_result | supported | 1 |
| R20260919_D11 | 19,21,22,23,30 | research_result | supported | 1 |
| R20260919_D12 | 22,24,30 | research_result | supported | 1 |
| R20260919_D13 | 12,20,22 | research_result | supported | 1 |
| R20260919_D14 | 09 | research_result | supported | 1 |
| R20260919_D15 | 07,09 | research_result | supported | 1 |
| R20260919_D16 |  | vendor_claim | supported | 1 |
| R20260919_D17 |  | vendor_claim | supported | 1 |
| R20260919_D18 |  | research_result | supported | 1 |
| R20260919_D19 | 19,30 | research_result | supported | 1 |
| R20260919_D20 |  | research_result | supported | 1 |
| R20260919_D21 | 22,30 | research_result | supported | 1 |
| R20260919_D22 | 20,30 | research_result | supported | 1 |
| R20260919_D23 | 19,22,30 | research_result | supported | 1 |
| R20260919_D24 | 19,22 | research_result | supported | 1 |
| R20260919_D25 | 19,21 | research_result | supported | 1 |
| R20260919_D26 | 19 | research_result | supported | 1 |
| R20260919_D27 | 19,22 | research_result | supported | 1 |
| R20260919_D28 | 22 | vendor_claim | supported | 1 |
| R20260919_D29 | 22 | research_result | supported | 1 |
| R20260919_D30 | 12 | vendor_claim | supported | 1 |
| R20260919_D31 |  | research_result | supported | 1 |
| R20260919_D37 | 25 | vendor_claim | supported | 1 |
| R20260919_CLAUDE_CONFIG | 13 | vendor_claim | supported | 1 |
| R20260919_MANAGED_SPLIT | 13,18 | vendor_claim | supported | 1 |
| R20260919_CURSOR_DATA | 15,18 | vendor_claim | supported | 1 |
| R20260919_CURSOR_PROJECTS | 15 | vendor_claim | supported | 1 |
| R20260919_CURSOR_HOOK_BOUNDARIES | 15 | vendor_claim | supported | 1 |
| R20260919_DSH_INSTALL | 16 | vendor_claim | supported | 1 |
| R20260919_OPENHANDS_PERSIST | 17 | vendor_claim | supported | 2 |
| R20260919_OPENHANDS_CONTAINER | 17 | vendor_claim | supported | 1 |
| R20260919_MCP_STATELESS | 08 | vendor_claim | supported | 1 |
| R20260919_HARNESSDEV_HOLDOUT | 19,22,24 | research_result | supported | 1 |
| R20260919_HARNESSBANK_GATES | 22 | research_result | supported | 1 |
| R20260919_SOLPI_MECHANISMS | 22 | research_result | supported | 1 |
| R20260919_JIT_FROZEN | 23 | research_result | supported | 1 |
| R20260919_CODEX_PROBE | 14 | factual | supported | 2 |

## 未登记的正文链接

- 无。

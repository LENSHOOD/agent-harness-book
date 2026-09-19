# Evidence registry 状态

本目录维护来源、历史证据及经过选择的承重主张。`claims_v2.jsonl` 是核心主张子集，不能代表全书逐句覆盖；`claims_backlog.jsonl`保存deferred研究线索及needs_review，不进入书稿strict core门；`claims.jsonl` 是未改写的旧段落级存量，不参与本轮主张判定。

<!-- registry-status: total=174 verified=150 unverified=24 -->

截至2026-09-19，本次 registry 共174条来源：150条 metadata verified、24条 unverified；证据195条；核心主张71条，状态为{'supported': 71}；backlog 1条。已核验仅指来源身份、指定版次及本地捕获定位；不等于逐句事实认证、实验复现或产品端到端通过。

本轮合并已存增量研究、固定仓库/API证据、各篇新增引用及执行摘要；补查快照按脚本实际读取时的文件集合登记。所有来源仍使用五种 source_type：`academic_paper`、`official_documentation`、`official_article`、`official_repository`、`platform_metadata`。社区资料映射为 platform_metadata，标记 community_discovery_only 与 core_claim_eligible=false，不进入承重claims。

原71条证据保留ID与内容：69条标为 `legacy_paraphrase`，其 `quote` 字段是历史转述，不作为直接引文；其余必须有本次逐字匹配定位。新证据区分 `direct_quote` 与 `source_summary`，同时记录 capture文件SHA-256、解码文本SHA-256、JSON pointer、字符/行定位及中文摘要。直接引文按来源作品/版次合计不超过25个英文词；别名不会获得额外额度。对summary的语义支撑是人工限定判断，脚本只验证定位和完整性。

GSME旧source ID钉住arXiv:2607.13683v1并保留错误v2元数据的历史记录；HarnessBank v2另有来源/证据，C019改用v2。C009补协议传输与方法枚举，C014拆dsh两执行路径，C015拆OpenHands旧Runtime与当前SDK；增加托管/自管、九月产品变化、进化论文及MCP2026-07-28的窄主张。版本化arXiv URL必须与version_or_commit匹配，abs/html同版通过url_aliases关联。

当前正文引用中，元数据未核验URL有0个；未绑定当前可复核捕获的URL有0个，两者含义不同。逐项清单、全部核心主张及状态见 `research/audits/revision_20260919/disposition_evidence.md`。旧的supported不自动继承；缺少原文绑定的主张保留needs_review。

离线整合：`python3 publishing/scripts/integrate_revision_evidence.py --write`；只读一致性检查：同脚本 `--check`。脚本只写本目录五文件与上述处置报告，不写历史claims.jsonl、run_manifest、正文或出版产物。audit_claim_ledger.py仍要求核心承重主张supported，不能通过改状态掩盖缺项；是否支持url_aliases以主代理维护的当前审计器为准。审计仅调用validate()，不调用会写其他报告的main()。

# Findings

Initial gh checks: local codex 0.142.5; official latest non-prerelease Codex rust-v0.155.1 published 2026-09-18T20:03:04Z; OpenHands v1.20.0 published 2026-09-17T07:15:18Z. Book chapter 14 currently uses turn/cancel, item/start and item/update. These require verification against the generated protocol, not inference from names.

Local Codex standard and experimental JSON schemas generated successfully under a network-denying, write-scoped macOS sandbox. Neither schema contains turn/cancel, item/start, item/update; both contain turn/interrupt, item/started, item/agentMessage/delta. The first stdio initialize attempt exited with Operation not permitted before replying; record as failed initialization, not a successful handshake.

dsh baseline cd5ef814 is 2026-08-27; target ddefc45 is 2026-09-17. VM source sandbox.ts is byte-identical and explicitly says node:vm is NOT containment (host-realm functions remain an escape route). New Plugin Manager, YAML-owned HMR and nontransactional Loader changes are material. Layer order and whole-config replacement already existed.

OpenHands baseline README already describes Agent Canvas and separate SDK ownership. SDK latest v1.49.2 (2026-09-17), baseline stable v1.44.0 (2026-08-27). Thus the overall separation is an older capability, not a September launch.

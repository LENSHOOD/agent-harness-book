# 公开发布前终验记录

终验日期：2026-08-28

适用内容版本：git `34be37385ee792592a25ce758ab4b136d3a584b9`

## 1. 发布前新增发现

在按发布流水线重新生成 PDF 时，旧产物与新产物页数、文件大小相同，但 blob 不同。根因有两处：ReportLab 默认写入构建时间与随机文档 ID；书签键使用 Python 进程级随机化的 `hash()`。这意味着此前“生成流程可复现”的结论只覆盖结构和内容，没有达到字节级可复现。

本轮启用 ReportLab invariant 模式，并在 Markdown 解析阶段为标题生成基于稳定序号、层级和文本的 SHA-256 书签键。GitHub Actions 新增二次渲染校验：保存第一次 SHA-256，再运行同一渲染器，任何字节差异都会使发布失败。

## 2. 本地终验结果

- Claim ledger：PASS，25/25 supported。
- 书稿结构：PASS，30 个规范章标题。
- VitePress production build：PASS。
- 完整版 PDF：135 页、257,594 个可提取字符、0 替换字符、0 空白页。
- 管理层版 PDF：14 页、3,723 个可提取字符、0 替换字符、0 空白页。
- PDF 与站点下载副本逐字节一致。
- 两个独立渲染进程得到相同 SHA-256：完整版 `177a984e55c355f719dfb40db854fa04fc1ee38ddc0af2b7fded8a4efc197604`；管理层版 `ecdb0b526f5a3a912dce0e983b08f828f2398ac7986f3015167862f74e2fcd06`。
- npm 生产依赖审计为 0 漏洞。完整开发依赖树报告 2 个 moderate、1 个 high，均来自 Vite/VitePress 本地开发服务器链，当前无 npm 自动修复版本；发布物是静态文件，不携带该运行时。

## 3. 审查边界

本机 Codex CLI 的独立 review 因 CLI 版本不支持当前模型而中断，没有把失败运行伪装为通过。发布判断依赖已经闭环的五份独立审阅记录、本轮人工差异审查及上述机器门禁。远端 GitHub Actions 与 GitHub Pages 状态在合并后另行验收。

## 4. 本地判定

内容版本 `34be37385ee792592a25ce758ab4b136d3a584b9` 通过本地发布前门禁，可以进入 PR、合并与 GitHub Pages 远端验收阶段。

import { defineConfig } from 'vitepress'
import bookStructure from '../../../publishing/book_structure.json'

const ch = (n: string, text: string) => ({ text, link: `/chapters/${n}` })
const partSidebar = bookStructure.parts.map((part) => ({
  text: part.title,
  collapsed: false,
  items: [
    { text: '本篇导言', link: `/parts/${part.intro}` },
    ...part.chapters.map((chapter) => ch(chapter.slug, chapter.title))
  ]
}))

export default defineConfig({
  lang: 'zh-CN',
  title: 'Agent Harness',
  description: '从执行脚手架到自我进化系统：企业 Agent 平台架构与工程实践',
  base: '/agent-harness-book/',
  cleanUrls: true,
  lastUpdated: true,
  head: [
    ['meta', { name: 'theme-color', content: '#075985' }],
    ['meta', { property: 'og:type', content: 'book' }],
    ['meta', { property: 'og:title', content: 'Agent Harness：从执行脚手架到自我进化系统' }],
    ['meta', { property: 'og:description', content: '企业 Agent 平台架构、主流 Harness 与受控进化' }]
  ],
  themeConfig: {
    logo: '/logo.svg',
    siteTitle: 'Agent Harness',
    nav: [
      { text: '在线阅读', link: '/chapters/00_preface' },
      { text: '精简版', link: '/executive-brief' },
      { text: '下载 PDF', link: '/agent-harness-book/downloads/agent_harness_book.pdf' },
      { text: 'GitHub', link: 'https://github.com/LENSHOOD/agent-harness-book' }
    ],
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: '搜索', buttonAriaLabel: '搜索' },
          modal: {
            noResultsText: '没有找到相关内容',
            resetButtonTitle: '清除查询',
            footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' }
          }
        }
      }
    },
    sidebar: [
      {
        text: '序',
        items: [ch(bookStructure.preface.slug, bookStructure.preface.title)]
      },
      ...partSidebar,
      {
        text: '附录', collapsed: true,
        items: [
          { text: '核心接口与伪代码', link: '/appendices/A_core_contracts_and_pseudocode' },
          { text: '架构评审检查表', link: '/appendices/B_architecture_review_checklist' },
          { text: '术语表', link: '/appendices/C_glossary' },
          { text: '概念索引', link: '/appendices/D_concept_index' },
          { text: '机器可读契约', link: '/appendices/E_machine_readable_contracts' },
          { text: '完整参考文献', link: '/references' }
        ]
      }
    ],
    outline: { level: [2, 3], label: '本页目录' },
    sidebarMenuLabel: '目录',
    returnToTopLabel: '返回顶部',
    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    docFooter: { prev: '上一章', next: '下一章' },
    lastUpdated: { text: '最后更新' },
    socialLinks: [{ icon: 'github', link: 'https://github.com/LENSHOOD/agent-harness-book' }],
    footer: { message: '公开阅读版本', copyright: 'Copyright © 2026 Lenshood' }
  },
  markdown: { lineNumbers: false },
  sitemap: { hostname: 'https://lenshood.github.io/agent-harness-book/' }
})

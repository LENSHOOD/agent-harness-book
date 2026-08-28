import { defineConfig } from 'vitepress'

const ch = (n: string, text: string) => ({ text, link: `/chapters/${n}` })

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
      { text: '下载 PDF', link: '/downloads/agent_harness_book.pdf' },
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
        items: [ch('00_preface', '为什么现在需要一本 Harness 小书')]
      },
      {
        text: '第一篇 历史', collapsed: false,
        items: [
          { text: '本篇导言', link: '/parts/01_history' },
          ch('01_from_control_loop_to_agent_runtime', '1. 从控制循环到 Agent Runtime'),
          ch('02_the_autonomous_agent_boom', '2. 自主 Agent 爆发与第一次祛魅'),
          ch('03_interface_is_part_of_intelligence', '3. 接口也是智能'),
          ch('04_the_coding_agent_turn', '4. Coding Agent 转折')
        ]
      },
      {
        text: '第二篇 原理', collapsed: false,
        items: [
          { text: '本篇导言', link: '/parts/02_principles' },
          ch('05_system_model_and_responsibility_boundaries', '5. 系统模型与责任边界'),
          ch('06_agent_loop_as_a_durable_state_machine', '6. Agent Loop 与持久状态机'),
          ch('07_context_cache_compaction_and_memory', '7. 上下文、压缩与记忆'),
          ch('08_tools_aci_mcp_and_code_mode', '8. 工具、ACI、MCP 与 Code Mode'),
          ch('09_permissions_sandbox_credentials_and_supply_chain', '9. 权限、沙箱与供应链'),
          ch('10_verification_completion_contracts_and_evidence_packages', '10. 验证、完成契约与证据包'),
          ch('11_multi_agent_delegation_and_collaboration_topologies', '11. 多 Agent 与协作拓扑'),
          ch('12_observability_traces_and_eval_operations', '12. 可观测性与评测运营')
        ]
      },
      {
        text: '第三篇 产品', collapsed: false,
        items: [
          { text: '本篇导言', link: '/parts/03_products' },
          ch('13_claude_code_thin_loop_thick_runtime', '13. Claude Code'),
          ch('14_openai_codex_protocolized_agent_core', '14. OpenAI Codex'),
          ch('15_cursor_ide_native_context_and_cloud_agents', '15. Cursor'),
          ch('16_deepseek_harness_composable_runtime', '16. DeepSeek Harness'),
          ch('17_openhands_agent_runtime_separation', '17. OpenHands'),
          ch('18_product_comparison_and_architecture_spectrum', '18. 产品横向比较')
        ]
      },
      {
        text: '第四篇 进化', collapsed: false,
        items: [
          { text: '本篇导言', link: '/parts/04_evolution' },
          ch('19_evolution_is_an_engineering_control_loop', '19. 进化是工程控制循环'),
          ch('20_within_task_evolution_search_reflection_and_repair', '20. 任务内进化'),
          ch('21_cross_task_memory_skills_and_experience', '21. 跨任务经验化'),
          ch('22_harness_evolution_prompts_tools_context_and_workflows', '22. Harness 进化'),
          ch('23_model_evolution_from_trajectories', '23. 模型进化'),
          ch('24_governed_evolution_loop', '24. 受控进化闭环')
        ]
      },
      {
        text: '第五篇 实践', collapsed: false,
        items: [
          { text: '本篇导言', link: '/parts/05_practice' },
          ch('25_three_end_to_end_cases', '25. 三个端到端案例'),
          ch('26_next_generation_enterprise_harness_architecture', '26. 企业 Harness 参考架构'),
          ch('27_agent_sdd_specification_driven_delivery', '27. Agent SDD'),
          ch('28_maturity_model_and_build_vs_buy', '28. 成熟度与 Build-vs-Buy'),
          ch('29_from_vendor_agents_to_owned_runtime', '29. 从接入到自研 Runtime'),
          ch('30_outlook_harness_os_and_evolving_agent_organizations', '30. 展望')
        ]
      },
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

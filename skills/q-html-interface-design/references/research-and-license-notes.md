# Research And License Notes

This skill was created from idea-level learning only. Do not copy external
code, prompts, schemas, text, images, or assets from the references below
without a separate license check and attribution record.

## External Sources Used As Idea References

| Source | Role | License / Safe-Use Posture | Influence |
|---|---|---|---|
| W3C WCAG 2.2 | Primary accessibility standard | Public standard; use as guidance, not copied text | Contrast, focus, target size, accessible controls |
| Nielsen Norman Group usability heuristics | Usability evaluation reference | Article/reference; no copied text | Status visibility, consistency, error prevention, recognition over recall |
| IBM Carbon dashboards | Mature dashboard design system | Open design guidance; idea-level use only | Dashboard types, KPI overview, structured layout |
| USWDS data visualizations | Public design-system guidance | Public government guidance; idea-level use only | Simple chart types, accessibility plus usability |
| Vercel Web Interface Guidelines | Agent-friendly web interface rules | Repository appears permissively licensed in public indexes, but no copied text | Review categories: forms, layout, animation, accessibility, performance |
| Anthropic `frontend-design` skill / plugin | Official frontend-design skill reference | Public source; no copied text, prompts, code, or assets | Pattern: choose a specific visual direction before implementation and avoid generic AI-looking UI |
| KAOPU-XiaoPu `web-design` | Community HTML/web design skill | MIT repository; no copied text, prompts, code, CSS, or assets | Pattern: durable design spec before code and post-implementation self-audit |
| Mermaid documentation | Diagram syntax reference | Open-source documentation; idea-level use only | Mermaid as documentation-native diagram option |
| `nextlevelbuilder/ui-ux-pro-max-skill` | Public UI skill prior art | No copied text or prompts | Pattern: skill routes UI tasks through design-system generation and review |
| `plugin87/ux-ui-agent-skills` | Public UI skill prior art | No copied text or prompts | Pattern: token-driven UI, accessibility, component states |
| `pixelact-ui/pixelact-ui` | Pixel style component prior art | No copied code/assets | Pattern: pixel style works best as a component/tokens layer, not random decoration |
| agentskill dashboard entries | Marketplace prior art | No copied text or skill bodies | Pattern: self-contained dashboard skill with KPI cards/charts/tables |
| GitHub Primer / Product UI | Design system reference | Idea-level use unless a separate license check allows copying | Dense developer UI, tables, action hierarchy |
| Grafana dashboard best practices | Product documentation | Idea-level use only | Observability dashboard structure and audience-first design |
| GOV.UK Design System | Public service design reference | Idea-level use only | Accessible forms, plain-language service patterns |
| shadcn/ui | Open-source component ecosystem | License-check before copying components | Clean composable component defaults |
| NES.css / 98.css / retro CSS families | Open-source style prior art | License-check before copying CSS/classes | Pixel/retro component language |
| Duolingo / Atlassian / Mailchimp references | Brand/playful design references | Do not copy brand assets, mascots, color identity, or writing | Cartoon/playful style calibration |
| Maggie Appleton / Josh W. Comeau / Brittany Chiang | Personal-site references | Do not copy illustrations, demos, source, or layout wholesale | Personal website structure, technical storytelling, interaction ideas |

## Local Sources Used As Owned Pattern References

| Local Artifact | Useful Pattern |
|---|---|
| `owned-patterns/ppt-intake-wizard.html` | Left step rail, form panels, choice cards, local runner fallback, JSON copy/download, status line |
| `q-workflow/scripts/token_usage.py` HTML dashboard | Console-dark status header, KPI cards, mix bars, health advice, dense tables, responsive grids |
| `q-project-overview/scripts/generate_project_overview_html.py` | Markdown-to-readable static HTML, Mermaid block support, simple article styling |
| `reports/skill_learning_validation_deck/layout_engine_v0_preview_v2.html` | Fixed-format slide preview, card/grid consistency, component centerline and connector validation lessons |

## Safe-Use Rule

When a future task wants to import a third-party UI kit, skill, template,
prompt, screenshot, or design token file, stop and perform a task-specific
license check before copying. This skill only preserves independently written
rules and local owned patterns.

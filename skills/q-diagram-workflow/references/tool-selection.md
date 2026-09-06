# Diagram Tool Selection

This file records reusable source-discovery conclusions. Use ideas and tool
categories only; do not copy third-party code, text, schemas, or assets.

## Default Choices

| Need | Preferred source format | Why |
|---|---|---|
| Connector pinouts, cables, wiring harnesses | WireViz YAML | Purpose-built for cables, connectors, pinouts, and generated SVG/PNG outputs. |
| Editable training/customer figure | draw.io `.drawio` | Human-editable source with common export formats. |
| Training slide-style figure in Markdown | PowerPoint `.pptx` plus exported PNG | Easy manual editing, direct PNG export, and compatible with PPT visual review habits. |
| Architecture or software/data flow | D2 | Text source, multiple layout engines, and CLI export to common formats. |
| Directed dependency/state graph | Graphviz DOT | Mature automatic layout for directed graphs. |
| Markdown-native quick flowchart | Mermaid | Easy to embed in Markdown where Mermaid rendering is supported. |
| Mixed diagram render service | Kroki | Unified API/self-host path for many diagram-as-code formats. |

## Practical Rule For Wiring Training Docs

For a training handson, avoid a dense pin-to-pin graphic. Use:

1. one overview figure showing board roles, grouped signal directions, power,
   USB/debug, and motor connection;
2. one connection table with exact pins and checks;
3. optional WireViz/draw.io source if a polished printable wiring figure is
   needed.

## Source Notes

- WireViz project: documents cables, wiring harnesses, connector pinouts, and
  generates graphical output from YAML using Graphviz.
  URL: https://github.com/wireviz/WireViz
- draw.io/diagrams.net: official documentation covers exports and the official
  MCP server for creating/opening diagrams in the draw.io editor.
  URL: https://www.drawio.com/docs/
  URL: https://www.drawio.com/docs/manual/generate/drawio-mcp-server/
- Public draw.io skills commonly generate native `.drawio` files and optionally
  export PNG/SVG/PDF, which is a useful pattern for editable AI-generated
  diagrams.
  URL: https://github.com/jgraph/drawio-mcp/tree/main/skill-cli
- D2: diagram scripting language with layout engine selection and CLI export to
  SVG/PNG/PDF/PPTX/GIF/ASCII.
  URL: https://d2lang.com/tour/layouts/
  URL: https://d2lang.com/tour/exports/
- Public D2 skills commonly keep a diagram-as-code source and render it, which
  is a useful pattern for repeatable architecture diagrams.
- Graphviz: DOT language and layout engines; `dot` is intended for directed
  graphs with edges generally aimed in one direction.
  URL: https://graphviz.org/doc/info/lang.html
  URL: https://graphviz.org/docs/layouts/dot/
- Kroki: unified HTTP API/self-host option for many text diagram formats.
  URL: https://docs.kroki.io/kroki/
- PowerPoint: `Slide.Export` can export a slide to an image file, making PPTX
  a practical editable source for Markdown PNG figures.
  URL: https://learn.microsoft.com/en-us/office/vba/api/powerpoint.slide.export

## License Posture

This skill uses the public sources above only as product/tool-selection
references. It does not copy code, prompts, schemas, text, images, or assets
from those projects.

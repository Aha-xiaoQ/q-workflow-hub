#!/usr/bin/env python3
"""Generate PROJECT_OVERVIEW.html from PROJECT_OVERVIEW.md."""

from __future__ import annotations

import argparse
import html
from pathlib import Path
import re


def render_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    out: list[str] = []
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    in_list = False
    in_table = False

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    for line in lines:
        if line.startswith("```"):
            if in_code:
                escaped = html.escape("\n".join(code_lines))
                if code_lang == "mermaid":
                    out.append(f'<div class="mermaid">{escaped}</div>')
                else:
                    out.append(f'<pre><code>{escaped}</code></pre>')
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                close_list()
                close_table()
                in_code = True
                code_lang = line.strip("`").strip().lower()
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            close_list()
            close_table()
            continue

        if line.startswith("|") and line.endswith("|"):
            cells = [render_inline(c.strip()) for c in line.strip("|").split("|")]
            if all(set(c.replace(" ", "")) <= {"-", ":"} for c in cells):
                continue
            if not in_table:
                out.append("<table><tbody>")
                in_table = True
            tag = "th" if "<th>" not in "".join(out[-2:]) and len(out) > 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>")
            continue
        close_table()

        if line.lstrip().startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{render_inline(line.lstrip()[2:].strip())}</li>")
            continue
        close_list()

        if line.startswith("#"):
            level = min(len(line) - len(line.lstrip("#")), 3)
            text = line[level:].strip()
            anchor = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
            out.append(f'<h{level} id="{anchor}">{render_inline(text)}</h{level}>')
            continue

        out.append(f"<p>{render_inline(line.strip())}</p>")

    close_list()
    close_table()
    return "\n".join(out)


def build_html(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    :root {{
      --bg: #f7f8fa;
      --panel: #ffffff;
      --ink: #18212f;
      --muted: #5b6472;
      --line: #d9dee7;
      --accent: #00a3a3;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font: 15px/1.55 "Segoe UI", Arial, sans-serif;
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 24px 56px;
    }}
    article {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 28px;
      box-shadow: 0 1px 3px rgba(18, 28, 45, 0.06);
    }}
    h1, h2, h3 {{ line-height: 1.2; margin: 1.2em 0 0.45em; }}
    h1 {{ margin-top: 0; font-size: 32px; }}
    h2 {{ font-size: 22px; border-top: 1px solid var(--line); padding-top: 20px; }}
    h3 {{ font-size: 17px; }}
    p, li {{ color: var(--ink); }}
    code {{
      background: #eef2f6;
      border: 1px solid #dfe5ec;
      border-radius: 4px;
      padding: 1px 4px;
      font-family: Consolas, monospace;
    }}
    pre {{
      overflow: auto;
      background: #111827;
      color: #f4f7fb;
      border-radius: 6px;
      padding: 14px;
    }}
    pre code {{ background: transparent; border: 0; color: inherit; padding: 0; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 14px 0 20px;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 8px 10px;
      vertical-align: top;
    }}
    th {{ background: #eef6f6; text-align: left; }}
    a {{ color: var(--accent); }}
    .mermaid {{
      background: #fbfcfe;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      margin: 16px 0;
      overflow: auto;
    }}
    .note {{ color: var(--muted); font-size: 13px; margin-top: 24px; }}
  </style>
</head>
<body>
  <main>
    <article>
{body}
      <p class="note">Generated from PROJECT_OVERVIEW.md. Mermaid diagrams require local or network access to the Mermaid renderer.</p>
    </article>
  </main>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose' }});
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--input", default="PROJECT_OVERVIEW.md")
    parser.add_argument("--output", default="PROJECT_OVERVIEW.html")
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    source = project_root / args.input
    target = project_root / args.output
    if not source.exists():
        raise SystemExit(f"missing source file: {source}")

    markdown = source.read_text(encoding="utf-8")
    title = next((line.lstrip("#").strip() for line in markdown.splitlines() if line.startswith("# ")), source.stem)
    body = markdown_to_html(markdown)
    target.write_text(build_html(title, body), encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Style Directions

Use this reference when the user asks for a technology, pixel, cartoon, clean,
or similarly opinionated visual direction.

## Common Rules

- Pick one dominant style and one supporting style. Do not combine technology,
  pixel, cartoon, and clean at full strength in the same page.
- Preserve task clarity. Style is allowed to make the page memorable, not to
  hide labels, reduce contrast, or increase scanning cost.
- Define palette, shape language, typography, icon/illustration treatment, and
  motion before coding.
- Convert broad labels into a specific visual premise. `Technology style` is a
  category; `firmware build cockpit` or `observability workbench` is a design
  direction.

## Technology Style

Best for observability, review reports, build/run status, embedded workflows,
and engineering dashboards.

- Premises: observability console, lab instrument panel, firmware build
  cockpit, data-review workbench, or developer-docs tool.
- Palette: neutral background, white or console-dark panels, cyan/green/blue
  accents, warn/danger colors reserved for state.
- Shapes: crisp panels, 1 px borders, compact radius, metric bars, terminal-like
  code chips, subtle grid/table structure.
- Useful motifs: status strips, circuit-like dividers, data mix bars, numbered
  lanes, monospace snippets.
- Avoid: neon overload, dark-on-dark text, fake 3D chrome, illegible glow.

## Pixel Style

Best for playful tools, retro demos, games, personal pages, and lightweight
experiments.

- Premises: OS-window nostalgia, terminal adventure, handheld-console UI,
  pixel badges in a clean portfolio, or retro status monitor.
- Use an integer spacing grid and sharp edges.
- Use hard shadows, stepped borders, and pixel-friendly icons.
- Keep text large enough; pixel styling fails quickly when labels are tiny.
- Use few colors and high contrast.
- Avoid applying pixel style to dense enterprise forms unless the user
  explicitly wants that tradeoff.

## Cartoon Style

Best for onboarding, learning tools, kid-friendly or playful explainers, and
friendly team demos.

- Premises: friendly onboarding companion, lab-notebook doodle, learning map,
  or light explainer frame around conventional engineering data.
- Use warm accent colors, simple rounded shapes, and optional small
  illustrations.
- Use character or mascot-like visuals only when they support the subject.
- Keep forms and data tables conventional even if the surrounding frame is
  playful.
- Avoid stock-like decoration, excessive shadows, and low-information art.

## Clean / Minimal Style

Best for daily engineering tools, configuration pages, review reports, and
professional handoff artifacts.

- Premises: quiet project archive, compact admin console, editorial technical
  portfolio, or compliance/checklist form.
- Use whitespace, restrained color, clear alignment, and strong typography
  hierarchy.
- Use borders before heavy shadows.
- Let data and controls carry the design.
- Avoid empty minimalism: every section still needs labels, states, and
  actionable content.

## Choosing A Direction

| Need | Choose |
|---|---|
| Repeated work, team, organization, or team tools, review pages | Clean with technology accents |
| Debug/run observability | Technology |
| Personal or creative prototype | Pixel or cartoon |
| Dense forms and dashboards | Clean first, style second |
| Diagram/explainer for nontechnical audience | Clean plus light cartoon |

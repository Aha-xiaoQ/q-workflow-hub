# HTML Visual Quality

Use this reference when `PROJECT_OVERVIEW.html` is meant for sharing, onboarding, executive scanning, or repeated project recovery, or when the generator/custom page needs visual changes.

`PROJECT_OVERVIEW.html` should feel like a restrained engineering project microsite, not a marketing landing page. Before changing the generator or a custom overview page, define a small visual grammar: audience, information priority, density, accent color, typography, diagram treatment, and navigation needs.

Prefer:

- quiet full-width sections or an unframed document layout over nested cards;
- one clear project title/status area, then scannable sections for outputs, map, commands, risks, and next steps;
- existing project context first: repo purpose, real diagrams, generated outputs, screenshots, PPT covers, or firmware/demo artifacts should shape the page before any generic theme choice;
- real project artifacts, diagrams, or screenshots only when they help the reader understand the project state;
- for visually important shared pages with unclear style, create or describe two to three concrete directions and pick one before applying it across the whole page;
- visual validation at desktop and narrow widths when the HTML is meant to be shared or reused.

Avoid generic hero marketing composition, decorative gradient blobs, crowded card grids, and style changes that make the Markdown source harder to maintain.

Minimal validation:

- regenerate `PROJECT_OVERVIEW.html` from the Markdown source;
- open or screenshot the page at desktop and narrow widths when it is user-facing;
- verify Mermaid fallback/readability if the CDN is unavailable;
- keep Markdown source maintainable and do not move project facts into generated-only HTML.

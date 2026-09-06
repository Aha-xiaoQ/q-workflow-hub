# Context Budget Design

Use this reference when optimizing token use, splitting large workflow files,
or deciding how much local context to read before acting.

## Principle

Minimize context by default, but do not hide decision-critical facts. The goal
is the smallest context set that makes the next action safe, reversible, and
recoverable.

## Token Health Loop

Use `scripts/token_usage.py --format html --open` when Xiao Q asks about token
usage or when a long session starts to feel heavy. Interpret the dashboard as a
local workflow signal, not an official bill.

Optimization target:

- Preserve a stable high cache ratio when it comes from repeated system,
  developer, skill, and project-routing context.
- Reduce total context only when it also lowers uncached input, output, or
  context pressure.
- Do not treat high `Cached%` as a problem by itself.

Health checks:

| Signal | Healthy | Watch | Action |
|---|---|---|---|
| Context pressure | below 65% latest turn context | 65-85% watch, above 85% high | checkpoint durable state, narrow the next task, or resume from saved state in a fresh session; if this is a workflow-rule/release/customer handoff task, recommend `workflow-health` / `体检` before expanding rules further |
| Cache ratio | high cached input with low uncached input | low cache on long inputs | keep static routers stable; avoid moving dynamic content ahead of stable instructions |
| Uncached input | targeted excerpts and summaries | broad full-file/log reads | use `rg`, headings, `Select-Object`, summaries, and artifact paths before opening large files |
| Output share | concise handoff by default | long answers or reasoning-heavy turns dominating cost | shorten final replies unless the user requested review, design, docs, or detailed analysis |
| Efficiency trend | input stable, cache spread low, cache savings high | high cached ratio but input growth high, cache spread high, or savings weak | treat as possible false-high cache; checkpoint, summarize, split context, stabilize the prompt prefix, and recommend `workflow-health` / `体检` when the bloat affects workflow or release decisions |

## Summary Artifacts Before Rows

When answering benchmark, audit, token, visual-review, or generated-report
questions, prefer machine summaries, headings, stats, and paths before reading
full row payloads or long Markdown reports. For workflow benchmark cost
questions, run the benchmark summary extractor when available and cite
`variant_summary` deltas first; inspect raw rows only for failed lanes, scorer
disputes, missing telemetry, or user-requested evidence.

This is a Project-tier, allow-risk optimization: it may run local read-only
summary scripts and targeted `rg`/heading searches, but it should not expand
into broad report reads merely to improve narrative completeness.

## Autonomous Context Governor

Use `scripts/context_governor.py --format text` as the lightweight preflight
before broad scans, multi-repo closure, deep research, long PPT/code loops,
skill updates, or sub-agent orchestration. The script wraps `token_usage.py`,
classifies the latest-turn pressure, flags cache instability, and can write a
compact task packet with `--packet-out <path>`.

Default gates:

| Level | Signal | Action |
|---|---|---|
| `ok` | latest context pressure below 60% and stable trend | continue with targeted reads and normal validation |
| `watch` | pressure 60-70%, cache spread above 50 pp, or input growth returns | write a task packet before starting another broad segment |
| `throttle` | pressure 70-85% or rising pressure plus unstable cache | finish validation/checkpoint first; avoid broad scans and long reports |
| `critical` | pressure at or above 85% | do not start a new broad task; checkpoint and resume from durable state in a fresh/compacted segment |

Allowed autonomous actions:

- run read-only token health checks;
- reduce read breadth and use `rg`, headings, stats, and file paths before full
  file loads;
- write or update a local task packet, active work item, or recovery note;
- after a recommended checkpoint or closed work node, automatically write a
  compact entry packet when the gate is `watch`, `throttle`, or `critical`;
- recommend a fresh session when the remaining work is not tiny.

Not allowed:

- pretending local files can shrink the already-loaded platform context;
- automatic pushes, public sync, destructive cleanup, or secret handling;
- carrying full logs, JSON dashboards, research dumps, or sub-agent essays in
  chat when a path and summary are enough.

## Entry Packet Budget

Compression entries are intentionally smaller than work reports. Use them as
recovery indexes with a key evidence chain, not as narrative summaries.

- Target 1-2 KB for normal entries; avoid exceeding about 3 KB.
- Include paths, commit ids, validation anchors, and next action.
- Do not include full logs, long diffs, research dumps, or sub-agent reports.
- Read linked evidence only on ambiguity, conflict, failure, or user request.

## Cache Stability Protocol

Use this protocol when `TOKEN` shows high cache-ratio spread, context pressure
above about 60%, or a session is about to start another broad research,
multi-agent, or skill-update task.

Goals:

- Keep stable instructions, skill routers, and source-of-truth pointers early
  and unchanged.
- Move dynamic content such as search results, sub-agent reports, visual review
  output, token JSON, long logs, and generated artifacts into files or late
  task-specific context.
- Continue work from a compact task packet instead of carrying the whole chat
  narrative.

Actions:

1. **Checkpoint first at 60-70% pressure.** Before another broad task, record
   the objective, authoritative files, changed files, validation status, and
   next command in durable state or a task packet.
2. **Use a task packet for the next segment.** Include only:
   - objective;
   - source-of-truth paths;
   - current state;
   - constraints and no-edit zones;
   - next 1-3 actions;
   - validation command or evidence target;
   - residual risks.
3. **Keep dynamic research late and bounded.** Put web/source findings, large
   excerpts, and sub-agent outputs in reports; pass only summaries and paths
   forward.
4. **Stabilize skill surfaces.** Prefer editing on-demand references over
   changing `SKILL.md` when the trigger/router does not need to change.
5. **Split high-pressure work.** Above about 70% pressure, finish the current
   validation or checkpoint before starting a new large branch. Above 85%,
   strongly prefer a fresh session from durable state unless the remaining
   action is tiny.

Avoid:

- pasting full JSON dashboards, full visual reports, or long sub-agent outputs
  into the main context when a path and summary are enough;
- asking multiple research sub-agents to produce essay-length reports;
- changing always-loaded routers for rare or experimental behavior;
- treating a high latest-turn cache ratio as healthy when cache spread is high
  and the task context is still growing.

Official prompt-cache basis checked on 2026-06-20: OpenAI prompt caching works
best when shared prompt prefixes remain stable, and latency guidance recommends
placing dynamic portions such as RAG results or history later in the prompt.
Local q-workflow turns this into stable routers, on-demand references, bounded
task packets, and dynamic-output handoff by file path.

## Task Packet Shape

Use this compact shape before continuing a broad or high-pressure workflow:

```text
TASK-PACKET v1
objective:
source_of_truth:
current_state:
changed_files:
constraints:
no_edit_zones:
next_actions:
validation:
handoff_paths:
residual_risks:
```

The task packet is not a replacement for project state. It is a short bridge
that lets the next segment avoid reloading full chat history or long reports.

Read order:

1. Use `Latest Turn` to decide what to do next in the current conversation.
2. Use `Current Session` to decide whether the whole chat is getting heavy.
3. Use `Active Project` and `Projects` to find recurring expensive workflows.
4. Use `Efficiency Trend` to distinguish real cache efficiency from context
   bloat hidden by high cached-token counts.
5. If cwd is a broad home directory, prefer transcript-inferred active project
   over treating the whole home folder as the project scope.

False-high-cache criteria:

- Recent latest-turn input grows quickly while cache ratio remains high.
- Cache ratio spread across recent events is large, suggesting an unstable
  prefix or frequent prompt-structure changes.
- Estimated cache savings are weak because uncached input or output/reasoning
  dominates the latest turn cost.

External calibration checked on 2026-06-17:

- OpenAI Prompt Caching exposes `cached_tokens` in usage details, activates for
  prompts at or above 1,024 tokens, and benefits from stable prefixes with
  static instructions/examples before dynamic user data.
- OpenAI `prompt_cache_key` can improve routing for workloads with shared long
  prefixes, but too many requests for the same prefix/key pair can overflow the
  cache route and reduce effectiveness. This is an API-side feature, not a
  local Codex JSONL setting.
- Extended prompt cache retention can improve cache locality when available in
  API integrations. Track as a future API/agent-integration feature, not as a
  current local dashboard control.
- Production LLM observability commonly tracks latency, token usage, cost, and
  dashboard comparisons by metric. For local Codex logs, only add latency-like
  metrics when the source timestamps represent real model latency rather than
  user/tool waiting time.
- Serving-layer systems such as vLLM define prefix-cache hit rate as queried
  tokens found in the cache divided by queried tokens. This reinforces using
  token-weighted cache hit rate, not only request-level hit/miss counts.

Future metrics to add only when reliable data exists:

| Metric | Use | Data requirement |
|---|---|---|
| TTFT / prefill latency | prove cache improves speed, not only cost | provider/API timing or reliable proxy trace |
| E2E latency and tokens/sec | catch slow responses, decode pressure, or tool wait | model/provider trace with start/end timestamps |
| cache-route saturation | detect same-prefix request bursts hurting hit rate | API request volume by `prompt_cache_key` and prefix |
| retention mode | compare in-memory vs extended cache behavior | API usage records with retention setting |
| request grouping | find expensive workflows by command, project, skill, or model | stable local metadata beyond cwd/transcript inference |
| error/retry rate | catch wasted tokens from failed or repeated calls | provider/proxy request status and retry metadata |

## Reading Tiers

| Tier | Trigger | Read |
|---|---|---|
| Micro | Exact fixed commands such as `help` / `帮助` | No tool reads when a stable answer is already known. |
| Quick | Resume/status with clear target | Routing state, active work item, one targeted `git status`. |
| Project | Named project resume or normal edit | Project state files and targeted sections. |
| Deep | Dirty, stale, contradictory, or agent-touched state | Relevant diffs, decisions, handoff notes, and source files. |
| Full | Cross-cutting rules, validation, or required skill load | Whole file only after stating why it is needed. |

## Activation And Risk Labels

New or revised rules should state their activation and risk posture when the
rule can affect context cost, file edits, commits, pushes, public sharing, or
credential handling.

Recommended fields:

- `Trigger`: concrete prompt, state, file pattern, or task condition.
- `Tier`: `Micro`, `Quick`, `Project`, `Deep`, or `Full`.
- `Risk`: `allow`, `ask`, or `deny`.
- `Reference`: the on-demand file that contains the detailed procedure.

Risk labels:

- `allow`: local, low-risk, recoverable reads or writes needed for the current
  task, such as targeted `git status`, `rg`, validation, or source/runtime
  mirror sync.
- `ask`: pushes, publishing, public/GitHub sync, destructive cleanup,
  credential handling, global configuration changes, or unclear blast-radius
  actions.
- `deny`: storing credentials/secrets, copying unclear-license material, moving
  private or restricted data into public artifacts, or bypassing user/admin security
  controls.

## File Structure Rules

- Keep `SKILL.md` as a router plus compact rules. Move long procedures,
  examples, and rare cases into `references/` or `workflows/`.
- Add a short table of contents or heading map to long state files before they
  exceed the suggested size in `TOKEN_BUDGET.md`.
- Split state into index and detail:
  - index: current focus, status, next action, changed files, validation gaps;
  - detail: dated work items, reports, logs, and artifact summaries.
- Prefer `rg`, `Select-String`, `git diff --stat`, file listings, and heading
  searches before opening long files.
- For generated artifacts, store path, hash, and summary; do not paste large
  exports into durable memory.

## Skill Design Rules

- Skill metadata should be specific enough to choose the right skill without
  reading it.
- The top of `SKILL.md` should route common cases to the smallest path.
- A selected skill may require full `SKILL.md` loading, so keep the file short
  and move detailed material out.
- If a skill grows beyond about 500 lines, either split the domain or turn the
  long sections into on-demand references.

## Stop Conditions

Stop reading more context when:

- the next action is clear and low risk;
- the missing detail is low impact and can be labeled as unknown;
- the user asked for a fixed command or micro answer;
- further reading would only improve narrative completeness, not correctness.

Escalate reading when:

- the worktree is dirty or touched by another agent;
- the instruction source is contradictory;
- the next action could commit, push, delete, publish, or expose private data;
- validation failed and the cause is not localized.

## Continuation Risk Control

Use this section before long, model-heavy, generated-artifact, or
interruption-prone work. Codex can compact long-task context automatically, so
the goal is not to prevent compaction; the goal is to make each next segment
recoverable from durable files if the chat or remote continuation fails.

Practical rules:

- Keep each work segment focused on one deliverable or one validation loop.
- Before starting an expensive or long-running segment, write or update the
  active work item with objective, current files, next command, and expected
  validation.
- After each meaningful substep, record one short checkpoint: completed step,
  changed files, validation status, and next action.
- Prefer resumable commands and deterministic scripts over one-off manual
  chat-only instructions.
- Store large outputs as files and summarize their paths; do not paste large
  logs, deck exports, or generated reports into active context.
- If the same task has already compacted or failed once, reduce the next segment
  size before continuing: fewer files, one artifact, one validation command, or
  one explicit decision.

Avoid:

- continuing a long failed window without updating durable state;
- broad scans or full-file reads just to rebuild narrative context;
- running expensive validation after recovery before comparing durable state
  with the latest user-visible request.

Official-doc basis checked on 2026-06-13: OpenAI Codex prompting guidance says
long tasks may automatically compact context; Codex best-practice guidance
recommends keeping durable guidance concise and updating durable instructions
after repeated mistakes. Local workflow rules turn that into rolling
checkpoints and smaller resumable segments.

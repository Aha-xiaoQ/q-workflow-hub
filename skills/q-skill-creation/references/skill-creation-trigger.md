# Skill Creation Trigger Standard

Use this reference when deciding whether to proactively evaluate, propose,
create, or avoid creating a new skill.

A skill is a durable routing and execution unit. Do not create one just because
a task was useful once. The default behavior is to evaluate and briefly propose
sedimentation, not to silently create a new top-level skill. Create or propose a
skill when the work has a repeatable trigger, reusable procedure, clear output
contract, and validation path that future agents should discover without chat
history.

## Trigger Levels

### Must Evaluate Or Propose Sedimentation

Evaluate whether to update an existing durable layer or propose skill
sedimentation when any of these happen:

- the user explicitly says skill, sediment, write it down, do not repeat this,
  form a process, standardize it, make it reusable for others, or asks whether
  such a capability already exists;
- the same failure mode, correction, or workflow miss appears more than once,
  or one serious failure exposes a stable process gap that a reusable rule can
  prevent;
- a hardware, code, PPT, public handoff, or customer-facing workflow needs a
  repeatable safety or quality gate;
- a project develops a repeated setup, debug, release, or onboarding sequence
  that future sessions must recover;
- a new tool integration needs stable commands, permissions, validation
  evidence, or failure handling;
- a review gate, intake flow, or tool helper could be reused by multiple
  upstream workflows;
- a lesson improves expert review, context management, or agent coordination
  beyond one project.

### May Create Directly After Authorization

Create directly, after checking for an existing owner, only when all are true:

- the user explicitly authorized skill creation/update, asked for
  standardization/sedimentation, or the current task is explicitly a
  skill-system task;
- the trigger and output contract are obvious from existing files or repeated
  evidence;
- no existing skill, reference, workflow, script, project memory, or profile can
  own the behavior with lower maintenance cost;
- the initial lifecycle state can be recorded as `candidate` or `pilot` with
  validation evidence;
- source/runtime mirrors and validation can be handled in the same pass.

### Ask Before Creating

Ask or offer 2-3 options when any of these are unclear:

- whether the skill should be generic, company/private, project-local, personal,
  public, or external/tool-oriented;
- the name, audience, output contract, or owner skill is ambiguous;
- the new skill may overlap an active skill or change routing defaults;
- creation would require public/private boundary decisions, third-party
  material, network access, or risky tooling;
- multiple useful shapes exist, such as top-level skill vs reference inside an
  existing skill.

### Do Not Create A New Top-Level Skill

Do not create a new skill when the better durable layer is:

- **existing skill update**: same trigger family and output contract already has
  an owner;
- **reference/workflow**: the lesson is a checklist, rubric, scenario, or mode
  inside one skill;
- **script**: the value is deterministic automation without a distinct
  user-facing routing contract;
- **project memory**: the facts are about one repository, board, demo,
  customer, or local state;
- **assistant profile**: the rule is a personal collaboration preference;
- **report/TODO**: the idea is unproven, one-off, or only an investigation
  result;
- **external skill unchanged**: the skill is third-party and should not be
  modified unless the user asks.

## Decision Ladder

If unsure, do not create a top-level skill yet. Record the idea in the smallest
durable layer, run one validation scenario, and revisit after evidence
accumulates.

Use the smallest durable layer that will reliably fire in future sessions:

1. Update project memory, profile, or TODO when the lesson is local or personal.
2. Update an existing skill's reference or workflow when ownership is clear.
3. Add a validation scenario or script when the behavior needs objective
   checking.
4. Create a project-local skill when the workflow is repeated but bounded to one
   project.
5. Create a top-level reusable skill when the workflow has independent user
   intent, output contract, validation gate, and long-term owner.
6. Split a skill only when `skill-composition-boundary.md` says triggers, risks,
   outputs, or context cost diverge.

## Minimum Evidence Before Creation

Before creating a new top-level skill, record:

- 2-3 example prompts or trigger symptoms;
- target users and non-users;
- why this is not just project memory, personal preference, report evidence, or
  an update to an existing skill;
- output contract and durable files produced;
- validation evidence or first scenario to run;
- source of truth and runtime/mirror plan;
- public/company/project/personal boundary;
- why updating an existing skill or reference is insufficient.

## Active User Reminder

When a user action matches this standard, briefly say which existing skill or
proposed skill would help and why. Keep the reminder short and action-oriented.
Do not interrupt urgent debugging, hardware safety, or user-requested narrow
work with a long skill discussion.

## Anti-Patterns

- Creating a top-level skill for a single chat insight.
- Creating a new skill because a file got large before checking references or
  workflows.
- Updating only runtime skill copies while the source of truth is stale.
- Letting a repeated failure stay only in chat or a report.
- Creating a skill silently when the user only needed a small rule update or
  project note.
- Asking the user whether to create a skill when they already explicitly asked
  for sedimentation and the target owner is obvious.
- Burying reusable skill behavior in project memory where future unrelated tasks
  will not find it.

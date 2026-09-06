# Collaboration Mechanisms

This document captures public-safe collaboration mechanisms that make
agent-assisted project work easier to recover, verify, and share. It is a
mechanism guide, not a private assistant profile. Keep real users, companies,
customers, machine paths, active work, credentials, and unreleased project facts
in the user's private hub or project repository.

## Public-Safe Boundary

Promote the rule, not the private incident that created it.

Public content may include:

- generic workflow rules, templates, validation gates, and examples;
- public-safe command names and placeholder paths;
- sanitized failure modes that could happen to any user;
- links to public documentation or independently written guidance.

Public content must not include:

- personal names, emails, accounts, machine names, private paths, or private
  remotes;
- company, customer, or internal project details;
- credentials, tokens, screenshots containing secrets, or private logs;
- active work status, private TODOs, or unreleased product facts.

## Mechanisms

| Mechanism | Use It When | Public Implementation |
|:---|:---|:---|
| Numbered TODO queue | A request contains several independent items or a TODO list is long. | Show a compact numbered list, keep numbers stable within the round, and mark each item done, paused, blocked, or deferred. |
| Completion closure ledger | A task is about to be called complete. | Reconcile the active pointer, matching TODOs, work item state, validation evidence, runtime mirrors when relevant, and residual risk. Completed work must not remain the default resume target. |
| UTF-8 and mojibake guard | Editing Markdown, skills, prompts, templates, or state files with non-ASCII text. | Use explicit UTF-8 reads/writes, search for replacement characters or common mojibake before commit, and never copy garbled terminal output into durable files. |
| Progressive context loading | Resuming, auditing, or changing a project. | Start with micro or quick routing state, then expand to project/deep/full reads only when risk, ambiguity, dirty state, or public sync requires it. |
| Micro-command paths | The user gives exact shortcuts such as `TODO`, `status`, or `checkpoint`. | Define the smallest reliable file or command path. Do not turn micro commands into broad project scans unless the state is ambiguous. |
| Durable lesson capture | Feedback repeats or a mistake reveals a reusable failure mode. | Convert the lesson into a rule, template, script, validation case, or TODO. Chat history alone is not durable memory. |
| Public/private source-of-truth split | Sharing a starter while keeping personal workflow state. | Public starter holds generic skills, scripts, and templates. Private workflow hubs hold profile details, project registry, active work, and private preferences. Project repos hold project facts and deliverables. |
| Public-sync scan gate | Before copying, publishing, pushing, or promoting a public starter candidate. | Run public scans for credentials, private paths, private domains, personal identifiers, and internal project names. Treat secret scanning or push protection as an additional remote guard, not a replacement for local review. |
| Validation and residual-risk handoff | Ending a work round or handing off to another agent. | State commands run, results, what was not checked, why it was not checked, remaining risk, next owner, and whether local commits are separate from remote pushes. |
| Stable expert role vs run instance | Using specialists, reviewers, or subagents. | Document stable expert roles as reusable contracts. Record platform agent nicknames or run ids only as trace evidence for that run. |
| Naming and variant consistency | A workflow label, repository name, skill name, or internal package name changes. | Keep a clear mapping, record aliases or migrations, and avoid mixing internal variant suffixes into user-facing recovery prompts. |
| Minimal repository contract | A starter is shared with other users. | Provide a README, license, contribution or maintenance guidance, security/private-data guidance, and a clear setup or quickstart path. |
| Source/runtime/bootstrap mirrors | A workflow installs generated runtime copies. | Treat source as authoritative, runtime as a loaded copy, and bootstrap mirrors as restore material. Compare file lists or hashes when sync matters. |
| Bounded autonomy | The user asks for a long or unattended run. | Define the goal, stop conditions, validation cadence, approval boundaries, and checkpoint path before continuing autonomously. |

## Adoption Checklist

Before calling a reusable workflow change complete:

1. Put the generic rule in the right public surface: skill, template, docs, or
   validation script.
2. Keep personal or company-only examples out of the public text.
3. Check counterpart variants if the project maintains more than one starter.
4. Run the public scan and encoding guard that match the touched files.
5. Report validation evidence, residual risk, local commit state, and pending
   push or publish state.

## Source Notes

These mechanisms are independently implemented for q-workflow, but the guard
rails line up with public documentation and common tool behavior:

- GitHub repository guidance treats files such as README, license,
  contribution guidance, and security guidance as expectation-setting material
  for contributors and users.
- GitHub secret scanning and push protection are designed to prevent supported
  credential patterns from reaching repositories.
- Microsoft documents different default encodings between Windows PowerShell
  and newer PowerShell versions; explicit UTF-8 handling avoids many cross-
  shell surprises.
- Git's porcelain status format is intended for stable script consumption.

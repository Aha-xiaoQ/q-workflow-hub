# Capability-Aware Skill Review

Use for a requested model/skill audit or a demonstrated instruction conflict.
This is an on-demand review procedure, not a required preflight for every task.

## Decide from evidence

Assume the model can reason and select methods. A skill should supply domain
facts, fragile-operation constraints and useful resources, not a simulated
capability ceiling. Review actual behavior paths before editing:

- Does a rule request information already supplied or approval already granted?
- Does it turn an example, style preference or past local failure into a global
  requirement, training lock or unrelated task?
- Does it select tests by affected artifact and intended claim, with a stopping
  condition once sufficient evidence is current?
- Does it assume a model name, fixed context window, unavailable tool, operating
  system, provider or automatic fallback without inspecting the actual host?
- Does it confuse public-safe content with permission to publish a private skill?

Keep domain correctness, data boundaries, factual caveats, independent release
review, native object preservation and reliable recovery. Preserve explicit user
training holds and approval checkpoints; do not infer new ones from a checklist.

## Managed and third-party skills

Classify each root as maintained source, installed copy, personal source or
provider-managed package. Audit cache entries separately from advertised active
skills: a cached or backup copy is not proof that it can activate.

Do not patch a provider cache as a durable fix or copy its content into a public
package. Record the exact conflict and use supported package configuration,
upstream maintenance or an authorized local source adaptation. Keep licenses.
When composing skills, resolve their instructions under the current host/user
hierarchy. A more specific route can clarify a broad default; it never bypasses
a tool policy. If a genuine conflict prevents the request, explain the exact
constraint rather than silently changing the requested artifact or destination.

For example, an existing spreadsheet edit is not new-workbook creation; native
reference structure should survive a template-based document task; a connector
batch size is not a new user-authorization boundary; reader-relevant uncertainty
belongs in a distributed document. Verify the owning tool's actual behavior and
supported features before selecting a path.

## Validate the revision

Use targeted positive, negative and transfer scenarios: an authorized change,
a read-only request, a revoked external action, an ambiguous consequential choice,
an unavailable capability, and a task from another domain. Run only applicable
cases and preserve actual reviewer evidence. Distinguish static findings,
deterministic tests, agent scenario results and measured model performance.
No finite instruction audit proves that skills never affect model performance.

## References

- [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model):
  instruction sensitivity, autonomy and verification calibration.
- [OpenAI skills](https://developers.openai.com/codex/skills): concise discovery,
  progressive disclosure and host-specific skill loading.

Apply current official guidance through actual exposed host capabilities.
These mechanisms are independently expressed; no third-party prompt or code is
included. Revisit after a meaningful host/skill change or observed regression.

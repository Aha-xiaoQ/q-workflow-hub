# Variant Delta

This file records public-safe notes about intentional differences between this
public starter and private or company variants.

## Public Starter Boundary

The public starter may include reusable generic skills and setup material. It
must not include:

- active personal work state;
- project registry entries for real work;
- project-specific facts;
- customer or private materials;
- credentials or tokens;
- generated project artifacts;
- internal repository URLs, hostnames, or machine paths.

## Variant Additions

Private or company variants may add skills, templates, validation scripts, or
brand assets that are not appropriate for the public starter. Those additions
should remain in the variant repository unless the underlying lesson is
rewritten as a generic, public-safe capability.

## Retirement Notes

Legacy collection repositories should not be used as active public sync sources.
Promote stable generic content into `q-workflow-hub`, and keep private/company
state in the private workflow hub or an internal company variant.

## Machine-Readable Variant Map

`docs/governance/VARIANT_MAP.json` is a conservative default with no automatic
organization-specific mappings or waivers. Store those rules in a private
policy file and pass it with `--variant-map`. Keep audit reports private when
they contain private paths or file names. Unmapped differences require review;
an empty map must never be treated as approval to copy private content.

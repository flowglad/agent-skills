---
name: author-flowglad-skill
description: Author and revise governed Flowglad Skill packages with Agent Skills instructions, OWS-native Python functions, synthetic JSON test cases, and lifecycle metadata. Use when creating or updating a reusable Flowglad capability, preparing a candidate revision, submitting through Flowglad MCP, following verification, or resolving package and OWS-ABI diagnostics.
---

# Author Flowglad Skill

Create a durable, intentionally reusable Flowglad Skill package and follow its immutable
revision lifecycle. New code private to one Automation belongs in that Automation's
executable bundle; use `author-flowglad-ows` for that lane. Preserve existing Skill-backed
histories. Unavailable or failed private authoring does not justify a duplicate Skill.

Use this package's bundled references for instructions. Live tools resolve authorized
state, exact SDK contracts, and validation results; they do not replace these instructions.

## Authoring process

1. Gather the reusable behavior, inputs, outputs, failure conditions, and representative synthetic cases.
2. Use `skills.list` and `skills.get` when Flowglad MCP is available. Prefer a suitable active Skill over creating a duplicate.
3. For a new Skill, derive the slug from the request. For an update, resolve the exact Skill and base revision; never infer identities from names.
4. Read `references/PACKAGE_CONTRACT.md` completely.
5. Copy `assets/starter-package`, rename `SKILL.template.md` to exactly `SKILL.md`, replace every placeholder, and extend only what the capability needs.
6. For every selected Python function, read `references/OWS_COMPATIBILITY.md` and the relevant sections of the bundled `references/CODE_ABI.md` and use the OWS code ABI. Do not add a CLI wrapper around OWS code.
7. Create or revise `SKILL.md`, support files, `scripts/**.py`, and small `flowglad-ows-code-test-v1` cases under `tests/**.json`. Keep scratch work outside the package.
8. Run Python syntax checks. Before a persistent write, submit unpublished bytes and synthetic fixtures to advertised `skills.create_validation_job`, then poll `skills.get_validation_job` to a terminal state and resolve diagnostics. Read `references/MCP_LIFECYCLE.md` for fixture validation and development testing. Do not execute the selected function as a positional-argument CLI.
9. Run this skill's bundled helper as `python3 /path/to/author-flowglad-skill/scripts/build-package-payload.py PACKAGE_DIR` for inline MCP preflight. For large packages or MCP byte-transport failures, add `--transport staged` and follow `references/MCP_LIFECYCLE.md`.
10. Submit only when the user explicitly asks to create, upload, publish, or update the remote Skill.
11. Poll `skills.get_lifecycle_request`, then `skills.get` until the candidate reaches its final verification state. Repair rejected authored bytes as a new immutable candidate on the same Skill, using the newest rejected revision as base when the first submission failed. A deferred development revision stays unpublished until explicitly submitted for publication.

## Package design

- Keep metadata in `meta.json` and Markdown instructions without YAML frontmatter in `SKILL.md`.
- Prefer small deterministic functions with explicit injected inputs and JSON-compatible returns.
- Put structural constraints in the surrounding OWS schemas and semantic constraints in Python.
- The bundled payload helper skips dot-prefixed files and directories in both transports; keep required package members visible. Do not embed tokens, cookies, hidden credentials, or customer datasets. Use small synthetic test inputs.
- Default new Python packages to OWS-native verification with no CLI entrypoint declarations.
- Preserve stable CLI entrypoint identities only when explicitly maintaining a legacy CLI package; do not add them to new OWS-native packages.
- Never fabricate Flowglad IDs or conflate Skill verification with OWS publication.

## Lifecycle integrity

- `skills.create` and `skills.create_candidate` accept inline base64 for small packages.
- Use `skills.create_package_upload_session` and `skills.finalize_package_upload_session` for large packages or transport failures; upload the exact declared bytes between those calls.
- An accepted lifecycle request or `verificationDispatched: true` does not prove verification success.
- Treat `active`, `verified`, `rejected`, and stale-base outcomes distinctly. Revisions are immutable.
- OWS publication separately validates the selected source function and exact revision.

## Boundaries and handoff

Do not author the surrounding OWS workflow; use `author-flowglad-ows`. Do not weaken the verifier or mutate a remote Skill without explicit intent.

Return the complete package, any legacy entrypoint declarations, exact local checks, lifecycle/Skill/revision identities when submitted, final verification diagnostics, and OWS publication status as a separate state.

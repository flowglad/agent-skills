---
name: author-flowglad-skill
description: Author and revise reusable Flowglad Skill packages containing Agent Skills instructions, native-Python CLI entrypoints, fixtures, and tests. Use when creating a governed Python capability, preparing a new Skill or candidate revision, submitting a package through Flowglad MCP, following automatic verification, resolving verification diagnostics, or preparing code for use by a Flowglad OWS program.
---

# Author Flowglad Skill

Create a durable Flowglad Skill package and follow its governed revision lifecycle.

## Authoring process

1. Gather the reusable behavior, inputs, outputs, failure conditions, and representative fixtures.
2. Use `skills.list` and `skills.get` when Flowglad MCP is available. Prefer an existing suitable active Skill over creating a duplicate.
3. Establish explicit intent:
   - For a new Skill, derive the slug only from the user's request.
   - For an update, require the exact Skill and base revision identities. Do not infer them from names.
4. Read `references/PACKAGE_CONTRACT.md` completely before authoring package files or entrypoint declarations.
5. Copy `assets/starter-package` and `assets/starter-entrypoints.json` for a minimal new CLI package. Rename the copied `SKILL.template.md` to exactly `SKILL.md`, replace every placeholder in `meta.json` and `SKILL.md`, then extend only what the requested capability needs.
6. When the package must be callable from OWS, also read `references/OWS_COMPATIBILITY.md` before writing its selected Python source. The CLI starter is not OWS-compatible by itself.
7. Create or revise `SKILL.md`, support files, native-Python scripts, synthetic fixtures, and tests. Keep scratch work outside the package.
8. Run every declared test and the exact smoke invocation for every entrypoint. Resolve all local failures.
9. Run `python3 scripts/build-package-payload.py PACKAGE_DIR --entrypoints ENTRYPOINTS.json` to encode the package objects when local execution is available. Treat its checks as packaging preflight, not authoritative verification.
10. Submit through `skills.create` or `skills.create_candidate` only when the user explicitly asks to create, upload, publish, or update the remote Flowglad Skill.
11. Poll `skills.get_lifecycle_request` until the lifecycle worker returns the Skill and candidate revision identities. Then poll `skills.get` for the candidate revision's actual verification status and diagnostics.
12. If verification rejects authored bytes, repair the package and submit a new immutable candidate. Do not retry the same rejected bytes as a substitute for a fix.

## Package design

- Prefer small deterministic programs with explicit positional arguments and machine-readable stdout.
- Keep package metadata in `meta.json` and keep `SKILL.md` limited to Markdown instructions without YAML frontmatter.
- Consume prepared local files or explicit values. Do not embed tokens, cookies, hidden credentials, or large source datasets.
- Put structural constraints in the interface and semantic constraints in code.
- Use small synthetic fixtures that exercise the declared interface without copying customer data.
- Preserve existing stable entrypoint IDs, names, and descriptions when updating a Skill.
- Do not fabricate stable Flowglad IDs. If an update requires a new entrypoint identity and no available tool allocates one, report that publication dependency.
- Keep Skill CLI entrypoint identities separate from OWS source selection. OWS pins the exact Python module `path` in a verified revision and names the selected function independently.

## Verification and publication integrity

- Flowglad automatically verifies every package submitted through `skills.create` or `skills.create_candidate`.
- `verificationDispatched: true` proves dispatch only. It does not prove verification success.
- Read final revision state and verification diagnostics through `skills.get`.
- Treat `active`, `verified`, `rejected`, and stale-base outcomes distinctly.
- Treat every revision as immutable. A repair is a new candidate revision.
- Do not claim OWS compatibility from Skill verification alone. OWS publication separately validates the selected source against the OWS code ABI.

## Boundaries

- Do not author the surrounding OWS workflow, schedule, connection graph, or artifact dataflow. Use `author-flowglad-ows` for orchestration.
- Do not reimplement or weaken the authoritative Flowglad verifier.
- Do not upload or mutate a remote Skill without explicit user intent.
- Do not claim activation, OWS publication, or execution from successful package authoring.

## Handoff

Return:

- The complete package and entrypoint declarations.
- The exact local tests and smoke invocations performed.
- The MCP lifecycle request, Skill, candidate revision, and entrypoint identities when submitted.
- Final verification state and diagnostics, or the exact unresolved publication dependency.
- OWS compatibility status separately from Skill verification status.

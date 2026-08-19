---
name: author-flowglad-ows
description: Author and revise Flowglad automation programs using the Flowglad profile of Open Workflow Specification 1.0.3. Use when creating an OWS YAML workflow, composing connections, browser tasks, artifacts, and verified Flowglad Skill revisions, translating an automation idea into OWS, diagnosing compiler errors, preparing a workflow for validation or publication, or modifying an existing Flowglad OWS program.
---

# Author Flowglad OWS

Create the canonical OWS source for a Flowglad automation.

## Authoring process

1. Gather the intended workflow inputs, outputs, tasks, dataflow, artifacts, external systems, reusable capabilities, and side effects.
2. Read `references/AUTHORING.md` completely before writing or revising a program. Treat it as the authoritative Flowglad profile reference.
3. For every code capability, read `references/SKILL_RESOURCES.md` and resolve an exact OWS-compatible verified Skill revision when possible.
4. If a required reusable capability is missing and `author-flowglad-skill` is available, use it to author and verify a package whose selected source also satisfies the OWS code ABI. Resume OWS authoring only after resolving the exact revision, module path, and selected function name.
5. Use a `space-file` code resource only when the user requests direct Space code, the Skill lifecycle is unavailable, or the code is intentionally automation-specific. Read `references/CODE_ABI.md` completely before writing or revising direct Python source.
6. Inspect the closest complete example when the workflow needs one:
   - Read `references/skill-backed-code.ows.yaml` for the preferred verified Skill-revision resource shape.
   - Read `references/invoice-reconciliation.ows.yaml` for authenticated connection actions, task-input injection, evidence artifacts, and a multi-command terminal DAG using direct Space code.
   - Read `references/yooz-bounded-document-number.ows.yaml` for direct code, inference, artifacts, and a terminal command-DAG proposal.
   - Read `references/mock-bank-browser-statement.ows.yaml` for a browser-agent call, a PDF artifact, and a direct code consumer.
   - Read `references/page-todo-update.ows.yaml` for exact Page reads and Page edit command DAGs.
7. Copy `assets/starter.ows.yaml` when starting a simple Skill-backed workflow, then replace every placeholder with an exact value.
8. Write the canonical workflow as YAML with the `.ows.yaml` extension. Create companion Python only for a selected `space-file` resource.
9. Validate with the Flowglad compiler or an advertised Flowglad MCP validation tool when either is available. Resolve every diagnostic before claiming compiler validity.
10. Publish or modify a remote Automation only when the user asks. Treat an update as publication of a new immutable revision, never as an in-place rewrite.
11. Report Skill verification, OWS compiler validation, resource validation, publication, activation, and execution as separate states.

## Resource integrity

- Never invent Flowglad IDs, source identities, Skill revision identities, connection authorities, or Website Access connections.
- Resolve exact values from user-provided context or available Flowglad tools.
- Prefer active or verified immutable Skill revisions over mutable Space files for reusable code.
- Do not infer OWS compatibility from Skill verification alone. OWS publication separately validates the selected function declaration and derives the immutable Skill manifest and file digests.
- Leave an obvious placeholder when an exact value is unavailable and list it in the handoff.
- Treat `space-file` code as live source: each run resolves and snapshots its current bytes once for that run.
- Do not claim publication readiness until every organization-scoped resource is accessible and every selected Skill revision and function validates.

## Profile guardrails

- Author OWS 1.0.3 with Flowglad automation profile v1 and the versioned Flowglad catalog.
- Keep portable behavior in standard OWS fields. Put only Flowglad runtime and security declarations under `with.fg`.
- Use inline JSON Schemas and a sequential top-level `do` list.
- Give every task an explicit timeout.
- Use only the catalog calls and task shapes allowed by `references/AUTHORING.md`.
- Use Python 3.11 for code calls.
- Keep orchestration in OWS and reusable computation in governed Skills when the code can satisfy both the Skill CLI and OWS code-entrypoint contracts.
- Do not generate legacy v0 definitions, `StepSpec[]`, or runner-specific intermediate representations.
- Do not emulate unsupported loops, retries, waits, forks, schedules, composite tasks, third-party catalogs, or generic `run` tasks.
- Do not claim that successful compilation authorizes activation or execution.

## Handoff

Return:

- The complete `.ows.yaml` document.
- Every required companion Python file only for selected `space-file` resources.
- Every pinned Skill ID, revision ID, module path, and selected OWS function.
- All unresolved identifiers, resources, and publication dependencies.
- The exact validation performed and diagnostics remaining.
- Skill verification, OWS publication, activation, and execution status without conflating them.

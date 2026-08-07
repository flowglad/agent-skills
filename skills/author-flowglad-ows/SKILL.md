---
name: author-flowglad-ows
description: Author and revise Flowglad automation programs using the Flowglad profile of Open Workflow Specification 1.0.3. Use when creating an OWS YAML workflow, translating an automation idea into Flowglad OWS, diagnosing compiler errors, preparing a workflow for validation or publication, or modifying an existing Flowglad OWS program.
---

# Author Flowglad OWS

Create the canonical OWS source for a Flowglad automation.

## Authoring process

1. Gather the intended workflow inputs, outputs, tasks, dataflow, artifacts, external systems, and side effects.
2. Read `references/AUTHORING.md` completely before writing or revising a program. Treat it as the authoritative Flowglad profile reference. When the program uses a code call, also read `references/CODE_ABI.md` completely before writing or revising its Python resource.
3. Inspect the closest complete example when the workflow needs one:
   - Read `references/invoice-reconciliation.ows.yaml` for authenticated connection actions, task-input injection, evidence artifacts, and a multi-command terminal DAG.
   - Read `references/yooz-bounded-document-number.ows.yaml` for code, inference, artifacts, and a terminal command-DAG proposal.
   - Read `references/mock-bank-browser-statement.ows.yaml` for a browser-agent call, a PDF artifact, and a code consumer.
4. Copy `assets/starter.ows.yaml` when starting a simple code workflow, then replace every placeholder with an exact value.
5. Write the canonical workflow as YAML with the `.ows.yaml` extension. Create referenced Python files separately.
6. Validate with the Flowglad compiler or an advertised Flowglad MCP validation tool when either is available. Resolve every diagnostic before claiming compiler validity.
7. Publish or modify a remote Automation only when the user asks. Treat an update as publication of a new immutable revision, never as an in-place rewrite.
8. Report authoring, compiler validation, resource validation, publication, activation, and execution as separate states.

## Resource integrity

- Never invent Flowglad IDs, source IDs, file digests, Skill revision identities, connection authorities, or browser-auth data sources.
- Resolve exact values from user-provided context or available Flowglad tools.
- Leave an obvious placeholder when an exact value is unavailable and list it in the handoff.
- Recompute every SHA-256 digest after changing referenced bytes.
- Do not claim publication readiness until every organization-scoped resource is accessible and digest-matched.

## Profile guardrails

- Author OWS 1.0.3 with Flowglad automation profile v1 and the versioned Flowglad catalog.
- Keep portable behavior in standard OWS fields. Put only Flowglad runtime and security declarations under `with.fg`.
- Use inline JSON Schemas and a sequential top-level `do` list.
- Give every task an explicit timeout.
- Use only the catalog calls and task shapes allowed by `references/AUTHORING.md`.
- Use Python 3.11 for code calls.
- Do not generate legacy v0 definitions, `StepSpec[]`, or runner-specific intermediate representations.
- Do not emulate unsupported loops, retries, waits, forks, schedules, composite tasks, third-party catalogs, or generic `run` tasks.
- Do not claim that successful compilation authorizes activation or execution.

## Handoff

Return:

- The complete `.ows.yaml` document.
- Every required companion Python file.
- All unresolved identifiers, digests, and publication dependencies.
- The exact validation performed and diagnostics remaining.
- Publication, activation, and execution status without conflating them.

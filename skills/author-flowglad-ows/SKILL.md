---
name: author-flowglad-ows
description: Author and revise Flowglad automation programs using the Flowglad profile of Open Workflow Specification 1.0.3. Use when creating OWS YAML, composing connections, browser tasks, artifacts, pinned MCP operations, and verified Flowglad Skill revisions, diagnosing compiler errors, or preparing an Automation for validation, publication, or activation.
---

# Author Flowglad OWS

Create the canonical OWS source for a Flowglad automation.

## Authoring process

1. Gather the workflow inputs, outputs, tasks, dataflow, artifacts, external systems, reusable capabilities, and side effects.
2. Call the connected Flowglad MCP tool `automations.get_authoring_spec` with `{}`. Record its `specVersion`, `specDigest`, `compilerVersion`, and section index. Treat this deployed specification as authoritative. If the tool is unavailable, stop and report that the current authoring specification could not be loaded; do not substitute remembered or bundled profile documentation.
3. Fetch `getting-started`, `required-envelope`, `task-shape`, `dataflow`, and `validation-diagnostics` by calling the same tool with `{ "section": "<id>" }`. Use the index's `summary` and `appliesWhen` fields to fetch every additional section relevant to the workflow. Fetch `artifacts` whenever an input or output originates as a file or is a large value. Require every section response to match the index's `specDigest` before authoring.
4. For reusable code, read `references/SKILL_RESOURCES.md` and resolve an exact verified Skill `revisionId`, Python module `path`, and selected function. If the capability is missing and `author-flowglad-skill` is available, create and verify it before resuming. Use a `space-file` only for intentionally automation-specific code or when the user requests it.
5. Read `references/CODE_ABI.md` before writing Python selected by a code task.
6. Inspect the closest complete example as supporting material after loading the relevant live sections:
   - `references/skill-backed-code.ows.yaml`: verified Skill revision.
   - `references/invoice-reconciliation.ows.yaml`: authenticated reads, artifacts, and a terminal DAG.
   - `references/yooz-bounded-document-number.ows.yaml`: code, inference, artifacts, and terminal output.
   - `references/mock-bank-browser-statement.ows.yaml`: browser agent, PDF artifact, and code consumer.
   - `references/page-todo-update.ows.yaml`: exact Page reads and Page edit proposals.
   - `references/mcp-ows-v1.ows.yaml`: pinned MCP reads and command proposals.
7. Copy `assets/starter.ows.yaml` for a simple Skill-backed workflow and replace every placeholder.
8. Write YAML with the `.ows.yaml` extension. Create companion Python only for a selected `space-file` resource.
9. Validate with the Flowglad compiler or an advertised Flowglad MCP validation tool. Resolve every diagnostic before claiming compiler validity.
10. Publish or modify a remote Automation only when the user asks. An update publishes a new immutable revision; it never rewrites an existing revision.
11. Report the live specification identity, compiler validation, resource resolution, publication, activation, and execution as separate states.

## Integrity guardrails

- Never invent Flowglad IDs, connection authorities, catalog pins, file paths, or browser-auth connections.
- A Skill resource contains `revisionId` and `path`; Flowglad derives the parent Skill. A Space resource contains `path`; Flowglad resolves it in the Automation's Space.
- Do not author `runtime` for code tasks. Flowglad seals Python 3.11 and the memory limit.
- Do not author inference provider, model, reasoning effort, or output limits. Flowglad seals them from organization policy.
- Browser profiles contain authored `instructions`, not prompt, vendor-skill, tool-set, or model-route identities.
- Resolve every pinned MCP catalog revision, schema hash, operation hash, and input schema from advertised capabilities. Never guess them.
- Do not infer OWS compatibility from Skill verification alone. Publication validates the selected function from the exact revision.
- Compiler acceptance of a placeholder revision proves document shape only; it does not prove that the Skill resource exists or is publishable.
- Leave an obvious placeholder when an exact value is unavailable and list it in the handoff.

## Profile guardrails

- Author OWS 1.0.3 with Flowglad automation profile v1 and the versioned Flowglad catalog.
- Keep portable behavior in standard OWS fields and Flowglad-specific declarations under `with.fg`.
- Use inline JSON Schemas, a sequential top-level `do` list, and an explicit timeout on every task.
- Use only task shapes documented in the fetched live authoring-spec sections.
- Keep orchestration in OWS and reusable computation in governed Skills.
- Do not generate legacy v0 definitions, `StepSpec[]`, runner-specific representations, or unsupported loops, retries, waits, forks, schedules, composite tasks, third-party catalogs, or generic `run` tasks.
- Successful compilation does not authorize publication, activation, or execution.

## Handoff

Return the complete `.ows.yaml`, any companion `space-file` Python, every pinned revision/path/function or MCP capability identity, unresolved publication dependencies, exact validation and remaining diagnostics, and the distinct Skill-verification, Automation-publication, activation, and execution states.

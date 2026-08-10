# Authoring Flowglad OWS programs

> Generated public reference for `@fg/workflow-compiler` 0.1.0 and
> Flowglad automation profile v1. Update the compiler-owned authoring reference;
> do not edit this generated file directly.

## Contents

- [Start with this document](#start-with-this-document)
- [What is standard OWS and what is Flowglad-specific?](#what-is-standard-ows-and-what-is-flowglad-specific)
- [Required envelope](#required-envelope)
- [Supported task shape](#supported-task-shape)
- [Dataflow and conditions](#dataflow-and-conditions)
- [Code calls](#code-calls)
- [Inference calls](#inference-calls)
- [Browser-agent calls](#browser-agent-calls)
- [Artifacts](#artifacts)
- [Authenticated connection actions](#authenticated-connection-actions)
- [Flowglad Page access](#flowglad-page-access)
- [Terminal command DAGs](#terminal-command-dags)
- [Capabilities are derived](#capabilities-are-derived)
- [Source identity, publication, and compatibility](#source-identity-publication-and-compatibility)
- [Validation and diagnostics](#validation-and-diagnostics)
- [Complete examples](#complete-examples)

This is the author reference for the Flowglad dialect of Open Workflow
Specification (OWS). A Flowglad automation program is an OWS 1.0.3 workflow
that opts into Flowglad profile v1 and calls the versioned Flowglad task
catalog.

Use this guide to write the canonical workflow document. The executable source
of truth is the document itself, not a runner-specific intermediate
representation.

> **Execution status:** Flowglad validates and publishes these documents as
> immutable revisions for the standalone OWS executor. Activation verifies the
> exact bundle, closure, digests, and runtime identity. Routing is behind
> the default-off, organization-allowlisted `schematized-automation-runtime`
> feature flag, so compiler validity alone does not authorize execution.

The normative upstream language is
[OWS 1.0.3](https://open-workflow-specification.org/). This guide documents the
additional restrictions and `fg` fields enforced by `@fg/workflow-compiler`.

## Start with this document

The smallest useful code workflow looks like this:

```yaml
document:
  dsl: '1.0.3'
  namespace: my-company
  name: normalize-invoice
  version: '1.0.0'
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1
      requiredExtensions:
        - https://flowglad.com/ows/extensions/capabilities/v1
        - https://flowglad.com/ows/extensions/runtime-profile/v1

use:
  catalogs:
    flowglad:
      endpoint:
        uri: https://flowglad.com/ows/catalogs/automation/v1

input:
  schema:
    format: jsonschema:2020-12
    document:
      type: object
      additionalProperties: false
      required: [invoice_id]
      properties:
        invoice_id: {type: string}

do:
  - normalize:
      input:
        from: '${ . }'
      call: code:1.0.0@flowglad
      with:
        fg:
          resource:
            kind: space-file
            spaceId: spc_replace_me
            path: automations/normalize.py
            digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
          entrypoint: normalize
          runtime:
            language: python
            version: '3.11'
            memoryMb: 128
      timeout:
        after: PT30S
      output:
        schema:
          format: jsonschema:2020-12
          document:
            type: object
            additionalProperties: false
            required: [normalized]
            properties:
              normalized: {type: boolean}

output:
  as: '${ . }'
  schema:
    format: jsonschema:2020-12
    document:
      type: object
      additionalProperties: false
      required: [normalized]
      properties:
        normalized: {type: boolean}
```

Replace the resource identity and digest with an actual resource visible to the
automation's organization. The compiler accepts the shape; publication also
resolves the resource and verifies its digest.

## What is standard OWS and what is Flowglad-specific?

Keep portable workflow behavior in standard OWS fields. Use `with.fg` only for
behavior that OWS does not define.

| Concern | Author it in |
| --- | --- |
| Workflow and task input/output schemas | Standard OWS `input` and `output` |
| Value selection and transformation | Standard OWS runtime expressions |
| Ordered task dataflow | Standard OWS `do`, `input.from`, and `export.as` |
| Conditional execution | Standard OWS task `if` |
| Task timeout | Standard OWS task `timeout` |
| Python or Skill resource identity | `with.fg.resource` on a Flowglad code call |
| Python function selection | `with.fg.entrypoint` on a Flowglad code call |
| Model or browser runtime profile | `with.fg.profile` |
| File/JSON artifact identity and integrity | `with.fg.produces` and `with.fg.consumes` |
| Authenticated connection actions | `with.fg.exactAuthentication` on a code call |
| Exact Flowglad Page reads | `with.fg.pageAccess` on a code call |
| Approval-bound terminal command proposal | `with.fg.terminal` on the final code call |
| Security capabilities | Do not author them; the compiler derives them |

Do not put business inputs under `with`. For every supported catalog call,
`with` must contain exactly one key named `fg`. Task values continue to flow
through standard OWS fields.

## Required envelope

Every program must:

1. Set `document.dsl` to exactly `'1.0.3'`.
2. Set `document.metadata.fg.profile` to
   `https://flowglad.com/ows/profiles/automation/v1`.
3. Define the `flowglad` catalog at
   `https://flowglad.com/ows/catalogs/automation/v1`.
4. Use inline schemas. A `schema.resource` reference is rejected anywhere in
   profile v1 because publication cannot seal an unpinned schema fetch.
5. Put top-level tasks in a sequential OWS `do` list.

`document.metadata.fg.requiredExtensions` is optional. When present, it is a
fail-closed compatibility assertion: every URI must be one of these profile-v1
URIs:

- `https://flowglad.com/ows/extensions/capabilities/v1`
- `https://flowglad.com/ows/extensions/exact-authentication/v1`
- `https://flowglad.com/ows/extensions/page-access/v1`
- `https://flowglad.com/ows/extensions/runtime-profile/v1`
- `https://flowglad.com/ows/extensions/artifacts/v1`
- `https://flowglad.com/ows/extensions/terminal-command-dag/v1`

List the extensions on which the program relies. An unknown required URI is a
compile error rather than an instruction to ignore unfamiliar behavior.

## Supported task shape

Each item in the top-level `do` array must contain exactly one named task:

```yaml
do:
  - task-name:
      call: code:1.0.0@flowglad
      with:
        fg: {}
      timeout:
        after: PT30S
```

Task names must match `[a-z][a-z0-9_-]{0,63}`. A task may use only these
standard fields:

- `call`
- `with`
- `if`
- `input`
- `output`
- `export`
- `timeout`
- `metadata`

Every task must declare a standard OWS timeout. `metadata` is descriptive and
never creates a capability grant.

Profile v1 rejects explicit `then` transitions, reusable functions, OWS task
extensions, third-party catalogs, schedules, composite tasks, forks, loops,
switches, retries, waits, event tasks, and generic `run` tasks. This is a
profile restriction, not a claim that OWS lacks those features. Profile v1 does
not accept them, and authors must not emulate them with an unrecognized `fg`
key.

## Dataflow and conditions

Use OWS runtime expressions directly. The compiler preserves them in the
resolved OWS model instead of translating them into a Flowglad expression
language.

```yaml
do:
  - first:
      input:
        from: '${ . }'
      # call, with, timeout, and output omitted here
      export:
        as: '${ $context + { first_result: . } }'

  - second:
      if: '${ $context.first_result.ready }'
      input:
        from: '${ $context.first_result }'
      # call, with, timeout, and output omitted here

output:
  as: '${ . }'
```

The standalone executor owns conformance to OWS expression and condition
semantics. The compiler proves that the document and supported profile are
valid; it does not execute expressions.

Canonical OWS tasks return their declared value directly. Do not wrap task
results in an application-specific control envelope. Use OWS failure, `if`, and
dataflow semantics. Any additional outcome convention requires a new profile
version.

## Code calls

Call `code:1.0.0@flowglad` for a pinned Python program.

The workflow document defines the direct OWS task value and schemas. The
executor's `flowglad.entrypoints` module is a Flowglad adapter convention, not
a second workflow language or result envelope. Code authors use the
[standalone executor code ABI](./CODE_ABI.md) for function
returns, runtime values, artifact slots, logging, and connection actions.

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: space-file
      spaceId: spc_123
      path: automations/reconcile.py
      digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    entrypoint: reconcile
    runtime:
      language: python
      version: '3.11'
      memoryMb: 256
    consumes: []
    produces: []
```

The resource is one of:

```yaml
# A Python file in a Space
kind: space-file
spaceId: spc_123
path: automations/reconcile.py
digest: sha256:...
```

```yaml
# An exact Python module in a verified Skill revision
kind: skill-revision
skillId: skl_123
revisionId: skr_123
path: scripts/reconcile.py
digest: sha256:...
```

Space-file paths are normalized relative POSIX paths, must end in `.py`, and
must not contain empty, `.`, or `..` segments. Publication reads the current
bytes, verifies the authored SHA-256 digest, and writes the bytes to the
content-addressed execution-resource store. For a Skill, the digest identifies
the verified revision manifest, while `path` selects the Python module inside
that sealed bundle and must name a `.py` file under `scripts/`. The code task's
`entrypoint` selects the public top-level function inside the module; Skill CLI
entrypoint IDs do not participate in OWS execution.

The only profile-v1 runtime is Python 3.11. `memoryMb` is an integer from 64
through 4096.

Each code task declares one public top-level Python function through
`entrypoint`. A plain selected function must be synchronous and declare zero
parameters. A function that needs injected task input or artifacts uses
`@entrypoint` from `flowglad.entrypoints`; the decorator binds its annotated
parameters and exposes a zero-argument wrapper to the OWS runtime. Publication
statically reads the OWS-selected declaration from the exact pinned bytes and,
for decorated functions, checks artifact parameters against `consumes` and
`produces`. The executor imports the sealed resource, requires the selected
runtime callable to have zero arguments, and serializes its JSON-compatible
return through the bounded stdout process channel. Author code sends
diagnostics only to stderr; there is no result envelope or result file.

```python
def reconcile() -> dict[str, bool]:
    return {"normalized": True}
```

For dependency injection, decorate an N-arity source function:

```python
from flowglad.entrypoints import ArtifactInput, Input, entrypoint


@entrypoint
def reconcile(invoice_id: Input, invoice_pdf: ArtifactInput) -> dict[str, object]:
    return {"invoice_id": invoice_id, "invoice_size": invoice_pdf.size_bytes}
```

`Input` binds the task-input object field with the same name. `TaskInput` binds
the complete task input. `ArtifactInput` and `ArtifactOutput` bind the matching
task-local aliases. Artifact parameters match the workflow declaration
exactly for decorated functions; the decorator does not add a capability. A
plain zero-argument function can instead use the task-scoped
`flowglad.runtime`, `flowglad.artifacts`, and `flowglad.connections` modules.
The
[code ABI](./CODE_ABI.md) defines the declaration grammar
and runtime failures.

### Code validation responsibilities

Authors put every structural constraint that JSON Schema can express in the
task input/output schemas, connection action parameter/result schemas, and
artifact declarations. The executor enforces those declarations at runtime, so
Python consumes admitted values directly instead of repeating defensive shape
checks.

| Executor owns | Python resource owns |
| --- | --- |
| Constructs the task-scoped modules and injects declared dependencies from sealed, admitted runtime state. | Declares only the dependencies the selected function uses and implements the task behavior. |
| Validates the task input before process launch and the function return against the task's OWS schemas. | Implements the transformation and checks semantic or cross-field invariants that the schemas do not express. |
| Admits consumed artifacts and enforces path containment, media type, size, and digest; verifies every produced slot after exit. | Uses the declared artifact objects and checks domain meaning inside file content when the workflow requires it. |
| Binds each `flowglad.connections` alias to sealed actions and each `flowglad.pages` alias to one visible Page; validates host results and enforces call budgets. | Chooses which declared reads to perform and checks business meaning, consistency, and completeness. |
| Invokes the declared function, serializes one bounded strict JSON value, requires exit status zero, supervises timeout/cancellation, and validates a declared terminal command DAG. | Returns one JSON-compatible task value, sends diagnostics to stderr, and raises when a business constraint fails. |

Python does not read or revalidate the internal manifest, connection alias
binding, artifact integrity metadata, or shapes already represented by a
declared schema. When a load-bearing invariant fits JSON Schema, the author
declares it there. When it does not, the resource checks it explicitly and
fails with a safe diagnostic.

## Inference calls

Call `inference:1.0.0@flowglad` for one schema-constrained model invocation.

```yaml
call: inference:1.0.0@flowglad
with:
  fg:
    profile:
      id: extract_document_number
      provider: openai
      model: gpt-pinned
      systemPrompt: Return the document number.
      instructions: Use only the supplied task input.
      maxOutputTokens: 1024
      maxResultBytes: 4096
    consumes: []
    produces: []
```

`provider` is `openai` or `anthropic`. The model, prompts, and bounds are part of
the immutable profile digest. Put the result shape in the task's standard OWS
`output.schema`; do not duplicate it under `with.fg`.

## Browser-agent calls

Call `browser-agent:1.0.0@flowglad` for a bounded browser-agent session.

```yaml
call: browser-agent:1.0.0@flowglad
with:
  fg:
    profile:
      id: download_statement
      targetOrigin: https://bank.example.com
      browserAuthDataSourceId: dsrc_123
      promptIdentity: bank/login@v1
      vendorSkillIdentity: bank/download_statement@v1
      toolSetIdentity: web-agent-tools-v1
      modelRoute: web-agent
      maxSteps: 20
    consumes: []
    produces: []
```

`targetOrigin` must be a canonical HTTPS origin with no path, query, fragment,
or trailing slash. The authentication data source, origin, prompt, vendor skill,
tool set, model route, and step bound are sealed into the task profile. `maxSteps`
is an integer from 1 through 100.

## Artifacts

Standard OWS fields carry JSON task values. Flowglad artifacts are the separate
file/large-value data plane. Declare an artifact once on its producer and bind
it by name on downstream consumers.

```yaml
# Producer
produces:
  - name: statement-pdf
    mediaType: application/pdf
    maxBytes: 10000000

# A downstream consumer
consumes:
  - statement-pdf
```

The fields have distinct purposes:

| Field | Meaning |
| --- | --- |
| `name` | Workflow-wide artifact identity. A consumer's `name` must match exactly one upstream producer. |
| `as` | Optional task-local Python name. It defaults to `name` with hyphens replaced by underscores. |
| `fileName` | Optional browser-download basename. The compiler otherwise derives a filename from `name` and `mediaType`. |
| `mediaType` | Required producer media type; an optional consumer assertion that must match. |
| `maxBytes` | Optional positive producer-side bound, at most 100 MiB. It defaults to 10 MiB. |
| `digest` | Optional SHA-256 assertion. A consumer assertion must match the producer declaration. |

The compiler generates the physical path. `fileName` identifies a provider
download when a browser task needs one; it does not grant access to an authored
filesystem location. A consumer uses the string shorthand above when the
default alias is sufficient. The object form supplies an explicit alias or an
additional media-type or digest assertion:

```yaml
consumes:
  - name: statement-pdf
    as: bank_statement
```

Python declares the aliases on the selected entrypoint:

```python
from flowglad.entrypoints import ArtifactInput, ArtifactOutput, entrypoint


@entrypoint
def normalize(
    bank_statement: ArtifactInput,
    normalized_context: ArtifactOutput,
) -> dict[str, int]:
    statement_bytes = bank_statement.read_bytes()
    normalized_context.write_json({"statement_size": len(statement_bytes)})
    return {"statement_size": len(statement_bytes)}
```

Consumed artifacts expose `path`, `media_type`, `size_bytes`, `digest`,
`open()`, `read_bytes()`, `read_text()`, and `read_json()`. Produced artifacts
expose `path`, `media_type`, `max_bytes`, `expected_digest`, `open()`,
`write_bytes()`, `write_text()`, and `write_json()`. JSON helpers require
`application/json`; text helpers use UTF-8. Input objects do not expose write
methods, and output objects do not expose read methods.

Within each task, consumed names, produced names, and all aliases are unique. An
artifact must be produced before it is consumed, and two tasks cannot produce
the same workflow artifact name. Omit `digest` for dynamic output with
execution-time bytes; the executor computes and records the actual digest.

## Authenticated connection actions

Only a code call may declare exact authenticated access. Each connection binds
an immutable connection ID to a task-local Python alias and a bounded set of
named provider actions. The declaration is not a general-purpose authenticated
fetch capability.

```yaml
exactAuthentication:
  connections:
    - connectionId: dsrc_123
      as: invoices
      connector: yooz
      actions:
        - name: get
          method: GET
          pathTemplate: /invoices/{{invoice_id}}
          bodyTemplate: null
          parameterSchema:
            type: object
            additionalProperties: false
            required: [invoice_id]
            properties:
              invoice_id: {type: string}
          resultSchema:
            type: object
            additionalProperties: true
  limits:
    maxCalls: 4
    maxResponseBytes: 2097152
    maxCumulativeResponseBytes: 4194304
    maxWallTimeMs: 30000
```

Rules enforced at compilation include:

- Connection IDs and aliases are unique within the task. Aliases and action
  names are lowercase Python identifiers and are not Python keywords.
- Action names are unique within their connection.
- `pathTemplate` is provider-relative and starts with `/`; absolute URLs are not
  accepted.
- A `{{parameter_name}}` path placeholder must be declared in
  `parameterSchema.properties`.
- A `GET` action has `bodyTemplate: null`.
- There are at most 128 connections, 128 total actions, and 128 calls.
  Per-response bytes are at most 2 MiB, cumulative bytes at most 16 MiB, and
  wall time is at most 120 seconds. The cumulative response bound is not lower
  than the per-response bound.

The compiler derives one `authenticated-read.exact` grant per connection action.
Python receives task-local aliases and methods, not credentials. The
executor/host interprets the sealed connection and action declaration and
performs the provider call; an undeclared pair fails closed.

```python
from flowglad.connections import invoices

invoice = invoices.get({"invoice_id": "inv_123"})
```

The module exists only for a code task with `exactAuthentication`. Import
connection aliases only from `flowglad.connections`; the runtime exposes no
top-level `connections` compatibility alias.

## Flowglad Page access

Only a code call may declare exact Page access. Each declaration binds an
immutable Page ID to a task-local Python alias. The runtime resolves the Page
through the automation Space's Page visibility scope, including transitively
linked Spaces, and fails closed if that access has been revoked.

```yaml
pageAccess:
  pages:
    - pageId: page_123
      as: todo
  limits:
    maxCalls: 2
    maxResponseBytes: 2097152
    maxCumulativeResponseBytes: 4194304
    maxWallTimeMs: 30000
```

Page IDs and aliases are unique within the task. Aliases are lowercase Python
identifiers and are not Python keywords. A task may declare at most 128 Pages
and 128 calls. The connection-read byte and wall-time maxima also apply.

The compiler derives one `page.read.exact` grant per Page. Python imports only
the declared aliases and calls `get_content()`:

```python
from flowglad.pages import todo

snapshot = todo.get_content()
markdown = snapshot["pageContent"]["contents"]
observation_id = snapshot["observationId"]
```

The result mirrors the exact `get_page_content` surface: `pageContent` includes
the current `contentsVersion`, bounded Markdown, and explicit truncation
metadata; `found` is true; and `observationId` identifies the full-content
version/hash observation. Use that observation ID as `baseObservationId` when
constructing an `edit-flowglad-page` command. Durable OWS evidence retains the
observation identity so approval preview and execution can verify it.

`flowglad.pages` exists only when `pageAccess` is declared. The runtime exposes
no top-level `pages` compatibility alias.

## Terminal command DAGs

The only profile-v1 terminal effect is an approval-bound command DAG proposal.
Declare it on a code call:

```yaml
with:
  fg:
    # resource and runtime omitted
    terminal:
      kind: command-dag
```

Python constructs the terminal value with the task-scoped helper module:

```python
from flowglad.commands import command, command_dag

proposal = command_dag(
    command("create-yooz-attachment", documentNumber="DOC-123"),
    title="Attach Yooz document",
    reasoning_summary="Attach the bounded Yooz document.",
)
```

The helper assigns each node's JSON filename and zero-based position, supplies
an empty edge list, and returns an ordinary JSON mapping. The executor owns the
workflow-run association, so scripts do not provide producer identity.
`ordering_edge` and
`data_edge` accept command declarations directly for multi-node DAGs, so source
code does not repeat filenames. The
[executor code ABI](./CODE_ABI.md) defines the complete
constructor signatures and validation boundary.

At most one task may declare `terminal`, and that task must be the final task in
the top-level `do` list. The task proposes a DAG; it does not execute commands
or bypass approval. Put the terminal value's schema in the standard task and
workflow `output.schema` fields.

## Capabilities are derived

Authors do not write requested-capability or capability-ceiling arrays. The
compiler derives the minimum Flowglad sidecar grants mechanically:

- code call → `code.execute`
- inference call → `model.invoke`
- browser call → one origin/data-source-bound `browser.session`
- consumed artifact → `artifact.read`
- produced artifact → `artifact.write`
- authenticated connection action → `authenticated-read.exact`
- declared Page → `page.read.exact`
- terminal declaration → `terminal-command-dag.construct`

Changing a catalog call or `fg` declaration changes the derived grants and the
sealed plan digest. Arbitrary task metadata never creates a grant.

## Source identity, publication, and compatibility

Flowglad stores the parsed JSON/YAML value as the canonical immutable source.
YAML comments, key order, scalar spelling, and whitespace are not retained. The
source digest uses RFC 8785 canonical JSON, so semantically identical mappings
have the same identity.

Successful compilation seals:

- the exact structured source and source digest;
- the official-SDK-normalized OWS model and its digest;
- task sidecars containing only Flowglad runtime/security semantics;
- the pinned catalog, task-profile, and code-resource closure;
- OWS, profile, compiler, and intended-executor versions; and
- the complete plan and closure digests.

Publication snapshots accessible Space-file bytes into the content-addressed
execution-resource store and verifies the authored digest. It requires an exact,
verified Skill revision and rejects missing, inaccessible, or digest-mismatched
resources. An identical plan is idempotent. Publication does not implicitly
activate a revision; activation fails closed unless the matching executor
version is available and the persisted bundle, closure, and digests match
exactly. Runtime routing is a separate, default-off feature-gated decision.

A different OWS revision, profile URI, catalog function version, extension
version, or compiler version is incompatible by default. Flowglad does not
silently translate or reinterpret it; author and publish a document accepted by
the available compiler.

## Validation and diagnostics

Within this repository, use the compiler directly:

```ts
import { compileFlowgladOwsWorkflow } from '@fg/workflow-compiler'

const source: unknown = Bun.YAML.parse(await Bun.file('automation.ows.yaml').text())
const result = compileFlowgladOwsWorkflow(source)

if (!result.ok) {
  for (const diagnostic of result.diagnostics) {
    console.error(`${diagnostic.path}: [${diagnostic.code}] ${diagnostic.message}`)
  }
  process.exitCode = 1
}
```

Diagnostics use JSON Pointer-like paths into the submitted document. Validation
has three distinct levels:

1. The official OWS SDK checks OWS schema and DSL validity.
2. The Flowglad compiler checks profile support, security declarations,
   artifacts, and terminal topology.
3. Publication resolves organization-scoped code resources, verifies exact
   bytes/manifests, and statically checks selected Python entrypoint
   declarations before storing the immutable revision.

None of these executes the workflow. Runtime conformance belongs to the
standalone executor, host, and gated application-boundary test suites.

## Complete examples

- [Invoice reconciliation: exact ledger read → evidence artifacts → command DAG](./invoice-reconciliation.ows.yaml)
- [Yooz: code → inference → code](./yooz-bounded-document-number.ows.yaml)
- [Mock Bank: browser agent → PDF artifact → code](./mock-bank-browser-statement.ows.yaml)
- [TODO Page: exact Page read → edit command DAG](./page-todo-update.ows.yaml)

The examples are validated with the official OWS 1.0.3 schema and the Flowglad
compiler and generate the standalone executor's committed canonical bundles.
The invoice-reconciliation example exercises task injection, scoped connection
actions, artifact production and consumption, and command-DAG edges through a
complete accounts-payable operation in the standalone CLI test harness.

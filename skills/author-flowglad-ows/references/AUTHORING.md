# Authoring Flowglad OWS programs

> Generated from `flowglad/provisioning-agent@53a6e5f3c888c08b5c564dff9c76adfaf05f8cd3` (`packages/workflow-compiler/AUTHORING.md`). Do not edit this exported file directly.

This is the author reference for the Flowglad dialect of Open Workflow
Specification (OWS). A Flowglad automation program is an OWS 1.0.3 workflow
that opts into Flowglad profile v1 and calls the versioned Flowglad task
catalog.

Use this guide to write the canonical workflow document. The executable source
of truth is the document itself, not a runner-specific intermediate
representation.

> **Execution status:** Flowglad validates and publishes these documents as
> immutable revisions for the standalone OWS executor. Activation verifies the
> exact bundle, closure, digests, and runtime identity. Compiler validity alone
> does not authorize execution; the revision must also be activated.

The normative upstream language is
[OWS 1.0.3](https://open-workflow-specification.org/). This guide documents the
additional restrictions and `fg` fields enforced by
`@fg/workflow-compiler`.

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
            path: automations/normalize.py
          entrypoint: normalize
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

Replace the resource path with an actual Python file in the Automation's Space.
The compiler accepts the shape; publication also checks that the resource is
accessible and has a valid Python entrypoint.

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
| Existing Space files supplied to the workflow | `document.metadata.fg.inputFiles` |
| One file supplied by the triggering invocation | `document.metadata.fg.invocationArtifacts` |
| File/JSON artifact identity and integrity | `with.fg.produces` and `with.fg.consumes` |
| Authenticated connection actions | `with.fg.exactAuthentication` on a code call |
| Pinned admitted MCP reads | `with.fg.mcpAccess` on a code call |
| Exact Flowglad Page reads | `with.fg.pageAccess` on a code call |
| Approval-bound terminal command proposal | `with.fg.terminal` on the final code call |
| Security capabilities | Do not author them; the compiler derives them |

### Exact-authentication binding lifecycle

Every `exactAuthentication.connections[].connectionId` must be a concrete, active,
nondeleted connection owned by the automation's organization. Its declared
`connector` must match the connection's sealed connector identity, and the
connection must be exposed either in the automation's owner Space or through
that Space's forward effective linked-Space closure.

Flowglad revalidates these bindings when a revision is published, whenever it is
activated or selected by rollback, and again immediately before run preparation
creates storage objects or grants. Runtime authorization remains mandatory to
close races after dispatch.

At runtime, `source_unavailable` means the connection is missing, inactive,
deleted, or no longer visible and produces the noncritical
`ows-runtime.host.binding_unavailable` event. `source_identity_mismatch` is
reserved for a visible, eligible connection whose connector disagrees with the
immutable declaration and produces the critical `ows-runtime.host.auth_failure`
event. Database resolution failures use `source_resolution_failed`.

### Denied exact-read settlement

New compilations seal `deniedResponsePolicy: fail-task` into every
`exactAuthentication` declaration that omits the field. Under this strict policy,
any exact-read response with status `denied` fails the task after the child process
has shut down but before its direct result is validated or any output artifact is
admitted. Catching the injected SDK exception in customer Python therefore cannot
convert an authorization denial into successful platform settlement.

Authors may explicitly set `deniedResponsePolicy: allow-handled` when degraded
execution is intentional and reviewed. Immutable historical bundles in which the
field is absent remain valid and use the same legacy `allow-handled` behavior; the
schema deliberately does not apply a parse-time default to those bundles. The SDK
continues to raise for denied calls in every policy mode—the field controls platform
settlement, not Python exception behavior.

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
- `https://flowglad.com/ows/extensions/mcp-access/v1`
- `https://flowglad.com/ows/extensions/page-access/v1`
- `https://flowglad.com/ows/extensions/runtime-profile/v1`
- `https://flowglad.com/ows/extensions/artifacts/v1`
- `https://flowglad.com/ows/extensions/invocation-artifacts/v1`
- `https://flowglad.com/ows/extensions/space-file-inputs/v1`
- `https://flowglad.com/ows/extensions/terminal-command-dag/v1`

List the extensions on which the program relies. An unknown required URI is a
compile error rather than an instruction to ignore unfamiliar behavior.
Programs that declare `mcpAccess` should include
`https://flowglad.com/ows/extensions/mcp-access/v1` so an executor that does
not understand pinned MCP reads fails before execution.

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

Call `code:1.0.0@flowglad` for a Python program.

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
      path: automations/reconcile.py
    entrypoint: reconcile
    consumes: []
    produces: []
```

The resource is one of:

```yaml
# A Python file in a Space
kind: space-file
path: automations/reconcile.py
```

```yaml
# An exact Python module in a verified Skill revision
kind: skill-revision
revisionId: skr_123
path: scripts/reconcile.py
```

Space-file paths are normalized relative POSIX paths, must end in `.py`, and
must not contain empty, `.`, or `..` segments. The path is always resolved in
the Automation's owning Space; authors do not repeat that Space ID. A Space file
is intentionally live: each run resolves its current bytes, snapshots that
version once for the run, and records the calculated SHA-256 digest internally.
For a Skill, `revisionId` identifies the immutable verified revision manifest.
Flowglad derives its parent Skill identity and verifies organization and Space
access; authors do not repeat `skillId`. `path` selects the Python module inside
that sealed bundle and must name a `.py` file under `scripts/`. Flowglad derives
and verifies Skill manifest and file digests internally. The code task's
`entrypoint` selects the public top-level function inside the module; Skill CLI
entrypoint IDs do not participate in OWS execution.

Authors do not select or configure a code runtime. The compiler seals Flowglad's
fixed Python 3.11 runtime and 128 MiB memory limit into every code task. An
authored `runtime` field is rejected. If a task exceeds the fixed limit, the
task fails; configurable runtime policy can be introduced later if operational
evidence requires it.

Each code task declares one public top-level Python function through
`entrypoint`. A plain selected function must be synchronous and declare zero
parameters. A function that needs injected task input or artifacts uses
`@entrypoint` from `flowglad.entrypoints`; the decorator binds its annotated
parameters and exposes a zero-argument wrapper to the OWS runtime. Publication
statically reads the OWS-selected declaration from the currently resolved bytes and,
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
      systemPrompt: Return the document number.
      instructions: Use only the supplied task input.
    consumes:
      - name: invoice-pdf
        as: invoice_pdf
    produces: []
```

Authors define the prompt identity and content; they do not select a provider,
model, reasoning effort, output-token limit, or result-byte limit. At
publication, Flowglad resolves those implementation details from its
organization-scoped inference policy and seals them into the immutable task
profile. This keeps executions reproducible while allowing Flowglad to operate
and evolve model routing without exposing it as workflow configuration. Put the
result shape in the task's standard OWS `output.schema`; do not duplicate it
under `with.fg`.

The authored profile is strict: `provider`, `model`, `reasoningEffort`,
`maxOutputTokens`, and `maxResultBytes` are rejected if supplied. Update and
republish older source documents instead of carrying those fields forward.

An inference task may consume declared upstream artifacts through the same
`with.fg.consumes` contract as a code task. The executor admits and copies each
artifact into a task-local read-only slot, and the host verifies its alias,
path, media type, size, and digest before constructing native model content
blocks. Profile v1 accepts PDF, JSON, GIF, JPEG, PNG, and WebP inference
artifacts. PDFs and images become native document/image blocks; JSON becomes a
bounded plain-text document. The ordinary standard OWS task input remains a
separate JSON value and is included alongside those files.

## Browser-agent calls

Call `browser-agent:1.0.0@flowglad` for a bounded browser-agent session.

```yaml
call: browser-agent:1.0.0@flowglad
with:
  fg:
    profile:
      id: download_statement
      connectionId: dsrc_123
      instructions: Download the requested statement as a PDF.
      maxSteps: 20
    consumes: []
    produces: []
```

`connectionId` identifies the Website Access connection visible to the
Automation's Space. At execution time, the trusted host derives the starting
HTTPS URL from the connection's configured host and path. It also derives
whether the site is public or requires the connection's active saved login;
authors never provide an origin, authentication strategy, or `loginAccountId`.

Browser navigation may follow ordinary public HTTPS redirects, including
cross-origin identity-provider redirects. Credential access remains limited to
the selected connection. The connection, authored instructions, and step bound
are sealed into the task profile. The host automatically loads a vendor skill
matching the resolved start URL when one is available. If no vendor skill
matches, the browser agent runs with its generic safety prompt and the authored
instructions. `maxSteps` is an integer from 1 through 100.

## Artifacts

### Space-file inputs

An existing file in the Program's Space can enter the workflow as an initial
artifact. Declare each required exact Space-visible path once in document
metadata:

```yaml
document:
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1
      inputFiles:
        - name: invoice-pdf
          path: inputs/invoice.pdf
          mediaType: application/pdf
          maxBytes: 20000000
```

A task consumes the declared name through the ordinary artifact contract:

```yaml
with:
  fg:
    consumes:
      - name: invoice-pdf
        as: invoice_pdf
```

Paths are exact normalized relative POSIX paths in the Program's owning Space
or its effective linked-Space scope. Globs, arbitrary Space IDs, and the
executor-reserved `bundle/`, `code/`, and `invocation/` roots are not accepted.
`maxBytes` defaults to 10 MiB and is capped at 100 MiB. Each run captures the
current file version once and records the digest calculated while staging it.

The runtime admits these files as read-only initial artifacts. They are visible
only to tasks that declare `consumes`, and they are not published as workflow
output artifacts. This `inputFiles` declaration is distinct from a code
resource whose `kind: space-file` selects a live Python module.

### Invocation artifact input

An Inbox-triggered Program can require one file from the triggering email as an
initial artifact. Declare its stable OWS reference name, expected media type,
and byte bound:

```yaml
document:
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1
      invocationArtifacts:
        - name: invoice-pdf
          mediaType: application/pdf
          maxBytes: 25000000
```

Profile v1 admits exactly one invocation-artifact declaration. At dispatch,
Flowglad requires exactly one active Inbox attachment whose content type matches
the declaration. Zero or multiple matches fail before execution. The runtime
verifies the attachment digest, stages it below
`/in/invocation-artifacts/<name>/`, and exposes it only to tasks that declare
the same name in `with.fg.consumes`. The artifact name is the workflow reference;
it does not need to match the attachment's original filename.

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
| `as` | Optional task-local alias. It defaults to `name` with hyphens replaced by underscores and is also the inference attachment title. |
| `fileName` | Optional browser-download basename. The compiler otherwise derives a filename from `name` and `mediaType`. |
| `mediaType` | Required producer media type; an optional consumer assertion that must match. |
| `maxBytes` | Optional positive producer-side bound, at most 100 MiB. It defaults to 10 MiB. |

The compiler generates the physical path. `fileName` identifies a provider
download when a browser task needs one; it does not grant access to an authored
filesystem location. A consumer uses the string shorthand above when the
default alias is sufficient. The object form supplies an explicit alias or an
additional media-type assertion:

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
expose `path`, `media_type`, `max_bytes`, `open()`, `write_bytes()`,
`write_text()`, and `write_json()`. JSON helpers require
`application/json`; text helpers use UTF-8. Input objects do not expose write
methods, and output objects do not expose read methods.

Within each task, consumed names, produced names, and all aliases are unique. An
artifact must be produced before it is consumed, and two tasks cannot produce
the same workflow artifact name. The executor computes and records each
produced artifact's actual digest and binds that digest to downstream reads.

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
          queryTemplate:
            - name: include
              value: line_items
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
  accepted. Query strings and fragments remain forbidden in the path.
- A `{{parameter_name}}` path placeholder must be declared in
  `parameterSchema.properties`.
- A GET action may declare up to 128 ordered `queryTemplate` entries. Each name
  is static, while its string value may contain `{{parameter_name}}`
  placeholders declared in `parameterSchema.properties`. Placeholder values
  must be strings, numbers, or booleans at runtime. Repeated names are
  preserved, and the authenticated-fetch service URL-encodes every name and
  materialized value. URL encoding does not escape a provider-specific query
  language, so its parameter schema must constrain any value embedded in one.
- A `GET` action has `bodyTemplate: null` and does not declare `bodyKind`. A
  POST action requires a body and cannot declare query parameters in profile
  v1. POST bodies default to `bodyKind: json` when the field is omitted.
- A read-only GraphQL POST declares `bodyKind: graphql`. Its `bodyTemplate`
  contains `query` plus optional `variables` and `operationName`; after exact
  placeholder substitution, the host materializes the authenticated-fetch
  GraphQL body. The provider adapter still parses the document and rejects
  mutations, subscriptions, unsupported multi-operation documents, or unsafe
  variables before dispatch.
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

Python supplies only the declared action parameters. It does not concatenate
URLs or encode query strings; the host materializes the sealed path and query
templates before dispatching the authenticated request.

For example, a declared Shopify Admin GraphQL query uses an explicitly typed
body while keeping the query and variables bounded by the parameter schema:

```yaml
name: inventory_quantities
method: POST
pathTemplate: /admin/api/2026-07/graphql.json
queryTemplate: []
bodyKind: graphql
bodyTemplate:
  query: '{{query}}'
  variables:
    ids: '{{ids}}'
  operationName: InventoryQuantities
parameterSchema:
  type: object
  additionalProperties: false
  required: [query, ids]
  properties:
    query: {type: string}
    ids:
      type: array
      minItems: 1
      maxItems: 25
      items: {type: string}
resultSchema:
  type: object
  additionalProperties: true
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

## Pinned MCP access

Only a code call may declare MCP reads. `mcpAccess` pins an admitted operation
to a connection, catalog revision, input schema, and operation hash; it never
contains transport or credential material. Its limits are required and bound
all reads in that task. `maxResponseBytes` is capped at 262144 bytes, while the
cumulative response limit cannot be lower than the per-call limit.

```yaml
with:
  fg:
    # resource and entrypoint omitted
    mcpAccess:
      connections:
        - connectionId: dsrc_billing
          as: billing
          reads:
            - name: list_invoices
              operationId: invoices.list
              toolName: list_invoices
              catalogRevisionId: mcrv_billing_v1
              schemaHash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
              operationHash: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
              inputSchema:
                type: object
                additionalProperties: false
                properties:
                  limit: {type: integer, minimum: 1, maximum: 10}
              outputSchema: # optional; validated when present
                type: object
                required: [items]
                properties:
                  items: {type: array}
      limits:
        maxCalls: 2
        maxResponseBytes: 16384
        maxCumulativeResponseBytes: 32768
        maxWallTimeMs: 5000
```

`as` is the task-local Python connection alias, `name` is the Python method on
that alias, and `operationId` is the immutable catalog operation identity.
`toolName`, `catalogRevisionId`, `schemaHash`, `operationHash`, and
`inputSchema` are required pins; `outputSchema` is optional because admitted
MCP servers may omit it. Connection aliases and method names must be lowercase
Python identifiers, and a method name cannot be shared with another declared
read or terminal command on that alias.

Python calls only the sealed method with one `arguments` object:

```python
from flowglad.connections import billing

result = billing.list_invoices(arguments={"limit": 10})
```

Before provider I/O, the runtime rechecks the connection identity, active
catalog revision, schema hash, operation hash, and admission status. An
unadmitted operation or stale catalog/schema/operation pin fails closed. The
bridge also validates `arguments` against `inputSchema`, enforces the declared
call/byte/wall-time budget, and validates the normalized result against
`outputSchema` when it was declared.

## Terminal command DAGs

The only profile-v1 terminal effect is an approval-bound command DAG proposal.
Declare it on a code call:

```yaml
with:
  fg:
    # resource and entrypoint omitted
    terminal:
      kind: command-dag
      connections:
        - connectionId: dsrc_qbo
          as: quickbooks
          connector: quickbooks
        - connectionId: dsrc_browser_portal
          as: vendor_portal
          connector: untyped
```

Declaring a terminal connection opts into connector-owned constructors sealed
by the compiler. It grants proposal construction only: it creates no
authenticated-read grant, host client, private socket, or provider operation.
Every command node in the connector's shared contract becomes a method on the
connection alias. Method names replace command-tag hyphens with underscores;
for example, `send-slack-message` becomes `send_slack_message`.

The generated SDK is exhaustive for the command node types available to the
terminal task:

| Available node type | Author-facing constructor |
| --- | --- |
| Static non-connector command | Standalone `flowglad.commands.<tag_as_snake_case>(**fields)` |
| Connector-provided command | `flowglad.connections.<alias>.<tag_as_snake_case>(**fields)` |
| Untyped browser order | `flowglad.connections.<alias>.order(**order_fields)` |

An unavailable node type has no synthetic constructor. Conversely, authors do
not hand-author `tag` or connection identity for an available type: its
constructor seals them. Static constructors require `terminal`; connection
methods additionally require the matching entry under `terminal.connections`.

The Untyped connector additionally declares the dynamic browser-order
capability. Its connection alias exposes `order(...)`; the compiler derives the
typed tag from the sealed connection ID:

```python
from flowglad.commands import command_dag
from flowglad.connections import vendor_portal

proposal = command_dag(
    vendor_portal.order(
        version="2",
        title="Submit vendor invoice",
        login_account_id="lacc_vendor_portal",
        slots={},
        steps=[
            {
                "kind": "act",
                "id": "submit_invoice",
                "title": "Submit invoice",
                "effect": "write",
                "description": "Submit the reviewed invoice",
                "intent": "submit",
            }
        ],
    ),
    title="Submit vendor invoice",
    reasoning_summary="Propose reviewed browser work on the selected portal.",
)
```

For a connection ID such as `dsrc_browser_portal`, this emits
`tag: "order_dsrc_browser_portal"` and
`connection_id: "dsrc_browser_portal"`. Neither field is caller-controlled.
`login_account_id` remains an ordinary kwarg because the typed browser-order
schema conditionally requires or forbids its exact value according to the
connection's authentication facts.

Declaring `terminal` also seals every static non-connector command node as a
standalone function in `flowglad.commands`, using the same tag-to-snake-case
mapping:

```python
from flowglad.commands import command_dag, publish_flowglad_files

proposal = command_dag(
    publish_flowglad_files(
        files=["close-report.md"],
        outputs=[{"path": "close-report.md", "render": "inline_markdown"}],
    ),
    title="Publish close report",
    reasoning_summary="Propose publishing the reviewed close report.",
)
```

Today this surface includes `publish_flowglad_files`,
`create_flowglad_page`, and `edit_flowglad_page`. Their kwargs become command
root fields; Python cannot override the sealed tag or dependency-envelope
fields.

Helper-command kwargs become command-root fields. Command-family methods expose
their selector explicitly and accept provider payload fields as flattened
kwargs. For example, QuickBooks `create-qbo-entity` becomes
`create_qbo_entity`:

```python
from flowglad.commands import command_dag
from flowglad.connections import quickbooks

proposal = command_dag(
    quickbooks.create_qbo_entity(
        object_kind="expense",
        AccountRef={"value": "42"},
        TotalAmt=19.95,
    ),
    title="Create QuickBooks expense",
    reasoning_summary="Propose one reviewed expense.",
)
```

The constructor lowers that declaration to this exact command envelope:

```json
{
  "tag": "create-qbo-entity",
  "connection_id": "dsrc_qbo",
  "object_kind": "expense",
  "payload": {"AccountRef": {"value": "42"}, "TotalAmt": 19.95}
}
```

The sealed connection identity, tag, selector field, and payload field cannot
be overridden by Python. Connector-declared family root fields, such as QBO's
optional `target` mapping overlay, remain at the command root; all other family
kwargs are nested under `payload`. Helper methods retain all supplied command
fields at the root. Use `command_file_name` to override a node's generated JSON
basename when proposing multiple nodes with the same tag; a provider field named
`file_name` remains ordinary command data. The generic
`flowglad.commands.command` helper remains available as a low-level compatibility
escape hatch for legacy or custom tags that have no generated constructor. Do
not use it to hand-author an available static, connector, or browser-order node.
Artifact-backed publication is the deliberate exception: no new typed helper API
is provided for this runtime-only form. Name admitted artifacts on explicit writes
and express deletes directly:

```python
publish = command('publish-flowglad-files', changes=[
    {'operation': 'write', 'path': 'financialData.json', 'artifact': 'financial-data'},
    {'operation': 'delete', 'path': 'oldFinancialData.json'},
])
proposal = command_dag(publish, title='Publish financial data')
```

`command_dag` remains the terminal wrapper. At dispatch, artifact names resolve
only against the authoritative executable run; command execution verifies the
persisted byte length and SHA-256 digest before any Space-file mutation.

### Pinned MCP command proposals

An MCP terminal connection declares its commands explicitly rather than using
connector metadata. The command declaration has the same pinned identity shape
as an MCP read. `outputSchema` remains optional; it is not required to propose
the command.

```yaml
with:
  fg:
    # resource and entrypoint omitted
    terminal:
      kind: command-dag
      connections:
        - connectionId: dsrc_billing
          as: billing
          connector: mcp
          commands:
            - name: create_invoice
              operationId: invoices.create
              toolName: create_invoice
              catalogRevisionId: mcrv_billing_v1
              schemaHash: cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
              operationHash: dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
              inputSchema:
                type: object
                additionalProperties: false
                required: [customer_id, amount]
                properties:
                  customer_id: {type: string}
                  amount: {type: number}
```

The `as`, `name`, and `operationId` relationship is identical to MCP reads:
the declaration makes `billing.create_invoice` available, while
`invoices.create` remains the pinned admitted catalog identity. The constructor
emits the existing MCP command literal with sealed `connection_id`,
`operation_id`, `catalog_revision_id`, `schema_hash`, and `operation_hash`.

```python
from flowglad.commands import command_dag
from flowglad.connections import billing

proposal = command_dag(
    billing.create_invoice(
        arguments={"customer_id": "cus_reviewed", "amount": 19.95}
    ),
    title="Create reviewed invoice",
    reasoning_summary="Propose the pinned MCP invoice creation operation.",
)
```

MCP reads and MCP command constructors accept `arguments={...}` only. Flattened
kwargs are rejected so business arguments cannot collide with the reserved
command envelope or pinned identity fields. `command_file_name` is the sole
additional keyword for a command constructor and only changes its generated
node filename; construction remains an approval-bound proposal and never
dispatches the provider.

```python
from flowglad.commands import command, command_dag
```

The helper assigns each node's JSON filename and zero-based position,
materializes explicit and inferred edges, and returns an ordinary JSON mapping.
The executor owns the workflow-run association, so scripts do not provide
producer identity.
Every command declaration has an immutable `output` namespace. Passing a prior
command output as a later command's top-level input infers the corresponding
data edge:

```python
from flowglad.commands import command_dag, publish_flowglad_files
from flowglad.connections import gmail

publish = publish_flowglad_files(files=["report.pdf"])
draft = gmail.create_gmail_draft(
    to=["recipient@example.com"],
    subject="Report",
    attachment_file_ids=[file.file_id for file in publish.output.flowglad_files],
)
proposal = command_dag(
    publish,
    draft,
    title="Publish and attach report",
    reasoning_summary="Attach the newly published report.",
)
```

The SDK treats the comprehension as a symbolic projection of every published
file's canonical ID and binds that projection to `attachment_file_ids`; the
unresolved target value is not serialized into the draft's `commandData`.
Each symbolic item in `publish.output.flowglad_files` exposes `file_id`,
`storage_path`, `file_name`, and nullable `content_type`. The canonical-ID
projection shown above is the supported collection projection for command
inputs.
Use `source.output["provider-field"]` when an output field is not a valid
Python attribute name. `ordering_edge` and `data_edge` continue to accept
command declarations directly; use explicit `data_edge` for dotted or indexed
target paths. In every form, source code does not repeat filenames. The
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
- browser call → one connection-bound `browser.session`
- consumed artifact → `artifact.read`
- produced artifact → `artifact.write`
- authenticated connection action → `authenticated-read.exact`
- declared Page → `page.read.exact`
- declared MCP read → `mcp.read.exact`
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
- the pinned catalog and task-profile closure plus exact code-resource references;
- OWS, profile, compiler, and intended-executor versions; and
- the complete plan and closure digests.

Publication validates that referenced Space files are accessible, but their
bytes remain live between runs. Run preparation resolves each Space resource
once, snapshots those bytes for that run, and records its calculated digest and
source version. Publication requires an exact verified Skill revision and
derives its immutable manifest digest internally. An identical plan is
idempotent. Publication does not implicitly
activate a revision; activation fails closed unless the matching executor
version is available and the persisted bundle, closure, and digests match
exactly. Runtime routing is a separate, default-off feature-gated decision.

A different OWS revision, profile URI, catalog function version, or compiler
version is incompatible by default. Flowglad does not
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
   artifacts, and terminal topology, then seals Flowglad-owned inference policy.
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
- [MCP: pinned admitted read → pinned command DAG](./mcp-ows-v1.ows.yaml)

The examples are validated with the official OWS 1.0.3 schema and the Flowglad
compiler and generate the standalone executor's committed canonical bundles.
The invoice-reconciliation example exercises task injection, scoped connection
actions, artifact production and consumption, and command-DAG edges through a
complete accounts-payable operation in the standalone CLI test harness.

### M1 boundary

M1 provides compiler, executor, host, and internal-chat support for the pinned
MCP declarations above. Public `ows_authoring.list_connection_capabilities`
and `ows_authoring.get_connection_capability` are Milestone 2 tools and must
not be added by M1.

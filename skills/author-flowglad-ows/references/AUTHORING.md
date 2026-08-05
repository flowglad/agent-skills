# Authoring Flowglad OWS programs

> Public reference snapshot for `@fg/workflow-compiler` 0.1.0 and Flowglad
> automation profile v1. Keep this file synchronized with the compiler-owned
> authoring reference before publishing changes to the skill.

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
- [Exact authenticated HTTP authority](#exact-authenticated-http-authority)
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
of truth is the document itself—not a generated v0 definition, `StepSpec[]`, or
runner-specific intermediate representation.

> **Execution status:** Flowglad can validate and publish these documents as
> immutable, inactive revisions. They cannot be activated or executed until the
> standalone OWS executor is delivered. Compiler validity therefore does not
> imply current executability.

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
| Model or browser runtime profile | `with.fg.profile` |
| File/JSON artifact identity and integrity | `with.fg.produces` and `with.fg.consumes` |
| Exact authenticated HTTP authority | `with.fg.exactAuthentication` on a code call |
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
never grants authority.

Profile v1 rejects explicit `then` transitions, reusable functions, OWS task
extensions, third-party catalogs, schedules, composite tasks, forks, loops,
switches, retries, waits, event tasks, and generic `run` tasks. This is a
profile restriction, not a claim that OWS lacks those features. Supporting one
later requires a new profile/compiler version; authors must not emulate it with
an unrecognized `fg` key.

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

The future executor owns conformance to OWS expression and condition semantics.
The compiler currently proves that the document and supported profile are
valid; it does not execute expressions.

Canonical OWS tasks return their declared value directly. Do not wrap task
results in the legacy `continue-bail-v0` envelope. Use OWS failure, `if`, and
dataflow semantics. If execution work later demonstrates a missing outcome
concept, it will be introduced only through a new profile version.

## Code calls

Call `code:1.0.0@flowglad` for a pinned Python program.

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: space-file
      spaceId: spc_123
      path: automations/reconcile.py
      digest: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
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
# An exact, verified Skill revision entrypoint
kind: skill-revision
skillId: skl_123
revisionId: skr_123
entrypointId: ske_123
digest: sha256:...
```

Space-file paths are normalized relative POSIX paths, must end in `.py`, and
must not contain empty, `.`, or `..` segments. Publication reads the current
bytes, verifies the authored SHA-256 digest, and writes the bytes to the
content-addressed execution-resource store. For a Skill, the digest identifies
the verified revision manifest.

The only profile-v1 runtime is Python 3.11. `memoryMb` is an integer from 64
through 4096.

The OWS executor's code-process ABI is a Milestone 4 contract. OWS revisions are
inactive until that ABI exists. Authors may rely on the established direction
that structured files—not stdout—carry task results and that stdout/stderr are
logs, but must not infer a new OWS result envelope from the current v0 runner.

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
it by name on later consumers.

```yaml
# Producer
produces:
  - name: statement-pdf
    as: statement_pdf
    mediaType: application/pdf
    maxBytes: 10000000
    path: statements/latest.pdf

# A later consumer
consumes:
  - name: statement-pdf
    as: bank_statement
    mediaType: application/pdf
```

The fields have distinct purposes:

| Field | Meaning |
| --- | --- |
| `name` | Workflow-wide artifact identity. A consumer's `name` must match exactly one earlier producer. |
| `as` | Task-local programmatic name. It becomes the key in that task's artifact input/output manifest. |
| `path` | Producer-owned normalized relative output path. Open file bytes using the runtime manifest's path, not `as`. |
| `mediaType` | Required producer media type; an optional consumer assertion that must match. |
| `maxBytes` | Positive producer-side bound, at most 100 MiB. |
| `digest` | Optional SHA-256 assertion. A consumer assertion must match the producer declaration. |

In particular, `as` is not a filesystem address. A consuming script finds the
artifact manifest entry by `as`, then opens the exact path supplied in that
entry. Different consumers may choose different local aliases for the same
workflow artifact.

Within each task, consumed names, consumed aliases, produced names, and produced
aliases must be unique. An artifact must be produced before it is consumed, and
two tasks cannot produce the same workflow artifact name. Omit `digest` for
dynamic output whose bytes are not known until execution; the executor computes
and records the actual digest.

## Exact authenticated HTTP authority

Only a code call may declare exact authenticated access. Each authority grants
one bounded provider operation; it is not a general-purpose authenticated fetch
capability.

```yaml
exactAuthentication:
  authorities:
    - id: get_invoice
      connector: yooz
      sourceId: dsrc_123
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

- Authority IDs use the same lowercase stable-ID syntax as task names and are
  unique within the task.
- `pathTemplate` is provider-relative and starts with `/`; absolute URLs are not
  accepted.
- A `{{parameter_name}}` path placeholder must be declared in
  `parameterSchema.properties`.
- A `GET` authority has `bodyTemplate: null`.
- The same `sourceId` cannot be associated with different connectors in one
  task.
- There are at most 128 authorities and 128 calls. Per-response bytes are at
  most 2 MiB, cumulative bytes at most 16 MiB, and wall time at most 120 seconds.
  The cumulative response bound cannot be lower than the per-response bound.

The compiler derives one `authenticated-read.exact` grant per authority. Python
does not receive credentials. The executor/host interprets the sealed authority
and performs the provider call; an undeclared authority fails closed.

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
- exact authority → `authenticated-read.exact`
- terminal declaration → `terminal-command-dag.construct`

Changing a catalog call or `fg` declaration changes the derived grants and the
sealed plan digest. Arbitrary task metadata never grants authority.

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
resources. An identical plan is idempotent. OWS revisions remain inactive and
activation fails closed until the matching executor version is available.

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
3. Publication resolves organization-scoped code resources and verifies exact
   bytes/manifests before storing the inactive revision.

None of these executes the workflow. Runtime conformance belongs to the
standalone executor and differential-verification milestones.

## Complete examples

- [Yooz: code → inference → code](./yooz-bounded-document-number.ows.yaml)
- [Mock Bank: browser agent → PDF artifact → code](./mock-bank-browser-statement.ows.yaml)

The examples are validated with the official OWS 1.0.3 schema and the Flowglad
compiler.

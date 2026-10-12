# Authoring Flowglad OWS programs

> Generated from `flowglad/provisioning-agent@8267a6c9cdcd190993a413db554395b76708d7a0` (`packages/workflow-compiler/AUTHORING.md`). Do not edit this exported file directly.

This is the author reference for the Flowglad dialect of Open Workflow
Specification (OWS). A Flowglad automation program is an OWS 1.0.3 workflow
that opts into Flowglad profile v1 and calls the versioned Flowglad task
catalog.

Use this guide to write the canonical workflow document. The executable source
of truth is the document itself, not a runner-specific intermediate
representation.

An executable Flowglad Automation that runs authored Python is a two-part
artifact: an immutable executable-bundle revision owns the Python package,
tests, entrypoint declarations, and supporting files; the OWS Automation owns
orchestration and selects an exact revision and entrypoint. When
`automations.create_draft` and `automations.bundle.*` are advertised, new code
that is private to one Automation uses that Automation's owned bundle. An
intentionally reusable capability, or an Automation with existing Skill-owned
history, continues to use an exact `skill-revision`. Tool availability selects
the lane before authoring starts. A failed private authoring request never falls
back to creating a Skill, and bundle ownership is never reassigned.

Production execution requires exact verified content and explicit exposure.
Manual Skill development may still use a sealed deferred-verification revision.
Historical `skill-revision` and `space-file` resources and their explicit
development workflows remain supported. Do not upload a loose Python file as
the normal path for new code.

> **Execution status:** Flowglad validates and publishes these documents as
> immutable revisions for the standalone OWS executor. Activation verifies the
> exact bundle, closure, digests, and runtime identity. Compiler validity alone
> does not authorize execution; the revision must also be activated.

### Automatic task retries

The executor automatically gives every code, inference, and browser-agent task
six total handler attempts, separated by a fixed one-second delay. Cancellation
stops the current attempt or delay and prevents another attempt. Inputs are
evaluated once, successful earlier tasks are not replayed, and failures in
condition, input, output, or export processing remain terminal. There is no YAML
retry knob: OWS-authored `try`/`catch.retry` is not supported, and retry policy is
not sealed into task sidecars or revision bundles.

Agent tasks run once and spend their entire model-step budget in that single
handler attempt; failures are not automatically replayed.

The normative upstream language is
[OWS 1.0.3](https://open-workflow-specification.org/). This guide documents the
additional restrictions and `fg` fields enforced by
[`@fg/workflow-compiler`](https://github.com/flowglad/provisioning-agent/blob/8267a6c9cdcd190993a413db554395b76708d7a0/packages/workflow-compiler/src/contracts.ts).

## Start with this document

Before copying this example, call `automations.list` for the target Space and
read its top-level `authoringMode`. Stop if the call fails or the field is absent
or not `yaml-triggers`: authoring mode is fail closed and must not be guessed.
New revisions omit top-level `input`; follow
[Trigger authoring](#trigger-authoring) when the workflow needs a payload.

The smallest useful automation makes an explicit no-action terminal decision:

```yaml
document:
  dsl: '1.0.3'
  namespace: my-company
  name: decide-invoice-actions
  version: '1.0.0'
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1

use:
  catalogs:
    flowglad:
      endpoint:
        uri: https://flowglad.com/ows/catalogs/automation/v1

do:
  - decide-actions:
      input:
        from: '${ . }'
      call: code:1.0.0@flowglad
      with:
        fg:
          resource:
            kind: automation-file-bundle-revision
            revisionId: fbr_replace_with_verified_revision
            entrypoint: decide-actions
          terminal:
            kind: command-dag
      timeout:
        after: PT30S
      output:
        schema:
          format: jsonschema:2020-12
          document:
            type: object
            additionalProperties: false
            required: [title, reasoningSummary, nodes, edges]
            properties:
              title: { type: string }
              reasoningSummary: { type: string }
              nodes: { type: array, items: { type: object } }
              edges: { type: array, items: { type: object } }

output:
  as: '${ . }'
  schema:
    format: jsonschema:2020-12
    document:
      type: object
      additionalProperties: false
      required: [title, reasoningSummary, nodes, edges]
      properties:
        title: { type: string }
        reasoningSummary: { type: string }
        nodes: { type: array, items: { type: object } }
        edges: { type: array, items: { type: object } }
```

Package `scripts/decide_actions.py`, its entrypoint declaration, supporting
files, and a small synthetic OWS test in the Automation-owned bundle. Replace
the example revision ID with the exact verified revision returned by the bundle
lifecycle. Its
`decide_actions` function can return
`command_dag(title="No actions needed", reasoning_summary="The invoice is already reconciled.")`
to complete successfully without proposing commands. The compiler accepts the
shape; private workflow publication also checks same-owner selection, verification,
lifecycle provenance and installed runtime support before publishing an immutable
workflow revision. Activate that revision explicitly; configure enabled state
separately.

### Develop interactively through MCP

This flow needs only the public docs and external organization MCP;
it never requires repository access. Initialize MCP, list tools, call
`flowglad.context`, and use its current `referenceCatalog`. Use
`reference.search` only for public contracts and `workspace.search` only for
authorized workspace state. Read exact resources with `resources.read` until
`truncated` is false.

Use typed tools to inspect authorized inputs, fixture-validate unpublished
source, create the selected code resource, seal the workflow, and diagnose its
run:

1. Identify the Space-visible connection with `workspace.search`,
   `connections.list`, or `spaces.connections.list`. Same-account connections
   remain distinct handles: select by ID and `exposedSpaces`. Follow the exact
   connection's `capabilitiesUri` and read it with `resources.read`. If a
   representative provider payload is needed, call `connections.fetch`
   separately with that documented request and connection ID. Never guess a
   path, parameter, or response field.
2. Use those observations to author narrow input/result schemas and the
   `exactAuthentication` actions described below. Interactive fetch is a
   development aid; it does not replace the sealed connection grants required
   by an executable OWS revision.
3. Decide ownership before writing. Preserve a compatible existing Skill and
   use `author-flowglad-skill` when reuse is intentional or the Automation is
   already Skill-backed. Otherwise, when the private tools are advertised, use
   the Automation-owned flow below. If they are absent, report that private
   authoring is unavailable; do not manufacture a Skill as fallback.
4. Before a persistent write, call `skills.create_validation_job` for a Skill,
   or `automations.create_validation_job` for an Automation alone or with local
   Skills, using unpublished bytes and synthetic fixtures. Poll the matching
   subject's `automations.get_validation_job` or `skills.get_validation_job`
   tool to a terminal state. The real Python SDK fixture
   host performs zero product writes and zero live SDK/provider calls.
5. For a Skill lane, put the returned `revisionId`, package-local
   `scripts/...py` path, and selected function in `with.fg.resource` and
   `with.fg.entrypoint`, then follow the existing create/development lifecycle.
   For a private lane, submit immutable package files and poll the lifecycle
   receipt and package status. Put its exact revision and callable key in the
   Automation-private resource, revise the workflow, explicitly activate, then
   separately configure enabled state only when requested.
6. Call `automations.run`, retain its `runId`, and inspect
   `automations.get_run` status/summary first. List diagnostics or artifacts and
   retrieve only necessary members. Verify member/archive digests and
   completeness. Oversized members are never silently truncated; use
   `automations.get_run_telemetry` for the renewable authorized archive.
   Schedules and event-triggered dispatches fail closed while any
   referenced Skill revision is unpublished.
7. Iterate on the selected ownership lane. Submit a successor with
   `automations.bundle.create_candidate` and poll `get_lifecycle_request` plus
   package status. Promotion never activates a workflow; revise and activate
   explicitly. Never follow `latest` as an execution selector. Both owners
   support deferred manual development testing followed by `publish_revision`.

Use interactive fetch to learn the provider payload that the Skill must
normalize, then use run telemetry to diagnose that Skill entrypoint inside the
real Automation runtime. Never copy credentials, access tokens, or other
secrets into the workflow, Skill package, schemas, logs, or fixtures.

For the shorter publish-first path, omit `verificationMode: deferred` and
`development: true`; wait for the Skill to become `active`, then create and run
the Automation normally.

If a Skill's first revision is rejected, revise the same Skill from that newest
rejected base. An active revision is not required for recovery. Read explicit
revision state; do not create a duplicate Skill to escape rejected history.

Validation and run evidence are outcome-first. Treat `processing`, `expired`,
`failed`, partial, and omitted evidence explicitly. Renew an expired URL by
calling its typed owner read again; revocation, retention expiry, tampered keys,
and digest mismatches fail closed. Never reconstruct missing evidence from run
history.

## Trigger authoring

Call `automations.list` for the target Space before authoring or revising any
OWS source. Read the required top-level `authoringMode` from the successful
result, even when the returned automation page is empty. If mode discovery
fails, is absent, or is not `yaml-triggers`, do not write. Author
`document.metadata.fg.triggers`, omit top-level `input`, and use
`assets/starter.yaml-triggers.ows.yaml`; the immutable source revision is the
only trigger-authoring authority.

### Discover exact trigger contracts before writing

An event or schedule declaration requires this ordered read sequence before any
create or revision write:

1. Search the public authoring docs for the desired trigger with
   `reference.search`, or inspect the unauthenticated `manifest.json`
   HTTPS resource when MCP is unavailable.
2. Read the exact `triggers/**/<contractVersion>.json` resource
   with `resources.read` or its public HTTPS `downloadUri`.
3. Copy only fields admitted by the returned strict `declarationSchema`, using
   its examples as the shape reference.

Trigger references, including `declarationSchema` and `payloadSchema`, are
public docs. Their HTTPS URLs require neither authentication nor MCP.

Do not guess a type, version, selector, or connection. Event selector fields
are flattened directly under `event`; there is no `selector` or `rule` wrapper.
A connection-backed event must include the logical `connection` required by the
fetched strict schema. Declare that stable logical ID once in
`document.metadata.fg.connections` with its connector and a `connectionId`
binding. The binding may be `null` while the source is an unresolved portable
draft, or the concrete connection ID visible to the Automation's owning Space
when publishing. Flowglad resolves the event's logical `connection` to the
runtime `connectionId` without changing the event `contractVersion`; authored
source must not include `connectionId` inside the event. Follow the trigger
resource's related provider authenticated-read reference when its payload
identifiers require provider lookup. Do not author `spaceId` in a trigger:
Space ownership comes from the Automation, not from a declaration. File- and
Page-backed events likewise use only the exact selector fields returned by the
contract.

For newly authored Page triggers, use `flowglad:page.created` contract version
2 and `flowglad:page.content_updated` contract version 3. These exact versions
are selector-free and expose `payload.actorPrincipalId` as a required nullable
organization-principal ID. A member-caused Page mutation supplies the trusted
persisted principal; Automation, System, and legacy events supply `null`. Older
Page contract versions retain their historical payload shapes and do not expose
this field.

CEL filters may compare the nullable field directly. Keep the comparison
null-safe when the workflow should run only for one member, for example:

```text
event:
  type: flowglad:page.content_updated
  contractVersion: 3
  filter:
    language: cel
    version: 1
    expression: >-
      payload.actorPrincipalId != null &&
      payload.actorPrincipalId == "oprn_replace_with_org_principal"
```

Use `payload.actorPrincipalId == null` when the workflow intentionally targets
Automation, System, or legacy Page mutations. Do not treat Page member IDs,
user IDs, approver identities, or upstream Automation provenance as causal
principal evidence.

A schedule owns its recurrence in source as the exact fetched
`contractVersion` plus a supported, self-contained `rrule` containing both
`DTSTART` and `RRULE`. Do not write an independent schedule row or put the
recurrence in `automations.update` configuration in YAML mode. Manual triggers
do not use the trigger-contract catalog; they own an inline
`jsonschema:2020-12` payload schema.

Uploaded connector events use a separate `uploaded` member. They never extend
the static `event.type` catalog. Author this member only from a
permission-scoped uploaded-connector capability returned for the target Space;
do not infer its fields from a provider slug, `Connector.Custom`, or package
bytes. The declaration pins contract version 1, the exact immutable
definition/revision/digest, one provider event type, a published connection or
explicit qualification context, and the admitted normalization output schema:

```text
- id: uploaded-invoice-created
  uploaded:
    contractVersion: 1
    definitionId: ucd_example
    revisionId: ucr_example
    definitionDigest: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    eventType: invoice.created
    authority:
      kind: published
      connectionId: dsrc_example
    payloadSchema:
      format: jsonschema:2020-12
      document:
        type: object
        properties:
          invoiceId: { type: string }
        required: [invoiceId]
        additionalProperties: false
    payloadSchemaDigest: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```

The digest shown is illustrative: use the capability's canonical SHA-256
digest for the exact inline schema. Compilation validates shape, bounds, and
digest consistency but grants no provider authority. Publication, activation,
and dispatch reload the immutable uploaded definition and re-resolve the
current organization, Space, route, connection or qualification capability.
If any identity, visibility, schema, feature flag, or credential fact is stale,
the trigger fails closed. Uploaded providers are intentionally absent from the
public static trigger catalog.

```yaml
document:
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1
      connections:
        - id: meeting-notes
          connector: fireflies
          connectionId: dsrc_replace_with_visible_connection
      triggers:
        - id: meeting-completed
          event:
            type: fireflies:transcript.completed
            contractVersion: 1
            connection: meeting-notes
        - id: inbox-file
          event:
            type: files:file.inserted
            contractVersion: 2
            filter:
              language: cel
              version: 1
              expression: >-
                payload.filePath.startsWith("uploads/") &&
                payload.source == "user"
        - id: daily-review
          schedule:
            contractVersion: 2
            rrule: |-
              DTSTART:20260101T090000Z
              RRULE:FREQ=DAILY
        - id: on-demand
          manual:
            schema:
              format: jsonschema:2020-12
              document:
                type: object
                additionalProperties: false
                properties:
                  invoiceId: { type: string }
```

The schedule `rrule` is constrained by the runtime-owned schedule authoring
descriptor for its exact `contractVersion`. It must contain both `DTSTART` and
`RRULE`. Version 1 supports `DAILY`, `WEEKLY`, `MONTHLY`, and `YEARLY`. Version
2 additionally supports `HOURLY` and `MINUTELY`; `SECONDLY` remains unsupported
because the scheduler operates at minute resolution. A Z-suffix DTSTART uses UTC:
`DTSTART:YYYYMMDDTHHMMSSZ`. A timezone DTSTART preserves its non-empty TZID
token: `DTSTART;TZID=<timezone>:YYYYMMDDTHHMMSS`.

Version 2 supports the following RRULE parameter shapes:

| Frequency  | Allowed keys                                      | Required keys and combination rules                                                                                                                                                                                                                                        |
| ---------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `MINUTELY` | `FREQ`, optional `INTERVAL`                       | `INTERVAL` is a positive integer; omit it for every minute.                                                                                                                                                                                                                |
| `HOURLY`   | `FREQ`, optional `INTERVAL`                       | `INTERVAL` is a positive integer; omit it for every hour.                                                                                                                                                                                                                  |
| `DAILY`    | `FREQ`, optional `INTERVAL`                       | `INTERVAL` is a positive integer; omit it for every day.                                                                                                                                                                                                                   |
| `WEEKLY`   | `FREQ`, `BYDAY`                                   | `BYDAY` is required and contains one or more unqualified weekdays such as `MO,WE,FR`.                                                                                                                                                                                      |
| `MONTHLY`  | `FREQ`, `BYDAY`, `BYMONTHDAY`, optional `BYMONTH` | Use one ordinal weekday or a complete weeks-by-weekdays Cartesian product in `BYDAY`, or use one or more `BYMONTHDAY` values (`1`–`31`, `-1`, `-2`, `-3`). `BYDAY` cannot be combined with `BYMONTHDAY` or `BYMONTH`; `BYMONTH` may limit `BYMONTHDAY` to selected months. |
| `YEARLY`   | `FREQ`, `BYMONTH`, `BYMONTHDAY`                   | Both are required. `BYMONTH` contains one or more months from `1` through `12`; `BYMONTHDAY` contains exactly one positive day from `1` through `31`.                                                                                                                      |

`COUNT`, `UNTIL`, `BYHOUR`, `BYMINUTE`, `BYSECOND`, interval values on weekly or
longer frequencies, and other RFC RRULE keys are unsupported because the
schedule mode cannot preserve their semantics. Representative valid version 2
declarations are:

```text
DTSTART:20260101T090000Z
RRULE:FREQ=MINUTELY;INTERVAL=5

DTSTART;TZID=America/New_York:20260101T091500
RRULE:FREQ=HOURLY;INTERVAL=2

DTSTART:20260101T090000Z
RRULE:FREQ=DAILY;INTERVAL=2

DTSTART;TZID=America/New_York:20260101T090000
RRULE:FREQ=WEEKLY;BYDAY=MO,WE,FR

DTSTART:20260101T090000Z
RRULE:FREQ=MONTHLY;BYMONTHDAY=1,15,-1;BYMONTH=1,4,7,10

DTSTART;TZID=Europe/London:20260101T090000
RRULE:FREQ=YEARLY;BYMONTH=1,4,7,10;BYMONTHDAY=1
```

Every fetched event `declarationSchema` exposes that one optional `filter`.
Copy it exactly when needed; do not add it to schedule or manual declarations.
The only data root in filter dialect v1 is `payload`, typed from the exact
immutable `payloadSchema` returned for the selected event type and contract
version. Publication rejects unknown roots, misspelled paths, invalid operand
types, disallowed functions, and expressions whose root result is not Boolean.
Fields whose schema is open or dynamic may be compared for equality or null,
but cannot be traversed or passed to a type-specific function until a future
contract names and types that structure.

The complete author-facing v1 operation allowlist is:

- Boolean composition: `!`, `&&`, and `||`.
- Equality and ordering: `==`, `!=`, `<`, `<=`, `>`, and `>=` on compatible
  schema types.
- List membership with `in`, plus list literals.
- One non-nested canonical collection predicate, `.all(item, predicate)` or
  `.exists(item, predicate)`.
- `size(value)` or `value.size()` for strings, lists, and typed objects.
- String methods `contains`, `startsWith`, `endsWith`, `lowerAscii`, and
  `upperAscii`.

Construction, arithmetic transforms, regular expressions, decoding, HTML
parsing, generalized reduction, structure rewriting, `has`, `map`, and
API-recipe transform helpers are not available. A future dialect version must
introduce any expansion explicitly.

Nullable fields may use null-compatible equality or membership directly. Guard
a nullable value before a string or number-specific operation; v1 recognizes
the short-circuit forms:

```cel
payload.sender != null && payload.sender.startsWith("+1")
payload.sender == null || payload.sender.lowerAscii().endsWith("@example.com")
payload.sender in [null, "+15551234567"]
```

Filters are bounded to 8,192 UTF-8 expression bytes, 768 CEL AST nodes, 1,000
items in each list literal or runtime collection, one collection-predicate
level, and a 1 MiB projected payload. The runtime keeps at most 512 compiled
filter plans per process and recompiles a sealed expression on a cache miss.
Projection, compilation, or evaluation failure is fail-closed and creates no
Automation run.

CEL is only a deny-only narrowing step after Flowglad has admitted a candidate
through event type, connection, Space visibility and attribution,
authorization, and the fetched contract's structural selectors.

A filter does not grant access or select a connection or Space, change the
event type, or make an otherwise ineligible trigger a candidate. Schema-aware
CEL event-filter authoring is GA for every organization. Publication and sealed
dispatch do not consult an organization rollout flag for CEL filters.

New or changed file event declarations must use contract version 2; new Page
declarations must use the exact latest versions listed above. These declarations
express event-data narrowing with the optional CEL `filter`. Earlier Page/file
versions remain public and executable only as immutable history: an Automation
revision may carry one forward only when the same stable trigger ID has
canonically identical event JSON in the exact claimed base revision. Any
event-field change requires the appropriate latest-version declaration;
Flowglad never translates legacy selectors or rewrites historical source.

The trigger types, numeric versions, and selectors above are illustrative only.
Fetch and use each live exact type/version resource and its strict
`declarationSchema` before publishing. Each declaration contains a stable
unique `id` and exactly one of `event`, `schedule`, or `manual`. Each logical
connection declaration also has a stable unique `id`; event `connection`
selects that ID, never the concrete binding. Flowglad derives the top-level
input union as `{triggerId, payload}`; do not author that derived `input`
yourself.

Triggers have no Space field and no per-trigger `enabled` or paused state. To
pause or resume execution, use the automation-level `enabled` configuration on
`automations.update`. This does not revise trigger source. To change a trigger,
first read the exact Automation and latest revision with `automations.get`, then
call `automations.update` with `operation: revise`, its exact `baseRevisionId`,
and the complete replacement definition. The returned revision is immutable.
Activate it separately with `operation: activate`, `desiredRevisionId`,
`expectedActiveRevisionId`, and an idempotency key. Independent trigger-row
operations are unavailable; revise the YAML definition instead.

### Triggerless and invocation-artifact rules

A YAML-mode WIP may declare `triggers: []`. It still has no top-level `input`,
accepts no caller payload, and must not declare an invocation artifact or
collection. A manual
Run now of an active triggerless revision receives the platform-created empty
input object; it is not a caller-defined payload channel. Add a manual trigger
with an inline payload schema when callers need to supply values.

Current source must omit `invocationArtifacts` (an empty generic-serializer
value is tolerated, but every nonempty list is rejected). A source may instead
declare the event-owned collection described in [Artifacts](#artifacts), but
only for exactly one automatic `event` trigger whose exact shared trigger
contract declares collection support. Manual, schedule, uploaded, triggerless,
and multi-trigger workflows cannot declare a collection. The collection never
replaces its trigger declaration.

The singular upload and binding path remains available only when executing an
already sealed historical revision. For a historical manual run with a singular
artifact, the dashboard keeps the existing create upload session → HTTP PUT →
finalize upload session → execute sequence, pinned to the active executable
revision, stable YAML trigger ID, and sealed artifact name. Those upload-session
routes are a direct dashboard helper, not current authoring syntax or MCP
authoring tools; MCP clients use `automations.run` without receiving storage
write grants.

Compiler validity, publication validity, activation, and execution eligibility
are separate states. An empty top-level `do` list may be saved as an inactive
WIP revision but cannot be activated. Compilation with placeholder Skill,
connection, or contract identities proves source shape only; publication
resolves exact resources, authoring mode, connection visibility, trigger and
artifact compatibility, and other organization-owned constraints before any
revision is persisted. Resolve every publication diagnostic rather than
claiming the WIP is runnable.

## What is standard OWS and what is Flowglad-specific?

Keep portable workflow behavior in standard OWS fields. Use `with.fg` only for
behavior that OWS does not define.

| Concern                                                 | Author it in                                                              |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| Legacy workflow and task input/output schemas           | Standard OWS `input` and `output`                                         |
| YAML-trigger workflow input                             | Derived from `document.metadata.fg.triggers`; never authored at top level |
| Value selection and transformation                      | Standard OWS runtime expressions                                          |
| Ordered task dataflow                                   | Standard OWS `do`, `input.from`, and `export.as`                          |
| Conditional execution                                   | Standard OWS task `if`                                                    |
| Task timeout                                            | Standard OWS task `timeout`                                               |
| Python or Skill resource identity                       | `with.fg.resource` on a Flowglad code call                                |
| Python function selection                               | `with.fg.entrypoint` on a Flowglad code call                              |
| Inference, browser, or workspace-agent runtime profile  | `with.fg.profile`                                                         |
| Existing Space files supplied to the workflow           | `document.metadata.fg.inputFiles`                                         |
| Event-owned files supplied by the triggering invocation | Name-only `document.metadata.fg.invocationArtifactCollections`            |
| File/JSON artifact identity and integrity               | `with.fg.produces` and `with.fg.consumes`                                 |
| Authenticated connection actions                        | `with.fg.exactAuthentication` on a code or agent call                     |
| Pinned admitted MCP reads                               | `with.fg.exactAuthentication` with `kind: mcp` actions on code or agent calls                                        |
| Exact Flowglad Page reads                               | `with.fg.pageAccess` on a code call                                       |
| Approval-bound terminal command proposal                | `with.fg.terminal` on the final code call                                 |
| Security capabilities                                   | Do not author them; the compiler derives them                             |

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
4. Use explicit inline JSON Schema 2020-12 wrappers. Every `schema` must contain
   exactly `format: jsonschema:2020-12` and `document`; the compiler does not
   default a missing format. A `schema.resource` reference is rejected anywhere
   in profile v1 because publication cannot seal an unpinned schema fetch.
5. Put top-level tasks in a sequential OWS `do` list.

New revisions must not author top-level `input`. Declare the revision-owned
trigger array instead and let the compiler derive input. Discover and verify
the `yaml-triggers` mode through `automations.list` before writing.

`document.metadata.fg.requiredExtensions` is optional. When present, it is a
fail-closed compatibility assertion: every URI must be one of these profile-v1
URIs:

- `https://flowglad.com/ows/extensions/capabilities/v1`
- `https://flowglad.com/ows/extensions/exact-authentication/v1`
- `https://flowglad.com/ows/extensions/flowglad-access/v1`
- `https://flowglad.com/ows/extensions/page-access/v1`
- `https://flowglad.com/ows/extensions/runtime-profile/v1`
- `https://flowglad.com/ows/extensions/artifacts/v1`
- `https://flowglad.com/ows/extensions/invocation-artifacts/v1`
- `https://flowglad.com/ows/extensions/space-file-inputs/v1`
- `https://flowglad.com/ows/extensions/terminal-command-dag/v1`

List the extensions on which the program relies. An unknown required URI is a
compile error rather than an instruction to ignore unfamiliar behavior.
Programs that declare `exactAuthentication` (HTTP or MCP) or `flowgladAccess` should include their
respective `https://flowglad.com/ows/extensions/exact-authentication/v1` or
`https://flowglad.com/ows/extensions/flowglad-access/v1` URI so an executor
that does not understand the declared read surface fails before execution.

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

The runtime also applies platform ceilings to the declared timeout: code and
inference tasks may run for at most five minutes, while browser-agent tasks may
run for at most twenty minutes. The complete automation invocation remains
bounded to forty minutes.

Profile v1 rejects explicit `then` transitions, reusable functions, OWS task
extensions, third-party catalogs, schedules, composite tasks, forks, loops,
switches, retries, waits, event tasks, and generic `run` tasks. This is a
profile restriction, not a claim that OWS lacks those features. Profile v1 does
not accept them, and authors must not emulate them with an unrecognized `fg`
key. In YAML mode, supported Flowglad event and schedule declarations live only
in `document.metadata.fg.triggers`; they are not OWS schedule or event tasks.

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
[standalone executor code ABI](CODE_ABI.md) for function
returns, runtime values, artifact slots, logging, and connection actions.

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: automation-file-bundle-revision
      revisionId: fbr_exact_verified_revision
      entrypoint: reconcile
    consumes: []
    produces: []
```

For intentionally reusable code and existing Skill-owned histories, the
resource is an exact module in a sealed Skill revision:

```yaml
kind: skill-revision
revisionId: skr_123
path: scripts/reconcile.py
```

`revisionId` identifies the immutable sealed revision manifest. Normal
Automation publication resolves a verified revision. An explicitly
development-marked Automation may resolve a candidate or verifying revision
only when a verification-run record has sealed the package against mutation.
Flowglad derives its parent Skill identity and verifies that the exact revision
belongs to the Automation's organization; authors do not repeat `skillId`.
Skill resolution has no Space-owner check. The Automation's Space remains the
consumer boundary: Automation publication and runtime access, including run
history, retain their independent Space authorization. `path` selects the
Python module inside that sealed bundle and must name a `.py` file under
`scripts/`. Flowglad derives and verifies Skill manifest and file digests
internally. The code task's `entrypoint` selects the public top-level function
inside the module; Skill CLI entrypoint IDs do not participate in OWS execution.

The compiler still accepts `kind: space-file` for compatibility with existing
Automation revisions. Those paths are live and each run snapshots whatever
bytes are present at execution time. Preserve that resource kind only when
maintaining an Automation that already depends on it; do not choose it for new
Python or migrate Skill-owned code back to a loose Space file.

<a id="automation-private-bundle-entrypoints-gated"></a>

### Automation-private bundle entrypoints

When the private authoring capability is advertised, new code intended only for
one Automation references one exact revision of that Automation's own private
executable bundle. Source uses a readable stable entrypoint key:

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: automation-file-bundle-revision
      revisionId: fbr_exact_verified_revision
      entrypoint: reconcile
```

Do not add a Python `path`, separate callable/function, Automation owner ID, or
`with.fg.entrypoint`. Flowglad derives the owner from the exact revision,
resolves the key to its stable entrypoint ID and verified revision snapshot,
and authenticates the complete canonical file manifest. Every private code task
in one workflow must select the same exact bundle revision; authorized Skill
resources may coexist in the same workflow.

The private package lifecycle matches Skill submission, verification, and promotion,
while ownership stays with the Automation. Discover current tools with `tools/list`;
public documentation is not proof that a capability is installed or enabled.

1. Call `automations.create_draft` to create the disabled, inactive owner.
2. Call `automations.bundle.create_candidate` with `automationId`, the exact
   `baseRevisionId` (null initially), and complete files. Submission ensures the
   bundle and seals immutable bytes. For large packages, use
   `create_upload_session`, PUT every declared file, then
   `finalize_upload_session` with the signed `uploadSessionId` alone.
3. Poll `automations.bundle.get_lifecycle_request` with the returned `jobId`,
   then inspect `automations.bundle.get` and `get_revision`. A succeeded creation
   receipt with `verificationDispatched: true` proves dispatch, not publication.
   Immediate submission automatically verifies and promotes eligible current work.
4. Put the exact same-owner revision and discovered entrypoint key in the OWS
   source, then `automations.update` with operation `revise`. No OWS function
   binding is needed. Revise publishes a workflow without activating it.
5. Explicitly activate the returned workflow revision with `automations.update`
   operation `activate`. Configure enabled state separately, only when requested.

Later edits submit a successor with the exact active package base. If the first
submission is rejected, recover its files and use the newest rejected revision as
base on the same owner. Never mutate sealed bytes. Concurrent passing verification
can finish `verified` without becoming active; inspect package and workflow
selections separately and reconcile stale bases before a deliberate retry.

For pre-publication tests, submit with `verificationMode: deferred`. The creation
receipt has `verificationDispatched: false`. Publish a workflow with
`development: true`, explicitly activate it, and test only through manual Run now.
Then call `automations.bundle.publish_revision`, poll its lifecycle request and
package state, revise to a normal workflow, and activate explicitly. Development
workflows cannot run from schedules or events even after their package publishes.

`automations.bundle.restore_revision` selects a qualified previously published
(`active` or `superseded`) package under current owner authorization and selection
checks. It never changes workflow pointers. To use the restored package, revise
with its exact revision, activate that workflow, and separately configure it.
Never substitute `latest` for an execution selector.

Historical Automation-owned file-bundle workflows are unsupported for execution.
Recover source through `list_revisions`, `get_revision`, and
`read_revision_file`, verify file hashes, explicitly resubmit as a package, then
republish and activate a new workflow. Old upload sessions require a new session;
old pending update requests terminate with rebuild guidance and zero adoption.
Bindings cannot recover historical private execution. Stored source and history,
independent managed CLI tools, historical Skill execution, Applications, and live
Space-file behavior are retained.

Package authoring and receipt reads/replay require current owner and Space
authorization, independent of rollout configuration. Accepted work drains and
supported published pinned execution continues under current owner, lifecycle,
verification and runtime checks. Unsupported private workflows stay rejected.
Use owner lifecycle/exposure controls and explicit cancellation for recovery;
compatible whole-release rollback preserves stored histories and exact pins.

Trusted resolution carries internal `executablePackage` metadata for both owners;
this is not a new Skill upload format. Publication, activation, and preparation
require authenticated installed `flowglad-ows-executable-packages` capability
proof from the routed executor/host. Admission remains
`flowglad-ows-bundle-entrypoint-v1`; executor invocation-v2 and Automation upload
declaration-v2 are distinct contracts. Every private attempt rechecks current
owner authority, persisted selection, integrity, cancellation, and attempt budget.
Skills retain organization authorization and do not acquire private host callbacks.
Failure or unavailable capability never permits falling back to a manufactured Skill.

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

For an injected source function returning `R`, the decorator shape is
`Callable[P, R] -> Callable[[], R]`: write `@entrypoint` directly (never
`@entrypoint()`), and let the launcher invoke its zero-argument wrapper.

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
the complete task input. `ArtifactInput`, `ArtifactCollectionInput`, and
`ArtifactOutput` bind the matching task-local aliases. Artifact parameters match the workflow declaration
exactly for decorated functions; the decorator does not add a capability. A
plain zero-argument function can instead use the task-scoped
`flowglad.runtime`, `flowglad.artifacts`, and `flowglad.connections` modules.
The
[code ABI](CODE_ABI.md) defines the declaration grammar
and runtime failures.

### Code validation responsibilities

Authors put every structural constraint that JSON Schema can express in the
task input/output schemas, connection action parameter/result schemas, and
artifact declarations. The executor enforces those declarations at runtime, so
Python consumes admitted values directly instead of repeating defensive shape
checks.

| Executor owns                                                                                                                                                                       | Python resource owns                                                                                              |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Constructs the task-scoped modules and injects declared dependencies from sealed, admitted runtime state.                                                                           | Declares only the dependencies the selected function uses and implements the task behavior.                       |
| Validates the task input before process launch and the function return against the task's OWS schemas.                                                                              | Implements the transformation and checks semantic or cross-field invariants that the schemas do not express.      |
| Admits consumed artifacts and enforces path containment, media type, size, and digest; verifies every produced slot after exit.                                                     | Uses the declared artifact objects and checks domain meaning inside file content when the workflow requires it.   |
| Binds each `flowglad.connections` alias to sealed actions and each `flowglad.pages` alias to one visible Page; validates host results and enforces call budgets.                    | Chooses which declared reads to perform and checks business meaning, consistency, and completeness.               |
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

## Agent calls

Call `agent:1.0.0@flowglad` for a bounded task that needs repeated model/tool
interaction over files. The agent owns a task-local just-bash workspace; OWS
owns orchestration, artifact grants, the output schema, and subsequent actions.

```yaml
call: agent:1.0.0@flowglad
with:
  fg:
    profile:
      id: workspace-agent
      revision: 1
      instructions: Analyze the supplied input and return a concise summary.
      maxSteps: 20
      maxResultBytes: 65536
input:
  from: '${ . }'
timeout:
  after: PT5M
output:
  schema:
    format: jsonschema:2020-12
    document:
      type: object
      additionalProperties: false
      required: [summary]
      properties:
        summary: { type: string }
export:
  as: '${ $context + { review: . } }'
```

Task input is any JSON value, mounted as `/in/input.json`. Instructions belong
to the sealed profile. Identity and inference metering come from the host;
JSON input cannot grant capabilities. `maxSteps` bounds model turns (1–100),
and `maxResultBytes` bounds the UTF-8 JSON result (1–1,048,576 bytes). The task
also has an authored timeout bounded by the invocation's agent-task policy.
Cancellation terminates the loop and cancels in-flight authenticated reads.
Agent tasks spend their step budget in one handler attempt.

The model has `bash` and `return_result` tools. The workspace is a task-local
in-memory filesystem with standard just-bash utilities. `/workspace` and `/tmp`
are scratch directories. The system prompt lists only the step's declared
files, required outputs, and named connection actions. Native Python and browser
work remain separate OWS tasks.

Agents use the same optional `exactAuthentication` declaration as Python code
tasks. Each binding names a connection alias, immutable source, allowed actions,
parameter/result schemas, and shared read limits. Publication checks connection
eligibility and space visibility; execution uses the same authenticated-read
host, source identity checks, request templates, evidence, and budgets as scripts.
Credentials stay in the host. Input JSON and workspace files cannot grant access.

For a binding named `invoices` with action `get_invoice`, the agent calls:

```sh
read-connection invoices get_invoice '{"invoice_id":"INV-42"}' > /workspace/invoice.json
```

Only declared aliases and actions are callable. The prompt points to each
selected action's parameter/result schemas at
`/in/connections/<alias>/<action>.json`. These files describe the sealed bindings;
editing them does not change access. Successful reads write JSON to stdout;
errors write a code and message to stderr with a nonzero exit status.
`deniedResponsePolicy` defaults to `fail-task`: a denied read prevents result and
artifact publication even if the shell handles the error. `allow-handled` permits
the agent to complete after handling a denial, matching scripts.

Use `consumes` to inject reference material, data files, and reusable shell scripts
under descriptive aliases such as `matching_rules`, `invoices`, and `ledger`.
OWS selects those artifacts from earlier tasks or declared invocation inputs;
artifact consumption does not grant resource-catalog discovery. Bind live
connection actions only when the task needs additional authenticated reads.

The model calls `return_result({value: ...})` with any JSON value satisfying
the task's required inline `output.schema`, then ends its turn. Invalid results
produce tool feedback for correction within the step budget. A text answer
alone is not a result. Exhaustion, cancellation, and runtime errors fail the
step. A successful host response contains the JSON value itself.

`consumes` and `produces` use the ordinary OWS artifact declarations. Consumed
files appear at `/in/artifacts/<alias>` after path, size, media-type declaration,
and digest verification. They are private copies; changing a copy cannot change
the upstream artifact. Write every produced artifact to `/out/<alias>` before
submitting the result. Only declared outputs are published, under the declared
byte limits. The executor validates the result and admits the files before
making them available to following tasks. Other workspace files are temporary.
No undeclared invocation files are mounted.

Every Automation requires one final, unconditional terminal code task whose DAG
is the workflow output. An agent step returns task data and artifacts for later
steps; it is not itself a terminal command producer.

Agent tasks may also declare `flowgladAccess` for read-only Flowglad resource
operations. Invoke `read-flowglad <operation> '<JSON arguments>'`; input schemas
are mounted at `/in/flowglad/<operation>.json`. Read the Flowglad SDK resource
operations section for declarations and limits. Pinned MCP reads use
`exactAuthentication` and the same `read-connection` command as HTTP reads.
`pageAccess` and `terminal` remain code-only; pass their results through task input
or declared artifacts when needed. Do not author provider or model routing.

See [AGENT_CALLS.md](./AGENT_CALLS.md) for compatibility and rollout guidance.
The [agent-review example](agent-review.ows.yaml) shows an agent step
followed by the required terminal Skill-backed code task.

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

### Discovered download collections

When a browser task must collect an unknown number of attachments, declare one
named collection instead of static `produces`:

```yaml
with:
  fg:
    # profile and consumes omitted
    produces: []
    downloadCollection:
      as: attachments
```

`downloadCollection` accepts exactly `{ as: identifier }`; `as` is a lowercase
Python identifier (not a Python keyword). It is mutually exclusive with a
non-empty `produces` declaration. Existing static browser artifacts remain
available when their count, names, and media types are known in advance.

The browser task result exposes an ordered metadata-only manifest at the named
alias:

```json
{
  "attachments": [
    {
      "download_id": "dcm_opaque_capability",
      "file_name": "statement.pdf",
      "content_type": "application/pdf",
      "size_bytes": 12345,
      "content_digest": "sha256:..."
    }
  ]
}
```

Each `download_id` is opaque and run-scoped; it is not a `file_*` record, a
Flowglad file, a path, or a URL. Code may inspect this metadata and fan out
declared commands using the IDs, but it cannot read the member bytes or turn an
ID into a bearer URL. The platform preserves existing browser capture limits:
at most 32 downloads, 100 MiB per member, and 200 MiB total. The collection
does not impose MIME restrictions; target providers report unsupported files.

In the first release, collection member bytes are available only to terminal
commands that explicitly declare collection URL resolution. SharePoint's
`upload-sharepoint-file-from-url` is the initial adopter. Fan out one command
per manifest member and pass the opaque ID, not a URL:

```python
uploads = [
    sharepoint.upload_sharepoint_file_from_url(
        source_download_id=member["download_id"],
        target_ref=configured_target_ref,
        server_relative_url=destination_folder,
        # Optional: omit to retain member["file_name"].
        file_name=renamed_files.get(member["download_id"]),
    )
    for member in browser_result["attachments"]
]
proposal = command_dag(*uploads)
```

`source_download_id` and `source_url` are exclusive. The legacy URL branch
continues to require both `source_url` and `file_name`. Collection IDs remain
run-scoped capabilities; they are re-authorized at command execution and never
resolve to bytes inside OWS code.

## Artifacts

If an input originates as a file, preserve it as a file artifact. Never embed
complete file contents—raw text, bytes, Base64, or compressed encodings—inside
workflow JSON input. If no admitted artifact input fits, report the unsupported
boundary rather than inventing an encoding transport.

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
resource whose compatibility-only `kind: space-file` selects a live Python
module in an existing Automation revision.

### Invocation artifact collection input

An automatic event may supply one ordered, mixed-MIME collection. Before adding
the declaration, follow [Discover exact trigger contracts before writing](#discover-exact-trigger-contracts-before-writing)
and read the exact shared contract for the one selected event type and version.
Proceed only when that contract reports invocation-artifact collection support.
The workflow must contain exactly that one automatic `event` trigger: manual,
schedule, uploaded, triggerless, unsupported-event, and multi-trigger sources
cannot select an unambiguous collection contract.

Current source omits `invocationArtifacts` and may declare at most one
`invocationArtifactCollections` item. That item is exactly `{ name }`:

```yaml
document:
  metadata:
    fg:
      profile: https://flowglad.com/ows/profiles/automation/v1
      invocationArtifactCollections:
        - name: receipts
```

Authors cannot set `maxItems`, `maxItemBytes`, `maxTotalBytes`, `mediaTypes`,
source selectors, or multiple collections. Flowglad seals the platform defaults
into executable metadata: 32 items, 10 MiB per item, and 50 MiB total. The exact
shared connector contract owns collection membership and transport support; the
source name is only the stable workflow reference. The sealed collection accepts
any valid MIME type as bounded opaque transport and does not imply that a
consumer can interpret every format.

Older immutable bundles may contain a singular `invocationArtifacts` entry or
a refined collection with limits and `mediaTypes`. Those shapes are executable
compatibility data, remain readable and bindable without source rewrites, and
must not be copied into new or revised source. Current publication always uses
the collection-only, name-only grammar above.

Only code tasks consume a collection, using the explicit collection kind so it
cannot be mistaken for a singular artifact:

```yaml
consumes:
  - kind: collection
    name: receipts
    as: receipts
```

The runtime sorts members by ordinal and stages each exact member at
`/in/invocation-artifacts/<collection>/<zero-padded-ordinal>-<safe-filename>`.
An empty collection is valid. Python binds the alias through
`ArtifactCollectionInput`; the immutable collection supports `len`, iteration,
and indexing. Each member exposes `ordinal`, `file_name`, and the unchanged
singular read surface: `path`, `media_type`, `size_bytes`, `digest`, `open()`,
`read_bytes()`, `read_text()`, and `read_json()`.

```python
from flowglad.entrypoints import ArtifactCollectionInput, entrypoint


@entrypoint
def summarize(receipts: ArtifactCollectionInput) -> dict[str, int]:
    return {"count": len(receipts), "bytes": sum(item.size_bytes for item in receipts)}
```

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

| Field       | Meaning                                                                                                                           |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `name`      | Workflow-wide artifact identity. A consumer's `name` must match exactly one upstream producer.                                    |
| `as`        | Optional task-local alias. It defaults to `name` with hyphens replaced by underscores and is also the inference attachment title. |
| `fileName`  | Optional browser-download basename. The compiler otherwise derives a filename from `name` and `mediaType`.                        |
| `mediaType` | Required producer media type; an optional consumer assertion that must match.                                                     |
| `maxBytes`  | Optional positive producer-side bound, at most 100 MiB. It defaults to 10 MiB.                                                    |

The compiler generates the physical path. `fileName` identifies a provider
download when a browser task needs one; it does not grant access to an authored
filesystem location. A consumer uses the string shorthand above when the
default alias is sufficient. The object form supplies an explicit alias or an
additional media-type assertion:

Artifact transport is bounded admission, not semantic parsing, rendering,
spreadsheet recalculation, or document conversion. The runtime performs
content-aware validation for formats it recognizes: PDF, strict JSON and
selected structured text types, UTF-8 `text/*`, PNG/JPEG/GIF/WebP,
SVG/TIFF/BMP, OOXML Office and legacy CFB Office containers, OpenDocument
packages, ZIP, GZIP, and RTF. Packages are inspected structurally and bounded;
archive members are never exposed or executed and macros are never run.
Unrecognized MIME types remain opaque while retaining the same path, size,
digest, and provenance checks.

Inference attachments are a separate model-native policy limited to JSON, PDF,
GIF, JPEG, PNG, and WebP. Office files, archives, structured exports, additional
image formats, email containers, database files, audio/video, and generic
`application/octet-stream` remain transport-only until an explicit conversion
and model-size policy is added.

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

Artifact paths are `pathlib.Path` values, including `path` on every invocation
artifact collection member. Keep that value for normal artifact work: inputs and
members default to binary `open("rb")` and also accept `"r"`; outputs default to
binary `open("wb")` and also accept `"w"`, `"x"`, and `"xb"`. Text modes return
text streams, binary modes return binary streams, and every output write helper
returns its integer byte count. Use `member.path.name` or the artifact helpers
without converting the path first.

Convert with `str(...)` only when a JSON-backed API field requires a string.
For example, a terminal task that intentionally passes staged collection paths
to a sealed Gmail command's string-valued `attachment_file_ids` field makes the
conversion at that boundary:

```python
from flowglad.commands import command_dag
from flowglad.connections import gmail
from flowglad.entrypoints import ArtifactCollectionInput, entrypoint


@entrypoint
def propose_receipt_draft(receipts: ArtifactCollectionInput) -> object:
    draft = gmail.create_gmail_draft(
        to=["recipient@example.com"],
        subject="Receipts",
        attachment_file_ids=[str(member.path) for member in receipts],
    )
    return command_dag(
        draft,
        title="Draft receipt email",
        reasoning_summary="Prepare the reviewed receipt attachments.",
    )
```

This conversion is deliberately local: it does not change the runtime artifact
path type or replace artifact read/write helpers.

Within each task, consumed names, produced names, and all aliases are unique. An
artifact must be produced before it is consumed, and two tasks cannot produce
the same workflow artifact name. The executor computes and records each
produced artifact's actual digest and binds that digest to downstream reads.

## Authenticated connection actions

Code and agent calls may declare exact authenticated access. Agent tasks invoke
the declared actions with `read-connection`; see Agent calls for shell syntax.
Each connection binds an immutable connection ID to a task-local alias and a
bounded set of named provider actions. The declaration is not a general-purpose authenticated
fetch capability.

Before authoring this declaration, use MCP `workspace.search` to find the exact
Space-visible connection, follow its `capabilitiesUri` with `resources.read`,
and then use `connections.fetch` to inspect a small representative payload.
Fetching interactively verifies the provider-relative path, query/body shape,
and observed field types without putting credentials in source. Treat the
response as sample evidence rather than a complete schema: keep nullable and
optional fields honest, bound arrays and strings deliberately, and preserve
safe handling for structured provider errors. The published workflow must
still declare every runtime operation below; an MCP fetch does not grant the
executor undeclared access.

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
              invoice_id: { type: string }
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
- There are at most 128 connections and 128 total actions. Limits and each of
  their four fields may be omitted, which seals the maximum for the
  `exactAuthentication` surface in the generated read-budget table in
  [Flowglad SDK resource operations](#flowglad-sdk-resource-operations). The
  cumulative response bound cannot be lower than the per-response bound.

The compiler derives one `authenticated-read.exact` grant per connection action.
Python receives task-local aliases and methods, not credentials. The
executor/host interprets the sealed connection and action declaration and
performs the provider call; an undeclared pair fails closed. Import the alias
inside the selected function because the module exists only when the task's
`exactAuthentication` declaration installs that connection.

```python
def fetch_invoice():
    from flowglad.connections import invoices

    return invoices.get({"invoice_id": "inv_123"})
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
    query: { type: string }
    ids:
      type: array
      minItems: 1
      maxItems: 25
      items: { type: string }
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
identifiers and are not Python keywords. A task may declare at most 128 Pages.
Limits and each of their four fields may be omitted, which seals the maximum
for the `pageAccess` surface in the generated read-budget table in
[Flowglad SDK resource operations](#flowglad-sdk-resource-operations).

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

Code and agent calls declare pinned MCP reads as `kind: mcp` actions under
`exactAuthentication`. Each action binds an approved read operation to its
connection, tool, catalog revision, schemas, and hashes; declarations never
contain transport destinations or credentials. HTTP and MCP actions share the
same task call, cumulative-byte, and wall-time budgets. Each MCP response is also
limited to 262144 bytes or the task's per-call limit, whichever is smaller.
Limits and each of their four fields may be omitted, which seals the maximum
for `exactAuthentication` in the generated read-budget table in
[Flowglad SDK resource operations](#flowglad-sdk-resource-operations). The
cumulative response limit cannot be lower than the per-call limit.

```yaml
with:
  fg:
    # resource and entrypoint omitted
    exactAuthentication:
      connections:
        - connectionId: dsrc_billing
          as: billing
          connector: mcp
          actions:
            - kind: mcp
              name: list_invoices
              operationId: invoices.list
              toolName: list_invoices
              catalogRevisionId: mcrv_billing_v1
              schemaHash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
              operationHash: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
              inputSchema:
                type: object
                additionalProperties: false
                properties:
                  limit: { type: integer, minimum: 1, maximum: 10 }
              outputSchema: # optional; validates the complete tool result
                type: object
                required: [content, structuredContent]
                properties:
                  content: { type: array, items: { type: object } }
                  structuredContent:
                    type: object
                    required: [items]
                    properties:
                      items: { type: array }
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
def list_reviewed_invoices():
    from flowglad.connections import billing

    return billing.list_invoices(arguments={"limit": 10})
```

Agent tasks invoke the same declared action through the existing shell command:

```sh
read-connection billing list_invoices '{"limit":10}'
```

Arguments cannot replace the declared connection, operation, tool, or pins.
The returned data preserves the complete sanitized MCP result, including
`content` and any `structuredContent`; tool-reported errors are failures.
`outputSchema`, when present, validates that complete result rather than an
extracted structured payload. MCP schemas declaring Draft-07 use that dialect;
otherwise validation uses Draft 2020-12.

Before provider I/O, the runtime rechecks connection visibility and identity, active
catalog revision, schema hash, operation hash, and admission status. An
unadmitted operation or stale catalog/schema/operation pin fails closed. The
bridge also validates `arguments` against `inputSchema`, enforces the declared
call/byte/wall-time budget, and validates the complete result against
`outputSchema` when it was declared. Reads use the stored approved catalog;
they do not trigger discovery or repin an action. Historical HTTP declarations
remain executable. Legacy separate MCP declarations are unsupported and fail
contract validation before execution.

## Flowglad SDK resource operations

Code and agent calls may declare `flowgladAccess`. Agent tasks invoke declared
operations with `read-flowglad`; the Python surface below applies to code tasks.
It declares versioned, read-only resource operations; `limits` and each of its
four fields are optional. An
omitted field seals the maximum for the `flowgladAccess` surface.

```yaml
with:
  fg:
    flowgladAccess:
      operations: [spaces.list.v1, spaces.get.v1]
      limits:
        maxCalls: 10
```

<!-- generated:read-budget-policy:start -->
An omitted limit field means the maximum for its read surface.
HTTP and MCP actions share exactAuthentication task budgets. MCP results also have a 262144-byte backend ceiling.

| Read surface | maxCalls | maxResponseBytes | maxCumulativeResponseBytes | maxWallTimeMs |
| --- | --- | --- | --- | --- |
| exactAuthentication | 128 | 5242880 | 16777216 | 120000 |
| pageAccess | 128 | 2097152 | 16777216 | 120000 |
| flowgladAccess | 128 | 2097152 | 16777216 | 120000 |
<!-- generated:read-budget-policy:end -->

Each versioned operation name derives an unversioned task-scoped Python method
under `flowglad.resources`; for example, `spaces.list.v1` becomes
`flowglad.resources.spaces.list(...)`. The generated catalog is:

<!-- generated:sdk-operations:start -->
| Operation | Python call | Pagination | Summary |
| --- | --- | --- | --- |
| `files.get.v1` | `flowglad.resources.files.get(...)` | none | Gets metadata for one current file visible in the Automation owner closure. |
| `files.get_text.v1` | `flowglad.resources.files.get_text(...)` | none | Gets a bounded rendition of one file visible in the Automation owner closure. |
| `files.list.v1` | `flowglad.resources.files.list(...)` | cursor | Lists current files visible in the Automation owner closure. |
| `files.search.v1` | `flowglad.resources.files.search(...)` | cursor | Searches current file metadata visible in the Automation owner closure. |
| `files.semantic_search.v1` | `flowglad.resources.files.semantic_search(...)` | none | Semantically discovers current files visible in the Automation owner closure. |
| `pages.get.v1` | `flowglad.resources.pages.get(...)` | none | Gets metadata for one currently visible Flowglad Page. |
| `pages.get_content.v1` | `flowglad.resources.pages.get_content(...)` | none | Gets bounded current content for one visible Flowglad Page. |
| `pages.list.v1` | `flowglad.resources.pages.list(...)` | cursor | Lists currently visible Flowglad Page metadata. |
| `pages.revisions.get.v1` | `flowglad.resources.pages.revisions.get(...)` | none | Gets the bounded change represented by one visible Flowglad Page revision. |
| `pages.revisions.list.v1` | `flowglad.resources.pages.revisions.list(...)` | cursor | Lists durable revisions for one currently visible Flowglad Page. |
| `pages.search.v1` | `flowglad.resources.pages.search(...)` | cursor | Searches currently visible Flowglad Pages. |
| `pages.semantic_search.v1` | `flowglad.resources.pages.semantic_search(...)` | none | Semantically discovers currently visible Flowglad Pages. |
| `spaces.get.v1` | `flowglad.resources.spaces.get(...)` | none | Gets one visible Flowglad Space by ID. |
| `spaces.list.v1` | `flowglad.resources.spaces.list(...)` | cursor | Lists visible Flowglad Spaces. |
| `spaces.members.list.v1` | `flowglad.resources.spaces.members.list(...)` | cursor | Lists active registered principals with effective access to one visible Space. |
<!-- generated:sdk-operations:end -->

List methods return `{ items, nextCursor }`. `nextCursor` is either `null` or
an opaque cursor: pass it back unchanged and do not construct or inspect it.
Get methods return the resource dictionary directly. Cursors are bound to the
exact operation, Automation owner, resolved target Space, and normalized
filters; changing any of those inputs returns `invalid_cursor`. Pagination is
live rather than snapshot-based, so current link, deletion, and eligibility
changes apply to the next call.

```python
from flowglad.resources import files, pages, spaces
from flowglad.resources.pages import revisions
from flowglad.resources.spaces import members

visible_pages = pages.list(limit=25)
matching_pages = pages.search(query="forecast", space_id="spc_123")
semantic_matches = pages.semantic_search(query="cash runway", top_k=10)
page = pages.get(page_id="page_123")
content = pages.get_content(page_id="page_123")
revision_page = revisions.list(page_id="page_123", limit=25)
revision = revisions.get(revision_id="prev_123")
eligible_principals = members.list(space_id="spc_123")

finance_files = files.list(space_id="spc_123", path_prefix="Finance", limit=20)
matching_files = files.search(query="quarterly", space_id="spc_123", path_prefix="Reports")
semantic_files = files.semantic_search(
    query="cash runway",
    space_id="spc_123",
    path_prefix="Finance",
    top_k=10,
)
file_metadata = files.get(file_id="file_123", space_id="spc_123")
file_rendition = files.get_text(file_id="file_123", space_id="spc_123", max_chars=24_000)
```

Normal SDK denials raise `FlowgladError`, importable from `flowglad.errors` and
re-exported by `flowglad.resources`. Its public codes are `invalid_argument`,
`not_found`, `permission_denied`, `invalid_cursor`, and `budget_exhausted`.

At revision activation, the current actor must be allowed to declare each
requested Page or effective-member capability. After activation, the sealed
operation grant and durable Automation scope are the authority: calls use the
Automation organization and owner Space, independent of the creator's current
account, permissions, membership, or the identity that dispatched a manual
run. There is no feature-flag or runtime creator-permission check.

Every file read accepts one optional `space_id`. Omit it to search the Automation owner's complete
current forward-visible Space closure; supply the owner, a direct child, or a transitive descendant
to narrow to exactly that Space. Unreachable, reverse-only, and deleted targets return `not_found`.
`path_prefix` is optional on list, lexical search, and semantic search, is applied independently to
each selected Space-visible path, accepts `/` as the root spelling, and matches complete path
segments. File search trims the query and performs deterministic case-normalized substring matching
over file ID, basename, visible path, and non-null content type. It does not search file bodies.
List and search return only `fileId`, exact owner `spaceId`, `path`, `name`, `contentType`,
`sizeBytes`, epoch-millisecond `uploadedAt`, and `version`; body content, storage keys, organization
and submitter identity, and run metadata are excluded.

`files.semantic_search(query, space_id=None, path_prefix=None, top_k=10)` is non-paginated and
returns the exact object below. Matches contain current authorized descriptors plus rank and bounded
chunk context; use the returned `spaceId` and `fileId` for an exact follow-up read.

```json
{
  "matches": [
    {
      "fileId": "file_123",
      "spaceId": "spc_123",
      "path": "Finance/runway.txt",
      "name": "runway.txt",
      "contentType": "text/plain",
      "sizeBytes": 4096,
      "uploadedAt": 1795027200000,
      "version": 3,
      "score": 0.91,
      "snippet": "Current authorized runway evidence.",
      "chunkIndex": 0,
      "chunkCount": 2
    }
  ],
  "coverage": {
    "indexState": "ready",
    "partial": false,
    "candidateWindowTruncated": false
  }
}
```

`indexState` is one of `ready`, `empty_or_building`, `stale`, or `unavailable`. A truncated
candidate window always sets `partial: true`. The result never exposes indexed timestamps,
content hashes, indexed versions, generation tokens, per-match truncation, rejected identities, or
filtered counts. Known embedding/vector failures return an empty `unavailable` result; current
database or authorization failures fail the call.

`files.get(file_id=..., space_id=...)` returns one current visible descriptor.
`files.get_text(file_id=..., space_id=...,
max_chars=...)` is the explicit body capability and returns the shared text-or-binary rendition:
direct text remains text, PDF and Excel use the existing readable rendition, and other formats fall
back to Base64 binary. Text includes `truncated`; it is true only when `max_chars` shortened the
returned text, and no truncation marker is appended. The binary branch is not shortened. Missing,
deleted, excluded, stale, folder-marker, cross-Space, and otherwise inaccessible targets all raise
the same `FlowgladError` with code `not_found`.

For Page list and search, omitted `space_id` reads the owner Space's current
forward-visible closure; one supplied `space_id` narrows within that closure.
For member listing, omission means the owner Space only, while a supplied
Space likewise must be in the current forward-visible closure. `space_id` is
singular on every method, and arrays are rejected. Page results are non-deleted
and identify their owning Space. Page `get` and `get_content` deliberately map
an absent, deleted, cross-organization, or no-longer-visible Page to the same
`not_found` error.

`pages.semantic_search(query, top_k=10)` is a non-paginated discovery call.
The query is bounded to 1,000 characters, `top_k` is between 1 and 25, and the
result contains at most that many ranked matches. Each match combines current
visible Page metadata with bounded score, snippet, chunk-position, and index
timestamp fields. It never returns Page bodies, revision/hash provenance,
vectors, or a cursor; use `pages.get_content` for an explicit current read.

`pages.revisions.list` requires `page_id` and returns durable content-edit revisions
in descending `createdAt`, then descending `revisionId`, order. Each item
contains only `revisionId`, `revisionKind`, and `createdAt`. Its cursor is also
bound to the parent Page. `pages.revisions.get` accepts only `revision_id` and
returns `revisionId`, `pageId`, `revisionKind`, `createdAt`, and one non-null
`diff`; an absent or invisible revision and an absent or invisible parent Page
all produce the same `not_found` error. The public revision kinds are
`user_edit` and `automation_edit`.

A revision `diff` contains `changed`, exact lowercase SHA-256
`oldTextSha256`/`newTextSha256` identities, complete `addedLines` and
`removedLines` counts, `hunks`, and `truncated`. Hunk lines use only
`unchanged`, `added`, or `removed` as `kind`; `text` has no diff-marker prefix
and preserves its exact stored line terminator, including CRLF or a missing
final newline. Hunk coordinates are unified-compatible. At most 1,000 logical
lines and 256 KiB of UTF-8 line text are returned, only complete hunks are
retained, and `truncated` is true exactly when a complete hunk was omitted.
The SDK does not expose historical Page bodies or arbitrary revision comparison.

`spaces.members.list` returns only `principalId`, `userId`, `displayName`,
`email`, and `accessSources`. Sources are the public tagged variants
`{kind: "direct_space_membership", role}`,
`{kind: "linked_space_membership", sourceSpaceId, role}`, and
`{kind: "organization_role", role}`. Membership IDs, role IDs, effective
permission arrays, and organization metadata are never returned.
The returned `principalId` values can be passed unchanged as
`organizationOwnerPrincipalIds` to `create_flowglad_task`; the command remains
a proposal and persists neither the Task nor assignments until its command DAG
is approved.

Successful `pages.get_content` calls return bounded Markdown and an
`observationId`, and record supplemental `page.read.exact` evidence containing
the exact Page version and content digest accepted by edit commands. Other
resource calls, including semantic search and revision list/get, emit only one generic
`flowglad.read` evidence record. SDK lifecycle logs use executor-owned identity
and bounded vocabulary; arguments, cursors, filters, revision and Page IDs,
Page content, diff lines, principal data, permissions, access sources,
responses, paths, credentials, metadata, and exception messages are excluded.
Missing, backpressured, or dropped telemetry cannot change results or
`FlowgladError` details.

The complete authority, visibility, observation, cursor, and privacy contracts
are specified by the Flowglad OWS profile and the executor code ABI. See the
[executor code ABI](CODE_ABI.md) for the SDK operation
mechanics and the published authenticated-read references for provider-specific
capabilities.

Programs that declare `flowgladAccess` should include
`https://flowglad.com/ows/extensions/flowglad-access/v1` in
`requiredExtensions`, just as programs declaring HTTP or MCP actions under
`exactAuthentication` should include the exact-authentication URI. This advisory compatibility assertion lets an executor
that does not understand the declared SDK surface fail before execution.

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
connection alias. Method names are deterministic lowercase snake case: tag
separators and case boundaries become underscores, and names that exceed the
Python identifier limit receive a stable hash suffix. For example,
`send-slack-message` becomes `send_slack_message`.

The generated SDK is exhaustive for the command node types available to the
terminal task:

| Available node type          | Author-facing constructor                                    |
| ---------------------------- | ------------------------------------------------------------ |
| Static non-connector command | Standalone `flowglad.commands.<tag_as_snake_case>(**fields)` |
| Connector-provided command   | `flowglad.connections.<alias>.<tag_as_snake_case>(**fields)` |
| Untyped browser order        | `flowglad.connections.<alias>.order(**order_fields)`         |

An unavailable node type has no synthetic constructor. Conversely, authors do
not hand-author `tag` or connection identity for an available type: its
constructor seals them. Static constructors require `terminal`; connection
methods additionally require the matching entry under `terminal.connections`.
Import terminal constructors and aliases inside the selected function. The
verifier loads the module before it invokes the selected function, while those
bindings are available only for a task with the matching sealed declaration.
Terminal connection declarations grant command construction only; authenticated
reads still require `exactAuthentication`, with an HTTP action or a pinned
`kind: mcp` action as appropriate.

The Untyped connector additionally declares the dynamic browser-order
capability. Its connection alias exposes `order(...)`; the compiler derives the
typed tag from the sealed connection ID:

```python
def propose_vendor_order():
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
    return proposal
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
def publish_close_report():
    from flowglad.commands import command_dag, publish_flowglad_files

    return command_dag(
        publish_flowglad_files(
            changes=[
                {"operation": "write", "path": "close-report.md", "artifact": "close-report"}
            ],
            outputs=[{"path": "close-report.md", "render": "inline_markdown"}],
        ),
        title="Publish close report",
        reasoning_summary="Propose publishing the reviewed close report.",
    )
```

This surface includes `publish_flowglad_files`, `create_flowglad_page`, and
`edit_flowglad_page`, plus the generic runtime-artifact bridge described below.
Organization-scoped publication also includes
`create_flowglad_task` only when the `automation-created-tasks` feature is
enabled for that organization. Generic local compilation remains deterministic
and includes every registry constructor unless the caller supplies an explicit
admitted-static-tag set.

### Publish Application data

Use `publish_application_data` when an Automation should replace an existing
Application's revision-backed `data.json`. The caller supplies only the
selected Application ID and the name of an upstream declared JSON artifact.
Discover the release-pinned constructor through
`flowglad.context.referenceCatalog`, search with `reference.search`, and read
the advertised command and Python SDK resources with `resources.read` instead
of relying on a copied schema. The producer uses the published code-entrypoint
artifact ABI: each `with.fg.produces` declaration binds an `ArtifactOutput`
parameter whose Python name is the declared `as` alias, or the artifact name
with hyphens replaced by underscores when `as` is omitted. Its `write_json`
method is admitted only for an `application/json` declaration. Thus
`revenue-data` below binds the `revenue_data` parameter; it is not an authored
filesystem path.

One Python resource can expose these two entrypoints:

```python
from flowglad.entrypoints import ArtifactOutput, entrypoint


@entrypoint
def build_revenue(revenue_data: ArtifactOutput) -> dict[str, bool]:
    revenue_data.write_json(
        {
            "revenuePanel": {"series": [{"month": "2026-09", "revenue": 125000}]},
            "cashFlowPanel": {"series": [{"month": "2026-09", "net": 82000}]},
        }
    )
    return {"ready": True}


@entrypoint
def publish_revenue() -> object:
    from flowglad.commands import command_dag, publish_application_data

    return command_dag(
        publish_application_data(
            applicationId="app_selected_by_the_user",
            artifact="revenue-data",
        ),
        title="Refresh revenue Application data",
        reasoning_summary="Publish the reviewed revenue artifact.",
    )
```

For this two-panel Application, its `state.schema.json` requires both branches:

```json
{
  "type": "object",
  "properties": {
    "revenuePanel": { "type": "object" },
    "cashFlowPanel": { "type": "object" }
  },
  "required": ["revenuePanel", "cashFlowPanel"],
  "additionalProperties": false
}
```

Declare the producer and terminal consumer in order:

```yaml
do:
  - build-revenue:
      call: code:1.0.0@flowglad
      with:
        fg:
          resource:
            kind: skill-revision
            revisionId: skr_selected_resource
            path: scripts/revenue.py
          entrypoint: build_revenue
          produces:
            - name: revenue-data
              mediaType: application/json
              maxBytes: 1048576
  - publish-revenue:
      call: code:1.0.0@flowglad
      with:
        fg:
          resource:
            kind: skill-revision
            revisionId: skr_selected_resource
            path: scripts/revenue.py
          entrypoint: publish_revenue
          consumes:
            - revenue-data
          terminal:
            kind: command-dag
```

The terminal proposal is effectful, non-reversible, and approval-required by
default; organization approval-rule overrides continue to apply. At execution,
the artifact must be one complete JSON state document for `data.json`, not a
patch or one branch. Flowglad resolves the current Application revision and
validates the entire document against that revision's complete
`state.schema.json`. It retains every code and non-data file, then replaces
`data.json` wholesale when the new revision is promoted. Omitted optional
branches are removed; omitted required branches fail whole-schema validation.
For a two-panel Application, both panels must be present in the same artifact
when its schema requires them. Separate publishers for different panels are
unsafe because each successful command replaces the same complete
`data.json`; later publication would discard any branch it leaves out.
Concurrent revision changes are retried internally at most three times with the
newest schema. Automation code must not supply a revision ID or write an
Application virtual path. Complete MCP code/schema submissions still use
`expectedActiveRevisionId`.

Each distinct successful command creates and activates one revision, even when
the JSON bytes are unchanged. Delivery and lost-response retries retain the
same durable logical command identity and replay the original receipt rather
than creating another revision. A polling timeout means the write outcome is
unknown. Once publication succeeds it remains committed if a later command in
the run fails. Activation does not change private/public visibility; public
sharing remains a separate explicit user action.

The command is available alongside Application authoring, files, and preview.
Application permissions and command approval requirements apply.

`create_flowglad_task` requires `title`, `instructions`, `dueAt`, and a non-empty
`organizationOwnerPrincipalIds` list:

```python
def propose_signed_engagement_letter():
    from flowglad.commands import command_dag, create_flowglad_task

    return command_dag(
        create_flowglad_task(
            title="Upload signed engagement letter",
            instructions="Upload the signed engagement letter for the 2026 engagement.",
            dueAt="2026-09-01T12:00:00-04:00",
            organizationOwnerPrincipalIds=["oprn_customer_owner"],
        ),
        title="Request signed engagement letter",
        reasoning_summary="Assign the customer work to the explicitly selected owner.",
    )
```

The owner list may be a literal or an ordinary value produced by earlier OWS
code or inference dataflow. It must resolve to concrete, distinct organization
owner principal IDs before execution. Do not pass display names, a deferred owner
selection instruction, or omit the list to request implicit member discovery.
An inference that chooses owners must receive a bounded ID/display-name
candidate list through declared OWS input or upstream dataflow. Organization,
Flowglad ownership, status, and automation provenance remain runtime-owned.

Static constructor kwargs become command root fields; Python cannot override
the sealed tag or dependency-envelope fields. OWS publication is
artifact-backed: `publish_flowglad_files` requires `changes`, rejects the
reasoning-only `files` form, and seals `publication_mode="explicit_changes"`.

Helper-command kwargs become command-root fields. Command-family methods expose
their selector explicitly and accept provider payload fields as flattened
kwargs. For example, QuickBooks `create-qbo-entity` becomes
`create_qbo_entity`:

```python
def propose_qbo_expense():
    from flowglad.commands import command_dag
    from flowglad.connections import quickbooks

    return command_dag(
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
  "payload": { "AccountRef": { "value": "42" }, "TotalAmt": 19.95 }
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
Name admitted artifacts on explicit writes and express deletes directly:

```python
def publish_financial_data():
    from flowglad.commands import command_dag, publish_flowglad_files

    publish = publish_flowglad_files(changes=[
        {'operation': 'write', 'path': 'financialData.json', 'artifact': 'financial-data'},
        {'operation': 'delete', 'path': 'oldFinancialData.json'},
    ])
    return command_dag(publish, title='Publish financial data')
```

For compatibility, the generic `command('publish-flowglad-files', changes=...)`
form also fills the same `explicit_changes` discriminator. It rejects `files`;
new code should use the typed constructor.

#### Runtime-generated private artifacts

Use the explicit three-node bridge when file bytes must incorporate fresh
command output. `compose_flowglad_text(parts=[...])` concatenates a non-empty,
ordered mixture of literal strings and scalar predecessor outputs and is
limited to 64 KiB of UTF-8. Each referenced part becomes an indexed DAG data
edge. Composition is only needed for multi-part text; bind a predecessor output
directly to a whole command field when no literal composition is required.

Pass the composed text to
`create_flowglad_artifact(name=..., media_type=..., content_text=...)`, or pass
one complete base64 payload with `content_base64=...`. Exactly one payload is
required. Names are safe basenames, media types are bare MIME types, decoded
bytes are limited to 10 MiB, and creation returns only an opaque artifact ID,
media type, byte count, and SHA-256 digest. The bytes remain private and scoped
to that DAG execution. Secret references cannot target compose parts or either
artifact-content field.

Finally, `publish_flowglad_files(path=..., artifact=...)` is the only operation
that creates an ordinary Flowglad Space file. The artifact must come from the
direct `artifact_id` output of the declared `create_flowglad_artifact` node;
the publisher retains its normal one-file download-URL handoff for a direct
downstream command.

```python
def publish_generated_shortcut():
    from flowglad.commands import (
        command_dag,
        compose_flowglad_text,
        create_flowglad_artifact,
        publish_flowglad_files,
    )

    text = compose_flowglad_text(parts=["[InternetShortcut]\nURL=", share.output.url, "\n"])
    artifact = create_flowglad_artifact(
        name="shared-link.url", media_type="application/internet-shortcut",
        content_text=text.output.text,
    )
    publish = publish_flowglad_files(path="Shared/shared-link.url", artifact=artifact.output.artifact_id)
    return command_dag(text, artifact, publish, title="Publish generated shortcut",
                       reasoning_summary="Compose, store privately, then publish one file.")
```

`command_dag` remains the terminal wrapper. At dispatch, artifact names resolve
only against the authoritative executable run; command execution verifies the
persisted byte length and SHA-256 digest before any Space-file mutation.

### Pinned Custom Connector request proposals

A Custom Connector child is declared explicitly because its request method is
customer-defined rather than part of the static connector command catalog. The
declaration contains only the child connection identity, display metadata, the
strict flat argument schema, and the current semantic definition hash:

```yaml
terminal:
  kind: command-dag
  connections:
    - connectionId: dsrc_custom_crm_create_contact
      as: crm
      connector: custom
      requests:
        - name: create_contact
          title: Create contact
          description: Create one reviewed CRM contact.
          definitionHash: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
          parameterSchema:
            type: object
            additionalProperties: false
            required: [email]
            properties:
              email: { type: string }
```

The declaration never contains a base URL, path, authentication placement,
header, or API key. Python calls the sealed constructor with only the flat
`arguments` object and optional `command_file_name`:

```python
def propose_crm_contact():
    from flowglad.commands import command_dag
    from flowglad.connections import crm

    return command_dag(
        crm.create_contact(arguments={"email": "reviewed@example.com"}),
        title="Create reviewed CRM contact",
        reasoning_summary="Propose one approval-bound Custom Connector request.",
    )
```

The constructor emits `execute-custom-api-request` with compiler-sealed
`connection_id` and `definition_hash`. Publication, activation, run preparation,
and command execution revalidate the organization flag, current child lifecycle,
effective Space visibility, connector identity, and definition hash. Editing a
semantic request field makes an older revision stale. Construction performs no
HTTP and creates no direct host grant; the returned DAG follows the standard
persisted approval policy and makes at most one provider attempt after approval.

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
                  customer_id: { type: string }
                  amount: { type: number }
```

The `as`, `name`, and `operationId` relationship is identical to MCP reads:
the declaration makes `billing.create_invoice` available, while
`invoices.create` remains the pinned admitted catalog identity. The constructor
emits the existing MCP command literal with sealed `connection_id`,
`operation_id`, `catalog_revision_id`, `schema_hash`, and `operation_hash`.

```python
def propose_mcp_invoice():
    from flowglad.commands import command_dag
    from flowglad.connections import billing

    return command_dag(
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
def publish_and_attach_report():
    from flowglad.commands import command_dag, publish_flowglad_files
    from flowglad.connections import gmail

    publish = publish_flowglad_files(
        changes=[{"operation": "write", "path": "report.pdf", "artifact": "report"}]
    )
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
    return proposal
```

The SDK treats the comprehension as a symbolic projection of every published
file's canonical ID and binds that projection to `attachment_file_ids`; the
unresolved target value is not serialized into the draft's `commandData`.
Each symbolic item in `publish.output.flowglad_files` exposes `file_id`,
`storage_path`, `file_name`, and nullable `content_type`. The canonical-ID
projection shown above is the supported collection projection for command
inputs. A publish node that writes exactly one file also exposes the scalar
`publish.output.flowglad_file_download_url`. Bind that field to commands that
need a concrete URL, such as `upload-sharepoint-file-from-url`. Publishes that
write zero or multiple files, perform only deletes, or have no issued presigned
download omit the scalar; use separate one-file publish nodes for multiple URL
uploads until fan-out support is available.
Use `source.output["provider-field"]` when an output field is not a valid
Python attribute name. To select nested provider JSON, use
`source.output["/body/id"]` or `data_edge(source, target,
output_field="/body/id", target_field="draft_id")`. These references stay symbolic
until command execution. Exact own top-level keys take precedence, including
slash-prefixed keys; dotted names remain literal. Otherwise slash-prefixed
selectors use RFC 6901 (`~0` for `~`, `~1` for `/`) with at most 2048 characters
and 32 segments. Arrays require canonical zero-based indices. Empty whole-output
selectors, URI fragments, wildcards, append indices and prototype traversal are
unsupported. The decoded root must be a declared output field. Missing values
fail execution and remain unresolved in approval previews; JSON null is a value.
`ordering_edge` and `data_edge` continue to accept
command declarations directly; use explicit `data_edge` for dotted or indexed
target paths. In every form, source code does not repeat filenames. The
[executor code ABI](CODE_ABI.md) defines the complete
constructor signatures and validation boundary.

Newly compiled constructors carry their authoritative parameter schemas. They
validate literal and dynamic arguments at the Python call boundary and raise a
bounded `TypeError` immediately when the value does not satisfy that schema.
Command output references remain deferred values so `command_dag` can form data
edges, and final DAG validation remains the serialization and semantic backstop.
M1 does not add a mandatory Python checker or the full JSON-Schema-to-Python
type projection; the generated SDK declarations accurately describe the
runtime surface while deeper static projection remains later work.

An automation may be saved as a draft with an empty top-level `do` list. Once
the workflow contains any steps, it must contain exactly one terminal code
task. A code task becomes that terminal task by declaring `with.fg.terminal`. That
declaration enables the task's allowed command constructors and marks its
returned `command_dag(...)` value as an approval proposal. The declaration does
not itself list the command nodes; the task's Python code constructs those nodes
at runtime. The terminal task must be the final task in the top-level `do` list
and cannot declare `if`; it always runs and makes the automation's command
decision.

Verification test cases require only `kind`, `entrypoint`, `input`, and
`expectedSubset`. They may include an optional test-only `terminal` declaration
when the test constructs a command. Its `kind` is `command-dag`; the static
`constructors` array uses the compiler's exact constructor descriptors, with
`method`, `tag`, and `argumentStyle` (and any variant-specific fields). The
isolated verifier exercises the same command-DAG construction path as a
production terminal task without granting the test access to live providers:

```json
{
  "kind": "flowglad-ows-code-test-v1",
  "entrypoint": { "path": "scripts/publish.py", "function": "publish_revenue" },
  "input": {},
  "expectedSubset": {
    "title": "Refresh revenue Application data",
    "nodes": [
      {
        "commandData": {
          "tag": "publish-application-data",
          "applicationId": "app_example",
          "artifact": "revenue-data"
        }
      }
    ]
  },
  "terminal": {
    "kind": "command-dag",
    "constructors": [
      {
        "method": "publish_application_data",
        "tag": "publish-application-data",
        "argumentStyle": "direct"
      }
    ]
  }
}
```

Omit `terminal` for ordinary result-only cases and for empty `command_dag`
results. When a test uses constructors, its declaration must include the exact
descriptors in `terminal.constructors`; malformed or missing declarations
report the `terminal.constructors` field. Where the fixture binding provides
connection aliases, test-only `terminal.connections` entries use `as`,
`connectionId`, and their own `constructors` array, matching the shared
authoring-validation binding shape. These declarations are consumed only by
verification. They do not replace production `with.fg.terminal`, call live
providers, dispatch a command, or create a host capability.

Dashboard-created drafts derive their workflow `input.schema` from the triggers
selected during creation. Preserve that input boundary when adding steps: it is
the contract for the schedule or event payload that starts the workflow.

The terminal task proposes a DAG; it does not execute commands or bypass
approval. A terminal workflow's top-level output must be that exact DAG. If the
task exports the DAG into `$context`, the workflow `output.as` expression must
select it without wrapping it in a report or other business payload. The
proposal is registered only from that successful terminal workflow output;
constructing a DAG in an earlier task, nesting it under another result, printing
it, or returning an ordinary non-DAG mapping does not register a proposal. The
executor compares the validated terminal proposal with the final output and
fails the run when they differ. Put the DAG schema in the standard task and
workflow `output.schema` fields.

Return a nonempty DAG when commands require approval or execution. Return
`command_dag(title=..., reasoning_summary=...)` with no command arguments when
the automation completed successfully and no actions are needed. That empty DAG
is still the validated task and workflow output, but Flowglad does not persist
an approval DAG for it and projects the run as `no_actions_needed`. Omitting or
conditionally skipping the terminal task is invalid; it is not a no-op result.

## Capabilities are derived

Authors do not write requested-capability or capability-ceiling arrays. The
compiler derives the minimum Flowglad sidecar grants mechanically:

- code call → `code.execute`
- inference call → `model.invoke`
- agent call → `agent.execute`
- browser call → one connection-bound `browser.session`
- consumed artifact → `artifact.read`
- produced artifact → `artifact.write`
- authenticated connection action → `authenticated-read.exact`
- declared Page → `page.read.exact`
- declared MCP read → `mcp.read.exact`
- declared Flowglad SDK operation → `flowglad.read`
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

For the intentional Skill-backed path, publish the Skill candidate and
wait for its verification result before publishing the Automation revision.
For pre-publication testing, defer Skill verification, publish the Automation
revision with `development: true`, and invoke it only through explicit Run now.
Schedule and event dispatches check the sealed dependency closure and
reject any Skill revision that is not `active` or `superseded`. Automation
publication derives the exact Skill manifest digest internally.
Compatibility-only Space resources remain
live between runs; publication checks access, and run preparation snapshots
their then-current bytes and source version once for the run. An identical plan
is idempotent. Publishing a later non-private revision does not implicitly activate it;
activation fails closed unless the matching executor
version is available and the persisted bundle, closure, and digests match
exactly. Runtime routing is a separate, default-off feature-gated decision.

Private publication persists one exact lifecycle-backed selection without changing
workflow activation or enabled state. Missing or mismatched persisted selections
fail closed; no adapter makes historical private workflows executable. Save-only
and read-only validation do not activate revisions. Deactivation remains available
when runtime support is unavailable.

### Revise, activate, then run

This explicit activation procedure applies to every package owner, including
Automation-private revisions.

`automations.create` creates revision 1 without activating it, including when
the definition contains executable steps. An empty `do` list likewise creates
an inactive draft revision and cannot be activated until a later revision adds
valid steps. New automations are persisted with `enabled: false` and a null
`activeExecutableSchemaRevisionId` by the current explicit lifecycle contract.
Activate a compiled revision in a separate operation, then use the
activation/update contract when enabling or disabling execution. Revision
creation and activation are also separate operations for later edits:

1. Call `automations.get`. Without `revisionId`, its `revision` field is the
   latest immutable revision, which may not be active. Treat
   `automation.activeExecutableSchemaRevisionId` as the authoritative executable
   pointer and retain both IDs.
2. Call `automations.update` with `operation: "revise"`,
   `baseRevisionId: revision.id`, and the new definition. This publishes a new
   immutable revision but does not activate it.
3. Call `automations.update` with `operation: "activate"`,
   `desiredRevisionId` set to the newly returned `revision.id`, and
   `expectedActiveRevisionId` set to the active pointer observed in step 1 (not
   automatically to the latest `revision.id`). Supply a stable
   `idempotencyKey` for retries.
4. Call `automations.run`. In run history, `executableRevisionId` is the ground
   truth for the revision that run used; compare it with the intended revision
   instead of assuming the latest revision executed.

Saving a newer uncompiled revision does not change the Automation's enabled
state, replace its active compiled revision, or reconcile that active
revision's event and schedule projections. An enabled Automation therefore
continues dispatching through its older active compiled revision while the
latest uncompiled revision remains non-executable and awaits setup. A paused
Automation remains paused. Do not attempt to activate or run the uncompiled
revision.

If another actor changes the active pointer between steps 1 and 3, activation
fails its optimistic-concurrency check. Fetch current state and reconcile the
revision choice before retrying; do not overwrite the newer activation blindly.

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

### Debugging failed runs

Start with `automations.get_run_history`. For a failed or timed-out executor
run, `terminalError` contains the bounded terminal executor error message. A
code-process failure includes its descriptive exception message when the
executor can recover one, so raise a specific exception that identifies the
failed operation and safe diagnostic context.

Current outcome retention is intentionally asymmetric:

- After a successful executor result, a non-null workflow output is retained as
  `terminalOutput`, and declared produced artifacts are validated, uploaded, and
  recorded before the run settles.
- Failed, timed-out, and cancelled executor results do not retain workflow
  output and do not publish produced artifacts. Do not use a failed-run artifact
  as a diagnostics channel.
- The current MCP run-history surface does not expose the bounded stderr event
  stream, full traceback/step trace, or failed-run output and artifact contents.
  Put the decisive, non-secret explanation in the raised exception rather than
  relying on printed stderr.

Run history has two status layers. `status` is the executor-owned program state:
`pending`, `running`, `succeeded`, `failed`, `timed_out`, or `cancelled`.
`runStatus` is the composite lifecycle state derived across program execution,
command-DAG registration and approval, and command execution. For example, an
executor `status` of `succeeded` can pair with `runStatus: no_actions_needed`
when no command DAG was registered, or with `awaiting_approval`, `executing`, or
a later command-execution outcome after a DAG was registered. Use `status` to
diagnose the OWS executor and `runStatus` to decide what should happen next.

### Retained post-run telemetry over MCP

For interactive Automation and Skill development, inspect the execution
transcript immediately after a terminal run:

1. Call `automations.get_run_telemetry` with the exact `runId` returned by
   `automations.run`; the run identifies its parent Automation. If it returns
   `state: processing`, poll the same read until it becomes `available`,
   `expired`, or `unavailable`.
2. When available, download the archive before `logicalExpiresAt`. Telemetry is
   logically retained for 30 days after run completion, and each returned
   download URL is valid for at most five minutes. Request a fresh URL while
   the archive remains logically available instead of persisting the signed
   URL.
3. Verify `archiveDigest`, then inspect `manifest.json` and `execution.json`.
   Verify each manifest member digest before trusting its contents. The
   transcript records ordered lifecycle and task evidence plus the permitted
   code, inference, and browser diagnostics captured for that run.
4. Check the redaction, omission, and truncation counts in both the MCP response
   and archive markers before concluding that evidence is complete. Telemetry
   is intentionally diagnostic and may omit or redact sensitive data; never
   design a workflow or Skill that depends on telemetry as an execution data
   channel.

Python SDK telemetry is automatic and does not require authored logging calls
or workflow options. The V3 transcript records every installed public SDK
binding and pairs each invoked SDK operation with started and terminal records.
Cross-host reads retain only bounded request/evidence correlation identity;
arguments, response and Page bodies, artifact contents, credentials, and
exception messages are excluded. A bounded `sdk.logs.dropped` evidence entry
reports transport, validation, or task-budget loss. These diagnostics never
change the Python result, artifact bytes, command/DAG values, stdout bytes, or
exception type/message.

Use the transcript to identify the failed task and attempt, compare the run's
plan/runtime digests with the intended active revision, and inspect safe
stdout/stderr or model/browser evidence. Keep `terminalError` as the primary
bounded failure summary: telemetry supplements run history but does not change
the run outcome or recover unpublished failed-run artifacts.

## Complete examples

- [Invoice reconciliation: exact ledger read → evidence artifacts → command DAG](invoice-reconciliation.ows.yaml)
- [Yooz: code → inference → code](yooz-bounded-document-number.ows.yaml)
- [Workspace agent: bounded review and authenticated reads → command DAG](agent-review.ows.yaml)
- [Browser statement: browser agent → PDF artifact → code](mock-bank-browser-statement.ows.yaml)
- [TODO Page: exact Page read → edit command DAG](page-todo-update.ows.yaml)
- [MCP: pinned admitted read → pinned command DAG](mcp-ows-v1.ows.yaml)

The examples are validated with the official OWS 1.0.3 schema and the Flowglad
compiler and generate the standalone executor's committed canonical bundles.
Their `skr_example_...` values identify fixture Skill revisions; replace them
with exact sealed revision IDs returned by the Skill lifecycle when adapting
an example for a real Automation. The corresponding Python paths are package
members under `scripts/`, not loose Automation files.
The invoice-reconciliation example exercises task injection, scoped connection
actions, artifact production and consumption, and command-DAG edges through a
complete accounts-payable operation in the standalone CLI test harness.

### M1 boundary

M1 provides compiler, executor, and host support for the pinned
MCP declarations above. Public `ows_authoring.list_connection_capabilities`
and `ows_authoring.get_connection_capability` are Milestone 2 tools and must
not be added by M1.

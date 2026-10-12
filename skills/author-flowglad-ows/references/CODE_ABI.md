# Flowglad OWS profile v1 code ABI

> Generated from `flowglad/provisioning-agent@8267a6c9cdcd190993a413db554395b76708d7a0` (`packages/workflow-executor/CODE_ABI.md`). Do not edit this exported file directly.

This is the author contract for `code:1.0.0@flowglad`. Each task declares one
public top-level function in a sealed Python 3.11 resource. The executor imports
the resource in an argv-based child with empty stdin and invokes the function
selected by the OWS task. The selected runtime callable must be synchronous and
zero-argument. It may be a plain zero-argument function or the zero-argument
wrapper produced when `@entrypoint` binds an N-arity source function's injected
dependencies. The return value is the direct OWS task value. The process uses
`/workspace` as its working directory and does not invoke a shell.

## Minimal program

<!-- minimal-example:start -->
```python
from flowglad.entrypoints import Input, entrypoint


@entrypoint
def reconcile_invoice(invoice_id: Input) -> dict[str, str]:
    return {"invoice_id": invoice_id}
```
<!-- minimal-example:end -->

The task extension names the function:

```yaml
entrypoint: reconcile_invoice
```

An entrypoint name contains only ASCII letters, digits, and underscores, starts
with a letter, and identifies a synchronous function defined at module scope.
There are two admitted declaration forms:

- A plain function declares no parameters and is invoked directly.
- An N-arity function uses `@entrypoint` from `flowglad.entrypoints`; the
  decorator has no parentheses and directly precedes the `def` declaration.
  Every parameter has one supported dependency annotation and has no default.
  Positional-only, keyword-only, variadic, and unannotated parameters are
  invalid.

For an injected source function returning `R`, `@entrypoint` has the callable
shape `Callable[P, R] -> Callable[[], R]`: it preserves the selected function's
name and returns the zero-argument wrapper that the launcher invokes. Write
`@entrypoint`, never `@entrypoint()`.

The trusted launcher requires either form to resolve to a zero-argument runtime
function and serializes its return to the bounded stdout process channel.
Author code does not print a result.

`flowglad.entrypoints` exports these dependency markers:

| Marker | Injected value |
| --- | --- |
| `Input` | The required `task_input` object field whose key matches the parameter name. |
| `TaskInput` | The complete admitted task input JSON value. An entrypoint declares this marker at most once. |
| `ArtifactInput` | The consumed artifact object whose local alias matches the parameter name. |
| `ArtifactCollectionInput` | The consumed immutable artifact collection whose local alias matches the parameter name. |
| `ArtifactOutput` | The produced artifact object whose local alias matches the parameter name. |

Publication reads the exact pinned source bytes without importing the module.
It verifies the OWS-selected public declaration. A plain declaration must have
zero parameters. A decorated declaration may have injected parameters and must
match the task's `consumes` and `produces` artifact aliases exactly. The runtime
repeats the decorated artifact check and reports missing task-input fields with
the available admitted keys. The workflow remains the capability authority;
the decorator only asserts and binds its selected function's dependencies.

The return is not a `continue`, `bail`, status, or version envelope. The executor
requires exit status zero and rejects non-JSON-compatible values, non-finite
numbers, unsolicited stdout, invalid JSON, multiple values, and values that fail
the task's OWS output schema.

## Runtime values

Every code task also installs the task-scoped `flowglad.runtime` module. It
provides task metadata and the complete input for code that needs it outside an
entrypoint parameter:

```python
from flowglad.runtime import task_id, task_input
```

| Name | Meaning |
| --- | --- |
| `task_id` | The current OWS task name. |
| `task_input` | The complete JSON value produced by the task's OWS `input` semantics. |

The executor constructs these values from the admitted task state and transports
them through an immutable internal manifest. The runtime module owns manifest
file access and JSON decoding. Resource code does not read executor environment
variables or manifest files. Declared OWS JSON schemas own task-value
validation, and artifact declarations own slot shape, containment, size, media
type, and digest validation. Resource code validates only business constraints
that those declarations do not express.

### Validation responsibility

| Executor owns | Resource code owns |
| --- | --- |
| Runtime-module construction and the admitted task state behind every exported value. | The declared entrypoint function and its task-specific behavior. |
| Task input and function-return shapes against their declared OWS schemas. | Semantic and cross-field invariants that the schemas do not express, such as an exact match count or a required relationship between values. |
| Consumed and produced artifact containment, media type, size, digest, declaration, and completeness. | Domain meaning inside artifact content when that meaning matters to the workflow. |
| Connection/action, Page, and pinned MCP-read admission; declared result schemas; and call/byte/time budgets. | Which admitted read to call and whether its result is meaningful, consistent, complete, and unambiguous for the business operation. |
| MCP command literal identity (`connection_id`, `operation_id`, catalog/schema/operation hashes) and terminal-DAG validation. | The MCP command `arguments` object and the business reason to propose it. |
| Function-return serialization, strict JSON stdout, exit status, process bounds, timeout/cancellation, and declared terminal command-DAG structure. | The returned business value and the decision to raise when a business invariant does not hold. |

Resource code does not repeat runtime-module shape checks, rebind connection
aliases to connection IDs, or recalculate artifact integrity metadata. It puts
structural constraints in the workflow schemas and uses explicit code checks
only for the remaining semantic constraints.

## Structured SDK telemetry

The executor automatically audits the task-scoped Python SDK. Authors do not
initialize a logger, add decorators, pass telemetry options, or change valid
code. Each installed public binding emits one `sdk.object.bound` record, and
each public SDK operation emits `sdk.operation.started` followed by exactly one
`sdk.operation.succeeded` or `sdk.operation.failed` record. The executor, not
the child, supplies run, invocation, task, and attempt identity.

Records contain only the SDK module, object kind, public name, operation,
phase, severity, status, duration, result type, bounded error class/code, and
an operation-specific allowlist. That allowlist may include declared or
observed counts and byte bounds, media type, already-exposed digests, pinned MCP
schema/operation hashes, and request/evidence correlation identity. Request
arguments, response and Page bodies, artifact contents, paths, credentials,
tokens, arbitrary metadata maps, and exception messages are never SDK-log
attributes.

The SDK writes message-framed records to a non-blocking Unix datagram channel,
not stdout or stderr. Each record is at most 16 KiB; one task admits at most
4,096 records and 1 MiB of record bytes. Serialization, oversize, task-budget,
closed-channel, and backpressure loss cannot fail an SDK call. The executor
aggregates transport and validation loss into one bounded
`sdk.logs.dropped` task-evidence record. Runs containing accepted SDK records
use the V3 execution transcript; historical V2 archives remain readable.

## Artifacts

Standard OWS input, output, and export fields carry JSON values between tasks.
Flowglad artifacts carry files that require separate persistence or integrity
metadata. An entrypoint declares each local artifact alias as a parameter:

```python
from flowglad.entrypoints import ArtifactInput, ArtifactOutput, entrypoint


@entrypoint
def normalize(
    invoice_pdf: ArtifactInput,
    normalized_context: ArtifactOutput,
) -> dict[str, int]:
    invoice_bytes = invoice_pdf.read_bytes()
    normalized_context.write_json({"size": len(invoice_bytes)})
    return {"size": len(invoice_bytes)}
```

The task-scoped `flowglad.artifacts` module exposes the same admitted objects
for direct inspection outside entrypoint binding.

Consumed artifact objects expose `path`, `media_type`, `size_bytes`, `digest`,
`open()`, `read_bytes()`, `read_text()`, and `read_json()`. Produced artifact
objects expose `path`, `media_type`, `max_bytes`, `open()`, `write_bytes()`,
`write_text()`, and `write_json()`. JSON helpers require
`application/json`; text helpers use UTF-8. An input has no write methods, and
an output has no read methods. `path` is available for APIs that require a path,
but ordinary reads and writes use the object methods.

Every artifact `path` property is a `pathlib.Path`, including an immutable
collection member's `path`. Keep it as a `Path` for path operations such as
`path.name`. Input artifacts and collection members open in binary read mode
(`"rb"`) by default and accept text read mode (`"r"`); outputs open in binary
write mode (`"wb"`) by default and accept `"w"`, `"x"`, and `"xb"`. Text modes
return a text stream and binary modes return a binary stream. `write_bytes`,
`write_text`, and `write_json` return the number of bytes written, not `None`.

Convert a path explicitly only at a JSON string boundary. For example, if a
sealed command's `attachment_file_ids` field accepts the staged artifact path
as a JSON string, make that boundary visible in the call:

```python
attachment_file_ids = [str(member.path) for member in receipts]
```

Do not convert paths before ordinary artifact operations; `member.read_bytes()`
and `member.path.name` retain the richer `Path` value.

An invocation artifact collection uses the additive `ArtifactCollectionInput`
marker. It does not change `ArtifactInput`:

```python
from flowglad.entrypoints import ArtifactCollectionInput, entrypoint


@entrypoint
def inspect(receipts: ArtifactCollectionInput) -> dict[str, object]:
    return {
        "count": len(receipts),
        "names": [member.file_name for member in receipts],
    }
```

The collection is immutable, supports `len()`, iteration, and integer indexing,
and preserves ascending source ordinal. A valid collection may be empty. Each
immutable member exposes `ordinal`, `file_name`, `path`, `media_type`,
`size_bytes`, `digest`, `open()`, `read_bytes()`, `read_text()`, and
`read_json()`. Member paths are deterministic and read-only:
`/in/invocation-artifacts/<collection>/<zero-padded-ordinal>-<safe-filename>`.
The runtime verifies every member's size and SHA-256 digest before binding it and
again after untrusted code exits.

On exit, every declared output is required and is checked for containment,
type, and size; the executor computes and records its actual SHA-256 digest.
An undeclared file in the task's artifact output directory
fails admission. Scratch files elsewhere are not published.

## Command DAG construction

Every code task installs the pure `flowglad.commands` construction module. Its
core helpers return ordinary JSON-compatible dictionaries and do not grant
terminal authority. A task with a compiler-sealed `terminal` declaration also
receives one standalone function for every static non-connector command node.
The task's `terminal` declaration and output schema still determine whether the
executor accepts a command DAG proposal.

The sealed SDK is exhaustive for the command node types available to that
terminal task:

| Available node type | Author-facing constructor |
| --- | --- |
| Static non-connector command | Standalone `flowglad.commands.<tag_as_snake_case>(**fields)` |
| Connector-provided command | `flowglad.connections.<alias>.<tag_as_snake_case>(**fields)` |
| Untyped browser order | `flowglad.connections.<alias>.order(**order_fields)` |

Static constructors require terminal authority. Connection methods also
require the compiler-sealed connection declaration. Every synthetic constructor
seals its tag, and connection-bound constructors additionally seal
`connection_id`; author code supplies only command payload fields.

Import sealed constructors and `flowglad.connections` aliases inside the
selected zero-argument function. The verifier imports Skill modules before it
invokes that function, while constructor and alias bindings exist only for a
task with the matching sealed `terminal` declaration. Terminal connection
aliases grant command construction only. Exact authenticated reads still
require `exactAuthentication`; pinned MCP reads require `kind: mcp` actions under `exactAuthentication`.

<!-- static-command-constructor-example:start -->
```python
def propose_files():
    from flowglad.commands import command_dag, publish_flowglad_files

    published = publish_flowglad_files(
        changes=[{"operation": "write", "path": "close-report.md", "artifact": "close-report"}],
        outputs=[{"path": "close-report.md", "render": "inline_markdown"}],
    )
    return command_dag(
        published,
        title="Publish close report",
        reasoning_summary="Propose publishing the reviewed close report.",
    )
```
<!-- static-command-constructor-example:end -->

The compiler derives `publish_flowglad_files`, `create_flowglad_page`, and
`edit_flowglad_page` from the shared static command registry. It also derives
`create_flowglad_task` when that static tag was admitted for the compiled
organization; organization publication admits it only while the
`automation-created-tasks` feature is enabled.

`create_flowglad_task` requires `title`, `instructions`, `dueAt`, and
`organizationOwnerPrincipalIds`. The owner argument must be a non-empty Python
list or an ordinary upstream OWS value that resolves to a non-empty list. The
terminal command accepts concrete, distinct organization owner principal IDs only—not display
names, deferred owner-selection instructions, or implicit member enumeration.
An inference chooser must receive a bounded ID/display-name candidate list via
declared input or upstream dataflow.

```python
def propose_signed_engagement_letter():
    from flowglad.commands import command_dag, create_flowglad_task

    task = create_flowglad_task(
        title="Upload signed engagement letter",
        instructions="Upload the signed engagement letter for the 2026 engagement.",
        dueAt="2026-09-01T12:00:00-04:00",
        organizationOwnerPrincipalIds=["oprn_customer_owner"],
    )
    return command_dag(
        task,
        title="Request signed engagement letter",
        reasoning_summary="Assign the customer work to the explicitly selected owner.",
    )
```

Every direct constructor accepts command payload fields as kwargs, seals the
tag, and rejects `connection_id`, `data_source_id`, `dependsOn`, `outputRefs`,
and `secretRefs`. `command_file_name` overrides the generated JSON basename
without consuming an ordinary payload field named `file_name`.
`publish_flowglad_files` additionally requires artifact-backed `changes`,
rejects the reasoning-only `files` form, and seals
`publication_mode="explicit_changes"`.

`command(tag, data=None, *, file_name=None, **fields)` creates one immutable
command declaration as a low-level compatibility escape hatch for legacy or
custom tags that have no generated constructor. Do not use it to hand-author an
available static, connector, or browser-order node. Keyword fields become
`commandData` fields. The optional mapping form supports field names that are
not Python identifiers or that match helper parameter names. The default
filename is `<tag>.json`; `file_name` supplies a different JSON basename.
For compatibility, the generic `command('publish-flowglad-files', changes=...)`
form fills the same discriminator, while rejecting `files`.

`command_dag(*commands, title, reasoning_summary, edges=())` assigns
zero-based positions in argument order and returns the complete terminal value.
The executor associates the proposal with its authoritative workflow run; the
script does not supply runtime identity. Passing no commands returns an empty
DAG (`nodes: []`, `edges: []`), which is the explicit successful
`no_actions_needed` decision. Every automation still executes exactly one final,
unconditional terminal code task; missing or skipped terminal execution is a
failure, not the empty-DAG representation.

Every command constructor returns a declaration with an immutable `output`
reference namespace, rather than an executed provider result. Pass a prior
command's output field directly as a later command's top-level input to infer
the data edge without repeating either command filename or the output field as
a string:

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
    return command_dag(
        publish,
        draft,
        title="Publish and attach report",
        reasoning_summary="Attach the newly published report.",
    )
```

For `publish_flowglad_files`, the SDK exposes the structured `flowglad_files`
collection rather than the executor's internal canonical-ID projection. The
shown comprehension is symbolic: `command_dag` lowers it to the canonical ID
array, omits the unresolved target field from `commandData`, and emits a data
edge from `publish-flowglad-files.json` to the draft's `attachment_file_ids`
field. Each symbolic file exposes `file_id`, `storage_path`, `file_name`, and
nullable `content_type`; the canonical-ID projection shown above is the
supported collection projection for command inputs. Output fields that are not
valid Python attribute names can use item access, such as
`source.output["provider-field"]`.
`ordering_edge(source, target)` expresses execution order. `data_edge(source,
target, output_field=..., target_field=...)` also binds a source result field to
a target input field; keep this explicit form for dotted or indexed target
paths. Edges reference command declarations directly, so author code does not
repeat generated filenames.

For every newly sealed constructor with a parameter schema, literal and dynamic
arguments are validated immediately when the constructor is called. An invalid
value raises a bounded `TypeError` at that call site; deferred command-output
references remain available for `command_dag` to lower into data edges. Final
terminal-DAG validation still protects serialization and workflow semantics.
This is runtime contract validation, not a mandatory Python type-checking gate.

The helpers enforce their construction invariants, including unique filenames,
and forward-only edges. The executor remains the authority for the task output
schema, terminal DAG schema, command schemas, and approval boundary.

### Connection-bound connector proposals

A terminal connection declaration installs its immutable alias in
`flowglad.connections` without granting an authenticated read or creating a
host bridge. The compiler seals one pure Python constructor method for every
command node declared by that connector. A command tag maps to its method name
by replacing hyphens with underscores, such as `send-slack-message` →
`send_slack_message`.

Helper-command kwargs become command-root fields:

```python
def propose_message():
    from flowglad.commands import command_dag
    from flowglad.connections import slack

    message = slack.send_slack_message(
        channel_id="C012345",
        text="The reconciliation is ready for review.",
    )
    return command_dag(
        message,
        title="Send reconciliation notice",
        reasoning_summary="Propose one reviewed Slack message.",
    )
```

Command-family methods keep their selector at the command root and accept the
provider payload as flattened kwargs. The SDK nests those kwargs under the
connector-declared payload field:

<!-- quickbooks-constructor-example:start -->
```python
def propose_expense():
    from flowglad.commands import command_dag
    from flowglad.connections import quickbooks

    expense = quickbooks.create_qbo_entity(
        object_kind="expense",
        AccountRef={"value": "42"},
        TotalAmt=19.95,
    )
    return command_dag(
        expense,
        title="Create QuickBooks expense",
        reasoning_summary="Propose one reviewed expense.",
    )
```
<!-- quickbooks-constructor-example:end -->

`create_qbo_entity(*, object_kind, command_file_name=None, **business_fields)`
emits exactly this `commandData`:

```json
{
  "tag": "create-qbo-entity",
  "connection_id": "dsrc_documented_qbo",
  "object_kind": "expense",
  "payload": {"AccountRef": {"value": "42"}, "TotalAmt": 19.95}
}
```

`object_kind` is the required root selector. Every other business keyword is
nested under `payload`, except connector-declared root fields such as QBO's
optional `target` mapping overlay. Helper-command methods keep every supplied
command field at the root. `command_file_name` overrides the generated JSON
basename when a DAG contains multiple nodes with the same tag; a business field
named `file_name` remains an ordinary command kwarg. Callers cannot supply
`tag`, `connection_id`, `data_source_id`, `dependsOn`, `outputRefs`, or
`secretRefs`; those command-envelope fields are rejected rather than
overridden. Construction is pure: it proposes an approval-bound command and
never dispatches a provider operation.

### Pinned MCP reads and command proposals

`exactAuthentication` installs the pinned `kind: mcp` read methods declared for a connection
alias. A read always takes one keyword-only JSON object, and the executor sends
the generated `exact-read.request` host frame before accepting only the matching
`exact-read.response` result:

<!-- mcp-read-command-example:start -->
```python
def propose_mcp_invoice():
    from flowglad.commands import command_dag
    from flowglad.connections import billing

    invoices = billing.list_invoices(arguments={"limit": 10})
    if not invoices["structuredContent"]["items"]:
        raise ValueError("The pinned MCP read returned no invoices")
    invoice = billing.create_invoice(arguments={"customer_id": "cus_reviewed", "amount": 19.95})
    return command_dag(
        invoice,
        title="Create reviewed invoice",
        reasoning_summary="Use a pinned MCP read before proposing a pinned command.",
    )
```
<!-- mcp-read-command-example:end -->

The corresponding terminal constructor emits exactly this command-data shape;
the five identity fields are copied from the compiler-sealed declaration rather
than accepted from Python:

```json
{
  "tag": "mcp-command-invoices-create-77bb32c75d4c",
  "connection_id": "dsrc_billing",
  "operation_id": "invoices.create",
  "catalog_revision_id": "mcrv_billing_v1",
  "schema_hash": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "operation_hash": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "arguments": {"customer_id": "cus_reviewed", "amount": 19.95}
}
```

Both MCP reads and MCP command constructors require `arguments={...}`.

Custom Connector terminal constructors use the same arguments-only call shape:
`method(arguments={...}, command_file_name=...)`. The compiler owns the fixed
`execute-custom-api-request` tag and seals `connection_id` plus
`definition_hash`; supervised Python cannot supply or override those fields.
The constructor is pure and returns an ordinary command declaration for the
generic terminal command-DAG path. It receives no URL, auth placement, header,
credential, direct HTTP client, or host grant.
Flattened kwargs are rejected, as are attempts to provide the reserved command
envelope or pinned fields. For commands, `command_file_name` is the only other
accepted keyword. The read bridge validates declared input and optional output
schemas, budgets the result, and rechecks active catalog revision, schema hash,
operation hash, admission, and connection identity before provider I/O.

### Untyped browser-order proposals

An Untyped terminal connection exposes one dynamic `order` constructor. The
compiler seals the typed tag from the connection ID and the SDK seals the same
ID into `connection_id`.

<!-- untyped-browser-order-example:start -->
```python
def propose_browser_order():
    from flowglad.commands import command_dag
    from flowglad.connections import vendor_portal

    browser_order = vendor_portal.order(
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
    )
    return command_dag(
        browser_order,
        title="Submit vendor invoice",
        reasoning_summary="Propose reviewed browser work on the selected portal.",
    )
```
<!-- untyped-browser-order-example:end -->

For `connectionId: dsrc_browser_portal`, `order(...)` emits
`tag: "order_dsrc_browser_portal"` and
`connection_id: "dsrc_browser_portal"`. Callers cannot override either field.
The remaining typed browser-order DSL fields stay at the command root.
`login_account_id` is supplied only when the admitted connection requires the
exact configured login account; connections backed by an active browser session
without a required login account omit it. The downstream typed command schema
enforces that conditional identity rule.

## Flowglad resource reads

### Repository-free fixture validation

The MCP unpublished-authoring validator loads code through this real Python SDK
and zero-argument entrypoint ABI. It supplies explicit synthetic fixtures and
compiler-derived terminal bindings, has no credentials or live SDK host calls,
and performs zero product writes. Passing proves syntax, types, fixture
behavior, admission, and infrastructure only—not provider connectivity or
publication.

The complete callable surface is generated from the runtime into the pinned
public `sdk/python/manifest.json` and `.pyi` resources. Repository-free authors
read those exact resources instead of inferring symbols from examples or this
prose. Include success and alternate/failure cases and compare emitted terminal
DAGs with independent expectations.

A code task whose sealed `flowgladAccess.operations` declaration names
`spaces.list.v1` receives the corresponding unversioned, task-scoped method at
`flowglad.resources.spaces.list`. Import the resource module and call its
methods with keyword arguments:

<!-- resource-sdk-example:start -->
```python
from flowglad.resources import spaces


def list_visible_spaces():
    page = spaces.list(limit=50)
    items = list(page["items"])
    while page["nextCursor"] is not None:
        page = spaces.list(limit=50, cursor=page["nextCursor"])
        items.extend(page["items"])
    return {"items": items, "nextCursor": page["nextCursor"]}
```
<!-- resource-sdk-example:end -->

Every collection operation returns the same `{ "items": [], "nextCursor":
null }` envelope. A cursor is opaque: pass it back unchanged to the same method
and filter set. It is bound to the exact operation, Automation owner, resolved
target Space, and normalized filters; changing any of those inputs raises
`invalid_cursor`. Pagination is live rather than snapshot-based, so Page
deletion, link removal, and member eligibility changes apply to the next call.
A `get` operation returns its resource dictionary directly:

```python
from flowglad.resources import spaces

space = spaces.get(space_id="spc_123")
print(space["spaceId"], space["name"])
```

The complete Page and member surface is registry-derived; no Python method list
is maintained separately:

```python
from flowglad.resources import pages
from flowglad.resources.pages import revisions
from flowglad.resources.spaces import members

page = pages.list(limit=25)
matches = pages.search(query="forecast", space_id="spc_123")
semantic_matches = pages.semantic_search(query="cash runway", top_k=10)
metadata = pages.get(page_id="page_123")
content = pages.get_content(page_id="page_123")
revision_page = revisions.list(page_id="page_123", limit=25)
revision = revisions.get(revision_id="prev_123")
principals = members.list(space_id="spc_123")
```

The file surface is a distinct registry-derived namespace:

```python
from flowglad.resources import files

finance = files.list(space_id="spc_123", path_prefix="Finance", limit=20)
matches = files.search(query="quarterly", space_id="spc_123", path_prefix="Reports")
semantic_matches = files.semantic_search(
    query="cash runway",
    space_id="spc_123",
    path_prefix="Finance",
    top_k=10,
)
metadata = files.get(file_id="file_123", space_id="spc_123")
rendition = files.get_text(file_id="file_123", space_id="spc_123", max_chars=24_000)
```

Normal SDK failures raise the public error type:

```python
from flowglad.errors import FlowgladError

try:
    space = spaces.get(space_id="spc_123")
except FlowgladError as error:
    print(error.code, error.message, error.details)
```

`FlowgladError` is also re-exported from `flowglad.resources`. Its `details`
mapping is immutable. The five stable public codes are `invalid_argument`,
`not_found`, `permission_denied`, `invalid_cursor`, and `budget_exhausted`.
A `budget_exhausted` error names the exhausted call, response-byte,
cumulative-byte, or wall-time budget in `details["budget"]`.

Each call crosses the private host bridge as one
`flowglad-resource.request` / `flowglad-resource.response` pair. The workflow
declaration remains the capability authority: the generated module exposes
exactly its declared operations. An undeclared operation is a program error,
not a runtime denial, and its method is absent. Without a `flowgladAccess`
declaration, the executor installs no `flowglad.resources` package;
`flowglad.errors` remains importable so shared task code can catch
`FlowgladError` when a declaration is present.

The current actor is checked when a revision activates. Runtime authorization
then uses the sealed operation grant and durable Automation organization and
owner-Space scope. It never depends on the creator's current account,
membership, or permissions, nor on a manual-run or dispatch identity, and it
does not evaluate a feature flag.

Every file call accepts an optional `space_id`. Omission searches the durable
Automation owner's current forward-visible Space closure; one owner, direct-child,
or transitive-descendant ID narrows to exactly that Space. Unreachable,
reverse-only, and deleted targets raise `not_found` before file or vector I/O.
`files.list`, `files.search`, and `files.semantic_search` accept an optional
Space-visible `path_prefix`; `/` means the root and prefixes match complete path
segments independently in every selected Space. List and lexical search return
metadata descriptors only, including the exact owner `spaceId`, and never file
bodies or storage keys. `files.get` returns one descriptor, while
`files.get_text` explicitly returns the shared direct-text, PDF, Excel, or
binary-fallback rendition. Bounded text reports `truncated` structurally without
an inline marker; binary data is not shortened. Missing, stale, excluded,
folder-marker, cross-Space, and otherwise inaccessible files all raise
`not_found`.

`files.semantic_search(query, space_id=None, path_prefix=None, top_k=10)` is
non-paginated. It returns camelCase `{matches, coverage}`. Each match combines a
current authorized descriptor with `score`, a snippet bounded to 280 characters,
`chunkIndex`, and `chunkCount`. Coverage contains `indexState` (`ready`,
`empty_or_building`, `stale`, or `unavailable`), `partial`, and
`candidateWindowTruncated`; a truncated candidate window always sets `partial`.
Known embedding or vector failures return empty `unavailable` coverage. The
result never exposes indexed timestamps, provenance tokens, per-match indexing
truncation, filtered identities, or rejected-candidate counts.

For Page list/search, omitted `space_id` means the owner's current forward
visible closure. For `spaces.members.list`, omission means the owner Space
only. One supplied `space_id` narrows within the same forward closure; arrays
are invalid. Page get/get_content map absent, deleted, foreign, and invisible
IDs uniformly to `not_found`. Member records contain only `principalId`,
`userId`, `displayName`, `email`, and these tagged `accessSources` variants:
`direct_space_membership` with `role`, `linked_space_membership` with
`sourceSpaceId` and `role`, or `organization_role` with `role`. Internal
membership/role IDs and effective permissions never cross the bridge.

`pages.semantic_search(query, top_k=10)` is discovery-only and non-paginated.
`query` is trimmed and bounded to 1,000 characters; `top_k` is between 1 and
25. It returns `{ "matches": [...] }`, with at most `top_k` currently visible
Pages ranked by the best indexed chunk. Each match contains current `pageId`,
`spaceId`, `spaceName`, `title`, `description`, `createdAt`, and `updatedAt`
metadata plus bounded `score`, `snippet`, `chunkIndex`, `chunkCount`, and
`indexedAt` discovery fields. Results never contain a Page body,
`pageRevisionId`, `contentHash`, vector data, or a continuation cursor. Use
`pages.get_content` for an explicit current-content read after discovery.

The declared revision calls are
`flowglad.resources.pages.revisions.list(...)` and
`flowglad.resources.pages.revisions.get(...)`. Revision list requires
`page_id`, accepts the standard bounded `limit` and opaque `cursor`, and
returns durable content-edit revisions newest first by `createdAt` and then `revisionId`.
Each list item contains only `revisionId`, `revisionKind`, and `createdAt`.
The cursor is additionally bound to its parent Page, so it cannot be replayed
against another Page. Revision get accepts only `revision_id` and returns
exactly `revisionId`, `pageId`, `revisionKind`, `createdAt`, and a non-null
`diff`. Absent and invisible revisions and parent Pages all raise the same
`not_found` error.

Revision kinds are `user_edit` and `automation_edit`. A revision `diff` contains `changed`, exact lowercase
SHA-256 `oldTextSha256` and `newTextSha256` values, complete `addedLines` and
`removedLines` counts, unified-compatible `hunks`, and `truncated`. Hunk lines
are tagged only `unchanged`, `added`, or `removed`; their `text` omits marker
prefixes and preserves the exact stored line terminator, including CRLF and a
missing final newline. The result retains only whole hunks within 1,000
logical lines and 256 KiB of UTF-8 line text. `truncated` is true exactly when
a complete hunk was omitted. There is no historical-body or arbitrary revision-comparison method.

Successful `pages.get_content` results contain bounded Markdown and an
`observationId`; the host adds one `page.read.exact` evidence record with the
Page ID, content version, digest, and observation time, alongside the generic
`flowglad.read` record. Revision list/get produce only one generic
`flowglad.read` record; semantic discovery does the same. They never produce
exact Page observation evidence. No exact Page evidence is emitted for another
operation or a failed call.

Each bound method emits one `sdk.object.bound` record, and each invocation emits
one `sdk.operation.started` plus one terminal record. These records contain
only executor-owned identity, the operation enum and outcome/error code,
duration/count fields, and safe request/evidence correlation identity—never
revision or Page IDs, cursors, Page content, diff lines, filters, principals,
permissions, access sources, responses, paths, credentials, resource metadata,
semantic queries, snippets, titles, descriptions, Space names, vectors, raw
results, rejected candidates, or exception messages. Descriptor absence, logger
backpressure, and dropped records cannot alter SDK results, `FlowgladError`
details, or task settlement; loss is observable only through bounded
`sdk.logs.dropped` evidence.

See the [Flowglad OWS profile](AUTHORING.md) for the
normative authority, defaults, privacy, observation, cursor, error, and
no-snapshot semantics.

## Exact authenticated reads

When the sealed code sidecar declares `exactAuthentication`, startup installs
the task-scoped `flowglad.connections` module. Each declared alias exposes only
its declared actions. If the same compiler-validated identity is also declared
as a terminal connection, one immutable alias exposes both surfaces:

```python
def fetch_invoice_rows():
    from flowglad.connections import invoices

    return invoices.get({"invoice_id": "inv_123"})
```

Pagination is operation-specific. When an action supports another page, its
parameter schema names the provider continuation value explicitly, such as a
cursor, offset, or page index.

GET actions may seal ordered query-parameter templates alongside their path.
Resource code still passes only the action parameter object; the host
materializes declared query placeholders and delegates URL encoding to the
authenticated-fetch service. Resource code does not concatenate query strings.

The private bridge rejects an undeclared connection/action pair or invalid
parameter schema before host dispatch. It enforces sealed call, response-byte,
cumulative-byte, and wall-time budgets and validates the host result schema. The
child receives neither credentials nor the general host socket. Exact
authenticated reads still require `exactAuthentication`; a terminal connection
declaration does not grant read access. Pinned MCP reads use `kind: mcp` actions under `exactAuthentication`.
Without a relevant connection declaration, the executor installs no
`flowglad.connections` alias.
When neither connection nor Page access is declared, it installs no private
socket environment. The executor never installs a top-level `connections`
compatibility alias.

## Exact Flowglad Page reads

When the sealed code sidecar declares `pageAccess`, startup installs the
task-scoped `flowglad.pages` module. Each alias exposes only `get_content()`:

```python
from flowglad.pages import todo

snapshot = todo.get_content()
markdown = snapshot["pageContent"]["contents"]
observation_id = snapshot["observationId"]
```

The result has `pageContent`, `found`, and `observationId` fields.
`pageContent` carries the Page ID, content version, bounded Markdown, and
explicit truncation lengths. The host records the full-content version and
SHA-256 observation as durable `page.read.exact` evidence. An
`edit-flowglad-page` command authored from this read uses `observationId` as its
`baseObservationId`; approval and execution resolve the version/hash from the
evidence rather than trusting command-authored values.

The private bridge rejects undeclared Page IDs, mismatched Page results,
invalid host results, and exhausted call, response-byte, cumulative-byte, or
wall-time budgets. The host also denies a declared Page that is no longer
visible to the automation Space. Without `pageAccess`, the executor installs no
`flowglad.pages` module. It never installs a top-level `pages` compatibility
alias.

## Authored process boundary

Each authored attempt runs in one operating-system process. Python threads and
asynchronous I/O remain available. Before the authored module is imported, the
Linux executor installs a static seccomp filter: `fork`, `vfork`, and process-form
`clone` return `EPERM`; `clone3` returns `ENOSYS` so libc can retry thread
creation through inspectable `clone`. Filter installation failure stops the
attempt before import. Executor-owned helpers such as `jq` run outside this
filtered process. The enclosing invocation container remains a separate
isolation boundary (see #10844).

## Failures and supervision

Stdout and stderr are concurrently drained without deadlocking. Stdout is a
bounded return channel and is never emitted as a log; stderr is a bounded log
stream. A nonzero exit, timeout, cancellation, malformed return, mutated input
artifact, missing declared output, or invalid output is terminal and blocks
downstream work. Failing on a nonzero exit is an intentional fail-closed
Flowglad constraint beyond the Java reference runner's process-return behavior.
Timeout and cancellation target the entire new process group with TERM, wait a
fixed grace period, then KILL if necessary; all processes and pipes are awaited
before the step returns.

## Package integrity and owner authority

Skill and Automation resources use the same authenticated executable-package
manifest/file/callable validator and the same Python function ABI. The envelope
is internal execution metadata, never a replacement Skill upload format. Skill
files, organization authorization and historical hashes remain unchanged. Private
Automation attempts additionally recheck host admission, exact persisted workflow
selection and cancellation on every retry. Historical private payloads require
rebuilding; historical Skill payloads remain compatible. Live Space and standalone
CLI invocation semantics are unchanged.

`flowglad-ows-sdk-bindings-v1` is an executor-generated task-private binding file
for sealed SDK command parameter/output schemas, not a package member. The
runtime derives it after package authentication; authors must not upload it.

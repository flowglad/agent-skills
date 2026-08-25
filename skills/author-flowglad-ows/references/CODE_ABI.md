# Flowglad OWS profile v1 code ABI

> Generated from `flowglad/provisioning-agent@53a6e5f3c888c08b5c564dff9c76adfaf05f8cd3` (`packages/workflow-executor/CODE_ABI.md`). Do not edit this exported file directly.

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

The trusted launcher requires either form to resolve to a zero-argument runtime
function and serializes its return to the bounded stdout process channel.
Author code does not print a result.

`flowglad.entrypoints` exports these dependency markers:

| Marker | Injected value |
| --- | --- |
| `Input` | The required `task_input` object field whose key matches the parameter name. |
| `TaskInput` | The complete admitted task input JSON value. An entrypoint declares this marker at most once. |
| `ArtifactInput` | The consumed artifact object whose local alias matches the parameter name. |
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

<!-- static-command-constructor-example:start -->
```python
from flowglad.commands import command_dag, publish_flowglad_files


def propose_files():
    published = publish_flowglad_files(
        files=["close-report.md"],
        outputs=[{"path": "close-report.md", "render": "inline_markdown"}],
    )
    return command_dag(
        published,
        title="Publish close report",
        reasoning_summary="Propose publishing the reviewed close report.",
    )
```
<!-- static-command-constructor-example:end -->

The compiler currently derives `publish_flowglad_files`,
`create_flowglad_page`, and `edit_flowglad_page` from the shared static command
registry. Each direct constructor accepts command payload fields as kwargs,
seals the tag, and rejects `connection_id`, `data_source_id`, `dependsOn`,
`outputRefs`, and `secretRefs`. `command_file_name` overrides the generated JSON
basename without consuming an ordinary payload field named `file_name`.

`command(tag, data=None, *, file_name=None, **fields)` creates one immutable
command declaration as a low-level compatibility escape hatch for legacy or
custom tags that have no generated constructor. Do not use it to hand-author an
available static, connector, or browser-order node. Keyword fields become
`commandData` fields. The optional mapping form supports field names that are
not Python identifiers or that match helper parameter names. The default
filename is `<tag>.json`; `file_name` supplies a different JSON basename.

`command_dag(*commands, title, reasoning_summary, edges=())` assigns
zero-based positions in argument order and returns the complete terminal value.
The executor associates the proposal with its authoritative workflow run; the
script does not supply runtime identity.

Every command declaration exposes an immutable `output` namespace. Pass a
prior command's output field directly as a later command's top-level input to
infer the data edge without repeating either command filename or the output
field as a string:

```python
from flowglad.commands import command_dag, publish_flowglad_files
from flowglad.connections import gmail

publish = publish_flowglad_files(files=["report.pdf"])
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
from flowglad.commands import command_dag
from flowglad.connections import slack


def propose_message():
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
from flowglad.commands import command_dag
from flowglad.connections import quickbooks


def propose_expense():
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

`mcpAccess` installs only the pinned read methods declared for a connection
alias. A read always takes one keyword-only JSON object, and the executor sends
the generated `mcp-read.request` host frame before accepting only the matching
`mcp-read.response` result:

<!-- mcp-read-command-example:start -->
```python
from flowglad.commands import command_dag
from flowglad.connections import billing


def propose_mcp_invoice():
    invoices = billing.list_invoices(arguments={"limit": 10})
    if not invoices["items"]:
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
from flowglad.commands import command_dag
from flowglad.connections import vendor_portal


def propose_browser_order():
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

## Exact authenticated reads

When the sealed code sidecar declares `exactAuthentication`, startup installs
the task-scoped `flowglad.connections` module. Each declared alias exposes only
its declared actions. If the same compiler-validated identity is also declared
as a terminal connection, one immutable alias exposes both surfaces:

```python
from flowglad.connections import invoices

rows = invoices.get({"invoice_id": "inv_123"})
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
child receives neither credentials nor the general host socket. Without either
`exactAuthentication` or a terminal connection declaration, the executor
installs no `flowglad.connections` module.
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

# Flowglad OWS profile v1 code ABI

This is the author contract for `code:1.0.0@flowglad`. Each task declares one
public top-level function in a sealed Python 3.11 resource. The executor imports
the resource in an argv-based child with empty stdin, injects the dependencies
declared by that function, and uses its return value as the direct OWS task value. The process
uses `/workspace` as its working directory and does not invoke a shell.

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
The function uses `@entrypoint` from `flowglad.entrypoints`; the decorator has
no parentheses and directly precedes the `def` declaration. Every parameter
has one supported dependency annotation and has no default. Positional-only,
keyword-only, variadic, and unannotated parameters are invalid. A
dependency-free function has no parameters. The trusted launcher calls the
decorated wrapper and serializes its return to the bounded stdout process
channel. Author code does not print a result.

`flowglad.entrypoints` exports these dependency markers:

| Marker | Injected value |
| --- | --- |
| `Input` | The required `task_input` object field whose key matches the parameter name. |
| `TaskInput` | The complete admitted task input JSON value. An entrypoint declares this marker at most once. |
| `ArtifactInput` | The consumed artifact object whose local alias matches the parameter name. |
| `ArtifactOutput` | The produced artifact object whose local alias matches the parameter name. |

Publication reads the exact pinned source bytes without importing the module.
It verifies the selected decorated declaration and requires its artifact
parameters to match the task's `consumes` and `produces` aliases exactly. The
runtime repeats this artifact check and reports missing task-input fields with
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
| Connection/action admission, parameter schemas, result schemas, and call/byte/time budgets. | Which admitted action to call and whether its result is meaningful, consistent, complete, and unambiguous for the business operation. |
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
objects expose `path`, `media_type`, `max_bytes`, `expected_digest`, `open()`,
`write_bytes()`, `write_text()`, and `write_json()`. JSON helpers require
`application/json`; text helpers use UTF-8. An input has no write methods, and
an output has no read methods. `path` is available for APIs that require a path,
but ordinary reads and writes use the object methods.

On exit, every declared output is required and is checked for containment,
type, size, and any authored digest; the executor then computes its actual
SHA-256 digest. An undeclared file in the task's artifact output directory
fails admission. Scratch files elsewhere are not published.

## Command DAG construction

Every code task installs the pure `flowglad.commands` construction module. Its
helpers return ordinary JSON-compatible dictionaries and do not grant terminal
authority. The task's `terminal` declaration and output schema still determine
whether the executor accepts a command DAG proposal.

```python
from flowglad.commands import command, command_dag

proposal = command_dag(
    command("create-yooz-attachment", documentNumber="DOC-123"),
    title="Attach Yooz document",
    reasoning_summary="Attach the bounded Yooz document.",
)
```

`command(tag, data=None, *, file_name=None, **fields)` creates one immutable
command declaration. Keyword fields become `commandData` fields. The optional
mapping form supports field names that are not Python identifiers or that match
helper parameter names. The default filename is `<tag>.json`; `file_name`
supplies a different JSON basename.

`command_dag(*commands, title, reasoning_summary, edges=())` assigns
zero-based positions in argument order and returns the complete terminal value.
The executor associates the proposal with its authoritative workflow run; the
script does not supply runtime identity.
`ordering_edge(source, target)` expresses execution order. `data_edge(source,
target, output_field=..., target_field=...)` also binds a source result field to
a target input field. Edges reference command declarations directly, so author
code does not repeat generated filenames.

The helpers enforce their construction invariants, including unique filenames,
and forward-only edges. The executor remains the authority for the task output
schema, terminal DAG schema, command schemas, and approval boundary.

## Exact authenticated reads

When the sealed code sidecar declares `exactAuthentication`, startup installs
the task-scoped `flowglad.connections` module. Each declared alias exposes only
its declared actions:

```python
from flowglad.connections import invoices

rows = invoices.get({"invoice_id": "inv_123"})
```

Pagination is operation-specific. When an action supports another page, its
parameter schema names the provider continuation value explicitly, such as a
cursor, offset, or page index.

The private bridge rejects an undeclared connection/action pair or invalid
parameter schema before host dispatch. It enforces sealed call, response-byte,
cumulative-byte, and wall-time budgets and validates the host result schema. The
child receives neither credentials nor the general host socket. Without
`exactAuthentication`, the executor installs no `flowglad.connections` module
and no private socket environment. The executor never installs a top-level
`connections` compatibility alias.

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

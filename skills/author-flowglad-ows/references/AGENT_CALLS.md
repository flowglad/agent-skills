# Workspace agent steps in OWS programs

> Generated from `flowglad/provisioning-agent@8267a6c9cdcd190993a413db554395b76708d7a0` (`packages/workflow-compiler/AGENT_CALLS.md`). Do not edit this exported file directly.

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
        summary: {type: string}
export:
  as: '${ $context + { review: . } }'
```

Task input is any JSON value, mounted as `/in/input.json`. Instructions belong
to the sealed profile. Identity and inference metering come from the host;
JSON input cannot grant capabilities. `maxSteps` bounds model turns (1–100),
and `maxResultBytes` bounds the UTF-8 JSON result (1–1,048,576 bytes). The task
also has an authored timeout bounded by the invocation's agent-task policy.
Cancellation terminates the loop and cancels in-flight authenticated reads. Agent tasks spend
their step budget in one handler attempt.

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
the agent does not discover an organization's resource catalog. Bind live
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

## Compatibility and rollout

This is a core model-surface change. The profile has a new identity and rejects
sealed revisions using the transitional reasoning profile. Republish affected
workflows with explicit inputs, artifacts, instructions, and result schemas;
do not reinterpret an existing sealed profile. Deploy compiler, host, and
executor contract changes together. Keep newly authored workspace-agent
revisions inactive until representative model evaluations have passed.
In particular, review file analysis,
structured-output correction, artifact production, budget exhaustion, and
cancellation; the host's deterministic transport tests do not substitute for
model-quality evaluation. Update the live authoring catalog and refresh its
recorded authoring replay evidence before enabling authoring-tool discovery of
this profile.

See [agent-review.ows.yaml](agent-review.ows.yaml) for a complete
advisory workflow and [AUTHORING.md](./AUTHORING.md) for OWS dataflow syntax.

A connection action may instead declare `kind: authenticated-fetch`, with a name
and JSON parameter/result schemas. Parameters use the shared authenticated-fetch
request shape (`method`, `path`, optional `query` and `body`). The host supplies the
bound source identifier and applies provider read policy; authored parameters
cannot select a different source. The same action works in code and agent tasks.

Agent tasks may also declare `flowgladAccess`. `read-flowglad <operation> '<JSON
arguments>'` invokes only declared operations through the shared Flowglad resource
host. Input schemas are exposed at `/in/flowglad/<operation>.json`.

The compiler supports a value result contract. Automation publication requires
one final unconditional terminal code task that produces the command DAG.

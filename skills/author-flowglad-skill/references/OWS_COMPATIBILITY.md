# Preparing a Skill for OWS code calls

Flowglad Skill verification and OWS publication validate different interfaces.

- Skill verification executes a declared `native-python` `cli-v1` script with positional string arguments, checks stdout, and runs declared tests.
- An OWS `code:1.0.0@flowglad` task selects source from an exact verified Skill revision and separately validates one Python function declaration using the Flowglad OWS code ABI.

A verified Skill is therefore not automatically OWS-callable. When OWS composition is required, make the selected script satisfy both contracts and validate the resulting OWS program before claiming compatibility.

## OWS source requirements

The selected source declares one public synchronous top-level function. It may be a plain zero-argument function, or a decorated function when it needs injected task input or artifacts:

```python
from flowglad.entrypoints import Input, entrypoint


@entrypoint
def reconcile(invoice_id: Input) -> dict[str, str]:
    return {"invoice_id": invoice_id}
```

The OWS task selects the exact module path and names the function independently:

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: skill-revision
      skillId: skl_exact
      revisionId: skr_exact
      path: scripts/reconcile.py
      digest: sha256:exact_verified_manifest_digest
    entrypoint: reconcile
    runtime:
      language: python
      version: '3.11'
      memoryMb: 128
```

A decorated function's parameters use only `Input`, `TaskInput`, `ArtifactInput`, or `ArtifactOutput` imported from `flowglad.entrypoints`. Artifact parameter aliases must exactly match the OWS task's `consumes` and `produces` declarations. A plain function declares no parameters. Either form returns the direct JSON-compatible OWS task value and does not print it.

The same file's CLI execution path remains responsible for the Skill entrypoint's positional arguments and stdout contract. Stable Skill CLI entrypoint IDs are lifecycle metadata; they do not select OWS source. Do not assume that passing one interface proves the other. Use the full `CODE_ABI.md` bundled with `author-flowglad-ows` when implementing artifacts, connection actions, runtime helpers, or terminal command DAGs.

## Required evidence

Before handoff, report these states separately:

1. Native-Python CLI tests and smoke checks passed locally.
2. The Skill revision passed Flowglad verification.
3. The OWS compiler accepted the `skill-revision` resource and selected function.
4. OWS publication resolved the exact verified manifest digest, if publication was requested.

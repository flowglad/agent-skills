# Preparing a Skill for OWS code calls

Flowglad Skill verification and OWS publication validate different interfaces.

- Skill verification executes a declared `native-python` `cli-v1` script with positional string arguments, checks stdout, and runs declared tests.
- An OWS `code:1.0.0@flowglad` task selects source from an exact verified Skill revision and separately validates one decorated Python function using the Flowglad OWS code ABI.

A verified Skill is therefore not automatically OWS-callable. When OWS composition is required, make the selected script satisfy both contracts and validate the resulting OWS program before claiming compatibility.

## OWS source requirements

The selected source declares one public synchronous top-level function:

```python
from flowglad.entrypoints import Input, entrypoint


@entrypoint
def reconcile(invoice_id: Input) -> dict[str, str]:
    return {"invoice_id": invoice_id}
```

The OWS task names that function separately from the stable Skill entrypoint identity:

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: skill-revision
      skillId: skl_exact
      revisionId: skr_exact
      entrypointId: ske_exact
      digest: sha256:exact_verified_manifest_digest
    entrypoint: reconcile
    runtime:
      language: python
      version: '3.11'
      memoryMb: 128
```

The decorated function parameters use only `Input`, `TaskInput`, `ArtifactInput`, or `ArtifactOutput` imported from `flowglad.entrypoints`. Artifact parameter aliases must exactly match the OWS task's `consumes` and `produces` declarations. The function returns the direct JSON-compatible OWS task value and does not print it.

The same file's CLI execution path remains responsible for the Skill entrypoint's positional arguments and stdout contract. Do not assume that passing one interface proves the other. Use the full `CODE_ABI.md` bundled with `author-flowglad-ows` when implementing artifacts, connection actions, runtime helpers, or terminal command DAGs.

## Required evidence

Before handoff, report these states separately:

1. Native-Python CLI tests and smoke checks passed locally.
2. The Skill revision passed Flowglad verification.
3. The OWS compiler accepted the `skill-revision` resource and decorated function.
4. OWS publication resolved the exact verified manifest digest, if publication was requested.

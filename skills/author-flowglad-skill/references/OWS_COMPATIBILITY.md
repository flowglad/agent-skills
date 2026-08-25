# Preparing a Skill for OWS code calls

Flowglad verifies new OWS-native Skill packages through the same selected-function ABI used by published Automations.

## Source requirements

Place Python under `scripts/**.py`. A workflow may select a public synchronous zero-argument function directly. When a function needs task input or artifacts, import `entrypoint` and only the required dependency markers from `flowglad.entrypoints`:

```python
from flowglad.entrypoints import Input, entrypoint


@entrypoint
def reconcile(invoice_id: Input) -> dict[str, str]:
    return {"invoice_id": invoice_id}
```

Supported injected parameter annotations are `Input`, `TaskInput`, `ArtifactInput`, and `ArtifactOutput`. Do not use defaults, variadic parameters, other decorators, or async functions. Return one JSON-compatible value. Send diagnostics to stderr by raising a safe exception; do not print a result.

Do not add `argparse`, `sys.argv`, an `if __name__ == "__main__"` block, positional-argument metadata, or a stdout CLI adapter. Those markers select or conflict with the legacy verification profile.

## Test cases

Put small synthetic OWS cases under `tests/**.json`:

```json
{
  "kind": "flowglad-ows-code-test-v1",
  "entrypoint": {
    "path": "scripts/reconcile.py",
    "function": "reconcile"
  },
  "input": {"invoice_id": "inv_example"},
  "expectedSubset": {"invoice_id": "inv_example"}
}
```

Each case uses only `kind`, `entrypoint`, `input`, and `expectedSubset`. Verification invokes the function through injected OWS bindings, requires a JSON-compatible result, and recursively checks the expected subset.

## Publication boundary

Skill verification proves the package's OWS profile. Automation publication still resolves the exact `revisionId` and module `path`, validates the selected function against the task's input and artifact declarations, and seals the revision into the Automation bundle. Report Skill verification and Automation publication separately.

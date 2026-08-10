# Using verified Skill revisions in OWS

Use a `skill-revision` resource when a reusable Flowglad Skill contains source that satisfies the OWS code ABI.

## Resolve the exact resource

1. Use `skills.list` to discover visible Skills.
2. Use `skills.get` to inspect the selected Skill's active or verified revisions, package files, manifest hashes, stable CLI entrypoints, and verification diagnostics.
3. Select an exact revision that has completed verification and is accessible to the Automation's Space.
4. Resolve all five values required by the OWS code task:
   - Stable `skillId`.
   - Immutable `revisionId`.
   - Exact Python module `path` within the revision, such as `scripts/reconcile.py`.
   - Verified revision `manifestHash`, used as the resource `digest`.
   - Selected Python function name, used as `with.fg.entrypoint`.

Stable Skill CLI entrypoint IDs are lifecycle metadata and do not select OWS source. Do not assume a CLI entrypoint name equals the selected OWS function name. Resolve the module path and function name from the exact locally authored or retrieved revision, or leave the dependency unresolved. OWS validation and publication must inspect the exact pinned bytes before compatibility is proven.

## Resource shape

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: skill-revision
      skillId: skl_exact
      revisionId: skr_exact
      path: scripts/reconcile.py
      digest: sha256:exact_verified_manifest_hash
    entrypoint: reconcile
    runtime:
      language: python
      version: '3.11'
      memoryMb: 128
    consumes: []
    produces: []
```

The resource `path` selects an immutable Python file from the verified revision. The separate `entrypoint` field selects one admitted top-level function inside that file. A Skill CLI entrypoint declaration may point at the same script, but its stable ID does not participate in OWS execution.

## Compatibility boundary

Flowglad Skill verification executes the source as a native-Python CLI with positional string arguments and stdout checks. OWS publication instead statically validates the selected function declaration against `references/CODE_ABI.md`. A revision can therefore be verified as a Skill while remaining invalid for a particular OWS code task.

Require the OWS compiler and publication resolver to confirm:

- The revision is verified and the digest matches its manifest.
- The selected module path belongs to that revision.
- The source contains the named public top-level admitted function.
- Its artifact parameters exactly match `consumes` and `produces` aliases.
- The function's admitted inputs and return value match the OWS task schemas.

## Missing capability

When no compatible Skill exists:

1. Use `author-flowglad-skill` if available.
2. State that the package must support both `native-python` `cli-v1` verification and the OWS code ABI.
3. Wait for an exact verified revision.
4. Resume OWS authoring with the resolved identities.

Use direct `space-file` code only when it is intentionally automation-specific, the Skill lifecycle is unavailable, or the user explicitly requests it. Direct code still follows `references/CODE_ABI.md` and uses an exact content digest.

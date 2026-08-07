# Using verified Skill revisions in OWS

Use a `skill-revision` resource when a reusable Flowglad Skill contains source that satisfies the OWS code ABI.

## Resolve the exact resource

1. Use `skills.list` to discover visible Skills.
2. Use `skills.get` to inspect the selected Skill's active or verified revisions, stable entrypoints, manifest hashes, and verification diagnostics.
3. Select an exact revision that has completed verification and is accessible to the Automation's Space.
4. Resolve all five identities required by the OWS code task:
   - Stable `skillId`.
   - Immutable `revisionId`.
   - Stable Skill `entrypointId` selecting the source file.
   - Verified revision `manifestHash`, used as the resource `digest`.
   - Decorated Python function name, used as `with.fg.entrypoint`.

Do not assume the stable Skill entrypoint name equals the decorated OWS function name. `skills.get` exposes package and entrypoint metadata but not source bodies. Resolve the function name from user-provided or locally authored source, or leave the dependency unresolved. OWS validation and publication must inspect the exact pinned bytes before compatibility is proven.

## Resource shape

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: skill-revision
      skillId: skl_exact
      revisionId: skr_exact
      entrypointId: ske_exact
      digest: sha256:exact_verified_manifest_hash
    entrypoint: reconcile
    runtime:
      language: python
      version: '3.11'
      memoryMb: 128
    consumes: []
    produces: []
```

The `entrypointId` selects the immutable Skill source file. The separate `entrypoint` field selects one top-level `@entrypoint` function inside that file.

## Compatibility boundary

Flowglad Skill verification executes the source as a native-Python CLI with positional string arguments and stdout checks. OWS publication instead statically validates the selected decorated function against `references/CODE_ABI.md`. A revision can therefore be verified as a Skill while remaining invalid for a particular OWS code task.

Require the OWS compiler and publication resolver to confirm:

- The revision is verified and the digest matches its manifest.
- The selected stable entrypoint belongs to that revision.
- The source contains the named public top-level decorated function.
- Its artifact parameters exactly match `consumes` and `produces` aliases.
- The function's admitted inputs and return value match the OWS task schemas.

## Missing capability

When no compatible Skill exists:

1. Use `author-flowglad-skill` if available.
2. State that the package must support both `native-python` `cli-v1` verification and the OWS code ABI.
3. Wait for an exact verified revision.
4. Resume OWS authoring with the resolved identities.

Use direct `space-file` code only when it is intentionally automation-specific, the Skill lifecycle is unavailable, or the user explicitly requests it. Direct code still follows `references/CODE_ABI.md` and uses an exact content digest.

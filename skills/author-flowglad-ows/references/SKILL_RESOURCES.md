# Using verified Skill revisions in OWS

Use a `skill-revision` resource when a reusable Flowglad Skill contains source that satisfies the OWS code ABI.

## Resolve the exact resource

1. Use `skills.list` to discover visible Skills.
2. Use `skills.get` to inspect active or verified revisions, package file metadata, and verification diagnostics.
3. Select an exact verified revision accessible to the Automation's Space.
4. Resolve the immutable `revisionId`, exact Python module `path`, and selected public function name.

Flowglad derives the parent Skill from `revisionId`; do not author a redundant `skillId`. Stable CLI entrypoint IDs are lifecycle metadata and do not select OWS source.

## Resource shape

```yaml
call: code:1.0.0@flowglad
with:
  fg:
    resource:
      kind: skill-revision
      revisionId: skr_exact
      path: scripts/reconcile.py
    entrypoint: reconcile
    consumes: []
    produces: []
```

Do not add `runtime`. The compiler seals Python 3.11 and the memory limit. Publication resolves the exact revision, derives the parent Skill and manifest, verifies access, and statically validates the selected function against the task's inputs and artifacts.

## Compatibility boundary

Skill verification and OWS publication are separate gates. Require publication validation to confirm that the revision is verified, the path belongs to it, the named public function is admitted, and its injected artifact parameters exactly match `consumes` and `produces`.

When no compatible Skill exists, use `author-flowglad-skill` if available, wait for an exact verified revision, then resume OWS authoring. Use direct `space-file` code only when it is intentionally automation-specific, the Skill lifecycle is unavailable, or the user explicitly requests it.

# Using verified Skill revisions in OWS

Use a `skill-revision` resource when a reusable Flowglad Skill contains source that satisfies the OWS code ABI.

## Resolve the exact resource

1. Use `skills.list` to discover visible Skills.
2. Use `skills.get` to inspect active or verified revisions, package file metadata, and verification diagnostics.
3. Select an exact verified revision in the Automation's organization. Skill authorization is organization-scoped; the Automation and runtime retain their separate Space authorization.
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

For intentionally reusable computation, use `author-flowglad-skill` when no compatible
Skill exists and the user has requested remote submission. Resolve the resulting exact
verified revision before normal publication. If the first revision is rejected, repair
the same Skill using the newest rejected base; do not create a duplicate.

New computation private to one Automation uses its Automation-owned executable bundle
when the capability is advertised. Read **Automation-private bundle entrypoints** in
[AUTHORING.md](AUTHORING.md). Unavailable or failed private authoring does not permit
creating a Skill as fallback. Preserve `space-file` only for existing Automation
histories that already use it.

An explicitly requested deferred development workflow may select sealed unpublished
content through manual execution. It requires `development: true`, explicit activation,
and later package publication plus normal workflow revision/activation. It cannot run
from schedules or events.

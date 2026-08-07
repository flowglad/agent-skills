# Flowglad Skill MCP lifecycle

Use this reference when Flowglad MCP exposes the versioned Skill tools.

## Discover before writing

1. Call `skills.list` to find visible Skills.
2. Call `skills.get` for a plausible match.
3. Reuse an active compatible entrypoint when it already provides the requested capability.

`skills.get` returns revision, file metadata, entrypoints, verification runs, and diagnostics, but not package file bodies. Editing therefore requires user-provided or locally mounted source bytes plus an explicit base revision identity.

## Create a new Skill

1. Prepare the complete package and entrypoint declarations.
2. Call `skills.create` with the slug, name, optional description and Space, base64 package objects, and entrypoints without IDs.
3. Record the returned lifecycle `jobId`. Do not blindly retry the non-idempotent write.
4. Poll `skills.get_lifecycle_request(jobId)` until the lifecycle job has typed output.
5. Read `skillId`, `candidateRevisionId`, and `verificationDispatched` from the successful result.
6. Poll `skills.get(skillId)` until the candidate revision leaves `candidate` or `verifying`.
7. Read the revision state and its latest verification-run diagnostics.

The lifecycle request records candidate creation and verification dispatch. The authoritative verification result is the revision and verification metadata returned by `skills.get`.

## Update an existing Skill

1. Resolve the exact Skill and active base revision through `skills.get`.
2. Preserve stable entrypoint IDs, names, and descriptions.
3. Call `skills.create_candidate` with `skillId`, exact `baseRevisionId`, changed package objects, complete entrypoint declarations, and the intended preserve/delete/move semantics.
4. Poll the lifecycle job, then the candidate revision through `skills.get` as for creation.

If the base becomes stale, inspect the new active revision and deliberately rebase the authored changes. Never overwrite or silently discard the competing revision.

## Interpret outcomes

| Evidence | Meaning |
| --- | --- |
| MCP call accepted | Lifecycle work was queued |
| Lifecycle job succeeded | Candidate exists and verification dispatch was attempted |
| `verificationDispatched: true` | Verification task was dispatched |
| Revision `verifying` | Verification is in progress |
| Revision `active` | Verification passed and the revision promoted |
| Revision `verified` | Verification passed but the revision did not become active, commonly because its base became stale |
| Revision `rejected` | Verification failed; inspect diagnostics |

Repair authored failures by changing the package and submitting a new candidate revision. A retry of the same immutable bytes is appropriate only for a known transient verification-infrastructure failure, and the retry operation is not currently exposed through the public MCP Skill tools.

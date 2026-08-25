# Flowglad Skill MCP lifecycle

Use this reference when Flowglad MCP exposes the versioned Skill tools.

## Permissions and discovery

Creating or updating a Skill requires organization `skills:write`. A Space-scoped create or candidate update also requires the corresponding Space access. Report denied authorization instead of retrying.

Call `skills.list`, then `skills.get`, before writing. Reuse a compatible active Skill when one exists. Reads return revision and file metadata, entrypoints, verification runs, and diagnostics, but not package bodies; updates require locally available bytes and an exact base revision.

## Choose a transport

Use inline transport for small packages:

```bash
python3 /path/to/author-flowglad-skill/scripts/build-package-payload.py PACKAGE_DIR
```

Pass the emitted `files` and `entrypoints` to `skills.create` or `skills.create_candidate`.

For large packages or MCP byte-transport failures, build a staged declaration:

```bash
python3 /path/to/author-flowglad-skill/scripts/build-package-payload.py PACKAGE_DIR --transport staged
```

The staged fragment contains exact `sizeBytes`, lowercase `sha256:` `contentHash`, role, and content type instead of base64 bodies.

## Inline create or update

For a new Skill, call `skills.create` with slug, human-readable name, optional description and Space, inline files, and normally an empty entrypoint list. For an update, call `skills.create_candidate` with the exact `skillId`, `baseRevisionId`, complete entrypoint declarations, changed files, and explicit preserve/delete/move semantics.

Record the returned `jobId`. These writes are non-idempotent; do not blindly retry after an ambiguous result.

## Staged create or update

1. Finalize every local package byte before creating a session.
2. Call `skills.create_package_upload_session` with `operation: create_skill` or `operation: create_candidate`, the staged file declarations, and the same normalized identity and entrypoint fields intended for finalization.
3. For every returned upload item, HTTP `PUT` the exact corresponding local bytes to `uploadUrl` with the advertised headers.
4. If any file changes, an upload expires, or a result is ambiguous, discard the session and create a new one.
5. After every PUT succeeds, call `skills.finalize_package_upload_session` once with `uploadSessionId` and the exact same operation/declaration. Do not include `uploadTtlSeconds` in finalization.
6. Record the returned lifecycle `jobId`.

## Follow verification

Poll `skills.get_lifecycle_request(jobId)` until it returns typed output. Record `skillId`, `candidateRevisionId`, and `verificationDispatched`, then poll `skills.get(skillId)` until the candidate leaves `candidate` or `verifying`.

| Evidence | Meaning |
| --- | --- |
| MCP call accepted | Lifecycle work was queued |
| Lifecycle job succeeded | A candidate exists and verification dispatch was attempted |
| `verificationDispatched: true` | Verification was dispatched, not completed |
| Revision `active` | Verification passed and the candidate promoted |
| Revision `verified` | Verification passed but did not promote, commonly because its base became stale |
| Revision `rejected` | Verification failed; inspect diagnostics |

If the base is stale, inspect the new active revision and deliberately rebase. Repair authored failures with changed bytes in a new candidate. Do not overwrite or silently discard a competing revision.

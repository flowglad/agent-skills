# Flowglad Skill package contract

Use this reference when authoring files or native-Python entrypoint declarations for a versioned Flowglad Skill.

## Package layout

Every package contains an exactly-cased `SKILL.md` with role `instructions`. Other members may live only under these roots:

| Path | Required role | Purpose |
| --- | --- | --- |
| `files/**` | Any non-`instructions` role; normally `file` | Ordinary visible support files |
| `scripts/**` | `script` | Executable Python |
| `references/**` | `reference` | Instructions loaded as needed |
| `assets/**` | `asset` | Fixtures and output templates |
| `tests/**` | `test` | Directly executable tests |

Paths are relative POSIX paths. Do not use backslashes, NUL, absolute paths, empty segments, `.` segments, or `..` segments. Paths must not collide after Unicode normalization and case folding. A `files/**` member must not map to the same visible path as another support member.

Current limits:

- Slug: 64 characters, lowercase letters and digits separated by single hyphens.
- Files: 128.
- Entrypoints: 32.
- Path depth: 8 segments.
- Path length: 512 UTF-8 bytes.
- Individual file: 10 MiB.
- Whole package: 50 MiB.

## `SKILL.md`

Start with YAML frontmatter delimited by `---`, followed by Markdown instructions. The strict frontmatter supports:

- Required `name`: exactly the Skill slug.
- Required `description`: non-empty and at most 1,024 characters. State what the Skill does and when an agent should use it.
- Optional `license`.
- Optional `compatibility`: at most 500 characters.
- Optional string-to-string `metadata`.
- Optional `allowed-tools` string.

Keep the body focused on how an agent should use the packaged capability. Put large domain references in `references/` and reusable execution in `scripts/`.

## Native-Python CLI entrypoints

Entrypoint declarations are lifecycle metadata, not package files. Each entrypoint has:

```json
{
  "name": "reconcile",
  "description": "Reconcile prepared bank and ledger files",
  "runtime": "native-python",
  "interface": "cli-v1",
  "scriptPath": "scripts/reconcile.py",
  "positionalArgs": [
    {
      "name": "bank-file",
      "description": "Prepared bank CSV path",
      "type": "string",
      "required": true
    }
  ],
  "fixturePaths": ["assets/bank.csv"],
  "smokeArgs": ["assets/bank.csv"],
  "outputChecks": [{"kind": "stdout-json"}],
  "testPaths": ["tests/reconcile_test.py"]
}
```

For `skills.create`, omit `id`; Flowglad allocates stable entrypoint identities. For `skills.create_candidate`, include and preserve the exact stable `ske_...` identity, name, and description of every existing entrypoint.

Entrypoint constraints:

- `scriptPath` names an exact `scripts/**.py` package member.
- Argument names start with a lowercase letter and contain lowercase letters, digits, or hyphens.
- Arguments are ordered positional strings. Required arguments precede any optional invocation behavior implemented by the script.
- `fixturePaths` name exact `assets/**` or `tests/**` members.
- `testPaths` name exact `tests/**` members.
- `smokeArgs` cover every required argument and do not exceed the declared argument count.
- `outputChecks` contains one to sixteen `exit-code`, `stdout-non-empty`, `stdout-contains`, or `stdout-json` checks.

Scripts send their declared result to stdout and diagnostics to stderr. Make the stdout contract deterministic and bounded.

## Verification stages

Flowglad verification runs automatically after candidate creation:

1. `structure`: package paths, roles, limits, frontmatter, and asset projection.
2. `syntax`: Python compilation for scripts and tests.
3. `interface`: entrypoint and smoke-argument consistency.
4. `smoke`: exact script invocation plus output checks.
5. `tests`: every declared test path executed directly.

Successful local execution is useful preflight but never substitutes for the server verification record.

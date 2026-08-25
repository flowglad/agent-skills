# Flowglad Skill package contract

Use this reference when authoring a versioned Flowglad Skill.

## Package layout

Every package contains exactly-cased `meta.json` metadata and `SKILL.md` instructions. Other members may live only under these roots:

| Path | Required role | Purpose |
| --- | --- | --- |
| `meta.json` | `file` | Strict package metadata |
| `SKILL.md` | `instructions` | Agent-facing instructions |
| `files/**` | Any non-`instructions` role; normally `file` | Ordinary visible support files |
| `scripts/**` | `script` | Executable Python |
| `references/**` | `reference` | Instructions loaded as needed |
| `assets/**` | `asset` | Fixtures and output templates |
| `tests/**` | `test` | OWS JSON cases or legacy executable tests |

Paths are relative POSIX paths. Do not use backslashes, NUL, absolute paths, empty segments, `.` segments, or `..` segments. Paths must not collide after Unicode normalization and case folding. A `files/**` member must not map to the same visible path as another support member.

Current limits:

- Slug: 64 characters, lowercase letters and digits separated by single hyphens.
- Files: 128.
- Entrypoints: 32.
- Path depth: 8 segments.
- Path length: 512 UTF-8 bytes.
- Individual file: 10 MiB.
- Whole package: 50 MiB.

## `meta.json`

Store package metadata as one strict JSON object with:

- Required `name`: exactly the Skill slug.
- Required `description`: non-empty and at most 1,024 characters. State what the Skill does and when an agent should use it.
- Optional `license`.
- Optional `compatibility`: at most 500 characters.
- Optional string-to-string `metadata`.
- Optional `allowed-tools` string.

Do not add other properties.

## `SKILL.md`

Write Markdown instructions without YAML frontmatter; versioned Flowglad Skill metadata belongs only in `meta.json`. Keep the instructions focused on how an agent should use the packaged capability. Put large domain references in `references/` and reusable execution in `scripts/`.

## OWS-native Python

Default new executable packages to the OWS verification profile. Put selected functions under `scripts/**.py`, use the function contract in `OWS_COMPATIBILITY.md`, and keep lifecycle `entrypoints` empty. Put synthetic `flowglad-ows-code-test-v1` JSON cases under `tests/**.json`.

The verifier selects the OWS profile when a script explicitly imports the Flowglad runtime and exposes an admitted function, or when the package contains an OWS JSON test case. It compiles Python, validates selected-function interfaces, loads modules with the OWS execution bindings, and executes the JSON cases through the zero-argument runtime ABI.

## Legacy CLI entrypoints

Use CLI entrypoints only when explicitly maintaining a legacy package. Do not combine CLI markers such as `sys.argv`, `argparse`, or `__main__` with OWS-native source.

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

1. `structure`: package paths, roles, limits, metadata, instructions, and asset projection.
2. `syntax`: Python compilation.
3. `interface`: the selected OWS function or legacy CLI declarations.
4. `smoke`: OWS module loading or the legacy CLI smoke invocation.
5. `tests`: OWS JSON cases or declared legacy test paths.

Successful local execution is useful preflight but never substitutes for the server verification record.

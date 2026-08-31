#!/usr/bin/env python3
"""Export public Flowglad authoring references from provisioning-agent."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CODE_ABI_DESTINATION = "skills/author-flowglad-ows/references/CODE_ABI.md"
SOURCE_MAPPINGS = {
    CODE_ABI_DESTINATION: "packages/workflow-executor/CODE_ABI.md",
    "skills/author-flowglad-ows/references/invoice-reconciliation.ows.yaml": (
        "packages/workflow-compiler/examples/invoice-reconciliation.ows.yaml"
    ),
    "skills/author-flowglad-ows/references/mock-bank-browser-statement.ows.yaml": (
        "packages/workflow-compiler/examples/mock-bank-browser-statement.ows.yaml"
    ),
    "skills/author-flowglad-ows/references/page-todo-update.ows.yaml": (
        "packages/workflow-compiler/examples/page-todo-update.ows.yaml"
    ),
    "skills/author-flowglad-ows/references/yooz-bounded-document-number.ows.yaml": (
        "packages/workflow-compiler/examples/yooz-bounded-document-number.ows.yaml"
    ),
    "skills/author-flowglad-ows/references/mcp-ows-v1.ows.yaml": (
        "packages/workflow-compiler/examples/mcp-ows-v1.ows.yaml"
    ),
}
COMPILER_SCRIPT = """
import { compileFlowgladOwsWorkflow } from './packages/workflow-compiler/src/index.ts'
let failed = false
for (const file of process.argv.slice(1)) {
  const source = Bun.YAML.parse(await Bun.file(file).text())
  const result = compileFlowgladOwsWorkflow(source)
  console.log(`${file}: ${result.ok ? 'PASS' : 'FAIL'}`)
  if (!result.ok) {
    failed = true
    console.error(JSON.stringify(result.diagnostics, null, 2))
  }
}
if (failed) process.exit(1)
"""


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_commit(source_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def generated_notice(commit: str, source_path: str, comment: str = ">") -> str:
    return (
        f"{comment} Generated from `flowglad/provisioning-agent@{commit}` "
        f"(`{source_path}`). Do not edit this exported file directly."
    )


def export_bytes(source_path: str, source: bytes, commit: str) -> bytes:
    text = source.decode("utf-8")
    if source_path == "packages/workflow-executor/CODE_ABI.md":
        title, remainder = text.split("\n", 1)
        text = f"{title}\n\n{generated_notice(commit, source_path)}\n\n{remainder.lstrip()}"
    elif source_path.endswith(".ows.yaml"):
        text = f"# {generated_notice(commit, source_path, comment='').strip()}\n{text}"
    return text.encode("utf-8")


def expected_exports(source_root: Path) -> tuple[dict[str, bytes], bytes]:
    commit = source_commit(source_root)
    exports: dict[str, bytes] = {}
    lock_files: dict[str, dict[str, str]] = {}
    for destination, source_path in SOURCE_MAPPINGS.items():
        source = (source_root / source_path).read_bytes()
        exported = export_bytes(source_path, source, commit)
        exports[destination] = exported
        lock_files[destination] = {
            "sourcePath": source_path,
            "sourceSha256": sha256(source),
            "exportedSha256": sha256(exported),
        }
    lock = {
        "sourceRepository": "flowglad/provisioning-agent",
        "sourceCommit": commit,
        "files": lock_files,
    }
    return exports, (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_with_compiler(source_root: Path) -> None:
    ows_root = REPOSITORY_ROOT / "skills/author-flowglad-ows"
    workflows = [
        ows_root / "assets/starter.ows.yaml",
        *sorted((ows_root / "references").glob("*.ows.yaml")),
    ]
    subprocess.run(
        ["bun", "-e", COMPILER_SCRIPT, "--", *(str(path) for path in workflows)],
        check=True,
        cwd=source_root,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--validate-compiler",
        action="store_true",
        help="compile every bundled OWS document using the source checkout",
    )
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    exports, lock = expected_exports(source_root)
    exports["sources.lock.json"] = lock

    stale: list[str] = []
    for relative_path, expected in exports.items():
        destination = REPOSITORY_ROOT / relative_path
        if args.check:
            if not destination.is_file() or destination.read_bytes() != expected:
                stale.append(relative_path)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(expected)

    if stale:
        print("Exported Flowglad authoring resources are stale:", file=sys.stderr)
        for path in stale:
            print(f"- {path}", file=sys.stderr)
        return 1
    if args.check:
        print("Exported Flowglad authoring resources match the source checkout.")
    else:
        print(f"Exported {len(exports) - 1} resources and updated sources.lock.json.")
    if args.validate_compiler:
        validate_with_compiler(source_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

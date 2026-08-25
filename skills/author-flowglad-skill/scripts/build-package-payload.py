#!/usr/bin/env python3
"""Build the files/entrypoints fragment used by Flowglad Skill MCP tools."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import mimetypes
from pathlib import Path
import re
import sys
import unicodedata

MAX_FILES = 128
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_PATH_BYTES = 512
MAX_PATH_DEPTH = 8
MAX_ENTRYPOINTS = 32
IGNORED_DIRECTORIES = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "node_modules",
}
IGNORED_BASENAMES = {".DS_Store", ".coverage", "coverage.xml", "Thumbs.db"}
IGNORED_SUFFIXES = (".pyc", ".pyo")


def role_for_path(path: str) -> str:
    if path == "SKILL.md":
        return "instructions"
    if path == "meta.json":
        return "file"
    for prefix, role in (
        ("files/", "file"),
        ("scripts/", "script"),
        ("references/", "reference"),
        ("assets/", "asset"),
        ("tests/", "test"),
    ):
        if path.startswith(prefix):
            return role
    raise ValueError(
        f"unsupported package path {path!r}; expected meta.json, SKILL.md, or an allowed support root"
    )


def content_type(path: Path) -> str | None:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed is not None:
        return guessed
    if path.suffix == ".py":
        return "text/x-python"
    return None


def validate_relative_path(path: str) -> None:
    if len(path.encode("utf-8")) > MAX_PATH_BYTES:
        raise ValueError(f"package path exceeds {MAX_PATH_BYTES} UTF-8 bytes: {path}")
    parts = path.split("/")
    if re.match(r"^[A-Za-z]:", path) or "\\" in path or "\0" in path:
        raise ValueError(f"package path is not a safe relative POSIX path: {path}")
    if len(parts) > MAX_PATH_DEPTH:
        raise ValueError(f"package path exceeds {MAX_PATH_DEPTH} segments: {path}")
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"package path contains an unsafe segment: {path}")


def is_ignored(relative: str) -> bool:
    parts = relative.split("/")
    basename = parts[-1]
    return (
        any(part in IGNORED_DIRECTORIES for part in parts)
        or basename in IGNORED_BASENAMES
        or basename.endswith(IGNORED_SUFFIXES)
    )


def logical_path(relative: str) -> str | None:
    if relative in {"meta.json", "SKILL.md"}:
        return None
    if relative.startswith("files/"):
        return relative.removeprefix("files/")
    if relative.startswith("assets/"):
        return relative.removeprefix("assets/")
    return relative


def package_files(package_dir: Path, transport: str) -> list[dict[str, object]]:
    if not package_dir.is_dir():
        raise ValueError(f"package directory does not exist: {package_dir}")
    paths = sorted(
        path
        for path in package_dir.rglob("*")
        if path.is_file() and not is_ignored(path.relative_to(package_dir).as_posix())
    )
    if not paths or len(paths) > MAX_FILES:
        raise ValueError(f"package must contain between 1 and {MAX_FILES} files")
    if any(path.is_symlink() for path in paths):
        raise ValueError("symbolic links are not supported in inline MCP packages")

    objects: list[dict[str, object]] = []
    total_bytes = 0
    casefolded: set[str] = set()
    logical_paths: set[str] = set()
    for path in paths:
        relative = path.relative_to(package_dir).as_posix()
        validate_relative_path(relative)
        key = unicodedata.normalize("NFKC", relative).casefold()
        if key in casefolded:
            raise ValueError(f"package path collides after case folding: {relative}")
        casefolded.add(key)
        visible = logical_path(relative)
        if visible is not None:
            logical_key = unicodedata.normalize("NFKC", visible).casefold()
            if logical_key in logical_paths:
                raise ValueError(f"package members map to the same logical path: {relative}")
            logical_paths.add(logical_key)

        body = path.read_bytes()
        if len(body) > MAX_FILE_BYTES:
            raise ValueError(f"package file exceeds {MAX_FILE_BYTES} bytes: {relative}")
        total_bytes += len(body)
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError(f"package exceeds {MAX_TOTAL_BYTES} total bytes")
        item: dict[str, object] = {
            "path": relative,
            "role": role_for_path(relative),
            "contentType": content_type(path),
        }
        if transport == "inline":
            item["contentBase64"] = base64.b64encode(body).decode("ascii")
        else:
            item["sizeBytes"] = len(body)
            item["contentHash"] = f"sha256:{hashlib.sha256(body).hexdigest()}"
        objects.append(item)

    if not any(item["path"] == "meta.json" for item in objects):
        raise ValueError("package must contain exactly-cased meta.json")
    if not any(item["path"] == "SKILL.md" for item in objects):
        raise ValueError("package must contain exactly-cased SKILL.md")
    return objects


def entrypoints(path: Path | None) -> object:
    if path is None:
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("entrypoints JSON must contain an array")
    if len(value) > MAX_ENTRYPOINTS:
        raise ValueError(f"entrypoints JSON exceeds {MAX_ENTRYPOINTS} entries")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Encode a local Flowglad Skill package for skills.create or skills.create_candidate"
    )
    parser.add_argument("package_dir", type=Path)
    parser.add_argument("--entrypoints", type=Path)
    parser.add_argument("--transport", choices=("inline", "staged"), default="inline")
    args = parser.parse_args()
    try:
        payload = {
            "files": package_files(args.package_dir.resolve(), args.transport),
            "entrypoints": entrypoints(args.entrypoints),
        }
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

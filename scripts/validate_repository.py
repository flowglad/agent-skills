#!/usr/bin/env python3
"""Validate the public Flowglad skill packages and exported OWS assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PROFILE_URI = "https://flowglad.com/ows/profiles/automation/v1"
CATALOG_URI = "https://flowglad.com/ows/catalogs/automation/v1"
ALLOWED_CALLS = {
    "browser-agent:1.0.0@flowglad",
    "code:1.0.0@flowglad",
    "inference:1.0.0@flowglad",
}
FORBIDDEN_INFERENCE_FIELDS = {
    "provider",
    "model",
    "reasoningEffort",
    "maxOutputTokens",
    "maxResultBytes",
}
FORBIDDEN_BROWSER_FIELDS = {
    "promptIdentity",
    "vendorSkillIdentity",
    "toolSetIdentity",
    "modelRoute",
}


def fail(message: str) -> None:
    raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_skill(skill_root: Path) -> None:
    skill_path = skill_root / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{skill_path}: missing YAML frontmatter")
    _, frontmatter_text, body = text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_text)
    if set(frontmatter) != {"name", "description"}:
        fail(f"{skill_path}: frontmatter must contain only name and description")
    if frontmatter["name"] != skill_root.name:
        fail(f"{skill_path}: name must match its directory")
    if not body.strip():
        fail(f"{skill_path}: instructions are empty")

    agent_metadata = yaml.safe_load((skill_root / "agents/openai.yaml").read_text(encoding="utf-8"))
    interface = agent_metadata.get("interface", {})
    short_description = interface.get("short_description", "")
    if not 25 <= len(short_description) <= 64:
        fail(f"{skill_root}/agents/openai.yaml: short_description must be 25-64 characters")
    if f"${skill_root.name}" not in interface.get("default_prompt", ""):
        fail(f"{skill_root}/agents/openai.yaml: default_prompt must mention the skill")


def validate_code_extension(path: Path, task_id: str, extension: dict[str, object]) -> None:
    if "runtime" in extension:
        fail(f"{path}: {task_id} authors compiler-owned runtime")
    resource = extension.get("resource")
    if not isinstance(resource, dict):
        fail(f"{path}: {task_id} has no code resource")
    if "skillId" in resource or "spaceId" in resource:
        fail(f"{path}: {task_id} repeats a compiler-derived resource identity")
    kind = resource.get("kind")
    if kind == "skill-revision" and not resource.get("revisionId"):
        fail(f"{path}: {task_id} has no revisionId")
    if kind not in {"skill-revision", "space-file"}:
        fail(f"{path}: {task_id} has unsupported resource kind {kind!r}")
    if not resource.get("path") or not extension.get("entrypoint"):
        fail(f"{path}: {task_id} must select a path and entrypoint")


def validate_workflow(path: Path) -> None:
    workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
    document = workflow.get("document", {})
    if document.get("dsl") != "1.0.3":
        fail(f"{path}: expected OWS 1.0.3")
    if document.get("metadata", {}).get("fg", {}).get("profile") != PROFILE_URI:
        fail(f"{path}: expected Flowglad automation profile v1")
    endpoint = workflow.get("use", {}).get("catalogs", {}).get("flowglad", {}).get("endpoint", {})
    if endpoint.get("uri") != CATALOG_URI:
        fail(f"{path}: expected the versioned Flowglad catalog")

    tasks = workflow.get("do")
    if not isinstance(tasks, list) or not tasks:
        fail(f"{path}: expected a sequential non-empty do list")
    for task_wrapper in tasks:
        if not isinstance(task_wrapper, dict) or len(task_wrapper) != 1:
            fail(f"{path}: each task must have one task ID")
        task_id, task = next(iter(task_wrapper.items()))
        if task.get("call") not in ALLOWED_CALLS:
            fail(f"{path}: {task_id} uses unsupported call {task.get('call')!r}")
        if not task.get("timeout", {}).get("after"):
            fail(f"{path}: {task_id} has no explicit timeout")
        extension = task.get("with", {}).get("fg", {})
        if task["call"].startswith("code:"):
            validate_code_extension(path, task_id, extension)
        elif task["call"].startswith("inference:"):
            profile = extension.get("profile", {})
            authored = FORBIDDEN_INFERENCE_FIELDS.intersection(profile)
            if authored:
                fail(f"{path}: {task_id} authors inference policy fields {sorted(authored)}")
        elif task["call"].startswith("browser-agent:"):
            profile = extension.get("profile", {})
            authored = FORBIDDEN_BROWSER_FIELDS.intersection(profile)
            if authored:
                fail(f"{path}: {task_id} uses retired browser fields {sorted(authored)}")
            if not profile.get("instructions"):
                fail(f"{path}: {task_id} has no browser instructions")


def validate_starter_package() -> None:
    package = REPOSITORY_ROOT / "skills/author-flowglad-skill/assets/starter-package"
    metadata = json.loads((package / "meta.json").read_text(encoding="utf-8"))
    if metadata.get("name") != "replace-me" or not metadata.get("description"):
        fail("starter package metadata must retain explicit replacement values")
    instructions = (package / "SKILL.template.md").read_text(encoding="utf-8")
    if instructions.startswith("---"):
        fail("starter SKILL.md instructions must not contain YAML frontmatter")
    script = (package / "scripts/main.py").read_text(encoding="utf-8")
    for legacy_marker in ("sys.argv", "__main__", "argparse"):
        if legacy_marker in script:
            fail(f"starter OWS package contains legacy CLI marker {legacy_marker}")
    if "flowglad.entrypoints" not in script or "@entrypoint" not in script:
        fail("starter script must declare an explicit OWS entrypoint")
    test_case = json.loads((package / "tests/main_test.json").read_text(encoding="utf-8"))
    if test_case.get("kind") != "flowglad-ows-code-test-v1":
        fail("starter test must use the OWS verification contract")


def validate_source_lock() -> None:
    lock = json.loads((REPOSITORY_ROOT / "sources.lock.json").read_text(encoding="utf-8"))
    if lock.get("sourceRepository") != "flowglad/provisioning-agent":
        fail("sources.lock.json has the wrong source repository")
    for path, record in lock.get("files", {}).items():
        actual = sha256(REPOSITORY_ROOT / path)
        if actual != record.get("exportedSha256"):
            fail(f"{path}: exported hash does not match sources.lock.json")


def main() -> int:
    try:
        for skill_root in sorted((REPOSITORY_ROOT / "skills").iterdir()):
            if skill_root.is_dir():
                validate_skill(skill_root)
        for path in sorted((REPOSITORY_ROOT / "skills/author-flowglad-ows").rglob("*.ows.yaml")):
            validate_workflow(path)
        validate_starter_package()
        validate_source_lock()
    except (KeyError, TypeError, ValueError, yaml.YAMLError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print("Flowglad public skill repository validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

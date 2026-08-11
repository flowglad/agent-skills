#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
BUILDER = SKILL_ROOT / "scripts" / "build-package-payload.py"
STARTER_PACKAGE = SKILL_ROOT / "assets" / "starter-package"
STARTER_ENTRYPOINTS = SKILL_ROOT / "assets" / "starter-entrypoints.json"


class BuildPackagePayloadTest(unittest.TestCase):
    def prepare_starter(self, root: Path) -> Path:
        package = root / "package"
        shutil.copytree(STARTER_PACKAGE, package)
        (package / "SKILL.template.md").rename(package / "SKILL.md")
        return package

    def run_builder(self, package: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(package),
                "--entrypoints",
                str(STARTER_ENTRYPOINTS),
            ],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_builds_complete_starter_package(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.prepare_starter(Path(directory))

            result = self.run_builder(package)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        files = {item["path"]: item for item in payload["files"]}
        self.assertEqual(files["meta.json"]["role"], "file")
        self.assertEqual(files["meta.json"]["contentType"], "application/json")
        self.assertEqual(files["SKILL.md"]["role"], "instructions")
        self.assertFalse(
            (STARTER_PACKAGE / "SKILL.template.md").read_text(encoding="utf-8").startswith("---")
        )
        self.assertEqual(payload["entrypoints"], json.loads(STARTER_ENTRYPOINTS.read_text()))

    def test_rejects_package_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.prepare_starter(Path(directory))
            (package / "meta.json").unlink()

            result = self.run_builder(package)

        self.assertEqual(result.returncode, 1)
        self.assertIn("package must contain exactly-cased meta.json", result.stderr)


if __name__ == "__main__":
    unittest.main()

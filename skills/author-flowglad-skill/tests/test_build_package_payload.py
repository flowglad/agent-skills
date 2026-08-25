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


class BuildPackagePayloadTest(unittest.TestCase):
    def prepare_starter(self, root: Path) -> Path:
        package = root / "package"
        shutil.copytree(STARTER_PACKAGE, package)
        (package / "SKILL.template.md").rename(package / "SKILL.md")
        return package

    def run_builder(
        self, package: Path, transport: str = "inline"
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(BUILDER),
                str(package),
                "--transport",
                transport,
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
        self.assertEqual(files["tests/main_test.json"]["role"], "test")
        self.assertFalse(
            (STARTER_PACKAGE / "SKILL.template.md").read_text(encoding="utf-8").startswith("---")
        )
        self.assertEqual(payload["entrypoints"], [])
        self.assertIn("contentBase64", files["scripts/main.py"])

    def test_builds_staged_file_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.prepare_starter(Path(directory))

            result = self.run_builder(package, "staged")

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        script = next(item for item in payload["files"] if item["path"] == "scripts/main.py")
        self.assertNotIn("contentBase64", script)
        self.assertGreater(script["sizeBytes"], 0)
        self.assertRegex(script["contentHash"], r"^sha256:[a-f0-9]{64}$")

    def test_ignores_generated_python_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.prepare_starter(Path(directory))
            generated = package / "scripts" / "__pycache__"
            generated.mkdir()
            (generated / "main.cpython-311.pyc").write_bytes(b"generated")

            result = self.run_builder(package)

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(any("__pycache__" in item["path"] for item in payload["files"]))

    def test_rejects_package_without_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = self.prepare_starter(Path(directory))
            (package / "meta.json").unlink()

            result = self.run_builder(package)

        self.assertEqual(result.returncode, 1)
        self.assertIn("package must contain exactly-cased meta.json", result.stderr)


if __name__ == "__main__":
    unittest.main()

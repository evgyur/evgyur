from __future__ import annotations

import base64
import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_profile", ROOT / "scripts" / "generate_profile.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProfileGeneratorTests(unittest.TestCase):
    def test_fixture_summary_excludes_fork_stars(self) -> None:
        import json

        data = json.loads((ROOT / "tests" / "fixtures" / "github.json").read_text())
        stats = MODULE.summarize(data)
        self.assertEqual(stats["stars"], "9")
        self.assertEqual(stats["original_repos"], "2")
        self.assertEqual(stats["top_languages"], "Python · Shell")

    def test_generated_svg_is_valid_and_public_safe(self) -> None:
        import json

        data = json.loads((ROOT / "tests" / "fixtures" / "github.json").read_text())
        portrait = (ROOT / "assets" / "portrait.txt").read_text()
        portrait_image = (ROOT / "assets" / "avatar-portrait.webp").read_bytes()
        svg = MODULE.render_svg(
            MODULE.summarize(data),
            portrait,
            base64.b64encode(portrait_image).decode("ascii"),
        )
        ET.fromstring(svg)
        self.assertNotIn("20.business", svg)
        self.assertNotIn("@iintellect", svg)
        self.assertIn("human20.app", svg)
        self.assertIn("@chip1cr", svg)
        self.assertIn("evgyur.pro", svg)
        self.assertIn("chip@human20", svg)
        self.assertIn("PUBLIC PROFILE", svg)
        self.assertNotIn("gho_", svg)
        self.assertNotIn("/home/", svg)


if __name__ == "__main__":
    unittest.main()

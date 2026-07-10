from __future__ import annotations

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
        portrait = json.loads((ROOT / "assets" / "portrait-glyphs.json").read_text())
        svg = MODULE.render_svg(MODULE.summarize(data), portrait)
        ET.fromstring(svg)
        self.assertNotIn("20.business", svg)
        self.assertNotIn("@iintellect", svg)
        self.assertIn("chip@human20.app", svg)
        self.assertNotIn("evgyur@human20.app", svg)
        self.assertIn("human20.app", svg)
        self.assertIn("@chip1cr", svg)
        self.assertIn("evgyur.pro", svg)
        self.assertIn("ASCII PORTRAIT", svg)
        self.assertNotIn("data:image", svg)
        self.assertNotIn("<image", svg)
        self.assertEqual(svg.count('class="portraitGlyph"'), 2610)
        self.assertIn('Evgeny &quot;Chip&quot; Yurchenko', svg)
        self.assertNotIn(">chip@human20<", svg)
        self.assertIn("PUBLIC PROFILE", svg)
        self.assertNotIn("gho_", svg)
        self.assertNotIn("/home/", svg)


if __name__ == "__main__":
    unittest.main()

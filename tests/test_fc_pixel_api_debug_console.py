import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "fc-pixel-api-debug-console"


class FcPixelApiDebugConsoleSkillTests(unittest.TestCase):
    def test_skill_exists_with_discoverable_frontmatter(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        self.assertTrue(skill_md.startswith("---\n"))
        frontmatter = re.search(r"^---\n(.*?)\n---", skill_md, re.DOTALL).group(1)
        self.assertIn("name: fc-pixel-api-debug-console", frontmatter)
        self.assertIn("description: Use when", frontmatter)
        self.assertIn("API debug", frontmatter)
        self.assertIn("FC Pixel", frontmatter)
        self.assertIn("single HTML", frontmatter)

    def test_skill_requires_fc_supermario_and_ui_dependency(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        required_terms = [
            "fc-supermario-pixel-html",
            "$fc-supermario-pixel-html",
            "$ui-ux-pro-max",
            "Do not fetch external Mario",
            "data:image/png;base64",
            "image-rendering: pixelated",
        ]
        for term in required_terms:
            self.assertIn(term, skill_md)

    def test_skill_captures_debug_console_interaction_rules(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        required_terms = [
            "window.location.origin",
            "relative paths",
            "/token",
            "Authorization",
            "request headers",
            "response headers",
            "HTTP status",
            "exception",
            "access_token",
            "localStorage",
            "finally",
            "disabled",
            "fireball",
            "question block",
            "mushroom",
            "parabolic",
            "prefers-reduced-motion",
        ]
        for term in required_terms:
            self.assertIn(term, skill_md)

    def test_skill_warns_against_visual_noise_and_proxy_by_default(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")

        required_terms = [
            "Do not add environment dropdowns",
            "Do not require a local proxy",
            "clean background",
            "decorative bricks",
            "one row",
            "avoid covering the active block",
            "no external image dependency",
        ]
        for term in required_terms:
            self.assertIn(term, skill_md)


if __name__ == "__main__":
    unittest.main()

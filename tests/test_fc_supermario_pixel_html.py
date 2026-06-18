import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "fc-supermario-pixel-html"
EXTRACT = SKILL / "scripts" / "extract_sprites.py"
BUILD_DEMO = SKILL / "scripts" / "build_demo.py"
SPRITES = SKILL / "assets" / "sprites" / "sprites.json"


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FcSupermarioPixelHtmlTests(unittest.TestCase):
    def test_skill_declares_ui_ux_pro_max_dependency(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        agent_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertIn("ui-ux-pro-max", skill_md)
        self.assertIn("$ui-ux-pro-max", skill_md)
        self.assertIn("static HTML", skill_md)
        self.assertIn("ui-ux-pro-max", agent_yaml)

    def test_skill_scope_is_interactive_ui_not_only_game_scene(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        style = (SKILL / "references" / "style-guide.md").read_text(encoding="utf-8")
        animation = (SKILL / "references" / "animation-scenes.md").read_text(
            encoding="utf-8"
        )
        patterns = (SKILL / "references" / "ui-patterns.md").read_text(
            encoding="utf-8"
        )

        required_skill_terms = [
            "interactive UI",
            "background animation",
            "buttons",
            "headings",
            "icons",
            "$ui-ux-pro-max",
        ]
        for term in required_skill_terms:
            self.assertIn(term, skill_md)

        self.assertIn("UI composition", style)
        self.assertIn("Components", style)
        self.assertIn("Sprite icons", style)
        self.assertIn("UI layer", animation)
        self.assertIn("background choreography", animation)
        self.assertIn("button", patterns)
        self.assertIn("tabs", patterns)
        self.assertIn("cards", patterns)

    def test_sprite_manifest_has_required_categories_and_unique_outputs(self):
        manifest = json.loads(SPRITES.read_text(encoding="utf-8"))

        self.assertEqual(manifest["version"], 1)
        categories = {sprite["category"] for sprite in manifest["sprites"]}
        self.assertTrue({"character", "enemy", "item", "effect", "level"} <= categories)
        self.assertGreaterEqual(len(manifest["sprites"]), 50)

        outputs = [sprite["output"] for sprite in manifest["sprites"]]
        self.assertEqual(len(outputs), len(set(outputs)))
        for sprite in manifest["sprites"]:
            self.assertIn("id", sprite)
            self.assertIn("source", sprite)
            self.assertIn("bbox", sprite)
            self.assertEqual(len(sprite["bbox"]), 4)

    def test_manifest_coordinates_are_inside_source_images(self):
        module = load_module(EXTRACT, "extract_sprites")
        manifest = module.load_manifest(SPRITES)
        sources = module.load_sources(SKILL)

        errors = module.validate_manifest(manifest, sources)

        self.assertEqual(errors, [])

    def test_extract_sprites_check_and_build_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "skill"
            shutil.copytree(SKILL, work)
            temp_contact_sheet = work / "assets" / "sprites" / "contact-sheet.png"
            if temp_contact_sheet.exists():
                temp_contact_sheet.unlink()

            check = subprocess.run(
                [sys.executable, str(work / "scripts" / "extract_sprites.py"), "--check"],
                cwd=work,
                text=True,
                capture_output=True,
            )
            self.assertEqual(check.returncode, 0, check.stderr + check.stdout)
            self.assertFalse(temp_contact_sheet.exists())

            build = subprocess.run(
                [sys.executable, str(work / "scripts" / "build_demo.py")],
                cwd=work,
                text=True,
                capture_output=True,
            )
            self.assertEqual(build.returncode, 0, build.stderr + build.stdout)

            html = (work / "dist" / "index.html").read_text(encoding="utf-8")
            self.assertIn("Pixel UI Command Center", html)
            self.assertIn("World 1-1", html)
            self.assertIn("prefers-reduced-motion", html)
            self.assertIn("image-rendering: pixelated", html)
            self.assertIn("data-action=\"pause\"", html)
            self.assertIn("data-action=\"replay\"", html)
            self.assertIn("data-action=\"speed\"", html)
            self.assertIn("data-view=\"overview\"", html)
            self.assertIn("data-view=\"scene\"", html)
            self.assertIn("data-icon=\"coin\"", html)
            self.assertIn("background animation", html)
            self.assertIn("level.world-1-1.overworld", html)
            self.assertNotIn("level.world-1-1.full", html)
            self.assertIn("walkMax", html)
            self.assertIn("runMax", html)
            self.assertIn("GROUND_Y", html)
            self.assertIn("enemy.goomba.ground.walk.0", html)
            self.assertIn("enemy.koopa.green.walk.0", html)

            extract = subprocess.run(
                [sys.executable, str(work / "scripts" / "extract_sprites.py")],
                cwd=work,
                text=True,
                capture_output=True,
            )
            self.assertEqual(extract.returncode, 0, extract.stderr + extract.stdout)
            self.assertTrue(temp_contact_sheet.is_file())

    def test_demo_physics_and_sprite_rules_are_documented(self):
        animation = (SKILL / "references" / "animation-scenes.md").read_text(
            encoding="utf-8"
        )
        style = (SKILL / "references" / "style-guide.md").read_text(encoding="utf-8")

        self.assertIn("grounded", animation)
        self.assertIn("acceleration", animation)
        self.assertIn("walkMax", animation)
        self.assertIn("runMax", animation)
        self.assertIn("overworld", style)
        self.assertIn("underground bonus", style)

    def test_interaction_choreography_rules_are_documented(self):
        animation = (SKILL / "references" / "animation-scenes.md").read_text(
            encoding="utf-8"
        )

        required_terms = [
            "single timeline",
            "coin disappears",
            "question block",
            "mushroom emerges",
            "Goomba becomes squashed",
            "Koopa becomes shell",
            "3 seconds",
            "stomp rebound",
            "gravity acceleration",
            "parabolic",
        ]
        for term in required_terms:
            self.assertIn(term, animation)

    def test_pipe_crop_has_transparent_background_after_extraction(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "skill"
            shutil.copytree(SKILL, work)

            subprocess.run(
                [sys.executable, str(work / "scripts" / "extract_sprites.py")],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )

            from PIL import Image

            pipe = Image.open(
                work / "assets" / "sprites" / "items" / "pipe-top-0.png"
            ).convert("RGBA")
            transparent_pixels = sum(
                1
                for pixel in pipe.getdata()
                if pixel[3] == 0
            )
            self.assertGreater(transparent_pixels, 0)

            forbidden_backgrounds = {
                (92, 148, 252),
                (200, 76, 12),
                (252, 188, 176),
            }
            opaque_background_pixels = [
                pixel
                for pixel in pipe.getdata()
                if pixel[3] and pixel[:3] in forbidden_backgrounds
            ]
            self.assertEqual(opaque_background_pixels, [])


if __name__ == "__main__":
    unittest.main()

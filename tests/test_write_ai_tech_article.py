import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "write-ai-tech-article"
VALIDATOR = SKILL / "scripts" / "validate_article.py"


def load_validator():
    spec = importlib.util.spec_from_file_location("validate_article", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_package(root, body, image_names):
    assets = root / "assets"
    assets.mkdir()
    for name in image_names:
        (assets / name).write_bytes(b"image")
    (root / "evidence.md").write_text("# Evidence\n", encoding="utf-8")
    (root / "image-manifest.md").write_text("# Images\n", encoding="utf-8")
    article = root / "article.md"
    article.write_text(body, encoding="utf-8")
    return article


class WriteAiTechArticleSkillTests(unittest.TestCase):
    def test_skill_has_discoverable_frontmatter_and_required_references(self):
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        agent_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")

        self.assertTrue(skill_md.startswith("---\nname: write-ai-tech-article\n"))
        for term in [
            "Chinese AI and technology articles",
            "Toutiao",
            "Baijiahao",
            "$imagegen",
            "references/editorial-style.md",
            "references/source-policy.md",
            "references/platform-and-output.md",
            "references/visual-guide.md",
        ]:
            self.assertIn(term, skill_md)
        self.assertIn("$write-ai-tech-article", agent_yaml)

    def test_source_policy_blocks_internal_octopus_material(self):
        source_policy = (SKILL / "references" / "source-policy.md").read_text(
            encoding="utf-8"
        )

        for term in [
            "raw/projects-octoparse/",
            "octopus-projects/",
            "wiki/octopus-services/",
            "tools/out/",
            "marked `Internal`",
            "raw/tech-daily/",
            "sole default exception",
            "Treat the Wiki as read-only",
        ]:
            self.assertIn(term, source_policy)

    def test_valid_article_package_passes(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prose = "技术变化需要事实支持，也需要解释机制和现实影响。" * 35
            images = ["cover.png", "figure-01.png", "figure-02.png"]
            image_markdown = "\n".join(
                f"![说明图片 {index}](assets/{name})"
                for index, name in enumerate(images, start=1)
            )
            article = write_package(root, f"# 标题\n\n{prose}\n\n{image_markdown}\n", images)

            errors = validator.validate_article(article, "article")

            self.assertEqual(errors, [])

    def test_valid_post_package_passes(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prose = "这项技术变化有明确证据。真正重要的不是宣传口号，而是成本、可靠性和普通用户能否实际受益。" * 3
            article = write_package(
                root,
                f"# 短帖标题\n\n{prose}\n\n![产品实物](assets/cover.png)\n",
                ["cover.png"],
            )

            errors = validator.validate_article(article, "post")

            self.assertEqual(errors, [])

    def test_validator_rejects_missing_images_placeholders_and_private_paths(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prose = "这是需要核验的技术判断。" * 60
            article = write_package(
                root,
                "# 标题\n\n"
                f"{prose}\n\nTODO /Users/stephen/raw/projects-octoparse\n\n"
                "![](assets/missing.png)\n",
                [],
            )

            errors = validator.validate_article(article, "article")

            combined = "\n".join(errors)
            self.assertIn("expected 3-4", combined)
            self.assertIn("empty alt text", combined)
            self.assertIn("does not exist", combined)
            self.assertIn("Unresolved placeholder", combined)
            self.assertIn("Private or restricted path marker", combined)

    def test_validator_rejects_octopus_project_directory_alias(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            prose = "经过核验的公开技术事实可以形成文章。" * 45
            images = ["cover.png", "figure-01.png", "figure-02.png"]
            image_markdown = "\n".join(
                f"![公开资料配图 {index}](assets/{name})"
                for index, name in enumerate(images, start=1)
            )
            article = write_package(
                root,
                f"# 标题\n\n{prose}\n\noctopus-projects/internal\n\n{image_markdown}\n",
                images,
            )

            errors = validator.validate_article(article, "article")

            self.assertTrue(
                any("Private or restricted path marker" in error for error in errors)
            )


if __name__ == "__main__":
    unittest.main()

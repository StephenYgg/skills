import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "isolate-git-merge-conflicts"


class IsolateGitMergeConflictsSkillTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        cls.openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

    def test_skill_has_discoverable_metadata(self):
        self.assertTrue(self.skill_md.startswith("---\n"))
        frontmatter = re.search(
            r"^---\n(.*?)\n---", self.skill_md, re.DOTALL
        ).group(1)

        self.assertIn("name: isolate-git-merge-conflicts", frontmatter)
        self.assertIn("when conflicts are expected or detected", frontmatter)
        self.assertIn("display_name: \"Git 合并冲突隔离\"", self.openai_yaml)
        self.assertIn("$isolate-git-merge-conflicts", self.openai_yaml)

    def test_skill_protects_source_and_existing_branches(self):
        required_terms = [
            "source HEAD",
            "worktree status",
            "<source-branch>_merge",
            "numeric suffix",
            "Never reset, overwrite, delete, or force-push",
            "never derive `_merge_merge`",
            "Preserve unrelated staged, unstaged, and untracked work",
            "Resolve conflicts only on the isolation branch",
        ]

        for term in required_terms:
            self.assertIn(term, self.skill_md)

    def test_skill_defines_confirmation_and_safe_replay(self):
        required_terms = [
            "默认：创建",
            "An explicit rejection",
            "`按默认`",
            "later directs the Agent to continue",
            "Mere silence is not permission",
            "abort only that merge/rebase/cherry-pick",
            "replay the operation there",
        ]

        for term in required_terms:
            self.assertIn(term, self.skill_md)

    def test_skill_preserves_git_authority_and_syncs_by_merge(self):
        required_terms = [
            "never supplies commit or push authority",
            "Return to the source branch only after",
            "默认：同步",
            "Merge the source branch into the isolation branch",
            "do not cherry-pick by default",
            "Push the isolation branch only when push is explicitly authorized",
        ]

        for term in required_terms:
            self.assertIn(term, self.skill_md)


if __name__ == "__main__":
    unittest.main()

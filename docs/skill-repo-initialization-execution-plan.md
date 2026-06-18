# Skill Repository Initialization Execution Plan

## Goal

Initialize `D:\Development\Skills` as a repository for agent skills using the architecture pattern from Anthropic's official skills repository.

## Steps

1. Add repository skeleton
   - Create `.claude-plugin/`
   - Create `skills/`
   - Create `spec/`
   - Create `template/`
   - Create `scripts/`

2. Add root metadata
   - Add `.gitignore` with common local noise.
   - Add `README.md` describing repository layout and workflow.

3. Add plugin marketplace metadata
   - Add `.claude-plugin/marketplace.json`.
   - Keep plugin list empty until real skills exist, instead of listing nonexistent paths.

4. Add skill template
   - Add `template/SKILL.md`.
   - Follow the official minimal frontmatter shape: `name` and `description`.

5. Add spec pointer
   - Add `spec/agent-skills-spec.md`.
   - Point to `https://agentskills.io/specification`.

6. Add validation script
   - Add `scripts/validate-skills.ps1`.
   - Check each `skills/*/SKILL.md` exists.
   - Check frontmatter includes `name` and `description`.
   - Check skill folder name matches frontmatter `name`.
   - Report empty `skills/` as valid.

7. Verify
   - Run `scripts/validate-skills.ps1`.
   - Run `git status --short`.

## Files To Create

```text
.claude-plugin/marketplace.json
.gitignore
README.md
docs/skill-repo-initialization-analysis-report.md
docs/skill-repo-initialization-execution-plan.md
scripts/validate-skills.ps1
skills/.gitkeep
spec/agent-skills-spec.md
template/SKILL.md
```

## Approval Gate

Wait for the user to say "开始" or otherwise approve before creating the repository skeleton beyond these two planning documents.


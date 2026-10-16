# Octoparse Skills

Octoparse-specific data warehouse workflows. General-purpose skills remain in
the repository's `skills/` directory. This collection does not move or replace
existing skills.

| Skill | Purpose |
| --- | --- |
| [octoparse-cdc-onboarding](octoparse-cdc-onboarding/SKILL.md) | Coordinate code analysis, source inspection, DDL, DataHub configuration and acceptance |
| [octoparse-warehouse-source-analysis](octoparse-warehouse-source-analysis/SKILL.md) | Explain business tables and fields using application code plus dbbb |
| [octoparse-starrocks-cdc-schema](octoparse-starrocks-cdc-schema/SKILL.md) | Design version-compatible CDC target DDL with business column comments |
| [octoparse-datahub-job-admin](octoparse-datahub-job-admin/SKILL.md) | Manage DataHub Jobs, Plans and Steps using bccc |
| [octoparse-cdc-verify-repair](octoparse-cdc-verify-repair/SKILL.md) | Monitor snapshot/incremental progress and diagnose incomplete or failed syncs |

## Installation

Install a directory symlink for each skill into the global Codex skill directory:

```bash
python3 octoparse-skills/install.py
python3 octoparse-skills/install.py --apply
```

The first command previews changes. The second creates the links. Use
`--destination /path/to/skills` for another installation root. Existing correct
links are retained; conflicting files/directories are never replaced.
Keep this checkout at a stable path because the installed links point to it.

## Maintenance

- Skills describe decisions and safety boundaries; production schemas and
  deployment configurations belong in `octopus.datahub.service/docs`.
- The sanitized AgentHub/Advisor examples are dated evidence, not current
  infrastructure configuration. Re-read live code, schemas and versions.
- Never archive database passwords, access tokens, proxy credentials, full
  failed rows, or private deployment endpoints in this collection.
- Creating/installing skills does not authorize commits or pushes.
- Helper tests use mocked CLIs and temporary files, never production resources:

```bash
python3 -m unittest discover -s octoparse-skills/tests -v
```

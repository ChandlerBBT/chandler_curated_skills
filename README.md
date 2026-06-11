# chandler_curated_skills

Chandler's curated Codex skills.

This repository currently contains:

- `artifact-manager`: keeps research deliverables organized with stable folders, versions, changelog, artifact index, and release packages.

## Repository Layout

```text
chandler_curated_skills/
|-- skills/
|   `-- artifact-manager/
|       `-- SKILL.md
`-- docs/
    `-- artifact-manager.md
```

## Install With Codex

In Codex, ask:

```text
Install the artifact-manager skill from:
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/artifact-manager
```

Restart Codex after installation so the new skill can be loaded.

## Install With The Skill Installer Script

If your Codex environment includes the built-in `skill-installer` helper, run:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo ChandlerBBT/chandler_curated_skills \
  --path skills/artifact-manager
```

On Windows PowerShell, the same command is typically:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo ChandlerBBT/chandler_curated_skills `
  --path skills/artifact-manager
```

Restart Codex after installation.

## Manual Install

Copy `skills/artifact-manager/` into your global Codex skills directory.

Common locations:

- Windows: `%USERPROFILE%\.codex\skills\artifact-manager\`
- macOS/Linux: `~/.codex/skills/artifact-manager/`

Some Codex or agent setups may use `.agents/skills` instead:

- Windows: `%USERPROFILE%\.agents\skills\artifact-manager\`
- macOS/Linux: `~/.agents/skills/artifact-manager/`

Restart Codex after copying the folder.

## About artifact-manager

Read the first-use guide here:

- [`docs/artifact-manager.md`](docs/artifact-manager.md)

Short version: this skill is meant to auto-trigger when Codex creates, edits, exports, organizes, or packages research artifacts such as reports, Markdown files, HTML files, charts, PPT assets, data tables, and research notes. You can also manually mention `artifact-manager` when you want to force the workflow.

## Updating A Skill

To update an existing installation, reinstall from the same path or replace the local `artifact-manager` folder with the latest repository version, then restart Codex.

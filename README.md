# chandler_curated_skills

Chandler's curated Codex skills.

This repository currently contains:

- `artifact-manager`: keeps research deliverables organized with stable folders, versions, changelog, artifact index, and release packages.
- `stock-analysis` (`stock_analysis`): disciplined stock research workflow covering fundamentals, financial quality, valuation, technical timing, catalysts, risk controls, and failure-review rule writeback.

## Repository Layout

```text
chandler_curated_skills/
|-- skills/
|   |-- artifact-manager/
|   |   `-- SKILL.md
|   `-- stock-analysis/
|       |-- SKILL.md
|       |-- agents/
|       `-- references/
`-- docs/
    |-- artifact-manager.md
    `-- stock-analysis.md
```

## Install With Codex

In Codex, ask:

```text
Install the artifact-manager skill from:
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/artifact-manager
```

For stock research, ask:

```text
Install the stock-analysis skill from:
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/stock-analysis
```

Restart Codex after installation so the new skill can be loaded.

## Install With The Skill Installer Script

If your Codex environment includes the built-in `skill-installer` helper, run:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo ChandlerBBT/chandler_curated_skills \
  --path skills/artifact-manager
```

For `stock-analysis`:

```bash
python ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo ChandlerBBT/chandler_curated_skills \
  --path skills/stock-analysis
```

On Windows PowerShell, the same command is typically:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo ChandlerBBT/chandler_curated_skills `
  --path skills/artifact-manager
```

For `stock-analysis`:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo ChandlerBBT/chandler_curated_skills `
  --path skills/stock-analysis
```

Restart Codex after installation.

## Manual Install

Copy `skills/artifact-manager/` into your global Codex skills directory.
For stock research, copy `skills/stock-analysis/`.

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

## About stock-analysis

Read the first-use guide here:

- [`docs/stock-analysis.md`](docs/stock-analysis.md)

Short version: this skill is meant to auto-trigger for stock research workflows such as screening, fundamentals, financial quality, valuation, technical timing, catalyst validation, risk controls, and failure-review rule writeback. Its display name is `stock_analysis`; the internal Codex skill name is `stock-analysis` because skill names are normalized to hyphen-case.

## Updating A Skill

To update an existing installation, reinstall from the same path or replace the local `artifact-manager` folder with the latest repository version, then restart Codex.

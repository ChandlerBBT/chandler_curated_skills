---
name: artifact-manager
description: Use this skill whenever the user creates, edits, rewrites, updates, organizes, packages, reviews, or exports research artifacts, reports, Markdown files, HTML files, charts, slide assets, data tables, analysis notes, or deliverables. Automatically manage directories, versions, changelog, artifact index, and release packages. Prevent scattered files and uncontrolled overwrites.
---

# Artifact Manager

## Purpose

Manage all Codex-generated research artifacts with stable folders, versions, changelog, index, and release packaging.

## Auto-trigger

Use this skill whenever the task involves:

- generating reports
- modifying reports
- creating HTML
- creating Markdown
- creating charts
- creating PPT assets
- creating data tables
- organizing research outputs
- packaging a deliverable
- cleaning duplicate drafts
- comparing versions

## Project initialization

If the current project does not already contain artifact management folders, create:

- `00_inbox/`
- `01_briefs/`
- `02_working/`
- `02_working/report/`
- `02_working/html/`
- `02_working/assets/`
- `02_working/data/`
- `03_reviews/`
- `04_releases/`
- `05_archive/`
- `changelog/`
- `index/`

Also create:

- `changelog/CHANGELOG.md`
- `index/artifact_index.md`

## File placement rules

Never leave generated artifacts in the repository root unless a project convention explicitly requires it, such as a GitHub repository `README.md`.

Use:

- drafts and editable files: `02_working/`
- review notes: `03_reviews/`
- stable outputs: `04_releases/`
- old drafts: `05_archive/`
- changelog: `changelog/CHANGELOG.md`
- registry: `index/artifact_index.md`

## Naming rule

Use:

`YYYY-MM-DD_topic_type_vX.Y.ext`

Examples:

- `2026-06-11_aios_report_v0.1.md`
- `2026-06-11_aios_dashboard_v0.2.html`
- `2026-06-11_aios_chart_v0.1.png`

## Version rule

- Draft versions use `v0.x`
- First stable release is `v1.0`
- Small revisions increase decimal version: `v1.1`
- Major restructuring creates new major version: `v2.0`
- Never overwrite files in `04_releases/`; create a new version instead

## Required behavior before editing

Before editing an existing artifact:

1. Locate the current version.
2. Identify whether the file is working draft or release.
3. If it is a release file, do not overwrite it.
4. Decide whether to update working draft or create a new version.

## Required behavior after every artifact task

Always update:

1. `changelog/CHANGELOG.md`
2. `index/artifact_index.md`

Then report:

- created files
- modified files
- archived files
- current version
- next recommended action

## Default output format

At the end of every task, output:

```text
本轮产物管理结果：
- created:
- modified:
- archived:
- current version:
- next action:
```

## Cleanup rule

When asked to clean or organize, do not delete files. Move obsolete files to `05_archive/` and record the action in changelog.

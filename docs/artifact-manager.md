# artifact-manager

`artifact-manager` is a Codex skill for keeping research project outputs from turning into scattered drafts.

It helps Codex manage:

- reports and Markdown drafts
- HTML deliverables and dashboards
- charts and image assets
- PPT or slide assets
- data tables, CSV, Excel, JSON, and SQL outputs
- research notes and review notes
- release packages

## What It Does

When a project has no artifact structure yet, the skill asks Codex to initialize folders like:

```text
00_inbox/
01_briefs/
02_working/
03_reviews/
04_releases/
05_archive/
changelog/
index/
```

It then guides Codex to:

- avoid leaving generated files in the project root
- place drafts under `02_working/`
- place stable outputs under `04_releases/`
- move old drafts to `05_archive/` instead of deleting them
- keep `changelog/CHANGELOG.md` updated
- keep `index/artifact_index.md` updated
- name files with a clear date, topic, type, and version

## Is It Automatic Or Manual?

It is designed to be automatic.

After installation and a Codex restart, Codex should use it whenever your task involves creating, editing, rewriting, exporting, organizing, reviewing, or packaging research artifacts.

Examples that should trigger it:

```text
帮我生成一份研究报告
```

```text
把这个 HTML 报告改成可发布版本
```

```text
整理当前项目目录，版本太乱了
```

```text
把这些图表和数据表打包成 release
```

You can also call it manually by name:

```text
使用 artifact-manager 帮我整理这个项目的产物
```

## What It Will Not Do

- It should not delete old files during cleanup.
- It should not overwrite stable release files.
- It should not blindly rename every historical file if that would break traceability.
- It should not replace human judgment about which artifact is the final business version.

## Recommended First Test

After installing and restarting Codex, open a new research project folder and ask:

```text
请生成一份 Markdown 研究报告，并按 artifact-manager 管理产物。
```

Expected result:

- Codex creates the artifact folders if missing.
- The report is placed under `02_working/report/` or `04_releases/`, depending on your request.
- `changelog/CHANGELOG.md` is updated.
- `index/artifact_index.md` is updated.
- Codex ends with a short management summary.

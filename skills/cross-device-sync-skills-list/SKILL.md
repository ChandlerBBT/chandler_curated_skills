---
name: cross-device-sync-skills-list
description: Maintain and synchronize Codex skills across devices through a private GitHub repository. Use when the user wants to inventory local Codex skills, back up skills, create or use a private repo such as chandler_codex_skills_list, restore skills onto a new device, compare local and cloud skill changes, or set up ongoing cross-device skill sync.
---

# Cross-device Skills Sync

Use this skill to keep user-authored Codex skills portable across devices. It maintains a GitHub-backed catalog plus source copies for syncable skills.

Repository split:

- Publish this management skill itself to `chandler_curated_skills`.
- Store each user's generated skill inventory and syncable skill sources in `chandler_codex_skills_list`.

## Ground Rules

- Treat user skills as source code. Back them up before overwriting or deleting.
- Sync user-managed skills from `$HOME/.agents/skills` and `$CODEX_HOME/skills`, excluding `$CODEX_HOME/skills/.system`.
- Record system and plugin-bundled skills in the inventory, but do not copy or reinstall them as user skills.
- A plain skill cannot run continuously by itself. For automatic sync, install an OS scheduled task, a Codex automation, or an explicit project hook that invokes the bundled script.
- A list alone cannot reinstall local custom skills on another device. Keep both `skills-list.json` and source copies under `skill_sources/`.
- Do not store credentials, `.env` files, private keys, `auth.json`, caches, build outputs, or virtual environments in the sync repo.
- Prefer a private GitHub repository for the skills catalog. Default catalog repo name: `chandler_codex_skills_list`.
- Keep the management skill source separate in a curated-skills repo such as `chandler_curated_skills`.

## Quick Workflow

Run the bundled script from this skill:

```bash
python scripts/sync_skills.py status
python scripts/sync_skills.py sync --repo ChandlerBBT/chandler_codex_skills_list
python scripts/sync_skills.py install --repo ChandlerBBT/chandler_codex_skills_list
python scripts/sync_skills.py publish-self --repo ChandlerBBT/chandler_curated_skills
```

When the user has not configured a repo:

1. Detect whether `~/.codex/cross-device-sync-skills-list.json` exists.
2. If not, ask for or infer the GitHub repo full name. Offer `ChandlerBBT/chandler_codex_skills_list` as the default when appropriate.
3. Check whether the repo exists with the available GitHub connector or GitHub CLI.
4. If it exists, run `install` first on a new device, then `sync`.
5. If it does not exist, create a private repo if a GitHub write mechanism is available. Otherwise, guide the user to authorize GitHub or create the repo, then run `sync`.

## Commands

- `scan`: print the local skill inventory without changing files.
- `prepare`: create or update the local sync repository folder with the current inventory and copied syncable skill sources.
- `sync`: pull the sync repo if possible, prepare the latest local snapshot, commit, and push.
- `install`: pull the sync repo and install remote skill sources into `$HOME/.agents/skills`.
- `status`: compare local skills with the last prepared repo snapshot.
- `configure`: save repo settings to `~/.codex/cross-device-sync-skills-list.json`.
- `publish-self`: prepare a local package of this management skill for the curated skills repository.

## Conflict Policy

- Before overwriting a local skill during `install`, copy the existing folder to `$CODEX_HOME/backups/skills-sync/<timestamp>/`.
- If a local skill and remote skill both changed, keep the backup and install the remote version only when the user asked to sync from cloud or passed `--force`.
- Treat missing local skills during `sync` as deletions only after the repo has been pulled successfully. This avoids wiping cloud state from a stale device.
- Keep `change-log.jsonl` in the sync repo so deletions and updates are auditable.

## GitHub Handling

Use the best available path:

1. GitHub connector for existing repo file reads/writes when available.
2. GitHub CLI if installed and authenticated.
3. Git with the user's credential manager for clone/push/pull.
4. GitHub REST API only when `GITHUB_TOKEN` or `GH_TOKEN` is present.

If no GitHub write path exists, stop after preparing the local sync repository and explain exactly what authorization is missing.

Do not create the catalog repo inside the curated skills repo. They serve different purposes:

- `chandler_curated_skills`: distribution source for this reusable sync skill.
- `chandler_codex_skills_list`: private device-specific skills catalog and source backup.

## Files Created In The Sync Repo

- `skills-list.json`: machine-readable inventory and hashes.
- `skills-list.md`: human-readable skill catalog.
- `skill_sources/`: copied source folders for syncable user skills.
- `change-log.jsonl`: append-only local change log.
- `README.md`: short repo purpose and restore instructions.

## Safety Checks

Before pushing:

- Confirm the target repo is private when metadata is available.
- Show which skills will be added, updated, or removed.
- Never include skipped secret-like files in `skill_sources/`.

After installing:

- Tell the user to restart Codex or use Force Reload Skills if newly installed skills do not appear.

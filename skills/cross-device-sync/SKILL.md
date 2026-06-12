---
name: cross-device-sync
description: Maintain and synchronize Codex skills plus safe Codex-related configuration across devices through a private GitHub repository. Use when the user wants to inventory or restore skills, Codex config.toml settings, MCP server links, plugin settings, SSH host aliases, Git remotes, or cross-device Codex setup state. Stores secret-free manifests and redacted templates only; never syncs private keys, tokens, auth files, passwords, or raw credentials.
---

# Cross-device Sync

Use this skill to make a Codex setup portable across devices. It maintains a private GitHub-backed snapshot of:

- user-managed Codex skills and their source folders
- redacted Codex configuration templates
- MCP server definitions and links with credentials removed
- installed/enabled plugin and marketplace settings
- SSH host aliases and Git remote links
- restore notes for rebuilding device-local secrets safely

## Repository Split

- Publish this reusable management skill itself to a curated skills repository, such as `chandler_curated_skills`.
- Store each user's generated sync catalog in that user's own private GitHub repository.
- For new users, default the private sync repo name to `<github-owner>_codex_sync`, such as `jack_codex_sync`.
- For existing users, keep their configured repository name if one already exists.

## Safety Model

Treat sync output as source-controlled infrastructure notes, not a secret manager.

Never copy these into the sync repo:

- `auth.json`, OAuth sessions, cookies, browser profiles, credential caches
- GitHub PATs, API keys, passwords, private keys, `.env` files
- SSH private key contents
- raw MCP URLs when query parameters or path fragments contain credentials
- machine-local caches, build outputs, virtual environments, `node_modules`, `.git`

Allowed by default:

- skill source folders after excluded files are filtered
- `config.toml` redacted templates
- MCP names, commands, transports, and redacted URLs
- SSH `Host`, `HostName`, `User`, `Port`, and redacted `IdentityFile` references
- Git remote URLs with embedded credentials removed
- plugin and marketplace names/settings with secrets removed

## Quick Workflow

Run the bundled script:

```bash
python scripts/sync_codex.py status
python scripts/sync_codex.py diff
python scripts/sync_codex.py configure --owner YOUR_GITHUB_OWNER
python scripts/sync_codex.py sync
python scripts/sync_codex.py install-skills
```

First run:

1. Detect whether `~/.codex/cross-device-sync.json` exists.
2. If not, ask for or infer the GitHub owner.
3. Offer `<owner>_codex_sync` as the default private repo name, but let the user change it.
4. Create the private repo if a GitHub write mechanism is available.
5. Prepare and push the first snapshot.

## Commands

- `scan`: print local skills and safe config inventory without changing files.
- `prepare`: update the local sync repository folder.
- `sync`: pull, prepare, commit, and push the snapshot.
- `diff`: compare the current device with the latest local/cloud snapshot and write a conflict report.
- `install-skills`: install syncable skills from the sync repo into `$HOME/.agents/skills`.
- `status`: compare local skills with the latest local snapshot.
- `configure`: save repo settings to `~/.codex/cross-device-sync.json`.
- `bootstrap`: infer or accept a GitHub owner, save config, optionally create the private sync repo, then prepare the first snapshot.
- `publish-self`: prepare this management skill for a curated skills repository.

## Output In The Private Sync Repo

- `skills-list.json`: machine-readable skill inventory and hashes.
- `skills-list.md`: readable skill catalog.
- `skill_sources/`: copied source folders for syncable user skills.
- `config/codex-config-summary.json`: parsed, secret-free Codex configuration inventory.
- `config/codex-config-redacted.toml`: redacted config template.
- `config/mcp-servers.json`: MCP server inventory with credentials removed.
- `config/ssh-config-summary.json`: SSH host alias inventory.
- `config/git-remotes.json`: Git remotes with credentials removed.
- `config/restore-notes.md`: what must be re-authenticated or recreated locally.
- `change-log.jsonl`: append-only sync log.
- `README.md`: snapshot purpose and restore instructions.

## Restore Policy

- Act as a restore guide after installation and restart. Do not merely report what exists in the snapshot; explain what was restored, what still needs user input, and what is intentionally blocked by the safety model.
- Skills are restorable automatically. Install or update syncable skills from the cloud snapshot into `$HOME/.agents/skills` without asking when there is no meaningful local conflict.
- If an existing local skill differs from the cloud version, back it up when that is clearly safe. Ask the user how to resolve the conflict when both sides appear intentionally edited, when the backup would be ambiguous, or when replacing it could discard user work.
- MCP servers, connector auth, API keys, OAuth sessions, SSH private keys, and other secrets are not automatically restored. When a redacted MCP entry or auth-dependent setting is found, identify the missing item by name and guide the user to provide the token/key, set an environment variable, or re-authorize the provider.
- For MCP entries with redacted URLs, generate the exact local config shape with placeholders and ask for the missing token or credential. If the user provides the credential in the current session, apply it to the local config carefully without printing the secret back.
- Config restore is advisory by default. Do not overwrite another device's `config.toml` or SSH config automatically.
- When the user asks to restore config, generate a reviewable patch or checklist first, then apply only the non-secret portions automatically when they are safe and clearly requested.
- Device-local secrets must be recreated through the appropriate provider UI, CLI, environment-variable setup, or a credential the user explicitly provides for this restore.

## Diff And Conflict Workflow

Before syncing across multiple devices:

1. Pull the latest private sync repo.
2. Run `python scripts/sync_codex.py diff`.
3. Classify changes:
   - `local_only`: exists on this device but not in cloud.
   - `cloud_only`: exists in cloud but not on this device.
   - `changed`: exists in both but differs.
   - `secret_required`: config exists but a token, key, OAuth login, or local SSH key must be recreated.
4. Ask the user how to resolve meaningful conflicts:
   - cloud wins: install cloud skills and use cloud config templates as the base.
   - local wins: push this device's snapshot to cloud.
   - merge: keep both where possible, then generate a manual config patch/checklist.
   - skip: leave the item unchanged.

For ABC-device scenarios, do not assume newer timestamp always wins. Compare hashes, paths, config summaries, and device names; explain the difference in plain language before asking.

## GitHub Handling

Use the best available path:

1. GitHub connector for existing repo file reads/writes when available.
2. GitHub CLI if installed and authenticated.
3. Git with the user's credential manager for clone/push/pull.
4. GitHub REST API only when `GITHUB_TOKEN` or `GH_TOKEN` is present.

If no GitHub write path exists, stop after preparing the local sync repository and explain what authorization is missing.

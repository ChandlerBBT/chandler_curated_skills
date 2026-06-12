# cross-device-sync

`cross-device-sync` is a Codex skill for keeping a Codex setup portable across devices.

It is distributed from this curated skills repository, but each user's actual sync snapshot belongs in that user's own private GitHub repository.

## What It Syncs

The skill maintains:

- user-managed Codex skill source folders
- redacted `config.toml` templates
- MCP server names, commands, transports, and redacted URLs
- plugin and marketplace settings with secrets removed
- SSH host aliases without private key contents
- Git remote URLs with embedded credentials removed
- diff reports for multi-device conflict review

## What It Never Syncs

It does not write raw credentials into GitHub:

- GitHub PATs
- API keys
- OAuth sessions
- `auth.json`
- browser cookies
- passwords
- SSH private key contents
- `.env` files

When another device needs a secret, Codex should ask the user to re-enter it, run the provider login flow, or recreate the local key through a secure process.

## Default Repository Rule

The default private sync repository name is derived from the GitHub owner:

```text
<github-owner>_codex_sync
```

Examples:

```text
jack -> jack_codex_sync
chandler -> chandler_codex_sync
```

The owner and repository name are configurable.

## First Run

Ask Codex:

```text
Use $cross-device-sync to bootstrap my Codex setup sync.
```

Codex should:

1. Infer your GitHub owner when possible.
2. Ask for the owner if it cannot infer one safely.
3. Offer `<owner>_codex_sync` as the default private repo name.
4. Create the private repo if GitHub authorization allows it.
5. Prepare and push the first setup snapshot.

## Diff Before Sync

On another device, ask:

```text
Use $cross-device-sync to diff this device against my cloud Codex setup.
```

The skill generates:

- `diff-report.json`
- `diff-report.md`

The report classifies:

- `local_only`: exists on this device but not in cloud
- `cloud_only`: exists in cloud but not on this device
- `changed`: exists in both but differs
- `secret_required`: configuration exists, but token/key/OAuth/SSH material must be recreated locally

Codex should then ask the user whether to use cloud, local, merge, or skip for meaningful conflicts.

## Restore On Another Device

Skills can be installed with:

```text
Use $cross-device-sync to install my synced skills.
```

Configuration restore is intentionally advisory. Codex should generate a reviewable checklist or patch before changing `config.toml`, MCP settings, SSH config, or Git remotes.


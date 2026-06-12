# Cross-device Sync Edge Cases

## What cannot be fully automatic from a skill alone

A Codex skill is loaded when Codex chooses or the user invokes it. It is not a resident background service and does not automatically run when Codex opens. Startup or continuous sync requires an external trigger such as a scheduled task, a Codex automation, a project hook, or a separate background service.

## List-only sync is insufficient

Local custom skills often have no public install source. To restore them on another device, the sync repo must store the skill folder contents as well as an inventory. For marketplace/plugin skills, store metadata and reinstall instructions rather than duplicating bundled plugin cache files.

## Config sync is not secret sync

Codex config, MCP definitions, SSH aliases, and Git remotes can include credentials directly or indirectly. The sync repo must store redacted templates and manifests, not raw secrets. Device-local secrets should be recreated through provider login, `gh auth login`, SSH key generation, password manager retrieval, or environment-variable setup.

## MCP servers

Record MCP server names, commands, transports, and redacted URLs. If an MCP URL contains a token in the query string, redact that parameter. If a command references environment variables, record the variable names but not their values.

## SSH

Record SSH host aliases and connection metadata. Do not copy private key contents. `IdentityFile` may be recorded as a redacted path or basename only.

## Deletions

Deletion should be explicit and auditable. A stale machine must pull first before declaring a remote skill deleted. Keep a change log entry for removed skills and rely on git history for recovery.

## Duplicate skill names

Codex can display duplicate skill names from different paths. The manifest must preserve scope and path. Install into `$HOME/.agents/skills` using folder names that avoid collision when necessary.

## System and plugin-bundled skills

System skills and plugin cache skills should be inventoried only. They should be restored by installing the corresponding Codex version or plugin, not by copying cache internals across devices.

## Multi-user behavior

Do not hardcode the maintainer's GitHub account into the sync flow. The curated repository that distributes this skill is separate from each user's private sync repository. On first run, infer the authenticated GitHub owner when possible; otherwise ask the user for an owner and offer `<owner>_codex_sync` as the default repo name, such as `jack_codex_sync` for owner `jack`.

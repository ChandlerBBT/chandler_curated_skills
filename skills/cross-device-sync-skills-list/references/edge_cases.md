# Cross-device Skills Sync Edge Cases

## What cannot be fully automatic from a skill alone

A Codex skill is loaded when Codex chooses or the user invokes it. It is not a resident background service and does not automatically run when Codex opens. Startup or continuous sync requires an external trigger such as a scheduled task, a Codex automation, a project hook, or a separate background service.

## List-only sync is insufficient

Local custom skills often have no public install source. To restore them on another device, the sync repo must store the skill folder contents as well as an inventory. For marketplace/plugin skills, store metadata and reinstall instructions rather than duplicating bundled plugin cache files.

## Deletions

Deletion should be explicit and auditable. A stale machine must pull first before declaring a remote skill deleted. Keep a change log entry for removed skills and rely on git history for recovery.

## Secrets and generated files

Skip `.env`, private keys, tokens, auth files, caches, virtual environments, node_modules, build outputs, compiled bytecode, and `.git` folders.

## Duplicate names

Codex can display duplicate skill names from different paths. The manifest must preserve scope and path. Install into `$HOME/.agents/skills` using folder names that avoid collision when necessary.

## System and plugin-bundled skills

System skills and plugin cache skills should be inventoried only. They should be restored by installing the corresponding Codex version or plugin, not by copying cache internals across devices.

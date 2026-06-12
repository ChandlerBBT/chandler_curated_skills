---
name: cross-device-sync-skills-list
description: Legacy compatibility entrypoint for the newer cross-device-sync skill. Use only when a user explicitly invokes the old cross-device-sync-skills-list name; route them to cross-device-sync for syncing Codex skills, config, MCP links, SSH aliases, Git remotes, and safe setup metadata across devices.
---

# Legacy Entrypoint

`cross-device-sync-skills-list` has been upgraded to `cross-device-sync`.

Use `$cross-device-sync` for all current workflows:

- sync Codex skills
- inventory redacted Codex config
- record MCP server links without secrets
- record SSH host aliases without private keys
- compare local and cloud setup differences
- generate conflict reports before syncing multiple devices

Do not extend this legacy skill. Keep it only so old prompts still route users to the new workflow.

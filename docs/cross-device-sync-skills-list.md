# cross-device-sync-skills-list

`cross-device-sync-skills-list` is a Codex skill for keeping user-managed Codex skills portable across devices.

It is distributed from this curated skills repository, but each user's actual skills catalog belongs in that user's own private GitHub repository.

## What It Does

The skill helps Codex:

- scan local skills from `.agents/skills` and `.codex/skills`
- record system and plugin-bundled skills without copying internal cache folders
- copy syncable user-managed skill sources into a private catalog repository
- generate `skills-list.json` and `skills-list.md`
- restore skills on a new device
- compare local and cloud skill changes
- keep an append-only `change-log.jsonl`

## Default Repository Rule

The default private catalog repository name is derived from the GitHub owner:

```text
<github-owner>_codex_skills_list
```

Examples:

```text
jack -> jack_codex_skills_list
chandler -> chandler_codex_skills_list
```

The owner and repository name are configurable. The skill must not assume the repository belongs to `ChandlerBBT`.

## First Run

Ask Codex:

```text
Use $cross-device-sync-skills-list to bootstrap my skills sync.
```

Codex should:

1. Infer your GitHub owner when possible.
2. Ask for the owner if it cannot infer one safely.
3. Offer `<owner>_codex_skills_list` as the default private repo name.
4. Create the private repo if GitHub authorization allows it.
5. Prepare and push the first skills catalog snapshot.

## Restore On Another Device

After installing this skill on another device, ask:

```text
Use $cross-device-sync-skills-list to install my skills from my GitHub catalog.
```

The skill should pull the catalog repo, back up any local conflicting skills, then install syncable skills into the user's skills directory.

## Important Boundary

A Codex skill is not a resident background service. It can guide sync and run bundled scripts when invoked, but automatic startup sync requires an external trigger such as:

- a scheduled OS task
- a Codex automation
- a project hook
- a separate background service

## Safety

The sync process should avoid copying:

- credentials
- `.env` files
- private keys
- `auth.json`
- cache folders
- build outputs
- virtual environments
- `.git` folders

Existing local skills are backed up before overwrite during restore.

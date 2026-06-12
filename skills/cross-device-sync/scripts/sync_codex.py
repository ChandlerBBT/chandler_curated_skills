#!/usr/bin/env python3
"""Synchronize Codex skills and safe setup metadata through a private GitHub repository."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_CATALOG_REPO_TEMPLATE = "{owner}_codex_sync"
SKILL_NAME = "cross-device-sync"
LEGACY_SKILL_NAME = "cross-device-sync-skills-list"
CONFIG_PATH = Path.home() / ".codex" / "cross-device-sync.json"
LEGACY_CONFIG_PATH = Path.home() / ".codex" / "cross-device-sync-skills-list.json"
SENSITIVE_KEY_RE = re.compile(r"(token|secret|password|passwd|pwd|key|credential|auth|cookie|session)", re.I)
TOKEN_RE = re.compile(r"(gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|[A-Za-z0-9_-]{32,})")
EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".system",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
EXCLUDED_FILES = {
    ".DS_Store",
    "Thumbs.db",
    "auth.json",
    "config.toml",
    "credentials.json",
}
EXCLUDED_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*.env",
    ".env*",
    "*token*",
    "*secret*",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, check=check)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8-sig"))
    if LEGACY_CONFIG_PATH.exists():
        return json.loads(LEGACY_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    return {}


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def default_local_repo() -> Path:
    config = load_config()
    repo_name = config.get("repo_name") or "codex_sync"
    return codex_home() / "skills-sync" / repo_name


def default_repo_name(owner: str | None) -> str:
    return DEFAULT_CATALOG_REPO_TEMPLATE.format(owner=owner) if owner else "codex_sync"


def resolve_repo(args: argparse.Namespace, config: dict) -> str | None:
    if args.repo:
        return args.repo
    if config.get("repository_full_name"):
        return config["repository_full_name"]
    owner = getattr(args, "owner", None) or config.get("github_owner")
    repo_name = getattr(args, "repo_name", None) or config.get("repo_name") or default_repo_name(owner)
    return f"{owner}/{repo_name}" if owner else None


def resolve_local_repo(args: argparse.Namespace, config: dict) -> Path:
    value = args.local_repo or config.get("local_repo_path")
    return Path(value).expanduser() if value else default_local_repo()


def infer_github_owner() -> str | None:
    env_owner = os.environ.get("GITHUB_OWNER") or os.environ.get("GH_OWNER")
    if env_owner:
        return env_owner
    gh = shutil.which("gh")
    if gh:
        result = run([gh, "api", "user", "--jq", ".login"], check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode("utf-8"))["login"]
        except urllib.error.HTTPError:
            return None
    configured = run(["git", "config", "--global", "github.user"], check=False)
    return configured.stdout.strip() or None


def parse_skill_md(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    name = path.parent.name
    description = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            frontmatter = text[3:end].splitlines()
            for line in frontmatter:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                value = value.strip().strip('"').strip("'")
                if key.strip() == "name":
                    name = value or name
                elif key.strip() == "description":
                    description = value
    return {"name": name, "description": description}


def should_exclude(path: Path) -> bool:
    if path.name in EXCLUDED_DIRS or path.name in EXCLUDED_FILES:
        return True
    lower = path.name.lower()
    return any(fnmatch.fnmatch(lower, pattern.lower()) for pattern in EXCLUDED_PATTERNS)


def redact_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    netloc = parsed.netloc
    if "@" in netloc:
        netloc = "<credentials>@" + netloc.rsplit("@", 1)[1]
    query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    redacted_pairs = [
        (key, "<REDACTED>" if SENSITIVE_KEY_RE.search(key) or TOKEN_RE.search(val) else val)
        for key, val in query_pairs
    ]
    query = urllib.parse.urlencode(redacted_pairs)
    fragment = "<REDACTED>" if TOKEN_RE.search(parsed.fragment) else parsed.fragment
    return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, query, fragment))


def redact_value(key: str, value):
    if SENSITIVE_KEY_RE.search(str(key)):
        return "<REDACTED>"
    if isinstance(value, str):
        value = redact_url(value)
        return TOKEN_RE.sub("<REDACTED>", value)
    if isinstance(value, list):
        return [redact_value(key, item) for item in value]
    if isinstance(value, dict):
        return {k: redact_value(k, v) for k, v in value.items()}
    return value


def redact_text(text: str) -> str:
    redacted_lines = []
    assignment = re.compile(r"^(\s*[\w.\-]+\s*=\s*)(.*)$")
    for line in text.splitlines():
        match = assignment.match(line)
        if match and SENSITIVE_KEY_RE.search(match.group(1)):
            redacted_lines.append(match.group(1) + '"<REDACTED>"')
            continue
        redacted_lines.append(TOKEN_RE.sub("<REDACTED>", redact_url(line)))
    return "\n".join(redacted_lines) + ("\n" if text.endswith("\n") else "")


def parse_toml(path: Path) -> dict:
    try:
        import tomllib
    except ModuleNotFoundError:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def nested_get(data: dict, *keys: str) -> dict:
    cur = data
    for key in keys:
        if not isinstance(cur, dict):
            return {}
        cur = cur.get(key, {})
    return cur if isinstance(cur, dict) else {}


def summarize_codex_config() -> dict:
    files = []
    config_text_parts = []
    config_paths = []
    base = codex_home()
    if (base / "config.toml").exists():
        config_paths.append(base / "config.toml")
    config_paths.extend(sorted(base.glob("*.config.toml")))
    seen = set()
    mcp_servers = []
    plugins = []
    marketplaces = []
    for path in config_paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        raw = path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_toml(path)
        redacted = redact_text(raw)
        config_text_parts.append(f"# Source: {path}\n{redacted}\n")
        files.append({"path": str(path), "exists": True, "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest()})
        for name, server in nested_get(parsed, "mcp_servers").items():
            item = {"name": name, **redact_value(name, server)}
            mcp_servers.append(item)
        for name, plugin in nested_get(parsed, "plugins").items():
            plugins.append({"name": name, **redact_value(name, plugin)})
        for name, marketplace in nested_get(parsed, "marketplaces").items():
            marketplaces.append({"name": name, **redact_value(name, marketplace)})
    return {
        "files": files,
        "mcp_servers": mcp_servers,
        "plugins": plugins,
        "marketplaces": marketplaces,
        "redacted_toml": "\n".join(config_text_parts).strip() + ("\n" if config_text_parts else ""),
    }


def summarize_ssh_config() -> dict:
    ssh_config = Path.home() / ".ssh" / "config"
    hosts = []
    if not ssh_config.exists():
        return {"files": [], "hosts": hosts}
    current: dict | None = None
    for raw_line in ssh_config.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        key, value = parts[0], parts[1]
        if key.lower() == "host":
            current = {"host": value, "options": {}}
            hosts.append(current)
        elif current is not None:
            if key.lower() == "identityfile":
                value = str(Path(value).name) if value else "<REDACTED>"
            current["options"][key] = redact_value(key, value)
    return {
        "files": [{"path": str(ssh_config), "exists": True}],
        "hosts": hosts,
    }


def summarize_git_remotes() -> dict:
    result = run(["git", "config", "--global", "--get-regexp", r"^url\..*\.insteadof$|^remote\..*\.url$"], check=False)
    remotes = []
    for line in result.stdout.splitlines():
        if not line.strip() or " " not in line:
            continue
        key, value = line.split(" ", 1)
        remotes.append({"key": key, "value": redact_url(value)})
    return {"global_git_url_settings": remotes}


def discover_setup() -> dict:
    codex_config = summarize_codex_config()
    return {
        "generated_at": now_iso(),
        "codex_config": {k: v for k, v in codex_config.items() if k != "redacted_toml"},
        "mcp_servers": codex_config["mcp_servers"],
        "plugins": codex_config["plugins"],
        "marketplaces": codex_config["marketplaces"],
        "ssh": summarize_ssh_config(),
        "git": summarize_git_remotes(),
        "secrets_policy": {
            "raw_credentials_synced": False,
            "notes": [
                "Tokens, passwords, auth files, cookies, sessions, and private keys are not copied.",
                "MCP and Git URLs are redacted when credentials or token-like values are detected.",
                "Recreate device-local secrets with each provider's login or credential setup flow.",
            ],
        },
        "redacted_toml": codex_config["redacted_toml"],
    }


def iter_files(root: Path):
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        dirs[:] = [d for d in dirs if not should_exclude(current_path / d)]
        for file_name in sorted(files):
            file_path = current_path / file_name
            if not should_exclude(file_path):
                yield file_path


def dir_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for file_path in iter_files(root):
        rel = file_path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def skill_roots(include_repo: bool = False) -> list[tuple[str, Path, bool]]:
    roots: list[tuple[str, Path, bool]] = [
        ("user", Path.home() / ".agents" / "skills", True),
        ("codex-user", codex_home() / "skills", True),
        ("codex-system", codex_home() / "skills" / ".system", False),
    ]
    if include_repo:
        cwd = Path.cwd().resolve()
        for parent in [cwd, *cwd.parents]:
            candidate = parent / ".agents" / "skills"
            if candidate.exists():
                roots.append(("repo", candidate, False))
    return roots


def discover_skills(include_repo: bool = False) -> list[dict]:
    skills: list[dict] = []
    seen: set[Path] = set()
    for scope, root, syncable in skill_roots(include_repo):
        if not root.exists():
            continue
        for skill_md in sorted(root.glob("*/SKILL.md")):
            folder = skill_md.parent.resolve()
            if folder in seen:
                continue
            seen.add(folder)
            metadata = parse_skill_md(skill_md)
            stat = skill_md.stat()
            skills.append(
                {
                    "name": metadata["name"],
                    "description": metadata["description"],
                    "folder_name": folder.name,
                    "scope": scope,
                    "path": str(folder),
                    "syncable": syncable and scope != "codex-system",
                    "sha256": dir_hash(folder),
                    "skill_md_mtime": dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat(),
                }
            )
    return skills


def clean_skill_sources(repo_dir: Path) -> None:
    target = repo_dir / "skill_sources"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)


def copy_skill_source(skill: dict, repo_dir: Path) -> None:
    source = Path(skill["path"])
    dest = repo_dir / "skill_sources" / skill["scope"] / skill["folder_name"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, ignore=lambda directory, names: [n for n in names if should_exclude(Path(directory) / n)])


def manifest_for(skills: list[dict], repo_full_name: str | None, setup: dict | None = None) -> dict:
    setup_summary = None
    if setup:
        setup_summary = {
            "codex_config_files": len(setup["codex_config"].get("files", [])),
            "mcp_servers": len(setup.get("mcp_servers", [])),
            "plugins": len(setup.get("plugins", [])),
            "marketplaces": len(setup.get("marketplaces", [])),
            "ssh_hosts": len(setup.get("ssh", {}).get("hosts", [])),
        }
    return {
        "schema_version": 1,
        "generated_at": now_iso(),
        "repository_full_name": repo_full_name,
        "device": {
            "hostname": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "",
            "home": str(Path.home()),
            "codex_home": str(codex_home()),
        },
        "summary": {
            "total": len(skills),
            "syncable": sum(1 for item in skills if item["syncable"]),
            "inventory_only": sum(1 for item in skills if not item["syncable"]),
            "setup": setup_summary,
        },
        "skills": skills,
    }


def markdown_catalog(manifest: dict) -> str:
    rows = [
        "# Codex Skills Catalog",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Repository: {manifest.get('repository_full_name') or 'not configured'}",
        "",
        "| Name | Scope | Syncable | Folder | SHA-256 | Description |",
        "|---|---|---:|---|---|---|",
    ]
    for skill in manifest["skills"]:
        desc = (skill.get("description") or "").replace("|", "\\|")
        rows.append(
            f"| {skill['name']} | {skill['scope']} | {str(skill['syncable']).lower()} | "
            f"`{skill['folder_name']}` | `{skill['sha256'][:12]}` | {desc} |"
        )
    rows.append("")
    return "\n".join(rows)


def repo_readme(repo_full_name: str | None) -> str:
    repo_text = repo_full_name or "your private GitHub repository"
    return "\n".join(
        [
            "# Codex Cross-device Sync",
            "",
            f"This private repository stores a portable Codex setup snapshot for `{repo_text}`.",
            "",
            "Use the `cross-device-sync` skill to scan, sync, and restore safe Codex setup metadata across devices.",
            "",
            "Important files:",
            "",
            "- `skills-list.json`: machine-readable inventory.",
            "- `skills-list.md`: readable catalog.",
            "- `skill_sources/`: copied user-managed skill folders.",
            "- `config/`: redacted Codex config, MCP, SSH, and Git setup manifests.",
            "- `change-log.jsonl`: sync history.",
            "",
        ]
    )


def find_this_skill_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[1],
        Path.home() / ".agents" / "skills" / SKILL_NAME,
        codex_home() / "skills" / SKILL_NAME,
        Path.home() / ".agents" / "skills" / LEGACY_SKILL_NAME,
        codex_home() / "skills" / LEGACY_SKILL_NAME,
    ]
    for candidate in candidates:
        if (candidate / "SKILL.md").exists():
            return candidate
    raise FileNotFoundError(f"Could not locate {SKILL_NAME}")


def ensure_git_repo(repo_dir: Path, repo_full_name: str | None) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    if not (repo_dir / ".git").exists():
        run(["git", "init"], repo_dir)
    if repo_full_name:
        remote_url = f"https://github.com/{repo_full_name}.git"
        remotes = run(["git", "remote"], repo_dir, check=False).stdout.split()
        if "origin" not in remotes:
            run(["git", "remote", "add", "origin", remote_url], repo_dir)


def git_pull(repo_dir: Path) -> None:
    if not (repo_dir / ".git").exists():
        return
    result = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], repo_dir, check=False)
    branch = result.stdout.strip() or "main"
    run(["git", "pull", "--ff-only", "origin", branch], repo_dir, check=False)


def git_commit_and_push(repo_dir: Path, message: str, push: bool) -> None:
    run(["git", "add", "."], repo_dir)
    status = run(["git", "status", "--porcelain"], repo_dir).stdout.strip()
    if not status:
        print("No sync repo changes to commit.")
        return
    run(["git", "commit", "-m", message], repo_dir)
    if push:
        result = run(["git", "push", "-u", "origin", "HEAD"], repo_dir, check=False)
        if result.returncode != 0:
            print(result.stderr.strip(), file=sys.stderr)
            print("Push failed. Authenticate GitHub for git push, install GitHub CLI, or push the local repo manually.", file=sys.stderr)


def publish_self(args: argparse.Namespace) -> None:
    config = load_config()
    repo_full_name = args.repo or config.get("curated_repository_full_name")
    if not repo_full_name:
        raise SystemExit("Pass --repo owner/name for the curated skills repository.")
    repo_dir = Path(args.local_repo).expanduser() if args.local_repo else Path(config.get("curated_local_repo_path", codex_home() / "skills-sync" / repo_full_name.split("/", 1)[1]))
    ensure_git_repo(repo_dir, repo_full_name)
    source = find_this_skill_dir()
    target = repo_dir / "skills" / SKILL_NAME
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target, ignore=lambda directory, names: [n for n in names if should_exclude(Path(directory) / n)])
    readme = repo_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# Chandler Curated Skills\n\nCurated Codex skills maintained by Chandler.\n\n",
            encoding="utf-8",
        )
    save_config(
        {
            **config,
            "curated_repository_full_name": repo_full_name,
            "curated_local_repo_path": str(repo_dir),
            "updated_at": now_iso(),
        }
    )
    git_commit_and_push(repo_dir, f"Publish {SKILL_NAME}", push=not args.no_push)
    print(f"Prepared {SKILL_NAME} for curated repo at {repo_dir}")


def append_change_log(repo_dir: Path, action: str, manifest: dict) -> None:
    entry = {
        "timestamp": now_iso(),
        "action": action,
        "device": manifest["device"],
        "summary": manifest["summary"],
    }
    with (repo_dir / "change-log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_setup_files(repo_dir: Path, setup: dict) -> None:
    config_dir = repo_dir / "config"
    if config_dir.exists():
        shutil.rmtree(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    redacted_toml = setup.pop("redacted_toml", "")
    (config_dir / "codex-config-summary.json").write_text(json.dumps(setup["codex_config"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (config_dir / "codex-config-redacted.toml").write_text(redacted_toml, encoding="utf-8")
    (config_dir / "mcp-servers.json").write_text(json.dumps(setup["mcp_servers"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (config_dir / "ssh-config-summary.json").write_text(json.dumps(setup["ssh"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (config_dir / "git-remotes.json").write_text(json.dumps(setup["git"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (config_dir / "restore-notes.md").write_text(restore_notes(setup), encoding="utf-8")


def restore_notes(setup: dict) -> str:
    lines = [
        "# Restore Notes",
        "",
        "This snapshot intentionally excludes raw credentials.",
        "",
        "## Recreate Locally",
        "",
        "- Re-authenticate GitHub, Google Drive, Notion, OpenAI, or other connectors in Codex/ChatGPT as needed.",
        "- Recreate MCP tokens and provider API keys through environment variables or provider setup flows.",
        "- Generate or copy SSH private keys through your password manager or secure key process; this repo does not store them.",
        "- Review `codex-config-redacted.toml` before applying any config to another machine.",
        "",
        "## Snapshot Counts",
        "",
        f"- MCP servers: {len(setup.get('mcp_servers', []))}",
        f"- Plugins: {len(setup.get('plugins', []))}",
        f"- Marketplaces: {len(setup.get('marketplaces', []))}",
        f"- SSH hosts: {len(setup.get('ssh', {}).get('hosts', []))}",
        "",
    ]
    return "\n".join(lines)


def load_cloud_snapshot(repo_dir: Path) -> dict:
    snapshot: dict = {"skills": [], "config": {}}
    skills_path = repo_dir / "skills-list.json"
    if skills_path.exists():
        snapshot["skills"] = json.loads(skills_path.read_text(encoding="utf-8")).get("skills", [])
    config_dir = repo_dir / "config"
    for name in [
        "codex-config-summary.json",
        "mcp-servers.json",
        "ssh-config-summary.json",
        "git-remotes.json",
    ]:
        path = config_dir / name
        if path.exists():
            snapshot["config"][name] = json.loads(path.read_text(encoding="utf-8"))
    return snapshot


def stable_json_hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def compare_skill_sets(local_skills: list[dict], cloud_skills: list[dict]) -> dict:
    def key(item: dict) -> str:
        return f"{item.get('scope')}::{item.get('folder_name')}"

    local_by_key = {key(item): item for item in local_skills if item.get("syncable")}
    cloud_by_key = {key(item): item for item in cloud_skills if item.get("syncable")}
    local_keys = set(local_by_key)
    cloud_keys = set(cloud_by_key)
    changed = []
    for item_key in sorted(local_keys & cloud_keys):
        local = local_by_key[item_key]
        cloud = cloud_by_key[item_key]
        if local.get("sha256") != cloud.get("sha256"):
            changed.append(
                {
                    "key": item_key,
                    "name": local.get("name") or cloud.get("name"),
                    "local_sha256": local.get("sha256"),
                    "cloud_sha256": cloud.get("sha256"),
                    "resolution_options": ["cloud_wins", "local_wins", "manual_merge", "skip"],
                }
            )
    return {
        "local_only": [local_by_key[k] for k in sorted(local_keys - cloud_keys)],
        "cloud_only": [cloud_by_key[k] for k in sorted(cloud_keys - local_keys)],
        "changed": changed,
    }


def compare_setup(local_setup: dict, cloud_config: dict) -> dict:
    comparisons = {}
    local_map = {
        "codex-config-summary.json": local_setup.get("codex_config", {}),
        "mcp-servers.json": local_setup.get("mcp_servers", []),
        "ssh-config-summary.json": local_setup.get("ssh", {}),
        "git-remotes.json": local_setup.get("git", {}),
    }
    for name, local_value in local_map.items():
        cloud_value = cloud_config.get(name)
        if cloud_value is None:
            status = "local_only"
        elif stable_json_hash(local_value) == stable_json_hash(cloud_value):
            status = "same"
        else:
            status = "changed"
        comparisons[name] = {
            "status": status,
            "local_hash": stable_json_hash(local_value),
            "cloud_hash": stable_json_hash(cloud_value) if cloud_value is not None else None,
            "resolution_options": ["cloud_base", "local_base", "manual_merge", "skip"] if status == "changed" else [],
        }
    cloud_only = sorted(set(cloud_config) - set(local_map))
    return {
        "files": comparisons,
        "cloud_only": cloud_only,
        "secret_required": [
            "Re-enter MCP tokens or API keys if a restored server needs them.",
            "Re-authenticate app connectors such as GitHub, Google Drive, Notion, or OpenAI.",
            "Recreate or securely copy SSH private keys; this sync repo never stores them.",
        ],
    }


def write_diff_report(repo_dir: Path, report: dict) -> None:
    (repo_dir / "diff-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Cross-device Sync Diff Report",
        "",
        f"Generated: {report['generated_at']}",
        f"Repository: {report.get('repository_full_name') or 'not configured'}",
        "",
        "## Skills",
        "",
        f"- Local only: {len(report['skills']['local_only'])}",
        f"- Cloud only: {len(report['skills']['cloud_only'])}",
        f"- Changed: {len(report['skills']['changed'])}",
        "",
        "## Setup",
        "",
    ]
    for name, item in report["setup"]["files"].items():
        lines.append(f"- `{name}`: {item['status']}")
    lines.extend(
        [
            "",
            "## Secret Required",
            "",
            *[f"- {item}" for item in report["setup"]["secret_required"]],
            "",
            "## Resolution Choices",
            "",
            "- `cloud_wins` / `cloud_base`: use the cloud snapshot as the base for this device.",
            "- `local_wins` / `local_base`: push this device's snapshot to cloud.",
            "- `manual_merge`: keep both sides visible and merge intentionally.",
            "- `skip`: leave the item unchanged.",
            "",
        ]
    )
    (repo_dir / "diff-report.md").write_text("\n".join(lines), encoding="utf-8")


def diff_snapshot(args: argparse.Namespace) -> dict:
    config = load_config()
    repo_dir = resolve_local_repo(args, config)
    if getattr(args, "pull", True):
        git_pull(repo_dir)
    cloud = load_cloud_snapshot(repo_dir)
    local_skills = discover_skills(include_repo=args.include_repo)
    local_setup = discover_setup()
    report = {
        "generated_at": now_iso(),
        "repository_full_name": resolve_repo(args, config),
        "device": {
            "hostname": os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "",
            "home": str(Path.home()),
            "codex_home": str(codex_home()),
        },
        "skills": compare_skill_sets(local_skills, cloud["skills"]),
        "setup": compare_setup(local_setup, cloud["config"]),
    }
    write_diff_report(repo_dir, report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report


def prepare(args: argparse.Namespace, action: str = "prepare") -> dict:
    config = load_config()
    repo_full_name = resolve_repo(args, config)
    repo_dir = resolve_local_repo(args, config)
    ensure_git_repo(repo_dir, repo_full_name)
    skills = discover_skills(include_repo=args.include_repo)
    setup = None if getattr(args, "no_config", False) else discover_setup()
    manifest = manifest_for(skills, repo_full_name, setup)
    clean_skill_sources(repo_dir)
    for skill in skills:
        if skill["syncable"]:
            copy_skill_source(skill, repo_dir)
    (repo_dir / "skills-list.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (repo_dir / "skills-list.md").write_text(markdown_catalog(manifest), encoding="utf-8")
    if setup:
        write_setup_files(repo_dir, setup)
    (repo_dir / "README.md").write_text(repo_readme(repo_full_name), encoding="utf-8")
    append_change_log(repo_dir, action, manifest)
    save_config(
        {
            **config,
            "repository_full_name": repo_full_name,
            "local_repo_path": str(repo_dir),
            "updated_at": now_iso(),
        }
    )
    print(f"Prepared {manifest['summary']['syncable']} syncable skills and setup inventory at {repo_dir}")
    return manifest


def backup_existing(path: Path) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_root = codex_home() / "backups" / "skills-sync" / timestamp
    backup_root.mkdir(parents=True, exist_ok=True)
    backup_path = backup_root / path.name
    shutil.copytree(path, backup_path)
    return backup_path


def install(args: argparse.Namespace) -> None:
    config = load_config()
    repo_dir = resolve_local_repo(args, config)
    if not (repo_dir / "skills-list.json").exists():
        raise SystemExit(f"No skills-list.json found in {repo_dir}. Run sync or clone the repo first.")
    if args.pull:
        git_pull(repo_dir)
    manifest = json.loads((repo_dir / "skills-list.json").read_text(encoding="utf-8"))
    target_root = Path.home() / ".agents" / "skills"
    target_root.mkdir(parents=True, exist_ok=True)
    installed = []
    for skill in manifest["skills"]:
        if not skill.get("syncable"):
            continue
        source = repo_dir / "skill_sources" / skill["scope"] / skill["folder_name"]
        if not source.exists():
            continue
        target = target_root / skill["folder_name"]
        if target.exists():
            local_hash = dir_hash(target)
            if local_hash == skill["sha256"]:
                continue
            if not args.force:
                backup = backup_existing(target)
                print(f"Backed up existing {target.name} to {backup}")
            shutil.rmtree(target)
        shutil.copytree(source, target)
        installed.append(skill["name"])
    print(f"Installed or updated {len(installed)} skills into {target_root}")
    for name in installed:
        print(f"- {name}")


def status(args: argparse.Namespace) -> None:
    config = load_config()
    repo_dir = resolve_local_repo(args, config)
    local = discover_skills(include_repo=args.include_repo)
    setup = None if getattr(args, "no_config", False) else discover_setup()
    print(json.dumps(manifest_for(local, resolve_repo(args, config), setup), indent=2, ensure_ascii=False))
    if (repo_dir / "skills-list.json").exists():
        remote_manifest = json.loads((repo_dir / "skills-list.json").read_text(encoding="utf-8"))
        remote_hashes = {(item["scope"], item["folder_name"]): item["sha256"] for item in remote_manifest.get("skills", [])}
        changed = [
            item for item in local
            if item["syncable"] and remote_hashes.get((item["scope"], item["folder_name"])) != item["sha256"]
        ]
        if changed:
            print("\nChanged compared with local sync repo:")
            for item in changed:
                print(f"- {item['name']} ({item['scope']}/{item['folder_name']})")


def configure(args: argparse.Namespace) -> None:
    config = load_config()
    owner = args.owner or infer_github_owner()
    repo_name = args.repo_name or config.get("repo_name") or default_repo_name(owner)
    if args.repo:
        config["repository_full_name"] = args.repo
    elif owner:
        config["repository_full_name"] = f"{owner}/{repo_name}"
    if owner:
        config["github_owner"] = owner
    if repo_name:
        config["repo_name"] = repo_name
    if args.local_repo:
        config["local_repo_path"] = str(Path(args.local_repo).expanduser())
    config["updated_at"] = now_iso()
    save_config(config)
    print(f"Saved config at {CONFIG_PATH}")


def bootstrap(args: argparse.Namespace) -> None:
    config = load_config()
    owner = args.owner or config.get("github_owner") or infer_github_owner()
    if not owner:
        raise SystemExit(
            "Could not infer your GitHub owner. Run configure --owner YOUR_GITHUB_OWNER, "
            "or authenticate GitHub CLI / set GITHUB_TOKEN."
        )
    repo_name = args.repo_name or config.get("repo_name") or default_repo_name(owner)
    repo_full_name = args.repo or f"{owner}/{repo_name}"
    configure_args = argparse.Namespace(repo=repo_full_name, owner=owner, repo_name=repo_name, local_repo=args.local_repo)
    configure(configure_args)
    if args.create:
        try:
            github_api_create_repo(repo_full_name, private=True)
        except Exception as exc:
            print(f"Could not create GitHub repo automatically: {exc}", file=sys.stderr)
            print("Create it as a private repository, then run sync.", file=sys.stderr)
    prepare(argparse.Namespace(repo=repo_full_name, local_repo=args.local_repo, include_repo=args.include_repo, no_config=args.no_config), action="bootstrap")


def github_api_create_repo(repo_full_name: str, private: bool = True) -> None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN or GH_TOKEN is required for REST repo creation.")
    owner, repo = repo_full_name.split("/", 1)
    req = urllib.request.Request(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as response:
        login = json.loads(response.read().decode("utf-8"))["login"]
    if owner.lower() != login.lower():
        raise RuntimeError(f"Token user is {login}; cannot create personal repo under {owner}.")
    body = json.dumps({"name": repo, "private": private, "auto_init": False}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/user/repos",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as response:
            created = json.loads(response.read().decode("utf-8"))
            print(f"Created private repo: {created['full_name']}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 422 and "name already exists" in detail.lower():
            print(f"Repository already exists: {repo_full_name}")
        else:
            raise RuntimeError(detail) from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="GitHub repository full name, e.g. owner/owner_codex_sync")
    parser.add_argument("--owner", help="GitHub owner or organization for the catalog repository")
    parser.add_argument("--repo-name", help="Catalog repository name, default: <owner>_codex_skills_list")
    parser.add_argument("--local-repo", help="Local sync repository path")
    parser.add_argument("--include-repo", action="store_true", help="Also inventory repo-scoped .agents/skills")
    parser.add_argument("--no-config", action="store_true", help="Skip Codex config, MCP, SSH, and Git setup inventory")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan")
    sub.add_parser("status")
    sub.add_parser("prepare")
    diff_parser = sub.add_parser("diff")
    diff_parser.add_argument("--no-pull", dest="pull", action="store_false")
    sync_parser = sub.add_parser("sync")
    sync_parser.add_argument("--no-pull", action="store_true")
    sync_parser.add_argument("--no-push", action="store_true")
    install_parser = sub.add_parser("install-skills")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--no-pull", dest="pull", action="store_false")
    legacy_install_parser = sub.add_parser("install")
    legacy_install_parser.add_argument("--force", action="store_true")
    legacy_install_parser.add_argument("--no-pull", dest="pull", action="store_false")
    configure_parser = sub.add_parser("configure")
    configure_parser.add_argument("--repo", required=False)
    configure_parser.add_argument("--owner", required=False)
    configure_parser.add_argument("--repo-name", required=False)
    configure_parser.add_argument("--local-repo", required=False)
    bootstrap_parser = sub.add_parser("bootstrap")
    bootstrap_parser.add_argument("--owner", required=False)
    bootstrap_parser.add_argument("--repo", required=False)
    bootstrap_parser.add_argument("--repo-name", required=False)
    bootstrap_parser.add_argument("--local-repo", required=False)
    bootstrap_parser.add_argument("--no-config", action="store_true")
    bootstrap_parser.add_argument("--create", action="store_true", help="Try to create the private catalog repo when credentials allow it")
    create_parser = sub.add_parser("create-github-repo")
    create_parser.add_argument("--owner", required=False)
    create_parser.add_argument("--repo", required=False)
    create_parser.add_argument("--repo-name", required=False)
    create_parser.add_argument("--private", action="store_true", default=True)
    publish_parser = sub.add_parser("publish-self")
    publish_parser.add_argument("--no-push", action="store_true")

    args = parser.parse_args()
    if args.command == "scan":
        setup = None if args.no_config else discover_setup()
        print(json.dumps(manifest_for(discover_skills(args.include_repo), resolve_repo(args, load_config()), setup), indent=2, ensure_ascii=False))
    elif args.command == "status":
        status(args)
    elif args.command == "prepare":
        prepare(args)
    elif args.command == "diff":
        diff_snapshot(args)
    elif args.command == "sync":
        config = load_config()
        repo_dir = resolve_local_repo(args, config)
        if not args.no_pull:
            git_pull(repo_dir)
        manifest = prepare(args, action="sync")
        git_commit_and_push(repo_dir, f"Sync Codex skills from {manifest['device']['hostname'] or 'device'}", push=not args.no_push)
    elif args.command in ("install", "install-skills"):
        install(args)
    elif args.command == "configure":
        configure(args)
    elif args.command == "create-github-repo":
        repo = resolve_repo(args, load_config())
        if not repo:
            raise SystemExit("Pass --repo owner/name or run configure first.")
        github_api_create_repo(repo, private=args.private)
    elif args.command == "publish-self":
        publish_self(args)


if __name__ == "__main__":
    main()

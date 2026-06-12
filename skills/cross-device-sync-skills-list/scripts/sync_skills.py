#!/usr/bin/env python3
"""Synchronize Codex user skills through a private GitHub-backed repository."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_CATALOG_REPO_NAME = "chandler_codex_skills_list"
DEFAULT_CURATED_REPO_NAME = "chandler_curated_skills"
SKILL_NAME = "cross-device-sync-skills-list"
CONFIG_PATH = Path.home() / ".codex" / "cross-device-sync-skills-list.json"
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
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {}


def save_config(config: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def default_local_repo() -> Path:
    return codex_home() / "skills-sync" / DEFAULT_CATALOG_REPO_NAME


def default_curated_local_repo() -> Path:
    return codex_home() / "skills-sync" / DEFAULT_CURATED_REPO_NAME


def resolve_repo(args: argparse.Namespace, config: dict) -> str | None:
    return args.repo or config.get("repository_full_name")


def resolve_local_repo(args: argparse.Namespace, config: dict) -> Path:
    value = args.local_repo or config.get("local_repo_path")
    return Path(value).expanduser() if value else default_local_repo()


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


def manifest_for(skills: list[dict], repo_full_name: str | None) -> dict:
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
            "# Codex Skills Sync",
            "",
            f"This private repository stores a portable Codex skills catalog for `{repo_text}`.",
            "",
            "Use the `cross-device-sync-skills-list` skill to scan, sync, and restore skills across devices.",
            "",
            "Important files:",
            "",
            "- `skills-list.json`: machine-readable inventory.",
            "- `skills-list.md`: readable catalog.",
            "- `skill_sources/`: copied user-managed skill folders.",
            "- `change-log.jsonl`: sync history.",
            "",
        ]
    )


def find_this_skill_dir() -> Path:
    candidates = [
        Path(__file__).resolve().parents[1],
        Path.home() / ".agents" / "skills" / SKILL_NAME,
        codex_home() / "skills" / SKILL_NAME,
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
    repo_full_name = args.repo or config.get("curated_repository_full_name") or f"ChandlerBBT/{DEFAULT_CURATED_REPO_NAME}"
    repo_dir = Path(args.local_repo).expanduser() if args.local_repo else Path(config.get("curated_local_repo_path", default_curated_local_repo()))
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


def prepare(args: argparse.Namespace, action: str = "prepare") -> dict:
    config = load_config()
    repo_full_name = resolve_repo(args, config)
    repo_dir = resolve_local_repo(args, config)
    ensure_git_repo(repo_dir, repo_full_name)
    skills = discover_skills(include_repo=args.include_repo)
    manifest = manifest_for(skills, repo_full_name)
    clean_skill_sources(repo_dir)
    for skill in skills:
        if skill["syncable"]:
            copy_skill_source(skill, repo_dir)
    (repo_dir / "skills-list.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (repo_dir / "skills-list.md").write_text(markdown_catalog(manifest), encoding="utf-8")
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
    print(f"Prepared {manifest['summary']['syncable']} syncable skills at {repo_dir}")
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
    print(json.dumps(manifest_for(local, resolve_repo(args, config)), indent=2, ensure_ascii=False))
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
    if args.repo:
        config["repository_full_name"] = args.repo
    if args.local_repo:
        config["local_repo_path"] = str(Path(args.local_repo).expanduser())
    config["updated_at"] = now_iso()
    save_config(config)
    print(f"Saved config at {CONFIG_PATH}")


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
    parser.add_argument("--repo", help="GitHub repository full name, e.g. ChandlerBBT/chandler_codex_skills_list")
    parser.add_argument("--local-repo", help="Local sync repository path")
    parser.add_argument("--include-repo", action="store_true", help="Also inventory repo-scoped .agents/skills")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("scan")
    sub.add_parser("status")
    sub.add_parser("prepare")
    sync_parser = sub.add_parser("sync")
    sync_parser.add_argument("--no-pull", action="store_true")
    sync_parser.add_argument("--no-push", action="store_true")
    install_parser = sub.add_parser("install")
    install_parser.add_argument("--force", action="store_true")
    install_parser.add_argument("--no-pull", dest="pull", action="store_false")
    configure_parser = sub.add_parser("configure")
    configure_parser.add_argument("--repo", required=False)
    configure_parser.add_argument("--local-repo", required=False)
    create_parser = sub.add_parser("create-github-repo")
    create_parser.add_argument("--private", action="store_true", default=True)
    publish_parser = sub.add_parser("publish-self")
    publish_parser.add_argument("--no-push", action="store_true")

    args = parser.parse_args()
    if args.command == "scan":
        print(json.dumps(manifest_for(discover_skills(args.include_repo), resolve_repo(args, load_config())), indent=2, ensure_ascii=False))
    elif args.command == "status":
        status(args)
    elif args.command == "prepare":
        prepare(args)
    elif args.command == "sync":
        config = load_config()
        repo_dir = resolve_local_repo(args, config)
        if not args.no_pull:
            git_pull(repo_dir)
        manifest = prepare(args, action="sync")
        git_commit_and_push(repo_dir, f"Sync Codex skills from {manifest['device']['hostname'] or 'device'}", push=not args.no_push)
    elif args.command == "install":
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

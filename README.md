<div align="center">

# Chandler Curated Skills

Curated Codex skills for reusable workflows, research discipline, and cross-device setup.

精心维护的 Codex Skills 集合，用于复用工作流、研究方法和跨设备配置同步。

[中文](#中文) | [English](#english)

</div>

---

## 中文

`chandler_curated_skills` 是一个 Codex Skills 仓库，收集我日常高频使用、已经沉淀成稳定流程的技能。你可以把某个 skill 安装到自己的 Codex 环境里，让 Codex 在对应任务中自动采用这套流程。

### 当前包含的 Skills

| Skill | 用途 | 安装路径 |
|---|---|---|
| `artifact-manager` | 管理报告、Markdown、HTML、图表、PPT 资产、数据表和研究产物，自动维护目录、版本、changelog 和 artifact index。 | `skills/artifact-manager` |
| `stock-analysis` | 面向股票研究的严谨投研流程，覆盖基本面、财报质量、估值、技术择时、催化验证、仓位风控和复盘规则回写。 | `skills/stock-analysis` |
| `cross-device-sync` | 通过每个用户自己的 GitHub 私有仓库维护 Codex skills、红acted Codex 配置、MCP 链接、SSH alias 和 Git remote 信息，方便多设备同步。默认同步仓库名为 `<github-owner>_codex_sync`。 | `skills/cross-device-sync` |

### 推荐安装方式

在 Codex 中直接让内置安装器安装指定路径：

```text
Use $skill-installer to install the skill from:
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/cross-device-sync
```

替换最后的路径即可安装其他 skill：

```text
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/artifact-manager
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/stock-analysis
```

安装后请重启 Codex，或在 Codex App 中执行 **Force Reload Skills**。

### 手动安装

把目标 skill 文件夹复制到你的用户级 skills 目录：

```text
Windows: %USERPROFILE%\.agents\skills\<skill-name>\
macOS/Linux: ~/.agents/skills/<skill-name>/
```

部分 Codex 环境也会扫描：

```text
Windows: %USERPROFILE%\.codex\skills\<skill-name>\
macOS/Linux: ~/.codex/skills/<skill-name>/
```

### 跨设备同步快速开始

安装 `cross-device-sync` 后，在 Codex 中说：

```text
Use $cross-device-sync to bootstrap my Codex setup sync.
```

首次运行时，它会：

1. 识别或询问你的 GitHub owner。
2. 默认使用 `<owner>_codex_sync` 作为私有同步仓库名，例如 `jack_codex_sync`。
3. 检测该仓库是否存在。
4. 如果不存在，在具备授权时创建私有仓库。
5. 扫描本机 Codex skills、安全配置清单、MCP、SSH alias 和 Git remote 信息。
6. 在其他设备上先生成 diff 报告，再让用户选择 cloud wins、local wins、merge 或 skip。

更详细说明见 [`docs/cross-device-sync.md`](docs/cross-device-sync.md)。

### 文档

- [`docs/artifact-manager.md`](docs/artifact-manager.md)
- [`docs/stock-analysis.md`](docs/stock-analysis.md)
- [`docs/cross-device-sync.md`](docs/cross-device-sync.md)

---

## English

`chandler_curated_skills` is a Codex Skills repository for reusable workflows that have become stable enough to share. Install a skill into your Codex environment so Codex can automatically follow the right process for matching tasks.

### Included Skills

| Skill | Purpose | Install path |
|---|---|---|
| `artifact-manager` | Keeps reports, Markdown, HTML, charts, slide assets, data tables, and research deliverables organized with directories, versions, changelog, and artifact index. | `skills/artifact-manager` |
| `stock-analysis` | A rigorous public-equity research workflow covering fundamentals, financial quality, valuation, technical timing, catalysts, position risk, and failure-review rule writeback. | `skills/stock-analysis` |
| `cross-device-sync` | Maintains Codex skills, redacted Codex config, MCP links, SSH aliases, and Git remotes through each user's own private GitHub repository. The default sync repo name is `<github-owner>_codex_sync`. | `skills/cross-device-sync` |

### Recommended Install

Ask Codex to install a skill with the built-in installer:

```text
Use $skill-installer to install the skill from:
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/cross-device-sync
```

Swap the final path to install another skill:

```text
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/artifact-manager
https://github.com/ChandlerBBT/chandler_curated_skills/tree/main/skills/stock-analysis
```

Restart Codex after installation, or run **Force Reload Skills** in the Codex App.

### Manual Install

Copy the target skill folder into your user-level skills directory:

```text
Windows: %USERPROFILE%\.agents\skills\<skill-name>\
macOS/Linux: ~/.agents/skills/<skill-name>/
```

Some Codex environments also scan:

```text
Windows: %USERPROFILE%\.codex\skills\<skill-name>\
macOS/Linux: ~/.codex/skills/<skill-name>/
```

### Cross-device Sync Quick Start

After installing `cross-device-sync`, ask Codex:

```text
Use $cross-device-sync to bootstrap my Codex setup sync.
```

On first run, it will:

1. Infer or ask for your GitHub owner.
2. Default to `<owner>_codex_sync` as the private sync repo name, such as `jack_codex_sync`.
3. Check whether that repository exists.
4. Create the private repository when an authorized GitHub path is available.
5. Scan local Codex skills, safe config inventory, MCP, SSH alias, and Git remote metadata.
6. Generate a diff report on other devices before asking whether cloud, local, merge, or skip should win.

See [`docs/cross-device-sync.md`](docs/cross-device-sync.md) for details.

### Documentation

- [`docs/artifact-manager.md`](docs/artifact-manager.md)
- [`docs/stock-analysis.md`](docs/stock-analysis.md)
- [`docs/cross-device-sync.md`](docs/cross-device-sync.md)

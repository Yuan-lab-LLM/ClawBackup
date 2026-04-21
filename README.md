# ClawBackup

<p align="center">
  <img src="https://raw.githubusercontent.com/Yuan-lab-LLM/ClawBackup/main/docs/assets/clawbackup-banner-fredoka2.png" alt="ClawBackup banner" width="920" />
</p>

<p align="center">
  A local backup utility for OpenClaw workspaces, built for fast first-run setup, scheduled backups, and clean CLI-based recovery workflows.
</p>

<p align="center">
  <strong>Languages:</strong>
  English |
  <a href="./README.zh-CN.md">简体中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a> |
  <a href="./README.de.md">Deutsch</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Backup%20Utility-ff7b72?style=for-the-badge" alt="OpenClaw Backup Utility" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/CLI-Multilingual-00c2d1?style=for-the-badge" alt="CLI Multilingual" />
  <img src="https://img.shields.io/badge/License-MIT-2ea44f?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <a href="#why-clawbackup">Why ClawBackup</a> |
  <a href="#what-it-backs-up">What It Backs Up</a> |
  <a href="#core-capabilities">Core Capabilities</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#first-run">First Run</a> |
  <a href="#development-and-release">Development & Release</a>
</p>

## Why ClawBackup

An OpenClaw workspace usually contains more than just one config file. It often includes credentials, agent profiles, memory files, workspace data, and scheduled tasks. Copying these files manually is easy once, but hard to keep consistent over time.

ClawBackup is designed to make local backup simple and repeatable:

- complete the first backup with a clean CLI flow
- enable scheduled backups without heavy setup
- review, restore, or remove old archives when needed
- install and distribute it using standard Python packaging workflows

ClawBackup fits especially well for:

- individual OpenClaw users who want dependable local backups
- users who frequently edit agent configuration and want rollback safety
- teams that want a standardized backup utility instead of manual file copy steps

## What It Backs Up

By default, ClawBackup backs up these OpenClaw files and directories:

- `openclaw.json`: main config file
- `credentials/`: API keys and tokens
- `agents/`: agent configs and auth profiles
- `workspace/`: memory files, `SOUL.md`, and user files
- `cron/`: scheduled task configuration

Default paths:

- OpenClaw data directory: `~/.openclaw`
- Backup output directory: `~/openclaw-backups`
- Compression format: `zip`
- Default retention policy: keep latest `10`, keep at least `3`, remove anything older than `30` days

## Core Capabilities

### Clean user-first CLI

The default home screen keeps the main workflow focused on four high-frequency actions:

- Back Up Now
- Schedule
- Reset Config
- Exit

Advanced commands such as history, config inspection, and logs are still available from the CLI, but they do not overload the first screen.

### Multilingual startup

The app currently supports:

- English
- Simplified Chinese
- Japanese
- Korean
- German

### Scheduled backups

Built-in scheduling presets include:

- every 6 hours
- daily at 02:00
- every Sunday at 02:00
- monthly on day 1 at 02:00
- custom cron expressions

### Retention control

ClawBackup supports both “keep all backups” and “keep only the latest N backups” retention strategies.

### History and restore

For generated archives, ClawBackup supports:

- browsing backup history
- restoring a selected backup
- deleting a single backup archive

## Quick Start

### Recommended: install with `pipx`

If `pipx` is not installed yet:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Close the current terminal, open a new one, then install the stable release directly from the wheel:

```bash
pipx install "https://github.com/Yuan-lab-LLM/ClawBackup/releases/download/v0.1.1/clawbackup-0.1.1-py3-none-any.whl"
```

After the project is published to PyPI, the same install becomes:

```bash
pipx install clawbackup
```

Run:

```bash
clawbackup
```

### Install the latest code from `main`

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### Install from local source

If you already cloned the repository:

```bash
python3 -m pip install .
```

or:

```bash
pipx install .
```

### Install with `pip`

If you prefer `pip` instead of `pipx`, install the published wheel directly:

```bash
python3 -m pip install "https://github.com/Yuan-lab-LLM/ClawBackup/releases/download/v0.1.1/clawbackup-0.1.1-py3-none-any.whl"
```

After PyPI publishing is enabled, users can also install with:

```bash
python3 -m pip install clawbackup
```

## First Run

Recommended first-run flow:

1. launch `clawbackup`
2. confirm or adjust the source and backup directories
3. run the first backup
4. configure scheduling only if you want automatic execution

Shortest path:

```bash
clawbackup
```

If you prefer direct commands:

```bash
clawbackup init
clawbackup backup
```

## Common Commands

### Main workflow

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

### Advanced commands

```bash
clawbackup history
clawbackup config
clawbackup log
```

## Upgrade and Uninstall

### Upgrade to the latest main branch

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### Upgrade or install a specific version

```bash
pipx install --force "https://github.com/Yuan-lab-LLM/ClawBackup/releases/download/v0.1.1/clawbackup-0.1.1-py3-none-any.whl"
```

### Uninstall

If installed with `pipx`:

```bash
pipx uninstall clawbackup
```

If installed with `pip`:

```bash
python3 -m pip uninstall clawbackup
```

## Local Files

Runtime files:

- config file: `~/.config/clawbackup/config.json`
- log file: `~/.config/clawbackup/clawbackup.log`

If you want to fully reset local state, use the in-app reset flow or remove the config file manually.

## Development and Release

### Run locally

```bash
python3 clawbackup.py
```

or:

```bash
python3 -m clawbackup
```

### Syntax check

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### Version locations

Before release, keep these locations aligned:

- `pyproject.toml`
- `src/clawbackup/__init__.py`
- UI version text inside `src/clawbackup/cli.py`

### Homebrew files

The repository already contains Homebrew-related files:

- `Formula/clawbackup.rb`
- `scripts/render_homebrew_formula.py`
- `scripts/homebrew_sha256.sh`
- `scripts/test_homebrew_local.sh`

### Release checklist

Recommended release flow:

1. update version numbers
2. commit changes
3. create a tag such as `v0.1.1`
4. push `main` and the tag
5. verify the GitHub Release
6. sync the Homebrew formula if needed

Common commands:

```bash
git add .
git commit -m "Release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

### Publish to PyPI

This repository is prepared for PyPI publishing through GitHub Actions trusted publishing.

Before the first publish:

1. create the `clawbackup` project on PyPI
2. in PyPI project settings, add a trusted publisher for:
   - owner: `Yuan-lab-LLM`
   - repository: `ClawBackup`
   - workflow: `publish-pypi.yml`
   - environment: `pypi`
3. in GitHub, approve the `pypi` environment if your org requires environment review

After that, the publish flow is:

1. build and verify the package locally if needed
2. create and push a release tag such as `v0.1.2`
3. open GitHub Actions and run the `Publish PyPI` workflow, or trigger it from a published release
4. verify the package on PyPI

Once PyPI publishing is live, end users can install with:

```bash
pipx install clawbackup
```

or:

```bash
python3 -m pip install clawbackup
```

## License

This project is released under the MIT License.

## Contributing

Issues and pull requests are welcome, especially around OpenClaw backup flows, restore workflows, and scheduling improvements.

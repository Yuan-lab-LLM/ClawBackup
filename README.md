# ClawBackup

ClawBackup 是一个面向 OpenClaw 的本地备份工具，提供简单的命令行界面，帮助用户快速完成以下事情：

- 备份 OpenClaw 关键数据
- 定时自动备份
- 管理保留策略
- 查看历史备份并恢复

适合两类人：

- 普通用户：希望快速备份 OpenClaw 工作目录，不想手动复制文件
- 开发者 / 运维：希望把备份流程标准化，并通过 `pipx`、`pip` 或 Homebrew 分发

License: `MIT`

## What It Backs Up

默认会备份这些内容：

- `openclaw.json`：主配置文件
- `credentials/`：API 密钥和令牌
- `agents/`：Agent 配置和认证档案
- `workspace/`：记忆、`SOUL.md`、用户文件
- `cron/`：定时任务配置

默认目录：

- OpenClaw 数据目录：`~/.openclaw`
- 备份输出目录：`~/openclaw-backups`
- 压缩格式：`zip`
- 默认保留策略：最近 `10` 份，最少保留 `3` 份，最多 `30` 天

## Features

- 首次启动支持语言选择：英 / 中 / 日 / 韩 / 德
- 首页保留简洁主菜单，适合普通用户
- 支持立即备份
- 支持定时设置
- 支持重置本地配置
- 支持查看历史备份、配置管理、日志等高级命令
- 支持 `pipx`、`pip`、Homebrew 安装

## Quick Start

### Option 1: Install with `pipx` (Recommended)

先安装 `pipx`：

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

关闭并重新打开一个终端后，安装：

```bash
pipx install .
```

如果你是从 GitHub 安装某个版本：

```bash
pipx install "git+https://github.com/<owner>/ClawBackup.git@v0.1.0"
```

### Option 2: Install with `pip`

```bash
python3 -m pip install .
```

### Run

```bash
clawbackup
```

也支持模块方式：

```bash
python3 -m clawbackup
```

## First Use

第一次使用建议就按下面的顺序：

1. 启动程序
2. 如有需要，进入配置流程确认目录
3. 执行第一次备份
4. 如需自动备份，再设置定时任务

最短路径：

```bash
clawbackup
```

首页常用菜单：

- `[1]` 立即备份
- `[2]` 定时设置
- `[3]` 重置配置
- `[4]` 退出

如果第一次还没配置好，进入 `[1]` 后可以继续选择：

- `立即备份`
- `编辑配置`
- `返回`

## Common Commands

基础命令：

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

高级命令：

```bash
clawbackup history
clawbackup config
clawbackup log
```

## Upgrade

如果你用 `pipx` 安装并想升级到 GitHub 上的指定版本：

```bash
pipx install --force "git+https://github.com/<owner>/ClawBackup.git@v0.1.0"
```

如果你用 `pip` 安装：

```bash
python3 -m pip install --upgrade "git+https://github.com/<owner>/ClawBackup.git@v0.1.0"
```

## Uninstall

如果你用 `pipx` 安装：

```bash
pipx uninstall clawbackup
```

如果你用 `pip` 安装：

```bash
python3 -m pip uninstall clawbackup
```

## Configuration Files

程序运行时会使用这些本地文件：

- 配置文件：`~/.config/clawbackup/config.json`
- 日志文件：`~/.config/clawbackup/clawbackup.log`

## For Developers

### Local Development

运行本地源码：

```bash
python3 clawbackup.py
```

语法检查：

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### Package Version

版本号需要保持这两个地方一致：

- `pyproject.toml`
- `src/clawbackup/__init__.py`

界面显示版本在：

- `src/clawbackup/cli.py`

## Homebrew

项目里已经包含 Homebrew 公式模板：

```text
Formula/clawbackup.rb
```

发布到 Homebrew 的推荐流程：

1. 构建源码包

```bash
python3 -m build --sdist
```

2. 计算 SHA256

```bash
./scripts/homebrew_sha256.sh dist/clawbackup-0.1.0.tar.gz
```

3. 生成公式

```bash
python3 scripts/render_homebrew_formula.py \
  dist/clawbackup-0.1.0.tar.gz \
  --github-repo Huifu1018/ClawBackup \
  --tag v0.1.0
```

4. 提交到你的 Homebrew tap 仓库

项目里还附带这些辅助文件：

- `docs/homebrew-tap-README.md`
- `docs/github-release-template.md`
- `scripts/test_homebrew_local.sh`

## Release Checklist

每次发版建议按这个顺序走：

1. 更新 `pyproject.toml` 版本号
2. 更新 `src/clawbackup/__init__.py` 的 `__version__`
3. 更新界面中的版本显示
4. 提交代码
5. 创建 tag，例如 `v0.1.0`
6. 推送 `main` 和 tag
7. 检查 GitHub Release
8. 如需 Homebrew，再更新 `Formula/clawbackup.rb`

常用命令：

```bash
git add .
git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main --tags
```

## GitHub Actions

项目已经带了自动发布工作流：

```text
.github/workflows/release.yml
```

触发方式：

- 推送 `v*` tag，例如 `v0.1.0`

这个工作流会自动：

- 执行语法检查
- 构建源码包
- 创建 GitHub Release
- 在配置了 `HOMEBREW_TAP_TOKEN` 时同步 Homebrew formula

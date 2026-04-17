# ClawBackup

<p align="center">
  一个面向 OpenClaw 工作空间的本地备份工具，提供可直接上手的 CLI 界面、定时自动备份能力，以及适合个人用户与团队分发的标准安装方式。
</p>

<p align="center">
  <strong>语言：</strong>
  <a href="./README.md">English</a> |
  简体中文 |
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
  <a href="#为什么是-clawbackup">为什么是 ClawBackup</a> |
  <a href="#备份内容">备份内容</a> |
  <a href="#核心能力">核心能力</a> |
  <a href="#快速开始">快速开始</a> |
  <a href="#首次使用">首次使用</a> |
  <a href="#开发与发布">开发与发布</a>
</p>

## 为什么是 ClawBackup

OpenClaw 的工作目录里，往往同时包含配置、密钥、Agent 档案、记忆文件和定时任务。手动复制这些内容并不难，但很难做得稳定、可重复，也很难长期保持一致。

ClawBackup 的目标不是做一个“复杂的备份平台”，而是提供一套更直接的本地备份体验：

- 用一个清晰的 CLI 流程完成第一次备份
- 用尽量少的配置，开启自动定时备份
- 用可读的历史记录查看、恢复和删除已有归档
- 用标准 Python 分发方式安装，适合个人使用，也适合团队统一部署

它适合这些场景：

- 个人用户希望定期保存自己的 OpenClaw 工作空间
- 经常改动 Agent 配置，希望在出问题前有可回滚的备份
- 团队想把 OpenClaw 备份流程做成统一工具，而不是手工步骤

## 备份内容

ClawBackup 默认会备份这些 OpenClaw 关键内容：

- `openclaw.json`：主配置文件
- `credentials/`：API 密钥和令牌
- `agents/`：Agent 配置与认证档案
- `workspace/`：记忆、`SOUL.md`、用户文件
- `cron/`：定时任务配置

默认路径如下：

- OpenClaw 数据目录：`~/.openclaw`
- 备份输出目录：`~/openclaw-backups`
- 压缩格式：`zip`
- 默认保留策略：最近 `10` 份，最少保留 `3` 份，最多 `30` 天

## 核心能力

### 面向用户的简洁 CLI

ClawBackup 的主界面默认聚焦在四个高频动作上：

- 立即备份
- 定时设置
- 重置配置
- 退出

而历史记录、日志、配置管理等能力仍然保留在命令行入口里，避免首页过重。

### 多语言启动体验

程序启动后支持多语言选择，目前支持：

- English
- 简体中文
- 日本語
- 한국어
- Deutsch

### 自动定时备份

内置常用备份频率预设，例如：

- 每 6 小时
- 每天 02:00
- 每周日 02:00
- 每月 1 日 02:00
- 自定义 cron 表达式

### 保留策略管理

支持按“全部保留”或“仅保留最近 N 份”的方式控制归档数量，减少旧备份长期堆积。

### 历史记录与恢复

对于已经生成的备份，ClawBackup 支持：

- 浏览备份历史
- 恢复指定备份
- 删除单个备份

## 快速开始

### 推荐方式：使用 `pipx`

如果你的机器上还没有 `pipx`：

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

关闭当前终端，重新打开一个新终端后，安装稳定版：

```bash
pipx install "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.0"
```

安装完成后直接运行：

```bash
clawbackup
```

### 直接安装最新代码

如果你希望体验仓库当前主分支版本：

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### 本地源码安装

如果你已经克隆了仓库，也可以直接在项目目录安装：

```bash
python3 -m pip install .
```

或：

```bash
pipx install .
```

## 首次使用

第一次使用建议按这个顺序：

1. 启动 `clawbackup`
2. 根据需要确认源目录和备份目录
3. 执行第一份备份
4. 如果希望自动执行，再配置定时任务

最短路径就是：

```bash
clawbackup
```

如果你更喜欢直接用命令：

```bash
clawbackup init
clawbackup backup
```

## 常用命令

### 主流程命令

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

### 高级命令

```bash
clawbackup history
clawbackup config
clawbackup log
```

## 升级与卸载

### 升级到最新主分支

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### 升级到指定版本

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.0"
```

### 卸载

如果你是用 `pipx` 安装：

```bash
pipx uninstall clawbackup
```

如果你是用 `pip` 安装：

```bash
python3 -m pip uninstall clawbackup
```

## 配置与本地文件

运行时会使用这些本地文件：

- 配置文件：`~/.config/clawbackup/config.json`
- 日志文件：`~/.config/clawbackup/clawbackup.log`

如果你需要清空本地状态，可以在程序中选择“重置配置”，或直接删除配置文件。

## 开发与发布

### 本地运行

```bash
python3 clawbackup.py
```

或：

```bash
python3 -m clawbackup
```

### 语法检查

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### 版本号位置

发布前需要同步这些位置：

- `pyproject.toml`
- `src/clawbackup/__init__.py`
- `src/clawbackup/cli.py` 中的界面版本显示

### Homebrew

项目中已包含 Homebrew 相关文件：

- `Formula/clawbackup.rb`
- `scripts/render_homebrew_formula.py`
- `scripts/homebrew_sha256.sh`
- `scripts/test_homebrew_local.sh`

### 发版清单

建议按以下顺序执行：

1. 更新版本号
2. 提交代码
3. 创建 tag，例如 `v0.1.0`
4. 推送 `main` 与 tag
5. 检查 GitHub Release
6. 如需 Homebrew，再同步公式

常用命令：

```bash
git add .
git commit -m "Release v0.1.0"
git tag v0.1.0
git push origin main --tags
```

## 许可证

本项目基于 MIT License 开源。

## 开源协作

欢迎提交 Issue 与 Pull Request，也欢迎围绕 OpenClaw 工作空间备份、恢复和自动化策略继续完善这个项目。

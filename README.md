# ClawBackup

OpenClaw 专属备份工具 CLI。

License: `MIT`

## Install

推荐使用 `pipx`：

```bash
pipx install .
```

如果本机还没有 `pipx`：

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

也可以直接用 `pip` 安装到当前环境：

```bash
python3 -m pip install .
```

## Homebrew

项目里已经带了一份 Homebrew 公式模板：

```bash
Formula/clawbackup.rb
```

发布到 Homebrew 的推荐流程：

1. 先打源码包

```bash
python3 -m build --sdist
```

2. 上传源码包到 GitHub Release

建议把 `dist/clawbackup-0.2.0.tar.gz` 上传到：

```text
https://github.com/Huifu1018/ClawBackup/releases/download/v0.2.0/clawbackup-0.2.0.tar.gz
```

3. 计算源码包的 SHA256

```bash
./scripts/homebrew_sha256.sh dist/clawbackup-0.2.0.tar.gz
```

4. 生成正式发布用的 Homebrew 公式

```bash
python3 scripts/render_homebrew_formula.py \
  dist/clawbackup-0.2.0.tar.gz \
  --github-repo Huifu1018/ClawBackup \
  --tag v0.2.0
```

如果你不想自动生成，也可以手动改 `Formula/clawbackup.rb` 里的这几项：

- `homepage`
- `url`
- `sha256`

5. 把公式提交到你的 Homebrew tap 仓库

完成后用户就可以这样安装：

```bash
brew install Huifu1018/tap/clawbackup
```

如果你要新建 `Huifu1018/homebrew-tap` 仓库，可以直接复用这份 README 模板：

```text
docs/homebrew-tap-README.md
```

如果你要发布 GitHub Release，也可以直接复用这份说明模板：

```text
docs/github-release-template.md
```

如果你想先在本机测试 Homebrew 安装，可以先准备源码包，然后自动生成一份本地可用的公式：

```bash
python3 -m build --sdist
python3 scripts/render_homebrew_formula.py dist/clawbackup-0.2.0.tar.gz
./scripts/test_homebrew_local.sh
```

说明：

- 现在的 Homebrew 不接受直接从项目目录里的 `Formula/*.rb` 安装
- 本地测试时，需要先把公式放进一个 tap
- `scripts/test_homebrew_local.sh` 会自动把公式复制到一个本地 tap，再执行安装

### Release Checklist

每次发布新版本时，按这个顺序检查：

1. 更新 `pyproject.toml` 里的版本号
2. 确认 `src/clawbackup/__init__.py` 里的 `__version__` 一致
3. 提交主项目仓库变更
4. 创建 Git tag，命名统一使用 `v版本号`，例如 `v0.2.0`
5. 推送 commit 和 tag 到 GitHub
6. 等待 GitHub Actions 自动构建并上传 `dist/clawbackup-<version>.tar.gz` 到 GitHub Release
7. 从 Release 页面或本地重新计算源码包的 SHA256
8. 重新生成 `Formula/clawbackup.rb`
9. 把公式同步到 `Huifu1018/homebrew-tap`
10. 用 `brew install Huifu1018/tap/clawbackup` 做一次干净安装验证

建议 Release tag 固定用这个格式：

```text
v0.2.0
v0.2.1
v0.3.0
```

对应的 GitHub Release 下载地址也保持同样规则：

```text
https://github.com/Huifu1018/ClawBackup/releases/download/v0.2.0/clawbackup-0.2.0.tar.gz
```

建议最少执行这几条命令：

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py scripts/render_homebrew_formula.py
git add .
git commit -m "Release v0.2.0"
git tag v0.2.0
git push origin main --tags
./scripts/homebrew_sha256.sh dist/clawbackup-0.2.0.tar.gz
python3 scripts/render_homebrew_formula.py \
  dist/clawbackup-0.2.0.tar.gz \
  --github-repo Huifu1018/ClawBackup \
  --tag v0.2.0
```

### GitHub Actions Release

项目已经带了自动发版工作流：

```text
.github/workflows/release.yml
```

触发方式：

- 推送 `v*` tag，例如 `v0.2.0`

这个工作流会自动：

- 执行 Python 语法检查
- 构建源码包 `dist/clawbackup-<version>.tar.gz`
- 把源码包上传到对应的 GitHub Release

### GitHub Actions Homebrew Tap Sync

Homebrew tap 同步现在已经并入同一个发布工作流：

```text
.github/workflows/release.yml
```

当你推送 `v*` tag 时，这个工作流会先创建 GitHub Release，再继续：

- 按 tag 重新构建源码包
- 生成最新的 `Formula/clawbackup.rb`
- 推送到 `Huifu1018/homebrew-tap`

启用前需要先在 `Huifu1018/ClawBackup` 仓库里配置一个 GitHub Secret：

```text
HOMEBREW_TAP_TOKEN
```

这个 token 需要对 `Huifu1018/homebrew-tap` 有写权限。
如果没有配置这个 secret，发布工作流会自动跳过 Homebrew tap 同步，不会影响 GitHub Release 本身。

## Run

```bash
clawbackup
```

也支持模块方式：

```bash
python3 -m clawbackup
```

## Direct commands

```bash
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

高级命令仍然可用，但默认不用进主菜单：

```bash
clawbackup history
clawbackup config
clawbackup log
```

## First Run

```bash
clawbackup
```

第一次使用只要两步：

- 先选 `1` 立即备份
- 如果还没配置过，就在第二层选 `2` 编辑配置

需要自动备份时，再回主菜单选 `2` 定时设置。

# ClawBackup

<p align="center">
  OpenClaw ワークスペース向けのローカルバックアップツール。初回セットアップ、定期バックアップ、CLI ベースの復元フローをわかりやすく提供します。
</p>

<p align="center">
  <strong>言語:</strong>
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a> |
  日本語 |
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
  <a href="#なぜ-clawbackup-か">なぜ ClawBackup か</a> |
  <a href="#バックアップ対象">バックアップ対象</a> |
  <a href="#主な機能">主な機能</a> |
  <a href="#クイックスタート">クイックスタート</a> |
  <a href="#初回利用">初回利用</a> |
  <a href="#開発とリリース">開発とリリース</a>
</p>

## なぜ ClawBackup か

OpenClaw のワークスペースには、設定ファイルだけでなく、資格情報、Agent プロファイル、メモリファイル、ワークスペースデータ、スケジュール設定などが含まれます。手動コピーは一度なら簡単ですが、継続的に正しく保つのは大変です。

ClawBackup は、ローカルバックアップをよりシンプルで再現可能にするためのツールです。

- 初回バックアップをわかりやすい CLI フローで完了
- 重い設定なしで定期バックアップを有効化
- 既存アーカイブの確認、復元、削除を簡単に実行
- 標準的な Python パッケージ方法で導入・配布

次のようなケースに向いています。

- OpenClaw ワークスペースを定期的に保存したい個人ユーザー
- Agent 設定を頻繁に変更し、巻き戻し手段を持ちたいユーザー
- 手作業ではなく標準化されたバックアップツールを使いたいチーム

## バックアップ対象

既定では次の OpenClaw 重要データをバックアップします。

- `openclaw.json`：メイン設定ファイル
- `credentials/`：API キーとトークン
- `agents/`：Agent 設定と認証プロファイル
- `workspace/`：メモリ、`SOUL.md`、ユーザーファイル
- `cron/`：スケジュール設定

既定値:

- OpenClaw データディレクトリ: `~/.openclaw`
- バックアップ出力先: `~/openclaw-backups`
- 圧縮形式: `zip`
- 保持ポリシー: 最新 `10` 件、最低 `3` 件、`30` 日を超えたものを削除

## 主な機能

### ユーザー向けに整理された CLI

ホーム画面では、主に次の 4 つの操作に集中できます。

- 今すぐバックアップ
- スケジュール設定
- 設定をリセット
- 終了

履歴、ログ、詳細設定などの上級コマンドは残したまま、初回画面は軽く保っています。

### 多言語起動

現在サポートしている言語:

- English
- 简体中文
- 日本語
- 한국어
- Deutsch

### 定期バックアップ

次のようなプリセットを用意しています。

- 6時間ごと
- 毎日 02:00
- 毎週日曜 02:00
- 毎月 1 日 02:00
- カスタム cron 式

### 保持ポリシー

「すべて保持」と「最新 N 件だけ保持」の両方に対応しています。

### 履歴と復元

生成済みバックアップに対して、次の操作が可能です。

- バックアップ履歴を確認
- 指定バックアップを復元
- 個別アーカイブを削除

## クイックスタート

### 推奨: `pipx` でインストール

`pipx` が未導入の場合:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

ターミナルを開き直した後、安定版をインストール:

```bash
pipx install "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

実行:

```bash
clawbackup
```

### `main` の最新コードを使う

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### ローカルソースからインストール

```bash
python3 -m pip install .
```

または:

```bash
pipx install .
```

## 初回利用

おすすめの流れ:

1. `clawbackup` を起動
2. 必要に応じてソースと保存先を確認
3. 最初のバックアップを実行
4. 自動化したい場合のみスケジュールを設定

最短ルート:

```bash
clawbackup
```

直接コマンドを使う場合:

```bash
clawbackup init
clawbackup backup
```

## よく使うコマンド

### 基本フロー

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

### 上級コマンド

```bash
clawbackup history
clawbackup config
clawbackup log
```

## アップグレードとアンインストール

### `main` の最新版に更新

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### 特定バージョンを導入

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

### アンインストール

`pipx` の場合:

```bash
pipx uninstall clawbackup
```

`pip` の場合:

```bash
python3 -m pip uninstall clawbackup
```

## ローカルファイル

実行時に使うファイル:

- 設定ファイル: `~/.config/clawbackup/config.json`
- ログファイル: `~/.config/clawbackup/clawbackup.log`

ローカル状態を完全に戻したい場合は、アプリ内のリセット機能を使うか、設定ファイルを削除してください。

## 開発とリリース

### ローカル実行

```bash
python3 clawbackup.py
```

または:

```bash
python3 -m clawbackup
```

### 構文チェック

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### バージョン管理箇所

リリース前に次を揃えてください。

- `pyproject.toml`
- `src/clawbackup/__init__.py`
- `src/clawbackup/cli.py` 内の UI バージョン表示

### Homebrew 関連

含まれているファイル:

- `Formula/clawbackup.rb`
- `scripts/render_homebrew_formula.py`
- `scripts/homebrew_sha256.sh`
- `scripts/test_homebrew_local.sh`

### リリース手順

1. バージョン番号更新
2. コミット
3. `v0.1.1` のような tag 作成
4. `main` と tag を push
5. GitHub Release を確認
6. 必要なら Homebrew formula を同期

```bash
git add .
git commit -m "Release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

## ライセンス

MIT License のもとで公開されています。

## コントリビュート

Issue と Pull Request を歓迎します。特に OpenClaw のバックアップ、復元、スケジュール改善に関する提案を歓迎します。

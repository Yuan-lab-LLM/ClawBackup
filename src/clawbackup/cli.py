#!/usr/bin/env python3
"""
ClawBackup — OpenClaw 备份工具 CLI
依赖：pip install rich
用法：python clawbackup.py [命令]
"""

import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

try:
    import readline  # noqa: F401
except ImportError:
    readline = None

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (BarColumn, Progress, SpinnerColumn,
                           TaskProgressColumn, TextColumn, TimeElapsedColumn)
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

# ── 颜色常量 ─────────────────────────────────────────────────
ACCENT  = "cyan"
OK      = "green"
WARN    = "yellow"
ERR     = "red"
MUTED   = "bright_black"
BOLD    = "bold"
SURFACE = "#e8fbfd"
ACCENT_SOFT = "#7fe7ec"
ACCENT_DEEP = "#1c6b70"
TEXT_DARK = "#102022"

console = Console()

# ── 默认配置 ─────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "openclaw_dir": "~/.openclaw",
    "backup_dir":   "~/openclaw-backups",
    "compress_format": "zip",
    "targets": [
        {"path": "openclaw.json", "enabled": True,  "desc": "主配置文件"},
        {"path": "credentials",   "enabled": True,  "desc": "API 密钥、令牌"},
        {"path": "agents",        "enabled": True,  "desc": "Agent 配置、认证档案"},
        {"path": "workspace",     "enabled": True,  "desc": "记忆、SOUL.md、用户文件"},
        {"path": "cron",          "enabled": True,  "desc": "定时任务配置"},
    ],
    "retention": {"max_count": 10, "max_days": 30, "min_count": 3},
    "notify": {
        "enabled": False,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        "only_on_failure": True,
    },
    "remote": {"enabled": False, "rclone_remote": ""},
}

CONFIG_PATH = Path.home() / ".config" / "clawbackup" / "config.json"
LOG_PATH    = Path.home() / ".config" / "clawbackup" / "clawbackup.log"

ICONS = {
    "openclaw.json": "⚙ ",
    "credentials":   "🔑",
    "agents":        "🤖",
    "workspace":     "🧠",
    "cron":          "⏱ ",
}


# ── 工具 ──────────────────────────────────────────────────────
def fmt_size(b: int) -> str:
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def safe_input(prompt: str, default: str = "") -> str:
    if prompt:
        console.print(prompt, end="")
    value = input()
    value = ANSI_ESCAPE_RE.sub("", value).strip()
    return value or default


def safe_prompt(label: str, default: str = "") -> str:
    hint = f"（默认 {default}）" if default else ""
    console.print(f"[{ACCENT}]{label}[/]{hint}")
    return safe_input("", default=default)


def content_width(max_width: int = 112) -> int:
    return max(72, min(max_width, console.size.width - 4))


def _describe_cron(expr: str) -> str:
    parts = expr.split()
    if len(parts) != 5:
        return "自定义计划"
    minute, hour, day, month, weekday = parts
    if minute.startswith("*/") and hour == day == month == weekday == "*":
        return f"每 {minute[2:]} 分钟执行一次"
    if minute == "0" and hour.startswith("*/") and day == month == weekday == "*":
        return f"每 {hour[2:]} 小时执行一次"
    if day == month == "*" and weekday == "*" and minute.isdigit() and hour.isdigit():
        return f"每天 {int(hour):02d}:{int(minute):02d} 执行"
    if day == month == "*" and minute.isdigit() and hour.isdigit() and weekday.isdigit():
        return f"每周 {weekday} {int(hour):02d}:{int(minute):02d} 执行"
    return "自定义计划"


def _describe_retention(retention: dict) -> str:
    max_count = retention.get("max_count", 10)
    max_days = retention.get("max_days", 30)
    min_count = retention.get("min_count", 3)
    if max_count <= 0 or max_days <= 0:
        return "全部保留"
    return f"保留最近 {max_count} 份（至少 {min_count} 份，最多 {max_days} 天）"


def _get_schedule_status(script: Path) -> dict:
    status = {
        "installed": False,
        "expr": "",
        "line": "",
        "command": "",
        "summary": "未安装定时任务",
    }
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        status["summary"] = "当前系统未提供 crontab"
        return status

    if result.returncode != 0:
        return status

    candidates = []
    script_name = script.name
    for raw in result.stdout.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if script_name in line or "clawbackup.py" in line:
            candidates.append(line)

    if not candidates:
        return status

    line = candidates[-1]
    parts = line.split(maxsplit=5)
    if len(parts) >= 6:
        expr = " ".join(parts[:5])
        command = parts[5]
    else:
        expr = ""
        command = line
    status.update(
        {
            "installed": True,
            "expr": expr,
            "line": line,
            "command": command,
            "summary": _describe_cron(expr) if expr else "已安装定时任务",
        }
    )
    return status


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, encoding="utf-8") as f:
            u = json.load(f)
        cfg = {**DEFAULT_CONFIG, **u}
        cfg["retention"] = {**DEFAULT_CONFIG["retention"], **u.get("retention", {})}
        cfg["notify"]    = {**DEFAULT_CONFIG["notify"],    **u.get("notify", {})}
        cfg["remote"]    = {**DEFAULT_CONFIG["remote"],    **u.get("remote", {})}
        return cfg
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def write_log(msg: str):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


# ── 界面组件 ──────────────────────────────────────────────────
def _build_clawbackup_banner() -> Group:
    target_width = content_width()
    align_center = lambda renderable: Align(renderable, align="center", width=target_width)

    if console.size.width < 110:
        eyebrow = Text("OPENCLAW BACKUP UTILITY", style="bold #a85a57")
        title_shadow = Text("  CLAWBACKUP", style="bold #8d1d1a")
        title = Text("CLAWBACKUP", style="bold #ff716b")
        brand = Text()
        brand.append("🦞 ", style="bold #ff6e69")
        brand.append("ClawBackup", style="bold #77d8ff")
        brand.append("  ", style="bold #77d8ff")
        brand.append("Version 0.1", style="bold #a85a57")
        brand.append("  ", style="bold #77d8ff")
        brand.append("OpenClaw 专属备份工具", style="bold #5d666d")
        return Group(
            align_center(eyebrow),
            align_center(title_shadow),
            align_center(title),
            align_center(brand),
        )

    glyphs = {
        "C": ["111110", "100000", "100000", "100000", "100000", "111110"],
        "L": ["100000", "100000", "100000", "100000", "100000", "111111"],
        "A": ["011110", "100001", "111111", "100001", "100001", "100001"],
        "W": ["100001", "100001", "100001", "101101", "110011", "100001"],
        "B": ["111110", "100001", "111110", "100001", "100001", "111110"],
        "K": ["100001", "100110", "111000", "100110", "100011", "100001"],
        "U": ["100001", "100001", "100001", "100001", "100001", "011110"],
        "P": ["111110", "100001", "111110", "100000", "100000", "100000"],
    }
    word = "CLAWBACKUP"
    row_colors = ["#ff8681", "#ff716b", "#ff645f", "#ff716b", "#ff807b", "#ff8f89"]
    letter_gap = 1
    cell_w = "█"

    height = len(glyphs["C"])
    width = sum(len(glyphs[ch][0]) for ch in word) + letter_gap * (len(word) - 1)
    front = [[" " for _ in range(width)] for _ in range(height)]

    cursor = 0
    for ch in word:
        glyph = glyphs[ch]
        for y, row in enumerate(glyph):
            for x, bit in enumerate(row):
                if bit == "1":
                    front[y][cursor + x] = "█"
        cursor += len(glyph[0]) + letter_gap

    lines = [align_center(Text("OPENCLAW BACKUP UTILITY", style="bold #a85a57"))]
    for y in range(height):
        line = Text()
        for x in range(width):
            if front[y][x] != " ":
                line.append(cell_w, style=f"bold {row_colors[y]}")
            else:
                line.append(" " * len(cell_w))
        lines.append(align_center(line))

    brand = Text()
    brand.append("🦞 ", style="bold #ff6e69")
    brand.append("ClawBackup", style="bold #77d8ff")
    brand.append("  ", style="bold #77d8ff")
    brand.append("Version 0.1", style="bold #a85a57")
    brand.append("  ", style="bold #77d8ff")
    brand.append("OpenClaw 专属备份工具", style="bold #5d666d")
    lines.append(align_center(brand))
    return Group(*lines)


def print_header():
    console.print()
    console.print(_build_clawbackup_banner())
    console.print()


def _command_help() -> Text:
    help_text = Text()
    help_text.append("命令: ", style=f"bold {TEXT_DARK}")
    help_text.append("init", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("backup", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("history", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("config", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("schedule", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("log", style=f"bold {ACCENT_DEEP}")
    help_text.append("  ")
    help_text.append("reset", style=f"bold {ACCENT_DEEP}")
    return help_text


def print_menu(cfg: dict):
    root = Path(cfg["openclaw_dir"]).expanduser()
    bdir = Path(cfg["backup_dir"]).expanduser()
    targets_enabled = sum(1 for t in cfg["targets"] if t.get("enabled", True))
    schedule = _get_schedule_status(Path(__file__).resolve())

    status = Table.grid(expand=True)
    status.add_column(ratio=1)
    status.add_column(ratio=1)
    status.add_column(ratio=1)
    status.add_row(
        Text(f"源目录  {root}", style=TEXT_DARK),
        Text(f"备份目录  {bdir}", style=TEXT_DARK),
        Text(f"格式  {cfg['compress_format']} / 项目 {targets_enabled}", style=TEXT_DARK),
    )

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    table.add_column(style=f"bold {ACCENT}", width=5, no_wrap=True)
    table.add_column(style=f"bold {TEXT_DARK}", width=12, no_wrap=True)
    table.add_column(style="dim")
    items = [
        ("i", "初始化",   "首次使用向导，快速写入目录和常用设置"),
        ("1", "立即备份",   "执行一次完整备份并按保留策略自动清理旧备份"),
        ("2", "备份历史",   "浏览已有归档，支持恢复或删除单个备份"),
        ("3", "配置管理",   "修改目录、保留策略与备份项目"),
        ("4", "定时任务",   "安装 cron 或 systemd timer，自动定期备份"),
        ("5", "查看日志",   "查看最近运行记录和结果"),
        ("6", "重置配置",   "清空已保存配置，并移除当前脚本对应的定时任务"),
        ("q", "退出",       "关闭当前会话"),
    ]
    for key, name, desc in items:
        table.add_row(Text(f"[{key}]", style=f"bold {ACCENT}"), name, desc)

    footer = Table.grid(expand=True)
    footer.add_column()
    footer.add_row(Text("首次使用建议先按 i 初始化，再执行 1 立即备份。", style=TEXT_DARK))
    footer.add_row(Text(f"定时任务状态: {schedule['summary']}", style=TEXT_DARK))
    footer.add_row(_command_help())

    body = Group(status, Text(""), table, Text(""), footer)
    console.print(Align.center(Panel(body, title="ClawBackup", border_style=ACCENT, padding=(0, 1), style=f"on {SURFACE}", width=content_width())))


def print_help():
    usage = Table.grid(padding=(0, 2))
    usage.add_column(style=f"bold {ACCENT_DEEP}", width=14)
    usage.add_column(style=TEXT_DARK)
    usage.add_row("初始化向导", "python3 clawbackup.py init")
    usage.add_row("启动菜单", "python3 clawbackup.py")
    usage.add_row("立即备份", "python3 clawbackup.py backup")
    usage.add_row("备份历史", "python3 clawbackup.py history")
    usage.add_row("配置管理", "python3 clawbackup.py config")
    usage.add_row("定时任务", "python3 clawbackup.py schedule")
    usage.add_row("查看日志", "python3 clawbackup.py log")
    usage.add_row("重置配置", "python3 clawbackup.py reset")

    first_use = Table.grid(padding=(0, 2))
    first_use.add_column(style=f"bold {ACCENT_DEEP}", width=4)
    first_use.add_column(style=TEXT_DARK)
    first_use.add_row("1.", "先运行 `python3 clawbackup.py init` 或在主菜单按 i。")
    first_use.add_row("2.", "确认 OpenClaw 目录、备份目录和压缩格式。")
    first_use.add_row("3.", "初始化完成后执行 [1]，生成第一次完整备份。")
    first_use.add_row("4.", "打开 [2] 备份历史，确认归档已经生成。")
    first_use.add_row("5.", "需要自动化时，再进入 [4] 安装定时任务。")

    notes = Text()
    notes.append("默认源目录: ", style=f"bold {TEXT_DARK}")
    notes.append(str(Path(DEFAULT_CONFIG["openclaw_dir"]).expanduser()), style=f"bold {ACCENT_DEEP}")
    notes.append("\n默认备份目录: ", style=f"bold {TEXT_DARK}")
    notes.append(str(Path(DEFAULT_CONFIG["backup_dir"]).expanduser()), style=f"bold {ACCENT_DEEP}")
    notes.append("\n配置文件: ", style=f"bold {TEXT_DARK}")
    notes.append(str(CONFIG_PATH), style=f"bold {ACCENT_DEEP}")
    notes.append("\n日志文件: ", style=f"bold {TEXT_DARK}")
    notes.append(str(LOG_PATH), style=f"bold {ACCENT_DEEP}")

    console.print()
    width = content_width()
    console.print(Align.center(Panel(_build_clawbackup_banner(), border_style=ACCENT, padding=(0, 1), style=f"on {SURFACE}", width=width)))
    console.print(Align.center(Panel(usage, title="Usage", border_style=ACCENT_SOFT, style=f"on {SURFACE}", width=width)))
    console.print(Align.center(Panel(first_use, title="First Run", border_style=ACCENT_SOFT, style=f"on {SURFACE}", width=width)))
    console.print(Align.center(Panel(notes, title="Defaults", border_style=ACCENT_SOFT, style=f"on {SURFACE}", width=width)))
    console.print()


def cmd_init(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]初始化向导", style=ACCENT))
    console.print(f"  [{MUTED}]用于第一次使用时快速完成常用设置。[/]")
    console.print(f"  [{MUTED}]不知道填什么时，直接回车即可保留括号里的默认值。[/]")
    console.print()

    console.print(f"  [{ACCENT}]1/4[/] 设置 OpenClaw 数据目录")
    console.print(f"  [{MUTED}]默认通常是 ~/.openclaw；如果你没有改过安装位置，直接回车。[/]")
    cfg["openclaw_dir"] = Prompt.ask(f"[{ACCENT}]OpenClaw 目录[/]", default=cfg["openclaw_dir"])
    console.print()

    console.print(f"  [{ACCENT}]2/4[/] 设置备份输出目录")
    console.print(f"  [{MUTED}]建议填一个你容易找到的位置；不确定就直接回车使用默认值。[/]")
    cfg["backup_dir"] = Prompt.ask(f"[{ACCENT}]备份输出目录[/]", default=cfg["backup_dir"])
    console.print()

    console.print(f"  [{ACCENT}]3/4[/] 选择压缩格式")
    console.print(f"  [{MUTED}]一般选 zip 就够用，兼容性最好；直接回车即可。[/]")
    cfg["compress_format"] = Prompt.ask(
        f"[{ACCENT}]压缩格式[/]",
        choices=["zip", "tar.gz", "tar.zst"],
        default=cfg.get("compress_format", "zip"),
    )
    console.print()

    console.print(f"  [{ACCENT}]4/4[/] 完成初始化")
    console.print(f"  [{MUTED}]当前会保留主配置、认证信息、agents、workspace 和 cron 配置。[/]")

    save_config(cfg)
    console.print(f"\n  [{OK}]✓  初始化完成，配置已保存到 {CONFIG_PATH}[/]")

    root = Path(cfg["openclaw_dir"]).expanduser()
    bdir = Path(cfg["backup_dir"]).expanduser()
    console.print(f"  [{MUTED}]源目录：{root}[/]")
    console.print(f"  [{MUTED}]备份目录：{bdir}[/]")
    console.print(f"  [bold {ACCENT}]下一步 1：[/][bold {TEXT_DARK}]回到主菜单后选择 [1] 立即备份，验证配置是否正确。[/]")
    console.print(f"  [bold {WARN}]下一步 2：[/][bold {TEXT_DARK}]如果你想自动定时备份，请在主菜单选择 [4] 定时任务，再单独配置执行频率。[/]\n")


def _remove_cron_jobs(script: Path) -> int:
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 0

    if result.returncode != 0:
        return 0

    lines = result.stdout.splitlines()
    kept = []
    removed = 0
    script_name = script.name
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and (str(script) in stripped or script_name in stripped):
            removed += 1
            continue
        kept.append(line)

    if removed:
        payload = "\n".join(kept).rstrip()
        if payload:
            payload += "\n"
        subprocess.run(["crontab", "-"], input=payload, text=True, check=True)
    return removed


def cmd_reset(_cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]重置配置", style=ACCENT))
    console.print(f"  [{WARN}]这会删除已保存的目录、压缩格式、保留策略等配置，并移除当前脚本对应的定时任务。[/]")
    console.print(f"  [{MUTED}]不会删除已有备份文件，也不会删除 OpenClaw 源数据。[/]")
    console.print()

    if not Confirm.ask(f"[{ERR}]确认继续重置？[/]", default=False):
        console.print(f"[{MUTED}]已取消。[/]\n")
        return

    removed_jobs = _remove_cron_jobs(Path(__file__).resolve())
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()

    console.print(f"  [{OK}]✓  已清空本地配置[/]")
    if removed_jobs:
        console.print(f"  [{OK}]✓  已移除 {removed_jobs} 条定时任务[/]")
    else:
        console.print(f"  [{MUTED}]未发现需要移除的定时任务。[/]")
    write_log("执行配置重置")
    console.print(f"  [{MUTED}]下次启动会自动回到默认配置，包括默认保留策略。[/]\n")


# ── 命令：立即备份 ────────────────────────────────────────────
def cmd_backup(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]立即备份", style=ACCENT))
    root     = Path(cfg["openclaw_dir"]).expanduser()
    bdir     = Path(cfg["backup_dir"]).expanduser()
    bdir.mkdir(parents=True, exist_ok=True)
    fmt      = cfg.get("compress_format", "zip")
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext      = {"zip": ".zip", "tar.gz": ".tar.gz", "tar.zst": ".tar.zst"}.get(fmt, ".zip")
    name     = f"openclaw_{ts}{ext}"
    dest     = bdir / name

    # 扫描目标
    targets = []
    for t in cfg["targets"]:
        if not t.get("enabled", True):
            continue
        p = root / t["path"]
        if p.exists():
            size = sum(f.stat().st_size for f in (p.rglob("*") if p.is_dir() else [p]) if f.is_file())
            targets.append((p, t["path"], size))
        else:
            console.print(f"  [{WARN}]⚠  {t['path']} 不存在，跳过[/]")

    if not targets:
        console.print(f"[{ERR}]✗  没有可备份的路径，请检查配置。[/]")
        return

    # 预览表
    tbl = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1))
    tbl.add_column("项目", style=ACCENT)
    tbl.add_column("说明", style=MUTED)
    tbl.add_column("大小", justify="right", style="white")
    for _, path_str, size in targets:
        icon = ICONS.get(path_str, "📁")
        tbl.add_row(f"{icon} {path_str}", "", fmt_size(size))
    console.print(tbl)
    console.print(f"  输出：[{MUTED}]{dest}[/]")
    console.print()

    if sys.stdin.isatty():
        if not Confirm.ask(f"[{ACCENT}]确认执行备份？[/]", default=True):
            console.print(f"[{MUTED}]已取消。[/]")
            return
    else:
        console.print(f"[{MUTED}]非交互环境，自动继续执行备份。[/]")

    console.print()

    # 进度条
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=32, style=MUTED, complete_style=ACCENT),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )

    with progress:
        total_size = sum(s for _, _, s in targets)
        task = progress.add_task("打包中...", total=len(targets))

        try:
            with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for p, path_str, size in targets:
                    icon = ICONS.get(path_str, "📁")
                    progress.update(task, description=f"{icon} {path_str}")
                    if p.is_file():
                        zf.write(p, p.relative_to(root))
                    elif p.is_dir():
                        for c in sorted(p.rglob("*")):
                            if c.is_file():
                                zf.write(c, c.relative_to(root))
                    progress.advance(task)
            progress.update(task, description="[green]压缩完成")
        except Exception as e:
            console.print(f"\n[{ERR}]✗  压缩失败：{e}[/]")
            return

    size_after = dest.stat().st_size
    console.print()
    console.print(f"  [{OK}]✓  备份成功[/]  {name}  [{MUTED}]({fmt_size(size_after)})[/]")
    write_log(f"备份成功 → {name} ({fmt_size(size_after)})")

    # 清理旧备份
    _prune(bdir, cfg["retention"])

    # 远程同步
    if cfg["remote"]["enabled"] and cfg["remote"]["rclone_remote"]:
        _sync_remote(dest, cfg["remote"]["rclone_remote"])

    console.print()


def _prune(bdir: Path, retention: dict):
    archives = sorted(bdir.glob("openclaw_*"), key=lambda p: p.stat().st_mtime, reverse=True)
    max_c = retention.get("max_count", 10)
    max_d = retention.get("max_days", 30)
    min_c = retention.get("min_count", 3)
    if max_c <= 0 or max_d <= 0:
        return
    cutoff = datetime.now() - timedelta(days=max_d)
    deleted = 0
    for i, p in enumerate(archives):
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if i >= min_c and (i >= max_c or mtime < cutoff):
            p.unlink()
            deleted += 1
    if deleted:
        console.print(f"  [{MUTED}]🗑  已清理 {deleted} 份旧备份[/]")
        write_log(f"清理旧备份 {deleted} 份")


def _sync_remote(src: Path, remote: str):
    console.print(f"  [{MUTED}]↑  同步到远程：{remote}[/]")
    try:
        subprocess.run(["rclone", "copy", str(src), remote], check=True)
        console.print(f"  [{OK}]✓  远程同步完成[/]")
    except FileNotFoundError:
        console.print(f"  [{WARN}]⚠  rclone 未安装，跳过[/]")
    except subprocess.CalledProcessError as e:
        console.print(f"  [{ERR}]✗  rclone 失败：{e}[/]")


# ── 命令：备份历史 ────────────────────────────────────────────
def cmd_history(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]备份历史", style=ACCENT))
    bdir     = Path(cfg["backup_dir"]).expanduser()
    archives = sorted(bdir.glob("openclaw_*"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not archives:
        console.print(f"  [{MUTED}]暂无备份记录。[/]\n")
        return

    tbl = Table(box=box.SIMPLE_HEAD, show_edge=False, padding=(0, 1))
    tbl.add_column("#",       style=MUTED,   width=4,  justify="right")
    tbl.add_column("文件名",  style="white",  width=38)
    tbl.add_column("大小",    style=ACCENT,   width=9,  justify="right")
    tbl.add_column("时间",    style=MUTED,    width=17)

    for i, p in enumerate(archives, 1):
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        tbl.add_row(str(i), p.name, fmt_size(p.stat().st_size), mtime)

    console.print(tbl)
    console.print(f"  [{MUTED}]共 {len(archives)} 份备份，路径：{bdir}[/]")
    console.print()

    action = Prompt.ask(
        f"[{ACCENT}]操作[/] [[bold]r[/]恢复  [bold]d[/]删除  [bold]回车[/]返回]",
        default="",
    ).strip().lower()

    if action == "r":
        num = Prompt.ask(f"[{ACCENT}]恢复序号[/]")
        try:
            p = archives[int(num) - 1]
        except (ValueError, IndexError):
            console.print(f"[{ERR}]无效序号[/]"); return
        root = Path(cfg["openclaw_dir"]).expanduser()
        if Confirm.ask(f"[{WARN}]恢复 {p.name} → {root}？这将覆盖现有文件[/]", default=False):
            with zipfile.ZipFile(p) as zf:
                zf.extractall(root)
            console.print(f"  [{OK}]✓  恢复完成[/]")
            write_log(f"恢复备份 → {p.name}")

    elif action == "d":
        num = Prompt.ask(f"[{ACCENT}]删除序号[/]")
        try:
            p = archives[int(num) - 1]
        except (ValueError, IndexError):
            console.print(f"[{ERR}]无效序号[/]"); return
        if Confirm.ask(f"[{ERR}]确认删除 {p.name}？[/]", default=False):
            p.unlink()
            console.print(f"  [{OK}]✓  已删除[/]")
            write_log(f"删除备份 → {p.name}")

    console.print()


# ── 命令：配置管理 ────────────────────────────────────────────
def cmd_config(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]配置管理", style=ACCENT))

    # 显示当前配置
    tree = Tree(f"[bold {ACCENT}]当前配置")
    tree.add(f"[{MUTED}]openclaw_dir[/]  {cfg['openclaw_dir']}")
    tree.add(f"[{MUTED}]backup_dir[/]    {cfg['backup_dir']}")
    tree.add(f"[{MUTED}]格式[/]          {cfg['compress_format']}")
    ret = cfg["retention"]
    tree.add(f"[{MUTED}]保留[/]          {_describe_retention(ret)}")
    targets_br = tree.add(f"[{MUTED}]备份项目[/]")
    for t in cfg["targets"]:
        icon = ICONS.get(t["path"], "📁")
        st   = f"[{OK}]✓[/]" if t.get("enabled") else f"[{MUTED}]○[/]"
        targets_br.add(f"{st} {icon} {t['path']}  [{MUTED}]{t['desc']}[/]")
    console.print(tree)
    console.print()

    action = Prompt.ask(
        f"[{ACCENT}]操作[/] [[bold]1[/]改路径  [bold]2[/]改保留策略  [bold]3[/]开关项目  [bold]e[/]用编辑器  [bold]回车[/]返回]",
        default="",
    ).strip().lower()

    if action == "1":
        v = Prompt.ask(f"[{ACCENT}]OpenClaw 目录[/]", default=cfg["openclaw_dir"])
        cfg["openclaw_dir"] = v
        v = Prompt.ask(f"[{ACCENT}]备份输出目录[/]", default=cfg["backup_dir"])
        cfg["backup_dir"] = v
        save_config(cfg)
        console.print(f"  [{OK}]✓  已保存[/]")

    elif action == "2":
        presets = [
            ("1", "全部保留", {"max_count": 0, "max_days": 0, "min_count": 0}),
            ("2", "只保留最近 3 个", {"max_count": 3, "max_days": 3650, "min_count": 3}),
            ("3", "只保留最近 5 个", {"max_count": 5, "max_days": 3650, "min_count": 3}),
            ("4", "只保留最近 10 个", {"max_count": 10, "max_days": 3650, "min_count": 3}),
            ("5", "自定义", None),
        ]
        console.print(f"  [{MUTED}]当前：{_describe_retention(ret)}[/]")
        pick_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        pick_tbl.add_column(style=f"bold {ACCENT}", width=4)
        pick_tbl.add_column(style="white")
        for key, label, _ in presets:
            pick_tbl.add_row(f"[{key}]", label)
        console.print(pick_tbl)
        choice = safe_prompt("保留策略", default="4")
        preset = next((item for item in presets if item[0] == choice), None)
        if not preset:
            console.print(f"[{ERR}]无效选择[/]")
            console.print()
            return
        if preset[2] is None:
            cfg["retention"]["max_count"] = int(Prompt.ask(f"[{ACCENT}]最多保留份数[/]", default=str(ret["max_count"])))
            cfg["retention"]["max_days"] = int(Prompt.ask(f"[{ACCENT}]最多保留天数[/]", default=str(ret["max_days"])))
            cfg["retention"]["min_count"] = int(Prompt.ask(f"[{ACCENT}]最少保留份数[/]", default=str(ret["min_count"])))
        else:
            cfg["retention"].update(preset[2])
        save_config(cfg)
        console.print(f"  [{OK}]✓  已保存[/]")

    elif action == "3":
        for i, t in enumerate(cfg["targets"]):
            st = "启用" if t.get("enabled") else "禁用"
            if Confirm.ask(f"  {ICONS.get(t['path'],'📁')} {t['path']} [{MUTED}]（当前{st}）[/] — 切换？", default=False):
                cfg["targets"][i]["enabled"] = not t.get("enabled", True)
        save_config(cfg)
        console.print(f"  [{OK}]✓  已保存[/]")

    elif action == "e":
        if not CONFIG_PATH.exists():
            save_config(cfg)
        editor = os.environ.get("EDITOR", "nano")
        os.system(f"{editor} '{CONFIG_PATH}'")

    console.print()


# ── 命令：定时任务 ────────────────────────────────────────────
def cmd_schedule(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]定时任务", style=ACCENT))
    script = Path(__file__).resolve()
    schedule = _get_schedule_status(script)

    status_tbl = Table.grid(padding=(0, 1))
    status_tbl.add_column(style=f"bold {ACCENT_DEEP}", width=10)
    status_tbl.add_column(style="white")
    status_tbl.add_row("当前状态", "已安装" if schedule["installed"] else "未安装")
    status_tbl.add_row("执行方式", schedule["summary"])
    if schedule["expr"]:
        status_tbl.add_row("表达式", schedule["expr"])
    if schedule["command"]:
        status_tbl.add_row("执行命令", schedule["command"])
    status_tbl.add_row("重启行为", "电脑重启后仍会继续按计划执行；关机或睡眠期间不会补跑。")
    console.print(Align.center(Panel(status_tbl, title="Current Schedule", border_style=ACCENT_SOFT, padding=(0, 1), style=f"on {SURFACE}", width=content_width())))
    console.print()

    presets = [
        ("0 */6 * * *",  "每 6 小时"),
        ("0 2 * * *",    "每天 02:00"),
        ("0 2 * * 0",    "每周日 02:00"),
        ("0 2 1 * *",    "每月 1 日 02:00"),
        ("custom",       "自定义 cron 表达式"),
    ]

    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column(style=f"bold {ACCENT}", width=4)
    tbl.add_column(style=MUTED, width=20)
    tbl.add_column(style="white")
    for i, (expr, label) in enumerate(presets, 1):
        tbl.add_row(f"[{i}]", label, "" if expr == "custom" else expr)
    console.print(tbl)

    choice = safe_prompt("选择频率", default="1")
    try:
        idx = int(choice) - 1
        expr, label = presets[idx]
    except (ValueError, IndexError):
        console.print(f"[{ERR}]无效选择[/]"); return

    if expr == "custom":
        expr = safe_prompt("输入 cron 表达式")

    console.print(f"\n  计划：[{ACCENT}]{expr}[/]  [{MUTED}]({_describe_cron(expr) if expr != 'custom' else label})[/]")
    script = str(script)

    if platform.system() == "Linux":
        console.print(f"[{ACCENT}]安装方式[/] [bold]1[/] systemd timer  [bold]2[/] crontab")
        method = safe_input("", default="1")
        if method == "1":
            _install_systemd(script)
        else:
            _install_cron(script, expr)
    else:
        _install_cron(script, expr)

    console.print()


def _install_cron(script: str, expr: str):
    line = f"{expr} {sys.executable} {script} backup >> {LOG_PATH} 2>&1"
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    existing = result.stdout if result.returncode == 0 else ""
    if script in existing:
        console.print(f"  [{WARN}]⚠  cron 任务已存在，跳过[/]"); return
    subprocess.run(["crontab", "-"], input=existing.rstrip() + f"\n{line}\n", text=True, check=True)
    console.print(f"  [{OK}]✓  crontab 已安装[/]")
    console.print(f"  [{MUTED}]{line}[/]")


def _install_systemd(script: str):
    svc = f"""[Unit]
Description=ClawBackup

[Service]
Type=oneshot
ExecStart={sys.executable} {script} backup
StandardOutput=append:{LOG_PATH}
StandardError=append:{LOG_PATH}
"""
    tmr = """[Unit]
Description=ClawBackup Timer

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h
Unit=clawbackup.service

[Install]
WantedBy=timers.target
"""
    d = Path.home() / ".config/systemd/user"
    d.mkdir(parents=True, exist_ok=True)
    (d / "clawbackup.service").write_text(svc)
    (d / "clawbackup.timer").write_text(tmr)
    for cmd in [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "enable", "--now", "clawbackup.timer"],
    ]:
        subprocess.run(cmd, check=True)
    console.print(f"  [{OK}]✓  systemd timer 已安装并启动[/]")
    console.print(f"  [{MUTED}]查看：systemctl --user status clawbackup.timer[/]")


# ── 命令：查看日志 ────────────────────────────────────────────
def cmd_log(_cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]运行日志", style=ACCENT))
    if not LOG_PATH.exists():
        console.print(f"  [{MUTED}]暂无日志记录。[/]\n"); return

    lines = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    n = Prompt.ask(f"[{ACCENT}]显示最近几条[/]", default="30")
    try:
        n = int(n)
    except ValueError:
        n = 30
    lines = lines[-n:]

    tbl = Table(box=box.SIMPLE, show_header=False, show_edge=False, padding=(0, 1))
    tbl.add_column(style=MUTED,  width=21)
    tbl.add_column(style="white")

    for line in lines:
        ts, _, msg = line.partition("] ")
        ts = ts.lstrip("[")
        if "成功" in msg or "完成" in msg or "✓" in msg:
            style = OK
        elif "警告" in msg or "⚠" in msg or "跳过" in msg:
            style = WARN
        elif "失败" in msg or "✗" in msg or "错误" in msg:
            style = ERR
        else:
            style = "white"
        tbl.add_row(ts, Text(msg, style=style))

    console.print(tbl)
    console.print(f"\n  [{MUTED}]日志文件：{LOG_PATH}[/]\n")


# ── 主循环 ────────────────────────────────────────────────────
COMMANDS = {
    "i": cmd_init,
    "1": cmd_backup,
    "2": cmd_history,
    "3": cmd_config,
    "4": cmd_schedule,
    "5": cmd_log,
    "6": cmd_reset,
}


def main():
    # 支持直接传子命令：ocbackup.py backup / list / log ...
    if len(sys.argv) > 1:
        alias = {"init": "i", "backup": "1", "history": "2", "config": "3", "schedule": "4", "log": "5", "reset": "6"}
        key = alias.get(sys.argv[1])
        if key:
            cfg = load_config()
            print_header()
            COMMANDS[key](cfg)
            return
        elif sys.argv[1] in ("-h", "--help"):
            print_help()
            return

    # 交互主菜单
    cfg = load_config()
    print_header()

    while True:
        print_menu(cfg)
        console.print(f"[{MUTED}]输入菜单编号，直接回车默认退出（q）。[/]")
        console.print(f"[bold {ACCENT}]>[/]")
        choice = safe_input("", default="q").lower()
        console.print()

        if choice in ("q", "quit", "exit", ""):
            console.print(f"[{MUTED}]再见。[/]\n")
            break

        fn = COMMANDS.get(choice)
        if fn:
            fn(cfg)
            cfg = load_config()
        else:
            console.print(f"[{ERR}]无效选项，请输入 i、1–6 或 q[/]\n")


if __name__ == "__main__":
    main()

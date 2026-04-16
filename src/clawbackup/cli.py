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

CURRENT_LANG = "en"
LANG_OPTIONS = [
    ("en", "English"),
    ("zh", "中文"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("de", "Deutsch"),
]

# ── 默认配置 ─────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "language": "en",
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

TARGET_DESC_KEYS = {
    "openclaw.json": "target_main_config",
    "credentials": "target_credentials",
    "agents": "target_agents",
    "workspace": "target_workspace",
    "cron": "target_cron",
}

I18N = {
    "en": {
        "default_hint": "(default {default})", "back_hint": "type b to go back",
        "custom_plan": "Custom schedule", "retain_all": "Keep all backups",
        "schedule_not_installed": "No scheduled task installed", "schedule_installed": "Scheduled task installed",
        "no_crontab": "crontab is not available on this system",
        "menu_now_backup": "Back Up Now", "menu_schedule": "Schedule", "menu_reset": "Reset Config", "menu_exit": "Exit",
        "menu_now_backup_desc": "Open backup flow or edit config first", "menu_schedule_desc": "Set automatic backup frequency",
        "menu_reset_desc": "Clear local config and scheduled task", "menu_exit_desc": "Close this session",
        "label_source": "Source", "label_backup": "Backup", "label_format": "Format", "label_items": "items", "label_schedule": "Schedule",
        "current_config": "Current Configuration", "panel_basics": "Basics", "panel_behavior": "Backup Behavior", "panel_targets": "Targets",
        "field_source": "Source", "field_backup": "Backup dir", "field_format": "Format", "field_retention": "Retention",
        "init_wizard": "Setup Wizard", "init_intro_1": "Quickly finish common settings for first use.", "init_intro_2": "Press Enter to keep the default value.",
        "step_source": "Set OpenClaw data directory", "step_backup": "Set backup output directory", "step_format": "Choose compression format", "step_retention": "Set retention policy",
        "default_path": "Default path", "new_path": "New path",
        "default_source_help": "~/.openclaw, press Enter to continue if unchanged.", "default_backup_help": "{value}, press Enter to continue if unchanged.",
        "new_path_help": "If needed, enter a new full path and press Enter.", "format_hint": "zip is recommended for best compatibility.",
        "unsupported_format": "Only zip / tar.gz / tar.zst are supported", "return": "Back",
        "keep_all": "Keep all", "keep_recent_3": "Keep latest 3", "keep_recent_5": "Keep latest 5", "keep_recent_10": "Keep latest 10",
        "invalid_keep_default": "Invalid choice, using default: keep latest 10.",
        "init_done": "Setup complete. Configuration saved to {path}", "next_step": "Next", "next_backup": "Return to the main menu and choose [1] Back Up Now.",
        "backup_entry": "Back Up Now", "edit_config": "Edit Config", "choose_action": "Choose action", "backed_out": "Back.",
        "reset_title": "Reset Configuration", "reset_warn_1": "This removes saved paths, compression format, retention policy, and the scheduled task for this script.",
        "reset_warn_2": "Existing backup archives and OpenClaw source data will not be deleted.", "confirm_reset": "Continue and reset?",
        "reset_done": "Local configuration cleared", "removed_jobs": "Removed {count} scheduled tasks", "no_jobs_found": "No scheduled tasks found to remove.",
        "reset_next": "Next startup will use defaults again.", "schedule_title": "Schedule", "schedule_state": "Status", "schedule_method": "Mode",
        "schedule_expr": "Expression", "schedule_cmd": "Command", "schedule_reboot": "After reboot it keeps running; missed runs during shutdown/sleep are not replayed.",
        "current_schedule": "Current Schedule", "preset_6h": "Every 6 hours", "preset_daily": "Daily 02:00", "preset_weekly": "Sunday 02:00", "preset_monthly": "1st day 02:00",
        "preset_custom": "Custom cron expression", "choose_frequency": "Choose frequency", "enter_cron": "Enter cron expression", "plan": "Plan", "install_method": "Install method",
        "crontab_unchanged": "Current schedule is unchanged", "crontab_updated": "crontab updated", "crontab_installed": "crontab installed",
        "main_prompt": "Choose 1-4, Enter exits.", "bye": "Bye.", "invalid_main": "Invalid option. Enter 1-4.",
        "target_main_config": "Main config file", "target_credentials": "API keys and tokens", "target_agents": "Agent configs and auth profiles", "target_workspace": "Memory, SOUL.md, user files", "target_cron": "Scheduled task config",
        "lang_title": "Select language", "lang_prompt": "Language", "weekday_0": "Sun", "weekday_1": "Mon", "weekday_2": "Tue", "weekday_3": "Wed", "weekday_4": "Thu", "weekday_5": "Fri", "weekday_6": "Sat", "weekday_7": "Sun",
        "every_minutes": "Every {value} minutes", "every_hours": "Every {value} hours", "daily_at": "Daily at {time}", "weekly_at": "Every {weekday} at {time}",
        "retain_recent": "Keep latest {count} backups (min {min_count}, max {max_days} days)", "brand_tagline": "OpenClaw backup utility",
    },
    "zh": {
        "default_hint": "（默认 {default}）", "back_hint": "输入 b 返回",
        "custom_plan": "自定义计划", "retain_all": "全部保留",
        "schedule_not_installed": "未安装定时任务", "schedule_installed": "已安装定时任务", "no_crontab": "当前系统未提供 crontab",
        "menu_now_backup": "立即备份", "menu_schedule": "定时设置", "menu_reset": "重置配置", "menu_exit": "退出",
        "menu_now_backup_desc": "默认进入备份；也可先配置", "menu_schedule_desc": "设置自动备份频率", "menu_reset_desc": "清空本地配置与定时任务", "menu_exit_desc": "关闭当前会话",
        "label_source": "源目录", "label_backup": "备份目录", "label_format": "格式", "label_items": "项目", "label_schedule": "定时任务",
        "current_config": "当前配置", "panel_basics": "基础设置", "panel_behavior": "备份行为", "panel_targets": "备份项目",
        "field_source": "源目录", "field_backup": "备份目录", "field_format": "压缩格式", "field_retention": "保留策略",
        "init_wizard": "初始化向导", "init_intro_1": "用于第一次使用时快速完成常用设置。", "init_intro_2": "不知道填什么时，直接回车即可保留括号里的默认值。",
        "step_source": "设置 OpenClaw 数据目录", "step_backup": "设置备份输出目录", "step_format": "选择压缩格式", "step_retention": "设置保留策略",
        "default_path": "默认路径", "new_path": "新路径",
        "default_source_help": "~/.openclaw，如不需要修改，直接回车，到下一步。", "default_backup_help": "{value}，如不需要修改，直接回车，到下一步。",
        "new_path_help": "如果需要修改，在光标处输入新的完整路径，回车确认。", "format_hint": "一般选 zip 就够用，兼容性最好；直接回车即可。",
        "unsupported_format": "仅支持 zip / tar.gz / tar.zst", "return": "返回",
        "keep_all": "全部保留", "keep_recent_3": "只保留最近 3 个", "keep_recent_5": "只保留最近 5 个", "keep_recent_10": "只保留最近 10 个",
        "invalid_keep_default": "无效选择，已使用默认保留最近 10 个。",
        "init_done": "初始化完成，配置已保存到 {path}", "next_step": "下一步", "next_backup": "回到主菜单后选择 [1] 立即备份。",
        "backup_entry": "立即备份", "edit_config": "编辑配置", "choose_action": "选择操作", "backed_out": "已返回。",
        "reset_title": "重置配置", "reset_warn_1": "这会删除已保存的目录、压缩格式、保留策略等配置，并移除当前脚本对应的定时任务。",
        "reset_warn_2": "不会删除已有备份文件，也不会删除 OpenClaw 源数据。", "confirm_reset": "确认继续重置？",
        "reset_done": "已清空本地配置", "removed_jobs": "已移除 {count} 条定时任务", "no_jobs_found": "未发现需要移除的定时任务。", "reset_next": "下次启动会自动回到默认配置，包括默认保留策略。",
        "schedule_title": "定时任务", "schedule_state": "当前状态", "schedule_method": "执行方式", "schedule_expr": "表达式", "schedule_cmd": "执行命令", "schedule_reboot": "电脑重启后仍会继续按计划执行；关机或睡眠期间不会补跑。",
        "current_schedule": "Current Schedule", "preset_6h": "每 6 小时", "preset_daily": "每天 02:00", "preset_weekly": "每周日 02:00", "preset_monthly": "每月 1 日 02:00",
        "preset_custom": "自定义 cron 表达式", "choose_frequency": "选择频率", "enter_cron": "输入 cron 表达式", "plan": "计划", "install_method": "安装方式",
        "crontab_unchanged": "当前计划未变化，无需修改", "crontab_updated": "crontab 已更新", "crontab_installed": "crontab 已安装",
        "main_prompt": "输入 1-4，直接回车默认退出。", "bye": "再见。", "invalid_main": "无效选项，请输入 1–4",
        "target_main_config": "主配置文件", "target_credentials": "API 密钥、令牌", "target_agents": "Agent 配置、认证档案", "target_workspace": "记忆、SOUL.md、用户文件", "target_cron": "定时任务配置",
        "lang_title": "选择语言", "lang_prompt": "语言", "weekday_0": "周日", "weekday_1": "周一", "weekday_2": "周二", "weekday_3": "周三", "weekday_4": "周四", "weekday_5": "周五", "weekday_6": "周六", "weekday_7": "周日",
        "every_minutes": "每 {value} 分钟执行一次", "every_hours": "每 {value} 小时执行一次", "daily_at": "每天 {time} 执行", "weekly_at": "每{weekday} {time} 执行",
        "retain_recent": "保留最近 {count} 份（至少 {min_count} 份，最多 {max_days} 天）", "brand_tagline": "OpenClaw 专属备份工具",
    },
}

I18N["ja"] = {
    **I18N["en"],
    "default_hint": "（既定値 {default}）", "back_hint": "b で戻る",
    "custom_plan": "カスタムスケジュール", "retain_all": "すべて保持",
    "schedule_not_installed": "スケジュール未設定", "schedule_installed": "スケジュール設定済み", "no_crontab": "このシステムでは crontab を利用できません",
    "menu_now_backup": "今すぐバックアップ", "menu_schedule": "スケジュール設定", "menu_reset": "設定をリセット", "menu_exit": "終了",
    "menu_now_backup_desc": "バックアップを開始、または先に設定", "menu_schedule_desc": "自動バックアップ頻度を設定", "menu_reset_desc": "ローカル設定とスケジュールを消去", "menu_exit_desc": "セッションを終了",
    "label_source": "ソース", "label_backup": "保存先", "label_format": "形式", "label_items": "項目", "label_schedule": "スケジュール",
    "current_config": "現在の設定", "panel_basics": "基本設定", "panel_behavior": "バックアップ動作", "panel_targets": "バックアップ対象",
    "field_source": "ソース", "field_backup": "保存先", "field_format": "圧縮形式", "field_retention": "保持ポリシー",
    "init_wizard": "初期設定ウィザード", "init_intro_1": "初回利用のための基本設定をすばやく完了します。", "init_intro_2": "迷ったら Enter で既定値を使用します。",
    "step_source": "OpenClaw データディレクトリを設定", "step_backup": "バックアップ出力先を設定", "step_format": "圧縮形式を選択", "step_retention": "保持ポリシーを設定",
    "default_path": "既定パス", "new_path": "新しいパス",
    "default_source_help": "~/.openclaw。変更不要なら Enter で次へ。", "default_backup_help": "{value}。変更不要なら Enter で次へ。",
    "new_path_help": "変更する場合は新しいフルパスを入力して Enter。", "format_hint": "互換性の高い zip を推奨します。",
    "unsupported_format": "zip / tar.gz / tar.zst のみ対応", "return": "戻る",
    "keep_all": "すべて保持", "keep_recent_3": "最新 3 件を保持", "keep_recent_5": "最新 5 件を保持", "keep_recent_10": "最新 10 件を保持",
    "invalid_keep_default": "無効な選択です。既定の最新 10 件を使用します。",
    "init_done": "初期設定完了。設定を {path} に保存しました", "next_step": "次へ", "next_backup": "メインメニューに戻って [1] を選択してください。",
    "backup_entry": "今すぐバックアップ", "edit_config": "設定を編集", "choose_action": "操作を選択", "backed_out": "戻りました。",
    "reset_title": "設定をリセット", "reset_warn_1": "保存されたパス、圧縮形式、保持ポリシー、およびこのスクリプトのスケジュールを削除します。",
    "reset_warn_2": "既存のバックアップや OpenClaw の元データは削除されません。", "confirm_reset": "リセットを続行しますか？",
    "reset_done": "ローカル設定を消去しました", "removed_jobs": "{count} 件のスケジュールを削除しました", "no_jobs_found": "削除対象のスケジュールはありませんでした。", "reset_next": "次回起動時は既定設定に戻ります。",
    "schedule_title": "スケジュール", "schedule_state": "状態", "schedule_method": "方式", "schedule_expr": "式", "schedule_cmd": "実行コマンド", "schedule_reboot": "再起動後も継続。電源オフやスリープ中の実行は補完されません。",
    "current_schedule": "Current Schedule", "preset_6h": "6時間ごと", "preset_daily": "毎日 02:00", "preset_weekly": "毎週日曜 02:00", "preset_monthly": "毎月1日 02:00",
    "preset_custom": "カスタム cron 式", "choose_frequency": "頻度を選択", "enter_cron": "cron 式を入力", "plan": "予定", "install_method": "インストール方式",
    "crontab_unchanged": "現在のスケジュールは変更ありません", "crontab_updated": "crontab を更新しました", "crontab_installed": "crontab を設定しました",
    "main_prompt": "1-4 を入力、Enter で終了。", "bye": "終了します。", "invalid_main": "無効な選択です。1-4 を入力してください。",
    "target_main_config": "メイン設定ファイル", "target_credentials": "API キーとトークン", "target_agents": "Agent 設定と認証プロファイル", "target_workspace": "記憶、SOUL.md、ユーザーファイル", "target_cron": "スケジュール設定",
    "lang_title": "言語を選択", "lang_prompt": "言語", "weekday_0": "日", "weekday_1": "月", "weekday_2": "火", "weekday_3": "水", "weekday_4": "木", "weekday_5": "金", "weekday_6": "土", "weekday_7": "日",
    "every_minutes": "{value}分ごとに実行", "every_hours": "{value}時間ごとに実行", "daily_at": "毎日 {time} に実行", "weekly_at": "毎週{weekday} {time} に実行",
    "retain_recent": "最新 {count} 件を保持（最小 {min_count} 件、最大 {max_days} 日）", "brand_tagline": "OpenClaw バックアップユーティリティ",
}
I18N["ko"] = {
    **I18N["en"],
    "default_hint": "(기본값 {default})", "back_hint": "b 입력 시 뒤로",
    "custom_plan": "사용자 지정 일정", "retain_all": "모두 보관",
    "schedule_not_installed": "예약 작업 없음", "schedule_installed": "예약 작업 설치됨", "no_crontab": "이 시스템에서는 crontab을 사용할 수 없습니다",
    "menu_now_backup": "지금 백업", "menu_schedule": "예약 설정", "menu_reset": "설정 초기화", "menu_exit": "종료",
    "menu_now_backup_desc": "바로 백업하거나 먼저 설정 편집", "menu_schedule_desc": "자동 백업 주기 설정", "menu_reset_desc": "로컬 설정과 예약 작업 삭제", "menu_exit_desc": "현재 세션 종료",
    "label_source": "원본", "label_backup": "백업", "label_format": "형식", "label_items": "항목", "label_schedule": "예약 작업",
    "current_config": "현재 설정", "panel_basics": "기본 설정", "panel_behavior": "백업 동작", "panel_targets": "백업 대상",
    "field_source": "원본", "field_backup": "백업 경로", "field_format": "압축 형식", "field_retention": "보관 정책",
    "init_wizard": "초기 설정 마법사", "init_intro_1": "처음 사용을 위한 기본 설정을 빠르게 완료합니다.", "init_intro_2": "잘 모르겠으면 Enter로 기본값을 사용하세요.",
    "step_source": "OpenClaw 데이터 디렉터리 설정", "step_backup": "백업 출력 경로 설정", "step_format": "압축 형식 선택", "step_retention": "보관 정책 설정",
    "default_path": "기본 경로", "new_path": "새 경로",
    "default_source_help": "~/.openclaw, 변경이 없으면 Enter로 다음 단계.", "default_backup_help": "{value}, 변경이 없으면 Enter로 다음 단계.",
    "new_path_help": "변경이 필요하면 새 전체 경로를 입력하고 Enter.", "format_hint": "호환성이 좋은 zip을 권장합니다.",
    "unsupported_format": "zip / tar.gz / tar.zst 만 지원합니다", "return": "뒤로",
    "keep_all": "모두 보관", "keep_recent_3": "최근 3개만 보관", "keep_recent_5": "최근 5개만 보관", "keep_recent_10": "최근 10개만 보관",
    "invalid_keep_default": "잘못된 선택입니다. 기본값(최근 10개)을 사용합니다.",
    "init_done": "초기 설정 완료. 설정이 {path} 에 저장되었습니다", "next_step": "다음 단계", "next_backup": "메인 메뉴로 돌아가 [1] 지금 백업을 선택하세요.",
    "backup_entry": "지금 백업", "edit_config": "설정 편집", "choose_action": "작업 선택", "backed_out": "뒤로 돌아갔습니다.",
    "reset_title": "설정 초기화", "reset_warn_1": "저장된 경로, 압축 형식, 보관 정책, 그리고 이 스크립트의 예약 작업을 삭제합니다.",
    "reset_warn_2": "기존 백업 파일과 OpenClaw 원본 데이터는 삭제되지 않습니다.", "confirm_reset": "계속 초기화하시겠습니까?",
    "reset_done": "로컬 설정을 삭제했습니다", "removed_jobs": "예약 작업 {count}개를 제거했습니다", "no_jobs_found": "제거할 예약 작업이 없습니다.", "reset_next": "다음 실행 시 기본 설정으로 돌아갑니다.",
    "schedule_title": "예약 설정", "schedule_state": "상태", "schedule_method": "방식", "schedule_expr": "표현식", "schedule_cmd": "실행 명령", "schedule_reboot": "재부팅 후에도 계속 실행되며, 종료/절전 중 누락된 실행은 보충되지 않습니다.",
    "current_schedule": "Current Schedule", "preset_6h": "6시간마다", "preset_daily": "매일 02:00", "preset_weekly": "매주 일요일 02:00", "preset_monthly": "매월 1일 02:00",
    "preset_custom": "사용자 지정 cron 표현식", "choose_frequency": "주기 선택", "enter_cron": "cron 표현식 입력", "plan": "계획", "install_method": "설치 방식",
    "crontab_unchanged": "현재 일정은 변경되지 않았습니다", "crontab_updated": "crontab 이 업데이트되었습니다", "crontab_installed": "crontab 이 설치되었습니다",
    "main_prompt": "1-4 입력, Enter는 종료.", "bye": "종료합니다.", "invalid_main": "잘못된 선택입니다. 1-4를 입력하세요.",
    "target_main_config": "메인 설정 파일", "target_credentials": "API 키와 토큰", "target_agents": "Agent 설정 및 인증 프로필", "target_workspace": "기억, SOUL.md, 사용자 파일", "target_cron": "예약 작업 설정",
    "lang_title": "언어 선택", "lang_prompt": "언어", "weekday_0": "일", "weekday_1": "월", "weekday_2": "화", "weekday_3": "수", "weekday_4": "목", "weekday_5": "금", "weekday_6": "토", "weekday_7": "일",
    "every_minutes": "{value}분마다 실행", "every_hours": "{value}시간마다 실행", "daily_at": "매일 {time} 실행", "weekly_at": "매주 {weekday} {time} 실행",
    "retain_recent": "최신 {count}개 보관 (최소 {min_count}개, 최대 {max_days}일)", "brand_tagline": "OpenClaw 백업 유틸리티",
}
I18N["de"] = {
    **I18N["en"],
    "default_hint": "(Standard {default})", "back_hint": "b zum Zurückgehen",
    "custom_plan": "Benutzerdefinierter Zeitplan", "retain_all": "Alle behalten",
    "schedule_not_installed": "Kein Zeitplan installiert", "schedule_installed": "Zeitplan installiert", "no_crontab": "crontab ist auf diesem System nicht verfügbar",
    "menu_now_backup": "Jetzt sichern", "menu_schedule": "Zeitplan", "menu_reset": "Konfiguration zurücksetzen", "menu_exit": "Beenden",
    "menu_now_backup_desc": "Backup starten oder zuerst konfigurieren", "menu_schedule_desc": "Automatische Sicherung konfigurieren", "menu_reset_desc": "Lokale Konfiguration und Zeitplan löschen", "menu_exit_desc": "Diese Sitzung beenden",
    "label_source": "Quelle", "label_backup": "Ziel", "label_format": "Format", "label_items": "Elemente", "label_schedule": "Zeitplan",
    "current_config": "Aktuelle Konfiguration", "panel_basics": "Grundlagen", "panel_behavior": "Backup-Verhalten", "panel_targets": "Ziele",
    "field_source": "Quelle", "field_backup": "Ziel", "field_format": "Format", "field_retention": "Aufbewahrung",
    "init_wizard": "Einrichtungsassistent", "init_intro_1": "Schnelle Grundeinrichtung für die erste Nutzung.", "init_intro_2": "Wenn Sie unsicher sind, drücken Sie Enter für den Standardwert.",
    "step_source": "OpenClaw-Datenverzeichnis festlegen", "step_backup": "Backup-Zielverzeichnis festlegen", "step_format": "Komprimierungsformat wählen", "step_retention": "Aufbewahrungsregel festlegen",
    "default_path": "Standardpfad", "new_path": "Neuer Pfad",
    "default_source_help": "~/.openclaw, bei keiner Änderung Enter für den nächsten Schritt.", "default_backup_help": "{value}, bei keiner Änderung Enter für den nächsten Schritt.",
    "new_path_help": "Falls nötig, neuen vollständigen Pfad eingeben und Enter drücken.", "format_hint": "zip wird für beste Kompatibilität empfohlen.",
    "unsupported_format": "Nur zip / tar.gz / tar.zst werden unterstützt", "return": "Zurück",
    "keep_all": "Alle behalten", "keep_recent_3": "Neueste 3 behalten", "keep_recent_5": "Neueste 5 behalten", "keep_recent_10": "Neueste 10 behalten",
    "invalid_keep_default": "Ungültige Auswahl, Standard: neueste 10 behalten.",
    "init_done": "Einrichtung abgeschlossen. Konfiguration gespeichert unter {path}", "next_step": "Nächster Schritt", "next_backup": "Im Hauptmenü [1] Jetzt sichern auswählen.",
    "backup_entry": "Jetzt sichern", "edit_config": "Konfiguration bearbeiten", "choose_action": "Aktion wählen", "backed_out": "Zurückgegangen.",
    "reset_title": "Konfiguration zurücksetzen", "reset_warn_1": "Gespeicherte Pfade, Komprimierungsformat, Aufbewahrungsregel und Zeitplan dieses Skripts werden gelöscht.",
    "reset_warn_2": "Vorhandene Backup-Dateien und OpenClaw-Quelldaten bleiben erhalten.", "confirm_reset": "Zurücksetzen fortsetzen?",
    "reset_done": "Lokale Konfiguration gelöscht", "removed_jobs": "{count} Zeitpläne entfernt", "no_jobs_found": "Keine zu entfernenden Zeitpläne gefunden.", "reset_next": "Beim nächsten Start werden wieder die Standardwerte verwendet.",
    "schedule_title": "Zeitplan", "schedule_state": "Status", "schedule_method": "Modus", "schedule_expr": "Ausdruck", "schedule_cmd": "Befehl", "schedule_reboot": "Nach Neustart weiter aktiv; während Aus/Schlaf verpasste Läufe werden nicht nachgeholt.",
    "current_schedule": "Current Schedule", "preset_6h": "Alle 6 Stunden", "preset_daily": "Täglich 02:00", "preset_weekly": "Sonntag 02:00", "preset_monthly": "Monatlich am 1. um 02:00",
    "preset_custom": "Benutzerdefinierter cron-Ausdruck", "choose_frequency": "Frequenz wählen", "enter_cron": "cron-Ausdruck eingeben", "plan": "Plan", "install_method": "Installationsart",
    "crontab_unchanged": "Aktueller Zeitplan unverändert", "crontab_updated": "crontab aktualisiert", "crontab_installed": "crontab installiert",
    "main_prompt": "1-4 eingeben, Enter beendet.", "bye": "Tschüss.", "invalid_main": "Ungültige Auswahl. Bitte 1-4 eingeben.",
    "target_main_config": "Hauptkonfigurationsdatei", "target_credentials": "API-Schlüssel und Tokens", "target_agents": "Agent-Konfigurationen und Auth-Profile", "target_workspace": "Memory, SOUL.md, Benutzerdateien", "target_cron": "Zeitplan-Konfiguration",
    "lang_title": "Sprache wählen", "lang_prompt": "Sprache", "weekday_0": "So", "weekday_1": "Mo", "weekday_2": "Di", "weekday_3": "Mi", "weekday_4": "Do", "weekday_5": "Fr", "weekday_6": "Sa", "weekday_7": "So",
    "every_minutes": "Alle {value} Minuten ausführen", "every_hours": "Alle {value} Stunden ausführen", "daily_at": "Täglich um {time}", "weekly_at": "Jeden {weekday} um {time}",
    "retain_recent": "Neueste {count} Backups behalten (min. {min_count}, max. {max_days} Tage)", "brand_tagline": "OpenClaw-Backup-Dienstprogramm",
}


def tr(key: str, **kwargs) -> str:
    bundle = I18N.get(CURRENT_LANG, I18N["zh"])
    template = bundle.get(key, I18N["en"].get(key, key))
    return template.format(**kwargs)


def set_lang(cfg: dict):
    global CURRENT_LANG
    CURRENT_LANG = cfg.get("language", "en")


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
    hint = tr("default_hint", default=default) if default else ""
    console.print(f"[{ACCENT}]{label}[/]{hint}")
    return safe_input("", default=default)


def safe_prompt_with_back(label: str, default: str = "") -> str | None:
    hint = tr("default_hint", default=default) if default else ""
    console.print(f"[{ACCENT}]{label}[/]{hint}  [{MUTED}]{tr('back_hint')}[/]")
    value = safe_input("", default=default)
    if value.lower() in ("b", "back"):
        return None
    return value


def content_width(max_width: int = 112) -> int:
    return max(72, min(max_width, console.size.width - 4))


def _compact_path(value: str, max_len: int = 24) -> str:
    home = str(Path.home())
    display = str(Path(value).expanduser())
    if display.startswith(home):
        display = "~" + display[len(home):]
    if len(display) <= max_len:
        return display
    head = max_len // 2 - 1
    tail = max_len - head - 1
    return f"{display[:head]}…{display[-tail:]}"


def _display_path(value: str) -> str:
    home = str(Path.home())
    display = str(Path(value).expanduser())
    if display.startswith(home):
        display = "~" + display[len(home):]
    return display


def choose_language(cfg: dict):
    if not sys.stdin.isatty():
        return
    current = cfg.get("language", "zh")
    current_index = next((i for i, (code, _) in enumerate(LANG_OPTIONS, 1) if code == current), 2)
    console.print(Rule(f"[bold {ACCENT}]{tr('lang_title')}", style=ACCENT))
    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column(style=f"bold {ACCENT}", width=4)
    tbl.add_column(style=TEXT_DARK)
    for i, (_, label) in enumerate(LANG_OPTIONS, 1):
        tbl.add_row(f"[{i}]", label)
    console.print(tbl)
    choice = safe_prompt(tr("lang_prompt"), default=str(current_index))
    try:
        idx = max(1, min(len(LANG_OPTIONS), int(choice))) - 1
    except ValueError:
        idx = current_index - 1
    cfg["language"] = LANG_OPTIONS[idx][0]
    save_config(cfg)
    set_lang(cfg)


def _describe_cron(expr: str) -> str:
    parts = expr.split()
    if len(parts) != 5:
        return tr("custom_plan")
    minute, hour, day, month, weekday = parts
    weekday_names = {str(i): tr(f"weekday_{i}") for i in range(8)}
    if minute.startswith("*/") and hour == day == month == weekday == "*":
        return tr("every_minutes", value=minute[2:])
    if minute == "0" and hour.startswith("*/") and day == month == weekday == "*":
        return tr("every_hours", value=hour[2:])
    if day == month == "*" and weekday == "*" and minute.isdigit() and hour.isdigit():
        return tr("daily_at", time=f"{int(hour):02d}:{int(minute):02d}")
    if day == month == "*" and minute.isdigit() and hour.isdigit() and weekday.isdigit():
        label = weekday_names.get(weekday, weekday)
        return tr("weekly_at", weekday=label, time=f"{int(hour):02d}:{int(minute):02d}")
    return tr("custom_plan")


def _describe_retention(retention: dict) -> str:
    max_count = retention.get("max_count", 10)
    max_days = retention.get("max_days", 30)
    min_count = retention.get("min_count", 3)
    if max_count <= 0 or max_days <= 0:
        return tr("retain_all")
    return tr("retain_recent", count=max_count, min_count=min_count, max_days=max_days)


def _get_schedule_status(script: Path) -> dict:
    status = {
        "installed": False,
        "expr": "",
        "line": "",
        "command": "",
        "summary": tr("schedule_not_installed"),
    }
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
    except FileNotFoundError:
        status["summary"] = tr("no_crontab")
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
            "summary": _describe_cron(expr) if expr else tr("schedule_installed"),
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
    if console.size.width < 90:
        t = Text()
        t.append("🦞 ", style="bold #ff6d67")
        t.append("CLAWBACKUP", style="bold #ff6d67")
        sub = Text()
        sub.append(f"{tr('brand_tagline')}  ", style=MUTED)
        sub.append("v0.1.1", style=f"bold {ACCENT}")
        return Group(align_center(t), align_center(sub))

    claw_lines = [
        "  ██████╗  ██╗        █████╗   ██╗    ██╗",
        " ██╔════╝  ██║       ██╔══██╗  ██║    ██║",
        " ██║       ██║       ███████║  ██║ █╗ ██║",
        " ██║       ██║       ██╔══██║  ██║███╗██║",
        " ╚██████╗  ███████╗  ██║  ██║  ╚███╔███╔╝",
        "  ╚═════╝  ╚══════╝  ╚═╝  ╚═╝   ╚══╝╚══╝ ",
    ]
    backup_lines = [
        " ██████╗   █████╗    ██████╗  ██╗  ██╗  ██╗   ██╗  ██████╗ ",
        " ██╔══██╗ ██╔══██╗  ██╔════╝  ██║ ██╔╝  ██║   ██║  ██╔══██╗",
        " ██████╔╝ ███████║  ██║       █████╔╝   ██║   ██║  ██████╔╝",
        " ██╔══██╗ ██╔══██║  ██║       ██╔═██╗   ██║   ██║  ██╔═══╝ ",
        " ██████╔╝ ██║  ██║  ╚██████╗  ██║  ██╗  ╚██████╔╝  ██║     ",
        " ╚═════╝  ╚═╝  ╚═╝   ╚═════╝  ╚═╝  ╚═╝   ╚═════╝   ╚═╝     ",
    ]
    row_colors = ["#ff9a95", "#ff887f", "#ff766e", "#ff655e", "#ff554f", "#ff6f6a"]

    eyebrow = Text()
    eyebrow.append("─" * 10 + "  ", style=f"dim {ACCENT_SOFT}")
    eyebrow.append("O P E N C L A W  B A C K U P  U T I L I T Y", style=f"bold {ACCENT_DEEP}")
    eyebrow.append("  " + "─" * 10, style=f"dim {ACCENT_SOFT}")

    lines = [align_center(eyebrow)]
    for i, raw in enumerate(claw_lines):
        lines.append(align_center(Text(raw, style=f"bold {row_colors[i]}")))
    lines.append(Text(""))
    for i, raw in enumerate(backup_lines):
        lines.append(align_center(Text(raw, style=f"bold {row_colors[i]}")))

    brand = Text()
    brand.append("🦞", style="bold #ff6d67")
    brand.append("  ClawBackup", style=f"bold {TEXT_DARK}")
    brand.append("  ", style="")
    brand.append("v0.1.1", style=f"bold {ACCENT}")
    brand.append("  ", style="")
    brand.append(tr("brand_tagline"), style=MUTED)
    lines.append(Text(""))
    lines.append(align_center(brand))
    return Group(*lines)


def print_header(compact: bool = False):
    console.print()
    if compact:
        console.print(Rule(f"[bold {ACCENT}]ClawBackup", style=ACCENT))
    else:
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
    schedule = _get_schedule_status(Path(__file__).resolve())
    summary = Table.grid(expand=True)
    summary.add_column(ratio=3, style=TEXT_DARK, no_wrap=True)
    summary.add_column(ratio=6, style=TEXT_DARK, no_wrap=True)
    summary.add_column(ratio=2, style=TEXT_DARK, justify="right", no_wrap=True)
    summary.add_row(
        Text.assemble(
            (f"{tr('label_source')}  ", f"bold {ACCENT_DEEP}"),
            (_compact_path(cfg["openclaw_dir"]), TEXT_DARK),
        ),
        Text.assemble(
            (f"{tr('label_backup')}  ", f"bold {ACCENT_DEEP}"),
            (_display_path(cfg["backup_dir"]), TEXT_DARK),
        ),
        Text.assemble(
            (f"{tr('label_items')} ", f"bold {ACCENT_DEEP}"),
            (str(sum(1 for t in cfg["targets"] if t.get("enabled"))), TEXT_DARK),
        ),
    )

    quick = Table.grid(expand=True, padding=(0, 1))
    quick.add_column(style=f"bold {ACCENT}", width=5, no_wrap=True)
    quick.add_column(style=ACCENT_DEEP, width=2, no_wrap=True)
    quick.add_column(style=f"bold {TEXT_DARK}", width=10, no_wrap=True)
    quick.add_column(style=MUTED)
    quick_items = [
        ("1", "▸", tr("menu_now_backup"), tr("menu_now_backup_desc")),
        ("2", "◷", tr("menu_schedule"), tr("menu_schedule_desc")),
        ("3", "↻", tr("menu_reset"), tr("menu_reset_desc")),
        ("4", "✦", tr("menu_exit"), tr("menu_exit_desc")),
    ]
    for key, icon, name, desc in quick_items:
        quick.add_row(Text(f"[{key}]", style=f"bold {ACCENT}"), icon, name, desc)

    footer = Table.grid(expand=True)
    footer.add_column()
    footer.add_row(Text(f"{tr('label_schedule')}：{schedule['summary']}", style=MUTED))

    body = Group(summary, Text(""), quick, Text(""), footer)
    console.print(Align.center(Panel(body, border_style=ACCENT, padding=(0, 1), style=f"on {SURFACE}", width=min(96, content_width(96)))))


def print_help():
    usage = Table.grid(padding=(0, 2))
    usage.add_column(style=f"bold {ACCENT_DEEP}", width=14)
    usage.add_column(style=TEXT_DARK)
    usage.add_row("启动菜单", "python3 clawbackup.py")
    usage.add_row("立即备份", "python3 clawbackup.py backup")
    usage.add_row("定时任务", "python3 clawbackup.py schedule")
    usage.add_row("初始化配置", "python3 clawbackup.py init")
    usage.add_row("重置配置", "python3 clawbackup.py reset")
    usage.add_row("高级命令", "history / config / log")

    first_use = Table.grid(padding=(0, 2))
    first_use.add_column(style=f"bold {ACCENT_DEEP}", width=4)
    first_use.add_column(style=TEXT_DARK)
    first_use.add_row("1.", "进入主菜单后按 [1] 立即备份。")
    first_use.add_row("2.", "如果还没配过，就在下一层选择 [2] 编辑配置。")
    first_use.add_row("3.", "配置完成后执行第一份备份。")
    first_use.add_row("4.", "需要自动化时，再进入 [2] 定时设置。")
    first_use.add_row("5.", "只有高级需求时，才用 history / config / log。")

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


def _render_config_tree(cfg: dict) -> Group:
    basics = Table.grid(padding=(0, 1))
    basics.add_column(style=f"bold {ACCENT_DEEP}", width=12)
    basics.add_column(style=TEXT_DARK)
    basics.add_row(tr("field_source"), cfg["openclaw_dir"])
    basics.add_row(tr("field_backup"), cfg["backup_dir"])

    behavior = Table.grid(padding=(0, 1))
    behavior.add_column(style=f"bold {ACCENT_DEEP}", width=12)
    behavior.add_column(style=TEXT_DARK)
    behavior.add_row(tr("field_format"), cfg["compress_format"])
    behavior.add_row(tr("field_retention"), _describe_retention(cfg["retention"]))

    targets = Table(box=box.SIMPLE, show_header=False, padding=(0, 1), expand=True)
    targets.add_column(style=f"bold {ACCENT}", width=3, no_wrap=True)
    targets.add_column(style=TEXT_DARK, width=16, no_wrap=True)
    targets.add_column(style="dim")
    for t in cfg["targets"]:
        icon = ICONS.get(t["path"], "📁")
        st = "✓" if t.get("enabled") else "○"
        targets.add_row(st, f"{icon} {t['path']}", tr(TARGET_DESC_KEYS.get(t["path"], t["desc"])))

    return Group(
        Text(tr("current_config"), style=f"bold {ACCENT}"),
        Panel(basics, title=tr("panel_basics"), border_style=ACCENT_SOFT, style=f"on {SURFACE}"),
        Panel(behavior, title=tr("panel_behavior"), border_style=ACCENT_SOFT, style=f"on {SURFACE}"),
        Panel(targets, title=tr("panel_targets"), border_style=ACCENT_SOFT, style=f"on {SURFACE}"),
    )


def cmd_init(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]{tr('init_wizard')}", style=ACCENT))
    console.print(f"  [{MUTED}]{tr('init_intro_1')}[/]")
    console.print(f"  [{MUTED}]{tr('init_intro_2')}[/]")
    console.print()

    console.print(f"  [{ACCENT}]1/4[/] {tr('step_source')}")
    console.print(f"  [{ACCENT}]{tr('default_path')}[/]：[{TEXT_DARK}]{tr('default_source_help')}[/]")
    console.print(f"  [{ACCENT}]{tr('new_path')}[/]：[{TEXT_DARK}]{tr('new_path_help')}[/]")
    value = safe_prompt_with_back(f"{tr('panel_basics')}【{tr('field_source')}】", cfg["openclaw_dir"])
    if value is None:
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return False
    cfg["openclaw_dir"] = value
    console.print()

    console.print(f"  [{ACCENT}]2/4[/] {tr('step_backup')}")
    console.print(f"  [{ACCENT}]{tr('default_path')}[/]：[{TEXT_DARK}]{tr('default_backup_help', value=cfg['backup_dir'])}[/]")
    console.print(f"  [{ACCENT}]{tr('new_path')}[/]：[{TEXT_DARK}]{tr('new_path_help')}[/]")
    value = safe_prompt_with_back(f"{tr('panel_basics')}【{tr('field_backup')}】", cfg["backup_dir"])
    if value is None:
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return False
    cfg["backup_dir"] = value
    console.print()

    console.print(f"  [{ACCENT}]3/4[/] {tr('step_format')}")
    console.print(f"  [{MUTED}]{tr('format_hint')}[/]")
    fmt_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    fmt_tbl.add_column(style=f"bold {ACCENT}", width=6)
    fmt_tbl.add_column(style="white")
    fmt_tbl.add_row("[1]", "zip")
    fmt_tbl.add_row("[2]", "tar.gz")
    fmt_tbl.add_row("[3]", "tar.zst")
    console.print(fmt_tbl)
    format_map = {
        "1": "zip",
        "2": "tar.gz",
        "3": "tar.zst",
        "zip": "zip",
        "tar.gz": "tar.gz",
        "tar.zst": "tar.zst",
    }
    while True:
        value = safe_prompt_with_back(f"{tr('panel_behavior')}【{tr('field_format')}】", cfg.get("compress_format", "zip"))
        if value is None:
            console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
            return False
        if value in format_map:
            cfg["compress_format"] = format_map[value]
            break
        console.print(f"[{ERR}]{tr('unsupported_format')}[/]")
    console.print()

    console.print(f"  [{ACCENT}]4/4[/] {tr('step_retention')}")
    presets = [
        ("1", tr("keep_all"), {"max_count": 0, "max_days": 0, "min_count": 0}),
        ("2", tr("keep_recent_3"), {"max_count": 3, "max_days": 3650, "min_count": 3}),
        ("3", tr("keep_recent_5"), {"max_count": 5, "max_days": 3650, "min_count": 3}),
        ("4", tr("keep_recent_10"), {"max_count": 10, "max_days": 3650, "min_count": 3}),
    ]
    pick_tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    pick_tbl.add_column(style=f"bold {ACCENT}", width=4)
    pick_tbl.add_column(style="white")
    for key, label, _ in presets:
        pick_tbl.add_row(f"[{key}]", label)
    pick_tbl.add_row("[5]", tr("return"))
    console.print(pick_tbl)
    choice = safe_prompt(f"{tr('panel_behavior')}【{tr('field_retention')}】", default="4")
    if choice.lower() in ("5", "b", "back"):
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return False
    preset = next((item for item in presets if item[0] == choice), None)
    if not preset:
        console.print(f"[{ERR}]{tr('invalid_keep_default')}[/]")
        preset = presets[3]
    cfg["retention"].update(preset[2])

    save_config(cfg)
    console.print(f"\n  [{OK}]✓  {tr('init_done', path=CONFIG_PATH)}[/]")

    root = Path(cfg["openclaw_dir"]).expanduser()
    bdir = Path(cfg["backup_dir"]).expanduser()
    console.print(f"  [{MUTED}]{tr('field_source')}：{root}[/]")
    console.print(f"  [{MUTED}]{tr('field_backup')}：{bdir}[/]")
    console.print(f"  [bold {ACCENT}]{tr('next_step')}：[/][bold {TEXT_DARK}]{tr('next_backup')}[/]\n")
    return True


def cmd_backup_entry(cfg: dict):
    console.print(Rule(f"[bold {ACCENT}]{tr('backup_entry')}", style=ACCENT))
    console.print(_render_config_tree(cfg))
    console.print()

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column(style=f"bold {ACCENT}", width=4)
    table.add_column(style="white")
    table.add_row("[1]", tr("backup_entry"))
    table.add_row("[2]", tr("edit_config"))
    table.add_row("[3]", tr("return"))
    console.print(table)

    choice = safe_prompt(tr("choose_action"), default="1").lower()
    if choice in ("3", "b", "back"):
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return
    if choice == "2":
        if cmd_init(cfg):
            cfg.update(load_config())
        return
    cmd_backup(cfg)


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
    console.print(Rule(f"[bold {ACCENT}]{tr('reset_title')}", style=ACCENT))
    console.print(f"  [{WARN}]{tr('reset_warn_1')}[/]")
    console.print(f"  [{MUTED}]{tr('reset_warn_2')}[/]")
    console.print()

    if not Confirm.ask(f"[{ERR}]{tr('confirm_reset')}[/]", default=False):
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return

    removed_jobs = _remove_cron_jobs(Path(__file__).resolve())
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()

    console.print(f"  [{OK}]✓  {tr('reset_done')}[/]")
    if removed_jobs:
        console.print(f"  [{OK}]✓  {tr('removed_jobs', count=removed_jobs)}[/]")
    else:
        console.print(f"  [{MUTED}]{tr('no_jobs_found')}[/]")
    write_log("执行配置重置")
    console.print(f"  [{MUTED}]{tr('reset_next')}[/]\n")


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
    ret = cfg["retention"]
    console.print(_render_config_tree(cfg))
    console.print()

    action = Prompt.ask(
        f"[{ACCENT}]操作[/] [[bold]1[/]改目录  [bold]2[/]保留策略  [bold]3[/]备份项目  [bold]e[/]高级编辑  [bold]回车[/]返回]",
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
    console.print(Rule(f"[bold {ACCENT}]{tr('schedule_title')}", style=ACCENT))
    script = Path(__file__).resolve()
    schedule = _get_schedule_status(script)

    status_tbl = Table.grid(padding=(0, 1))
    status_tbl.add_column(style=f"bold {ACCENT_DEEP}", width=10)
    status_tbl.add_column(style="white")
    status_tbl.add_row(tr("schedule_state"), tr("schedule_installed") if schedule["installed"] else tr("schedule_not_installed"))
    status_tbl.add_row(tr("schedule_method"), schedule["summary"])
    if schedule["expr"]:
        status_tbl.add_row(tr("schedule_expr"), schedule["expr"])
    if schedule["command"]:
        status_tbl.add_row(tr("schedule_cmd"), schedule["command"])
    status_tbl.add_row(" ", tr("schedule_reboot"))
    console.print(Align.center(Panel(status_tbl, title=tr("current_schedule"), border_style=ACCENT_SOFT, padding=(0, 1), style=f"on {SURFACE}", width=content_width())))
    console.print()

    presets = [
        ("0 */6 * * *",  tr("preset_6h")),
        ("0 2 * * *",    tr("preset_daily")),
        ("0 2 * * 0",    tr("preset_weekly")),
        ("0 2 1 * *",    tr("preset_monthly")),
        ("custom",       tr("preset_custom")),
    ]

    tbl = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    tbl.add_column(style=f"bold {ACCENT}", width=4)
    tbl.add_column(style=MUTED, width=20)
    tbl.add_column(style="white")
    for i, (expr, label) in enumerate(presets, 1):
        tbl.add_row(f"[{i}]", label, "" if expr == "custom" else expr)
    tbl.add_row("[6]", tr("return"), "")
    console.print(tbl)

    choice = safe_prompt(tr("choose_frequency"), default="1")
    if choice.lower() in ("6", "b", "back"):
        console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
        return
    try:
        idx = int(choice) - 1
        expr, label = presets[idx]
    except (ValueError, IndexError):
        console.print(f"[{ERR}]{tr('invalid_main')}[/]"); return

    if expr == "custom":
        expr = safe_prompt_with_back(tr("enter_cron"))
        if expr is None:
            console.print(f"[{MUTED}]{tr('backed_out')}[/]\n")
            return

    console.print(f"\n  {tr('plan')}：[{ACCENT}]{expr}[/]  [{MUTED}]({_describe_cron(expr) if expr != 'custom' else label})[/]")
    script = str(script)

    if platform.system() == "Linux":
        console.print(f"[{ACCENT}]{tr('install_method')}[/] [bold]1[/] systemd timer  [bold]2[/] crontab")
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
    rows = [row for row in existing.splitlines() if row.strip()]
    matched = [row for row in rows if script in row]

    if matched:
        if any(row.strip() == line for row in matched):
            console.print(f"  [{MUTED}]{tr('crontab_unchanged')}[/]")
            console.print(f"  [{MUTED}]{line}[/]")
            return
        rows = [row for row in rows if script not in row]
        rows.append(line)
        payload = "\n".join(rows) + "\n"
        subprocess.run(["crontab", "-"], input=payload, text=True, check=True)
        console.print(f"  [{OK}]✓  {tr('crontab_updated')}[/]")
        console.print(f"  [{MUTED}]{line}[/]")
        return

    payload = (existing.rstrip() + "\n" if existing.strip() else "") + f"{line}\n"
    subprocess.run(["crontab", "-"], input=payload, text=True, check=True)
    console.print(f"  [{OK}]✓  {tr('crontab_installed')}[/]")
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
    "1": cmd_backup_entry,
    "2": cmd_schedule,
    "3": cmd_reset,
}


def main():
    # 支持直接传子命令：ocbackup.py backup / list / log ...
    if len(sys.argv) > 1:
        alias = {"init": "init", "backup": "backup", "history": "history", "config": "config", "schedule": "schedule", "log": "log", "reset": "reset"}
        key = alias.get(sys.argv[1])
        if key:
            cfg = load_config()
            set_lang(cfg)
            print_header(compact=True)
            direct_commands = {
                "init": cmd_init,
                "backup": cmd_backup,
                "history": cmd_history,
                "config": cmd_config,
                "schedule": cmd_schedule,
                "log": cmd_log,
                "reset": cmd_reset,
            }
            direct_commands[key](cfg)
            return
        elif sys.argv[1] in ("-h", "--help"):
            print_help()
            return

    # 交互主菜单
    cfg = load_config()
    set_lang(cfg)
    choose_language(cfg)
    print_header(compact=False)

    while True:
        print_menu(cfg)
        console.print(f"[{MUTED}]{tr('main_prompt')}[/]")
        console.print(f"[bold {ACCENT}]>[/]")
        choice = safe_input("", default="4").lower()
        console.print()

        if choice in ("4", "q", "quit", "exit", ""):
            console.print(f"[{MUTED}]{tr('bye')}[/]\n")
            break

        fn = COMMANDS.get(choice)
        if fn:
            fn(cfg)
            cfg = load_config()
            set_lang(cfg)
        else:
            console.print(f"[{ERR}]{tr('invalid_main')}[/]\n")


if __name__ == "__main__":
    main()

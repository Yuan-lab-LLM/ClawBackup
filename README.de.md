# ClawBackup

<p align="center">
  <img src="./docs/assets/clawbackup-banner-fredoka2.png" alt="ClawBackup banner" width="920" />
</p>

<p align="center">
  Ein lokales Backup-Werkzeug für OpenClaw-Workspaces mit schnellem Ersteinstieg, geplanten Backups und klaren CLI-basierten Wiederherstellungsabläufen.
</p>

<p align="center">
  <strong>Sprachen:</strong>
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a> |
  <a href="./README.ja.md">日本語</a> |
  <a href="./README.ko.md">한국어</a> |
  Deutsch
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Backup%20Utility-ff7b72?style=for-the-badge" alt="OpenClaw Backup Utility" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/CLI-Multilingual-00c2d1?style=for-the-badge" alt="CLI Multilingual" />
  <img src="https://img.shields.io/badge/License-MIT-2ea44f?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <a href="#warum-clawbackup">Warum ClawBackup</a> |
  <a href="#was-gesichert-wird">Was gesichert wird</a> |
  <a href="#kernfunktionen">Kernfunktionen</a> |
  <a href="#schnellstart">Schnellstart</a> |
  <a href="#erster-start">Erster Start</a> |
  <a href="#entwicklung-und-release">Entwicklung und Release</a>
</p>

## Warum ClawBackup

Ein OpenClaw-Workspace besteht meist nicht nur aus einer Konfigurationsdatei. Häufig gehören auch Zugangsdaten, Agent-Profile, Speicherdateien, Workspace-Daten und geplante Aufgaben dazu. Ein manuelles Kopieren ist einmalig leicht, aber langfristig schwer konsistent zu halten.

ClawBackup soll lokale Backups einfacher und wiederholbar machen:

- das erste Backup über einen klaren CLI-Ablauf abschließen
- geplante Backups ohne schwere Einrichtung aktivieren
- vorhandene Archive ansehen, wiederherstellen oder löschen
- Installation und Verteilung über Standard-Python-Workflows ermöglichen

Besonders geeignet ist es für:

- einzelne OpenClaw-Nutzer, die zuverlässige lokale Backups wollen
- Nutzer, die Agent-Konfigurationen häufig ändern und eine Rückfalloption brauchen
- Teams, die einen standardisierten Backup-Workflow statt manueller Kopiervorgänge wollen

## Was gesichert wird

Standardmäßig sichert ClawBackup diese OpenClaw-Inhalte:

- `openclaw.json`: Hauptkonfigurationsdatei
- `credentials/`: API-Schlüssel und Tokens
- `agents/`: Agent-Konfigurationen und Auth-Profile
- `workspace/`: Speicherdateien, `SOUL.md` und Nutzerdateien
- `cron/`: Konfiguration geplanter Aufgaben

Standardpfade:

- OpenClaw-Datenverzeichnis: `~/.openclaw`
- Backup-Zielverzeichnis: `~/openclaw-backups`
- Komprimierungsformat: `zip`
- Standard-Aufbewahrung: letzte `10`, mindestens `3`, alles älter als `30` Tage entfernen

## Kernfunktionen

### Benutzerorientierte CLI

Die Startseite konzentriert sich auf vier Hauptaktionen:

- Jetzt sichern
- Zeitplan
- Konfiguration zurücksetzen
- Beenden

Verlauf, Logs und Detailkonfiguration bleiben verfügbar, überladen aber nicht den ersten Bildschirm.

### Mehrsprachiger Start

Derzeit unterstützte Sprachen:

- English
- 简体中文
- 日本語
- 한국어
- Deutsch

### Geplante Backups

Vorgefertigte Zeitpläne:

- alle 6 Stunden
- täglich um 02:00
- jeden Sonntag um 02:00
- am 1. jedes Monats um 02:00
- benutzerdefinierter cron-Ausdruck

### Aufbewahrungsregeln

Unterstützt sowohl „alles behalten“ als auch „nur die letzten N Backups behalten“.

### Verlauf und Wiederherstellung

Für erzeugte Archive unterstützt ClawBackup:

- Backup-Verlauf anzeigen
- ausgewähltes Backup wiederherstellen
- einzelnes Backup löschen

## Schnellstart

### Empfohlen: Installation mit `pipx`

Falls `pipx` noch nicht installiert ist:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Terminal neu öffnen und stabile Version installieren:

```bash
pipx install "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

Starten:

```bash
clawbackup
```

### Neueste Version aus `main`

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### Installation aus lokalem Quellcode

```bash
python3 -m pip install .
```

oder:

```bash
pipx install .
```

## Erster Start

Empfohlener Ablauf:

1. `clawbackup` starten
2. Quell- und Backup-Verzeichnis prüfen oder anpassen
3. erstes Backup ausführen
4. Zeitplan nur dann einrichten, wenn automatische Ausführung gewünscht ist

Kürzester Weg:

```bash
clawbackup
```

Direkt per Befehl:

```bash
clawbackup init
clawbackup backup
```

## Häufige Befehle

### Hauptablauf

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

### Erweiterte Befehle

```bash
clawbackup history
clawbackup config
clawbackup log
```

## Upgrade und Deinstallation

### Auf den neuesten Stand von `main`

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### Bestimmte Version installieren oder aktualisieren

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

### Deinstallation

Bei Installation mit `pipx`:

```bash
pipx uninstall clawbackup
```

Bei Installation mit `pip`:

```bash
python3 -m pip uninstall clawbackup
```

## Lokale Dateien

Verwendete Laufzeitdateien:

- Konfigurationsdatei: `~/.config/clawbackup/config.json`
- Logdatei: `~/.config/clawbackup/clawbackup.log`

Wenn du den lokalen Zustand vollständig zurücksetzen willst, nutze die Reset-Funktion in der App oder lösche die Konfigurationsdatei manuell.

## Entwicklung und Release

### Lokal starten

```bash
python3 clawbackup.py
```

oder:

```bash
python3 -m clawbackup
```

### Syntaxprüfung

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### Versionsstellen

Vor einem Release diese Stellen synchron halten:

- `pyproject.toml`
- `src/clawbackup/__init__.py`
- UI-Versionsanzeige in `src/clawbackup/cli.py`

### Homebrew-Dateien

- `Formula/clawbackup.rb`
- `scripts/render_homebrew_formula.py`
- `scripts/homebrew_sha256.sh`
- `scripts/test_homebrew_local.sh`

### Release-Checkliste

1. Versionsnummern aktualisieren
2. Änderungen committen
3. Tag wie `v0.1.1` anlegen
4. `main` und Tag pushen
5. GitHub Release prüfen
6. Falls nötig Homebrew-Formel synchronisieren

```bash
git add .
git commit -m "Release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz.

## Mitwirken

Issues und Pull Requests sind willkommen, besonders rund um Backup-Abläufe, Wiederherstellung und Zeitplan-Verbesserungen für OpenClaw.

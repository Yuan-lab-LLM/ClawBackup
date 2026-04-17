# ClawBackup

<p align="center">
  <img src="./docs/assets/clawbackup-banner-fredoka2.png" alt="ClawBackup banner" width="920" />
</p>

<p align="center">
  OpenClaw 워크스페이스를 위한 로컬 백업 도구로, 빠른 초기 설정, 예약 백업, CLI 기반 복구 흐름을 간결하게 제공합니다.
</p>

<p align="center">
  <strong>언어:</strong>
  <a href="./README.md">English</a> |
  <a href="./README.zh-CN.md">简体中文</a> |
  <a href="./README.ja.md">日本語</a> |
  한국어 |
  <a href="./README.de.md">Deutsch</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/OpenClaw-Backup%20Utility-ff7b72?style=for-the-badge" alt="OpenClaw Backup Utility" />
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+" />
  <img src="https://img.shields.io/badge/CLI-Multilingual-00c2d1?style=for-the-badge" alt="CLI Multilingual" />
  <img src="https://img.shields.io/badge/License-MIT-2ea44f?style=for-the-badge" alt="MIT License" />
</p>

<p align="center">
  <a href="#왜-clawbackup인가">왜 ClawBackup인가</a> |
  <a href="#백업-대상">백업 대상</a> |
  <a href="#핵심-기능">핵심 기능</a> |
  <a href="#빠른-시작">빠른 시작</a> |
  <a href="#첫-사용">첫 사용</a> |
  <a href="#개발과-배포">개발과 배포</a>
</p>

## 왜 ClawBackup인가

OpenClaw 워크스페이스에는 단순한 설정 파일만 있는 것이 아니라, 자격 증명, Agent 프로필, 메모리 파일, 워크스페이스 데이터, 예약 작업까지 함께 들어 있는 경우가 많습니다. 수동 복사는 한 번은 쉽지만, 계속 정확하게 유지하기는 어렵습니다.

ClawBackup 은 로컬 백업을 더 단순하고 반복 가능하게 만들기 위한 도구입니다.

- 명확한 CLI 흐름으로 첫 백업을 빠르게 완료
- 무거운 설정 없이 자동 백업 활성화
- 기존 아카이브를 조회, 복원, 삭제 가능
- 표준 Python 패키징 방식으로 설치 및 배포 가능

다음과 같은 경우에 특히 잘 맞습니다.

- OpenClaw 워크스페이스를 주기적으로 보존하고 싶은 개인 사용자
- Agent 설정을 자주 바꾸며 롤백 수단이 필요한 사용자
- 수동 절차 대신 표준화된 백업 도구를 팀에 도입하려는 경우

## 백업 대상

기본적으로 다음 OpenClaw 핵심 항목을 백업합니다.

- `openclaw.json`: 메인 설정 파일
- `credentials/`: API 키와 토큰
- `agents/`: Agent 설정과 인증 프로필
- `workspace/`: 메모리, `SOUL.md`, 사용자 파일
- `cron/`: 예약 작업 설정

기본 경로:

- OpenClaw 데이터 디렉터리: `~/.openclaw`
- 백업 출력 디렉터리: `~/openclaw-backups`
- 압축 형식: `zip`
- 기본 보관 정책: 최신 `10`개 유지, 최소 `3`개 유지, `30`일보다 오래된 항목 정리

## 핵심 기능

### 사용자 중심 CLI

기본 홈 화면은 네 가지 핵심 작업에 집중합니다.

- 지금 백업
- 예약 설정
- 설정 초기화
- 종료

히스토리, 로그, 상세 설정 같은 고급 기능은 남겨 두되 첫 화면을 무겁지 않게 유지합니다.

### 다국어 시작 화면

현재 지원 언어:

- English
- 简体中文
- 日本語
- 한국어
- Deutsch

### 자동 예약 백업

내장 프리셋:

- 6시간마다
- 매일 02:00
- 매주 일요일 02:00
- 매월 1일 02:00
- 사용자 지정 cron 표현식

### 보관 정책

“모두 보관” 또는 “최신 N개만 보관” 전략을 지원합니다.

### 히스토리와 복원

생성된 백업에 대해 다음 작업이 가능합니다.

- 백업 히스토리 조회
- 특정 백업 복원
- 개별 백업 삭제

## 빠른 시작

### 권장: `pipx` 설치

`pipx` 가 아직 없다면:

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

터미널을 다시 연 뒤 안정 버전 설치:

```bash
pipx install "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

실행:

```bash
clawbackup
```

### `main` 최신 코드 설치

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### 로컬 소스에서 설치

```bash
python3 -m pip install .
```

또는:

```bash
pipx install .
```

## 첫 사용

권장 순서:

1. `clawbackup` 실행
2. 필요하면 원본/백업 경로 확인
3. 첫 백업 실행
4. 자동 실행이 필요할 때만 예약 설정

가장 짧은 경로:

```bash
clawbackup
```

직접 명령을 쓰고 싶다면:

```bash
clawbackup init
clawbackup backup
```

## 자주 쓰는 명령

### 기본 흐름

```bash
clawbackup
clawbackup init
clawbackup backup
clawbackup schedule
clawbackup reset
```

### 고급 명령

```bash
clawbackup history
clawbackup config
clawbackup log
```

## 업그레이드와 제거

### 최신 `main` 으로 업그레이드

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@main"
```

### 특정 버전 설치 또는 업그레이드

```bash
pipx install --force "git+https://github.com/Yuan-lab-LLM/ClawBackup.git@v0.1.1"
```

### 제거

`pipx` 로 설치했다면:

```bash
pipx uninstall clawbackup
```

`pip` 로 설치했다면:

```bash
python3 -m pip uninstall clawbackup
```

## 로컬 파일

실행 시 사용하는 파일:

- 설정 파일: `~/.config/clawbackup/config.json`
- 로그 파일: `~/.config/clawbackup/clawbackup.log`

로컬 상태를 완전히 초기화하려면 앱의 초기화 기능을 사용하거나 설정 파일을 직접 삭제하면 됩니다.

## 개발과 배포

### 로컬 실행

```bash
python3 clawbackup.py
```

또는:

```bash
python3 -m clawbackup
```

### 문법 검사

```bash
python3 -m py_compile clawbackup.py src/clawbackup/cli.py src/clawbackup/__init__.py
```

### 버전 위치

릴리스 전에 다음 위치를 맞춰야 합니다.

- `pyproject.toml`
- `src/clawbackup/__init__.py`
- `src/clawbackup/cli.py` 의 UI 버전 문자열

### Homebrew 관련 파일

- `Formula/clawbackup.rb`
- `scripts/render_homebrew_formula.py`
- `scripts/homebrew_sha256.sh`
- `scripts/test_homebrew_local.sh`

### 릴리스 체크리스트

1. 버전 번호 수정
2. 커밋
3. `v0.1.1` 같은 tag 생성
4. `main` 과 tag 푸시
5. GitHub Release 확인
6. 필요하면 Homebrew formula 동기화

```bash
git add .
git commit -m "Release v0.1.1"
git tag v0.1.1
git push origin main --tags
```

## 라이선스

MIT License 로 배포됩니다.

## 기여

Issue 와 Pull Request 를 환영합니다. 특히 OpenClaw 백업, 복원, 예약 개선과 관련된 제안을 환영합니다.

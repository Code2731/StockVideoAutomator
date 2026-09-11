# Stock Video Automator

GUI-based YouTube downloader with seamless AI agent integration via Model Context Protocol (MCP).

## 📥 Downloads / 다운로드

최신 버전의 Stock Video Automator를 다운로드하세요. (Nuitka로 컴파일되어 별도의 파이썬 설치 없이 실행 가능합니다.)

- 🍎 **macOS (Apple Silicon / Intel):** [Download StockVideoAutomator.app.zip](https://github.com/namhyunjun/StockVideoAutomator/releases/latest)
- 🪟 **Windows (64-bit):** [Download StockVideoAutomator.exe](https://github.com/namhyunjun/StockVideoAutomator/releases/latest)

> **안내:**
> - macOS에서는 다운로드 후 앱을 우클릭하고 `열기`를 선택하여 실행 권한을 부여해야 할 수 있습니다.
> - 위 링크는 GitHub Releases 페이지로 연결됩니다. 운영체제에 맞는 파일을 다운로드하세요.

---

## 🚀 Features / 주요 기능
- **직관적인 GUI:** PySide6 기반의 깔끔하고 사용하기 쉬운 인터페이스 제공.
- **다양한 다운로드 옵션:** 비디오, 오디오 추출, 특정 화질 및 코덱 선택 지원.
- **AI 에이전트 연동 (MCP):** Model Context Protocol 브릿지 서버 내장.
- **백그라운드 실행:** 시스템 트레이(작업 표시줄)로 최소화 및 알림 기능 지원.

## 🛠️ How to Build (For Developers)

직접 소스코드를 빌드하여 실행 파일을 만들려면 아래 스크립트를 사용하세요. (Nuitka 필요)

**macOS:**
```bash
./build_nuitka.sh
```

**Windows:**
```bat
build_nuitka.bat
```

# PDF Helper

PyQt6 기반 PDF·Word 다중 파일 병합 및 AES-256 암호화 도구입니다.

## 사용 방법

1. **파일 추가 ▾**에서 PDF / Word / 혼합 파일 여러 개를 선택하거나 목록에 끌어다 놓습니다.
2. 목록 내부 드래그 또는 ▲/▼ 버튼으로 순서를 변경합니다. 위에서 아래 순서대로 병합합니다.
3. 저장할 PDF 경로를 지정합니다.
4. 비밀번호를 자동 생성하거나 직접 입력합니다. 비밀번호 없이 저장할 수도 있습니다.
5. **순서대로 PDF 병합 및 저장**을 누릅니다.

Word(DOC, DOCX)는 LibreOffice를 사용해 PDF로 변환합니다. PDF 파일만 병합하면 LibreOffice가 필요하지 않습니다.

## 설치 및 실행

Python 3.11 이상 및 Word 변환 시 LibreOffice가 필요합니다.

```bash
python -m venv .venv
pip install -r requirements.txt
python main.py
```

Windows에서는 가상환경 활성화 시 `.venv\\Scripts\\activate`, Linux/macOS에서는 `source .venv/bin/activate`를 사용합니다.

## 운영체제 지원

GitHub Actions의 **다중 운영체제 빌드** 워크플로를 통해 Windows x64, macOS Intel/Apple Silicon, Linux x64/ARM64 빌드를 구성했습니다. ChromeOS에서는 Linux 개발 환경(Crostini)을 활성화한 후 Linux 실행 파일을 사용합니다. 실제 기기 호환성은 추가 확인이 필요합니다. Word 변환에는 각 기기의 LibreOffice 설치가 필요합니다.

## 주의사항

- 암호화된 입력 PDF는 현재 지원하지 않습니다.
- 결과 파일은 입력 파일과 동일한 경로로 지정할 수 없습니다.
- Word 문서의 레이아웃은 LibreOffice 및 설치 글꼴에 영향을 받습니다.
- 암호는 자동 저장하지 않습니다. 생성된 암호는 사용자가 보관해야 합니다.
- 병합 중 실패하면 기존 결과 파일은 보존합니다.

## 테스트

```bash
pip install -r requirements-dev.txt
python -m compileall -q main.py pdf_helper tests
python -m pytest -q
```

자세한 구현 구조는 [docs/architecture.md](docs/architecture.md)에서 확인할 수 있습니다.

## 실행 시 자동 의존성 설치

앱 시작 시 LibreOffice를 자동 감지합니다. 이미 설치되었다면 아무 작업도 하지 않습니다.
설치되지 않은 경우 사용자 확인을 받은 뒤 지원되는 패키지 관리자를 통해 다운로드/설치를 시도합니다.

- Windows: winget (TheDocumentFoundation.LibreOffice)
- macOS: Homebrew cask (libreoffice)
- ChromeOS Crostini / Debian 계열 Linux: apt-get 및 pkexec (관리자 인증 필요)

패키지 관리자/인증 도구가 없거나 설치가 실패하면 수동 설치가 필요합니다.
설치에는 인터넷 연결이 필요하며 시스템 관리자 인증이 요청될 수 있습니다.
사용자가 설치를 거절해도 **PDF 파일끼리의 병합은 정상적으로 사용할 수 있습니다.**
실행 파일의 Python/PyQt6/pypdf 라이브러리는 PyInstaller로 포함되며, 배포 파일 실행 시 pip 설치를 수행하지 않습니다.

## 운영체제별 수동 설치 안내

앱이 LibreOffice를 찾지 못하면 운영체제에 맞는 단계별 설치 방법을 보여줍니다.

- **Windows:** PowerShell에서 `winget install --id TheDocumentFoundation.LibreOffice --exact` 실행. winget이 없다면 공식 홈페이지에서 설치 파일을 내려받습니다.
- **macOS:** Homebrew 설치 환경이라면 `brew install --cask libreoffice`, 아니라면 공식 홈페이지의 macOS 설치 파일을 사용합니다.
- **ChromeOS(Crostini) / Debian / Ubuntu:** Linux 터미널에서 `sudo apt update` 다음 `sudo apt install -y libreoffice-writer`. 완료 후 `libreoffice --version`으로 확인합니다.

자동 설치가 불가능하거나 실패해도 수동 설치 절차를 안내하며, PDF 파일만 병합하는 기능은 계속 사용할 수 있습니다.

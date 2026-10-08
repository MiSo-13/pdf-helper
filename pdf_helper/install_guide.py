"""운영체제별 LibreOffice 설치 안내 (실행 가능한 명령과 검증 방법)."""
from __future__ import annotations

import platform


OFFICIAL_URL = "https://www.libreoffice.org/download/download-libreoffice/"


def installation_guide(system: str | None = None) -> tuple[str, str]:
    """표시 제목과 줄바꿈이 포함된 단계별 설치 안내를 반환한다."""
    system = system or platform.system()
    if system == "Windows":
        return ("Windows 설치 안내",
                "1. 시작 메뉴에서 PowerShell을 실행하세요.\n"
                "2. 아래 명령을 입력해 설치하세요.\n"
                "   winget install --id TheDocumentFoundation.LibreOffice --exact\n"
                "3. 설치가 끝나면 PDF Helper를 다시 실행하세요.\n\n"
                "winget이 없다면 아래 공식 사이트에서 Windows 설치 프로그램을 받아 실행하세요.\n"
                f"{OFFICIAL_URL}")
    if system == "Darwin":
        return ("macOS 설치 안내",
                "방법 A (Homebrew가 설치된 경우):\n"
                "1. 터미널을 실행하세요.\n"
                "2. brew install --cask libreoffice\n"
                "3. 설치 후 PDF Helper를 재실행하세요.\n\n"
                "방법 B (Homebrew가 없는 경우):\n"
                "아래 공식 사이트에서 macOS용 파일을 다운로드하여 설치하세요.\n"
                "설치 후 응용 프로그램의 LibreOffice를 확인하세요.\n"
                f"{OFFICIAL_URL}")
    if system == "Linux":
        return ("ChromeOS(Crostini) / Linux 설치 안내",
                "ChromeOS: 설정에서 Linux 개발 환경을 활성화하고 '터미널'을 여세요.\n"
                "Debian/Ubuntu/Crostini에서는 다음 명령을 한 줄씩 실행하세요.\n\n"
                "   sudo apt update\n"
                "   sudo apt install -y libreoffice-writer\n\n"
                "관리자 비밀번호를 요청하면 Linux 사용자 비밀번호를 입력하세요.\n"
                "설치 확인: libreoffice --version\n"
                "설치 후 PDF Helper를 다시 실행하세요.\n\n"
                "apt 명령이 없다면 사용 중인 배포판의 패키지 관리자 또는 공식 사이트를 이용하세요.\n"
                f"{OFFICIAL_URL}")
    return ("설치 안내", "현재 운영체제는 자동 설치를 지원하지 않습니다.\n" + OFFICIAL_URL)

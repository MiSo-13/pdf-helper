"""운영체제별 설치 안내의 명령과 줄바꿈 검증."""
from pdf_helper.install_guide import installation_guide


def test_windows_guide():
    title, body = installation_guide("Windows")
    assert "Windows" in title
    assert "winget install" in body
    assert "https://" in body
    assert "\\n" not in body


def test_macos_guide():
    _, body = installation_guide("Darwin")
    assert "brew install --cask libreoffice" in body
    assert "Homebrew가 없는 경우" in body


def test_crostini_guide():
    title, body = installation_guide("Linux")
    assert "Crostini" in title
    assert "sudo apt update" in body
    assert "sudo apt install -y libreoffice-writer" in body
    assert "libreoffice --version" in body
    assert "\\n" not in body


def test_other_os_fallback():
    _, body = installation_guide("Unknown")
    assert "https://" in body

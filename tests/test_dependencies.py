"""LibreOffice 자동 설치 정책 테스트."""
from unittest.mock import patch

from pdf_helper import dependencies


def test_detect_installed():
    with patch.object(dependencies, "find_libreoffice", return_value="/usr/bin/soffice"):
        assert dependencies.is_installed()
    with patch.object(dependencies, "find_libreoffice", side_effect=RuntimeError("missing")):
        assert not dependencies.is_installed()


def test_windows_winget_command():
    with patch.object(dependencies.platform, "system", return_value="Windows"), patch.object(
        dependencies.shutil, "which", side_effect=lambda x: "C:/winget.exe" if x == "winget" else None
    ):
        command, _ = dependencies.install_command()
    assert command[1:4] == ["install", "--id", "TheDocumentFoundation.LibreOffice"]


def test_macos_brew_command():
    with patch.object(dependencies.platform, "system", return_value="Darwin"), patch.object(
        dependencies.shutil, "which", return_value="/opt/homebrew/bin/brew"
    ):
        command, _ = dependencies.install_command()
    assert command == ["/opt/homebrew/bin/brew", "install", "--cask", "libreoffice"]


def test_crostini_apt_command():
    with patch.object(dependencies.platform, "system", return_value="Linux"), patch.object(
        dependencies.shutil, "which", side_effect=lambda x: "/usr/bin/" + x
    ):
        command, _ = dependencies.install_command()
    assert command == ["/usr/bin/pkexec", "/usr/bin/apt-get", "install", "-y", "libreoffice-writer"]


def test_missing_package_manager_is_safe():
    with patch.object(dependencies.platform, "system", return_value="Linux"), patch.object(
        dependencies.shutil, "which", return_value=None
    ):
        command, _ = dependencies.install_command()
    assert command is None


def test_install_failure():
    class Result:
        returncode = 1
        stderr = "install failed"
        stdout = ""
    with patch.object(dependencies.subprocess, "run", return_value=Result()):
        try:
            dependencies.install_libreoffice(["fake", "install"])
        except RuntimeError as exc:
            assert "install failed" in str(exc)
        else:
            raise AssertionError("Expected RuntimeError")


def test_install_success():
    class Result:
        returncode = 0
        stderr = ""
        stdout = ""
    with patch.object(dependencies.subprocess, "run", return_value=Result()), patch.object(
        dependencies, "is_installed", return_value=True
    ):
        dependencies.install_libreoffice(["fake", "install"])

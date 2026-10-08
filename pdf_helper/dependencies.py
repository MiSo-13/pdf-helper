"""LibreOffice 실행 환경 점검 및 사용자 동의 기반 자동 설치."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess

from .service import find_libreoffice


def is_installed() -> bool:
    try:
        find_libreoffice()
    except RuntimeError:
        return False
    return True


def install_command() -> tuple[list[str] | None, str]:
    """지원 패키지 관리자에서만 명시적으로 선택된 설치 명령을 반환한다."""
    system = platform.system()
    if system == "Windows":
        winget = shutil.which("winget")
        if winget:
            return ([winget, "install", "--id", "TheDocumentFoundation.LibreOffice",
                     "--exact", "--source", "winget", "--accept-source-agreements",
                     "--accept-package-agreements", "--disable-interactivity"],
                    "Windows 패키지 관리자(winget)")
        return None, "winget을 사용할 수 없습니다. LibreOffice 공식 설치 프로그램이 필요합니다."
    if system == "Darwin":
        brew = shutil.which("brew")
        if brew:
            return [brew, "install", "--cask", "libreoffice"], "Homebrew"
        return None, "Homebrew가 없어 자동 설치를 지원하지 않습니다."
    if system == "Linux":
        # Crostini(Debian) 및 Ubuntu 등 apt 기반 환경만 자동 설치 지원.
        apt = shutil.which("apt-get")
        pkexec = shutil.which("pkexec")
        if apt and pkexec:
            return [pkexec, apt, "install", "-y", "libreoffice-writer"], "apt / pkexec (관리자 인증 필요)"
        return None, "apt-get 또는 pkexec가 없습니다. Linux 패키지 관리자로 설치해야 합니다."
    return None, "자동 설치를 지원하지 않는 운영체제입니다."


def install_libreoffice(command: list[str]) -> None:
    """사용자 확인 후 백그라운드 작업 스레드에서만 호출한다."""
    try:
        process = subprocess.run(command, capture_output=True, text=True, timeout=900, check=False)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("설치 제한 시간(15분)을 초과했습니다.") from exc
    except OSError as exc:
        raise RuntimeError(f"설치를 시작하지 못했습니다: {exc}") from exc
    if process.returncode:
        detail = (process.stderr or process.stdout or "").strip()
        raise RuntimeError(f"설치 실패 (종료 코드 {process.returncode}): {detail[-600:]}")
    if not is_installed():
        raise RuntimeError("설치 명령은 종료됐지만 LibreOffice를 찾지 못했습니다. 앱을 재실행하거나 설치 경로를 확인하세요.")

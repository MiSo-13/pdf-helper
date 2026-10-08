"""ChromeOS Crostini 전용 Qt 플랫폼 선택.

QApplication 생성 및 QtGui 로딩 전에 호출해야 한다.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys


def is_crostini() -> bool:
    if sys.platform != "linux":
        return False
    # Crostini의 고유한 통합 파일시스템과 환경변수를 기준으로 확인한다.
    return bool(
        os.environ.get("SOMMELIER_VERSION")
        or os.environ.get("CROS_USER_ID_HASH")
        or Path("/dev/.cros_milestone").exists()
        or Path("/mnt/chromeos").is_dir()
    )


def configure_qt_platform() -> str:
    """Crostini Wayland 연결 불안정을 피해 XWayland(xcb)를 사용한다.

    외부에서 명시한 offscreen/xcb 등은 덮어쓰지 않는다.
    """
    if is_crostini() and not os.environ.get("QT_QPA_PLATFORM"):
        if os.environ.get("DISPLAY"):
            os.environ["QT_QPA_PLATFORM"] = "xcb"
    return os.environ.get("QT_QPA_PLATFORM", "system-default")

"""로컬에서 생성된 아이콘을 포함해 PyInstaller 패키지를 빌드합니다."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


def build_command(platform: str | None = None) -> list[str]:
    platform = platform or sys.platform
    icon_dir = ROOT / "assets"
    png = icon_dir / "app-icon.png"
    if not png.is_file():
        raise FileNotFoundError("assets/app-icon.png이 없습니다. 먼저 python scripts/generate_app_icon.py를 실행하세요.")

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean",
           "--name", "PDF-Helper", "--add-data", f"{png}{';' if platform == 'win32' else ':'}assets"]
    if platform in ("win32", "darwin"):
        cmd.append("--windowed")
    if platform != "darwin":
        cmd.append("--onefile")
    icon = icon_dir / ("app-icon.ico" if platform == "win32" else "app-icon.icns" if platform == "darwin" else "app-icon.png")
    if icon.is_file():
        cmd.extend(["--icon", str(icon)])
    cmd.append("main.py")
    return cmd


if __name__ == "__main__":
    subprocess.run(build_command(), check=True, cwd=ROOT)

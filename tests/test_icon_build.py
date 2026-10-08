"""배포 아이콘이 로컬에서 제공됐을 때의 플랫폼별 패키징 테스트."""
from pathlib import Path

import pytest
from scripts import build_with_icon


def test_build_requires_icon(tmp_path, monkeypatch):
    monkeypatch.setattr(build_with_icon, "ROOT", tmp_path)
    with pytest.raises(FileNotFoundError):
        build_with_icon.build_command("linux")


@pytest.mark.parametrize("platform,suffix", [
    ("win32", ".ico"), ("darwin", ".icns"), ("linux", ".png")
])
def test_packaging_icon_by_platform(tmp_path, monkeypatch, platform, suffix):
    folder = tmp_path / "assets"
    folder.mkdir()
    (folder / "app-icon.png").write_bytes(b"fake")
    (folder / ("app-icon" + suffix)).write_bytes(b"fake")
    monkeypatch.setattr(build_with_icon, "ROOT", tmp_path)
    command = build_with_icon.build_command(platform)
    assert "--add-data" in command
    assert "--icon" in command
    assert command[command.index("--icon") + 1].endswith(suffix)
    assert ("--onefile" in command) == (platform != "darwin")

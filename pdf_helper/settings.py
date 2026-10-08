"""PDF Helper 로컬 설정(JSON): 앱 실행 위치의 data/config/settings.json."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile

from .diagnostics import logger


def application_directory() -> Path:
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
        if sys.platform == "darwin" and root.name == "MacOS" and root.parent.name == "Contents":
            root = root.parent.parent.parent
        return root
    return Path(__file__).resolve().parent.parent


def settings_path() -> Path:
    return application_directory() / "data" / "config" / "settings.json"


class SettingsStore:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else settings_path()
        self._data = {"last_output_directory": ""}
        self.load()

    def load(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.is_file():
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if not isinstance(raw, dict):
                    raise ValueError("설정 파일의 루트가 객체가 아닙니다.")
                value = raw.get("last_output_directory", "")
                self._data["last_output_directory"] = value if isinstance(value, str) else ""
            else:
                self.save()
        except (OSError, ValueError, TypeError) as exc:
            logger().warning("SETTINGS_LOAD_FAILED type=%s", type(exc).__name__)

    @property
    def last_output_directory(self) -> str:
        value = self._data["last_output_directory"]
        return value if value and Path(value).is_dir() else ""

    def update_output_path(self, output_path: str | Path) -> bool:
        path = Path(output_path).expanduser().resolve()
        if not path.parent.is_dir():
            return False
        self._data["last_output_directory"] = str(path.parent)
        return self.save()

    def save(self) -> bool:
        staged = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            fd, staged = tempfile.mkstemp(prefix=".settings-", suffix=".json", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self._data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(staged, self.path)
            return True
        except OSError as exc:
            logger().warning("SETTINGS_SAVE_FAILED type=%s", type(exc).__name__)
            return False
        finally:
            if staged is not None:
                try:
                    Path(staged).unlink(missing_ok=True)
                except OSError:
                    pass

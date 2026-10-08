"""예기치 않은 종료 진단용 로그. 문서 본문과 비밀번호는 기록하지 않는다."""
from __future__ import annotations

import faulthandler
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
import tempfile


_crash_stream = None


def enable_diagnostics() -> Path | None:
    global _crash_stream
    try:
        directory = Path(tempfile.gettempdir()) / "pdf-helper"
        directory.mkdir(parents=True, exist_ok=True)
        log_path = directory / "crash.log"
        _crash_stream = log_path.open("a", encoding="utf-8")
        faulthandler.enable(file=_crash_stream, all_threads=True)
        handler = RotatingFileHandler(directory / "app.log", maxBytes=512_000, backupCount=2, encoding="utf-8")
        logging.basicConfig(level=logging.ERROR, handlers=[handler], force=True)
        previous_hook = sys.excepthook

        def on_exception(exc_type, value, traceback):
            logging.error("처리되지 않은 예외", exc_info=(exc_type, value, traceback))
            previous_hook(exc_type, value, traceback)

        sys.excepthook = on_exception
        return directory
    except OSError:
        return None

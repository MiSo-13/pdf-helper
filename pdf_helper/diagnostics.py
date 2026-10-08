"""앱 생명주기, Qt, Python, 네이티브 종료를 추적하는 로컬 진단 로그."""
from __future__ import annotations

import faulthandler
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import platform
import sys
import threading

_LOGGER = logging.getLogger("pdf_helper")
_crash_stream = None
_qt_handler = None


def log_directory() -> Path:
    """배포 실행파일 옆 또는 소스 프로젝트 루트의 logs 디렉터리."""
    if getattr(sys, "frozen", False):
        root = Path(sys.executable).resolve().parent
        if sys.platform == "darwin" and root.name == "MacOS" and root.parent.name == "Contents":
            # .app 실행시 앱 번들(읽기 전용일 수 있음) 바깥에 로그 보관.
            root = root.parent.parent.parent
    else:
        root = Path(__file__).resolve().parent.parent
    return root / "logs"

def logger() -> logging.Logger:
    return _LOGGER


def enable_diagnostics() -> Path | None:
    """오류 로그를 시작 시 초기화하며 예외 발생시 기록을 최대한 보장한다."""
    global _crash_stream
    try:
        directory = log_directory()
        directory.mkdir(parents=True, exist_ok=True)
        _crash_stream = (directory / "crash.log").open("a", encoding="utf-8", buffering=1)
        faulthandler.enable(file=_crash_stream, all_threads=True)
        _LOGGER.setLevel(logging.DEBUG)
        _LOGGER.propagate = False
        if not _LOGGER.handlers:
            file_handler = RotatingFileHandler(
                directory / "app.log", maxBytes=2_000_000, backupCount=4, encoding="utf-8"
            )
            file_handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s [pid=%(process)d thread=%(threadName)s] "
                "%(name)s: %(message)s"
            ))
            _LOGGER.addHandler(file_handler)

        old_hook = sys.excepthook

        def on_exception(exc_type, value, tb):
            _LOGGER.critical("처리하지 못한 메인 스레드 예외", exc_info=(exc_type, value, tb))
            old_hook(exc_type, value, tb)

        sys.excepthook = on_exception
        old_thread_hook = threading.excepthook

        def on_thread_exception(args):
            _LOGGER.critical("처리하지 못한 Python 스레드 예외",
                             exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
            old_thread_hook(args)

        threading.excepthook = on_thread_exception
        _LOGGER.info("APP_START os=%s release=%s python=%s frozen=%s",
                     platform.system(), platform.release(), platform.python_version(),
                     getattr(sys, "frozen", False))
        return directory
    except OSError:
        return None


def install_qt_logging() -> None:
    """QApplication 생성 전 Qt 메시지를 기록한다. 메시지에 개인정보가 포함될 수 있다."""
    global _qt_handler
    from PyQt6.QtCore import QtMsgType, qInstallMessageHandler

    def handler(mode, context, message):
        # Qt 콜백에서 예외를 밖으로 전파하면 프로세스가 종료될 수 있다.
        try:
            levels = {
                QtMsgType.QtDebugMsg: logging.DEBUG,
                QtMsgType.QtInfoMsg: logging.INFO,
                QtMsgType.QtWarningMsg: logging.WARNING,
                QtMsgType.QtCriticalMsg: logging.ERROR,
                QtMsgType.QtFatalMsg: logging.CRITICAL,
            }
            level = levels.get(mode, logging.WARNING)
            _LOGGER.log(level, "QT mode=%s %s", getattr(mode, "name", str(mode)), message)
        except BaseException:
            # 로깅 실패가 사용자 GUI를 종료시키지 않도록 한다.
            pass

    _qt_handler = handler  # Python 콜백 참조 유지
    qInstallMessageHandler(_qt_handler)


def event(name: str, **fields) -> None:
    # 파일 경로/본문/비밀번호는 기록하지 않고 상태와 개수만 기록한다.
    safe = " ".join(f"{key}={value}" for key, value in fields.items())
    _LOGGER.info("%s %s", name, safe)


def log_exception(operation: str) -> None:
    _LOGGER.exception("작업 예외 operation=%s", operation)

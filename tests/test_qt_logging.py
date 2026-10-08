"""Qt 메시지 핸들러에서 QtMsgType과 로깅 오류를 안전하게 처리하는지 확인."""
import logging

from PyQt6.QtCore import QtMsgType, qWarning
from pdf_helper import diagnostics


def test_qt_message_handler_does_not_throw(caplog, monkeypatch):
    messages = []
    monkeypatch.setattr(diagnostics.logger(), "log",
                        lambda level, fmt, *args: messages.append((level, fmt % args)))
    diagnostics.install_qt_logging()
    qWarning("GUI warning regression")
    assert any("GUI warning regression" in message for _, message in messages)
    assert any(level == logging.WARNING for level, _ in messages)


def test_qt_logging_failure_does_not_crash(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("logging is unavailable")
    monkeypatch.setattr(diagnostics.logger(), "log", fail)
    diagnostics.install_qt_logging()
    qWarning("logging backend failure should not terminate application")

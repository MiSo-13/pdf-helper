"""실행 위치별 로그 디렉터리 결정 및 이벤트 기록 테스트."""
from pathlib import Path
from unittest.mock import patch
import logging

from pdf_helper import diagnostics


def test_source_logs_go_to_project_root():
    expected = Path(diagnostics.__file__).resolve().parent.parent / "logs"
    assert diagnostics.log_directory() == expected


def test_frozen_windows_or_linux_logs_next_to_binary(tmp_path):
    executable = tmp_path / "PDF-Helper"
    with patch.object(diagnostics.sys, "frozen", True, create=True), patch.object(
        diagnostics.sys, "executable", str(executable)
    ), patch.object(diagnostics.sys, "platform", "linux"):
        assert diagnostics.log_directory() == tmp_path / "logs"


def test_macos_app_logs_next_to_app_bundle(tmp_path):
    executable = tmp_path / "PDF-Helper.app" / "Contents" / "MacOS" / "PDF-Helper"
    with patch.object(diagnostics.sys, "frozen", True, create=True), patch.object(
        diagnostics.sys, "executable", str(executable)
    ), patch.object(diagnostics.sys, "platform", "darwin"):
        assert diagnostics.log_directory() == tmp_path / "logs"


def test_logging_creates_files(tmp_path):
    with patch.object(diagnostics, "log_directory", return_value=tmp_path):
        directory = diagnostics.enable_diagnostics()
        diagnostics.event("TEST_LOG_EVENT", count=2)
        for handler in diagnostics.logger().handlers:
            handler.flush()
        assert directory == tmp_path
        assert (tmp_path / "app.log").is_file()
        assert (tmp_path / "crash.log").is_file()

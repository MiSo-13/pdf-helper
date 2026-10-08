"""Crostini Qt 플랫폼 설정 단위 테스트."""
from unittest.mock import patch
from pdf_helper import platform_setup


def test_crostini_wayland_switches_to_xcb(monkeypatch):
    monkeypatch.setattr(platform_setup, "is_crostini", lambda: True)
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    assert platform_setup.configure_qt_platform() == "xcb"


def test_user_preference_is_preserved(monkeypatch):
    monkeypatch.setattr(platform_setup, "is_crostini", lambda: True)
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("DISPLAY", ":0")
    assert platform_setup.configure_qt_platform() == "offscreen"


def test_general_linux_unchanged(monkeypatch):
    monkeypatch.setattr(platform_setup, "is_crostini", lambda: False)
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    monkeypatch.setenv("DISPLAY", ":0")
    assert platform_setup.configure_qt_platform() == "system-default"
    assert "QT_QPA_PLATFORM" not in platform_setup.os.environ


def test_without_x11_display_does_not_force_xcb(monkeypatch):
    monkeypatch.setattr(platform_setup, "is_crostini", lambda: True)
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("QT_QPA_PLATFORM", raising=False)
    assert platform_setup.configure_qt_platform() == "system-default"


def test_crostini_detection_env(monkeypatch):
    monkeypatch.setattr(platform_setup.sys, "platform", "linux")
    monkeypatch.setenv("SOMMELIER_VERSION", "1")
    assert platform_setup.is_crostini()

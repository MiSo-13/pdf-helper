"""JSON 설정 저장, 복원, 손상 및 실행 위치별 경로 테스트."""
import json
from pathlib import Path
from unittest.mock import patch

from pdf_helper import settings


def test_new_file_and_restore_directory(tmp_path):
    path = tmp_path / "data" / "config" / "settings.json"
    store = settings.SettingsStore(path)
    assert path.is_file()
    assert store.last_output_directory == ""
    output = tmp_path / "result.pdf"
    assert store.update_output_path(output)
    assert json.loads(path.read_text(encoding="utf-8"))["last_output_directory"] == str(tmp_path)
    assert settings.SettingsStore(path).last_output_directory == str(tmp_path)


def test_corrupted_settings_file_is_safe(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{ broken", encoding="utf-8")
    store = settings.SettingsStore(path)
    assert store.last_output_directory == ""
    assert store.update_output_path(tmp_path / "new.pdf")
    assert json.loads(path.read_text(encoding="utf-8"))["last_output_directory"] == str(tmp_path)


def test_missing_last_directory_is_ignored(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"last_output_directory": str(tmp_path / "gone")}), encoding="utf-8")
    store = settings.SettingsStore(path)
    assert store.last_output_directory == ""


def test_invalid_destination_does_not_overwrite(tmp_path):
    path = tmp_path / "settings.json"
    store = settings.SettingsStore(path)
    before = path.read_text(encoding="utf-8")
    assert not store.update_output_path(tmp_path / "missing" / "target.pdf")
    assert path.read_text(encoding="utf-8") == before


def test_source_settings_directory():
    root = Path(settings.__file__).resolve().parent.parent
    assert settings.application_directory() == root


def test_frozen_binary_directory(tmp_path):
    exe = tmp_path / "PDF-Helper"
    with patch.object(settings.sys, "frozen", True, create=True), patch.object(
        settings.sys, "executable", str(exe)
    ), patch.object(settings.sys, "platform", "linux"):
        assert settings.settings_path() == tmp_path / "data" / "config" / "settings.json"


def test_macos_bundle_directory(tmp_path):
    exe = tmp_path / "PDF-Helper.app" / "Contents" / "MacOS" / "PDF-Helper"
    with patch.object(settings.sys, "frozen", True, create=True), patch.object(
        settings.sys, "executable", str(exe)
    ), patch.object(settings.sys, "platform", "darwin"):
        assert settings.settings_path() == tmp_path / "data" / "config" / "settings.json"


def test_last_input_directory_persisted_separately(tmp_path):
    config = tmp_path / "settings.json"
    store = settings.SettingsStore(config)
    input_folder = tmp_path / "inputs"
    input_folder.mkdir()
    source = input_folder / "source.pdf"
    source.write_bytes(b"%PDF-1.4")
    output = tmp_path / "result.pdf"
    assert store.update_output_path(output)
    assert store.update_input_path(source)
    restored = settings.SettingsStore(config)
    assert restored.last_input_directory == str(input_folder)
    assert restored.last_output_directory == str(tmp_path)


def test_missing_input_folder_falls_back(tmp_path):
    config = tmp_path / "settings.json"
    config.write_text(json.dumps({"last_input_directory": str(tmp_path / "missing"),
                                  "last_output_directory": ""}), encoding="utf-8")
    assert settings.SettingsStore(config).last_input_directory == ""


def test_old_config_backward_compatible(tmp_path):
    config = tmp_path / "settings.json"
    config.write_text(json.dumps({"last_output_directory": str(tmp_path)}), encoding="utf-8")
    store = settings.SettingsStore(config)
    assert store.last_output_directory == str(tmp_path)
    assert store.last_input_directory == ""

"""드래그 앤 드롭과 파일 선택창 충돌 회귀 테스트 (Qt offscreen)."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import Qt, QMimeData, QUrl, QPointF
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QApplication, QFileDialog, QListWidget

from pdf_helper.window import FileList, PdfHelperWindow


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def _pdf(path):
    path.write_bytes(b"%PDF-1.4\n")
    return str(path)


def test_drop_two_external_files_and_reorder(app, tmp_path):
    widget = FileList()
    widget.show()
    first, second = _pdf(tmp_path / "first.pdf"), _pdf(tmp_path / "second.pdf")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(first), QUrl.fromLocalFile(second)])
    event = QDropEvent(
        QPointF(widget.rect().center()), Qt.DropAction.CopyAction,
        mime, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier
    )
    widget.dropEvent(event)
    assert event.isAccepted()
    app.processEvents()
    assert widget.paths() == [first, second]
    widget.setCurrentRow(1)
    item = widget.takeItem(1)
    widget.insertItem(0, item)
    assert widget.paths() == [second, first]
    widget.close()


def test_duplicate_drop_does_not_duplicate_items(app, tmp_path):
    widget = FileList()
    first = _pdf(tmp_path / "first.pdf")
    widget.add_paths([first, first])
    assert widget.paths() == [first]
    widget.close()


def test_file_selection_uses_qt_dialog(app, tmp_path, monkeypatch):
    window = PdfHelperWindow()
    observed = []
    selected = _pdf(tmp_path / "one.pdf")
    def pick_files(*args, **kwargs):
        observed.append(kwargs["options"])
        return [selected], "PDF (*.pdf)"
    def pick_output(*args, **kwargs):
        observed.append(kwargs["options"])
        return str(tmp_path / "output.pdf"), "PDF (*.pdf)"
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", pick_files)
    monkeypatch.setattr(QFileDialog, "getSaveFileName", pick_output)
    window._choose_files("PDF (*.pdf)")
    window._select_output()
    assert window.files.paths() == [selected]
    assert window.output_field.text() == str(tmp_path / "output.pdf")
    assert all(flag & QFileDialog.Option.DontUseNativeDialog for flag in observed)
    window.close()


def test_file_dialog_remembers_last_input_folder(app, tmp_path, monkeypatch):
    from pdf_helper.settings import SettingsStore
    directory = tmp_path / "inputs"
    directory.mkdir()
    selected = _pdf(directory / "selected.pdf")
    settings = SettingsStore(tmp_path / "config" / "settings.json")
    window = PdfHelperWindow()
    window.settings = settings
    seen = []
    def choose(*args, **kwargs):
        seen.append(args[2])
        return [selected], "PDF (*.pdf)"
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", choose)
    window._choose_files("PDF (*.pdf)")
    window._choose_files("PDF (*.pdf)")
    assert seen == ["", str(directory)]
    assert SettingsStore(settings.path).last_input_directory == str(directory)
    window.close()

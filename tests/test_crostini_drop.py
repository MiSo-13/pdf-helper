"""Crostini/X11 파일 드롭 MIME 포맷과 UI 회귀 테스트."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtCore import QMimeData, QUrl, Qt, QPointF
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import QApplication

from pdf_helper.window import FileList, PdfHelperWindow


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_extract_uri_list_file_urls(tmp_path):
    path = tmp_path / "한글 문서.pdf"
    path.write_bytes(b"mock")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    assert FileList.extract_paths(mime) == [str(path)]


def test_extract_plain_text_file_uri(tmp_path):
    path = tmp_path / "test.pdf"
    path.write_bytes(b"mock")
    mime = QMimeData()
    mime.setText(QUrl.fromLocalFile(str(path)).toString() + "\n")
    assert FileList.extract_paths(mime) == [str(path)]


def test_external_drop_into_window(app, tmp_path):
    window = PdfHelperWindow()
    window.show()
    path = tmp_path / "test.pdf"
    path.write_bytes(b"mock")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    event = QDropEvent(QPointF(1, 1), Qt.DropAction.CopyAction, mime,
                       Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
    window.dropEvent(event)
    assert event.isAccepted()
    app.processEvents()
    assert window.files.paths() == [str(path)]
    window.close()


def test_clipboard_file_addition(app, tmp_path):
    window = PdfHelperWindow()
    path = tmp_path / "file.docx"
    path.write_text("mock")
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(path))])
    QApplication.clipboard().setMimeData(mime)
    window._paste_files()
    assert window.files.paths() == [str(path)]
    window.close()

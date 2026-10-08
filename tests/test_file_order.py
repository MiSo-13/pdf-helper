"""파일 병합 순서 번호 표시 및 화면 문구 회귀 테스트."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PyQt6.QtWidgets import QApplication
from pdf_helper.window import PdfHelperWindow, FileList


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def test_file_list_renumber_after_add_remove_and_reorder(app, tmp_path):
    paths = []
    for name in ("a.pdf", "b.docx", "c.pdf"):
        file = tmp_path / name
        file.write_bytes(b"test")
        paths.append(str(file))
    widget = FileList()
    widget.add_paths(paths)
    assert [widget.item(i).text().split(".  ", 1)[0] for i in range(3)] == ["1", "2", "3"]
    assert widget.paths() == paths

    item = widget.takeItem(2)
    widget.insertItem(0, item)
    widget.renumber()
    assert widget.paths() == [paths[2], paths[0], paths[1]]
    assert [widget.item(i).text().split(".  ", 1)[0] for i in range(3)] == ["1", "2", "3"]

    widget.takeItem(1)
    widget.renumber()
    assert [widget.item(i).text().split(".  ", 1)[0] for i in range(2)] == ["1", "2"]
    widget.close()


def test_main_window_move_updates_numbering(app, tmp_path):
    window = PdfHelperWindow()
    paths = []
    for name in ("one.pdf", "two.pdf", "three.pdf"):
        file = tmp_path / name
        file.write_bytes(b"test")
        paths.append(str(file))
    window.files.add_paths(paths)
    window.files.setCurrentRow(1)
    window.files.item(1).setSelected(True)
    window._move(-1)
    assert window.files.paths()[0] == paths[1]
    assert window.files.item(0).text().startswith("1.  ")
    assert window.files.item(1).text().startswith("2.  ")
    window.files.item(0).setSelected(True)
    window._remove_selected()
    assert window.files.item(0).text().startswith("1.  ")
    window.close()

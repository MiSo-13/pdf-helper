"""여러 파일을 원하는 순서로 병합하는 PyQt6 UI."""
from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import QObject, QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QGuiApplication
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMenu, QMessageBox, QPushButton, QToolButton,
    QVBoxLayout, QWidget,
)

from .service import SUPPORTED_SUFFIXES, generate_password, merge_documents


class FileList(QListWidget):
    """외부 파일 드롭과 목록 내부 드래그 순서 변경을 동시에 허용한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls() and any(u.isLocalFile() for u in event.mimeData().urls()):
            self.add_paths([u.toLocalFile() for u in event.mimeData().urls()])
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def add_paths(self, paths):
        existing = {self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())}
        skipped = []
        for raw in paths:
            path = Path(raw).expanduser().resolve()
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
                skipped.append(str(raw))
                continue
            if str(path) in existing:
                continue
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(f"{path.name}  ({path.suffix.lower()[1:].upper()})")
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(str(path))
            self.addItem(item)
            existing.add(str(path))
        if skipped:
            QMessageBox.warning(self, "지원하지 않는 파일", "PDF, DOC, DOCX 파일만 추가할 수 있습니다.\n" + "\n".join(skipped[:5]))

    def paths(self) -> list[str]:
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]


class MergeWorker(QObject):
    finished = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, inputs: list[str], output: str, password: str | None):
        super().__init__()
        self.inputs, self.output, self.password = inputs, output, password

    def run(self):
        try:
            pages = merge_documents(self.inputs, self.output, self.password)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(pages)


class PdfHelperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Helper")
        self.resize(800, 590)
        self.thread = None
        self.worker = None
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(10)
        layout.addWidget(QLabel("파일을 위에서 아래 순서로 합칩니다. PDF / Word 파일을 끌어다 놓을 수 있습니다."))

        tools = QHBoxLayout()
        self.add_button = QToolButton()
        self.add_button.setText("파일 추가 ▾")
        self.add_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(self.add_button)
        for title, filter_text in (
            ("PDF 추가", "PDF (*.pdf)"),
            ("Word 추가", "Word (*.doc *.docx)"),
            ("PDF / Word 한 번에 추가", "문서 (*.pdf *.doc *.docx)"),
        ):
            action = QAction(title, self)
            action.triggered.connect(lambda checked=False, f=filter_text: self._choose_files(f))
            menu.addAction(action)
        self.add_button.setMenu(menu)
        tools.addWidget(self.add_button)
        self.remove_button = QPushButton("선택 삭제")
        self.remove_button.clicked.connect(self._remove_selected)
        tools.addWidget(self.remove_button)
        self.up_button = QPushButton("▲ 위로")
        self.up_button.clicked.connect(lambda: self._move(-1))
        tools.addWidget(self.up_button)
        self.down_button = QPushButton("▼ 아래로")
        self.down_button.clicked.connect(lambda: self._move(1))
        tools.addWidget(self.down_button)
        self.clear_button = QPushButton("전체 삭제")
        self.clear_button.clicked.connect(lambda: self.files.clear())
        tools.addWidget(self.clear_button)
        tools.addStretch()
        layout.addLayout(tools)

        self.files = FileList()
        layout.addWidget(self.files, 1)
        self.files.model().rowsInserted.connect(self._refresh_count)
        self.files.model().rowsRemoved.connect(self._refresh_count)
        self.files.model().rowsMoved.connect(self._refresh_count)
        self.count_label = QLabel("0개 파일")
        layout.addWidget(self.count_label)

        output_row = QHBoxLayout()
        output_row.addWidget(QLabel("저장 위치"))
        self.output_field = QLineEdit()
        output_row.addWidget(self.output_field, 1)
        output_button = QPushButton("찾아보기")
        output_button.clicked.connect(self._select_output)
        output_row.addWidget(output_button)
        layout.addLayout(output_row)

        self.encrypt_checkbox = QCheckBox("PDF 열기 비밀번호 설정 (AES-256)")
        self.encrypt_checkbox.setChecked(True)
        layout.addWidget(self.encrypt_checkbox)
        password_row = QHBoxLayout()
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        password_row.addWidget(self.password_field, 1)
        self.generate_button = QPushButton("자동 생성")
        self.generate_button.clicked.connect(lambda: self.password_field.setText(generate_password()))
        password_row.addWidget(self.generate_button)
        self.copy_button = QPushButton("복사")
        self.copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.password_field.text()))
        password_row.addWidget(self.copy_button)
        self.show_checkbox = QCheckBox("표시")
        self.show_checkbox.toggled.connect(
            lambda enabled: self.password_field.setEchoMode(
                QLineEdit.EchoMode.Normal if enabled else QLineEdit.EchoMode.Password
            )
        )
        password_row.addWidget(self.show_checkbox)
        layout.addLayout(password_row)
        self.encrypt_checkbox.toggled.connect(self._toggle_password)
        self.generate_button.click()

        self.status_label = QLabel("Word 변환에는 LibreOffice가 필요합니다.")
        layout.addWidget(self.status_label)
        self.merge_button = QPushButton("순서대로 PDF 병합 및 저장")
        self.merge_button.clicked.connect(self._start_merge)
        layout.addWidget(self.merge_button)

    def _refresh_count(self, *args):
        self.count_label.setText(f"{self.files.count()}개 파일")

    def _choose_files(self, filter_text: str):
        paths, _ = QFileDialog.getOpenFileNames(self, "병합할 파일 선택", "", filter_text)
        self.files.add_paths(paths)
        if paths and not self.output_field.text():
            first = Path(paths[0])
            self.output_field.setText(str(first.with_name(first.stem + "_merged.pdf")))

    def _remove_selected(self):
        for item in reversed(self.files.selectedItems()):
            self.files.takeItem(self.files.row(item))

    def _move(self, delta: int):
        indexes = sorted((self.files.row(item) for item in self.files.selectedItems()), reverse=delta > 0)
        for index in indexes:
            target = index + delta
            if 0 <= target < self.files.count():
                item = self.files.takeItem(index)
                self.files.insertItem(target, item)
                item.setSelected(True)
                self.files.setCurrentItem(item)

    def _select_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "결과 PDF 저장", self.output_field.text() or "merged.pdf", "PDF (*.pdf)"
        )
        if path:
            self.output_field.setText(path if path.lower().endswith(".pdf") else path + ".pdf")

    def _toggle_password(self, enabled):
        for item in (self.password_field, self.generate_button, self.copy_button, self.show_checkbox):
            item.setEnabled(enabled)

    def _start_merge(self):
        paths = self.files.paths()
        output = self.output_field.text().strip()
        if not paths or not output:
            QMessageBox.warning(self, "입력 확인", "하나 이상의 문서와 저장 위치를 설정하세요.")
            return
        password = self.password_field.text() if self.encrypt_checkbox.isChecked() else None
        if password is not None and not password:
            QMessageBox.warning(self, "비밀번호 확인", "비밀번호를 입력하거나 자동 생성하세요.")
            return
        if Path(output).expanduser().resolve().exists():
            answer = QMessageBox.question(self, "덮어쓰기", "결과 파일이 이미 있습니다. 덮어쓸까요?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.merge_button.setEnabled(False)
        self.files.setEnabled(False)
        self.status_label.setText("Word 변환 및 PDF 병합 중...")
        self.thread = QThread(self)
        self.worker = MergeWorker(paths, output, password)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._success)
        self.worker.failed.connect(self._failure)
        self.worker.finished.connect(self.thread.quit)
        self.worker.failed.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self._clear_worker)
        self.thread.start()

    def _clear_worker(self):
        self.merge_button.setEnabled(True)
        self.files.setEnabled(True)
        self.thread = None
        self.worker = None

    def _success(self, pages):
        self.status_label.setText(f"완료: {pages}페이지를 저장했습니다.")
        QMessageBox.information(self, "완료", f"{pages}페이지 PDF 저장 완료\n{self.output_field.text()}")

    def _failure(self, reason):
        self.status_label.setText("실패: " + reason)
        QMessageBox.critical(self, "병합 실패", reason)

"""여러 파일을 원하는 순서로 병합하는 PyQt6 UI."""
from __future__ import annotations

from pathlib import Path
from PyQt6.QtCore import QObject, QThread, Qt, QTimer, QEvent, pyqtSignal
from PyQt6.QtGui import QAction, QGuiApplication
from PyQt6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QMainWindow, QMenu, QMessageBox, QPushButton, QToolButton,
    QVBoxLayout, QWidget, QApplication,
)

from .service import SUPPORTED_SUFFIXES, generate_password, merge_documents
from .dependencies import install_command, install_libreoffice, is_installed
from .install_guide import installation_guide
from .diagnostics import event as record_event, log_exception
from .settings import SettingsStore


class FileList(QListWidget):
    """외부 파일 드롭과 목록 내부 드래그 순서 변경을 동시에 허용한다."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setAlternatingRowColors(True)
        self.setDropIndicatorShown(True)
        self.setAcceptDrops(True)

    def renumber(self):
        """파일 목록의 현재 행 번호를 병합 순서로 표시한다."""
        for index in range(self.count()):
            item = self.item(index)
            path = Path(item.data(Qt.ItemDataRole.UserRole))
            item.setText(f"{index + 1}.  {path.name}  ({path.suffix[1:].upper()})")

    def _external_files(self, event):
        # 내부 드래그는 반드시 Qt의 InternalMove 경로에 위임한다.
        if event.source() is self:
            return None
        return self.extract_paths(event.mimeData())

    @staticmethod
    def extract_paths(mime):
        # X11 파일 관리자는 text/uri-list 이외의 MIME으로 경로를 전달하기도 한다.
        if mime.hasUrls():
            paths = [str(Path(url.toLocalFile())) for url in mime.urls() if url.isLocalFile()]
            if paths:
                return paths
        if mime.hasText():
            from PyQt6.QtCore import QUrl
            urls = [QUrl(line.strip()) for line in mime.text().splitlines() if line.strip().startswith("file://")]
            paths = [str(Path(url.toLocalFile())) for url in urls if url.isLocalFile()]
            if paths:
                return paths
        return None

    def dragEnterEvent(self, event):
        record_event("DRAG_ENTER", source_internal=event.source() is self,
                     urls=event.mimeData().hasUrls(), formats=",".join(event.mimeData().formats())[:200])
        if self._external_files(event) is not None:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if self._external_files(event) is not None:
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        paths = self._external_files(event)
        record_event("DROP_RECEIVED", kind="internal" if paths is None else "external", count=len(paths or []))
        if paths is None:
            try:
                super().dropEvent(event)
            except Exception:
                log_exception("internal_drop")
                raise
            QTimer.singleShot(0, self.renumber)
            record_event("INTERNAL_DROP_FINISHED", count=self.count())
            return
        event.acceptProposedAction()
        # Qt의 dropEvent 도중 model을 직접 변경하지 않고 이벤트 이후 처리한다.
        QTimer.singleShot(0, lambda selected=list(paths): self.add_paths(selected))

    def add_paths(self, paths):
        record_event("FILES_ADD_START", requested=len(paths), current=self.count())
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
        self.renumber()
        record_event("FILES_ADD_FINISH", count=self.count(), skipped=len(skipped))
        if skipped:
            QTimer.singleShot(0, lambda items=list(skipped): QMessageBox.warning(
                self, "지원하지 않는 파일", "PDF, DOC, DOCX 파일만 추가할 수 있습니다.\n" + "\n".join(items[:5])
            ))

    def paths(self) -> list[str]:
        return [self.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.count())]


class MergeWorker(QObject):
    finished = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, inputs: list[str], output: str, password: str | None):
        super().__init__()
        self.inputs, self.output, self.password = inputs, output, password

    def run(self):
        record_event("MERGE_WORKER_START", count=len(self.inputs), encrypted=self.password is not None)
        try:
            pages = merge_documents(self.inputs, self.output, self.password)
        except Exception as exc:
            log_exception("merge_worker")
            self.failed.emit(str(exc))
        else:
            record_event("MERGE_WORKER_DONE", pages=pages)
            self.finished.emit(pages)


class InstallWorker(QObject):
    finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command

    def run(self):
        record_event("INSTALL_WORKER_START")
        try:
            install_libreoffice(self.command)
        except Exception as exc:
            log_exception("install_worker")
            self.failed.emit(str(exc))
        else:
            record_event("INSTALL_WORKER_DONE")
            self.finished.emit()


class PdfHelperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        record_event("MAIN_WINDOW_INIT_START")
        self.settings = SettingsStore()
        self.setWindowTitle("PDF Helper")
        QApplication.instance().installEventFilter(self)
        self.resize(800, 590)
        self.thread = None
        self.worker = None
        self.install_thread = None
        self.install_worker = None
        root = QWidget()
        self.setCentralWidget(root)
        self.setAcceptDrops(True)
        layout = QVBoxLayout(root)
        layout.setSpacing(10)
        layout.addWidget(QLabel("PDF·Word 파일을 추가하세요. 목록 순서대로 합쳐집니다."))

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
        paste_button = QPushButton("붙여넣기 (Ctrl+V)")
        paste_button.clicked.connect(self._paste_files)
        tools.addWidget(paste_button)
        self.remove_button = QPushButton("삭제")
        self.remove_button.clicked.connect(self._remove_selected)
        tools.addWidget(self.remove_button)
        self.up_button = QPushButton("▲ 위로")
        self.up_button.clicked.connect(lambda: self._move(-1))
        tools.addWidget(self.up_button)
        self.down_button = QPushButton("▼ 아래로")
        self.down_button.clicked.connect(lambda: self._move(1))
        tools.addWidget(self.down_button)
        self.clear_button = QPushButton("모두 삭제")
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
        self.output_field.setPlaceholderText("저장할 PDF 파일 경로")
        self.output_field.editingFinished.connect(self._persist_output_directory)
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

        self.status_label = QLabel("준비")
        layout.addWidget(self.status_label)
        self.merge_button = QPushButton("PDF 저장")
        self.merge_button.clicked.connect(self._start_merge)
        layout.addWidget(self.merge_button)
        QTimer.singleShot(200, self._check_dependencies)
        record_event("MAIN_WINDOW_INIT_FINISH")

    def _show_install_guide(self, reason: str = ""):
        title, steps = installation_guide()
        message = QMessageBox(self)
        message.setIcon(QMessageBox.Icon.Information)
        message.setWindowTitle(title)
        message.setText("Word 변환용 LibreOffice 설치 방법")
        message.setInformativeText((reason + "\n\n" if reason else "") + steps
                                   + "\n\n설치하지 않아도 PDF끼리는 병합할 수 있습니다.")
        message.setStandardButtons(QMessageBox.StandardButton.Ok)
        message.exec()

    def _check_dependencies(self):
        record_event("DEPENDENCY_CHECK_START")
        if is_installed():
            record_event("DEPENDENCY_PRESENT")
            self.status_label.setText("PDF·Word 파일을 사용할 수 있습니다.")
            return
        command, method = install_command()
        record_event("DEPENDENCY_MISSING", automatic=command is not None)
        if command is None:
            self.status_label.setText("PDF 병합 가능 · Word 변환은 설치 필요")
            self._show_install_guide(method)
            return
        title, steps = installation_guide()
        answer = QMessageBox.question(
            self, "LibreOffice 자동 설치",
            "Word 파일을 PDF로 변환하려면 LibreOffice가 필요합니다.\n"
            f"설치 도구: {method}\n\n"
            "지금 자동 설치를 시도할까요? 관리자 인증과 인터넷 연결이 필요할 수 있습니다.\n"
            "아니요를 선택하면 수동 설치 방법을 안내합니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if answer != QMessageBox.StandardButton.Yes:
            record_event("INSTALL_DECLINED")
            self.status_label.setText("PDF 병합 가능 · Word 변환은 설치 필요")
            self._show_install_guide()
            return
        record_event("INSTALL_APPROVED")
        self.status_label.setText(f"{method}로 LibreOffice 설치 중...")
        self.merge_button.setEnabled(False)
        self.install_thread = QThread(self)
        self.install_worker = InstallWorker(command)
        self.install_worker.moveToThread(self.install_thread)
        self.install_thread.started.connect(self.install_worker.run)
        self.install_worker.finished.connect(self._install_success)
        self.install_worker.failed.connect(self._install_failed)
        self.install_worker.finished.connect(self.install_thread.quit)
        self.install_worker.failed.connect(self.install_thread.quit)
        self.install_thread.finished.connect(self.install_worker.deleteLater)
        self.install_thread.finished.connect(self.install_thread.deleteLater)
        self.install_thread.finished.connect(self._clear_install_worker)
        self.install_thread.start()

    def _install_success(self):
        record_event("INSTALL_SUCCEEDED")
        self.status_label.setText("LibreOffice 설치 완료 · Word 변환 가능")
        QMessageBox.information(self, "설치 완료", "LibreOffice를 설치했습니다.")

    def _install_failed(self, reason):
        record_event("INSTALL_FAILED")
        self.status_label.setText("LibreOffice 자동 설치 실패 · PDF끼리 병합 가능")
        self._show_install_guide("자동 설치 실패: " + reason)

    def _clear_install_worker(self):
        record_event("INSTALL_THREAD_FINISHED")
        self.merge_button.setEnabled(True)
        self.install_thread = None
        self.install_worker = None

    def _refresh_count(self, *args):
        record_event("FILES_MODEL_CHANGED", count=self.files.count())
        self.files.renumber()
        self.count_label.setText(f"{self.files.count()}개 파일")

    def _choose_files(self, filter_text: str):
        record_event("OPEN_FILE_DIALOG_START")
        paths, _ = QFileDialog.getOpenFileNames(
            self, "병합할 파일 선택", self.settings.last_input_directory, filter_text,
            options=QFileDialog.Option.DontUseNativeDialog
        )
        record_event("OPEN_FILE_DIALOG_DONE", count=len(paths))
        if paths:
            saved = self.settings.update_input_path(paths[0])
            record_event("INPUT_DIRECTORY_SETTINGS_UPDATED", success=saved)
        self.files.add_paths(paths)
        if paths and not self.output_field.text():
            first = Path(paths[0])
            directory = self.settings.last_output_directory
            self.output_field.setText(str(Path(directory or first.parent) / (first.stem + "_merged.pdf")))

    def eventFilter(self, watched, qt_event):
        """클립보드 파일이 있을 때만 Ctrl+V를 가로채고 텍스트 편집은 유지한다."""
        kind = qt_event.type()
        if kind not in (QEvent.Type.KeyPress, QEvent.Type.DragEnter, QEvent.Type.Drop):
            return super().eventFilter(watched, qt_event)
        # 다른 창/대화상자의 입력을 방해하지 않는다.
        if self.isActiveWindow() and (watched is self or
                                     isinstance(watched, QWidget) and self.isAncestorOf(watched)):
            if kind in (QEvent.Type.DragEnter, QEvent.Type.Drop):
                if watched is self or watched is self.files or watched is self.files.viewport():
                    record_event("QT_EVENT_PROBE", kind=kind.name,
                                 widget=type(watched).__name__,
                                 formats=",".join(qt_event.mimeData().formats())[:160])
            elif (qt_event.key() == Qt.Key.Key_V
                  and qt_event.modifiers() == Qt.KeyboardModifier.ControlModifier
                  and not isinstance(watched, QLineEdit)
                  and not isinstance(QApplication.focusWidget(), QLineEdit)):
                mime = QApplication.clipboard().mimeData()
                if mime is not None and FileList.extract_paths(mime):
                    record_event("CTRL_V_FILES")
                    self._paste_files()
                    return True
        return super().eventFilter(watched, qt_event)

    def closeEvent(self, event):
        app = QApplication.instance()
        if app is not None:
            app.removeEventFilter(self)
        super().closeEvent(event)

    def _paste_files(self):
        mime = QApplication.clipboard().mimeData()
        paths = FileList.extract_paths(mime) if mime is not None else None
        record_event("PASTE_FILES", count=len(paths or []), formats=",".join(mime.formats())[:200] if mime else "none")
        if paths:
            self.files.add_paths(paths)
        else:
            QMessageBox.information(self, "클립보드", "복사된 PDF/Word 파일 경로가 없습니다. 파일 추가 메뉴를 사용하세요.")

    def dragEnterEvent(self, event):
        paths = FileList.extract_paths(event.mimeData())
        record_event("WINDOW_DRAG_ENTER", has_urls=event.mimeData().hasUrls(), count=len(paths or []))
        if paths:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if FileList.extract_paths(event.mimeData()):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        paths = FileList.extract_paths(event.mimeData())
        record_event("WINDOW_DROP", count=len(paths or []))
        if paths:
            event.acceptProposedAction()
            QTimer.singleShot(0, lambda selected=list(paths): self.files.add_paths(selected))
        else:
            super().dropEvent(event)

    def _remove_selected(self):
        record_event("REMOVE_SELECTED", count=len(self.files.selectedItems()))
        for item in reversed(self.files.selectedItems()):
            self.files.takeItem(self.files.row(item))
        self.files.renumber()

    def _move(self, delta: int):
        record_event("MOVE_SELECTED", direction=delta, count=len(self.files.selectedItems()))
        indexes = sorted((self.files.row(item) for item in self.files.selectedItems()), reverse=delta > 0)
        for index in indexes:
            target = index + delta
            if 0 <= target < self.files.count():
                item = self.files.takeItem(index)
                self.files.insertItem(target, item)
                item.setSelected(True)
                self.files.setCurrentItem(item)
        self.files.renumber()

    def _select_output(self):
        record_event("SAVE_DIALOG_START")
        initial = self.output_field.text().strip()
        if not initial:
            initial = str(Path(self.settings.last_output_directory) / "merged.pdf") if self.settings.last_output_directory else "merged.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "결과 PDF 저장", initial, "PDF (*.pdf)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        record_event("SAVE_DIALOG_DONE", selected=bool(path))
        if path:
            self.output_field.setText(path if path.lower().endswith(".pdf") else path + ".pdf")
            self._persist_output_directory()

    def _persist_output_directory(self):
        value = self.output_field.text().strip()
        if value:
            saved = self.settings.update_output_path(value)
            record_event("OUTPUT_DIRECTORY_SETTINGS_UPDATED", success=saved)

    def _toggle_password(self, enabled):
        for item in (self.password_field, self.generate_button, self.copy_button, self.show_checkbox):
            item.setEnabled(enabled)

    def _start_merge(self):
        record_event("MERGE_BUTTON_CLICKED")
        paths = self.files.paths()
        output = self.output_field.text().strip()
        if not paths or not output:
            QMessageBox.warning(self, "입력 확인", "하나 이상의 문서와 저장 위치를 설정하세요.")
            return
        self._persist_output_directory()
        password = self.password_field.text() if self.encrypt_checkbox.isChecked() else None
        if password is not None and not password:
            QMessageBox.warning(self, "비밀번호 확인", "비밀번호를 입력하거나 자동 생성하세요.")
            return
        if Path(output).expanduser().resolve().exists():
            answer = QMessageBox.question(self, "덮어쓰기", "결과 파일이 이미 있습니다. 덮어쓸까요?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        record_event("MERGE_PREPARED", count=len(paths), encrypted=password is not None)
        self.merge_button.setEnabled(False)
        self.files.setEnabled(False)
        self.status_label.setText("PDF 생성 중...")
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
        record_event("MERGE_THREAD_FINISHED")
        self.merge_button.setEnabled(True)
        self.files.setEnabled(True)
        self.thread = None
        self.worker = None

    def _success(self, pages):
        record_event("MERGE_SUCCEEDED", pages=pages)
        self.status_label.setText(f"완료: {pages}페이지를 저장했습니다.")
        QTimer.singleShot(0, lambda: QMessageBox.information(self, "완료", f"{pages}페이지 PDF 저장 완료\n{self.output_field.text()}"))

    def _failure(self, reason):
        record_event("MERGE_FAILED")
        self.status_label.setText("실패: " + reason)
        QTimer.singleShot(0, lambda detail=reason: QMessageBox.critical(self, "병합 실패", detail))

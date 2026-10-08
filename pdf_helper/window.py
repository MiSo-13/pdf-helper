"""PDF 변환·병합·암호화 데스크톱 화면."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QCheckBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .service import create_merged_pdf, generate_password


class MergeWorker(QObject):
    finished = pyqtSignal(int)
    failed = pyqtSignal(str)

    def __init__(self, pdf: str, word: str, output: str, password: str | None):
        super().__init__()
        self.pdf, self.word, self.output, self.password = pdf, word, output, password

    def run(self) -> None:
        try:
            pages = create_merged_pdf(self.pdf, self.word, self.output, self.password)
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.finished.emit(pages)


class PdfHelperWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Helper")
        self.resize(690, 310)
        self.thread: QThread | None = None
        self.worker: MergeWorker | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setSpacing(12)
        form = QFormLayout()
        layout.addLayout(form)

        self.pdf_field = QLineEdit()
        self.word_field = QLineEdit()
        self.output_field = QLineEdit()
        self.pdf_field.setReadOnly(True)
        self.word_field.setReadOnly(True)
        for label, field, callback in (
            ("원본 PDF", self.pdf_field, self._select_pdf),
            ("추가할 Word", self.word_field, self._select_word),
            ("저장 위치", self.output_field, self._select_output),
        ):
            wrapper = QWidget()
            line = QHBoxLayout(wrapper)
            line.setContentsMargins(0, 0, 0, 0)
            line.addWidget(field)
            browse = QPushButton("찾아보기")
            browse.clicked.connect(callback)
            line.addWidget(browse)
            form.addRow(label, wrapper)

        self.encrypt_checkbox = QCheckBox("최종 PDF에 비밀번호 설정 (AES-256)")
        self.encrypt_checkbox.setChecked(True)
        layout.addWidget(self.encrypt_checkbox)

        password_row = QHBoxLayout()
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("비밀번호를 생성하거나 직접 입력하세요")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.generate_button = QPushButton("자동 생성")
        self.copy_button = QPushButton("복사")
        self.show_checkbox = QCheckBox("표시")
        password_row.addWidget(self.password_field)
        password_row.addWidget(self.generate_button)
        password_row.addWidget(self.copy_button)
        password_row.addWidget(self.show_checkbox)
        layout.addLayout(password_row)

        self.encrypt_checkbox.toggled.connect(self._toggle_password)
        self.generate_button.clicked.connect(lambda: self.password_field.setText(generate_password()))
        self.copy_button.clicked.connect(lambda: QGuiApplication.clipboard().setText(self.password_field.text()))
        self.show_checkbox.toggled.connect(
            lambda checked: self.password_field.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        self.generate_button.click()

        self.status_label = QLabel("PDF를 선택한 뒤 Word를 추가해 병합합니다. (Word → PDF 변환에는 LibreOffice 필요)")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.merge_button = QPushButton("PDF 생성")
        self.merge_button.clicked.connect(self._start_merge)
        layout.addWidget(self.merge_button)

    def _toggle_password(self, enabled: bool) -> None:
        for control in (self.password_field, self.generate_button, self.copy_button, self.show_checkbox):
            control.setEnabled(enabled)

    def _select_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "원본 PDF 선택", "", "PDF (*.pdf)")
        if path:
            self.pdf_field.setText(path)
            if not self.output_field.text():
                self.output_field.setText(str(Path(path).with_name(Path(path).stem + "_merged.pdf")))

    def _select_word(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Word 선택", "", "Word (*.docx *.doc)")
        if path:
            self.word_field.setText(path)

    def _select_output(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "결과 PDF 저장", self.output_field.text() or "merged.pdf", "PDF (*.pdf)"
        )
        if path:
            self.output_field.setText(path if path.lower().endswith(".pdf") else path + ".pdf")

    def _start_merge(self) -> None:
        pdf, word, output = (field.text().strip() for field in
                             (self.pdf_field, self.word_field, self.output_field))
        if not pdf or not word or not output:
            QMessageBox.warning(self, "입력 확인", "PDF, Word, 저장 위치를 모두 선택하세요.")
            return
        password = self.password_field.text() if self.encrypt_checkbox.isChecked() else None
        if password is not None and not password:
            QMessageBox.warning(self, "비밀번호 확인", "비밀번호를 입력하거나 자동 생성하세요.")
            return
        if Path(output).expanduser().resolve().exists():
            answer = QMessageBox.question(self, "파일 덮어쓰기", "결과 파일이 이미 존재합니다. 덮어쓸까요?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.merge_button.setEnabled(False)
        self.status_label.setText("변환 및 병합 중...")
        self.thread = QThread(self)
        self.worker = MergeWorker(pdf, word, output, password)
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

    def _clear_worker(self) -> None:
        self.merge_button.setEnabled(True)
        self.thread = None
        self.worker = None

    def _success(self, pages: int) -> None:
        self.status_label.setText(f"완료: {pages}페이지 PDF를 저장했습니다.")
        QMessageBox.information(self, "완료", f"PDF 생성 완료 ({pages}페이지)\n{self.output_field.text()}")

    def _failure(self, reason: str) -> None:
        self.status_label.setText("실패: " + reason)
        QMessageBox.critical(self, "PDF 생성 실패", reason)

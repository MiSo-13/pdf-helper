"""PDF Helper GUI 진입점."""
import sys
from PyQt6.QtWidgets import QApplication
from pdf_helper.window import PdfHelperWindow
from pdf_helper.diagnostics import enable_diagnostics


def main() -> int:
    enable_diagnostics()
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Helper")
    window = PdfHelperWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

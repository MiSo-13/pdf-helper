"""PDF Helper GUI 진입점."""
import sys
from PyQt6.QtWidgets import QApplication
from pdf_helper.window import PdfHelperWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Helper")
    window = PdfHelperWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

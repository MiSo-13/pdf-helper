"""PDF Helper GUI 진입점."""
import sys
from PyQt6.QtWidgets import QApplication
from pdf_helper.window import PdfHelperWindow
from pdf_helper.diagnostics import enable_diagnostics, install_qt_logging, event, log_exception


def main() -> int:
    enable_diagnostics()
    install_qt_logging()
    event("APP_INITIALIZING")
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("PDF Helper")
        app.aboutToQuit.connect(lambda: event("APP_ABOUT_TO_QUIT"))
        window = PdfHelperWindow()
        window.show()
        event("MAIN_WINDOW_SHOWN")
        code = app.exec()
        event("APP_EXIT", code=code)
        return code
    except BaseException:
        log_exception("main")
        raise


if __name__ == "__main__":
    sys.exit(main())

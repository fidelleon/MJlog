import sys

from PySide6.QtWidgets import QApplication  # noqa: E402

from mjlog.gui.main_window import MainWindow  # noqa: E402


def main():
    """Launch MJlog GUI application."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

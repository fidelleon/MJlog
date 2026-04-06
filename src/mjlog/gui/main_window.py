"""MDI main window for MJlog."""

from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QCloseEvent

from mjlog.gui.ui.main_window_ui import Ui_MainWindow


class MainWindow(QMainWindow):
    """Main MDI window for MJlog application."""

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionInitializeDatabase.triggered.connect(
            self.on_init_db_requested
        )
        self.ui.actionViewCountries.triggered.connect(
            self.on_view_countries_requested
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Close all MDI child windows first so they can save their state."""
        for sub_window in self.ui.mdiArea.subWindowList():
            widget = sub_window.widget()
            if widget is not None and hasattr(widget, "save_state"):
                widget.save_state()
        super().closeEvent(event)

    def on_init_db_requested(self):
        """Handle Initialize database action."""
        from mjlog.gui.windows.read_data_window import ReadDataWindow

        child_window = ReadDataWindow(self.ui.mdiArea)
        self.ui.mdiArea.addSubWindow(child_window)
        child_window.show()

    def on_view_countries_requested(self):
        """Handle View > Countries action."""
        from mjlog.gui.windows.countries_window import CountriesWindow

        child_window = CountriesWindow(self.ui.mdiArea)
        self.ui.mdiArea.addSubWindow(child_window)
        child_window.show()

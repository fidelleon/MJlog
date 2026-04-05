"""MDI main window for MJlog."""

from PySide6.QtWidgets import QMainWindow, QMdiArea
from PySide6.QtGui import QAction


class MainWindow(QMainWindow):
    """Main MDI window for MJlog application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MJlog")
        self.setGeometry(100, 100, 1024, 768)

        self.mdi_area = QMdiArea()
        self.setCentralWidget(self.mdi_area)

        self.create_menu_bar()

    def create_menu_bar(self):
        """Create menu bar with File and Settings menus."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        file_menu.addAction("Exit", self.close)

        settings_menu = menubar.addMenu("Settings...")
        init_db_action = QAction("Initialize database", self)
        init_db_action.triggered.connect(self.on_init_db_requested)
        settings_menu.addAction(init_db_action)

    def on_init_db_requested(self):
        """Handle Initialize database action."""
        from mjlog.gui.windows.read_data_window import ReadDataWindow

        child_window = ReadDataWindow(self.mdi_area)
        self.mdi_area.addSubWindow(child_window)
        child_window.show()

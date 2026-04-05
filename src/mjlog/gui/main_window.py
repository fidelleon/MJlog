"""MDI main window for MJlog."""

from PySide6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QMessageBox,
)

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
        self.ui.actionImportDXCC.triggered.connect(
            self.on_import_dxcc_requested
        )

    def on_init_db_requested(self):
        """Handle Initialize database action."""
        from mjlog.gui.windows.read_data_window import ReadDataWindow

        child_window = ReadDataWindow(self.ui.mdiArea)
        self.ui.mdiArea.addSubWindow(child_window)
        child_window.show()

    def on_import_dxcc_requested(self):
        """Handle Import DXCC action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import DXCC Data",
            "",
            "Excel Files (*.xlsx);;All Files (*)",
        )

        if not file_path:
            return

        try:
            from mjlog.db.loaders import import_dxcc_to_db

            count = import_dxcc_to_db(file_path)
            if count > 0:
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Imported {count} DXCC entities successfully.",
                )
            else:
                QMessageBox.warning(
                    self,
                    "No Import Needed",
                    "Database already contains DXCC entities.",
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Failed",
                f"Error importing DXCC data:\n{str(e)}",
            )

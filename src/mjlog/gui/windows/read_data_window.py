"""Read data MDI child window."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal, Qt


class ReadDataWindow(QWidget):
    """MDI child window for reading data from database."""

    data_loaded = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Read Local Data")
        self.setGeometry(50, 50, 400, 250)

        layout = QVBoxLayout()

        self.read_button = QPushButton("Read local data")
        self.read_button.clicked.connect(self.on_read_clicked)
        layout.addWidget(self.read_button)

        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setLayout(layout)

        self.data_loaded.connect(self.on_data_loaded)

    def on_read_clicked(self):
        """Handle Read local data button click."""
        self.status_label.setText("Loading...")
        try:
            from mjlog.db.models import Entry
            from mjlog.db.session import get_session

            session = get_session()
            try:
                entries = session.query(Entry).all()
                self.data_loaded.emit(entries)
            finally:
                session.close()
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def on_data_loaded(self, entries):
        """Handle data loaded signal."""
        count = len(entries)
        self.status_label.setText(f"Loaded {count} entries")
        if count > 0:
            for entry in entries:
                print(f"  - {entry}")

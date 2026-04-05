"""Countries viewer window for DXCC entities."""

from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent

from mjlog.db.session import get_session
from mjlog.db.models import DXCCEntity
from mjlog.gui.settings import load_window_state, save_window_state


class CountriesWindow(QWidget):
    """MDI child window showing DXCC countries in a read-only table."""

    WINDOW_NAME = "CountriesWindow"

    def __init__(self, mdi_area):
        super().__init__()
        self.mdi_area = mdi_area
        self.setWindowTitle("DXCC Countries")

        self.all_entities = []

        main_layout = QVBoxLayout(self)

        # Create filter controls
        filter_layout = QHBoxLayout()

        # Special Use dropdown
        filter_layout.addWidget(QLabel("Special Use:"))
        self.combo_special_use = QComboBox()
        self.combo_special_use.addItems(["All", "Regular", "Special use"])
        self.combo_special_use.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.combo_special_use)

        # Deleted dropdown
        filter_layout.addWidget(QLabel("Deleted:"))
        self.combo_deleted = QComboBox()
        self.combo_deleted.addItems(["All", "No", "Yes"])
        self.combo_deleted.currentIndexChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.combo_deleted)

        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Create read-only table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)

        # Set up columns
        columns = [
            "Prefix",
            "Entity Code",
            "Name",
            "DXCC Name",
            "Continent",
            "ITU Zone",
            "CQ Zone",
            "Latitude",
            "Longitude",
            "UTC Offset",
            "Special Use",
            "Deleted",
        ]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Load all entities from database
        session = get_session()
        try:
            self.all_entities = session.query(DXCCEntity).order_by(
                DXCCEntity.entity_code
            ).all()
        finally:
            session.close()

        # Load saved state
        self.load_state()

        # Initial population
        self.apply_filters()

        # Auto-resize columns to content
        self.table.resizeColumnsToContents()

        main_layout.addWidget(self.table)

    def load_state(self) -> None:
        """Load window geometry and dropdown states from saved state."""
        state = load_window_state(self.WINDOW_NAME)

        # Restore window geometry
        if "geometry" in state:
            geom = state["geometry"]
            self.setGeometry(
                geom["x"], geom["y"], geom["width"], geom["height"]
            )
        else:
            self.setGeometry(0, 0, 900, 600)

        # Restore dropdown selections
        special_use_index = state.get("special_use_index", 0)
        deleted_index = state.get("deleted_index", 0)
        self.combo_special_use.setCurrentIndex(special_use_index)
        self.combo_deleted.setCurrentIndex(deleted_index)

        # Restore column widths
        column_widths = state.get("column_widths", {})
        for col_idx, width in column_widths.items():
            try:
                self.table.setColumnWidth(int(col_idx), width)
            except (ValueError, IndexError):
                pass

    def apply_filters(self) -> None:
        """Filter table based on dropdown selections."""
        special_use_index = self.combo_special_use.currentIndex()
        deleted_index = self.combo_deleted.currentIndex()

        # Filter by special_use
        if special_use_index == 0:  # All
            special_use_filter = None
        elif special_use_index == 1:  # Regular
            special_use_filter = False
        else:  # Special use
            special_use_filter = True

        # Filter by deleted
        if deleted_index == 0:  # All
            deleted_filter = None
        elif deleted_index == 1:  # No
            deleted_filter = False
        else:  # Yes
            deleted_filter = True

        filtered_entities = [
            e for e in self.all_entities
            if (special_use_filter is None or
                e.special_use == special_use_filter) and
            (deleted_filter is None or e.deleted == deleted_filter)
        ]

        self.table.setRowCount(len(filtered_entities))

        for row, entity in enumerate(filtered_entities):
            items = [
                str(entity.prefix),
                str(entity.entity_code),
                str(entity.name),
                str(entity.dxcc_name),
                str(entity.continent),
                str(entity.itu_zone if entity.itu_zone else ""),
                str(entity.cq_zone_id if entity.cq_zone_id else ""),
                str(entity.latitude if entity.latitude else ""),
                str(entity.longitude if entity.longitude else ""),
                str(entity.utc_offset if entity.utc_offset else ""),
                "Yes" if entity.special_use else "No",
                "Yes" if entity.deleted else "No",
            ]

            for col, item_text in enumerate(items):
                table_item = QTableWidgetItem(item_text)
                table_item.setFlags(
                    table_item.flags() & ~Qt.ItemIsEditable
                )
                self.table.setItem(row, col, table_item)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save window state before closing."""
        geometry = self.geometry()
        state = {
            "geometry": {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height(),
            },
            "special_use_index": self.combo_special_use.currentIndex(),
            "deleted_index": self.combo_deleted.currentIndex(),
            "column_widths": {
                str(i): self.table.columnWidth(i)
                for i in range(self.table.columnCount())
            },
        }
        save_window_state(self.WINDOW_NAME, state)
        super().closeEvent(event)

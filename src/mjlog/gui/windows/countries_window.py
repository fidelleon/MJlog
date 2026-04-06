"""Countries viewer window for DXCC entities."""

from PySide6.QtWidgets import (
    QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout,
    QComboBox, QLabel
)
from PySide6.QtCore import Qt, QEvent, QObject
from PySide6.QtGui import QCloseEvent

from mjlog.db.session import get_session
from mjlog.db.models import DXCCEntity
from mjlog.gui.settings import load_window_state, save_window_state


class _SubWindowEventFilter(QObject):
    """Event filter installed on the QMdiSubWindow to track move/resize."""

    def __init__(self, on_geometry_changed):
        super().__init__()
        self._on_geometry_changed = on_geometry_changed

    def eventFilter(self, watched, event) -> bool:
        if event.type() in (QEvent.Type.Move, QEvent.Type.Resize):
            self._on_geometry_changed(watched.geometry())
        return False  # never consume the event


class CountriesWindow(QWidget):
    """MDI child window showing DXCC countries in a read-only table."""

    WINDOW_NAME = "CountriesWindow"

    def __init__(self, mdi_area):
        super().__init__()
        self.mdi_area = mdi_area
        self.setWindowTitle("DXCC Countries")

        self.all_entities = []
        self._mdi_sub_window = None
        self._sub_window_event_filter = None
        self._current_geometry = None

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
        self.combo_deleted.addItems(["All", "Current", "Deleted"])
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

        # Store geometry for later use after window is added to MDI area
        self.saved_geometry = state.get("geometry", None)

    def _on_subwindow_geometry_changed(self, geometry) -> None:
        """Called whenever the MDI subwindow is moved or resized."""
        self._current_geometry = {
            "x": geometry.x(),
            "y": geometry.y(),
            "width": geometry.width(),
            "height": geometry.height(),
        }

    def show(self) -> None:
        """Override show to apply geometry and install event filter."""
        super().show()

        self._mdi_sub_window = self.parent()

        if self._mdi_sub_window is not None:
            # Install event filter to track move/resize in real time
            self._sub_window_event_filter = _SubWindowEventFilter(
                self._on_subwindow_geometry_changed
            )
            self._mdi_sub_window.installEventFilter(
                self._sub_window_event_filter
            )

            # Apply saved geometry
            if self.saved_geometry:
                geom = self.saved_geometry
                self._mdi_sub_window.setGeometry(
                    geom["x"], geom["y"],
                    geom["width"], geom["height"]
                )
            else:
                self._mdi_sub_window.setGeometry(0, 0, 900, 600)
        else:
            self.setGeometry(0, 0, 900, 600)

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
        elif deleted_index == 1:  # Current
            deleted_filter = False
        else:  # Deleted
            deleted_filter = True

        filtered_entities = [
            e for e in self.all_entities
            if (special_use_filter is None or
                e.special_use == special_use_filter) and
            (deleted_filter is None or e.deleted == deleted_filter)
        ]

        # Temporarily disable sorting while updating table to prevent
        # synchronization issues between filter and sort
        self.table.setSortingEnabled(False)
        self.table.clearContents()
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

        # Re-enable sorting after all data is loaded
        self.table.setSortingEnabled(True)

    def save_state(self) -> None:
        """Save window geometry and UI state to persistent settings."""
        # Use the geometry tracked via the event filter (updated on every
        # move/resize), which is always accurate regardless of teardown state
        geometry = self._current_geometry or self.saved_geometry or {
            "x": 0, "y": 0, "width": 900, "height": 600
        }

        state = {
            "geometry": geometry,
            "special_use_index": self.combo_special_use.currentIndex(),
            "deleted_index": self.combo_deleted.currentIndex(),
            "column_widths": {
                str(i): self.table.columnWidth(i)
                for i in range(self.table.columnCount())
            },
        }
        save_window_state(self.WINDOW_NAME, state)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Save window state before closing."""
        self.save_state()
        super().closeEvent(event)

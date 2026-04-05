"""Countries viewer window for DXCC entities."""

from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt

from mjlog.db.session import get_session
from mjlog.db.models import DXCCEntity


class CountriesWindow(QWidget):
    """MDI child window showing DXCC countries in a read-only table."""

    def __init__(self, mdi_area):
        super().__init__()
        self.mdi_area = mdi_area
        self.setWindowTitle("DXCC Countries")
        self.setGeometry(0, 0, 900, 600)

        layout = QVBoxLayout(self)

        # Create read-only table
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

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

        # Populate table from database
        session = get_session()
        try:
            entities = session.query(DXCCEntity).order_by(
                DXCCEntity.entity_code
            ).all()

            self.table.setRowCount(len(entities))

            for row, entity in enumerate(entities):
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

            # Auto-resize columns to content
            self.table.resizeColumnsToContents()

        finally:
            session.close()

        layout.addWidget(self.table)

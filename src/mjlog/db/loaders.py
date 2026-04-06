"""Data loaders for importing external data into database."""

import zipfile
import xml.etree.ElementTree as ET

from mjlog.db.models import DXCCEntity

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def col_letter_to_num(col_letter):
    """Convert Excel column letter to 0-based position (A=0, B=1, ..., Z=25, AA=26)."""
    result = 0
    for char in col_letter:
        result = result * 26 + (ord(char) - ord('A') + 1)
    return result - 1


def load_dxcc_from_xlsx(xlsx_path: str):
    """Load DXCC entities from Excel file for updating existing entities.

    Args:
        xlsx_path: Path to DXCC.xlsx file

    Returns:
        List of DXCCEntity objects
    """
    entities = []

    try:
        with zipfile.ZipFile(xlsx_path, "r") as zip_ref:
            # Read shared strings (for cell references)
            with zip_ref.open("xl/sharedStrings.xml") as strings_file:
                strings_tree = ET.parse(strings_file)
                strings_root = strings_tree.getroot()
                strings = []
                for t in strings_root.findall(f"{NS}si"):
                    t_elem = t.find(f"{NS}t")
                    if t_elem is not None:
                        strings.append(t_elem.text)

            # Read worksheet
            with zip_ref.open("xl/worksheets/sheet1.xml") as sheet_file:
                tree = ET.parse(sheet_file)
                root = tree.getroot()

            rows = root.findall(f".//{NS}row")

            # Skip header row, process data rows
            for row in rows[1:]:
                cells = row.findall(f"{NS}c")

                # Build sparse array for this row
                values = [None] * 13
                for cell in cells:
                    ref = cell.get("r")  # e.g., "A2", "B2"
                    if ref:
                        col_letter = ref.rstrip("0123456789")
                        col_num = col_letter_to_num(col_letter)
                        if col_num < 13:
                            v_elem = cell.find(f"{NS}v")
                            if v_elem is not None and v_elem.text:
                                values[col_num] = v_elem.text

                # Parse and create entity
                try:
                    prefix_idx = int(float(values[0]))
                    dxcc_idx = int(float(values[1]))
                    name_idx = int(float(values[2]))
                    continent_idx = int(float(values[3]))
                    prefixes_idx = int(float(values[8])) if values[8] else None

                    entity = DXCCEntity(
                        prefix=strings[prefix_idx],
                        dxcc_name=strings[dxcc_idx],
                        name=strings[name_idx],
                        continent=strings[continent_idx],
                        itu_zone=(
                            int(float(values[4])) if values[4] else None
                        ),
                        latitude=(
                            float(values[5]) if values[5] else None
                        ),
                        longitude=(
                            float(values[6]) if values[6] else None
                        ),
                        utc_offset=(
                            int(float(values[7])) if values[7] else None
                        ),
                        prefixes=(
                            strings[prefixes_idx]
                            if prefixes_idx is not None
                            else None
                        ),
                        cq_zone_id=(
                            int(float(values[9])) if values[9] else None
                        ),
                        entity_code=(
                            int(float(values[10])) if values[10] else None
                        ),
                        special_use=(
                            bool(int(float(values[11])))
                            if values[11]
                            else False
                        ),
                        deleted=(
                            bool(int(float(values[12])))
                            if values[12]
                            else False
                        ),
                    )
                    entities.append(entity)
                except (IndexError, ValueError, TypeError) as e:
                    print(f"Error parsing row: {e}")
                    continue

    except Exception as e:
        print(f"Error loading DXCC data: {e}")
        raise

    return entities

"""Data loaders for importing external data into database."""

import zipfile
import xml.etree.ElementTree as ET

from mjlog.db.models import DXCCEntity
from mjlog.db.session import get_session

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def load_dxcc_from_xlsx(xlsx_path: str):
    """Load DXCC entities from Excel file.

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
                if len(cells) < 13:
                    continue

                # Extract values
                values = []
                for cell in cells[:13]:
                    v_elem = cell.find(f"{NS}v")
                    if v_elem is not None and v_elem.text:
                        values.append(v_elem.text)
                    else:
                        values.append(None)

                # Parse and create entity
                try:
                    prefix_idx = int(float(values[0]))
                    dxcc_idx = int(float(values[1]))
                    name_idx = int(float(values[2]))
                    continent_idx = int(float(values[3]))
                    prefixes_idx = int(float(values[8]))

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
                        prefixes=strings[prefixes_idx],
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


def import_dxcc_to_db(xlsx_path: str) -> int:
    """Import DXCC entities from Excel file into database.

    Args:
        xlsx_path: Path to DXCC.xlsx file

    Returns:
        Number of entities imported
    """
    entities = load_dxcc_from_xlsx(xlsx_path)
    session = get_session()

    try:
        # Check for existing data
        existing_count = session.query(DXCCEntity).count()
        if existing_count > 0:
            msg = f"Database already has {existing_count} DXCC entities"
            print(msg)
            return 0

        # Add all entities
        session.add_all(entities)
        session.commit()
        print(f"Imported {len(entities)} DXCC entities")
        return len(entities)

    except Exception as e:
        session.rollback()
        print(f"Error importing data: {e}")
        raise
    finally:
        session.close()

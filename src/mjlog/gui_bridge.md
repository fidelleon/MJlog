# GUI Bridge: CLI → Qt/PySide6 Integration

This document outlines the strategy for evolving the CLI into a PySide6 GUI while preserving the existing command structure and database layer.

## Architecture Overview

### Current State (CLI)
- `main.py` → `mjlog.cli.cli()` (click dispatcher)
- Commands: `init-db`, `add`, `list-entries`
- Database: SQLAlchemy session + models in `mjlog.db`
- Config: Loads `DATABASE_URL` from `mjlog.env`

### Future State (GUI)
- `main.py` → `mjlog.gui.MainWindow()` (PySide6 QMainWindow)
- Commands become **signals** → slots (Qt event system)
- Database layer **unchanged** (reuse `mjlog.db` module)
- Config layer **unchanged** (reuse `mjlog.config` module)

## Signal/Slot Mapping

CLI commands will map to GUI signals and slots for clean separation:

```
CLI Command          →  GUI Signal/Slot
──────────────────────────────────────
init-db              →  MainWindow.init_db_requested()
add (title, content) →  MainWindow.entry_add_requested(title: str, content: str)
list-entries         →  MainWindow.entries_list_requested()
```

### Entry Point Migration

**Before (CLI)**
```python
# main.py
from mjlog.cli import cli
def main():
    cli()
```

**After (GUI)**
```python
# main.py
from mjlog.gui import MainWindow
from PySide6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

## Module Structure

New GUI module to add:
```
src/mjlog/
├── gui/
│   ├── __init__.py
│   ├── main_window.py       # QMainWindow subclass
│   ├── widgets/             # Custom widgets (optional)
│   │   ├── __init__.py
│   │   └── entry_list.py
│   └── signals/             # Signal definitions (optional)
│       ├── __init__.py
│       └── events.py
├── cli.py                    # Keep for testing/scripting
├── config.py                 # Reuse
├── db/
│   ├── __init__.py          # Reuse
│   ├── models.py            # Reuse
│   └── session.py           # Reuse
└── __init__.py
```

## Implementation Strategy

### Phase 1: GUI Stub
1. Create `mjlog.gui.MainWindow` as empty PySide6 QMainWindow
2. Keep CLI working alongside GUI (dual-mode in main.py with --gui flag)
3. Update main.py to detect mode and launch accordingly

### Phase 2: Signal Binding
1. Define custom signals in `MainWindow` matching CLI commands
2. Connect signals to database operations (reuse `mjlog.db` layer)
3. Implement basic UI widgets (entry form, list view)

### Phase 3: Full Integration
1. Remove dual-mode logic; make GUI primary
2. Migrate CLI to internal command dispatcher (optional for headless testing)
3. Add PySide6-specific features (persistence, styling, etc.)

## Database Reuse Pattern

GUI will **not** duplicate database logic. Instead:

```python
# src/mjlog/gui/main_window.py
from mjlog.db.models import Entry
from mjlog.db.session import get_session


class MainWindow(QMainWindow):
    def handle_add_entry(self, title: str, content: str):
        """Reuse the same database layer as CLI."""
        session = get_session()
        try:
            entry = Entry(title=title, content=content)
            session.add(entry)
            session.commit()
            self.entries_updated.emit()  # Signal refresh
        finally:
            session.close()
```

## Config Reuse Pattern

GUI will use the same config bootstrap:

```python
# src/mjlog/gui/__init__.py
from mjlog.config import get_database_url

# Validate config at startup
try:
    db_url = get_database_url()
except ValueError as e:
    # Show error dialog to user
    show_error_dialog(str(e))
```

## Testing Strategy

- **CLI tests**: Test commands directly via `mjlog.cli`
- **Database tests**: Test ORM layer in isolation
- **GUI tests**: Test signal/slot connections with `QTest`
- **Integration tests**: Full flow from GUI → DB → signal emission

## Notes

- Keep database and config modules **CLI-agnostic** for maximum reuse
- Use Qt's signal/slot mechanism instead of direct function calls for loose coupling
- Consider creating a **service layer** (`mjlog.services`) if business logic grows complex
- Plan for headless mode: keep CLI for scripting/automation

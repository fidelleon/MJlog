# AGENTS.md

## Project Snapshot
- **MJlog**: A Python GUI application (PySide6) for ham radio logging with PostgreSQL backend.
- **Entry point**: `main.py` launches PySide6 GUI (`MainWindow` from `mjlog.gui.main_window`).
- **Package**: `src/mjlog/` contains all application code (CLI, DB, GUI modules).
- **Data layer**: SQLAlchemy ORM with Alembic migrations; supports PostgreSQL and read-only MySQL (HRD QSO log).
- **Testing**: pytest with fixtures (in-memory SQLite for tests), ~25% coverage target, 18+ tests passing.

## Architecture Overview

### Directory Structure
```
src/mjlog/
├── __init__.py
├── cli.py              # Click-based CLI (init_db command)
├── config.py           # Environment loading (mjlog.env -> DATABASE_URL, HRD_DATABASE_URL)
├── db/
│   ├── models.py       # SQLAlchemy ORM: ~500 lines, 15+ model classes
│   └── session.py      # Engine/session factory; dual DB support (main + HRD)
├── gui/
│   ├── main_window.py  # MDI main window with action handlers
│   ├── settings.py     # Settings persistence
│   ├── ui/             # Generated UI files (Qt Designer)
│   └── windows/        # Sub-windows: CountriesWindow, ReadDataWindow
alembic/               # Schema migrations; env.py imports from src/mjlog
tests/
├── conftest.py         # Fixtures: db_session, test_db_engine, app_config, mock_qapp
├── db/test_models.py   # Model tests (Mode, Band, DXCCEntity, etc.)
├── gui/                # GUI tests (pytest-qt)
└── fixtures/factories.py  # factory-boy factories
```

### Data Flow
1. **Startup**: `main.py` → `main()` → `QApplication` → `MainWindow()`
2. **MainWindow** loads UI from `Ui_MainWindow` (generated from Qt Designer)
3. **Menu actions** (File → Initialize Database, View → Countries) instantiate child windows
4. **Child windows** (CountriesWindow, ReadDataWindow) manipulate database via SQLAlchemy sessions
5. **Database**: PostgreSQL (via `DATABASE_URL`); optional HRD MySQL read-only access (via `HRD_DATABASE_URL`)
6. **Models** in `src/mjlog/db/models.py` define all tables (DXCCEntity, Mode, Band, Station, QSO, Membership, etc.)

### Key Integration Points
- **Config bootstrap**: `mjlog.config.load_config()` loads `mjlog.env` from repo root; must run before database calls
- **Session management**: `mjlog.db.session.get_session()` returns thread-local session; caches engine/factory globally
- **Dual database**: `get_session(db="hrd")` → reads from MySQL HRD table; `get_session()` (default) → PostgreSQL
- **GUI bridges**: Child windows use `save_state()` on close (MainWindow.closeEvent); settings persist to disk

## Critical Developer Workflows

### Environment & Dependencies
```bash
# Sync locked dependencies
uv sync --frozen

# Run GUI app from repo root
uv run python main.py

# Initialize database (CLI command)
uv run python -m mjlog.cli init_db
```

### Testing & Quality
```bash
# Run all tests (pytest with in-memory SQLite)
uv run pytest

# Run with coverage (targets src/mjlog, fail-under=50%)
uv run pytest --cov=src/mjlog --cov-report=html

# Lint (ruff, flake8, mypy, black, isort)
uv run ruff check .
uv run flake8 src/mjlog tests
uv run mypy src/mjlog/
uv run black src/mjlog tests
uv run isort src/mjlog tests

# Type-check with strict mode
uv run mypy src/mjlog/ --strict
```

### Database Migrations
```bash
# Generate migration from model changes
uv run alembic revision --autogenerate -m "Description"

# Apply migrations
uv run alembic upgrade head

# Downgrade (if needed)
uv run alembic downgrade -1
```

### GUI Development
- UI files generated via Qt Designer → compiled to `mjlog/gui/ui/main_window_ui.py`
- Rebuild with: `bash scripts/build_ui.sh`
- See `src/mjlog/gui/BUILD_UI.md` for details

## Project-Specific Conventions

### Configuration & Environment
- **Config file**: `mjlog.env` (repo root); loaded by `mjlog.config.load_config()`
- **Required vars**: `DATABASE_URL` (PostgreSQL), `HRD_DATABASE_URL` (MySQL, optional)
- **Format**: `DATABASE_URL=postgresql://user:pass@localhost/mjlog`

### Database
- **ORM**: SQLAlchemy 2.0 with declarative mapping (`Base = declarative_base()`)
- **Models file**: `src/mjlog/db/models.py` (single ~500-line file with all models)
- **Migrations**: Alembic in `alembic/` folder; imports `Base.metadata` from models
- **Testing**: Tests use in-memory SQLite (conftest.py fixture `test_db_engine`); no PostgreSQL required locally
- **Key models**:
  - **DXCCEntity**: Ham radio DXCC countries/entities with Big CTY prefix data (fetched from country-files.com feed)
  - **Mode/Band**: Radio modes and frequency bands
  - **Station**: User's station config
  - **QSO**: Contact log entries
  - **Membership**: Club membership tracking
  - **HRDQso**: Read-only MySQL view of external HRD database

### GUI Patterns
- **MDI (Multi-Document Interface)**: MainWindow uses QMdiArea for child windows
- **Sub-windows**: Inherit from QWidget, implement `save_state()` for persistence
- **Lazy imports**: Sub-window classes imported inside action handlers (e.g., `on_view_countries_requested()`) to avoid startup overhead
- **UI generation**: Qt Designer files compiled to `ui/` folder; imported as `from mjlog.gui.ui.main_window_ui import Ui_MainWindow`

### Testing Patterns
- **Fixtures** (in `tests/conftest.py`):
  - `test_db_engine`: Session-scoped in-memory SQLite
  - `db_session`: Function-scoped, rolled back after each test
  - `app_config`: Mocked environment vars
  - `mock_qapp`: Mocked QApplication
- **Factories** (in `tests/fixtures/factories.py`): Use factory-boy for model instances
- **Test markers**: `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.gui`, `@pytest.mark.db`
- **Coverage config**: `pyproject.toml` excludes `src/mjlog/gui/ui/*` (generated files)

### Import Organization
- **Relative imports**: Use absolute imports from `mjlog.*` (not relative)
- **Stub types**: Use `from typing import TYPE_CHECKING` for forward refs
- **isort config**: Black profile, 100-char line length (see `pyproject.toml`)

## File Reference Guide

| File | Purpose |
|------|---------|
| `main.py` | Entry point; launches QApplication and MainWindow |
| `src/mjlog/cli.py` | Click CLI dispatcher; `init_db` command |
| `src/mjlog/config.py` | Environment variable loading (mjlog.env) |
| `src/mjlog/db/models.py` | All SQLAlchemy ORM models (~500 lines) |
| `src/mjlog/db/session.py` | Engine/session factory; dual DB support |
| `src/mjlog/gui/main_window.py` | MDI main window class |
| `src/mjlog/gui/windows/*.py` | Child windows (CountriesWindow, ReadDataWindow) |
| `alembic/env.py` | Alembic migration runner; imports from src/mjlog |
| `alembic/versions/*.py` | Migration scripts |
| `tests/conftest.py` | pytest fixtures and configuration |
| `tests/db/test_models.py` | Database model tests |
| `tests/fixtures/factories.py` | factory-boy test data factories |
| `pyproject.toml` | Project metadata, dependencies, tool configs |
| `mjlog.env` | Runtime configuration (DATABASE_URL, etc.) |

## Common Tasks & Patterns

### Adding a New Model
1. Add class to `src/mjlog/db/models.py` inheriting from `Base`
2. Generate migration: `uv run alembic revision --autogenerate -m "Add NewModel"`
3. Write tests in `tests/db/test_models.py`
4. Commit migration + model

### Adding a New GUI Window
1. Design UI in Qt Designer; save to `src/mjlog/gui/ui/window_name.ui`
2. Run `bash scripts/build_ui.sh` to generate `window_name_ui.py`
3. Create `src/mjlog/gui/windows/window_name.py` inheriting from QWidget
4. Import and instantiate in `MainWindow` action handler (use lazy import)
5. Implement `save_state()` for persistence

### Adding a CLI Command
1. Add `@cli.command()` function to `src/mjlog/cli.py`
2. Implement with Click decorators
3. Test with `uv run python -m mjlog.cli command_name`

### Running Tests Locally
- **Full suite**: `uv run pytest -v` (uses in-memory SQLite)
- **With coverage**: `uv run pytest --cov=src/mjlog --cov-report=html`
- **Single test**: `uv run pytest tests/db/test_models.py::TestMode::test_mode_creation -v`
- **No PostgreSQL needed**: conftest.py uses SQLite `:memory:` database

## Agent Change Checklist
- ✅ Check `pyproject.toml` before adding dependencies; keep dev tools in `[dependency-groups].dev`
- ✅ After code changes, run: `uv run pytest`, `uv run ruff check .`, `uv run python main.py`
- ✅ For database changes, generate migration: `uv run alembic revision --autogenerate -m "Description"`
- ✅ Update this file if adding new major subsystems or changing architecture
- ✅ Ensure tests pass before commit: `uv run pytest` (target 50%+ coverage)

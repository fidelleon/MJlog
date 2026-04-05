# AGENTS.md

## Project Snapshot
- `MJlog` is an early-stage Python app with a single executable entrypoint: `main.py`.
- Current runtime behavior is intentionally minimal: `main()` prints `"Hello from mjlog!"` and exits.
- Project metadata and dependencies are defined in `pyproject.toml`; locked resolution is in `uv.lock`.
- `README.md` is short; this file is the main agent-facing operational guide.

## Architecture and Data Flow (Current)
- Startup path is explicit and linear: `if __name__ == "__main__":` -> `main()` in `main.py`.
- There is no package/module tree yet (`src/` does not exist).
- No persistence/UI/env bootstrap code is wired yet; declared deps are future integration points.
- Preserve startup inspectability: route new bootstrapping through `main()` first.

## Verified Developer Workflows
- Sync environment from lockfile:
  - `uv sync --frozen`
- Run app from repo root:
  - `uv run python main.py`
- Linting:
  - `uv run ruff check .`
  - `uv run flake8 main.py`
- `uv run flake8 .` currently traverses `.venv/` and reports third-party issues; keep flake8 scoped to project files until config excludes are added.

## Dependency Intent and Integration Boundaries
- Runtime dependencies declared in `pyproject.toml`:
  - `pyside6` -> GUI layer
  - `sqlalchemy` -> storage/data layer
  - `dotenv` -> environment configuration
- None are imported in `main.py` yet; when introducing one, create a clear boundary module and call it from `main()`.

## Conventions to Preserve
- Keep executable flow straightforward (match `main.py` style: tiny `main()`, explicit entrypoint guard).
- Use uv commands in docs/scripts to match lockfile-driven workflow.
- Align naming with `name = "mjlog"` when creating package paths.
- If you add major structure, update both `README.md` and `AGENTS.md` with concrete file references.

## Agent Change Checklist
- Confirm startup location in `main.py` before refactoring.
- Check `pyproject.toml` before adding tools/dependencies; keep dev tools in `[dependency-groups].dev`.
- After code changes, run at minimum: `uv run python main.py` and `uv run ruff check .`.
- Run flake8 against project files explicitly (for example `main.py`) until excludes exist.

# Backend

FastAPI backend for the UK Energy Grid Data & VPP Optimisation project, managed with [uv](https://docs.astral.sh/uv/).

## Setup

```bash
uv sync --all-groups
```

## Commands

| Command | Purpose |
|---|---|
| `uv run uvicorn app.main:app --reload` | Run the dev server at http://localhost:8000 |
| `uv run pytest` | Run the test suite |
| `uv run ruff check .` | Lint |
| `uv run ruff format .` | Format |
| `uv run ruff format --check .` | Check formatting without writing |

## Structure

- `app/core/` — shared configuration and utilities used by every subproject (e.g. `config.py`).
- `app/api/` — one router module per subproject/tab: `dashboard.py`, `forecasting.py`, `vpp.py`, plus `health.py` for the liveness check. Routers only depend on `app/core`, never on each other.
- `tests/` — pytest suite, mirrors the `app/` structure.

## Adding a new router

1. Create `app/api/<name>.py` with an `APIRouter(prefix="/api/<name>", tags=["<name>"])`.
2. Add a module docstring describing the subproject's real-world purpose.
3. Include the router in `app/main.py`.
4. Add a test under `tests/`.

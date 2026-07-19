# UK Energy Grid Data & VPP Optimisation

[![CI](https://github.com/james-hughes1/uk-energy-data/actions/workflows/ci.yml/badge.svg)](https://github.com/james-hughes1/uk-energy-data/actions/workflows/ci.yml)
[![Frontend](https://img.shields.io/badge/frontend-React%20%2B%20TypeScript%20%2B%20Vite-61DAFB)](frontend/README.md)
[![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20uv-009688)](backend/README.md)
[![License](https://img.shields.io/badge/license-unlicensed-lightgrey)](#)

A website for learning about the UK power grid — built by exploring real grid data, forecasting
energy prices, and optimising a virtual power plant (VPP) against those forecasts.

The project is organised as three self-contained tabs, each treated as its own subproject:

| Tab | What it does | Status |
|---|---|---|
| **Dashboard** | Live/historical UK grid data — e.g. imbalance price, system demand | Imbalance price chart wired up with mock data; live feed not yet connected |
| **Forecasting** | Energy price forecasting using quantile regression | Scaffolded — page and route exist, no model yet |
| **VPP Optimisation** | Battery dispatch optimisation for a virtual power plant, driven by the forecasts | Scaffolded — page and route exist, no optimiser yet |

The goal is to learn by building, not just to ship a dashboard — so each tab pairs its
implementation with plain-English explanations of the real-world context and, where relevant, the
data science/ML techniques behind it (see the `ExplainerPanel` component on each page).

## Architecture

```
uk-energy-data/
├── frontend/   React + TypeScript + Vite — one page per tab, shared UI/data-fetching in src/common/
└── backend/    FastAPI (Python, managed with uv) — one router per tab, shared config in app/core/
```

Each subproject (dashboard / forecasting / VPP) is kept independent on both sides of the stack:
frontend pages and backend routers never import from each other, only from the shared
`common`/`core` code. This keeps each tab addable/removable/rewritable without ripping up the
others. See [`frontend/README.md`](frontend/README.md) and [`backend/README.md`](backend/README.md)
for the full breakdown of each side, plus the pattern to follow when adding a new page/router.

## Quickstart

```bash
# Frontend
cd frontend
npm install
npm run dev        # http://localhost:5173

# Backend (in another terminal)
cd backend
uv sync --all-groups
uv run uvicorn app.main:app --reload   # http://localhost:8000
```

With just the frontend running, the Dashboard tab renders against mock data
(`frontend/src/dashboard/data/mockGridData.ts`) — no backend required to look around. The backend
currently exposes only placeholder `/api/<tab>/ping` endpoints and `/health`, ready to be filled in
with real data sources (e.g. Elexon/BMRS, National Grid ESO Data Portal) and model logic.

## Tech stack

- **Frontend** — React 19, TypeScript, Vite, React Router, Tailwind CSS, Plotly (`react-plotly.js`)
  for charts, Vitest + React Testing Library for tests, ESLint + Prettier for linting/formatting.
- **Backend** — FastAPI, Pydantic Settings, managed with [uv](https://docs.astral.sh/uv/), pytest
  for tests, Ruff for linting/formatting.

## Guidelines this project follows

1. Keep the code clean and documented; use appropriate linters/formatters (ESLint + Prettier for
   the frontend, Ruff for the backend).
2. Make the website visually pleasing to enable deeper understanding.
3. Include unit tests to ensure the code is robust (Vitest + React Testing Library, pytest).
4. Keep clear separation between subprojects, with shared code factored out separately.
5. Explain the real-world context and ML techniques used, in both the docs and the site itself.
6. Use Conventional Commits (`-type-: description`) for commit messages.

## Development tooling

- **Linting/formatting**: `npm run lint` / `npm run format` in `frontend/`; `uv run ruff check .` /
  `uv run ruff format .` in `backend/`.
- **Tests**: `npm run test` in `frontend/`; `uv run pytest` in `backend/`.
- **CI**: GitHub Actions runs lint, format-check, tests, and build for both sides on every push/PR
  (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)).
- **Pre-commit hooks**: install once at the repo root, then hooks run automatically on `git commit`.

  ```bash
  pipx install pre-commit   # or: pip install pre-commit
  pre-commit install
  ```

  The frontend hooks assume `frontend/node_modules` already exists (`npm install`), and the
  backend hooks assume `backend/.venv` already exists (`uv sync`).

## Roadmap

- [ ] Connect the Dashboard to a live data source (Elexon/BMRS or National Grid ESO) in place of
      mock data.
- [ ] Build the quantile regression model behind the Forecasting tab.
- [ ] Build the VPP battery-dispatch optimiser, driven by the forecasting output.
- [ ] Replace backend `/ping` placeholders with real endpoints as each subproject comes online.

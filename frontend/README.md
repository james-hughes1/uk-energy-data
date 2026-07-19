# Frontend

React + TypeScript + Vite frontend for the UK Energy Grid Data & VPP Optimisation project.

## Setup

```bash
npm install
```

## Commands

| Command                | Purpose                                       |
| ---------------------- | --------------------------------------------- |
| `npm run dev`          | Start the dev server at http://localhost:5173 |
| `npm run build`        | Type-check and build for production           |
| `npm run preview`      | Preview the production build                  |
| `npm run lint`         | Lint with ESLint                              |
| `npm run format`       | Format with Prettier                          |
| `npm run format:check` | Check formatting without writing              |
| `npm run test`         | Run the test suite once                       |
| `npm run test:watch`   | Run tests in watch mode                       |

## Structure

- `src/common/` — code shared by every subproject: `components/` (NavBar, PageLayout, ExplainerPanel, ErrorBoundary), `api/client.ts` (fetch wrapper for the backend), `hooks/`, `types/`, `utils/`.
- `src/dashboard/`, `src/forecasting/`, `src/vpp/` — one folder per tab/subproject. Each maps to a route in `src/App.tsx` and only imports from `common/` or itself, never from another subproject.
- `tests/` — Vitest + React Testing Library suite.

Each page wraps its explanatory content in a shared `ExplainerPanel` component, which is the anchor point for the real-world/ML-technique explanations called for by the project guidelines.

## Adding a new page

1. Create `src/<name>/<Name>Page.tsx` using `PageLayout` and `ExplainerPanel`.
2. Add a route for it in `src/App.tsx`.
3. Add a tab entry in `src/common/components/NavBar.tsx`.

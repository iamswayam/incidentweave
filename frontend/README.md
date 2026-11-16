# IncidentWeave Evaluation UI

React + Vite + TypeScript frontend for inspecting grounded investigations and hybrid retrieval (semantic, fulltext, RRF).

## Quick start

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL. By default the Vite dev server proxies `/api` to `http://localhost:8000`.

Start the FastAPI backend separately (`python -m scripts.serve` from the repo root).

## Settings

Use the in-app Settings dialog for:

- API base URL (leave empty to use the `/api` proxy)
- `X-API-Secret` when the backend requires it
- Optional GitHub repo URL for citation links

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Local development server |
| `npm run build` | Production build (`dist/`) |
| `npm run preview` | Preview the production build |

## Environment

See `.env.example`.

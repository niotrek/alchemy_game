

# Apothecaria — workshop starter

A cozy alchemist's apothecary. The starter you clone before the GitHub Copilot CLI workshop.

## Prerequisites

Install github cli:

curl -fsSL [https://gh.io/copilot-install](https://gh.io/copilot-install) | bash



You need Python 3.12, `[uv](https://docs.astral.sh/uv/)` (the Python package manager that runs `uv sync`), and Node 20+.

**macOS / Linux:**

```bash
# uv — Python package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Python 3.12 — uv can install it for you
uv python install 3.12

# Node 20+ — via Homebrew (macOS) or your distro's package manager
brew install node                                  # macOS
# or: curl -fsSL https://fnm.vercel.app/install | bash && fnm install 20
```

**Windows (PowerShell):**

```powershell
# uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Python 3.12
uv python install 3.12

# Node 20+
winget install OpenJS.NodeJS.LTS
```

Verify everything is on your `PATH`:

```bash
uv --version && python3.12 --version && node --version && make --version
```

> Windows users: `make` isn't installed by default. Use [Chocolatey](https://chocolatey.org/) (`choco install make`) or run the underlying commands from the [Make targets](#make-targets) table directly.

## Quickstart

```bash
git clone <this-repo>
cd <repo>
uv sync                # install python deps
make install           # install frontend deps (npm)
make seed              # creates apothecaria.sqlite
make dev               # backend on :8000, frontend on :5173
```

Open [http://localhost:5173](http://localhost:5173) for the game, or [http://localhost:8000/api/health](http://localhost:8000/api/health) for a backend health check.

## Endpoints (Phase A)


| Method | Path                      | What                                                |
| ------ | ------------------------- | --------------------------------------------------- |
| GET    | /api/health               | Health check                                        |
| GET    | /api/inventory            | List ingredients                                    |
| GET    | /api/recipes              | List recipes (with their ingredients)               |
| POST   | /api/customers/spawn      | Spawn a new customer (debugging / demo)             |
| GET    | /api/customers/next       | Get the oldest unserved customer                    |
| POST   | /api/customers/{id}/serve | Serve a customer (`{"ingredient_slugs": [...]}`)    |
| POST   | /api/brew                 | Combine ingredients (`{"ingredient_slugs": [...]}`) |
| WS     | /ws/events                | Live event stream (customer arrivals)               |


## Customer state

Active customers live **in memory** on `app.state.customer_store` and are reset on every server restart. The brew/serve event itself is recorded persistently in the `brew_history` table (with the customer fields snapshotted), so analytics queries still work after a customer is gone.

## Configuration

All settings via env vars (prefix `APOTHECARIA_`):


| Variable                               | Default                          | Notes                            |
| -------------------------------------- | -------------------------------- | -------------------------------- |
| `APOTHECARIA_DATABASE_URL`             | `sqlite:///./apothecaria.sqlite` |                                  |
| `APOTHECARIA_CUSTOMER_ARRIVAL_SECONDS` | `30`                             | Speed up to `5` while testing    |
| `APOTHECARIA_USE_AGENT_CUSTOMERS`      | `false`                          | M4 will flip this                |
| `APOTHECARIA_USE_CANNED_AGENT`         | `false`                          | Fallback for failed Ollama setup |


## Editing seed content

`backend/apothecaria/content/{ingredients,recipes,customers}.json` is the source of truth.
The seed loader **upserts** by slug — re-running `make seed` after editing a JSON file
updates the existing row. Pydantic schemas (`IngredientSeed`, `RecipeSeed`) validate the
files at load time and produce friendly errors for typos.

## Make targets


| Target              | What                               |
| ------------------- | ---------------------------------- |
| `make dev`          | Run backend + frontend together    |
| `make backend-dev`  | Backend only                       |
| `make frontend-dev` | Frontend only                      |
| `make install`      | `npm install` for the frontend     |
| `make build`        | TypeScript + vite production build |
| `make test`         | Run pytest (backend)               |
| `make lint`         | `ruff check` + `tsc --noEmit`      |
| `make format`       | `ruff format`                      |
| `make type`         | `mypy`                             |
| `make seed`         | Upsert JSON content into SQLite    |
| `make db-reset`     | Delete the sqlite file and re-seed |


## Frontend

- Vite + TypeScript. The scene is plain DOM + CSS — no Three.js, no WebGL.
- Vanilla DOM overlays for the four panels (customer dialog, grimoire, brew result, inventory bar).
- Ingredient art lives in `frontend/public/sprites/ingredients/` as PNGs, referenced by the `sprite` field in `ingredients.json`. Jar body color is derived from the slug as a fallback.
- `make dev` starts both processes; backend is `[api]`-prefixed, frontend `[web]`-prefixed.
- `make build` produces a static bundle in `frontend/dist/`.
- `make install` runs `npm install` inside `frontend/`. Run it once after cloning.

### Adding a new ingredient

1. Drop a PNG into `frontend/public/sprites/ingredients/` (or reuse an existing one).
2. Add an entry to `backend/apothecaria/content/ingredients.json` with `slug`, `name`, `lore`, and `sprite` (filename only).
3. Run `make seed` (upsert).
4. Refresh the browser. A new jar appears on the shelf with that sprite; the jar body color is derived from the slug.


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyStock is a full-stack LEGO inventory management system. Backend: Django + DRF. Frontend: React + Vite. Auth: Google OAuth + JWT.

## Development Commands

### Option A: Docker (preferred)
```bash
docker compose up --build                                        # Start all services
docker compose exec backend python manage.py migrate             # Run migrations
docker compose exec backend python manage.py createsuperuser     # Create admin user
docker compose exec backend python manage.py seed_locations      # Seed default locations
```

### Option B: Manual
Requires **pyenv** (Python) and **nvm** (Node). Both are pinned via `.python-version` (3.11) and `.nvmrc` (20) respectively.

```bash
# Backend
pyenv install 3.11    # one-time; skip if already installed
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend (separate terminal)
cd frontend && nvm use && npm install && npm run dev
```

If `brew upgrade` breaks the environment, rebuild with:
```bash
# Python / backend
rm -rf venv && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# Node / frontend
cd frontend && rm -rf node_modules package-lock.json && npm install
```

### Frontend scripts
```bash
cd frontend
npm run dev      # Vite dev server (localhost:5173)
npm run build    # Production build
npm run lint     # ESLint
npm run preview  # Preview production build
```

### Management commands
```bash
python manage.py clear_all_data [--confirm]   # Clear all inventory data
python manage.py delete_zero_stock_items       # Remove zero-stock items
```

### Port cleanup
```bash
lsof -ti:8000 | xargs kill -9   # Kill backend
lsof -ti:5173 | xargs kill -9   # Kill frontend
```

## Architecture

### Backend (`backend/` + `inventory/`)
- `backend/settings.py` — dev config (SQLite, permissive CORS)
- `backend/settings_production.py` — prod config (PostgreSQL, strict security)
- `inventory/models.py` — all data models
- `inventory/views.py` — DRF ViewSets (all filter by `request.user`)
- `inventory/serializers.py` — DRF serializers
- `inventory/auth_views.py` — Google OAuth token exchange, JWT issuance
- `inventory/scraper.py` — fetches LEGO product info from Brickset/LEGO.com on item creation

### Frontend (`frontend/src/`)
- `api.js` — centralized fetch client; injects JWT from localStorage, auto-logouts on 401
- `AuthContext.jsx` — auth state, token storage, user profile
- `App.jsx` — main UI with all sections (item lookup, receive/ship, inventory, journal, locations)

### Data Models

| Model | Scope | Notes |
|---|---|---|
| `Item` | Global (shared) | LEGO set, unique by `item_id` |
| `Location` | Per-user | Unique `(user, name)` |
| `StockTransaction` | Per-user | RECEIVE or SHIP |
| `Inventory` | Per-user | Denormalized current qty per `(user, item, location)` |
| `TransactionJournal` | Per-user | Audit log; denormalizes item/location names for history preservation after deletion |

### API Routes
All under `/api/`:
- `locations/`, `items/`, `transactions/`, `inventory/`, `journal/` — standard router ViewSets
- `auth/login/` — POST Google ID token → JWT access+refresh
- `auth/refresh/` — POST refresh token → new access token
- `auth/me/` — GET current user profile

### Authentication Flow
1. Frontend shows Google OAuth button (`@react-oauth/google`)
2. Google returns ID token to frontend
3. Frontend POSTs ID token to `/api/auth/login/`
4. Backend verifies with Google, creates/fetches user, returns JWT pair
5. JWT stored in `localStorage`; access token expires in 1h, refresh in 7 days

### Multi-tenancy
All ViewSets filter queryset by `request.user`. Items are the only shared resource across users.

## Environment Variables

**Dev** — create `.env` in project root:
```
DJANGO_SECRET_KEY=...
GOOGLE_OAUTH2_CLIENT_ID=...
GOOGLE_OAUTH2_CLIENT_SECRET=...
```

**Frontend** — `frontend/.env` (or build args):
```
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=...
```

**Production** — `stack.env` (not in git; see `stack.env.example`). Includes all of the above plus `DATABASE_URL`, `POSTGRES_*`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CORS_ALLOWED_ORIGINS`.

> `VITE_*` variables are baked into the frontend at build time — changing them requires rebuilding the frontend image.

## Production Deployment

Uses `docker-compose.prod.yml` with PostgreSQL and Nginx (embedded in frontend container).

```bash
docker compose -f docker-compose.prod.yml up --build
docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate
```

Hosted via Portainer + Cloudflare Tunnels. Frontend at `mystock.trahey.net`, API at `api.mystock.trahey.net`.

## Key Notes

- **No test suite** — testing is manual/staging only.
- **Migrations** — always commit migration files; never commit `db.sqlite3`.
- **Journal denormalization** — `TransactionJournal` stores string copies of item ID, item name, and location name so history is preserved after deletions.
- **Web scraper** — triggers automatically on new item creation; gracefully handles failures.

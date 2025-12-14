# Django Development & Database Workflow

## Database & Migration Best Practices
- Track all migration files (`migrations/*`) in git, except `__pycache__`, never track your *actual* database file (`db.sqlite3`, etc.).
- Ignore all DBs, pyc files, `.env`, media, etc. in `.gitignore` (check it is enforced).
- Never track files in `__pycache__`. Do not keep committed DB backups in the repo.
- Use the latest migrations in the repo to set up/update any environment (dev, CI, production).

## Onboarding - New Developer Setup
1. Clone the repo and install Docker Desktop (or set up a Python environment).
2. Use `docker compose up` to start all services, or manually set up a virtualenv and install requirements.
3. Initialize the database by running migrations with:
   - `docker compose run --rm backend python manage.py migrate`
4. (Optional) Load initial data (seed, createsuperuser, etc.)

## Development Workflow
- After making any model changes:
  - Run `python manage.py makemigrations` (or inside the container).
  - Commit all new migration files.
- Never remove migrations shared on the main branch except to resolve unrecoverable issues in dev only.
- Periodically reset and test by deleting your dev DB and running all migrations from scratch.

## Releasing & Upgrading
- Before a release, test DB initialization:
  - Delete your `db.sqlite3`, ensure `docker compose run --rm backend python manage.py migrate` works from scratch.
- Tag the release only after validating migration chain is healthy.
- When pulling changes:
   - Always run `docker compose run --rm backend python manage.py migrate` to update your schema.

## Switching to PostgreSQL for Production
- Use SQLite for local dev. For production, use PostgreSQL (see `docker-compose.prod.yml`).
- Add `psycopg[binary]` to your requirements for PostgreSQL backend.
- Set environment variables: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DATABASE_URL` as needed.
- To migrate/initialize your prod DB: `docker compose -f docker-compose.prod.yml run --rm backend python manage.py migrate`
- Use volumes for persistent PG data.

## Docker Compose Commands
- Start dev: `docker compose up --build`
- Run Django management: `docker compose run --rm backend python manage.py <cmd>`
- Stop and remove containers: `docker compose down`
- For prod/PG: add `-f docker-compose.prod.yml`

---

For further details, see `README.md` or ask the project maintainer.

# Repository Guidelines

## Agent Workflow Requirements
- Read relevant files before coding.
- Add or update tests when changing backend services, API contracts, or UI behavior.
- Keep changes minimal and simple; touch as little code as possible.
- Commit and push successful changes immediately with small, clear messages.


## Project Structure & Module Organization
- `backend/` hosts the FastAPI service, `alembic/` migrations, `tests/`, and reusable scripts; `backend/app` is the code entry point, `backend/tests` holds pytest suites.
- `frontend/` contains the Vite + React app (`src/components`, `src/pages`, `src/services`) plus `package.json`, build tooling, and static assets; the compiled bundle lands in `frontend/dist` for deployments.
- DevOps artifacts live at the root: `docker-compose.yml`, `kubernetes/` manifests, and `terraform/` subdirectories for AWS/GCP/Azure; documentation lives in `docs/` with supplementary guides (`DEVELOPER_GUIDE.md`, `CONTRIBUTING.md`, `create-prd.md`).

## Build, Test, and Development Commands
- `docker-compose up -d` boots the full stack locally, followed by `docker-compose exec backend alembic upgrade head` to sync the database and `docker-compose exec backend python scripts/create_superadmin.py` to seed an admin.
- `docker-compose down` tears the environment down; rerun `docker-compose logs -f backend` for troubleshooting.
- `cd backend && python -m pytest tests/ -v --cov=app` runs the Python test suite with coverage; use `docker compose exec backend python -m pytest ...` when working inside containers.
- `cd frontend && npm install` then `npm run dev` to serve the SPA on `localhost:3000`; `npm run build` compiles it for production and `npm run preview` checks the production build locally.
- `cd frontend && npm run lint` enforces ESLint/Prettier rules before committing.

## Coding Style & Naming Conventions
- Python code follows PEP 8 with explicit type hints, 100-character max lines, and structured imports; run `black backend/app` and `isort backend/app` before pushing.
- React + TypeScript uses functional components and hooks, `camelCase` for functions/variables, `PascalCase` for components, and colocated hooks/services under `frontend/src`. ESLint (`frontend/package.json` script `lint`) plus Prettier keep formatting consistent.
- Keep API routes and services descriptive (`auth_service.py`, `billing_service.py`), and align frontend route/component names with `src/pages` and `src/components/*` folders to signal feature ownership.

## Testing Guidelines
- Backend tests live under `backend/tests/` with `test_*.py` naming; async helpers rely on `pytest.ini`’s `asyncio_mode = auto`. Aim for ≥80% coverage and rerun `python -m pytest tests/ -v --cov=app` after schema changes.
- Frontend specs use Vitest; name files `*.test.ts` or `*.test.tsx` and execute via `npm test`. Install deps first so Vitest/React tooling can warm up.
- Favor regression tests for billing, tenancy, and RBAC work; update API docs or docstrings when business logic matures.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`); pair the prefix with a concise summary (e.g., `feat: add tenant billing audit log`).
- PRs must include a clear description, linked issues, testing steps, and screenshots for UI changes; ensure CI passes, coverage does not decrease, and at least one maintainer approves before merging.
- Update `README.md`, `DEVELOPER_GUIDE.md`, or linked docs when adding user-facing features or new architecture notes.

## Security & Configuration Tips
- Start from `.env.example` and never commit secrets—store production TLS, Stripe, database, and OAuth keys in a secure vault before deployment.
- Keep tenancy variables (`TENANCY_MODE`, `TENANT_IDENTIFICATION`), Stripe hooks (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`), and Redis/SMTP endpoints aligned between backend env vars and `docker-compose.yml`.
- Use row-level security by default; enable `ENABLE_CSRF_PROTECTION` and rate limits (`RATE_LIMIT_PER_MINUTE`) in staging/production.

# Repository Guidelines

## Project Structure & Module Organization
- `backend/`: FastAPI app in `backend/app`, migrations in `backend/alembic`, tests in `backend/tests`.
- `frontend/`: Vite + React app in `frontend/src` (components, pages, services, hooks).
- `kubernetes/` and `terraform/`: deployment manifests and infra-as-code.

## Architecture Overview
- FastAPI API with tenant context enforced in middleware/services; Alembic manages schema changes.
- React frontend talks to the API; PostgreSQL stores tenant, user, role, and billing data.

## Build, Test, and Development Commands
- `docker-compose up -d`: start the local stack.
- `docker-compose exec backend alembic upgrade head`: run migrations.
- `docker-compose exec backend python scripts/create_superadmin.py`: seed an admin user.
- `cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`: run API without Docker.
- `cd frontend && npm install && npm run dev`: run the Vite dev server; `npm run build` for production.

## Coding Style & Naming Conventions
- Backend: PEP 8, type hints, 100-char max line length; format with `black backend/app` and `isort backend/app`.
- Frontend: ESLint (`npm run lint`), React hooks patterns; format with Prettier via `npm run format`.
- Tests: Python uses `tests/test_*.py`; frontend follows component folder naming in `frontend/src/components/`.

## Testing Guidelines
- Backend: `cd backend && pytest tests/ -v --cov=app` (80%+ coverage required).
- Frontend: `cd frontend && npm test` (Vitest); add tests for new features.

## Agent Workflow Requirements
- Read relevant files before coding.
- Add or update tests when changing backend services, API contracts, or UI behavior.
- Do not commit secrets; use `.env` sourced from `.env.example`.
- Write a checkbox-based plan in `tasks/todo.md`, then ask for user approval before editing.
- Execute tasks in order and mark items complete as you go.
- Add a short change summary to `tasks/todo.md`.
- Append a log of actions to `docs/activity.md`.
- Keep changes minimal and simple; touch as little code as possible.
- Commit and push successful changes immediately with small, clear messages.

## Commit & Pull Request Guidelines
- Conventional Commits required (e.g., `feat: add billing webhook`).
- PRs need a clear description, linked issues, and doc updates when behavior changes.
- CI must pass; at least one maintainer approval required.

## Troubleshooting
- Services not reachable: check `docker-compose ps`, then `docker-compose logs -f backend`.
- DB/Redis issues: run migrations, or reset with `docker-compose down -v` then `docker-compose up -d postgres redis`.

## Security & Configuration Tips
- Copy `.env.example` to `.env` and keep secrets (e.g., Stripe keys) out of git.
- Prefer running the stack via Docker for parity with production services.

## Documentation References
- `README.md` for product overview and quickstart.
- `DEVELOPER_GUIDE.md` for workflow conventions and local setup.
- `CONTRIBUTING.md` for contribution and review expectations.

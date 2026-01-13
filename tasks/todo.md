# Auth UI Flow Plan

- [x] Review current frontend auth pages, services, and routing.
- [x] Add register flow and form validation, plus error handling.
- [x] Add token refresh/logout wiring and update route guards.
- [x] Add minimal UI polish for auth screens and success messaging.
- [ ] Smoke test login/register flows against the API.

## Change Summary
- Added register form, validation, and login messaging in the auth UI.
- Added token storage, refresh, and auth-aware route guard behavior.
- Added basic auth session tests for token expiry handling.

# Auth Register Fix Plan

- [x] Fix register response schema to accept UUID IDs.
- [x] Restart backend and re-test register flow.
- [x] Update activity log with the fix.

# HTTPS + Router Flags Plan

- [x] Add self-signed certs and nginx HTTPS config for local dev.
- [x] Update Docker/Nginx wiring to serve HTTPS.
- [x] Verify frontend loads over HTTPS without mixed-content issues.
- [x] Enable React Router future flags to silence warnings.

## Change Summary
- Added a dev cert generation script and nginx HTTPS configuration.
- Switched the frontend API base URL to HTTPS for local proxying.
- Enabled React Router future flags to silence v7 warnings.

# Vite HMR over HTTPS Plan

- [x] Add Vite config to use WSS HMR behind nginx (client host/port/protocol).
- [x] Update nginx to proxy WebSocket upgrade headers for Vite.
- [x] Restart frontend/nginx and verify HMR connects over WSS.

## Change Summary
- Added Vite config to point HMR to WSS on the nginx HTTPS endpoint.
- Updated nginx to forward WebSocket upgrade headers for Vite HMR.

# Client Groups + Entity Access Plan

- [x] Review existing tenant/user/role models and alembic baseline for integration points.
- [x] Add SQLAlchemy models and exports for client groups, group entities, group memberships, and entity memberships.
- [x] Create Alembic migration with tenant-scoped tables and client-group uniqueness constraint.
- [x] Add or note tests for the client role group constraint (if test infra exists). (No backend tests found.)
- [x] Update docs: append activity log and add change summary to tasks/todo.md.

## Change Summary
- Added client group and entity membership models with tenant-scoped constraints and indexes.
- Added Alembic migration for client groups, memberships, and client-only uniqueness enforcement.
- Noted missing backend test infrastructure for the requested constraint coverage.

# Docs Alignment Plan

- [x] Review current codebase architecture references (FastAPI/React/Postgres) vs docs.
- [x] Update docs/architecture.md to remove Laravel/Blade references and align with FastAPI + React.
- [x] Update docs/requirements.md to align terminology with current tenant/user/role model.
- [x] Update docs/data_model_overview.txt to reflect current tenant/user/role naming and stack.
- [x] Update docs/activity.md with the documentation alignment action.
- [x] Add a brief change summary to tasks/todo.md.

## Change Summary
- Updated architecture docs to reflect the current FastAPI + React structure and folders.
- Aligned data model overview terminology with tenant-scoped roles and client groups.
- Tweaked requirements language to match tenant-scoped role defaults.

# Client Group Constraints Plan

- [x] Review existing RLS policies and role model usage for client membership constraints.
- [x] Add Alembic migration to enable RLS and add policies for new client group tables.
- [x] Tighten client group membership constraint to align with role model (role_id or role slug FK) and migrate data if needed.
- [x] Update models to reflect the tightened constraints.
- [x] Add or note tests for constraint enforcement (if test infra exists). (No backend tests found.)
- [x] Update docs/activity.md and add a brief change summary to tasks/todo.md.
- [x] Commit and push changes with Conventional Commits.

## Change Summary
- Enabled RLS and tenant isolation policies for client group and entity membership tables.
- Added a role slug uniqueness constraint and FK to tighten client group memberships.
- Updated models to align with role-based membership enforcement.

# Seed + Verification Plan

- [x] Review existing seed scripts and docs for role creation patterns.
- [x] Add a small seed helper for the `client` role (if missing) or document SQL verification steps.
- [x] Update docs/activity.md and add a brief change summary to tasks/todo.md.
- [x] Commit and push changes with Conventional Commits.

## Change Summary
- Added a seed helper to ensure the global `client` role exists.
- Logged the role seed helper addition in docs/activity.md.

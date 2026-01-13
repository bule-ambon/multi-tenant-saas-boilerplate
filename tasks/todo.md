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

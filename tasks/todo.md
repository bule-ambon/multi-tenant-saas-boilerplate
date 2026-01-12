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

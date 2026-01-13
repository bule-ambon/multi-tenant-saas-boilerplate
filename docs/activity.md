# Activity Log

- Added register UI flow, token refresh handling, and auth session tests.
- Fixed register response schema to accept UUID IDs.
- Added HTTPS dev setup with self-signed certs and enabled React Router future flags.
- Configured Vite HMR to connect over WSS through nginx.
- Added client group and entity membership models/migration with a client-only uniqueness constraint.
- Aligned architecture and requirements docs with the current FastAPI + React stack.
- Added RLS policies and role constraints for client group memberships.
- Added a helper script to seed the global client role.
- Updated agent workflow to allow routine command execution without asking.
- Ran the client role seed script; alembic upgrade failed due to existing client_groups table.

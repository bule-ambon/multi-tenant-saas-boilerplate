This file is NOT instructions for an AI agent but rather only for Humans developers to read.

# Frontend orientation

## Entry point, routing, and shell
- `main.tsx` renders `App` under `React.StrictMode` and pulls in `index.css` for the shared visual language.
- `App.tsx` wires up `@tanstack/react-query` with light defaults (single retries, no refetch on focus) and a `BrowserRouter` that opts into React Router v7 future flags.
- Routes cover the public landing/`/login`/`/register`, while `/dashboard`, `/billing`, and `/admin` are wrapped inside `PrivateRoute` and the shared `Layout`. That means those views only render once an access token is present or refresh tokens bring the session back; otherwise the user is redirected to `/login`.
- `Layout` supplies the tenant portal shell: a centered navigation bar with links to Dashboard/Billing/Admin plus a logout button that clears localStorage tokens and sends the user back to `/login`. `Outlet` renders the currently selected protected page inside the `main.page-shell` container.

## Auth handshake and helpers
- `services/auth.ts` handles login/register/refresh using `fetch` against `VITE_API_URL` (default `http://localhost:8000`). Tokens and expiry timestamps are stored in `localStorage`.
- `login`/`register` POST to `/api/v1/auth/login` and `/api/v1/auth/register` respectively, throwing on any non-OK response so the form can show the backend `detail`.
- `PrivateRoute` uses `isAuthenticated()` and `refreshTokens()` to keep protected routes from showing until there’s a valid session.
- `authFetch` adds `Authorization: Bearer` headers for authenticated calls and automatically retries once if a 401 occurs after refreshing.
- `LoginPage` and `RegisterPage` are plain forms that call the above services, display inline errors, and, upon successful registration + verification, immediately log in and navigate to `/dashboard`.
- Registration enforces a multi-rule password policy (length, uppercase, lowercase, digit, special character) and only shows the user success messaging if email verification is still pending.

## Home, billing, and admin landing content
- `HomePage` is the public-facing hero: MVP pill, headline, stats grid, benefit highlights, and a checklist-style list of actions. CTA buttons link to `/login` and `/register`.
- `BillingPage` and `AdminPage` are placeholders that describe their intended scopes (“Manage plans, invoices, and payment methods” and “Manage users, roles, and tenant settings”). Their routes inherit the same layout shell as the dashboard.

## Dashboard breakdown (the core of the MVP)
- All dashboard content currently lives in `DashboardPage.tsx` with in-file arrays representing the current view. There is no backend integration yet, so the experience is deterministic.

### Client groups & entities
- Top section is a `section-card` grid displaying:
  * A headline & context copy (“Tax year 2025 · Showing Client Group ‘Coastal Planning’ …”).
  * A decorative “Switch tax year” pill (span-only, no handler yet).
  * Client group cards showing name, status pill (styled with the purple `.pill` class), metadata tags, and a supporting note.
  * An adjacent “Entities in view” list that surfaces entity name, type, data source, and sync status using the same meta spacing.

### Trial Balance grid
- Presents `trialBalanceAccounts`, each row showing:
  * Account name, prior-year balance, monthly columns for Jan→Dec (`MONTHS` constant), and a YTD sum (`priorBalance + monthly sum`).
  * Cells show “No data” when month data is `null`/`undefined`.
  * When the “Include Calculated Values” button (toggles `includeCalculated` state) is active, overlay chips appear inside each cell that has an `overlay` value, and the tie-out difference text below drops to zero.
  * The tie-out paragraph explains the current import run (hard-coded “2025-03”), whether overlay values are displayed, and lists the top two overlay drivers (sorted by absolute amount) using inline currency formatting.

### Intercompany reconciliation
- A list of payer→receiver rows showing directional accounts, variance, status badges, and notes.
- Status badges (`.badge` with `.green` or `.yellow`) are driven by the `statusColor` map, and the variance is formatted as USD.
- Each item includes a “Needs Review” or “Reconciled” state plus supporting text (“Receiver side has no rent entry for May…”).
  * The period pill (“Period: Mar”) is static.

### Roll-up mapping & allocations
- Another section-card lists roll-up mappings between child and parent entities, the linked income/balance sheet accounts, allocation notes, and a pill showing the last published run (e.g., “Roll-up 2025-03 (Published)”).

## Styling & layout cues
- `index.css` defines the overall palette and layout utilities:
  * Global background gradients, inter typography, and shadowed `.section-card` containers with rounded corners.
  * `.app-shell`, `.app-header`, and `.nav-links` keep the tenant shell centered and responsive.
  * Utility classes like `.pill`, `.section-row`, `.button-toggle`, `.table-wrapper`, `.trial-balance-table`, `.overlay-chip`, `.recon-item`, and `.rollup-item` are reused by the dashboard to maintain the card/grid look.
  * Buttons and link styles receive hover/active states that match the purple brand accent.

## What developers should expect going forward
- The dashboard data is static; hooking into the backend will mean replacing the hard-coded arrays with React Query calls (using `authFetch` once actual endpoints exist) and rendering server-controlled metadata. The `includeCalculated` toggle currently just shows overlay chips and zeroes out the tie-out paragraph; data-driven overlays should drive both the chart and textual summaries.
- Navigation (Dashboard/Billing/Admin) and logout already rely on the layout shell, so the focus for new pages is just populating the respective routes inside that wrapper.
- `PrivateRoute` ensures users stay authenticated; any new API requests should use `authFetch` or the token helpers to honor the current session and refresh logic.
- Use `VITE_API_URL` to point to the backend (default `http://localhost:8000`) when wiring the dashboard data, and keep the login/register forms’ error handling in place to surface backend validation failures to users.

# Architecture Documentation

## Project Overview
Passthrough Roll-Up & Reconciliation Platform (MVP) — a multi-tenant CPA web app to:
- Ingest **Trial Balance** data (primarily from **QuickBooks Online**) as **versioned runs**
- Support **manual/pro forma** entities (with derived monthly activity)
- Model **effective-dated ownership + special allocation rules**
- Compute **monthly intercompany reconciliation** using **directional payer → receiver** pairs
- Produce **passthrough roll-ups** as a **calculated overlay layer** (never overwriting base TB)
- Support **parallel work across multiple tax years** and a **year close/carryforward** workflow

## Operating System
- **Ubuntu 24.04 LTS**

---

## Architectural Principles

### Multi-Tenancy
- Data is isolated per **Firm (Tenant)**.
- Every query is scoped by tenant (middleware + model scopes + policies).
- Background jobs validate tenant scope before processing.

### Versioned, Reproducible Financial Data
- Imports and derived runs create **new immutable snapshots**.
- Users can re-run imports/calculations and compare results across runs.
- The UI always resolves:
  - “active base run” for an entity/year
  - “published roll-up run” for a client group/year

### Overlay, Don’t Overwrite
- Base values are stored as immutable snapshots (`tb_snapshots` + `tb_lines`).
- Calculated values (roll-ups) are stored as separate overlay entries (`overlay_entries`).
- UI includes a toggle: **Base only** vs **Base + calculated overlays**.

### Effective Dating Everywhere It Matters
- Agreements, ownership edges, roll-up mappings, and special allocations are effective-dated.
- Ownership graph is computed “as of” each period.

---

## Application Architecture

### Layers
1. **Web UI (React + Vite)**
   - Trial balance grid
   - Reconciliation views
   - Roll-up run dashboards (compute/publish/compare)
   - Agreements editor (ownership + allocations)
   - Calculated toggle

2. **API Layer (FastAPI Routers + Services)**
   - Validates inputs and permissions
   - Creates run records
   - Dispatches jobs
   - Coordinates domain services

3. **Domain Services**
   - Ownership graph builder + cycle detection
   - QBO ingestion service
   - Derived pro forma engine
   - Reconciliation engine
   - Roll-up engine (allocation + overlays)
   - Year close/carryforward engine

4. **Jobs / Queues**
   - QBO import jobs (rate limits + retries/backoff)
   - Derived pro forma jobs
   - Recon computation jobs
   - Roll-up computation jobs

5. **Database**
   - Tenant-scoped reference data (entities, accounts, mappings)
   - Versioned run records
   - Immutable snapshots
   - Overlay entries
   - Audit events

---

## Directory Structure (Current)
```txt
backend/
  app/
    api/
    core/
    middleware/
    models/
  alembic/
    versions/
  scripts/

frontend/
  src/
    components/
    pages/
    services/
    hooks/
```

---

## Domain Modules

### Tenancy & Access Control
**Goal:** Firm isolation, roles, auditability.
- Roles (suggested): Admin / Manager / Staff / Read-only
- Audit log records all changes affecting:
  - mappings, agreements, special allocations
  - reconciliation status/notes
  - published roll-up outputs
  - any “active run” pointer changes

---

### Client Groups (Engagements / Portfolio Views)
**Goal:** Group entities into overlapping engagement contexts.
- A Client Group can include many entities.
- Entities may belong to multiple client groups.

---

### Entities & Data Source Types
**Goal:** Entities can be QBO-connected, manual/pro forma, or owner nodes.
- Source types:
  - `QBO_CONNECTED`
  - `MANUAL_PROFORMA`
- Individuals can be modeled as entities when needed for ownership networks.

---

### Agreements & Ownership Graph
**Goal:** Build ownership network “as of” each period to support allocations + visualization.
- Agreements are effective-dated.
- Rules:
  - allocation totals must sum to ~100% within tolerance
  - cycles in ownership graph block publishing roll-ups

---

### Financial Storage Model (Base + Overlay)
**Goal:** Support trial balance grid (prior ending + monthly activity), provenance, and overlays.
- Base snapshot types:
  - `PRIOR_ENDING` (12/31 prior year)
  - `MONTH_ACTIVITY` (Jan–Dec activity)
- Provenance:
  - `QBO_IMPORTED`
  - `MANUAL_ENTRY`
  - `DERIVED_PROFORMA`
- Calculated layer:
  - `ROLLUP_OVERLAY` entries, tied to a roll-up run (toggleable)

---

### QBO Ingestion
**Goal:** Versioned import runs with visible status.
- Each import creates an `import_run` record.
- The job writes **new** snapshots + lines tied to that run.
- Jobs handle:
  - rate limiting
  - retries/backoff
  - status updates and error capture

---

### Derived Pro Forma (Manual Entities)
**Goal:** Allow MANUAL_PROFORMA entities to have a complete TB shape.
- User enters manual prior-ending balances.
- A derived run produces monthly activity snapshots based on system rules.

---

### Intercompany Reconciliation (Directional Payer → Receiver)
**Goal:** Compute monthly variances and track resolution workflow.
- Pair definition:
  - payer entity + payer account
  - receiver entity + receiver account
- Results store:
  - payer amount, receiver amount, variance
  - status + notes
- Calculations use **Base TB monthly activity** (not overlays).

---

### Roll-Ups & Passthrough Allocations
**Goal:** Compute passthrough income allocations and write overlays into parent accounts.
Roll-up engine steps:
1. Build ownership graph as-of each period (effective agreements)
2. Validate totals + detect cycles (block publish)
3. Compute passthrough income amounts from base layer
4. Apply special allocations first (most specific wins)
5. Apply default pro-rata allocations to remaining amounts
6. Write overlays tied to the roll-up run:
   - Parent P&L passthrough account
   - Parent BS “Investment in Child” account

Publishing:
- Many roll-up runs can exist per year; one can be marked **published** (active for UI).

---

### Year Close & Carryforward
**Goal:** Support parallel-year work + formal close later.
- Carryforward: prior year ending becomes next year opening.
- Close: income statement closed into retained earnings/equity accounts (configurable).
- System records:
  - close rules applied
  - source runs/snapshots used
  - generated next-year opening snapshot

---

## Database Schema (Reference)

> This is a **starter reference** (logical + example DDL). Implement via Laravel migrations and adapt names as needed.

### Core Tenancy + Security
```sql
CREATE TABLE firms (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  firm_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (firm_id),
  FOREIGN KEY (firm_id) REFERENCES firms(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE audit_events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  firm_id BIGINT NOT NULL,
  user_id BIGINT NULL,
  action VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id BIGINT NULL,
  payload_json JSON NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (firm_id),
  INDEX (user_id),
  FOREIGN KEY (firm_id) REFERENCES firms(id),
  FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Engagement Context
```sql
CREATE TABLE client_groups (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  firm_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  notes TEXT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (firm_id),
  FOREIGN KEY (firm_id) REFERENCES firms(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE client_group_entities (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  client_group_id BIGINT NOT NULL,
  entity_id BIGINT NOT NULL,
  start_date DATE NULL,
  end_date DATE NULL,
  tags_json JSON NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  UNIQUE KEY uq_cg_entity (client_group_id, entity_id),
  FOREIGN KEY (client_group_id) REFERENCES client_groups(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Entities + QBO Connections
```sql
CREATE TABLE entities (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  firm_id BIGINT NOT NULL,
  name VARCHAR(255) NOT NULL,
  entity_type VARCHAR(50) NOT NULL,
  tax_classification VARCHAR(50) NULL,
  source_type VARCHAR(50) NOT NULL, -- QBO_CONNECTED | MANUAL_PROFORMA
  status VARCHAR(50) NOT NULL DEFAULT 'active',
  notes TEXT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (firm_id),
  FOREIGN KEY (firm_id) REFERENCES firms(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE qbo_connections (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_id BIGINT NOT NULL,
  realm_id VARCHAR(64) NOT NULL,
  refresh_token_encrypted TEXT NOT NULL,
  last_synced_at TIMESTAMP NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  UNIQUE KEY uq_entity (entity_id),
  FOREIGN KEY (entity_id) REFERENCES entities(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Accounts + Base TB Snapshots
```sql
CREATE TABLE accounts (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_id BIGINT NOT NULL,
  external_account_id VARCHAR(64) NULL, -- QBO account id or null for manual
  name VARCHAR(255) NOT NULL,
  account_type VARCHAR(50) NULL,
  active TINYINT(1) NOT NULL DEFAULT 1,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (entity_id),
  FOREIGN KEY (entity_id) REFERENCES entities(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE import_runs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_id BIGINT NOT NULL,
  tax_year INT NOT NULL,
  through_period_end_date DATE NOT NULL,
  status VARCHAR(30) NOT NULL, -- queued|running|success|failed
  started_at TIMESTAMP NULL,
  finished_at TIMESTAMP NULL,
  triggered_by_user_id BIGINT NULL,
  error_text TEXT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (entity_id, tax_year),
  FOREIGN KEY (entity_id) REFERENCES entities(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tb_snapshots (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_id BIGINT NOT NULL,
  tax_year INT NOT NULL,
  period_end_date DATE NOT NULL,
  snapshot_type VARCHAR(30) NOT NULL, -- PRIOR_ENDING | MONTH_ACTIVITY
  source VARCHAR(30) NOT NULL,        -- QBO_IMPORTED | MANUAL_ENTRY | DERIVED_PROFORMA
  run_type VARCHAR(30) NOT NULL,      -- IMPORT | DERIVED
  run_id BIGINT NOT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  UNIQUE KEY uq_snapshot (entity_id, tax_year, period_end_date, snapshot_type, run_type, run_id),
  INDEX (entity_id, tax_year, period_end_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE tb_lines (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  snapshot_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  amount DECIMAL(18,2) NOT NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (snapshot_id),
  INDEX (account_id),
  FOREIGN KEY (snapshot_id) REFERENCES tb_snapshots(id),
  FOREIGN KEY (account_id) REFERENCES accounts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Roll-Up Runs + Overlays
```sql
CREATE TABLE rollup_runs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  client_group_id BIGINT NOT NULL,
  tax_year INT NOT NULL,
  through_period_end_date DATE NOT NULL,
  status VARCHAR(30) NOT NULL, -- draft|computed|published|failed
  inputs_json JSON NULL,
  created_by BIGINT NULL,
  published_at TIMESTAMP NULL,
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (client_group_id, tax_year),
  FOREIGN KEY (client_group_id) REFERENCES client_groups(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE overlay_entries (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  entity_id BIGINT NOT NULL,
  tax_year INT NOT NULL,
  period_end_date DATE NOT NULL,
  account_id BIGINT NOT NULL,
  amount DECIMAL(18,2) NOT NULL,
  source_run_type VARCHAR(30) NOT NULL, -- ROLLUP
  source_run_id BIGINT NOT NULL,        -- rollup_runs.id
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (entity_id, tax_year, period_end_date),
  INDEX (source_run_type, source_run_id),
  FOREIGN KEY (entity_id) REFERENCES entities(id),
  FOREIGN KEY (account_id) REFERENCES accounts(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### Intercompany Reconciliation
```sql
CREATE TABLE recon_pairs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  client_group_id BIGINT NOT NULL,
  payer_entity_id BIGINT NOT NULL,
  payer_account_id BIGINT NOT NULL,
  receiver_entity_id BIGINT NOT NULL,
  receiver_account_id BIGINT NOT NULL,
  tolerance_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  sign_rule VARCHAR(30) NOT NULL DEFAULT 'as_is', -- as_is|flip_receiver|flip_payer
  created_at TIMESTAMP NULL,
  updated_at TIMESTAMP NULL,
  INDEX (client_group_id),
  FOREIGN KEY (client_group_id) REFERENCES client_groups(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE recon_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  recon_pair_id BIGINT NOT NULL,
  tax_year INT NOT NULL,
  period_end_date DATE NOT NULL,
  payer_amount DECIMAL(18,2) NOT NULL,
  receiver_amount DECIMAL(18,2) NOT NULL,
  variance DECIMAL(18,2) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'open', -- open|partial|cleared
  updated_by BIGINT NULL,
  updated_at TIMESTAMP NULL,
  created_at TIMESTAMP NULL,
  UNIQUE KEY uq_recon (recon_pair_id, tax_year, period_end_date),
  FOREIGN KEY (recon_pair_id) REFERENCES recon_pairs(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE recon_notes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  recon_result_id BIGINT NOT NULL,
  note TEXT NOT NULL,
  created_by BIGINT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (recon_result_id),
  FOREIGN KEY (recon_result_id) REFERENCES recon_results(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## Integration Strategy

### Trial Balance Grid (Shape + Provenance)
- For each Entity + Tax Year, UI displays:
  - Prior-year ending balance (12/31 prior year)
  - Jan–Dec monthly activity
- Missing months display explicitly as **No data** unless “treat missing as zero” is enabled.
- Provenance is tracked per snapshot/run and per overlay run.

### Overlay Toggle (Base vs Calculated)
- Base values come from `tb_snapshots`/`tb_lines`.
- Calculated values come from `overlay_entries` for the selected published run.
- UI toggle changes whether overlay values are added into displayed totals.

### Ownership Graph + Cycle Detection
- Ownership edges are effective-dated.
- Roll-up publish requires:
  - totals ≈ 100%
  - no cycles detected

### QBO Import Jobs
- Import runs are queued jobs.
- Store run status + errors for user visibility.
- Use retry/backoff on rate limiting.

---

## Development Environment Setup (Laravel-friendly)

### Queue Worker (Supervisor example)
```ini
[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /var/www/app/artisan queue:work --sleep=3 --tries=3 --timeout=120
autostart=true
autorestart=true
numprocs=1
redirect_stderr=true
stdout_logfile=/var/www/app/storage/logs/worker.log
```

### Scheduler (Cron)
```bash
* * * * * cd /var/www/app && php artisan schedule:run >> /dev/null 2>&1
```

---

## Security Considerations

### Application Security
- Enforce tenant scope in:
  - middleware/policies
  - model global scopes
- Validate + sanitize inputs at request boundaries.
- Use CSRF protection and secure session cookies.

### Token Security (QBO)
- Store refresh tokens encrypted at rest.
- Restrict access to connection records by firm.

### Auditability
- Create audit events for:
  - agreement/mapping changes
  - roll-up publish actions
  - recon status changes
  - active run pointer updates

---

## Best Practices

### Runs + “Active” Pointers
Create a deterministic pointer table (or equivalent) so the UI doesn’t guess:
- `entity_year_state(entity_id, tax_year, active_import_run_id, active_proforma_run_id, active_published_rollup_run_id)`

### Explainability for Calculations
Optional but recommended:
- store drilldown rows per roll-up run (who got what, why, from what rule)

### Performance
- Store normalized lines; pivot at read time.
- Index by:
  - entity_id + tax_year + period_end_date
  - run identifiers
  - client_group_id + tax_year for dashboards

---

## Testing Checklist
- [ ] Tenant isolation: cannot read/write across firms
- [ ] Import run writes new snapshots without overwriting old ones
- [ ] TB grid math: prior ending + sum(month activity) = ending
- [ ] Missing month displays “No data” unless toggled to zero
- [ ] Overlay toggle changes results as expected
- [ ] Ownership cycle detection blocks roll-up publishing
- [ ] Allocation totals near 100% within tolerance
- [ ] Recon variance computed correctly (payer/receiver + sign rules)
- [ ] Roll-up overlays tie back to run and support drilldown
- [ ] Year close produces correct next-year opening snapshot

---

## Documentation References
- `requirements.md`
- `data_model_overview.txt`
- `techstack.md`
- Sample format source: `Sample Tech Stack file.md`

# Requirements Document — Passthrough Income Roll-Up & Reconciliation (CPA Web App)

## Project Overview

### Product Name
Passthrough Roll-Up & Reconciliation Platform (working title)

### Version
1.0.0 (MVP)

### Purpose
Enable a CPA firm to ingest trial balance data (primarily from QuickBooks Online), model passthrough ownership across multi-entity networks, reconcile intercompany activity monthly, and produce period-to-date income roll-ups and estimated tax liability outputs—while supporting overlapping “client groups/engagements” that can share entities.

### Target Audience
- CPA firm staff (admins, managers, preparers)
- Client-side bookkeepers (limited access, as needed)
- Clients/owners (read-only dashboards/reports, optional in v1)

---

## Glossary (Key Terms)
- **Firm (Tenant)**: One CPA firm using the system (data isolated per firm).
- **Client Group (Engagement / Portfolio View)**: A selectable set of entities for a specific engagement/reporting view. Entities may belong to multiple client groups.
- **Entity**: A legal/tax entity or individual node in the network (partnership, S-corp, trust, individual, etc.).
- **Period**: A month in a tax year; represented by month-end date.
- **Base TB Layer**: Imported/manual trial balance values (the “tie-out” layer).
- **Calculated Layer**: Overlay values produced by roll-up computations (toggleable).
- **Reconciliation Pair**: Directional payer→receiver intercompany account mapping used for monthly recon.
- **Roll-Up Mapping**: Child→parent mapping defining where passthrough income lands and which parent balance sheet account tracks “investment in child”.

---

## Functional Requirements

### 1. Tenancy, Users, Roles

#### 1.1 Firm (Tenant) Isolation
- **REQ-TEN-001**: System shall isolate all data by Firm (tenant). Cross-tenant data access is prohibited.

#### 1.2 Users & Roles
- **REQ-USER-001**: System shall support users within a firm with role-based permissions (Admin, Manager, Staff, Read-Only).
- **REQ-USER-002**: System shall support client-facing read-only users (optional in v1; may be firm-only for MVP).
- **REQ-USER-003**: System shall audit user actions that modify financial data, mappings, agreements, and reconciliations.

---

### 2. Client Groups, Entities, Tax Years

#### 2.1 Client Groups (Many-to-Many Membership)
- **REQ-GRP-001**: Users shall create Client Groups to represent engagement-specific collections of entities for reporting, reconciliation, and roll-up.
- **REQ-GRP-002**: System shall support many-to-many membership between Client Groups and Entities (an Entity may belong to multiple Client Groups).
- **REQ-GRP-003**: Client Group membership shall allow metadata (start/end dates, tags/notes).

#### 2.2 Entities (Nodes in the Network)
- **REQ-ENT-001**: Users shall create and manage Entities with attributes: name, EIN/identifier (optional), entity type (tax classification), status, and notes.
- **REQ-ENT-002**: System shall support “Individual” as an Entity node type.
- **REQ-ENT-003**: Entities may exist without QuickBooks Online (manual via csv upload using a template).

#### 2.3 Tax Year Model + Parallel-Year Work
- **REQ-YEAR-001**: System shall support multiple tax years per Client Group, viewable and editable in parallel (e.g., work on 2026 while still reviewing 2025).
- **REQ-YEAR-002**: All imported/manual financial snapshots, reconciliations, and roll-up runs shall be scoped to (Client Group, Tax Year, Period).
- **REQ-YEAR-003**: UI shall provide a clear Tax Year selector; all major views reflect selected year.

#### 2.4 Year Close & Carryforward (Rollover)

- **REQ-YEAR-101**: System shall support a “Close Year / Carryforward” workflow per Entity for a given tax year.
- **REQ-YEAR-102**: Rollover shall set the next year’s opening position using the prior year 12/31 ending balances, closing income statement activity into retained earnings/equity per configurable close rules.
- **REQ-YEAR-103**: Rollover shall not copy or reset non-year-scoped configuration (partnership agreements, reconciliation pair definitions, roll-up mappings). These remain effective-dated and continue across years unless explicitly changed.
- **REQ-YEAR-104**: System shall record an auditable “Year Close Record” (source data version used, close rules applied, and resulting opening balances).
- **REQ-YEAR-105**: System shall allow work on the new tax year to begin before the prior year is formally closed (years viewable in parallel).


---

### 3. Data Sources & Ingestion (QBO + Manual)

#### 3.1 Entity Data Source Type
- **REQ-DATA-001**: Each Entity shall have a Data Source Type: `QBO_CONNECTED` or `MANUAL_PROFORMA`.
- **REQ-DATA-002**: Changing an entity’s data source type shall not delete historical snapshots.

#### 3.2 QuickBooks Online Integration (QBO_CONNECTED)
- **REQ-QBO-001**: System shall support connecting an Entity to QBO via OAuth and store refresh tokens securely.
- **REQ-QBO-002**: System shall ingest trial balance data sufficient to populate:
  - prior-year ending balances (e.g., 12/31/2024)
  - monthly activity (Jan–Dec) for the selected year
- **REQ-QBO-003**: Imports shall be versioned (“Import Runs”) and reproducible.
- **REQ-QBO-004**: System shall handle QBO API rate limits with retries/backoff and user-visible import status.

#### 3.3 Pro Forma Entities (MANUAL_PROFORMA)

- **REQ-PRO-001**: A Pro Forma entity represents “what QBO would report if the entity had QBO and were fully reconciled with the network.”
- **REQ-PRO-002**: Pro Forma TB shall consist of:
  - a **manual** 12/31 prior-year ending balance (seeded from tax returns/K-1s; documented assumptions allowed), and
  - **derived** Jan–Dec monthly activity computed as the implied counter-entries to other entities’ QBO activity per configured intercompany pairing/mapping conventions.
- **REQ-PRO-003**: Pro Forma monthly activity shall be generated via versioned, reproducible “Derived Pro Forma Runs” with per-value provenance and audit trail.
- **REQ-PRO-004**: Pro Forma monthly activity shall be treated as part of the **Base TB layer** for that entity (i.e., it is the entity’s “source-of-truth TB” in lieu of QBO), distinct from roll-up calculated overlays.

---

### 4. Partnership Agreements (Ownership & Allocations)

#### 4.1 Partnership Agreement Records (Effective-Dated)
- **REQ-AGR-001**: System shall store one or more Partnership Agreements per Entity (effective-dated).
- **REQ-AGR-002**: Each agreement shall include:
  - As-Of Date (and optional End Date)
  - Entity tax filing classification (Individual, SMLLC, Partnership, S-Corp, C-Corp, Trust, etc.), which may change over time via new agreement records
  - Owner list (owners may be Individuals or Entities)

#### 4.2 Ownership + Allocation Fields
- **REQ-AGR-101**: For each owner entry, system shall store:
  - Ownership % (capital/equity)
  - Income Allocation % (profit allocation)
- **REQ-AGR-102**: If Income Allocation % is not specified, default Income Allocation % = Ownership %.
- **REQ-AGR-103**: System shall validate allocation totals per agreement (e.g., income allocations total 100%, within rounding tolerance).
- **REQ-AGR-104**: Agreements may be saved as Draft, but roll-up runs may not be published using invalid allocation totals.

#### 4.3 Ownership Graph
- **REQ-OWN-001**: System shall construct an ownership graph “as-of” a selected period using the effective agreement for each entity at that date.
- **REQ-OWN-002**: System shall detect cycles in ownership (and block publish until resolved).

---

### 5. Financials Model & Trial Balance Grid

#### 5.1 Trial Balance Grid Shape
- **REQ-FIN-001**: For each Entity and Tax Year, system shall display a financials table where:
  - Column A: Account
  - Column B: Prior-year ending balance (TB format) as of 12/31 prior year
  - Columns C–N: Jan–Dec monthly activity for the current year
- **REQ-FIN-002**: The YTD ending balance per account shall equal:
  `Prior-Year Ending Balance + Σ(Monthly Activity Jan..Dec)`
- **REQ-FIN-003**: The UI may show totals (row/column) and an optional computed YTD column.

#### 5.2 Missing Period Data
- **REQ-FIN-101**: Missing months shall be explicitly represented as “No data” (not assumed zero) unless the user applies an explicit “treat missing as zero” option.

#### 5.3 Value Provenance (Base vs Calculated)
- **REQ-FIN-201**: System shall store values with provenance:
  - Source Type: `QBO_IMPORTED` | `MANUAL` | `CALCULATED`
  - Source Run ID (import run / roll-up run)
  - Timestamp and user/system actor
- **REQ-FIN-202**: System shall maintain a two-layer model:
  - Base TB layer (QBO_IMPORTED + MANUAL)
  - Calculated layer (CALCULATED overlays)
- **REQ-FIN-203**: Calculated values shall never overwrite base values; they must be stored as overlays.

#### 5.4 Calculated Toggle + QBO Tie-Out
- **REQ-FIN-301**: UI shall provide a toggle: “Include Calculated Values (On/Off)”.
- **REQ-FIN-302**: When Calculated = Off, displayed totals shall match the corresponding QBO YTD Trial Balance (for the same entity/year/as-of) within rounding tolerance.
- **REQ-FIN-303**: If tie-out fails, UI shall show the difference and top contributing accounts, plus which import run is active.
- **REQ-FIN-304**: When Calculated = On, UI shall visually mark overlay-affected cells and support drilldown to the generating roll-up run.

---

### 6. Intercompany Reconciliation (Directional Payer → Receiver)

#### 6.1 Reconciliation Pair Definitions
- **REQ-RECON-001**: Users shall define intercompany reconciliation pairs within a Client Group.
- **REQ-RECON-002**: Each pair shall be directional: Payer Entity → Receiver Entity.
- **REQ-RECON-003**: Each pair shall reference dedicated accounts on both sides (payer-side and receiver-side) used to track intercompany items.
- **REQ-RECON-004**: Pairs shall support a Pair Type (e.g., Distributions, Guaranteed Payments, Principal, Rent, Mgmt Fees, Intercompany Loan, Other) and sign/matching rules.

#### 6.2 Conventions & Readiness
- **REQ-RECON-101**: System shall provide guidance that QBO account setup must follow an intercompany pairing convention (dedicated accounts).
- **REQ-RECON-102**: System shall provide a “readiness check” per pair indicating whether required accounts exist and have activity.

#### 6.3 Monthly Reconciliation Computation
- **REQ-RECON-201**: For each period, system shall compute payer-side vs receiver-side activity variance per pair using the TB monthly activity columns.
- **REQ-RECON-202**: System shall flag unreconciled pairs when variance exceeds configurable thresholds.
- **REQ-RECON-203**: System shall flag “missing counterpart” patterns (activity present on one side but not the other).
- **REQ-RECON-204**: Users shall assign a status and notes per pair per period (Reconciled / Needs Review / Explained).

---

### 7. Roll-Up Mappings & Passthrough Income Calculations

#### 7.1 Roll-Up Mappings (Not Reconciliation)
- **REQ-ROLLMAP-001**: Users shall define roll-up mappings within a Client Group for each Child→Parent relationship where the parent is an owner entity.
- **REQ-ROLLMAP-002**: Each mapping shall identify:
  1) Parent P&L account where child passthrough income will be reported
  2) Parent balance sheet account tracking “Investment in Child”
- **REQ-ROLLMAP-003**: Roll-up mappings may be effective-dated.

#### 7.2 Allocation Rules (Default Pro-Rata + Special Overrides)
- **REQ-ALLOC-001**: Default passthrough income allocation shall use the effective Partnership Agreement’s Income Allocation % (pro-rata).
- **REQ-ALLOC-101**: System shall support Special Allocation Rules that override the default pro-rata allocation when present.
- **REQ-ALLOC-102**: Special allocation rules shall be effective-dated and may apply at:
  - entity-wide scope for a period range, and/or
  - account/category scope (period + account/category)
- **REQ-ALLOC-103**: Allocation precedence:
  1) special allocations (most specific wins)
  2) default pro-rata for remaining amounts
- **REQ-ALLOC-104**: System shall validate total allocated amount equals total income allocated per scope (within rounding tolerance); over-allocation blocks publish.

#### 7.3 Roll-Up Runs (Versioned, Auditable)
- **REQ-ROLL-001**: Users shall create a Roll-Up Run for a Client Group + Tax Year + through-period.
- **REQ-ROLL-002**: A Roll-Up Run shall compute passthrough income allocations and produce CALCULATED overlay entries (toggleable).
- **REQ-ROLL-003**: System shall maintain an audit trail per run: inputs (import versions, agreements as-of), rules applied, and outputs.
- **REQ-ROLL-004**: Users shall be able to publish a roll-up run and retain prior published runs for comparison.

---

### 8. Dashboards & Visualization

#### 8.1 Client Group Dashboard
- **REQ-DASH-001**

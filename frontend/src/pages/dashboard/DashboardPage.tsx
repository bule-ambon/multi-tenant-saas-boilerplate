import { useMemo, useState } from 'react'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const clientGroups = [
  {
    name: 'Coastal Planning Group',
    taxYear: '2025',
    status: 'Active',
    tags: ['Close runway: 2 weeks', 'Includes 4 entities'],
    note: 'Reconciliation work in progress—awaiting final rent pairs.',
  },
  {
    name: 'Summerset Holdings Engagement',
    taxYear: '2025',
    status: 'Review',
    tags: ['Special allocations', 'Pending carryforward'],
    note: 'Income allocation drafts have been saved but not published.',
  },
]

const entitySnapshot = [
  { name: 'Coastal Holdings LP', type: 'Partnership', dataSource: 'QBO_CONNECTED', status: 'Synced 3/18' },
  { name: 'Summerset LLC', type: 'S-Corp', dataSource: 'MANUAL_PROFORMA', status: 'Derived 3/16' },
  { name: 'North Harbor Trust', type: 'Trust', dataSource: 'QBO_CONNECTED', status: 'Synced 3/17' },
]

type TrialBalanceAccount = {
  account: string
  priorBalance: number
  months: Record<string, number | null>
  overlay: Record<string, number>
}

const trialBalanceAccounts: TrialBalanceAccount[] = [
  {
    account: 'Revenue – Consulting',
    priorBalance: 420000,
    months: {
      Jan: 36000,
      Feb: 38000,
      Mar: 42000,
      Apr: 44000,
      May: 0,
      Jun: 18000,
      Jul: 22000,
      Aug: null,
      Sep: 32000,
      Oct: 28000,
      Nov: 31000,
      Dec: 0,
    },
    overlay: { Mar: 1500, Jun: 2200, Sep: -800 },
  },
  {
    account: 'COGS – Operations',
    priorBalance: -185000,
    months: {
      Jan: -12000,
      Feb: -14000,
      Mar: -13000,
      Apr: -16000,
      May: null,
      Jun: -9800,
      Jul: -11200,
      Aug: -9000,
      Sep: -11500,
      Oct: -12700,
      Nov: -11900,
      Dec: null,
    },
    overlay: { Apr: -600, Aug: -900 },
  },
]

const reconciliationPairs = [
  {
    payer: 'Coastal Holdings LLP',
    payerAccount: '7700 – Intercompany Distributions',
    receiver: 'Summerset LLC',
    receiverAccount: '1510 – Due To Affiliates',
    type: 'Distributions',
    variance: -4200,
    status: 'Needs Review',
    notes: 'Receiver side has no rent entry for May, needs match.',
  },
  {
    payer: 'North Harbor Trust',
    payerAccount: '7705 – Guaranteed Payments',
    receiver: 'Coastal Holdings LLP',
    receiverAccount: '1515 – Due From Affiliates',
    type: 'Guaranteed Payments',
    variance: -320,
    status: 'Reconciled',
    notes: 'Variance within threshold for Apr.',
  },
]

const rollups = [
  {
    child: 'Summerset LLC',
    parent: 'North Harbor Trust',
    incomeAccount: 'Income → Passthrough Income – Services',
    investmentAccount: 'Assets → Investment in Summerset',
    allocation: 'Default pro-rata (Income Allocation %)',
    lastRun: 'Roll-up 2025-03 (Published)',
  },
  {
    child: 'Coastal Holdings LLP',
    parent: 'North Harbor Trust',
    incomeAccount: 'Income → Passthrough Income – Investment',
    investmentAccount: 'Assets → Investment in Coastal',
    allocation: 'Special override: 40% fixed for Q2–Q4',
    lastRun: 'Roll-up 2025-01 (Published)',
  },
]

const formatCurrency = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value)

const DashboardPage = () => {
  const [includeCalculated, setIncludeCalculated] = useState(false)

  const overlaySummaries = useMemo(
    () =>
      trialBalanceAccounts.flatMap((account) =>
        Object.entries(account.overlay).map(([month, amount]) => ({
          account: account.account,
          month,
          amount,
        })),
      ),
    [],
  )

  const topOverlayDrivers = overlaySummaries
    .slice()
    .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
    .slice(0, 2)

  const overlayTotal = overlaySummaries.reduce((sum, entry) => sum + entry.amount, 0)

  const tieOutDifference = includeCalculated ? 0 : overlayTotal

  const renderMonthCell = (account: TrialBalanceAccount, month: string) => {
    const baseValue = account.months[month as keyof typeof account.months]
    const overlayValue = account.overlay[month as keyof typeof account.overlay]
    const hasOverlay = includeCalculated && overlayValue !== undefined
    return (
      <td>
        {baseValue === null || baseValue === undefined ? (
          <span style={{ opacity: 0.8, color: '#475569' }}>No data</span>
        ) : (
          formatCurrency(baseValue)
        )}
        {hasOverlay ? (
          <div className="overlay-chip" aria-label={`Calculated overlay ${formatCurrency(overlayValue ?? 0)}`}>
            Overlay {formatCurrency(overlayValue!)}
          </div>
        ) : null}
      </td>
    )
  }

  const getYtd = (account: TrialBalanceAccount) => {
    const monthSum = MONTHS.reduce((sum, month) => {
      const value = account.months[month as keyof typeof account.months]
      return sum + (value ?? 0)
    }, 0)
    return account.priorBalance + monthSum
  }

  const statusColor: Record<string, string> = {
    Reconciled: 'green',
    'Needs Review': 'yellow',
    Explained: 'green',
  }

  return (
    <div className="page-shell">
      <section className="section-card">
          <div className="section-row">
            <div>
              <h2>Client groups & entities</h2>
              <p style={{ margin: 0, color: '#475569' }}>
                Tax year context: <strong>2025</strong> · Showing Client Group “Coastal Planning” and the overlapping
                “Summerset Holdings” engagement.
              </p>
            </div>
            <span className="pill">Switch tax year</span>
          </div>
          <div
            className="grid"
            style={{
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              marginTop: '16px',
            }}
          >
            <div>
              <ul className="client-group-list">
                {clientGroups.map((group) => (
                  <li key={group.name} className="client-group-item">
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <h3>{group.name}</h3>
                      <span className="pill" style={{ background: '#e0f2fe', color: '#0369a1' }}>
                        {group.status}
                      </span>
                    </div>
                    <div className="client-group-meta">
                      <span>Tax year: {group.taxYear}</span>
                      {group.tags.map((tag) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>
                    <p style={{ margin: 0, color: '#475569' }}>{group.note}</p>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 style={{ marginTop: 0 }}>Entities in view</h3>
              <ul style={{ padding: 0, margin: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {entitySnapshot.map((entity) => (
                  <li
                    key={entity.name}
                    style={{
                      borderRadius: '12px',
                      padding: '12px',
                      background: '#f8fafc',
                      border: '1px solid rgba(15, 23, 42, 0.05)',
                    }}
                  >
                    <strong>{entity.name}</strong>
                    <div className="client-group-meta">
                      <span>{entity.type}</span>
                      <span>{entity.dataSource}</span>
                      <span>{entity.status}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>
        <section className="section-card">
          <div className="section-row">
            <div>
              <h2>Trial Balance grid</h2>
              <p style={{ margin: 0, color: '#475569' }}>
                Prior-year ending balances plus monthly activity with calculated overlays tracked separately.
              </p>
            </div>
            <button
              type="button"
              className={`button-toggle ${includeCalculated ? 'active' : ''}`}
              onClick={() => setIncludeCalculated((prev) => !prev)}
              aria-pressed={includeCalculated}
            >
              Include Calculated Values: {includeCalculated ? 'On' : 'Off'}
            </button>
          </div>
          <div className="table-wrapper">
            <table className="trial-balance-table">
              <thead>
                <tr>
                  <th>Account</th>
                  <th>Prior year</th>
                  {MONTHS.map((month) => (
                    <th key={month}>{month}</th>
                  ))}
                  <th>YTD (Base)</th>
                </tr>
              </thead>
              <tbody>
                {trialBalanceAccounts.map((account) => (
                  <tr key={account.account}>
                    <td>{account.account}</td>
                    <td>{formatCurrency(account.priorBalance)}</td>
                    {MONTHS.map((month) => renderMonthCell(account, month))}
                    <td>{formatCurrency(getYtd(account))}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ marginTop: '12px', color: '#475569' }}>
            Tie-out difference to QBO YTD (active import run: 2025-03). Calculated overlays {includeCalculated ? 'are' : 'are not'} shown
            here, so difference is {formatCurrency(tieOutDifference)}. Top overlay contributions:{' '}
            {topOverlayDrivers.map((driver) => (
              <span key={`${driver.account}-${driver.month}`}>
                {driver.account} ({driver.month}): {formatCurrency(driver.amount)}
                {driver !== topOverlayDrivers[topOverlayDrivers.length - 1] ? ', ' : ''}
              </span>
            ))}
          </p>
        </section>
        <section className="section-card">
          <div className="section-row">
            <div>
              <h2>Intercompany reconciliation</h2>
              <p style={{ margin: 0, color: '#475569' }}>
                Directional payer→receiver pairs surface unmatched activity thresholds for each period.
              </p>
            </div>
            <span className="pill">Period: Mar</span>
          </div>
          <ul className="recon-list">
            {reconciliationPairs.map((pair) => (
              <li key={pair.payer + pair.receiver} className="recon-item">
                <div>
                  <strong>
                    {pair.payer} → {pair.receiver}
                  </strong>
                  <div className="recon-meta">
                    <span>{pair.payerAccount}</span>
                    <span>{pair.receiverAccount}</span>
                    <span>Type: {pair.type}</span>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div className="recon-status">
                    <span className={`badge ${statusColor[pair.status] ?? 'yellow'}`}>{pair.status}</span>
                    <span>{formatCurrency(pair.variance)}</span>
                  </div>
                  <p style={{ margin: '6px 0 0', fontSize: '0.9rem', color: '#475569' }}>{pair.notes}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
        <section className="section-card">
          <div className="section-row">
            <div>
              <h2>Roll-up mapping & allocations</h2>
              <p style={{ margin: 0, color: '#475569' }}>
                Child→parent mappings use partnership agreements (effective dated) to allocate passthrough income.
              </p>
            </div>
            <span className="pill">Latest published runs</span>
          </div>
          <ul className="rollup-list">
            {rollups.map((item) => (
              <li key={item.child} className="rollup-item">
                <div>
                  <strong>
                    {item.child} → {item.parent}
                  </strong>
                  <div className="rollup-meta">
                    <span>P&L: {item.incomeAccount}</span>
                    <span>BS: {item.investmentAccount}</span>
                    <span>{item.allocation}</span>
                  </div>
                </div>
                <div>
                  <span className="pill" style={{ background: '#fef3c7', color: '#92400e' }}>
                    {item.lastRun}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
    </div>
  )
}

export default DashboardPage

import { Link } from 'react-router-dom'

const stats = [
  { label: 'Tenants supported', value: '12 firms' },
  { label: 'Client groups live', value: '38 portfolios' },
  { label: 'Reconciliation coverage', value: '420 periods' },
  { label: 'Roll-up runs', value: '178 published' },
]

const highlights = [
  {
    title: 'Client group storytelling',
    description:
      'Slice your network by engagement, tax year, or initiative, then share consistent context across dashboards.',
  },
  {
    title: 'Trial balance transparency',
    description:
      'Prior-year balances, monthly TB activity, and calculated overlays stay explicitly versioned so auditors can trace each amount.',
  },
  {
    title: 'Intercompany readiness',
    description:
      'Define directional pairs, alert for missing counterpart activity, and assign status/notes to each period.',
  },
  {
    title: 'Roll-up intelligence',
    description:
      'Roll-up runs apply effective-dated ownership, special allocations, and audit-ready inputs before publishing overlays.',
  },
]

const actions = [
  'Select a client group + tax year to scope all views',
  'Review reconciliation pairs and fix missing counterparts',
  'Publish carryforward-ready roll-up runs with audit trails',
  'Invite read-only client users when dashboards are ready',
]

const HomePage = () => {
  return (
    <main className="page-shell">
      <section className="hero">
        <div className="hero-overview">
          <span className="pill">MVP</span>
          <h1>Passthrough income roll-ups for multi-entity CPA firms</h1>
          <p>
            Ingest trial balance data from QuickBooks, model ownership, and reconcile intercompany activity across
            overlapping engagements—then publish roll-up results alongside provenance-ready dashboards.
          </p>
          <div className="cta-buttons">
            <Link to="/login" className="cta-primary">
              Sign in
            </Link>
            <Link to="/register" className="cta-secondary">
              Request access
            </Link>
          </div>
        </div>
        <div className="stats-grid" aria-live="polite">
          {stats.map((stat) => (
            <div key={stat.label} className="stat-card">
              <strong>{stat.value}</strong>
              <span>{stat.label}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="section-card">
        <h2>Designed for firms with complex passthrough networks</h2>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))' }}>
          {highlights.map((highlight) => (
            <article key={highlight.title} style={{ padding: '14px 16px' }}>
              <h3 style={{ margin: '0 0 6px' }}>{highlight.title}</h3>
              <p style={{ margin: 0, color: '#475569' }}>{highlight.description}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="section-card">
        <h2>Primary actions for this MVP</h2>
        <p>Use the dashboard to keep the team aligned on client groups, trial balances, reconciliations, and roll-ups.</p>
        <ul className="list-seed">
          {actions.map((action) => (
            <li key={action}>
              <span>{action}</span>
            </li>
          ))}
        </ul>
      </section>
    </main>
  )
}

export default HomePage

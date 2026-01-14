import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import { logout } from '../../services/auth'

const Layout = () => {
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <nav>
          <div>
            <strong style={{ fontSize: '1.1rem' }}>Passthrough Intelligence</strong>
            <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>Tenant portal</p>
          </div>
          <div className="nav-links">
            <NavLink to="/dashboard" className={({ isActive }) => (isActive ? 'active' : '')}>
              Dashboard
            </NavLink>
            <NavLink to="/billing" className={({ isActive }) => (isActive ? 'active' : '')}>
              Billing
            </NavLink>
            <NavLink to="/admin" className={({ isActive }) => (isActive ? 'active' : '')}>
              Admin
            </NavLink>
          </div>
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </nav>
      </header>
      <main className="page-shell">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

import { Link, useNavigate, Outlet } from 'react-router-dom'
import { logout } from '../../services/auth'

const Layout = () => {
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div>
      <header>
        <nav>
          <Link to="/dashboard">Dashboard</Link> |{' '}
          <Link to="/billing">Billing</Link> | <Link to="/admin">Admin</Link>
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </nav>
      </header>
      <Outlet />
    </div>
  )
}

export default Layout

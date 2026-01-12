import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { isAuthenticated } from '../../services/auth'

const PrivateRoute = () => {
  const location = useLocation()
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <Outlet />
}

export default PrivateRoute

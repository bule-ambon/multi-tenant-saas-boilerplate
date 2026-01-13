import { useEffect, useState } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { isAuthenticated, refreshTokens } from '../../services/auth'

const PrivateRoute = () => {
  const location = useLocation()
  const [status, setStatus] = useState<'checking' | 'authenticated' | 'unauthenticated'>(
    'checking',
  )

  useEffect(() => {
    let isActive = true
    const checkSession = async () => {
      if (isAuthenticated()) {
        if (isActive) {
          setStatus('authenticated')
        }
        return
      }

      const refreshed = await refreshTokens()
      if (isActive) {
        setStatus(refreshed ? 'authenticated' : 'unauthenticated')
      }
    }

    checkSession()
    return () => {
      isActive = false
    }
  }, [])

  if (status === 'checking') {
    return (
      <main>
        <p>Checking your session...</p>
      </main>
    )
  }

  if (status === 'unauthenticated') {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  return <Outlet />
}

export default PrivateRoute

import { Link } from 'react-router-dom'

const HomePage = () => {
  return (
    <main>
      <h1>Multi-Tenant SaaS Platform</h1>
      <p>Welcome. Sign in to access your dashboard.</p>
      <p>
        <Link to="/login">Go to login</Link>
      </p>
    </main>
  )
}

export default HomePage

import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login, register } from '../../services/auth'

const MIN_PASSWORD_LENGTH = 8

const validatePassword = (password: string) => {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return `Password must be at least ${MIN_PASSWORD_LENGTH} characters`
  }
  if (!/[A-Z]/.test(password)) {
    return 'Password must contain at least one uppercase letter'
  }
  if (!/[a-z]/.test(password)) {
    return 'Password must contain at least one lowercase letter'
  }
  if (!/[0-9]/.test(password)) {
    return 'Password must contain at least one digit'
  }
  if (!/[!@#$%^&*()_+\-[\]{}|;:,.<>?]/.test(password)) {
    return 'Password must contain at least one special character'
  }
  return null
}

const RegisterPage = () => {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    setSuccess(null)

    const passwordError = validatePassword(password)
    if (passwordError) {
      setError(passwordError)
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setIsSubmitting(true)
    try {
      const user = await register({ email, password, full_name: fullName || undefined })
      if (user.is_verified) {
        await login(email, password)
        navigate('/dashboard', { replace: true })
        return
      }
      setSuccess('Account created. Please verify your email before logging in.')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main>
      <h1>Register</h1>
      <p>Create an account to get started.</p>
      <form onSubmit={onSubmit}>
        <div>
          <label htmlFor="fullName">Full name</label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="confirmPassword">Confirm password</label>
          <input
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            required
          />
        </div>
        {error ? <p role="alert">{error}</p> : null}
        {success ? <p role="status">{success}</p> : null}
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </main>
  )
}

export default RegisterPage

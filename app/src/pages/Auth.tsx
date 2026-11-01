import { useEffect, useState } from 'react'

interface User {
  sub: string
  email: string
  name: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')
const apiUrl = (path: string) => `${API_BASE_URL}${path}`

export default function Auth() {
  const [user, setUser] = useState<User | null>(null)
  const [csrfToken, setCsrfToken] = useState<string>('')
  const [loading, setLoading] = useState(true)

  // 1. Check session & fetch CSRF token on page load
  useEffect(() => {
    fetch(apiUrl('/auth/me'), { credentials: 'include' })
      .then((res) => {
        if (!res.ok) throw new Error('Not logged in')
        return res.json()
      })
      .then((data) => {
        setUser(data.user)
        setCsrfToken(data.csrf_token)
      })
      .catch(() => {
        setUser(null)
        setCsrfToken('')
      })
      .finally(() => setLoading(false))
  }, [])

  // 2. Protected POST request with X-CSRF-Token header
  const handleRefreshEmails = async () => {
    const res = await fetch(apiUrl('/emails/refresh'), {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken, // Required by verify_csrf_and_origin
      },
    })

    if (res.ok) {
      const data = await res.json()
      console.log('Refresh started:', data)
    } else {
      console.error('Failed to refresh emails:', res.status)
    }
  }

  // 3. Protected POST logout
  const handleLogout = async () => {
    const res = await fetch(apiUrl('/auth/logout'), {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRF-Token': csrfToken,
      },
    })

    if (res.ok) {
      setUser(null)
      setCsrfToken('')
    }
  }

  if (loading) return <p>Loading...</p>

  return (
    <div style={{ padding: '2rem' }}>
      {!user ? (
        <a href={apiUrl('/auth/login')}>
          <button type="button">Sign in with Google</button>
        </a>
      ) : (
        <div>
          <p>Signed in as <strong>{user.email}</strong></p>
          <button type="button" onClick={handleRefreshEmails}>
            Refresh Emails
          </button>
          <button type="button" onClick={handleLogout} style={{ marginLeft: '1rem' }}>
            Log Out
          </button>
        </div>
      )}
    </div>
  )
}
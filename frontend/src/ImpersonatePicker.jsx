import { useState, useEffect } from 'react'
import { api } from './api'
import { useAuth } from './AuthContext'

function ImpersonatePicker({ onClose }) {
  const { impersonate } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [impersonating, setImpersonating] = useState(false)

  useEffect(() => {
    api.getUsers()
      .then(setUsers)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  const handleSelect = async (userId) => {
    setImpersonating(true)
    try {
      await impersonate(userId)
      onClose()
      // Reload so all data re-fetches as the impersonated user
      window.location.reload()
    } catch (err) {
      setError(err.message)
      setImpersonating(false)
    }
  }

  const filtered = users.filter((u) => {
    const q = search.toLowerCase()
    return (
      u.email.toLowerCase().includes(q) ||
      u.username.toLowerCase().includes(q) ||
      `${u.first_name} ${u.last_name}`.toLowerCase().includes(q)
    )
  })

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 3000,
      }}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        background: '#fff',
        borderRadius: '8px',
        padding: '24px',
        width: '420px',
        maxHeight: '70vh',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.25)',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '1.2em' }}>Impersonate User</h2>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', fontSize: '1.4em', cursor: 'pointer', lineHeight: 1 }}
          >
            ×
          </button>
        </div>

        <input
          type="search"
          placeholder="Search by email or name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          autoFocus
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            fontSize: '0.95em',
          }}
        />

        {error && <p style={{ color: 'red', margin: 0, fontSize: '0.9em' }}>{error}</p>}

        <div style={{ overflowY: 'auto', flex: 1 }}>
          {loading && <p style={{ color: '#888', textAlign: 'center' }}>Loading users…</p>}
          {!loading && filtered.length === 0 && (
            <p style={{ color: '#888', textAlign: 'center' }}>No users found</p>
          )}
          {filtered.map((u) => (
            <button
              key={u.id}
              disabled={impersonating}
              onClick={() => handleSelect(u.id)}
              style={{
                display: 'block',
                width: '100%',
                textAlign: 'left',
                padding: '10px 12px',
                marginBottom: '4px',
                background: '#f9fafb',
                border: '1px solid #e5e7eb',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.9em',
              }}
            >
              <div style={{ fontWeight: 600 }}>{u.email}</div>
              {(u.first_name || u.last_name) && (
                <div style={{ color: '#6b7280', fontSize: '0.85em' }}>
                  {u.first_name} {u.last_name}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ImpersonatePicker

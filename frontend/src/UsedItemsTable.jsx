import { useState } from 'react'
import { api } from './api'

function UsedItemsTable({ usedItems, onRefresh }) {
  const [editingId, setEditingId] = useState(null)
  const [editNotes, setEditNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleShip = async (item) => {
    if (!window.confirm(`Ship unit ${item.used_item_id}?\n\nNotes: ${item.notes || '(none)'}\n\nThis unit will be removed from inventory. The transaction will be saved in the journal.`)) return
    setLoading(true)
    setError('')
    try {
      await api.shipUsedItem(item.id)
      onRefresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (item) => {
    if (!window.confirm(`Delete unit ${item.used_item_id}? This cannot be undone and will NOT create a journal entry.`)) return
    setLoading(true)
    setError('')
    try {
      await api.deleteUsedItem(item.id)
      onRefresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const startEdit = (item) => {
    setEditingId(item.id)
    setEditNotes(item.notes)
    setError('')
  }

  const saveEdit = async (item) => {
    setLoading(true)
    setError('')
    try {
      await api.updateUsedItem(item.id, { notes: editNotes })
      setEditingId(null)
      onRefresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (usedItems.length === 0) {
    return <p style={{ color: '#888', margin: '8px 0' }}>No used units in inventory.</p>
  }

  return (
    <div>
      {error && <p style={{ color: 'red', fontSize: '0.9em' }}>{error}</p>}
      <table className="inventory-table" style={{ marginTop: '8px' }}>
        <thead>
          <tr>
            <th>Unit ID</th>
            <th>Location</th>
            <th>Condition Notes</th>
            <th>Received</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {usedItems.map((item) => (
            <tr key={item.id}>
              <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{item.used_item_id}</td>
              <td>{item.location?.name || <span style={{ color: '#aaa' }}>—</span>}</td>
              <td style={{ maxWidth: '280px' }}>
                {editingId === item.id ? (
                  <textarea
                    value={editNotes}
                    onChange={(e) => setEditNotes(e.target.value)}
                    rows={3}
                    style={{ width: '100%', fontSize: '0.85em', boxSizing: 'border-box' }}
                    autoFocus
                  />
                ) : (
                  <span style={{ whiteSpace: 'pre-wrap', fontSize: '0.9em' }}>
                    {item.notes || <span style={{ color: '#aaa' }}>No notes</span>}
                  </span>
                )}
              </td>
              <td style={{ fontSize: '0.85em', whiteSpace: 'nowrap' }}>
                {new Date(item.received_at).toLocaleDateString()}
              </td>
              <td className="actions-cell" style={{ whiteSpace: 'nowrap' }}>
                {editingId === item.id ? (
                  <>
                    <button
                      onClick={() => saveEdit(item)}
                      disabled={loading}
                      className="btn-link"
                      style={{ color: '#16a34a' }}
                    >
                      Save
                    </button>
                    <span className="separator">|</span>
                    <button
                      onClick={() => setEditingId(null)}
                      className="btn-link"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => startEdit(item)}
                      className="btn-link"
                      disabled={loading}
                    >
                      Edit
                    </button>
                    <span className="separator">|</span>
                    <button
                      onClick={() => handleShip(item)}
                      className="btn-link btn-ship"
                      disabled={loading}
                    >
                      Ship
                    </button>
                    <span className="separator">|</span>
                    <button
                      onClick={() => handleDelete(item)}
                      className="btn-link"
                      style={{ color: '#dc3545' }}
                      disabled={loading}
                    >
                      Delete
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default UsedItemsTable

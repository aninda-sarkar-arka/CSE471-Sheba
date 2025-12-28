import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { getSocket } from '../services/socket'
import ChatComponent from './ChatComponent'

export default function ComplaintPage() {
  const [form, setForm] = useState({ title: '', description: '', provider_unique_id: '', service_request_id: '' })
  const [complaints, setComplaints] = useState([])
  const [message, setMessage] = useState('')
  const [user, setUser] = useState(null)
  const [pastProviders, setPastProviders] = useState([])

  useEffect(() => {
    api.get('/auth/me').then(res => setUser(res.data.user)).catch(e => { })
    loadComplaints()
    loadPastProviders()
    const socket = getSocket()
    socket.on('complaint_update', () => loadComplaints())
    return () => socket.off('complaint_update')
  }, [])





  async function loadPastProviders() {
    try {
      const res = await api.get('/user/past-providers')
      setPastProviders(res.data || [])
    } catch (e) { }
  }



  async function loadComplaints() {
    try {
      const res = await api.get('/complaints')
      setComplaints(res.data || [])
    } catch (e) { }
  }

  async function submit(e) {
    e.preventDefault()
    try {
      const payload = {
        title: form.title,
        description: form.description,
        provider_unique_id: form.provider_unique_id || undefined,
        service_request_id: form.service_request_id || undefined,
      }
      await api.post('/complaints', payload)
      setMessage('✓ Complaint submitted successfully')
      setForm({ title: '', description: '', provider_unique_id: '', service_request_id: '' })
      loadComplaints()
      setTimeout(() => setMessage(''), 3000)
    } catch (err) {
      const m = err?.response?.data?.msg || err?.message || 'Error submitting complaint'
      setMessage('✗ ' + m)
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>

      {/* Header Banner */}
      <div style={{ background: '#FFF0F3', padding: '30px', borderRadius: 16, marginBottom: 24, textAlign: 'center' }}>
        <h1 style={{ color: 'var(--primary)', marginBottom: 8 }}>Help & Support Center</h1>
        <p style={{ color: '#666', fontSize: '1.1rem' }}>We are here to help. Report any issues or share your feedback.</p>
      </div>

      <div className="grid">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>File a Complaint</h2>
          <form onSubmit={submit}>
            <div className="form-row">
              <label>Issue Title</label>
              <input placeholder="e.g. Service not started yet" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
            </div>
            <div className="form-row">
              <label>Description of Issue</label>
              <textarea placeholder="Please describe what happened..." value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} required style={{ minHeight: 120 }} />
            </div>
            <div className="form-row">
              <div style={{ display: 'flex', gap: 10 }}>
                <div style={{ flex: 1 }}>




                  <label>Select Provider (Optional)</label>
                  <select
                    value={form.provider_unique_id}
                    onChange={e => setForm({ ...form, provider_unique_id: e.target.value })}
                  >
                    <option value="">-- Select a Provider --</option>
                    {pastProviders.map(p => (
                      <option key={p.id} value={p.provider_unique_id}>
                        {p.name} ({p.provider_unique_id})
                      </option>
                    ))}






                  </select>
                  {pastProviders.length === 0 && <small className="muted">You haven't hired any providers yet.</small>}
                </div>
                <div style={{ flex: 1 }}>
                  <label>Request ID (Optional)</label>
                  <input type="number" placeholder="123" value={form.service_request_id} onChange={e => setForm({ ...form, service_request_id: e.target.value })} />
                </div>
              </div>
            </div>
            <div className="form-row">
              <button className="btn" type="submit" style={{ width: '100%', padding: 12 }}>Submit Report</button>
              <div style={{ marginTop: 12, textAlign: 'center', color: message.startsWith('✓') ? 'green' : 'red' }}>{message}</div>
            </div>
          </form>
        </div>

        <div className="card">
          <h3 style={{ marginTop: 0 }}>My Support Tickets</h3>
          {complaints.length === 0 && <div className="muted" style={{ padding: 40, textAlign: 'center', background: '#f9fafb', borderRadius: 8 }}>No active complaints or tickets.</div>}

          <div style={{ maxHeight: 600, overflowY: 'auto' }}>
            {complaints.map(c => (
              <div key={c.id} style={{ border: '1px solid #e5e7eb', padding: 16, borderRadius: 8, marginBottom: 16, background: 'white', boxShadow: '0 2px 4px rgba(0,0,0,0.02)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <strong style={{ fontSize: '1.1rem' }}>{c.title}</strong>
                  <span className="badge" style={{
                    background: c.status === 'pending' ? '#FEF3C7' : c.status === 'reviewed' ? '#EFF6FF' : '#D1FAE5',
                    color: c.status === 'pending' ? '#D97706' : c.status === 'reviewed' ? '#2563EB' : '#059669'
                  }}>{c.status.toUpperCase()}</span>
                </div>

                <div className="small muted" style={{ marginBottom: 12 }}>Created: {new Date(c.created_at).toLocaleString()}</div>

                {(c.provider_unique_id || c.service_request_id) && (
                  <div style={{ background: '#f3f4f6', padding: 8, borderRadius: 4, fontSize: '0.9rem', marginBottom: 12 }}>
                    {c.provider_unique_id && <span style={{ marginRight: 12 }}><strong>Provider:</strong> {c.provider_unique_id}</span>}
                    {c.service_request_id && <span><strong>Request #:</strong> {c.service_request_id}</span>}
                  </div>
                )}

                <div style={{ marginBottom: 12 }}>{c.description}</div>

                {c.admin_response && (
                  <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: '#F0F9FF', border: '1px solid #BAE6FD', color: '#0369A1' }}>
                    <strong>Admin Response:</strong> {c.admin_response}
                  </div>
                )}

                {/* Chat */}
                {user && c.status !== 'reviewed' && (
                  <div style={{ marginTop: 16 }}>
                    <ChatComponent complaintId={c.id} currentUser={user} initialStatus={c.status} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

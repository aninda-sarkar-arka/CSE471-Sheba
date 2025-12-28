import React, { useEffect, useState } from 'react'
import api from '../services/api'
import { Link } from 'react-router-dom'
import { getSocket } from '../services/socket'
import ServiceChat from './ServiceChat'

export default function ProviderDashboard() {
  const [requests, setRequests] = useState([])
  const [notifications, setNotifications] = useState([])
  const [message, setMessage] = useState('')
  const [activeTab, setActiveTab] = useState('pending') // pending | active | history
  const [activeChat, setActiveChat] = useState(null) // serviceRequestId
  const [currentUser, setCurrentUser] = useState(null)

  useEffect(() => {
    loadUser()
    loadRequests()
    loadNotifications()

    const socket = getSocket()
    socket.on('connect', () => console.log('Socket connected'))
    socket.on('notification', () => {
      loadNotifications()
      loadRequests()
    })

    return () => {
      socket.off('connect')
      socket.off('notification')
    }
  }, [])

  async function loadUser() {
    try {
      const res = await api.get('/auth/me')
      setCurrentUser(res.data.user)
    } catch (e) { }
  }

  async function loadRequests() {
    try {
      const res = await api.get('/service_requests')
      setRequests(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  async function loadNotifications() {
    try {
      const res = await api.get('/notifications')
      setNotifications(res.data || [])
    } catch (e) { }
  }

  async function act(requestId, action) {
    try {
      await api.post(`/service_requests/${requestId}/${action}`)
      setMessage(`Request ${action}ed`)
      loadRequests()
    } catch (err) {
      setMessage('Error performing action')
    }
  }

  const pendingRequests = requests.filter(r => r.status === 'pending')
  const activeRequests = requests.filter(r => r.status === 'accepted')
  const historyRequests = requests.filter(r => ['completed', 'rejected', 'cancelled'].includes(r.status))

  const selectedRequests = activeTab === 'pending' ? pendingRequests
    : activeTab === 'active' ? activeRequests
      : historyRequests

  return (
    <div className="grid">
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ marginTop: 0, marginBottom: 4 }}>Provider Dashboard</h2>
            {currentUser && currentUser.provider_unique_id && (
              <div style={{
                display: 'inline-block',
                background: '#EFF6FF',
                color: '#1D4ED8',
                padding: '4px 8px',
                borderRadius: 4,
                fontSize: '0.85rem',
                fontWeight: 600,
                border: '1px solid #DBEAFE'
              }}>
                ID: {currentUser.provider_unique_id}
              </div>
            )}
          </div>
          <div style={{ textAlign: 'right' }}>
            <Link to="/profile" className="btn outline" style={{ textDecoration: 'none' }}>Edit Profile</Link>
          </div>
        </div>

        {/* Tabs */}
        <div style={{ display: 'flex', gap: 10, marginBottom: 20, borderBottom: '1px solid #eee', paddingBottom: 10 }}>
          <button className={`btn ${activeTab === 'pending' ? '' : 'secondary'}`} onClick={() => setActiveTab('pending')}>
            Available Jobs ({pendingRequests.length})
          </button>
          <button className={`btn ${activeTab === 'active' ? '' : 'secondary'}`} onClick={() => setActiveTab('active')}>
            Active Jobs ({activeRequests.length})
          </button>
          <button className={`btn ${activeTab === 'history' ? '' : 'secondary'}`} onClick={() => setActiveTab('history')}>
            History
          </button>
        </div>

        {selectedRequests.length === 0 && <p className="muted">No requests in this category.</p>}

        {selectedRequests.map(r => (
          <div key={r.id} style={{ border: '1px solid #eee', padding: 16, marginBottom: 16, borderRadius: 8, background: '#fff' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{r.category} Job</div>
                <div className="small muted">Created: {new Date(r.created_at).toLocaleString()}</div>
              </div>
              <div>
                <span className={`badge ${r.status === 'accepted' ? 'green' : 'yellow'}`}>{r.status}</span>
              </div>
            </div>

            <div style={{ marginTop: 12, marginBottom: 12, color: '#4b5563' }}>{r.description || 'No description provided'}</div>

            {/* Actions based on status */}
            <div className="flex">
              {r.status === 'pending' && (
                <>
                  <button className="btn" onClick={() => act(r.id, 'accept')}>Accept Job</button>
                  <button className="btn secondary" onClick={() => act(r.id, 'reject')}>Ignore</button>
                </>
              )}

              {r.status === 'accepted' && (
                <>
                  <button className="btn" onClick={() => setActiveChat(activeChat === r.id ? null : r.id)}>
                    {activeChat === r.id ? 'Close Chat' : 'Chat with Customer'}
                  </button>
                  <button className="btn outline" onClick={() => act(r.id, 'complete')}>Mark Completed</button>
                </>
              )}

              {r.status === 'completed' && r.rating && (
                <div className="small" style={{ color: 'goldenrod' }}>
                  Rating: {r.rating} ⭐
                </div>
              )}
            </div>

            {/* Chat Area */}
            {activeChat === r.id && currentUser && (
              <div style={{ marginTop: 16 }}>
                <ServiceChat
                  requestId={r.id}
                  currentUser={currentUser}
                />
              </div>
            )}
          </div>
        ))}
        <div className="muted">{message}</div>
      </div>

      {/* Notifications Sidebar */}
      <div className="card">
        <h3 style={{ marginTop: 0 }}>Notifications</h3>
        <div style={{ maxHeight: 500, overflowY: 'auto' }}>
          {notifications.length === 0 && <div className="muted">No notifications</div>}
          {notifications.map(n => (
            <div key={n.id} style={{ padding: 10, borderBottom: '1px solid #eee', background: n.is_read ? 'transparent' : '#f0f9ff' }}>
              <div style={{ fontSize: '0.9rem' }}>{n.message}</div>
              <div className="small muted" style={{ marginTop: 4 }}>{new Date(n.created_at).toLocaleTimeString()}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

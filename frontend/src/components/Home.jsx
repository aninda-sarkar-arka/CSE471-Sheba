import React from 'react'

export default function Home(){
  return (
    <div className="card">
      <h1 style={{marginTop:0}}>Welcome to ServiceHub</h1>
      <p className="muted">Create a provider profile, list services, and connect with local customers.</p>
      <div style={{marginTop:16}}>
        <div className="small muted">Quick tips</div>
        <ul>
          <li>Use <strong>Profile</strong> to add location and skills.</li>
          <li>Use <strong>Services</strong> to add service listings (barber, plumber, etc.).</li>
        </ul>
      </div>
    </div>
  )
}

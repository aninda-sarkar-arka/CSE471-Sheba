import React, {useState} from 'react'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function LoginPage(){
  const [form, setForm] = useState({username:'', password:''})
  const [msg, setMsg] = useState('')

  async function login(e){
    e.preventDefault()
    try{
      const res = await api.post('/auth/login', form)
      setMsg('✓ Login successful')
      // give user feedback before redirecting
      setTimeout(()=> navigate('/'), 800)
    }catch(err){
      console.error('Login error:', err)
      const m = err?.response?.data?.msg || err?.message || 'Login failed'
      setMsg('✗ ' + m)
    }
  }

  const navigate = useNavigate()

  return (
    <div className="card" style={{maxWidth:520}}>
      <h2 style={{marginTop:0}}>Login</h2>
      <form onSubmit={login} style={{marginTop:12}}>
        <div className="form-row"><input placeholder="username" value={form.username} onChange={e=>setForm({...form, username:e.target.value})} /></div>
        <div className="form-row"><input type="password" placeholder="password" value={form.password} onChange={e=>setForm({...form, password:e.target.value})} /></div>
        <div className="form-row"><button className="btn" type="submit">Login</button> <span className="muted" style={{marginLeft:8}}>{msg}</span></div>
      </form>
    </div>
  )
}

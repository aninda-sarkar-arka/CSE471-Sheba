import React, {useState} from 'react'
import api from '../services/api'
import { useNavigate } from 'react-router-dom'

export default function RegisterPage(){
  const [form, setForm] = useState({username:'', password:''})
  const [msg, setMsg] = useState('')
  const navigate = useNavigate()

  async function register(e){
    e.preventDefault()
    try{
      await api.post('/auth/register', form)
      setMsg('Registered — you can login')
      navigate('/login')
    }catch(err){
      setMsg('Registration failed')
    }
  }

  return (
    <div className="card" style={{maxWidth:520}}>
      <h2 style={{marginTop:0}}>Register</h2>
      <form onSubmit={register} style={{marginTop:12}}>
        <div className="form-row"><input placeholder="username" value={form.username} onChange={e=>setForm({...form, username:e.target.value})} /></div>
        <div className="form-row"><input type="password" placeholder="password" value={form.password} onChange={e=>setForm({...form, password:e.target.value})} /></div>
        <div className="form-row"><button className="btn" type="submit">Register</button> <span className="muted" style={{marginLeft:8}}>{msg}</span></div>
      </form>
    </div>
  )
}

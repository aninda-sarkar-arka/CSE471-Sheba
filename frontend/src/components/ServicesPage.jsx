import React, {useState, useEffect} from 'react'
import api from '../services/api'

function ServiceRow({s, onDelete}){
  return (
    <div style={{border:'1px solid #ddd', padding:8, marginBottom:8}}>
      <h4>{s.title} <small>({s.category})</small></h4>
      <div>{s.description}</div>
      <div>Provider: {s.provider_username}</div>
      <div>Price: {s.price}</div>
      {onDelete && <button onClick={()=>onDelete(s.id)}>Delete</button>}
    </div>
  )
}

export default function ServicesPage(){
  const [services, setServices] = useState([])
  const [form, setForm] = useState({title:'', category:'', description:'', price:''})
  const [message, setMessage] = useState('')

  useEffect(()=>{ load() }, [])
  async function load(){
    try{
      const res = await api.get('/services')
      setServices(res.data)
    }catch(e){
      console.error(e)
    }
  }

  async function create(e){
    e.preventDefault()
    try{
      await api.post('/services', form)
      setMessage('Created')
      setForm({title:'', category:'', description:'', price:''})
      load()
    }catch(err){
      setMessage('Error creating (login required)')
    }
  }

  async function handleDelete(id){
    if(!confirm('Delete service?')) return
    try{
      await api.delete(`/services/${id}`)
      load()
    }catch(e){
      alert('Error deleting')
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <div className="header-row">
          <h2 style={{margin:0}}>Services</h2>
        </div>
        <form onSubmit={create} style={{marginTop:12}}>
          <div className="form-row"><input placeholder="Title" value={form.title} onChange={e=>setForm({...form, title:e.target.value})} /></div>
          <div className="form-row"><input placeholder="Category (e.g. plumber)" value={form.category} onChange={e=>setForm({...form, category:e.target.value})} /></div>
          <div className="form-row"><input placeholder="Price" value={form.price} onChange={e=>setForm({...form, price:e.target.value})} /></div>
          <div className="form-row"><textarea placeholder="Description" value={form.description} onChange={e=>setForm({...form, description:e.target.value})} /></div>
          <div className="form-row">
            <button className="btn" type="submit">Create Service</button>
            <span style={{marginLeft:8}} className="muted">{message}</span>
          </div>
        </form>
      </div>

      <div>
        {services.map(s=> (
          <div key={s.id} className="list-item" style={{marginBottom:12}}>
            <div className="header-row">
              <div>
                <div style={{fontWeight:600}}>{s.title}</div>
                <div className="small muted">{s.category} • {s.provider_username}</div>
              </div>
              <div className="space">
                <div className="small muted">{s.price}</div>
                <button className="btn secondary" onClick={()=>handleDelete(s.id)}>Delete</button>
              </div>
            </div>
            <div style={{marginTop:8}} className="muted">{s.description}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

import React, {useState, useEffect} from 'react'
import api from '../services/api'

const PARTNER_CATEGORIES = ['electrician','plumber','barber','housemaid','ac repair','fridge repair']
const LOCATIONS = ['Badda','Aftabnagar','Middle badda','Gulsan','mohakhali','Banani','Notunbazar','Rampura','Banashree','Motijheel','Mirpur1','Mirpur2','Mirpur10']

export default function ProfilePage(){
  const [profile, setProfile] = useState({
    name:'', location:'', skills:'', service_area:'', profile_photo:'',
    nid:'', partner_category:'', partner_locations:[], fee_min:'', fee_max:''
  })
  const [message, setMessage] = useState('')
  const [editingUser, setEditingUser] = useState(false)
  const [editingPartner, setEditingPartner] = useState(false)
  const [userMsg, setUserMsg] = useState('')
  const [partnerMsg, setPartnerMsg] = useState('')

  useEffect(()=>{
    async function load(){
      try{
        const res = await api.get('/profile')
        const data = res.data
        // ensure partner_locations is an array
        data.partner_locations = data.partner_locations || []
        setProfile(prev=>({...prev, ...data}))
      }catch(e){
        // not logged in or error
      }
    }
    load()
  },[])

  function toSkillsString(s){
    if(!s) return ''
    if(Array.isArray(s)) return s.join(',')
    return s
  }

  function toggleLocation(loc){
    setProfile(prev=>{
      const arr = prev.partner_locations || []
      let next
      if(arr.includes(loc)) next = arr.filter(x=>x!==loc)
      else {
        if(arr.length >= 3) return prev
        next = [...arr, loc]
      }
      return {...prev, partner_locations: next}
    })
  }

  async function saveUser(e){
    e && e.preventDefault()
    try{
      const payload = {
        name: profile.name,
        location: profile.location,
        service_area: profile.service_area,
        profile_photo: profile.profile_photo
      }
      const res = await api.put('/profile', payload)
      setUserMsg('✓ Saved')
      setEditingUser(false)
      setProfile(prev => ({...prev, ...res.data}))
    }catch(err){
      console.error('Save error:', err)
      const errMsg = err?.response?.data?.msg || err?.message || 'Error saving'
      setUserMsg('✗ ' + errMsg)
    }
  }

  async function savePartner(e){
    e && e.preventDefault()
    try{
      const payload = {
        nid: profile.nid,
        partner_category: profile.partner_category,
        partner_locations: profile.partner_locations,
        fee_min: profile.fee_min,
        fee_max: profile.fee_max,
        profile_photo: profile.profile_photo
      }
      const res = await api.put('/profile', payload)
      setPartnerMsg('✓ Saved')
      setEditingPartner(false)
      setProfile(prev => ({...prev, ...res.data}))
    }catch(err){
      console.error('Save error:', err)
      const msg = err?.response?.data?.msg || err?.message || 'Error saving'
      setPartnerMsg('✗ ' + msg)
    }
  }

  return (
    <div className="grid">
      <div className="card">
        <div className="header-row">
          <h3 style={{marginTop:0}}>User Profile</h3>
          <div className="space">
            {editingUser ? (
              <>
                <button className="btn secondary" onClick={()=>{ setEditingUser(false); setUserMsg('') }}>Cancel</button>
                <button className="btn" onClick={saveUser}>Save</button>
              </>
            ) : (
              <button className="btn secondary" onClick={()=>{ setEditingUser(true); setUserMsg('') }}>Edit</button>
            )}
          </div>
        </div>

        <form style={{marginTop:8}} onSubmit={e=>e.preventDefault()}>
          <div className="form-row" style={{display:'flex', gap:12, alignItems:'center'}}>
            <div style={{flex:'0 0 80px'}}>
              <img src={profile.profile_photo|| '/placeholder.png'} alt="photo" className="photo" />
            </div>
            <div style={{flex:1}}>
              <label>Full name</label>
              <input value={profile.name||''} onChange={e=>setProfile({...profile, name:e.target.value})} disabled={!editingUser} />
              <div className="small muted">(This name is stored in your profile and is separate from your login username)</div>
            </div>
          </div>

          <div className="form-row">
            <label>House address</label>
            <input value={profile.location||''} onChange={e=>setProfile({...profile, location:e.target.value})} disabled={!editingUser} />
          </div>
          <div className="form-row">
            <label>Phone number</label>
            <input value={profile.service_area||''} onChange={e=>setProfile({...profile, service_area:e.target.value})} disabled={!editingUser} />
          </div>
          <div className="form-row">
            <label>Profile photo (URL)</label>
            <input value={profile.profile_photo||''} onChange={e=>setProfile({...profile, profile_photo:e.target.value})} disabled={!editingUser} />
          </div>
          <div className="form-row muted small">{userMsg}</div>
        </form>
      </div>

      <div className="card">
        <div className="header-row">
          <h3 style={{marginTop:0}}>Partner Profile</h3>
          <div className="space">
            {editingPartner ? (
              <>
                <button className="btn secondary" onClick={()=>{ setEditingPartner(false); setPartnerMsg('') }}>Cancel</button>
                <button className="btn" onClick={savePartner}>Save</button>
              </>
            ) : (
              <button className="btn secondary" onClick={()=>{ setEditingPartner(true); setPartnerMsg('') }}>Edit</button>
            )}
          </div>
        </div>

        <p className="small muted">Fill partner details if you want to register as a service partner.</p>
        <form style={{marginTop:8}} onSubmit={e=>e.preventDefault()}>
          <div className="form-row">
            <label>Full name</label>
            <input value={profile.name||''} disabled />
          </div>
          <div className="form-row">
            <label>NID (only for partner)</label>
            <input value={profile.nid||''} onChange={e=>setProfile({...profile, nid:e.target.value})} disabled={!editingPartner} />
          </div>
          <div className="form-row">
            <label>Category</label>
            <select value={profile.partner_category||''} onChange={e=>setProfile({...profile, partner_category:e.target.value})} disabled={!editingPartner} >
              <option value="">-- select category --</option>
              {PARTNER_CATEGORIES.map(c=> <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-row">
            <label>Work areas (select up to 3)</label>
            <div style={{display:'flex', flexWrap:'wrap', gap:8}}>
              {LOCATIONS.map(loc=> (
                <label key={loc} style={{display:'inline-flex', alignItems:'center', gap:6}}>
                  <input type="checkbox" checked={(profile.partner_locations||[]).includes(loc)} onChange={()=>toggleLocation(loc)} disabled={!editingPartner} />
                  <span className="small">{loc}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="form-row">
            <label>Expected fee range (min - max)</label>
            <div style={{display:'flex', gap:8}}>
              <input type="number" min={200} max={5000} value={profile.fee_min||''} onChange={e=>setProfile({...profile, fee_min: Number(e.target.value)})} placeholder="min" disabled={!editingPartner} />
              <input type="number" min={200} max={5000} value={profile.fee_max||''} onChange={e=>setProfile({...profile, fee_max: Number(e.target.value)})} placeholder="max" disabled={!editingPartner} />
            </div>
          </div>

          <div className="form-row">
            <label>Profile photo (URL)</label>
            <input value={profile.profile_photo||''} onChange={e=>setProfile({...profile, profile_photo:e.target.value})} disabled={!editingPartner} />
          </div>

          <div className="form-row muted small">{partnerMsg}</div>
        </form>
      </div>
    </div>
  )
}

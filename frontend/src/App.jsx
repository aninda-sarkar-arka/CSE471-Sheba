import React from 'react'
import {BrowserRouter, Routes, Route} from 'react-router-dom'
import ProfilePage from './components/ProfilePage'
import Home from './components/Home'
import LoginPage from './components/LoginPage'
import RegisterPage from './components/RegisterPage'
import Header from './components/Header'

export default function App(){
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header />
        <main className="container">
          <Routes>
            <Route path="/" element={<Home/>} />
            <Route path="/profile" element={<ProfilePage/>} />
            <Route path="/login" element={<LoginPage/>} />
            <Route path="/register" element={<RegisterPage/>} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

import React, { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const Navbar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const { email, isDemo, logout } = useAuth()
  const [profileOpen, setProfileOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const menuRef = useRef<HTMLDivElement>(null)

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchTerm.trim()) return
    navigate(`/library?q=${encodeURIComponent(searchTerm.trim())}`)
  }

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setProfileOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [menuRef])

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  const avatarInitial = email ? email[0].toUpperCase() : '?'

  const navLinks = [
    { name: 'Today', path: '/' },
    { name: 'Library', path: '/library' },
    { name: 'Revisit', path: '/revisit' },
    { name: 'Collections', path: '/collections' },
    { name: 'Insights', path: '/insights' }
  ]

  return (
    <nav className="glass-panel" style={{ position: 'relative', zIndex: 50, margin: '24px auto 40px', maxWidth: '1200px', padding: '0', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px 24px', borderRight: '1px solid var(--border-color)' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '6px', background: 'linear-gradient(135deg, var(--primary-color), var(--secondary-color))' }}></div>
          <h2 style={{ margin: 0, fontSize: '1.2rem', fontFamily: 'Outfit, sans-serif' }}>HalfLife</h2>
        </Link>
        <div style={{ display: 'flex' }}>
          {navLinks.map((link) => (
            <Link 
              key={link.path}
              to={link.path}
              style={{ 
                padding: '18px 24px', 
                color: location.pathname === link.path ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontWeight: location.pathname === link.path ? '600' : '400',
                borderBottom: location.pathname === link.path ? '2px solid var(--primary-color)' : '2px solid transparent',
                transition: 'var(--transition-fast)'
              }}
            >
              {link.name}
            </Link>
          ))}
        </div>
      </div>
      
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', paddingRight: '24px' }}>
        <form onSubmit={handleSearch} style={{ position: 'relative' }}>
          <input
            type="text"
            placeholder="Search..."
            className="input-base"
            style={{ width: '200px', padding: '8px 12px', borderRadius: '20px' }}
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </form>
        <div ref={menuRef} style={{ position: 'relative' }}>
          <button 
            onClick={() => setProfileOpen(!profileOpen)}
            style={{ 
              background: 'transparent', border: 'none', color: 'var(--text-primary)', 
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px',
              padding: '8px', borderRadius: '8px'
            }}
          >
            <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--bg-surface-elevated)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {avatarInitial}
            </div>
          </button>
          
          {profileOpen && (
            <div className="glass-panel" style={{
              position: 'absolute', top: '100%', right: '0', marginTop: '8px',
              minWidth: '200px', display: 'flex', flexDirection: 'column',
              padding: '8px', zIndex: 100,
              background: 'rgb(30, 33, 42)', backdropFilter: 'none', WebkitBackdropFilter: 'none',
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.5)',
            }}>
              <div style={{ padding: '8px 16px', borderBottom: '1px solid var(--border-color)', marginBottom: '8px' }}>
                <div style={{ fontWeight: '600' }}>{isDemo ? 'Demo account' : 'Signed in'}</div>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>{email}</div>
              </div>
              <button className="btn-secondary" style={{ textAlign: 'left', border: 'none', justifyContent: 'flex-start' }} onClick={() => { navigate('/preferences'); setProfileOpen(false); }}>Preferences</button>
              <button className="btn-secondary" style={{ textAlign: 'left', border: 'none', justifyContent: 'flex-start' }} onClick={() => { navigate('/test-prompts'); setProfileOpen(false); }}>Test Prompts</button>
              <button className="btn-secondary" style={{ textAlign: 'left', border: 'none', justifyContent: 'flex-start', color: 'var(--status-red)' }} onClick={handleLogout}>Sign out</button>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar

import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile, updateProfile } from '../services/api'
import { useTheme } from '../context/ThemeContext'
import '../styles/adminDashboard.css'
import '../styles/accountSettings.css'

// ── Password strength ─────────────────────────────────────────────────────────
function getStrength(pw) {
  if (!pw) return 0
  let score = 0
  if (pw.length >= 1)            score++ // any input → at least Weak
  if (pw.length >= 8)            score++ // 8+ characters
  if (/[0-9]/.test(pw))          score++ // contains a number
  if (/[^A-Za-z0-9]/.test(pw))   score++ // contains a symbol
  return score
}
const STRENGTH_LABELS  = ['', 'Weak', 'Fair', 'Good', 'Strong']
const STRENGTH_CLASSES = ['', 'filled-weak', 'filled-fair', 'filled-good', 'filled-strong']
const STRENGTH_COLORS  = ['', '#ef4444', '#f59e0b', '#248daa', '#20963c']

// ── Icons ─────────────────────────────────────────────────────────────────────
const IconBack = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
)
const IconUser = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconEye = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
)
const IconEyeOff = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/>
    <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
)

function AccountSettings() {
  const navigate = useNavigate()
  const { highContrast, setHighContrast } = useTheme()

  // refs for scroll-to
  const refEmail    = useRef(null)
  const refPassword = useRef(null)
  const refAccessibility = useRef(null)
  const refNotifs   = useRef(null)
  const refDanger   = useRef(null)

  const scrollTo = (ref) => ref.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })

  const [userId,  setUserId]  = useState(null)
  const [loading, setLoading] = useState(true)

  // Password visibility toggles
  const [showEmailPw,   setShowEmailPw]   = useState(false)
  const [showCurrentPw, setShowCurrentPw] = useState(false)
  const [showNewPw,     setShowNewPw]     = useState(false)
  const [showConfirmPw, setShowConfirmPw] = useState(false)

  // Email
  const [currentEmail, setCurrentEmail] = useState('')
  const [newEmail,     setNewEmail]     = useState('')
  const [emailPw,      setEmailPw]      = useState('')
  const [emailMsg,     setEmailMsg]     = useState(null)
  const [emailSaving,  setEmailSaving]  = useState(false)

  // Password
  const [currentPw, setCurrentPw] = useState('')
  const [newPw,     setNewPw]     = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwMsg,     setPwMsg]     = useState(null)
  const [pwSaving,  setPwSaving]  = useState(false)
  const strength = getStrength(newPw)

  // Accessibility (high contrast lives in ThemeContext; other prefs are local for now)
  const [fontSize,       setFontSize]       = useState('small')
  const [colorBlindMode, setColorBlindMode] = useState('normal')

  // Notifications
  const [notifEmail,    setNotifEmail]    = useState(true)
  const [notifSecurity, setNotifSecurity] = useState(true)
  const [notifUpdates,  setNotifUpdates]  = useState(false)
  const [notifMarketing,setNotifMarketing]= useState(false)
  const [notifMsg,      setNotifMsg]      = useState(null)
  const [notifSaving,   setNotifSaving]   = useState(false)

  // Profile name (for avatar initials + display)
  const [name, setName] = useState('')

  // Danger modals
  const [showDelete, setShowDelete] = useState(false)

  // ── Load ────────────────────────────────────────────────────────────────────
  useEffect(() => {
    const load = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) { navigate('/login', { replace: true }); return }

      // getUser() hits the server so email is always up-to-date after a change
      const { data: { user } } = await supabase.auth.getUser()
      setUserId(user.id)
      setCurrentEmail(user.email ?? '')

      try {
        const prof = await getProfile(session.user.id)
        setName(prof.name ?? '')
        setNotifEmail(prof.notify_appointment_reminders ?? true)
        setNotifSecurity(prof.notify_appointment_updates  ?? true)
        setNotifUpdates(prof.notify_messages              ?? false)
      } catch {}

      setLoading(false)
    }
    load()
  }, [navigate])

  const initials = name
    ? name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2)
    : currentEmail.slice(0, 2).toUpperCase()

  // ── Update email ────────────────────────────────────────────────────────────
  const handleUpdateEmail = async () => {
    setEmailMsg(null)
    if (!newEmail)  { setEmailMsg({ type: 'error', text: 'New email is required.' }); return }
    setEmailSaving(true)
    try {
      const { error } = await supabase.auth.updateUser({ email: newEmail })
      if (error) throw new Error(error.message)
      setEmailMsg({ type: 'success', text: 'Verification link sent to your new address.' })
      setNewEmail(''); setEmailPw('')
    } catch (e) {
      setEmailMsg({ type: 'error', text: e.message ?? 'Failed to update email.' })
    }
    setEmailSaving(false)
  }

  // ── Update password ─────────────────────────────────────────────────────────
  const handleUpdatePassword = async () => {
    setPwMsg(null)
    if (!newPw)              { setPwMsg({ type: 'error', text: 'New password is required.' }); return }
    if (newPw !== confirmPw) { setPwMsg({ type: 'error', text: 'Passwords do not match.' });   return }
    if (strength < 2)        { setPwMsg({ type: 'error', text: 'Password is too weak.' });     return }
    setPwSaving(true)
    try {
      const { error } = await supabase.auth.updateUser({ password: newPw })
      if (error) throw new Error(error.message)
      setPwMsg({ type: 'success', text: 'Password updated successfully.' })
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
    } catch (e) {
      setPwMsg({ type: 'error', text: e.message ?? 'Failed to update password.' })
    }
    setPwSaving(false)
  }

  // ── Save notifications ──────────────────────────────────────────────────────
  const handleSaveNotifications = async () => {
    setNotifMsg(null)
    setNotifSaving(true)
    try {
      await updateProfile(userId, {
        notify_appointment_reminders: notifEmail,
        notify_appointment_updates:   notifSecurity,
        notify_messages:              notifUpdates,
      })
      setNotifMsg({ type: 'success', text: 'Notification preferences saved.' })
    } catch (e) {
      setNotifMsg({ type: 'error', text: e.message ?? 'Failed to save preferences.' })
    }
    setNotifSaving(false)
  }

  // ── Logout ──────────────────────────────────────────────────────────────────
  const [showLogout, setShowLogout] = useState(false)
  const handleLogout = async () => {
    setShowLogout(false)
    sessionStorage.removeItem('userRole')
    await supabase.auth.signOut()
    navigate('/login')
  }

  // ── Danger actions ──────────────────────────────────────────────────────────
  const handleDelete = async () => {
    setShowDelete(false)
    await supabase.auth.signOut()
    navigate('/login')
  }

  if (loading) return null

  return (
    <div className="adb-layout as-layout">

      {/* ── Sidebar ── */}
      <aside className="adb-sidebar">
        <div className="adb-profile">
          <div className="adb-avatar"><IconUser /></div>
          <span className="adb-profile-name">{name || currentEmail}</span>
          <span className="adb-profile-role">My Account</span>
        </div>

        <nav className="adb-nav">
          {/* SECURITY */}
          <span className="as-nav-group-label">SECURITY</span>
          <div className="adb-nav-item" onClick={() => scrollTo(refEmail)}>
            <span className="adb-nav-label">Change Email</span>
          </div>
          <div className="adb-nav-item" onClick={() => scrollTo(refPassword)}>
            <span className="adb-nav-label">Change Password</span>
          </div>

          {/* PREFERENCES */}
          <span className="as-nav-group-label">PREFERENCES</span>
          <div className="adb-nav-item" onClick={() => scrollTo(refAccessibility)}>
            <span className="adb-nav-label">Accessibility</span>
          </div>
          <div className="adb-nav-item" onClick={() => scrollTo(refNotifs)}>
            <span className="adb-nav-label">Notifications</span>
          </div>

          {/* ACCOUNT */}
          <span className="as-nav-group-label">ACCOUNT</span>
          <div className="adb-nav-item" onClick={() => scrollTo(refDanger)}>
            <span className="adb-nav-label">Danger Zone</span>
          </div>

        </nav>
      </aside>

      {/* ── Main ── */}
      <main className="adb-main">
        <div className="as-top-actions">
          <button className="adb-back-btn" onClick={() => navigate('/')}>
            <IconBack /> Home
          </button>
          <button className="as-logout-btn" onClick={() => setShowLogout(true)}>
            Log Out
          </button>
        </div>

        <h1 className="adb-welcome">Account Settings</h1>
        <p className="adb-subtitle">Manage your security and app preferences.</p>

        {/* ── Change Email ── */}
        <div className="as-card" ref={refEmail}>
          <h2 className="as-card-title">Change Email</h2>
          <p className="as-card-sub">
            Your current email is <strong>{currentEmail}</strong>. We'll send a verification link to your new address.
          </p>

          <div className="as-field">
            <label className="as-label">New Email Address</label>
            <input
              className="as-input"
              type="email"
              value={newEmail}
              onChange={e => setNewEmail(e.target.value)}
              placeholder="new@example.com"
            />
          </div>
          <div className="as-field">
            <label className="as-label">Confirm Password</label>
            <div className="as-input-wrap">
              <input
                className="as-input"
                type={showEmailPw ? 'text' : 'password'}
                value={emailPw}
                onChange={e => setEmailPw(e.target.value)}
                placeholder="Enter password to confirm"
              />
              <button className="as-eye-btn" type="button" onClick={() => setShowEmailPw(v => !v)}>
                {showEmailPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
          </div>

          {emailMsg && <div className={`as-feedback ${emailMsg.type}`}>{emailMsg.text}</div>}

          <div className="as-card-footer">
            <button className="as-btn-cancel" onClick={() => { setNewEmail(''); setEmailPw(''); setEmailMsg(null) }}>Cancel</button>
            <button className="as-btn-primary" onClick={handleUpdateEmail} disabled={emailSaving}>
              {emailSaving ? 'Sending…' : 'Update Email'}
            </button>
          </div>
        </div>

        {/* ── Change Password ── */}
        <div className="as-card" ref={refPassword}>
          <h2 className="as-card-title">Change Password</h2>
          <p className="as-card-sub">Choose a strong password with at least 8 characters, a number, and a symbol.</p>

          <div className="as-field">
            <label className="as-label">Current Password</label>
            <div className="as-input-wrap">
              <input
                className="as-input"
                type={showCurrentPw ? 'text' : 'password'}
                value={currentPw}
                onChange={e => setCurrentPw(e.target.value)}
                placeholder="••••••••"
              />
              <button className="as-eye-btn" type="button" onClick={() => setShowCurrentPw(v => !v)}>
                {showCurrentPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
          </div>
          <div className="as-field">
            <label className="as-label">New Password</label>
            <p className="as-pw-hint">Min. 8 characters · at least one number · at least one symbol (!, @, #…)</p>
            <div className="as-input-wrap">
              <input
                className="as-input"
                type={showNewPw ? 'text' : 'password'}
                value={newPw}
                onChange={e => setNewPw(e.target.value)}
                placeholder="••••••••"
              />
              <button className="as-eye-btn" type="button" onClick={() => setShowNewPw(v => !v)}>
                {showNewPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
            <div className="as-strength-bar" style={{ marginTop: 10 }}>
              {[1,2,3,4].map(i => (
                <div key={i} className={`as-strength-seg${i <= strength ? ' ' + STRENGTH_CLASSES[strength] : ''}`} />
              ))}
            </div>
            <p className="as-strength-text" style={{ color: strength > 0 ? STRENGTH_COLORS[strength] : '#94a3b8' }}>
              {newPw ? STRENGTH_LABELS[strength] : 'Start typing to check strength'}
            </p>
          </div>
          <div className="as-field">
            <label className="as-label">Confirm Password</label>
            <div className="as-input-wrap">
              <input
                className={`as-input${confirmPw && confirmPw !== newPw ? ' error' : ''}`}
                type={showConfirmPw ? 'text' : 'password'}
                value={confirmPw}
                onChange={e => setConfirmPw(e.target.value)}
                placeholder="••••••••"
              />
              <button className="as-eye-btn" type="button" onClick={() => setShowConfirmPw(v => !v)}>
                {showConfirmPw ? <IconEyeOff /> : <IconEye />}
              </button>
            </div>
          </div>

          {pwMsg && <div className={`as-feedback ${pwMsg.type}`}>{pwMsg.text}</div>}

          <div className="as-card-footer">
            <button className="as-btn-cancel" onClick={() => { setCurrentPw(''); setNewPw(''); setConfirmPw(''); setPwMsg(null) }}>Cancel</button>
            <button className="as-btn-primary" onClick={handleUpdatePassword} disabled={pwSaving}>
              {pwSaving ? 'Updating…' : 'Update Password'}
            </button>
          </div>
        </div>

        {/* ── Accessibility ── */}
        <div className="as-card" ref={refAccessibility}>
          <h2 className="as-card-title">Accessibility Options</h2>
          <p className="as-card-sub">Adjust visual settings for better readability and usability.</p>
        
          <div className="as-toggle-row">
            <div className="as-toggle-info">
              <span className="as-toggle-label">High Contrast Mode</span>
              <span className="as-toggle-desc">Increase contrast for better visibility</span>
            </div>
            <label className="as-toggle">
              <input type="checkbox" checked={highContrast} onChange={e => setHighContrast(e.target.checked)} />
              <span className="as-toggle-track" />
            </label>
          </div>

          <div className="as-accessibility-grid">
            <div className="as-field">
              <label className="as-label">Font Size</label>
              <div className="as-radio-group">
                <label className="as-radio">
                  <input type="radio" name="fontSize" value="small" checked={fontSize === 'small'} onChange={e => setFontSize(e.target.value)} />
                  <span>Small</span>
                </label>

                <label className="as-radio">
                  <input type="radio" name="fontSize" value="medium" checked={fontSize === 'medium'} onChange={e => setFontSize(e.target.value)} />
                  <span>Medium</span>
                </label>

                <label className="as-radio">
                  <input type="radio" name="fontSize" value="large" checked={fontSize === 'large'} onChange={e => setFontSize(e.target.value)} />
                  <span>Large</span>
                </label>
              </div>
            </div>  

            <div className="as-field">
              <label className="as-label">Colorblind Theme</label>
              <div className="as-radio-group">
                <label className="as-radio">
                  <input type="radio" name="colorblindTheme"value="normal" checked={colorBlindMode === 'normal'} onChange={e => setColorBlindMode(e.target.value)} />
                  <span>Normal</span>
                </label>

                <label className="as-radio">
                  <input type="radio" name="colorblindTheme" value="protanopia" checked={colorBlindMode === 'protanopia'} onChange={e => setColorBlindMode(e.target.value)} />
                  <span>Protanopia (Red-Blind)</span>
                </label>

                <label className="as-radio">
                  <input type="radio" name="colorblindTheme" value="deuteranopia" checked={colorBlindMode === 'deuteranopia'} onChange={e => setColorBlindMode(e.target.value)} />
                  <span>Deuteranopia (Green-Blind)</span>
                </label>

                <label className="as-radio">
                  <input type="radio" name="colorblindTheme" value="tritanopia" checked={colorBlindMode === 'tritanopia'} onChange={e => setColorBlindMode(e.target.value)} />
                  <span>Tritanopia (Blue-Blind)</span>
                </label>
              </div>
            </div>
          </div>

          <div className="as-accessibility-preview">
            <label className="as-label">Preview</label>

            <div className="as-preview-box">
              <p className="as-label" style={{marginBottom: 4}}>Confirm appointment details:</p>
              <p className="as-preview-copy">Book normal appointment September 5th 2025 at 9 am?</p>

              <div className="as-preview-actions">
                <button type="button" className="as-btn-cancel">Cancel</button>
                <button type="button" className="as-btn-primary">Confirm</button>
              </div>
            </div>

            <div className="as-preview-status">
              <h4 className="as-label">Status Indicators</h4>

              <div className="as-status-item">
                <span className="as-status-dot confirmed" />
                <span>Confirmed</span>
              </div>

              <div className="as-status-item">
                <span className="as-status-dot pending" />
                <span>Pending</span>
              </div>

              <div className="as-status-item">
                <span className="as-status-dot cancelled" />
                <span>Cancelled</span>
              </div>
            </div>
          </div>  
        </div>

        {/* ── Notifications ── */}
        <div className="as-card" ref={refNotifs}>
          <h2 className="as-card-title">Notification Preferences</h2>
          <p className="as-card-sub">Choose how and when you'd like to be notified.</p>

          <div className="as-toggle-row">
            <div className="as-toggle-info">
              <span className="as-toggle-label">Email Notifications</span>
              <span className="as-toggle-desc">Receive updates and alerts via email</span>
            </div>
            <label className="as-toggle">
              <input type="checkbox" checked={notifEmail} onChange={e => setNotifEmail(e.target.checked)} />
              <span className="as-toggle-track" />
            </label>
          </div>

          <div className="as-toggle-row">
            <div className="as-toggle-info">
              <span className="as-toggle-label">Security Alerts</span>
              <span className="as-toggle-desc">Get notified about suspicious login attempts</span>
            </div>
            <label className="as-toggle">
              <input type="checkbox" checked={notifSecurity} onChange={e => setNotifSecurity(e.target.checked)} />
              <span className="as-toggle-track" />
            </label>
          </div>

          <div className="as-toggle-row">
            <div className="as-toggle-info">
              <span className="as-toggle-label">Product Updates</span>
              <span className="as-toggle-desc">News about new features and improvements</span>
            </div>
            <label className="as-toggle">
              <input type="checkbox" checked={notifUpdates} onChange={e => setNotifUpdates(e.target.checked)} />
              <span className="as-toggle-track" />
            </label>
          </div>

          <div className="as-toggle-row">
            <div className="as-toggle-info">
              <span className="as-toggle-label">Marketing Emails</span>
              <span className="as-toggle-desc">Tips, offers, and promotional content</span>
            </div>
            <label className="as-toggle">
              <input type="checkbox" checked={notifMarketing} onChange={e => setNotifMarketing(e.target.checked)} />
              <span className="as-toggle-track" />
            </label>
          </div>

          {notifMsg && <div className={`as-feedback ${notifMsg.type}`}>{notifMsg.text}</div>}

          <div className="as-card-footer">
            <button className="as-btn-primary" onClick={handleSaveNotifications} disabled={notifSaving}>
              {notifSaving ? 'Saving…' : 'Save Preferences'}
            </button>
          </div>
        </div>

        {/* ── Danger Zone ── */}
        <div className="as-card as-card-danger" ref={refDanger}>
          <div className="as-danger-title-row">
            <span style={{ color: '#dc2626', fontSize: 18 }}>⚠</span>
            <h2 className="as-danger-title">Danger Zone</h2>
          </div>
          <p className="as-danger-sub">These actions are irreversible. Please proceed with caution.</p>

          <div className="as-danger-row">
            <div className="as-danger-info">
              <span className="as-danger-item-title">Delete Account</span>
              <span className="as-danger-item-desc">Permanently delete your account and all data. This cannot be undone.</span>
            </div>
            <button className="as-btn-danger-fill" onClick={() => setShowDelete(true)}>Delete Account</button>
          </div>
        </div>
      </main>

      {/* ── Logout Modal ── */}
      {showLogout && (
        <div className="as-modal-overlay" onClick={() => setShowLogout(false)}>
          <div className="as-modal" onClick={e => e.stopPropagation()}>
            <div className="as-modal-header" style={{ background: '#113c51' }}>
              <h2>Log Out</h2>
              <p>You will be returned to the login screen.</p>
            </div>
            <div className="as-modal-body">
              <p>Are you sure you want to log out of your account?</p>
            </div>
            <div className="as-modal-footer">
              <button className="as-modal-cancel" onClick={() => setShowLogout(false)}>Cancel</button>
              <button className="as-btn-danger-fill" style={{ flex: 1, height: 44 }} onClick={handleLogout}>Log Out</button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Modal ── */}
      {showDelete && (
        <div className="as-modal-overlay" onClick={() => setShowDelete(false)}>
          <div className="as-modal" onClick={e => e.stopPropagation()}>
            <div className="as-modal-header">
              <h2>Delete Account</h2>
              <p>This action is permanent and cannot be undone.</p>
            </div>
            <div className="as-modal-body">
              <p>All your data, appointments, and history will be permanently deleted.</p>
            </div>
            <div className="as-modal-footer">
              <button className="as-modal-cancel" onClick={() => setShowDelete(false)}>Cancel</button>
              <button className="as-btn-danger-fill" style={{ flex: 1, height: 44 }} onClick={handleDelete}>Delete Forever</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AccountSettings

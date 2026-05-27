import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabaseClient'
import { getProfile } from '../services/api'
import { listAdminUsers, changeUserRole, deactivateUser, deleteUser } from '../services/adminApi'
import '../styles/adminDashboard.css'
import '../styles/adminUsers.css'

// ── Icons ─────────────────────────────────────────────────────────────────────
const IconDashboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
)
const IconUsers = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
    <circle cx="9" cy="7" r="4"/>
    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
  </svg>
)
const IconCalendar = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="4" width="18" height="18" rx="2"/>
    <line x1="16" y1="2" x2="16" y2="6"/>
    <line x1="8" y1="2" x2="8" y2="6"/>
    <line x1="3" y1="10" x2="21" y2="10"/>
  </svg>
)
const IconSettings = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3"/>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
  </svg>
)
const IconLogout = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
    <polyline points="16 17 21 12 16 7"/>
    <line x1="21" y1="12" x2="9" y2="12"/>
  </svg>
)
const IconUser = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
)
const IconSearch = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
)
const IconChevronLeft = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
)
const IconChevronRight = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
)
const IconWarning = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
)

const ROLES = ['patient', 'doctor', 'admin']
const PER_PAGE = 20

// ── Main component ─────────────────────────────────────────────────────────────
function AdminUsers() {
  const navigate = useNavigate()

  // Auth
  const [authorized, setAuthorized] = useState(false)
  const [currentUserId, setCurrentUserId] = useState(null)
  const [profile, setProfile] = useState(null)

  // Data
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  // Filters
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  // Modals
  const [roleModal, setRoleModal]           = useState(null)   // { user }
  const [deactivateModal, setDeactivateModal] = useState(null) // { user }
  const [deleteModal, setDeleteModal]       = useState(null)   // { user }

  // Modal state
  const [selectedRole, setSelectedRole] = useState('')
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError]   = useState(null)

  // ── Auth check ──────────────────────────────────────────────────────────────
  useEffect(() => {
    const checkAccess = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) {
        sessionStorage.removeItem('userRole')
        navigate('/login', { replace: true })
        return
      }

      setCurrentUserId(session.user.id)

      if (sessionStorage.getItem('userRole') === 'admin') {
        setAuthorized(true)
        try { setProfile(await getProfile(session.user.id)) } catch {}
        return
      }

      const { data: roleRows } = await supabase
        .from('user_roles')
        .select('roles(name)')
        .eq('user_id', session.user.id)

      const role = roleRows?.[0]?.roles?.name
      if (role !== 'admin') {
        sessionStorage.removeItem('userRole')
        navigate('/', { replace: true })
        return
      }

      sessionStorage.setItem('userRole', 'admin')
      setAuthorized(true)
      try { setProfile(await getProfile(session.user.id)) } catch {}
    }

    checkAccess()
  }, [navigate])

  // ── Fetch users ─────────────────────────────────────────────────────────────
  const fetchUsers = useCallback(async (pg = 1) => {
    setLoading(true)
    setError(null)
    try {
      const data = await listAdminUsers({
        page: pg,
        perPage: PER_PAGE,
        role: roleFilter || undefined,
        status: statusFilter || undefined,
      })
      setUsers(data.users || [])
      setHasMore((data.users || []).length >= PER_PAGE)
    } catch (err) {
      setError(err.message || 'Failed to load users.')
    } finally {
      setLoading(false)
    }
  }, [roleFilter, statusFilter])

  useEffect(() => {
    if (!authorized) return
    setPage(1)
    fetchUsers(1)
  }, [authorized, roleFilter, statusFilter, fetchUsers])

  const handlePageChange = (newPage) => {
    setPage(newPage)
    fetchUsers(newPage)
  }

  // ── Logout ───────────────────────────────────────────────────────────────────
  const handleLogout = async () => {
    sessionStorage.removeItem('userRole')
    await supabase.auth.signOut()
    navigate('/login')
  }

  // ── Filtered (client-side search on email) ───────────────────────────────────
  const filteredUsers = search.trim()
    ? users.filter(u => u.email?.toLowerCase().includes(search.toLowerCase()))
    : users

  // ── Action handlers ──────────────────────────────────────────────────────────
  const openRoleModal = (user) => {
    setSelectedRole(user.role || 'patient')
    setActionError(null)
    setRoleModal({ user })
  }

  const handleChangeRole = async () => {
    if (!roleModal || !selectedRole) return
    setActionLoading(true)
    setActionError(null)
    try {
      await changeUserRole(roleModal.user.user_id, selectedRole)
      setUsers(prev => prev.map(u =>
        u.user_id === roleModal.user.user_id ? { ...u, role: selectedRole } : u
      ))
      setRoleModal(null)
    } catch (err) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeactivate = async () => {
    if (!deactivateModal) return
    setActionLoading(true)
    setActionError(null)
    try {
      await deactivateUser(deactivateModal.user.user_id)
      setUsers(prev => prev.map(u =>
        u.user_id === deactivateModal.user.user_id ? { ...u, status: 'inactive' } : u
      ))
      setDeactivateModal(null)
    } catch (err) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!deleteModal) return
    setActionLoading(true)
    setActionError(null)
    try {
      await deleteUser(deleteModal.user.user_id)
      setUsers(prev => prev.filter(u => u.user_id !== deleteModal.user.user_id))
      setDeleteModal(null)
    } catch (err) {
      setActionError(err.message)
    } finally {
      setActionLoading(false)
    }
  }

  // ── Display name ─────────────────────────────────────────────────────────────
  const displayName = profile?.name ?? profile?.first_name ?? '…'
  const initials = displayName !== '…'
    ? displayName.split(' ').map(p => p[0]).join('').toUpperCase().slice(0, 2)
    : '?'

  if (!authorized) return null

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="admin-page adb-layout">

      {/* ── Sidebar — same structure as AdminDashboard ── */}
      <aside className="adb-sidebar">
        <div className="adb-profile">
          <div className="adb-avatar"><IconUser /></div>
          <button className="adb-profile-name" onClick={() => navigate('/admin-profile')}>
            {displayName}
          </button>
          <span className="adb-profile-role">Admin</span>
        </div>

        <nav className="adb-nav">
          <div className="adb-nav-item" onClick={() => navigate('/admin-dashboard')}>
            <span className="adb-nav-icon-svg"><IconDashboard /></span>
            <span className="adb-nav-label">Dashboard</span>
          </div>
          <div className="adb-nav-item active">
            <span className="adb-nav-icon-svg"><IconUsers /></span>
            <span className="adb-nav-label">Users</span>
          </div>
          <div className="adb-nav-item" onClick={() => navigate('/appointmenthistory')}>
            <span className="adb-nav-icon-svg"><IconCalendar /></span>
            <span className="adb-nav-label">Appointments</span>
          </div>
          <div className="adb-nav-item" onClick={() => navigate('/admin/closures')}>
            <span className="adb-nav-icon-svg"><IconSettings /></span>
            <span className="adb-nav-label">Settings</span>
          </div>
          <div className="adb-nav-item adb-nav-logout" onClick={handleLogout}>
            <span className="adb-nav-icon-svg"><IconLogout /></span>
            <span className="adb-nav-label">Log Out</span>
          </div>
        </nav>
      </aside>

      {/* ── Main ── */}
      <main className="admin-main">

        {/* Top bar */}
        <div className="admin-topbar">
          <div>
            <h1 className="admin-topbar-title">User Management</h1>
            <p className="admin-topbar-sub">View and manage all registered users</p>
          </div>
        </div>

        {/* Card */}
        <div className="admin-content">
        <div className="admin-card">

          {/* Filter bar */}
          <div className="admin-filter-bar">
            <div className="admin-search-wrap">
              <span className="admin-search-icon"><IconSearch /></span>
              <input
                className="admin-search"
                type="text"
                placeholder="Search by email…"
                value={search}
                onChange={e => setSearch(e.target.value)}
              />
            </div>

            <select
              className="admin-select"
              value={roleFilter}
              onChange={e => { setRoleFilter(e.target.value); setPage(1) }}
            >
              <option value="">All Roles</option>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="admin">Admin</option>
            </select>

            <select
              className="admin-select"
              value={statusFilter}
              onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
            >
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          {/* Error banner */}
          {error && !loading && (
            <div className="admin-error-banner">
              <IconWarning /> {error}
              <button className="admin-retry-btn" onClick={() => fetchUsers(page)}>Retry</button>
            </div>
          )}

          {/* Table */}
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Last Sign In</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i}>
                      {Array.from({ length: 6 }).map((__, j) => (
                        <td key={j}><div className="skeleton" style={{ width: j === 5 ? 160 : '80%', height: 16 }} /></td>
                      ))}
                    </tr>
                  ))
                ) : filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={6}>
                      <div className="admin-state">
                        <div className="admin-state-icon"><IconUsers /></div>
                        <p className="admin-state-title">No users found</p>
                        <p className="admin-state-sub">
                          {search || roleFilter || statusFilter
                            ? 'Try adjusting your filters or search query.'
                            : 'No users have registered yet.'}
                        </p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map(user => {
                    const isOwn = user.user_id === currentUserId
                    const isInactive = user.status === 'inactive'
                    return (
                      <tr key={user.user_id}>
                        <td className="admin-td-email">{user.email ?? '—'}</td>
                        <td>
                          <span className={`role-badge role-${user.role ?? 'unknown'}`}>
                            {user.role ?? 'none'}
                          </span>
                        </td>
                        <td>
                          <span className={`status-badge status-${user.status}`}>
                            {user.status}
                          </span>
                        </td>
                        <td className="admin-td-meta">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="admin-td-meta">
                          {user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleDateString() : 'Never'}
                        </td>
                        <td>
                          <div className="action-btns">
                            <button
                              className="action-btn role"
                              onClick={() => openRoleModal(user)}
                              title="Change role"
                            >
                              Role
                            </button>
                            <button
                              className="action-btn deactivate"
                              onClick={() => { setActionError(null); setDeactivateModal({ user }) }}
                              disabled={isOwn || isInactive}
                              title={isOwn ? 'Cannot deactivate own account' : isInactive ? 'Already inactive' : 'Deactivate user'}
                            >
                              Deactivate
                            </button>
                            <button
                              className="action-btn delete"
                              onClick={() => { setActionError(null); setDeleteModal({ user }) }}
                              disabled={isOwn}
                              title={isOwn ? 'Cannot delete own account' : 'Delete user'}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {!loading && !error && filteredUsers.length > 0 && (
            <div className="admin-pagination">
              <button
                className="page-btn"
                onClick={() => handlePageChange(page - 1)}
                disabled={page === 1}
              >
                <IconChevronLeft />
              </button>
              <span className="page-info">Page {page}</span>
              <button
                className="page-btn"
                onClick={() => handlePageChange(page + 1)}
                disabled={!hasMore}
              >
                <IconChevronRight />
              </button>
            </div>
          )}

        </div>
        </div>
      </main>

      {/* ── Change Role Modal ── */}
      {roleModal && (
        <div className="modal-overlay" onClick={() => setRoleModal(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header blue">
              <h2>Change Role</h2>
              <p>{roleModal.user.email}</p>
            </div>
            <div className="modal-body">
              <p className="modal-label">Select new role</p>
              <div className="role-options">
                {ROLES.map(r => (
                  <button
                    key={r}
                    className={`role-option-btn ${selectedRole === r ? 'selected' : ''}`}
                    onClick={() => setSelectedRole(r)}
                  >
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </button>
                ))}
              </div>
              {actionError && <p className="modal-error">{actionError}</p>}
            </div>
            <div className="modal-footer">
              <button className="modal-cancel" onClick={() => setRoleModal(null)} disabled={actionLoading}>
                Cancel
              </button>
              <button
                className="modal-confirm blue"
                onClick={handleChangeRole}
                disabled={actionLoading || selectedRole === roleModal.user.role}
              >
                {actionLoading ? 'Saving…' : 'Save Role'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Deactivate Modal ── */}
      {deactivateModal && (
        <div className="modal-overlay" onClick={() => setDeactivateModal(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header orange">
              <h2>Deactivate User</h2>
            </div>
            <div className="modal-body">
              <p>Are you sure you want to deactivate <strong>{deactivateModal.user.email}</strong>?</p>
              <p className="modal-note">The user will be banned and unable to log in. Their data will be preserved.</p>
              {actionError && <p className="modal-error">{actionError}</p>}
            </div>
            <div className="modal-footer">
              <button className="modal-cancel" onClick={() => setDeactivateModal(null)} disabled={actionLoading}>
                Cancel
              </button>
              <button className="modal-confirm orange" onClick={handleDeactivate} disabled={actionLoading}>
                {actionLoading ? 'Deactivating…' : 'Deactivate'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Delete Modal ── */}
      {deleteModal && (
        <div className="modal-overlay" onClick={() => setDeleteModal(null)}>
          <div className="modal-card" onClick={e => e.stopPropagation()}>
            <div className="modal-header red">
              <h2>Delete User</h2>
            </div>
            <div className="modal-body">
              <div className="modal-warning-box">
                <IconWarning />
                <span>This action is <strong>permanent</strong> and cannot be undone.</span>
              </div>
              <p>All data associated with <strong>{deleteModal.user.email}</strong> will be permanently removed.</p>
              {actionError && <p className="modal-error">{actionError}</p>}
            </div>
            <div className="modal-footer">
              <button className="modal-cancel" onClick={() => setDeleteModal(null)} disabled={actionLoading}>
                Cancel
              </button>
              <button className="modal-confirm red" onClick={handleDelete} disabled={actionLoading}>
                {actionLoading ? 'Deleting…' : 'Delete User'}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}

export default AdminUsers

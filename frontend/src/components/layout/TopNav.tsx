import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Bell, FileText, Box, Settings, LogOut, User, Map } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../../stores/authStore'
import { getAlertCounts } from '../../api/alerts'
import { clsx } from 'clsx'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/map',       label: 'Live Map',  icon: Map },
  { to: '/alerts',    label: 'Alerts',    icon: Bell },
  { to: '/reports',   label: 'Reports',   icon: FileText },
  { to: '/assets',    label: 'Assets',    icon: Box },
  { to: '/settings',  label: 'Settings',  icon: Settings },
]

export default function TopNav() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const { data: counts } = useQuery({
    queryKey: ['alert-counts'],
    queryFn: getAlertCounts,
    refetchInterval: 30_000,
  })

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 bg-navy-800 border-b border-navy-500 flex items-center px-4 gap-4 shrink-0">
      {/* Logo / Brand */}
      <div className="flex items-center gap-2.5 mr-4 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-steel-400 flex items-center justify-center shrink-0">
          <span className="text-white font-bold text-xs">ST</span>
        </div>
        <div className="hidden sm:block">
          <div className="text-sm font-bold text-white leading-none">SiteTrack</div>
          <div className="text-xs text-steel-300 leading-none mt-0.5">RTLS Intelligence</div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex items-center gap-1 flex-1">
        {NAV.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => clsx(isActive ? 'nav-link-active' : 'nav-link')}
          >
            <Icon size={15} />
            <span className="hidden md:inline">{label}</span>
            {label === 'Alerts' && counts && counts.total > 0 && (
              <span
                className={clsx(
                  'ml-1 px-1.5 py-0.5 rounded-full text-xs font-bold leading-none',
                  counts.critical > 0
                    ? 'bg-red-500 text-white'
                    : 'bg-amber-500 text-white'
                )}
              >
                {counts.total}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* User menu */}
      <div className="flex items-center gap-2 shrink-0">
        <div className="flex items-center gap-2 px-2 py-1 rounded-md bg-navy-700 border border-navy-500">
          <User size={14} className="text-steel-300" />
          <span className="text-sm text-steel-200 hidden sm:inline">{user?.username}</span>
          <span className="text-xs text-steel-300 hidden md:inline capitalize">({user?.role})</span>
        </div>
        <button
          onClick={handleLogout}
          className="p-2 hover:bg-navy-600 rounded-md text-steel-300 hover:text-white transition-colors"
          title="Logout"
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  )
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Lock, User } from 'lucide-react'
import { login } from '../api/auth'
import { useAuthStore } from '../stores/authStore'

export default function Login() {
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(username, password)
      setAuth(data.access_token, {
        id: 0,
        username: data.username,
        email: '',
        role: data.role,
        full_name: data.full_name,
        is_active: true,
      })
      navigate('/dashboard')
    } catch {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-steel-400 flex items-center justify-center mb-4">
            <span className="text-white font-bold text-2xl">ST</span>
          </div>
          <h1 className="text-xl font-bold text-white">SiteTrack</h1>
          <p className="text-sm text-steel-300 mt-1">Meridian Industrial — RTLS Demo</p>
        </div>

        {/* Card */}
        <div className="card p-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-steel-200 mb-1.5">Username</label>
              <div className="relative">
                <User size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-steel-300" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="input pl-9"
                  placeholder="admin"
                  required
                  autoFocus
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-steel-200 mb-1.5">Password</label>
              <div className="relative">
                <Lock size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-steel-300" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input pl-9"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            {error && (
              <p className="text-xs text-red-400 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full">
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 size={14} className="animate-spin" /> Signing in…
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-5 pt-4 border-t border-navy-500">
            <p className="text-xs text-steel-300 mb-2">Demo credentials:</p>
            <div className="space-y-1 font-mono text-xs text-steel-200">
              <div>admin / sitetrack-admin</div>
              <div>analyst / sitetrack-analyst</div>
              <div>viewer / sitetrack-viewer</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

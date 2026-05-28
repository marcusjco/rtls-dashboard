import { useQuery } from '@tanstack/react-query'
import { getNotificationRules } from '../api/alerts'
import { useAuthStore } from '../stores/authStore'
import { Mail, Phone, Webhook, Shield, Database, Bot, Users } from 'lucide-react'

export default function Settings() {
  const user = useAuthStore((s) => s.user)
  const { data: rules } = useQuery({ queryKey: ['notification-rules'], queryFn: getNotificationRules })
  const isAdmin = user?.role === 'admin'

  return (
    <div className="p-5 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-lg font-bold text-white">Settings</h1>
        <p className="text-xs text-steel-300">System configuration and administration</p>
      </div>

      {/* Current user */}
      <section className="card p-4 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Users size={14} className="text-steel-400" /> Current Session
        </h2>
        <div className="grid grid-cols-2 gap-3 text-xs">
          <div><span className="text-steel-300">Username:</span> <span className="text-white ml-2">{user?.username}</span></div>
          <div><span className="text-steel-300">Role:</span> <span className="text-white ml-2 capitalize">{user?.role}</span></div>
          <div><span className="text-steel-300">Full Name:</span> <span className="text-white ml-2">{user?.full_name || '—'}</span></div>
        </div>
      </section>

      {/* AI configuration */}
      <section className="card p-4 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Bot size={14} className="text-steel-400" /> AI Configuration
        </h2>
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between py-2 border-b border-navy-500">
            <span className="text-steel-300">Model</span>
            <span className="text-white font-mono">claude-sonnet-4-6</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-navy-500">
            <span className="text-steel-300">Context Window</span>
            <span className="text-white">20 messages</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-navy-500">
            <span className="text-steel-300">RAG Knowledge Base</span>
            <span className="badge-success">Loaded</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-steel-300">Tool Functions Available</span>
            <span className="text-white">12 tools</span>
          </div>
        </div>
      </section>

      {/* Database info */}
      <section className="card p-4 space-y-3">
        <h2 className="text-sm font-semibold text-white flex items-center gap-2">
          <Database size={14} className="text-steel-400" /> Database
        </h2>
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between py-2 border-b border-navy-500">
            <span className="text-steel-300">Type</span>
            <span className="text-white">SQLite</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-navy-500">
            <span className="text-steel-300">Database</span>
            <span className="text-white font-mono">sitetrack.db</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-steel-300">Dataset</span>
            <span className="text-white">Meridian Industrial — Synthetic RTLS Demo Data</span>
          </div>
        </div>
      </section>

      {/* Notification routing */}
      <section className="card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Shield size={14} className="text-steel-400" /> Notification Routing Rules
          </h2>
          {!isAdmin && <span className="text-xs text-steel-300">Admin only to edit</span>}
        </div>
        <p className="text-xs text-steel-300 leading-relaxed">
          These rules define how alerts are routed to team members. In production, real email/SMS/webhooks fire. In the demo, notifications are simulated and logged.
        </p>
        <div className="space-y-2">
          {rules?.map((rule) => (
            <div key={rule.id} className="flex items-center gap-3 px-3 py-2 bg-navy-800 rounded-md border border-navy-500 text-xs">
              {rule.channel === 'email' && <Mail size={13} className="text-steel-400 shrink-0" />}
              {rule.channel === 'sms' && <Phone size={13} className="text-steel-400 shrink-0" />}
              {rule.channel === 'webhook' && <Webhook size={13} className="text-steel-400 shrink-0" />}
              <div className="flex-1 min-w-0">
                <div className="text-white font-medium">{rule.label}</div>
                <div className="text-steel-300 truncate">{rule.destination}</div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {rule.alert_type && (
                  <span className="badge-info">{rule.alert_type.replace(/_/g, ' ')}</span>
                )}
                {rule.severity && (
                  <span className={rule.severity === 'critical' ? 'badge-critical' : 'badge-warning'}>
                    {rule.severity}
                  </span>
                )}
                <span className={rule.is_active ? 'text-green-400' : 'text-steel-300'}>
                  {rule.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Demo note */}
      <section className="border border-steel-400/20 rounded-lg p-4 bg-steel-400/5">
        <p className="text-xs text-steel-300 leading-relaxed">
          <span className="text-steel-200 font-semibold">Demo Mode:</span> This instance uses a synthetic SQLite database
          populated with realistic RTLS data for Meridian Industrial. In production, this connects
          to a live BLE positioning engine output via the real-time data pipeline.
        </p>
      </section>
    </div>
  )
}

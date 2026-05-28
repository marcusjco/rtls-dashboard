import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAlerts, resolveAlert, getNotificationRules } from '../api/alerts'
import { AlertTriangle, CheckCircle, Shield, Clock, Mail, Phone, Webhook, Filter, Bell } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { clsx } from 'clsx'
import type { Alert, AlertSeverity } from '../types'
import { useAuthStore } from '../stores/authStore'

function SeverityBadge({ severity }: { severity?: AlertSeverity }) {
  if (severity === 'critical') return <span className="badge-critical"><AlertTriangle size={9} /> Critical</span>
  if (severity === 'warning') return <span className="badge-warning"><AlertTriangle size={9} /> Warning</span>
  return <span className="badge-info">Info</span>
}

function AlertTypeLabel({ type }: { type?: string }) {
  const labels: Record<string, string> = {
    battery_low:            'Battery Low',
    long_dwell_inspection:  'QC Dwell Exceeded',
    stale_inventory:        'Stale Inventory',
    shipment_anomaly:       'Shipment Delay',
    tag_not_reporting:      'Tag Not Reporting',
  }
  return <span className="text-xs text-steel-300">{labels[type || ''] || type}</span>
}

function AlertRow({ alert, onResolve, canResolve }: {
  alert: Alert
  onResolve: (id: number) => void
  canResolve: boolean
}) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div
      className={clsx(
        'border-b border-navy-500 last:border-0 transition-colors',
        alert.is_resolved ? 'opacity-60' : '',
        alert.severity === 'critical' && !alert.is_resolved ? 'bg-red-950/10' : ''
      )}
    >
      <div
        className="px-4 py-3 flex items-start gap-3 cursor-pointer hover:bg-navy-700/50"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="mt-0.5 shrink-0">
          {alert.is_resolved
            ? <CheckCircle size={15} className="text-green-500" />
            : alert.severity === 'critical'
              ? <AlertTriangle size={15} className="text-red-500" />
              : <AlertTriangle size={15} className="text-amber-500" />
          }
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium text-white truncate">{alert.title}</span>
            <SeverityBadge severity={alert.severity as AlertSeverity} />
            {alert.notification_sent && (
              <span className="badge-info"><Mail size={9} /> Notified</span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-0.5 flex-wrap">
            <AlertTypeLabel type={alert.alert_type} />
            {alert.zone_name && (
              <span className="text-xs text-steel-300">Zone: {alert.zone_name}</span>
            )}
            <span className="text-xs text-steel-300 flex items-center gap-1">
              <Clock size={10} />
              {alert.created_at ? formatDistanceToNow(new Date(alert.created_at), { addSuffix: true }) : '—'}
            </span>
          </div>
        </div>
        {!alert.is_resolved && canResolve && (
          <button
            onClick={(e) => { e.stopPropagation(); onResolve(alert.id) }}
            className="btn-ghost text-xs shrink-0"
          >
            Resolve
          </button>
        )}
        {alert.is_resolved && (
          <span className="badge-success shrink-0">Resolved</span>
        )}
      </div>

      {expanded && (
        <div className="px-4 pb-3 ml-9 space-y-2 border-t border-navy-500/50 pt-3">
          <p className="text-sm text-steel-200 leading-relaxed">{alert.message}</p>
          {alert.is_resolved && alert.resolved_by && (
            <p className="text-xs text-steel-300">
              Resolved by <span className="text-white">{alert.resolved_by}</span>
              {alert.resolved_at && ` ${formatDistanceToNow(new Date(alert.resolved_at), { addSuffix: true })}`}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

function ChannelIcon({ channel }: { channel?: string }) {
  if (channel === 'email') return <Mail size={13} className="text-steel-400" />
  if (channel === 'sms') return <Phone size={13} className="text-steel-400" />
  return <Webhook size={13} className="text-steel-400" />
}

export default function Alerts() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const [severityFilter, setSeverityFilter] = useState<string>('')
  const [resolvedFilter, setResolvedFilter] = useState<string>('open')

  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts', severityFilter, resolvedFilter],
    queryFn: () => getAlerts({
      severity: severityFilter || undefined,
      is_resolved: resolvedFilter === 'open' ? false : resolvedFilter === 'resolved' ? true : undefined,
      days: 14,
    }),
    refetchInterval: 30_000,
  })

  const { data: rules } = useQuery({
    queryKey: ['notification-rules'],
    queryFn: getNotificationRules,
  })

  const resolveMutation = useMutation({
    mutationFn: (id: number) => resolveAlert(id, user?.username || 'unknown'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['alerts'] })
      qc.invalidateQueries({ queryKey: ['alert-counts'] })
    },
  })

  const canResolve = user?.role === 'admin' || user?.role === 'analyst'

  return (
    <div className="p-5 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">Alert Manager</h1>
          <p className="text-xs text-steel-300">
            {alerts?.filter((a) => !a.is_resolved).length ?? 0} open alerts
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Alert list */}
        <div className="xl:col-span-2 space-y-3">
          {/* Filters */}
          <div className="flex items-center gap-2 flex-wrap">
            <Filter size={13} className="text-steel-300" />
            {['open', 'resolved', 'all'].map((v) => (
              <button
                key={v}
                onClick={() => setResolvedFilter(v)}
                className={clsx('btn-ghost text-xs capitalize', resolvedFilter === v && 'bg-navy-600 text-white')}
              >
                {v}
              </button>
            ))}
            <div className="h-4 w-px bg-navy-500" />
            {['', 'critical', 'warning', 'info'].map((v) => (
              <button
                key={v}
                onClick={() => setSeverityFilter(v)}
                className={clsx('btn-ghost text-xs capitalize', severityFilter === v && 'bg-navy-600 text-white')}
              >
                {v || 'All Severity'}
              </button>
            ))}
          </div>

          <div className="card overflow-hidden">
            {isLoading && (
              <p className="p-4 text-xs text-steel-300">Loading alerts…</p>
            )}
            {!isLoading && (!alerts || alerts.length === 0) && (
              <p className="p-4 text-xs text-steel-300">No alerts match the current filter.</p>
            )}
            {alerts?.map((alert) => (
              <AlertRow
                key={alert.id}
                alert={alert}
                onResolve={(id) => resolveMutation.mutate(id)}
                canResolve={canResolve}
              />
            ))}
          </div>
        </div>

        {/* Notification routing panel */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Bell size={14} className="text-steel-400" /> Notification Routing
          </h2>
          <div className="card p-3">
            <p className="text-xs text-steel-300 mb-3 leading-relaxed">
              When alerts fire, the AI routes notifications to configured channels. In production, these send real emails, SMS, or webhooks.
            </p>
            <div className="space-y-2">
              {rules?.map((rule) => (
                <div key={rule.id} className="flex items-start gap-2 p-2 bg-navy-800 rounded-md border border-navy-500">
                  <ChannelIcon channel={rule.channel} />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-white truncate">{rule.label}</div>
                    <div className="text-xs text-steel-300 truncate">{rule.destination}</div>
                    <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                      {rule.alert_type ? (
                        <span className="badge-info text-xs">{rule.alert_type.replace(/_/g, ' ')}</span>
                      ) : (
                        <span className="badge-info text-xs">All types</span>
                      )}
                      {rule.severity && (
                        <SeverityBadge severity={rule.severity as AlertSeverity} />
                      )}
                    </div>
                  </div>
                  <div className={clsx('w-2 h-2 rounded-full mt-1 shrink-0', rule.is_active ? 'bg-green-500' : 'bg-navy-400')} />
                </div>
              ))}
            </div>
            <p className="text-xs text-steel-300/60 mt-3 italic">
              Simulation: notifications are logged but not sent.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

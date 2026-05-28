import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { getDashboard } from '../api/dashboard'
import { AlertTriangle, Tag, Battery, Activity, Clock, ChevronRight, ChevronDown, Package, Truck } from 'lucide-react'
import { formatDistanceToNow, format } from 'date-fns'
import { clsx } from 'clsx'
import type { ZoneSummary } from '../types'

function StatCard({ label, value, icon: Icon, accent, to }: {
  label: string
  value: number | string
  icon: React.ElementType
  accent?: string
  to: string
}) {
  return (
    <Link
      to={to}
      className="card p-4 flex items-center gap-3 hover:border-steel-400/40 hover:bg-navy-600 transition-colors group cursor-pointer"
    >
      <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center shrink-0', accent || 'bg-steel-400/20')}>
        <Icon size={18} className={accent ? 'text-white' : 'text-steel-400'} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xl font-bold text-white">{value}</div>
        <div className="text-xs text-steel-300">{label}</div>
      </div>
      <ChevronRight size={14} className="text-steel-400/40 group-hover:text-steel-400 transition-colors shrink-0" />
    </Link>
  )
}

const ZONE_TYPE_COLORS: Record<string, string> = {
  storage:    'bg-steel-400/20 text-steel-300',
  receiving:  'bg-blue-900/40 text-blue-300',
  shipping:   'bg-green-900/40 text-green-300',
  inspection: 'bg-amber-900/40 text-amber-300',
  transit:    'bg-purple-900/40 text-purple-300',
}

function ZoneCard({ zone }: { zone: ZoneSummary }) {
  const pct = zone.max_capacity ? Math.min((zone.active_tags / zone.max_capacity) * 100, 100) : 0
  const barColor = pct > 90 ? 'bg-red-500' : pct > 70 ? 'bg-amber-500' : 'bg-steel-400'
  const labelColor = ZONE_TYPE_COLORS[zone.zone_type] || 'bg-steel-400/20 text-steel-300'

  return (
    <div className="card p-3">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0 mr-2">
          <div className="text-xs font-semibold text-white leading-tight truncate">{zone.zone_name}</div>
          <div className={clsx('text-xs mt-1 px-1.5 py-0.5 rounded inline-block', labelColor)}>
            {zone.zone_type}
          </div>
        </div>
        <div className="text-lg font-bold text-white shrink-0">{zone.active_tags}</div>
      </div>
      {zone.max_capacity && (
        <div className="mt-2">
          <div className="h-1 bg-navy-500 rounded-full overflow-hidden">
            <div
              className={clsx('h-full rounded-full transition-all', barColor)}
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="text-xs text-steel-300 mt-0.5">{zone.active_tags} / {zone.max_capacity} capacity</div>
        </div>
      )}
    </div>
  )
}

function eventTypeLabel(type: string) {
  const map: Record<string, string> = {
    zone_entry:      'entered',
    zone_exit:       'exited',
    position_update: 'updated position in',
  }
  return map[type] || type
}

export default function Dashboard() {
  const [expandedEvent, setExpandedEvent] = useState<number | null>(null)

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: getDashboard,
    refetchInterval: 30_000,
  })

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <div className="text-steel-300 flex items-center gap-2">
        <Activity size={16} className="animate-pulse" /> Loading facility data…
      </div>
    </div>
  )

  if (error || !data) return (
    <div className="p-6 text-red-400">Failed to load dashboard. Check backend connection.</div>
  )

  const { stats, zones, recent_events } = data

  return (
    <div className="p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-white">Facility Dashboard</h1>
          <p className="text-xs text-steel-300">Meridian Industrial — Live Overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-steel-300">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Live
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-7 gap-3">
        <StatCard label="Active Tags" value={stats.total_active_tags} icon={Tag} to="/assets" />
        <StatCard
          label="Critical Alerts"
          value={stats.open_critical_alerts}
          icon={AlertTriangle}
          accent={stats.open_critical_alerts > 0 ? 'bg-red-600' : undefined}
          to="/alerts"
        />
        <StatCard
          label="Warnings"
          value={stats.open_warning_alerts}
          icon={AlertTriangle}
          accent={stats.open_warning_alerts > 0 ? 'bg-amber-600' : undefined}
          to="/alerts"
        />
        <StatCard label="Assets Tracked" value={stats.assets_tracked} icon={Package} to="/assets" />
        <StatCard label="Movements Today" value={stats.assets_in_transit_today} icon={Truck} to="/assets" />
        <StatCard
          label="Battery Warnings"
          value={stats.battery_warnings}
          icon={Battery}
          accent={stats.battery_warnings > 0 ? 'bg-amber-700' : undefined}
          to="/alerts"
        />
        <StatCard label="Total Alerts" value={stats.total_open_alerts} icon={Activity} to="/alerts" />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Zone overview */}
        <div className="xl:col-span-2">
          <h2 className="text-sm font-semibold text-white mb-3">Zone Occupancy</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {zones.map((z) => (
              <ZoneCard key={z.zone_id} zone={z} />
            ))}
          </div>
        </div>

        {/* Recent events */}
        <div>
          <h2 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Clock size={14} className="text-steel-400" /> Recent Events
          </h2>
          <div className="card divide-y divide-navy-500">
            {recent_events.length === 0 && (
              <p className="p-4 text-xs text-steel-300">No recent events.</p>
            )}
            {recent_events.map((ev, i) => {
              const isOpen = expandedEvent === i
              const displayName = ev.entity_name || ev.tag_uid
              return (
                <div key={i}>
                  <button
                    onClick={() => setExpandedEvent(isOpen ? null : i)}
                    className="w-full text-left px-3 py-2.5 hover:bg-navy-600 transition-colors group"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-xs text-white font-medium truncate flex-1">
                        <span className="text-steel-300 font-mono">{displayName}</span>
                        {' '}{eventTypeLabel(ev.event_type)}{' '}
                        <span className="text-steel-200">{ev.zone_name || 'unknown zone'}</span>
                        {ev.zone_code && (
                          <span className="text-steel-300/60 ml-1">({ev.zone_code})</span>
                        )}
                      </div>
                      {isOpen
                        ? <ChevronDown size={11} className="text-steel-400 shrink-0 mt-0.5" />
                        : <ChevronRight size={11} className="text-steel-400/40 group-hover:text-steel-400 shrink-0 mt-0.5 transition-colors" />
                      }
                    </div>
                    <div className="text-xs text-steel-300 mt-0.5">
                      {formatDistanceToNow(new Date(ev.timestamp_utc), { addSuffix: true })}
                    </div>
                  </button>
                  {isOpen && (
                    <div className="px-3 py-2 bg-navy-800 border-t border-navy-500 space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-steel-300">Tag UID</span>
                        <span className="text-white font-mono">{ev.tag_uid}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-steel-300">Event</span>
                        <span className="text-white capitalize">{ev.event_type.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-steel-300">Zone</span>
                        <span className="text-white">
                          {ev.zone_name || '—'}
                          {ev.zone_code && <span className="text-steel-300 ml-1">({ev.zone_code})</span>}
                        </span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-steel-300">Timestamp</span>
                        <span className="text-white">{format(new Date(ev.timestamp_utc), 'MMM d, HH:mm:ss')}</span>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

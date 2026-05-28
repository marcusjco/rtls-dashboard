import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getParts, getPartHistory } from '../api/assets'
import { Battery, MapPin, X, ChevronRight, Package } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { clsx } from 'clsx'
import type { Part, LocationHistoryPoint } from '../types'

const STATUS_LABELS: Record<string, string> = {
  received:       'Received',
  in_storage:     'In Storage',
  in_inspection:  'In Inspection',
  shipped:        'Shipped',
  in_transit:     'In Transit',
}

const STATUS_COLORS: Record<string, string> = {
  received:       'text-blue-400',
  in_storage:     'text-steel-300',
  in_inspection:  'text-amber-400',
  shipped:        'text-green-400',
  in_transit:     'text-purple-400',
}

function BatteryBadge({ level }: { level?: number }) {
  if (level === undefined || level === null) return <span className="text-steel-300 text-xs">—</span>
  const color = level <= 10 ? 'text-red-400' : level <= 20 ? 'text-amber-400' : 'text-green-400'
  return (
    <span className={clsx('text-xs flex items-center gap-1', color)}>
      <Battery size={11} />{Math.round(level)}%
    </span>
  )
}

function ZoneBadge({ name, code }: { name?: string; code?: string }) {
  if (!name) return <span className="text-xs text-steel-300">—</span>
  return (
    <span className="text-xs flex items-center gap-1 text-steel-200">
      <MapPin size={10} />
      {name}
      {code && <span className="text-steel-300/60">({code})</span>}
    </span>
  )
}

function HistoryPanel({
  assetCode,
  onClose,
}: {
  assetCode: string
  onClose: () => void
}) {
  const { data, isLoading } = useQuery({
    queryKey: ['asset-history', assetCode],
    queryFn: () => getPartHistory(assetCode, 48),
  })

  return (
    <div className="fixed right-80 top-14 bottom-0 w-72 bg-navy-800 border-l border-navy-500 flex flex-col z-10">
      <div className="px-4 py-3 border-b border-navy-500 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-white font-mono">{assetCode}</div>
          <div className="text-xs text-steel-300">Location History (48h)</div>
        </div>
        <button onClick={onClose} className="p-1 hover:bg-navy-600 rounded text-steel-300">
          <X size={14} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading && <p className="text-xs text-steel-300">Loading…</p>}
        {data?.map((ev: LocationHistoryPoint, i: number) => (
          <div key={i} className="flex items-start gap-2 text-xs">
            <div className="w-1.5 h-1.5 rounded-full bg-steel-400 mt-1.5 shrink-0" />
            <div>
              <div className="text-white capitalize">{ev.event_type.replace(/_/g, ' ')}</div>
              <div className="text-steel-300">
                {ev.zone_name || '—'}
                {ev.zone_code && <span className="text-steel-300/60 ml-1">({ev.zone_code})</span>}
              </div>
              <div className="text-steel-300/60">
                {formatDistanceToNow(new Date(ev.timestamp_utc), { addSuffix: true })}
              </div>
            </div>
          </div>
        ))}
        {data && data.length === 0 && (
          <p className="text-xs text-steel-300">No events in last 48h.</p>
        )}
      </div>
    </div>
  )
}

const CATEGORIES = [
  'Mechanical Components',
  'Electronic Assemblies',
  'Hydraulic Subassemblies',
  'Raw Material Stock',
  'Finished Goods',
]

export default function Assets() {
  const [selectedCode, setSelectedCode] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterCategory, setFilterCategory] = useState<string>('')

  const { data: assets, isLoading } = useQuery({
    queryKey: ['assets', filterStatus, filterCategory],
    queryFn: () => getParts({
      status: filterStatus || undefined,
      category: filterCategory || undefined,
    }),
  })

  return (
    <div className="p-5 space-y-5">
      <div>
        <h1 className="text-lg font-bold text-white">Asset Tracker</h1>
        <p className="text-xs text-steel-300">
          {assets ? `${assets.length.toLocaleString()} assets tracked` : 'Loading…'} — real-time RTLS data
        </p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="input py-1.5 text-xs w-44"
        >
          <option value="">All Statuses</option>
          {Object.entries(STATUS_LABELS).map(([val, label]) => (
            <option key={val} value={val}>{label}</option>
          ))}
        </select>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="input py-1.5 text-xs w-52"
        >
          <option value="">All Categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
        {(filterStatus || filterCategory) && (
          <button
            onClick={() => { setFilterStatus(''); setFilterCategory('') }}
            className="btn-ghost text-xs py-1"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Assets table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-steel-300 text-xs">Loading assets…</div>
        ) : (
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-navy-500 text-steel-300">
                <th className="text-left px-4 py-2.5 font-medium">Asset Code</th>
                <th className="text-left px-4 py-2.5 font-medium hidden md:table-cell">Category</th>
                <th className="text-left px-4 py-2.5 font-medium">Current Zone</th>
                <th className="text-left px-4 py-2.5 font-medium hidden sm:table-cell">Status</th>
                <th className="text-left px-4 py-2.5 font-medium">Battery</th>
                <th className="text-left px-4 py-2.5 font-medium hidden lg:table-cell">Tag</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {assets?.map((a: Part) => (
                <tr
                  key={a.id}
                  className={clsx(
                    'border-b border-navy-500/50 hover:bg-navy-700/50 cursor-pointer transition-colors',
                    selectedCode === a.asset_code && 'bg-navy-700'
                  )}
                  onClick={() => setSelectedCode(selectedCode === a.asset_code ? null : a.asset_code)}
                >
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <Package size={11} className="text-steel-400 shrink-0" />
                      <span className="font-mono font-medium text-white">{a.asset_code}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-steel-300 hidden md:table-cell">{a.category || '—'}</td>
                  <td className="px-4 py-2.5">
                    <ZoneBadge name={a.current_zone_name} code={a.current_zone_code} />
                  </td>
                  <td className="px-4 py-2.5 hidden sm:table-cell">
                    <span className={clsx('text-xs', STATUS_COLORS[a.status || ''] || 'text-steel-300')}>
                      {STATUS_LABELS[a.status || ''] || a.status || '—'}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <BatteryBadge level={a.tag?.battery_level} />
                  </td>
                  <td className="px-4 py-2.5 text-steel-300 font-mono hidden lg:table-cell">
                    {a.tag_uid}
                  </td>
                  <td className="px-4 py-2.5">
                    <ChevronRight size={12} className={clsx('transition-colors', selectedCode === a.asset_code ? 'text-steel-400' : 'text-steel-300/40')} />
                  </td>
                </tr>
              ))}
              {assets && assets.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-steel-300">
                    No assets match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {selectedCode && (
        <HistoryPanel
          assetCode={selectedCode}
          onClose={() => setSelectedCode(null)}
        />
      )}
    </div>
  )
}

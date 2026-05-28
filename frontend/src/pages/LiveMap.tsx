import { useEffect, useRef, useState, useCallback } from 'react'
import { Activity } from 'lucide-react'

const FLOOR_W = 60
const FLOOR_H = 40

const ZONES = [
  { name: 'Left Storage',   x: 0,  y: 0,  w: 9,  h: 34, color: '#6366f1', fill: 'rgba(99,102,241,0.12)' },
  { name: 'Upper Assembly', x: 9,  y: 0,  w: 38, h: 20, color: '#16a34a', fill: 'rgba(22,163,74,0.12)'  },
  { name: 'Right Storage',  x: 47, y: 0,  w: 13, h: 34, color: '#0d9488', fill: 'rgba(13,148,136,0.12)' },
  { name: 'Main Aisle',     x: 0,  y: 20, w: 60, h: 4,  color: '#94a3b8', fill: 'rgba(148,163,184,0.08)' },
  { name: 'Staging Area',   x: 0,  y: 24, w: 15, h: 12, color: '#d97706', fill: 'rgba(217,119,6,0.12)'  },
  { name: 'Assembly Line',  x: 15, y: 24, w: 32, h: 12, color: '#dc2626', fill: 'rgba(220,38,38,0.12)'  },
  { name: 'QA Station',     x: 47, y: 24, w: 13, h: 12, color: '#7c3aed', fill: 'rgba(124,58,237,0.12)' },
  { name: 'Receiving Dock', x: 0,  y: 36, w: 9,  h: 4,  color: '#ea580c', fill: 'rgba(234,88,12,0.18)'  },
  { name: 'Shipping Dock',  x: 51, y: 36, w: 9,  h: 4,  color: '#ea580c', fill: 'rgba(234,88,12,0.18)'  },
]

const ANCHORS = [
  { id: 'A1', x: 4,  y: 4  },
  { id: 'A2', x: 56, y: 4  },
  { id: 'A3', x: 4,  y: 36 },
  { id: 'A4', x: 56, y: 36 },
  { id: 'A5', x: 30, y: 20 },
]

// Simulated tags (in a real integration these come from the RTLS backend WebSocket)
const INITIAL_TAGS = [
  { id: 'TAG-001', label: 'Forklift Alpha',   type: 'Vehicle',   color: '#6366f1', x: 4,  y: 16, zone: 'Left Storage',  anchor: 'A1', rssi: -68 },
  { id: 'TAG-002', label: 'Pallet Cart 02',   type: 'Equipment', color: '#d97706', x: 28, y: 8,  zone: 'Upper Assembly', anchor: 'A5', rssi: -71 },
  { id: 'TAG-003', label: 'Shipping Cart 03', type: 'Equipment', color: '#dc2626', x: 52, y: 37, zone: 'Shipping Dock',  anchor: 'A4', rssi: -74 },
  { id: 'TAG-004', label: 'Rack Scanner 04',  type: 'Equipment', color: '#0d9488', x: 53, y: 14, zone: 'Right Storage',  anchor: 'A2', rssi: -70 },
  { id: 'TAG-005', label: 'Assembly Trolley', type: 'Vehicle',   color: '#16a34a', x: 30, y: 28, zone: 'Assembly Line',  anchor: 'A5', rssi: -66 },
  { id: 'TAG-006', label: 'Staging Forklift', type: 'Vehicle',   color: '#7c3aed', x: 7,  y: 28, zone: 'Staging Area',   anchor: 'A3', rssi: -69 },
]

interface TagState {
  id: string; label: string; type: string; color: string
  x: number; y: number; zone: string; anchor: string; rssi: number
}

function currentZone(x: number, y: number): string {
  for (const z of ZONES) {
    if (x >= z.x && x <= z.x + z.w && y >= z.y && y <= z.y + z.h) return z.name
  }
  return 'Floor'
}

function nearestAnchor(x: number, y: number): string {
  let best = 'A1', bestDist = Infinity
  for (const a of ANCHORS) {
    const d = Math.hypot(x - a.x, y - a.y)
    if (d < bestDist) { bestDist = d; best = a.id }
  }
  return best
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r); ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

export default function LiveMap() {
  const canvasRef  = useRef<HTMLCanvasElement>(null)
  const wrapRef    = useRef<HTMLDivElement>(null)
  const imgRef     = useRef<HTMLImageElement | null>(null)
  const scaleRef   = useRef(1)
  const tagsRef    = useRef<TagState[]>(INITIAL_TAGS.map(t => ({ ...t })))
  const hoverRef   = useRef<string | null>(null)
  const selRef     = useRef<string | null>(null)
  const [tags, setTags] = useState<TagState[]>(INITIAL_TAGS.map(t => ({ ...t })))
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [selId, setSelId] = useState<string | null>(null)
  const [tooltip, setTooltip] = useState<{ x: number; y: number; tag: TagState } | null>(null)

  // Load floor image
  useEffect(() => {
    const img = new Image()
    img.src = '/floor.png'
    img.onload = () => { imgRef.current = img; draw() }
    imgRef.current = img
  }, [])

  const px = (v: number) => v * scaleRef.current

  const draw = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    const img = imgRef.current
    if (img?.complete && img.naturalWidth > 0) {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
      ctx.fillStyle = 'rgba(0,0,0,0.2)'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
    } else {
      ctx.fillStyle = '#111d32'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
    }

    const s = scaleRef.current

    // Zones
    for (const z of ZONES) {
      ctx.fillStyle = z.fill
      ctx.fillRect(px(z.x), px(z.y), px(z.w), px(z.h))
      ctx.strokeStyle = z.color
      ctx.lineWidth = 1.5
      ctx.globalAlpha = 0.65
      ctx.strokeRect(px(z.x) + 0.75, px(z.y) + 0.75, px(z.w) - 1.5, px(z.h) - 1.5)
      ctx.globalAlpha = 1

      const fs = Math.max(9, Math.min(11, s * 1.7))
      ctx.font = `600 ${fs}px Inter,sans-serif`
      const tw = ctx.measureText(z.name).width
      const lx = px(z.x) + 6, ly = px(z.y) + 6
      const ph = fs + 6, pw = tw + 12
      ctx.fillStyle = 'rgba(10,18,30,0.75)'
      roundRect(ctx, lx, ly, pw, ph, 3)
      ctx.fill()
      ctx.fillStyle = '#e2e8f0'
      ctx.fillText(z.name, lx + 6, ly + ph - 5)
    }

    // Anchors
    for (const a of ANCHORS) {
      const ax = px(a.x), ay = px(a.y)
      ctx.strokeStyle = '#6366f1'; ctx.lineWidth = 1; ctx.globalAlpha = 0.2
      ctx.beginPath(); ctx.arc(ax, ay, 14, 0, Math.PI * 2); ctx.stroke()
      ctx.globalAlpha = 1
      ctx.fillStyle = '#4338ca'
      ctx.beginPath(); ctx.arc(ax, ay, 5, 0, Math.PI * 2); ctx.fill()
      ctx.fillStyle = '#fff'
      ctx.beginPath(); ctx.arc(ax, ay, 2, 0, Math.PI * 2); ctx.fill()
      ctx.font = `bold ${Math.max(8, s * 1.2)}px sans-serif`
      ctx.fillStyle = 'rgba(255,255,255,0.85)'
      ctx.fillText(a.id, ax + 7, ay - 4)
    }

    // Tags
    for (const t of tagsRef.current) {
      const tx = px(t.x), ty = px(t.y)
      const isHov = hoverRef.current === t.id
      const isSel = selRef.current  === t.id
      const r = isSel ? 9 : isHov ? 8 : 6

      if (isSel || isHov) {
        ctx.strokeStyle = t.color; ctx.lineWidth = 2; ctx.globalAlpha = 0.3
        ctx.beginPath(); ctx.arc(tx, ty, r + 8, 0, Math.PI * 2); ctx.stroke()
        ctx.globalAlpha = 1
      }
      ctx.fillStyle = 'rgba(255,255,255,0.9)'
      ctx.beginPath(); ctx.arc(tx, ty, r + 2, 0, Math.PI * 2); ctx.fill()
      ctx.fillStyle = t.color
      ctx.beginPath(); ctx.arc(tx, ty, r, 0, Math.PI * 2); ctx.fill()

      const short = t.id.slice(-3)
      const fs = Math.max(8, s * 1.4)
      ctx.font = `bold ${fs}px sans-serif`
      const lw = ctx.measureText(short).width
      ctx.fillStyle = 'rgba(10,18,30,0.85)'
      roundRect(ctx, tx + r + 3, ty - fs / 2 - 2, lw + 8, fs + 4, 3)
      ctx.fill()
      ctx.fillStyle = '#fff'
      ctx.fillText(short, tx + r + 7, ty + fs / 2 - 1)
    }
  }, [])

  const resize = useCallback(() => {
    const canvas = canvasRef.current, wrap = wrapRef.current
    if (!canvas || !wrap) return
    const maxW = wrap.clientWidth - 24, maxH = wrap.clientHeight - 24
    scaleRef.current = Math.min(maxW / FLOOR_W, maxH / FLOOR_H)
    canvas.width  = Math.round(FLOOR_W * scaleRef.current)
    canvas.height = Math.round(FLOOR_H * scaleRef.current)
    draw()
  }, [draw])

  useEffect(() => {
    resize()
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [resize])

  // Simulate tag movement
  useEffect(() => {
    let phase = 0
    const interval = setInterval(() => {
      phase += 0.025
      tagsRef.current = tagsRef.current.map((t, i) => {
        const nx = Math.max(0.5, Math.min(FLOOR_W - 0.5, t.x + Math.sin(phase + i * 1.3) * 0.18))
        const ny = Math.max(0.5, Math.min(FLOOR_H - 0.5, t.y + Math.cos(phase + i * 0.9) * 0.12))
        return { ...t, x: nx, y: ny, zone: currentZone(nx, ny), anchor: nearestAnchor(nx, ny) }
      })
      setTags([...tagsRef.current])
      draw()
    }, 250)
    return () => clearInterval(interval)
  }, [draw])

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect()
    const mx = (e.clientX - rect.left) / scaleRef.current
    const my = (e.clientY - rect.top)  / scaleRef.current
    const hit = tagsRef.current.find(t => Math.hypot(t.x - mx, t.y - my) < 10 / scaleRef.current) ?? null
    hoverRef.current = hit?.id ?? null
    setHoverId(hit?.id ?? null)
    if (hit) setTooltip({ x: e.clientX, y: e.clientY, tag: hit })
    else     setTooltip(null)
    draw()
  }

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect()
    const mx = (e.clientX - rect.left) / scaleRef.current
    const my = (e.clientY - rect.top)  / scaleRef.current
    const hit = tagsRef.current.find(t => Math.hypot(t.x - mx, t.y - my) < 10 / scaleRef.current) ?? null
    selRef.current  = hit ? (selRef.current === hit.id ? null : hit.id) : null
    setSelId(selRef.current)
    draw()
  }

  return (
    <div className="flex h-full overflow-hidden">

      {/* Left: tag list */}
      <div className="w-52 shrink-0 bg-navy-800 border-r border-navy-500 flex flex-col overflow-hidden">
        <div className="px-3 py-2.5 border-b border-navy-500 text-xs font-semibold text-steel-300 uppercase tracking-wider bg-navy-900">
          Active Tags
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {tags.map(t => (
            <div
              key={t.id}
              onClick={() => { selRef.current = selRef.current === t.id ? null : t.id; setSelId(selRef.current); draw() }}
              onMouseEnter={() => { hoverRef.current = t.id; setHoverId(t.id); draw() }}
              onMouseLeave={() => { hoverRef.current = null; setHoverId(null); draw() }}
              className={`rounded-lg p-2 cursor-pointer border transition-colors ${
                selId === t.id   ? 'bg-navy-600 border-steel-400' :
                hoverId === t.id ? 'bg-navy-700 border-navy-400'  :
                                   'bg-navy-700 border-navy-500 hover:border-navy-400'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: t.color }} />
                <span className="text-xs font-bold text-white font-mono">{t.id}</span>
                <span className="text-xs text-steel-300 ml-auto">{t.type}</span>
              </div>
              <div className="text-xs font-medium text-steel-100 truncate">{t.label}</div>
              <div className="text-xs text-steel-400 mt-0.5">{t.zone}</div>
              <div className="text-xs text-steel-300/60">{t.rssi} dBm · {t.anchor}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Center: floor plan */}
      <div className="flex-1 flex flex-col overflow-hidden bg-navy-900">
        <div className="px-4 py-2.5 border-b border-navy-500 flex items-center justify-between bg-navy-800">
          <div>
            <span className="text-sm font-semibold text-white">Facility Floor Plan</span>
            <span className="text-xs text-steel-300 ml-3">Meridian Industrial · 60 × 40 m</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-steel-300">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-steel-400" />
              Anchor
            </div>
            <div className="flex items-center gap-1.5">
              <Activity size={11} className="text-green-400 animate-pulse" />
              Live · 4 Hz
            </div>
          </div>
        </div>
        <div ref={wrapRef} className="flex-1 flex items-center justify-center p-3 overflow-hidden">
          <canvas
            ref={canvasRef}
            style={{ borderRadius: 10, boxShadow: '0 4px 24px rgba(0,0,0,0.4)', cursor: 'crosshair' }}
            onMouseMove={handleMouseMove}
            onMouseLeave={() => { hoverRef.current = null; setHoverId(null); setTooltip(null); draw() }}
            onClick={handleClick}
          />
        </div>
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          style={{ position: 'fixed', left: tooltip.x + 16, top: tooltip.y - 10, pointerEvents: 'none', zIndex: 200 }}
          className="bg-navy-700 border border-navy-400 rounded-lg px-3 py-2 text-xs text-steel-100 shadow-xl"
        >
          <div className="font-bold text-white mb-1">{tooltip.tag.label}</div>
          <div>{tooltip.tag.id} · {tooltip.tag.type}</div>
          <div className="text-steel-300">Zone: {tooltip.tag.zone}</div>
          <div className="text-steel-300">Position: {tooltip.tag.x.toFixed(1)}m, {tooltip.tag.y.toFixed(1)}m</div>
          <div className="text-steel-300">RSSI: {tooltip.tag.rssi} dBm · {tooltip.tag.anchor}</div>
        </div>
      )}
    </div>
  )
}

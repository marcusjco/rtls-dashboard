import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getReportTypes, getReports, generateReport } from '../api/reports'
import { FileText, Download, Loader2, Calendar, ChevronRight, Play } from 'lucide-react'
import { formatDistanceToNow, subDays, format } from 'date-fns'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { clsx } from 'clsx'
import type { Report } from '../types'
import { useAuthStore } from '../stores/authStore'

export default function Reports() {
  const user = useAuthStore((s) => s.user)
  const qc = useQueryClient()
  const canGenerate = user?.role === 'admin' || user?.role === 'analyst'

  const [selectedType, setSelectedType] = useState<string>('')
  const [dateFrom, setDateFrom] = useState(format(subDays(new Date(), 7), 'yyyy-MM-dd'))
  const [dateTo, setDateTo] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [viewing, setViewing] = useState<Report | null>(null)

  const downloadPdf = async (reportId: number, reportName: string) => {
    const token = localStorage.getItem('token')
    const res = await fetch(`/api/reports/${reportId}/download/pdf`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${reportName.replace(/ /g, '_')}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const { data: reportTypes } = useQuery({ queryKey: ['report-types'], queryFn: getReportTypes })
  const { data: reports } = useQuery({ queryKey: ['reports'], queryFn: getReports })

  const generateMutation = useMutation({
    mutationFn: () =>
      generateReport({
        report_type: selectedType,
        date_from: new Date(dateFrom).toISOString(),
        date_to: new Date(dateTo).toISOString(),
      }),
    onSuccess: (report) => {
      qc.invalidateQueries({ queryKey: ['reports'] })
      setViewing(report)
    },
  })

  return (
    <div className="p-5 space-y-5">
      <div>
        <h1 className="text-lg font-bold text-white">Report Generator</h1>
        <p className="text-xs text-steel-300">AI-generated operational reports from facility data</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
        {/* Left: Template selector + generate */}
        <div className="space-y-4">
          <div className="card p-4 space-y-3">
            <h3 className="text-sm font-semibold text-white">Report Type</h3>
            <div className="space-y-1.5">
              {reportTypes?.map((rt) => (
                <button
                  key={rt.id}
                  onClick={() => setSelectedType(rt.id)}
                  className={clsx(
                    'w-full text-left px-3 py-2.5 rounded-md border transition-colors',
                    selectedType === rt.id
                      ? 'bg-steel-400/20 border-steel-400/50 text-white'
                      : 'bg-navy-800 border-navy-500 text-steel-200 hover:border-steel-400/30 hover:bg-navy-700'
                  )}
                >
                  <div className="text-xs font-medium">{rt.label}</div>
                  <div className="text-xs text-steel-300 mt-0.5">{rt.description}</div>
                </button>
              ))}
            </div>
          </div>

          {selectedType && (
            <div className="card p-4 space-y-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <Calendar size={13} className="text-steel-400" /> Date Range
              </h3>
              <div>
                <label className="text-xs text-steel-300 mb-1 block">From</label>
                <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} className="input text-xs" />
              </div>
              <div>
                <label className="text-xs text-steel-300 mb-1 block">To</label>
                <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} className="input text-xs" />
              </div>
              {canGenerate ? (
                <button
                  onClick={() => generateMutation.mutate()}
                  disabled={generateMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {generateMutation.isPending ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      Generating with AI…
                    </>
                  ) : (
                    <>
                      <Play size={13} />
                      Generate Report
                    </>
                  )}
                </button>
              ) : (
                <p className="text-xs text-steel-300 text-center">Analysts and admins can generate reports.</p>
              )}
              {generateMutation.isPending && (
                <p className="text-xs text-steel-300 text-center">
                  Claude is querying facility data and writing the report…
                </p>
              )}
            </div>
          )}

          {/* Previous reports */}
          {reports && reports.length > 0 && (
            <div className="card p-3 space-y-2">
              <h3 className="text-xs font-semibold text-steel-300 uppercase tracking-wider">Previous Reports</h3>
              {reports.slice(0, 8).map((r: Report) => (
                <button
                  key={r.id}
                  onClick={() => setViewing(r)}
                  className={clsx(
                    'w-full text-left px-2.5 py-2 rounded-md border transition-colors flex items-center gap-2',
                    viewing?.id === r.id
                      ? 'bg-steel-400/20 border-steel-400/50'
                      : 'bg-navy-800 border-navy-500 hover:bg-navy-700'
                  )}
                >
                  <FileText size={12} className="text-steel-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-white truncate">{r.report_name}</div>
                    <div className="text-xs text-steel-300">
                      {r.created_at ? formatDistanceToNow(new Date(r.created_at), { addSuffix: true }) : '—'}
                    </div>
                  </div>
                  <ChevronRight size={11} className="text-steel-300 shrink-0" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Report viewer */}
        <div className="xl:col-span-2">
          {!viewing && !generateMutation.isPending && (
            <div className="card h-full flex items-center justify-center p-12">
              <div className="text-center space-y-2">
                <FileText size={36} className="text-steel-400/40 mx-auto" />
                <p className="text-sm text-steel-300">Select a report type and click Generate</p>
                <p className="text-xs text-steel-300/60">Claude will query the database and write the report</p>
              </div>
            </div>
          )}

          {generateMutation.isPending && (
            <div className="card h-64 flex items-center justify-center">
              <div className="text-center space-y-3">
                <Loader2 size={24} className="animate-spin text-steel-400 mx-auto" />
                <p className="text-sm text-steel-300">Claude is generating your report…</p>
                <p className="text-xs text-steel-300/60">Querying facility data and writing analysis</p>
              </div>
            </div>
          )}

          {viewing && !generateMutation.isPending && (
            <div className="card overflow-hidden">
              <div className="px-4 py-3 border-b border-navy-500 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">{viewing.report_name}</h3>
                  <p className="text-xs text-steel-300">
                    By {viewing.generated_by}
                    {viewing.created_at && ` · ${formatDistanceToNow(new Date(viewing.created_at), { addSuffix: true })}`}
                  </p>
                </div>
                {viewing.file_path && (
                  <button
                    onClick={() => downloadPdf(viewing.id, viewing.report_name)}
                    className="btn-secondary text-xs flex items-center gap-1.5"
                  >
                    <Download size={12} /> PDF
                  </button>
                )}
              </div>
              <div className="p-5 overflow-y-auto max-h-[calc(100vh-260px)]">
                <div className="prose prose-invert prose-sm max-w-none [&_h1]:text-white [&_h1]:text-lg [&_h2]:text-steel-300 [&_h2]:text-base [&_h3]:text-steel-200 [&_strong]:text-white [&_table]:text-xs [&_th]:text-steel-300 [&_code]:bg-navy-800 [&_code]:px-1 [&_code]:rounded">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {viewing.content_md || '_No content available._'}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

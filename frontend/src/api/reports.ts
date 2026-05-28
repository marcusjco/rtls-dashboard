import api from './client'
import type { Report, ReportType } from '../types'

export const getReportTypes = (): Promise<ReportType[]> =>
  api.get('/reports/types').then((r) => r.data)

export const getReports = (): Promise<Report[]> =>
  api.get('/reports').then((r) => r.data)

export const generateReport = (data: {
  report_type: string
  report_name?: string
  date_from: string
  date_to: string
}): Promise<Report> => api.post('/reports/generate', data).then((r) => r.data)

export const downloadReportPdf = (id: number): void => {
  const token = localStorage.getItem('token')
  window.open(`/api/reports/${id}/download/pdf?token=${token}`, '_blank')
}

import api from './client'
import type { DashboardSummary } from '../types'

export const getDashboard = (): Promise<DashboardSummary> =>
  api.get('/dashboard/summary').then((r) => r.data)

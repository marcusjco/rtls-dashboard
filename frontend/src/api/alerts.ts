import api from './client'
import type { Alert, AlertCounts, NotificationRule } from '../types'

export const getAlerts = (params?: {
  severity?: string
  is_resolved?: boolean
  alert_type?: string
  days?: number
}): Promise<Alert[]> => api.get('/alerts', { params }).then((r) => r.data)

export const getAlertCounts = (): Promise<AlertCounts> =>
  api.get('/alerts/counts').then((r) => r.data)

export const resolveAlert = (id: number, resolvedBy: string): Promise<Alert> =>
  api.patch(`/alerts/${id}/resolve`, { resolved_by: resolvedBy }).then((r) => r.data)

export const getNotificationRules = (): Promise<NotificationRule[]> =>
  api.get('/alerts/notification-rules').then((r) => r.data)

export const createNotificationRule = (data: {
  alert_type?: string
  severity?: string
  channel: string
  destination: string
  label: string
}): Promise<NotificationRule> =>
  api.post('/alerts/notification-rules', data).then((r) => r.data)

export const deleteNotificationRule = (id: number): Promise<void> =>
  api.delete(`/alerts/notification-rules/${id}`)

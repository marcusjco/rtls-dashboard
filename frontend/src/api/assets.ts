import api from './client'
import type { Part, LocationHistoryPoint } from '../types'

export const getParts = (params?: { status?: string; category?: string }): Promise<Part[]> =>
  api.get('/assets/assets', { params }).then((r) => r.data)

export const getPartHistory = (
  partCode: string,
  hours = 48
): Promise<LocationHistoryPoint[]> =>
  api.get(`/assets/assets/${partCode}/history`, { params: { hours } }).then((r) => r.data)

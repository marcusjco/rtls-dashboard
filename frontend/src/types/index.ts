export interface User {
  id: number
  username: string
  email: string
  role: 'admin' | 'analyst' | 'viewer'
  full_name?: string
  is_active: boolean
}

export interface TagInfo {
  tag_uid: string
  battery_level?: number
  last_seen?: string
}

export interface Part {
  id: number
  asset_code: string
  tag_uid: string
  category?: string
  status?: string
  current_zone_id?: number
  current_zone_name?: string
  current_zone_code?: string
  first_seen?: string
  tag?: TagInfo
}

export interface LocationHistoryPoint {
  zone_id?: number
  zone_name?: string
  zone_code?: string
  event_type: string
  x_pos?: number
  y_pos?: number
  velocity_fps?: number
  timestamp_utc: string
}

export type AlertSeverity = 'critical' | 'warning' | 'info'

export interface Alert {
  id: number
  alert_type?: string
  severity?: AlertSeverity
  tag_uid?: string
  zone_id?: number
  zone_name?: string
  entity_name?: string
  title?: string
  message?: string
  is_resolved: boolean
  resolved_by?: string
  resolved_at?: string
  notification_sent: boolean
  notification_channel?: string
  created_at?: string
}

export interface AlertCounts {
  critical: number
  warning: number
  info: number
  total: number
}

export interface NotificationRule {
  id: number
  alert_type?: string
  severity?: string
  channel?: string
  destination?: string
  label?: string
  is_active: boolean
}

export interface ZoneSummary {
  zone_id: number
  zone_name: string
  zone_type: string
  is_restricted: boolean
  active_tags: number
  max_capacity?: number
}

export interface StatsBar {
  total_active_tags: number
  open_critical_alerts: number
  open_warning_alerts: number
  total_open_alerts: number
  assets_tracked: number
  assets_in_transit_today: number
  battery_warnings: number
}

export interface RecentEvent {
  tag_uid: string
  entity_name?: string
  zone_name?: string
  zone_code?: string
  event_type: string
  timestamp_utc: string
}

export interface DashboardSummary {
  stats: StatsBar
  zones: ZoneSummary[]
  recent_events: RecentEvent[]
}

export interface Report {
  id: number
  report_name?: string
  report_type?: string
  generated_by?: string
  date_from?: string
  date_to?: string
  content_md?: string
  file_path?: string
  created_at?: string
}

export interface ReportType {
  id: string
  label: string
  description: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

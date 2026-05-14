export type Zone = 'main' | 'zone2'

export type ThemeName =
  | 'gold' | 'blue' | 'red' | 'green'
  | 'olive' | 'violet' | 'purple' | 'pink' | 'orange'

export interface Theme {
  label: string
  accent: string
  accentDim: string
}

export interface NowPlaying {
  song?: string
  artist?: string
  station?: string
  image_url?: string
}

export interface SurroundModeEntry {
  id: number
  category: string
  command: string
  display_name: string
  active?: boolean
}

export interface ThemeConfig {
  base: ThemeName
  overrides: Record<string, string>
}

export interface ReceiverState {
  surround_mode_list?: SurroundModeEntry[]
  connected: boolean
  discovering?: boolean
  power?: boolean
  volume?: number
  volume_max?: number
  muted?: boolean
  source?: string
  surround_mode?: string
  channel_volumes?: Record<string, number>
  speaker_calibration?: Record<string, number>
  dynamic_eq?: boolean
  dynamic_volume?: string
  multeq?: string
  ref_level_offset?: number
  sleep_timer?: number
  eco_mode?: string
  tone_control?: boolean
  bass?: number
  treble?: number
  subwoofer_level?: number
  now_playing?: NowPlaying
  play_state?: 'play' | 'pause' | 'stop'
  stream_quality?: string
  z2_power?: boolean
  z2_volume?: number
  z2_muted?: boolean
  z2_source?: string
  source_name?: string
  z2_source_name?: string
  heos_source?: string
  theme_config?: ThemeConfig
}

export interface SourceEntry {
  id: string
  name: string
}

export interface DeviceInfo {
  device_name?: string
  zone1_name?: string
  zone2_name?: string
  theme?: ThemeName
  receiver_ip?: string
  discovering?: boolean
  channel_names?: Record<string, string>
  source_name_map?: Record<string, string>
  sources?: string[]
}

export interface ApiResponse {
  ok: boolean
  status: number
  error?: string
}

export type PostFn = (path: string, body?: Record<string, unknown>) => Promise<ApiResponse>

export type SendCommandFn = (command: string) => void

export interface SoundModeEntry {
  speakers: string
  description: string
  bestFor: string
  notes?: string
}

import { useState } from 'react'
import ThemePicker from './ThemePicker'

export default function StatusBar({ deviceName, state, wsConnected, receiverIp, currentTheme, onThemeChange, activeZone = 'main' }) {
  const [expanded, setExpanded] = useState(false)
  const androidTv = state?.android_tv || {}
  const isAndroidTv = activeZone === 'androidtv'
  const telnetOk = state?.connected
  const androidTvOk = androidTv.connected
  const power = state?.power
  const ok = (isAndroidTv ? androidTvOk : telnetOk) && wsConnected
  const title = isAndroidTv ? (androidTv.device_name || androidTv.device_info?.model || 'Android TV') : deviceName

  return (
    <div className="pt-5 pb-3">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-lg font-bold text-denon-text tracking-tight">{title}</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className={`${ok ? 'badge-green' : 'badge-red'} cursor-pointer hover:brightness-110 transition-all`}
          >
            <span className={`w-2 h-2 rounded-full ${ok ? 'bg-denon-green animate-pulse' : 'bg-denon-red'}`} />
            {ok ? 'Connected' : 'Disconnected'}
            <svg className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
          </button>
          <ThemePicker currentTheme={currentTheme} onThemeChange={onThemeChange} />
        </div>
      </div>

      {expanded && (
        <div className="mt-2 p-3 bg-denon-surface/50 rounded-xl border border-denon-border/50 text-xs space-y-1.5 fade-in">
          <div className="flex justify-between">
            <span className="text-denon-muted">Receiver IP</span>
            <span className="text-denon-text font-mono">{receiverIp || '-'}</span>
          </div>
          {isAndroidTv && (
            <div className="flex justify-between">
              <span className="text-denon-muted">Android TV IP</span>
              <span className="text-denon-text font-mono">{androidTv.host || '-'}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-denon-muted">Telnet Connection</span>
            <span className={telnetOk ? 'text-denon-green' : 'text-denon-red'}>
              {telnetOk ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {isAndroidTv && (
            <div className="flex justify-between">
              <span className="text-denon-muted">Android TV Remote</span>
              <span className={androidTvOk ? 'text-denon-green' : 'text-denon-red'}>
                {androidTvOk ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-denon-muted">WebSocket</span>
            <span className={wsConnected ? 'text-denon-green' : 'text-denon-red'}>
              {wsConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-denon-muted">Power State</span>
            <span className="text-denon-text">{power === true ? 'On' : power === false ? 'Standby' : 'Unknown'}</span>
          </div>
          {isAndroidTv && androidTv.current_app && (
            <div className="flex justify-between gap-3">
              <span className="text-denon-muted">Current App</span>
              <span className="text-denon-text truncate">{androidTv.current_app}</span>
            </div>
          )}
          {state?.surround_mode && (
            <div className="flex justify-between">
              <span className="text-denon-muted">Surround Mode</span>
              <span className="text-denon-text">{state.surround_mode}</span>
            </div>
          )}
          {state?.eco_mode && (
            <div className="flex justify-between">
              <span className="text-denon-muted">Eco Mode</span>
              <span className="text-denon-text">{state.eco_mode}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

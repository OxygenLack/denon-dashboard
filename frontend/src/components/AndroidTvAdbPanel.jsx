import { useEffect, useMemo, useRef, useState } from 'react'

function TinyButton({ children, className = '', ...props }) {
  return (
    <button
      type="button"
      className={`px-3 py-2 rounded-xl text-xs font-semibold transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

function statusClass(status) {
  if (status?.connected) return 'badge-green'
  if (status?.enabled === false || status?.state === 'unauthorized') return 'badge-muted'
  return 'badge-red'
}

function formatKb(value) {
  if (!Number.isFinite(value)) return '-'
  const gb = value / 1024 / 1024
  if (gb >= 1) return `${gb.toFixed(1)} GB`
  return `${Math.round(value / 1024)} MB`
}

export default function AndroidTvAdbPanel({ tv }) {
  const [host, setHost] = useState(tv?.host || '')
  const [connectPort, setConnectPort] = useState(5555)
  const [pairPort, setPairPort] = useState('')
  const [pairCode, setPairCode] = useState('')
  const [status, setStatus] = useState(null)
  const [apps, setApps] = useState([])
  const [query, setQuery] = useState('')
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [detailsOpen, setDetailsOpen] = useState(false)
  const [screenshotUrl, setScreenshotUrl] = useState(null)
  const [continuousScreenshot, setContinuousScreenshot] = useState(false)
  const [powerConfirm, setPowerConfirm] = useState(null)
  const [powerCountdown, setPowerCountdown] = useState(10)
  const [uninstallConfirm, setUninstallConfirm] = useState(null)
  const [uninstallCountdown, setUninstallCountdown] = useState(10)
  const screenshotRef = useRef(null)
  const screenshotBusyRef = useRef(false)

  const connected = Boolean(status?.connected)
  const current = status?.current_app || {}
  const diagnostics = status?.diagnostics || {}
  const storage = diagnostics.storage
  const statusLabel = status?.enabled === false ? 'ADB Disabled' : connected ? 'ADB Connected' : status?.state ? `ADB ${status.state}` : 'ADB Disconnected'

  useEffect(() => {
    loadStatus()
    return () => {
      if (screenshotRef.current) URL.revokeObjectURL(screenshotRef.current)
    }
  }, [])

  useEffect(() => {
    if (!tv?.host || host) return
    setHost(tv.host)
  }, [tv?.host, host])

  useEffect(() => {
    if (!powerConfirm) return undefined
    if (powerCountdown <= 0) {
      const action = powerConfirm
      setPowerConfirm(null)
      setPowerCountdown(10)
      runPower(action)
      return undefined
    }
    const timer = setTimeout(() => setPowerCountdown(value => value - 1), 1000)
    return () => clearTimeout(timer)
  }, [powerConfirm, powerCountdown])

  useEffect(() => {
    if (!uninstallConfirm) return undefined
    if (uninstallCountdown <= 0) {
      const app = uninstallConfirm
      setUninstallConfirm(null)
      setUninstallCountdown(10)
      uninstallApp(app)
      return undefined
    }
    const timer = setTimeout(() => setUninstallCountdown(value => value - 1), 1000)
    return () => clearTimeout(timer)
  }, [uninstallConfirm, uninstallCountdown])

  useEffect(() => {
    if (!continuousScreenshot || !connected) return undefined
    let cancelled = false
    const tick = async () => {
      if (cancelled || screenshotBusyRef.current) return
      await refreshScreenshot({ trackBusy: false })
    }
    tick()
    const timer = setInterval(tick, 1500)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [continuousScreenshot, connected])

  const request = async (path, body, method = 'POST', options = {}) => {
    const trackBusy = options.trackBusy !== false
    if (trackBusy) setBusy(path)
    setError(null)
    try {
      const res = await fetch(`/api/v1/androidtv/adb${path}`, {
        method,
        headers: method === 'POST' ? { 'Content-Type': 'application/json' } : undefined,
        body: method === 'POST' ? JSON.stringify(body || {}) : undefined,
      })
      if (options.blob) {
        if (!res.ok) {
          const message = await res.text().catch(() => res.statusText)
          throw new Error(message || `HTTP ${res.status}`)
        }
        return await res.blob()
      }
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`)
      return data
    } catch (err) {
      setError(err.message)
      return null
    } finally {
      if (trackBusy) setBusy(null)
    }
  }

  const loadStatus = async () => {
    const data = await request('/status', null, 'GET')
    if (!data) return
    setStatus(data)
    if (data.host && !host) setHost(data.host)
    if (data.port) setConnectPort(data.port)
  }

  const connect = async () => {
    const data = await request('/connect', { host: host.trim(), port: Number(connectPort) || 5555 })
    if (data) {
      setStatus(data)
      if (data.connected) setDetailsOpen(false)
      await loadApps()
    }
  }

  const pair = async () => {
    const data = await request('/pair', {
      host: host.trim(),
      port: Number(pairPort),
      code: pairCode.trim().toUpperCase(),
    })
    if (data?.ok) {
      setPairCode('')
      await connect()
    }
  }

  const disconnect = async () => {
    const data = await request('/disconnect')
    if (data) {
      setStatus(data)
      setDetailsOpen(true)
      setApps([])
      clearScreenshot()
    }
  }

  const loadApps = async () => {
    const data = await request('/apps', null, 'GET')
    if (data?.apps) setApps(data.apps)
  }

  const refreshCurrent = async () => {
    const data = await request('/current-app', null, 'GET')
    if (data) setStatus(prev => ({ ...(prev || {}), current_app: data }))
  }

  const refreshDiagnostics = async () => {
    const data = await request('/diagnostics', null, 'GET')
    if (data) setStatus(prev => ({ ...(prev || {}), diagnostics: data }))
  }

  const refreshScreenshot = async (options = {}) => {
    if (screenshotBusyRef.current) return
    screenshotBusyRef.current = true
    try {
      const blob = await request(`/screenshot?t=${Date.now()}`, null, 'GET', { blob: true, trackBusy: options.trackBusy !== false })
      if (!blob) return
      clearScreenshot()
      const url = URL.createObjectURL(blob)
      screenshotRef.current = url
      setScreenshotUrl(url)
    } finally {
      screenshotBusyRef.current = false
    }
  }

  const clearScreenshot = () => {
    if (screenshotRef.current) URL.revokeObjectURL(screenshotRef.current)
    screenshotRef.current = null
    setScreenshotUrl(null)
  }

  const launchApp = async (app) => {
    const ok = await request('/apps/launch', { package: app.package, activity: app.activity }, 'POST', { trackBusy: false })
    if (ok) setTimeout(refreshCurrent, 600)
  }

  const forceStopApp = async (app) => {
    const ok = await request('/apps/force-stop', { package: app.package }, 'POST', { trackBusy: false })
    if (ok) setTimeout(refreshCurrent, 600)
  }

  const startUninstallConfirm = (app) => {
    setUninstallCountdown(10)
    setUninstallConfirm(app)
  }

  const cancelUninstallConfirm = () => {
    setUninstallConfirm(null)
    setUninstallCountdown(10)
  }

  const uninstallApp = async (app) => {
    const ok = await request('/apps/uninstall', { package: app.package }, 'POST', { trackBusy: false })
    if (ok) {
      setApps(items => items.filter(item => item.package !== app.package))
      setTimeout(refreshCurrent, 600)
    }
  }

  const toggleFavorite = async (app) => {
    const next = !app.favorite
    const ok = await request('/apps/favorite', { package: app.package, favorite: next }, 'POST', { trackBusy: false })
    if (ok) setApps(items => items.map(item => item.package === app.package ? { ...item, favorite: next } : item))
  }

  const sendText = async () => {
    const value = text.trim()
    if (!value) return
    const ok = await request('/text', { text: value }, 'POST', { trackBusy: false })
    if (ok) setText('')
  }

  const startPowerConfirm = (action) => {
    setPowerCountdown(10)
    setPowerConfirm(action)
  }

  const cancelPowerConfirm = () => {
    setPowerConfirm(null)
    setPowerCountdown(10)
  }

  const runPower = async (action) => {
    await request('/power', { action }, 'POST', { trackBusy: false })
    setTimeout(loadStatus, 800)
  }

  const filteredApps = useMemo(() => {
    const needle = query.trim().toLowerCase()
    if (!needle) return apps
    return apps.filter(app =>
      app.name?.toLowerCase().includes(needle) ||
      app.package.toLowerCase().includes(needle)
    )
  }, [apps, query])

  return (
    <div className="card space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-denon-text">ADB</h2>
          <p className="text-xs text-denon-muted mt-1">
            {status?.model || tv?.device_name || tv?.device_info?.model || 'Android TV'}
          </p>
        </div>
        <button
          type="button"
          onClick={() => setDetailsOpen(open => !open)}
          className={`${statusClass(status)} cursor-pointer hover:brightness-110`}
        >
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-denon-green' : 'bg-denon-red'}`} />
          {statusLabel}
          <svg className={`w-3 h-3 transition-transform ${detailsOpen ? 'rotate-180' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
        </button>
      </div>

      {detailsOpen && (
        <div className="space-y-3 fade-in">
          <div className="grid gap-2 sm:grid-cols-[1fr_7rem_auto_auto]">
            <input
              type="text"
              value={host}
              onChange={e => setHost(e.target.value)}
              placeholder="192.168.1.120"
              className="bg-denon-surface border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
            />
            <input
              type="number"
              min="1"
              max="65535"
              value={connectPort}
              onChange={e => setConnectPort(e.target.value)}
              placeholder="5555"
              className="bg-denon-surface border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
            />
            <TinyButton disabled={!host.trim() || busy || status?.enabled === false} onClick={connect} className="bg-denon-gold text-denon-dark">
              Connect
            </TinyButton>
            <TinyButton disabled={!connected || busy} onClick={disconnect} className="bg-denon-surface text-denon-text border border-denon-border">
              Disconnect
            </TinyButton>
          </div>

          <div className="rounded-xl border border-denon-border/50 bg-denon-surface/40 p-3 space-y-3">
            <div>
              <h3 className="text-xs font-semibold text-denon-muted uppercase">Pair ADB</h3>
              <p className="mt-1 text-[11px] text-denon-muted">
                Use the pairing port and code shown by Wireless debugging on the Android TV.
              </p>
            </div>
            <div className="grid gap-2 sm:grid-cols-[1fr_7rem_8rem_auto]">
              <input
                type="text"
                value={host}
                onChange={e => setHost(e.target.value)}
                placeholder="192.168.1.120"
                className="bg-denon-dark border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
              />
              <input
                type="number"
                min="1"
                max="65535"
                value={pairPort}
                onChange={e => setPairPort(e.target.value)}
                placeholder="Port"
                className="bg-denon-dark border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
              />
              <input
                type="text"
                value={pairCode}
                onChange={e => setPairCode(e.target.value.toUpperCase())}
                onKeyDown={e => e.key === 'Enter' && host.trim() && pairPort && pairCode.trim() && pair()}
                placeholder="Code"
                className="bg-denon-dark border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
              />
              <TinyButton disabled={!host.trim() || !pairPort || !pairCode.trim() || busy || status?.enabled === false} onClick={pair} className="bg-denon-gold text-denon-dark">
                Pair
              </TinyButton>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs sm:grid-cols-4">
            <Info label="Android" value={status?.android_version} />
            <Info label="Build" value={status?.build} />
            <Info label="Resolution" value={status?.resolution} />
            <Info label="IP" value={diagnostics.wifi_ip} mono />
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-denon-red/40 bg-denon-red/10 px-3 py-2 text-xs text-red-200">
          {error}
        </div>
      )}

      <div className="rounded-xl border border-denon-border/50 bg-denon-surface/40 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-xs font-semibold text-denon-muted uppercase">Current app</p>
            <p className="mt-1 text-sm text-denon-text">{current.name || current.package || '-'}</p>
            <p className="text-[11px] text-denon-muted font-mono truncate">{current.activity || current.package || '-'}</p>
          </div>
          <TinyButton disabled={!connected} onClick={refreshCurrent} className="bg-denon-surface text-denon-text border border-denon-border">
            Refresh
          </TinyButton>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-denon-border/50 bg-denon-surface/40 p-3 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-denon-muted uppercase">Screenshot</h3>
            <div className="flex gap-2">
              <TinyButton disabled={!connected || busy === '/screenshot'} onClick={() => refreshScreenshot()} className="bg-denon-surface text-denon-text border border-denon-border">
                Screenshot
              </TinyButton>
              <button
                type="button"
                aria-label="Continuous screenshot refresh"
                title="Continuous refresh"
                disabled={!connected}
                onClick={() => setContinuousScreenshot(value => !value)}
                className={`flex h-9 w-9 items-center justify-center rounded-xl border transition-all active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed ${
                  continuousScreenshot
                    ? 'border-denon-green/50 bg-denon-green/15 text-denon-green ring-1 ring-denon-green/40'
                    : 'border-denon-border bg-denon-surface text-denon-text'
                }`}
              >
                <svg className={`h-4 w-4 ${continuousScreenshot ? 'animate-spin' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M21 12a9 9 0 0 1-15.5 6.2" />
                  <path d="M3 12A9 9 0 0 1 18.5 5.8" />
                  <path d="M18 2v4h-4" />
                  <path d="M6 22v-4h4" />
                </svg>
              </button>
            </div>
          </div>
          <div className="aspect-video overflow-hidden rounded-xl border border-denon-border/60 bg-black/40 flex items-center justify-center">
            {screenshotUrl ? (
              <img src={screenshotUrl} alt="Android TV screenshot" className="h-full w-full object-contain" />
            ) : (
              <span className="text-xs text-denon-muted">No screenshot</span>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-denon-border/50 bg-denon-surface/40 p-3 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-semibold text-denon-muted uppercase">Diagnostics</h3>
            <TinyButton disabled={!connected} onClick={refreshDiagnostics} className="bg-denon-surface text-denon-text border border-denon-border">
              Refresh
            </TinyButton>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <Info label="Ping" value={diagnostics.ping === true ? 'OK' : diagnostics.ping === false ? 'Fail' : '-'} />
            <Info label="Storage" value={storage ? `${formatKb(storage.available_kb)} free` : '-'} />
            <Info label="Used" value={storage?.used_percent} />
            <Info label="Last error" value={diagnostics.last_error || status?.last_error || '-'} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <TinyButton disabled={!connected} onClick={() => runPower('wake')} className="bg-denon-surface text-denon-text border border-denon-border">
              Wake
            </TinyButton>
            <TinyButton disabled={!connected} onClick={() => startPowerConfirm('sleep')} className="bg-denon-surface text-denon-text border border-denon-border">
              Sleep
            </TinyButton>
            <TinyButton disabled={!connected} onClick={() => startPowerConfirm('power')} className="bg-denon-surface text-denon-text border border-denon-border">
              Power
            </TinyButton>
            <TinyButton disabled={!connected} onClick={() => startPowerConfirm('reboot')} className="bg-denon-red/20 text-denon-red border border-denon-red/40">
              Reboot
            </TinyButton>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-denon-border/50 bg-denon-surface/40 p-3 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-xs font-semibold text-denon-muted uppercase">Apps</h3>
          <TinyButton disabled={!connected} onClick={loadApps} className="bg-denon-surface text-denon-text border border-denon-border">
            Refresh
          </TinyButton>
        </div>
        <input
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search apps"
          className="w-full bg-denon-dark border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50"
        />
        <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
          {filteredApps.map(app => (
            <div key={app.package} className="flex items-center justify-between gap-2 rounded-xl border border-denon-border/50 bg-denon-card/60 p-2">
              <button type="button" onClick={() => launchApp(app)} className="min-w-0 flex-1 text-left">
                <p className="text-sm font-medium text-denon-text truncate">{app.name}</p>
                <p className="text-[11px] text-denon-muted font-mono truncate">{app.package}</p>
              </button>
              <div className="flex shrink-0 gap-1.5">
                <TinyButton onClick={() => toggleFavorite(app)} className={`${app.favorite ? 'bg-denon-gold text-denon-dark' : 'bg-denon-surface text-denon-text border border-denon-border'}`}>
                  Fav
                </TinyButton>
                <TinyButton onClick={() => forceStopApp(app)} className="bg-denon-red/10 text-denon-red border border-denon-red/30">
                  Stop
                </TinyButton>
                <TinyButton onClick={() => startUninstallConfirm(app)} className="bg-denon-red/20 text-denon-red border border-denon-red/40">
                  Remove
                </TinyButton>
              </div>
            </div>
          ))}
          {connected && filteredApps.length === 0 && (
            <div className="rounded-xl border border-denon-border/50 bg-denon-card/50 p-3 text-xs text-denon-muted">
              No apps
            </div>
          )}
        </div>
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendText()}
          placeholder="Send text over ADB"
          disabled={!connected}
          className="flex-1 bg-denon-surface border border-denon-border rounded-xl px-3 py-2 text-sm text-denon-text placeholder-denon-muted focus:outline-none focus:border-denon-gold/50 disabled:opacity-40"
        />
        <TinyButton disabled={!connected || !text.trim()} onClick={sendText} className="bg-denon-gold text-denon-dark">
          Send
        </TinyButton>
      </div>

      {powerConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-sm rounded-2xl border border-denon-border bg-denon-card p-5 shadow-2xl">
            <h3 className="text-base font-semibold text-denon-text">{powerConfirm === 'reboot' ? 'Reboot Android TV' : 'ADB power action'}</h3>
            <p className="text-xs text-denon-muted mt-1">{powerConfirm} will run in {powerCountdown}s.</p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <button type="button" className="btn-ghost" onClick={cancelPowerConfirm}>
                Cancel
              </button>
              <button type="button" className={powerConfirm === 'reboot' ? 'btn-danger' : 'btn-primary'} onClick={() => {
                const action = powerConfirm
                cancelPowerConfirm()
                runPower(action)
              }}>
                Run now
              </button>
            </div>
          </div>
        </div>
      )}

      {uninstallConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
          <div className="w-full max-w-sm rounded-2xl border border-denon-border bg-denon-card p-5 shadow-2xl">
            <h3 className="text-base font-semibold text-denon-text">Uninstall app</h3>
            <p className="text-xs text-denon-muted mt-1">
              {uninstallConfirm.name || uninstallConfirm.package} will be uninstalled in {uninstallCountdown}s.
            </p>
            <p className="mt-2 truncate font-mono text-[11px] text-denon-muted">{uninstallConfirm.package}</p>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <button type="button" className="btn-ghost" onClick={cancelUninstallConfirm}>
                Cancel
              </button>
              <button type="button" className="btn-danger" onClick={() => {
                const app = uninstallConfirm
                cancelUninstallConfirm()
                uninstallApp(app)
              }}>
                Remove now
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function Info({ label, value, mono = false }) {
  return (
    <div className="min-w-0 rounded-xl border border-denon-border/40 bg-denon-card/50 px-3 py-2">
      <p className="text-[10px] font-semibold uppercase text-denon-muted">{label}</p>
      <p className={`mt-1 truncate text-xs text-denon-text ${mono ? 'font-mono' : ''}`}>{value || '-'}</p>
    </div>
  )
}

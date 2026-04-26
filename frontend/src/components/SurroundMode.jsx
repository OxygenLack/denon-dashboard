const COMMON_MODES = [
  'MOVIE', 'MUSIC', 'GAME', 'DIRECT', 'PURE DIRECT',
  'STEREO', 'AUTO', 'DOLBY ATMOS', 'DOLBY SURROUND',
  'DOLBY DIGITAL', 'DTS SURROUND', 'DTS:X',
  'MULTI CH IN', 'MCH STEREO',
]

/* Receivers report variant strings (e.g. "DOLBY AUDIO - DSUR" for DOLBY SURROUND).
   Match when either string contains the other, so the active mode highlights. */
function isActiveMode(current, mode) {
  if (!current) return false
  if (current === mode) return true
  const c = current.toUpperCase()
  const m = mode.toUpperCase()
  return c.includes(m) || m.includes(c)
}

export default function SurroundMode({ state, sendCommand }) {
  const current = state?.surround_mode

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-medium text-denon-muted">Surround Mode</h2>
        {current && (
          <span className="text-xs text-denon-gold font-medium bg-denon-gold/10 px-2 py-0.5 rounded-lg">
            {current}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 gap-2">
        {COMMON_MODES.map(mode => (
          <button
            key={mode}
            onClick={() => sendCommand(`MS${mode}`)}
            className={`py-2.5 px-3 rounded-xl text-xs font-medium transition-all text-left ${
              isActiveMode(current, mode)
                ? 'bg-denon-gold text-denon-dark ring-2 ring-denon-gold/30'
                : 'bg-denon-surface text-denon-text hover:bg-denon-border'
            }`}
          >
            {mode}
          </button>
        ))}
      </div>
    </div>
  )
}

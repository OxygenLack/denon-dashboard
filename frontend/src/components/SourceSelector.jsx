const BluetoothIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round" className="inline w-4 h-4 align-text-bottom">
    <path d="M7 7l10 10-5 5V2l5 5L7 17" />
  </svg>
)

const SpotifyIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="inline w-4 h-4 align-text-bottom">
    <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm4.6 14.4a.6.6 0 0 1-.84.2c-2.3-1.4-5.2-1.72-8.6-.94a.6.6 0 1 1-.28-1.18c3.74-.86 6.94-.48 9.52 1.08a.6.6 0 0 1 .2.84zm1.22-2.72a.78.78 0 0 1-1.06.26c-2.64-1.62-6.66-2.1-9.78-1.14a.78.78 0 0 1-.46-1.5c3.56-1.08 7.98-.56 11.04 1.3a.78.78 0 0 1 .26 1.08zm.1-2.84C14.68 8.86 9.38 8.68 6.3 9.6a.94.94 0 0 1-.54-1.8c3.54-1.06 9.4-.86 13.1 1.34a.94.94 0 0 1-.94 1.64z" />
  </svg>
)

const SOURCE_ICONS = {
  GAME: '🎮', BD: '📀', TV: '📺', 'SAT/CBL': '📡', MPLAY: '▶️',
  NET: '🌐', BT: <BluetoothIcon />, AUX1: '🖥️', AUX2: '🔌', CD: '💿',
  TUNER: '📻', PHONO: '🎵', DVD: '📀', USB: '💾', 'USB/IPOD': '💾',
  SPOTIFY: <SpotifyIcon />, PANDORA: '🎵', SIRIUSXM: '📻', HDRADIO: '📻',
  IRADIO: '📻', SERVER: '🖥️', FAVORITES: '⭐',
}

const DEFAULT_SOURCES = {
  PHONO: 'Phono', CD: 'CD', TUNER: 'Tuner', DVD: 'DVD', BD: 'Blu-ray',
  TV: 'TV Audio', 'SAT/CBL': 'SAT/Cable', MPLAY: 'Media Player',
  GAME: 'Game', NET: 'Online Music', BT: 'Bluetooth',
  AUX1: 'AUX1', AUX2: 'AUX2',
}

export default function SourceSelector({ state, sendCommand, sources, sourceNameMap, zone = 'main' }) {
  const current = zone === 'main' ? state?.source : state?.z2_source
  const prefix = zone === 'main' ? 'SI' : 'Z2'

  const sourceList = sources.length > 0
    ? sources
    : Object.entries(DEFAULT_SOURCES).map(([id, name]) => ({ id, name }))

  const getName = (code) => sourceNameMap?.[code] || DEFAULT_SOURCES[code] || code

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-medium text-denon-muted uppercase tracking-wider">Input Source</h2>
        {current && (
          <span className="text-xs text-denon-gold font-medium">
            {SOURCE_ICONS[current] || '🔊'} {getName(current)}
          </span>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {sourceList.map(s => {
          const active = current === s.id
          return (
            <button
              key={s.id}
              onClick={() => sendCommand(`${prefix}${s.id}`)}
              className={`group relative py-3 px-3 rounded-xl text-sm font-medium transition-all duration-150 text-left overflow-hidden ${
                active
                  ? 'bg-gradient-to-br from-denon-gold/20 to-amber-500/10 text-denon-gold ring-1 ring-denon-gold/40'
                  : 'bg-denon-surface/70 text-denon-text hover:bg-denon-surface hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              <span className="text-base mr-1.5">{SOURCE_ICONS[s.id] || '🔊'}</span>
              <span className="text-xs">{s.name}</span>
              {active && (
                <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-denon-gold" />
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

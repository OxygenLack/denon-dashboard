const BluetoothIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
       strokeLinecap="round" strokeLinejoin="round" className="inline w-4 h-4 align-text-bottom">
    <path d="M7 7l10 10-5 5V2l5 5L7 17" />
  </svg>
)

const SOURCE_ICONS = {
  GAME: '🎮', BD: '📀', TV: '📺', 'SAT/CBL': '📡', MPLAY: '▶️',
  NET: '🌐', BT: <BluetoothIcon />, AUX1: '🖥️', AUX2: '🔌', CD: '💿',
  TUNER: '📻', PHONO: '🎵', DVD: '📀', USB: '💾', 'USB/IPOD': '💾',
  SPOTIFY: '🎵', PANDORA: '🎵', SIRIUSXM: '📻', HDRADIO: '📻',
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

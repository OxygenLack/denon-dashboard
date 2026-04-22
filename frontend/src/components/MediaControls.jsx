const MEDIA_SOURCES = ['NET', 'MPLAY', 'BT', 'USB', 'USB/IPOD', 'SPOTIFY', 'PANDORA', 'SIRIUSXM', 'IRADIO', 'SERVER', 'FAVORITES']

export default function MediaControls({ state, sendCommand, post, zone = 'main' }) {
  const source = zone === 'main' ? state?.source : state?.z2_source
  const mediaCapable = MEDIA_SOURCES.includes(source)

  // Now-playing data comes from WebSocket state (backend polls HEOS once for all clients)
  const nowPlaying = state?.now_playing
  const playState = state?.play_state

  const doMedia = async (action) => {
    try {
      const base = window.location.origin
      await fetch(`${base}/api/v1/media/${action}`, { method: 'POST' })
    } catch { /* ignore */ }
  }

  if (!mediaCapable) return null

  const isPlaying = playState === 'play'
  const song = nowPlaying?.song
  const artist = nowPlaying?.artist
  const albumArt = nowPlaying?.image_url

  return (
    <div className="card">
      <h2 className="text-xs font-medium text-denon-muted uppercase tracking-wider mb-3">Now Playing</h2>

      {/* Now Playing Info */}
      {(song || artist) && (
        <div className="flex items-center gap-3 mb-4">
          {albumArt && (
            <img
              src={albumArt}
              alt="Album art"
              className="w-12 h-12 rounded-lg object-cover shadow-md flex-shrink-0"
            />
          )}
          <div className="min-w-0 flex-1">
            {song && <p className="text-sm font-medium text-denon-text truncate">{song}</p>}
            {artist && <p className="text-xs text-denon-muted truncate">{artist}</p>}
          </div>
          <span className={`text-[10px] px-2 py-0.5 rounded-full ${
            isPlaying
              ? 'bg-denon-green/10 text-denon-green'
              : 'bg-denon-surface text-denon-muted'
          }`}>
            {isPlaying ? '▶ Playing' : '⏸ Paused'}
          </span>
        </div>
      )}

      {/* Transport Controls */}
      <div className="flex items-center justify-center gap-3">
        <button
          onClick={() => doMedia('previous')}
          className="w-11 h-11 rounded-xl bg-denon-surface/70 text-denon-muted hover:text-denon-text hover:bg-denon-surface transition-all active:scale-95 flex items-center justify-center"
          title="Previous"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
          </svg>
        </button>

        <button
          onClick={() => doMedia(isPlaying ? 'pause' : 'play')}
          className="w-14 h-14 rounded-2xl bg-gradient-to-br from-denon-gold to-amber-600 text-denon-dark shadow-lg shadow-denon-gold/25 hover:brightness-110 transition-all active:scale-95 flex items-center justify-center"
          title={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
            </svg>
          ) : (
            <svg className="w-6 h-6 ml-0.5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8 5v14l11-7z"/>
            </svg>
          )}
        </button>

        <button
          onClick={() => doMedia('next')}
          className="w-11 h-11 rounded-xl bg-denon-surface/70 text-denon-muted hover:text-denon-text hover:bg-denon-surface transition-all active:scale-95 flex items-center justify-center"
          title="Next"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
            <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

import { useState, useEffect, memo } from 'react'
import { getTheme, applyTheme } from './theme'
import { useWebSocket } from './hooks/useWebSocket'
import ReceiverSetup from './components/ReceiverSetup'
import { useDeviceInfo } from './hooks/useDeviceInfo'
import { useApi } from './hooks/useApi'
import StatusBar from './components/StatusBar'
import PowerControl from './components/PowerControl'
import VolumeControl from './components/VolumeControl'
import SourceSelector from './components/SourceSelector'
import SurroundMode from './components/SurroundMode'
import ChannelLevels from './components/ChannelLevels'
import ToneControls from './components/ToneControls'
import SubwooferLevel from './components/SubwooferLevel'
import AudioSettings from './components/AudioSettings'
import MediaControls from './components/MediaControls'
import Zone2Controls from './components/Zone2Controls'
import AndroidTvRemote from './components/AndroidTvRemote'

const FALLBACK_CHANNEL_NAMES = {
  FL: 'Front L', FR: 'Front R', C: 'Center', SW: 'Subwoofer',
  SW2: 'Sub 2', SL: 'Surround L', SR: 'Surround R',
  SBL: 'SB Left', SBR: 'SB Right', SB: 'SB',
  FHL: 'Height L', FHR: 'Height R',
  FWL: 'Wide L', FWR: 'Wide R',
  TFL: 'Top F.L', TFR: 'Top F.R', TML: 'Top M.L', TMR: 'Top M.R',
  TRL: 'Top R.L', TRR: 'Top R.R',
}

const MemoChannelLevels = memo(ChannelLevels)
const MemoAudioSettings = memo(AudioSettings)
const MemoSourceSelector = memo(SourceSelector)
const MemoVolumeControl = memo(VolumeControl)
const MemoPowerControl = memo(PowerControl)
const MemoStatusBar = memo(StatusBar)
const MemoMediaControls = memo(MediaControls)
const MemoAndroidTvRemote = memo(AndroidTvRemote)

export default function App() {
  const { state, wsConnected, sendCommand } = useWebSocket()
  const { info, refreshDevice } = useDeviceInfo()
  const { post } = useApi()
  const [zone, setZone] = useState('main')
  const [activeSection, setActiveSection] = useState('controls')
  const [currentTheme, setCurrentTheme] = useState('gold')

  useEffect(() => {
    const t = getTheme(info?.theme)
    applyTheme(t)
    setCurrentTheme(t)
  }, [info?.theme])

  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-denon-dark">
        <div className="text-center">
          <div className="w-14 h-14 border-4 border-denon-gold/30 border-t-denon-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-denon-muted text-sm">Connecting...</p>
        </div>
      </div>
    )
  }

  const deviceName = info?.device_name || 'Denon AVR'
  const zoneName = info?.zone1_name || 'Main Zone'
  const z2Name = info?.zone2_name || 'Zone 2'
  const channelNames = (info?.channel_names && Object.keys(info.channel_names).length > 0)
    ? info.channel_names
    : FALLBACK_CHANNEL_NAMES
  const sourceNameMap = info?.source_name_map || {}
  const configuredSources = info?.sources || []
  const receiverSetupReason = !info?.receiver_ip ? 'no_host' : 'connect_failed'

  const mainSections = [
    { id: 'controls', label: 'Controls' },
    { id: 'speakers', label: 'Speakers' },
    { id: 'audio', label: 'Audio / EQ' },
  ]

  const renderReceiverSetup = () => (
    <ReceiverSetup
      reason={receiverSetupReason}
      onConnect={refreshDevice}
      currentTheme={currentTheme}
      onThemeChange={setCurrentTheme}
      embedded
    />
  )

  return (
    <div className="max-w-2xl mx-auto px-4 pb-8 min-h-screen">
      <MemoStatusBar
        deviceName={deviceName}
        state={state}
        wsConnected={wsConnected}
        receiverIp={info?.receiver_ip}
        currentTheme={currentTheme}
        onThemeChange={setCurrentTheme}
        activeZone={zone}
      />

      <div className="grid grid-cols-3 gap-0 mb-5 bg-denon-card/50 rounded-2xl p-1.5 border border-denon-border/50 backdrop-blur-sm">
        <button
          onClick={() => setZone('main')}
          className={`py-3 px-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            zone === 'main'
              ? 'bg-gradient-to-r from-denon-gold to-amber-500 text-denon-dark shadow-lg shadow-denon-gold/25'
              : 'text-denon-muted hover:text-denon-text'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
            <span className="truncate">{zoneName}</span>
          </span>
        </button>
        <button
          onClick={() => setZone('zone2')}
          className={`py-3 px-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            zone === 'zone2'
              ? 'bg-gradient-to-r from-denon-gold to-amber-500 text-denon-dark shadow-lg shadow-denon-gold/25'
              : 'text-denon-muted hover:text-denon-text'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
            <span className="truncate">{z2Name}</span>
          </span>
        </button>
        <button
          onClick={() => setZone('androidtv')}
          className={`py-3 px-2 rounded-xl text-sm font-semibold transition-all duration-200 ${
            zone === 'androidtv'
              ? 'bg-gradient-to-r from-denon-gold to-amber-500 text-denon-dark shadow-lg shadow-denon-gold/25'
              : 'text-denon-muted hover:text-denon-text'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="5" width="18" height="12" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/></svg>
            <span className="truncate">Android TV</span>
          </span>
        </button>
      </div>

      {zone === 'main' && (
        <>
          {!state.connected ? renderReceiverSetup() : (
            <>
              <div className="flex gap-1 mb-4">
                {mainSections.map(s => (
                  <button
                    key={s.id}
                    onClick={() => setActiveSection(s.id)}
                    className={`flex-1 py-2 rounded-lg text-xs font-medium transition-all ${
                      activeSection === s.id
                        ? 'bg-denon-surface text-denon-gold border border-denon-gold/30'
                        : 'text-denon-muted hover:text-denon-text'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>

              <div className="space-y-4 fade-in" key={activeSection}>
                {activeSection === 'controls' && (
                  <>
                    <MemoPowerControl state={state} sendCommand={sendCommand} zone="main" />
                    <MemoVolumeControl state={state} sendCommand={sendCommand} post={post} />
                    <MemoMediaControls state={state} sendCommand={sendCommand} post={post} />
                    <MemoSourceSelector
                      state={state}
                      sendCommand={sendCommand}
                      sources={configuredSources}
                      sourceNameMap={sourceNameMap}
                    />
                    <SurroundMode state={state} sendCommand={sendCommand} />
                  </>
                )}

                {activeSection === 'speakers' && (
                  <>
                    <MemoChannelLevels
                      channels={state.channel_volumes || {}}
                      channelNames={channelNames}
                      sendCommand={sendCommand}
                      post={post}
                      calibration={state.speaker_calibration}
                    />
                    <SubwooferLevel state={state} post={post} />
                  </>
                )}

                {activeSection === 'audio' && (
                  <>
                    <ToneControls state={state} post={post} />
                    <MemoAudioSettings state={state} post={post} />
                  </>
                )}
              </div>
            </>
          )}
        </>
      )}

      {zone === 'zone2' && (
        <div className="fade-in">
          {!state.connected ? renderReceiverSetup() : (
            <Zone2Controls
              state={state}
              sendCommand={sendCommand}
              post={post}
              sources={configuredSources}
              sourceNameMap={sourceNameMap}
              zoneName={z2Name}
            />
          )}
        </div>
      )}

      {zone === 'androidtv' && (
        <MemoAndroidTvRemote state={state} />
      )}
    </div>
  )
}

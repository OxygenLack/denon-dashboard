import { useState } from 'react'
import { useWebSocket } from './hooks/useWebSocket'
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

const CHANNEL_NAMES = {
  FL: 'Front L', FR: 'Front R', C: 'Center', SW: 'Subwoofer',
  SW2: 'Sub 2', SL: 'Surround L', SR: 'Surround R',
  SBL: 'SB Left', SBR: 'SB Right', SB: 'SB',
  FHL: 'Height L', FHR: 'Height R',
  FWL: 'Wide L', FWR: 'Wide R',
  TFL: 'Top F.L', TFR: 'Top F.R', TML: 'Top M.L', TMR: 'Top M.R',
  TRL: 'Top R.L', TRR: 'Top R.R',
}

export default function App() {
  const { state, wsConnected, sendCommand } = useWebSocket()
  const { info } = useDeviceInfo()
  const { post } = useApi()
  const [zone, setZone] = useState('main')
  const [activeSection, setActiveSection] = useState('controls')

  if (!state) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-denon-dark">
        <div className="text-center">
          <div className="w-14 h-14 border-4 border-denon-gold/30 border-t-denon-gold rounded-full animate-spin mx-auto mb-4" />
          <p className="text-denon-muted text-sm">Connecting to receiver…</p>
        </div>
      </div>
    )
  }

  const deviceName = info?.device_name || 'Denon AVR'
  const zoneName = info?.zone1_name || 'Main Zone'
  const z2Name = info?.zone2_name || 'Zone 2'
  const sourceNameMap = info?.source_name_map || {}
  const configuredSources = info?.sources || []

  const mainSections = [
    { id: 'controls', label: 'Controls' },
    { id: 'speakers', label: 'Speakers' },
    { id: 'audio', label: 'Audio / EQ' },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 pb-8 min-h-screen">
      {/* Header + Health */}
      <StatusBar
        deviceName={deviceName}
        state={state}
        wsConnected={wsConnected}
        receiverIp={info?.receiver_ip}
      />

      {/* Zone Selector */}
      <div className="flex gap-0 mb-5 bg-denon-card/50 rounded-2xl p-1.5 border border-denon-border/50 backdrop-blur-sm">
        <button
          onClick={() => setZone('main')}
          className={`flex-1 py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-200 ${
            zone === 'main'
              ? 'bg-gradient-to-r from-denon-gold to-amber-500 text-denon-dark shadow-lg shadow-denon-gold/25'
              : 'text-denon-muted hover:text-denon-text'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
            {zoneName}
          </span>
        </button>
        <button
          onClick={() => setZone('zone2')}
          className={`flex-1 py-3 px-4 rounded-xl text-sm font-semibold transition-all duration-200 ${
            zone === 'zone2'
              ? 'bg-gradient-to-r from-denon-gold to-amber-500 text-denon-dark shadow-lg shadow-denon-gold/25'
              : 'text-denon-muted hover:text-denon-text'
          }`}
        >
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/></svg>
            {z2Name}
          </span>
        </button>
      </div>

      {/* Main Zone */}
      {zone === 'main' && (
        <>
          {/* Section tabs */}
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
                <PowerControl state={state} sendCommand={sendCommand} zone="main" />
                <VolumeControl state={state} sendCommand={sendCommand} post={post} />
                <MediaControls state={state} sendCommand={sendCommand} post={post} />
                <SourceSelector
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
                <ChannelLevels
                  channels={state.channel_volumes || {}}
                  channelNames={CHANNEL_NAMES}
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
                <AudioSettings state={state} post={post} />
              </>
            )}
          </div>
        </>
      )}

      {/* Zone 2 */}
      {zone === 'zone2' && (
        <div className="fade-in">
          <Zone2Controls
            state={state}
            sendCommand={sendCommand}
            post={post}
            sources={configuredSources}
            sourceNameMap={sourceNameMap}
            zoneName={z2Name}
          />
        </div>
      )}
    </div>
  )
}

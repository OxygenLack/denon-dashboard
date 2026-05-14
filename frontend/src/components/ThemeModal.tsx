import { useState, useEffect, useRef } from 'react'
import { THEMES, applyThemeConfig, saveThemeToServer } from '../theme'
import { DEMO_MODE } from '../demoData'
import type { Theme, ThemeConfig, ThemeName } from '../types'

interface OverrideVar {
  key: string
  label: string
  defaultFor: (t: Theme) => string
}

const OVERRIDE_VARS: OverrideVar[] = [
  { key: '--accent',     label: 'Accent',     defaultFor: t => t.accent },
  { key: '--accent-dim', label: 'Accent Dim', defaultFor: t => t.accentDim },
  { key: '--bg',         label: 'Background', defaultFor: () => '#0D0D0D' },
  { key: '--card',       label: 'Card',       defaultFor: () => '#1A1A1A' },
  { key: '--surface',    label: 'Surface',    defaultFor: () => '#242424' },
  { key: '--border',     label: 'Border',     defaultFor: () => '#333333' },
  { key: '--text',       label: 'Text',       defaultFor: () => '#E5E5E5' },
  { key: '--muted',      label: 'Muted',      defaultFor: () => '#888888' },
]

interface Props {
  currentConfig: ThemeConfig
  onClose: () => void
  onSaved?: (config: ThemeConfig) => void
}

export default function ThemeModal({ currentConfig, onClose, onSaved }: Props) {
  const [draft, setDraft] = useState<ThemeConfig>(currentConfig)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [overridesExpanded, setOverridesExpanded] = useState(false)
  const modalRef = useRef<HTMLDivElement>(null)

  // Live preview
  useEffect(() => {
    applyThemeConfig(draft)
  }, [draft])

  // Escape to cancel
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleCancel()
    }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [currentConfig])

  // Trap focus on mount
  useEffect(() => {
    const first = modalRef.current?.querySelector<HTMLElement>('button, input, [tabindex]')
    first?.focus()
  }, [])

  function handlePickBase(name: ThemeName) {
    setDraft({ base: name, overrides: {} })
  }

  function handleOverride(key: string, value: string) {
    setDraft(d => ({ ...d, overrides: { ...d.overrides, [key]: value } }))
  }

  function handleClearOverride(key: string) {
    setDraft(d => {
      const overrides = { ...d.overrides }
      delete overrides[key]
      return { ...d, overrides }
    })
  }

  function handleResetAll() {
    setDraft({ base: draft.base, overrides: {} })
  }

  function handleCancel() {
    applyThemeConfig(currentConfig)
    onClose()
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    try {
      if (!DEMO_MODE) await saveThemeToServer(draft)
      onSaved?.(draft)
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save theme')
    } finally {
      setSaving(false)
    }
  }

  const baseTheme = THEMES[draft.base] ?? THEMES.gold

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) handleCancel() }}
    >
      <div
        ref={modalRef}
        className="bg-denon-card border border-denon-border rounded-2xl w-full max-w-md max-h-[90vh] overflow-y-auto shadow-2xl shadow-black/60 fade-in"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-denon-border/60">
          <h2 className="text-denon-text font-semibold text-base">Theme Settings</h2>
          <button
            onClick={handleCancel}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-denon-muted hover:text-denon-text hover:bg-denon-surface/70 transition-all"
            aria-label="Close"
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-5 space-y-5">
          {/* Base theme */}
          <div>
            <p className="text-[11px] text-denon-muted uppercase tracking-wider mb-3">Base Theme</p>
            <div className="grid grid-cols-3 gap-2">
              {(Object.entries(THEMES) as [ThemeName, Theme][]).map(([name, theme]) => (
                <button
                  key={name}
                  onClick={() => handlePickBase(name)}
                  className={`flex flex-col items-center gap-1.5 py-2.5 px-1 rounded-xl transition-all ${
                    draft.base === name
                      ? 'bg-denon-surface ring-1 ring-denon-border'
                      : 'hover:bg-denon-surface/50'
                  }`}
                >
                  <span
                    className="w-6 h-6 rounded-full ring-2 ring-offset-2 ring-offset-denon-card"
                    style={{
                      backgroundColor: theme.accent,
                      boxShadow: draft.base === name ? `0 0 12px ${theme.accent}60` : 'none',
                    }}
                  />
                  <span className={`text-[10px] font-medium ${draft.base === name ? 'text-denon-text' : 'text-denon-muted'}`}>
                    {theme.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Color overrides */}
          <div className="border border-denon-border/50 rounded-xl overflow-hidden">
            <button
              onClick={() => setOverridesExpanded(e => !e)}
              className="w-full flex items-center justify-between px-4 py-3 text-denon-text hover:bg-denon-surface/50 transition-all"
            >
              <span className="text-sm font-medium">Color Overrides</span>
              <div className="flex items-center gap-2">
                {Object.keys(draft.overrides).length > 0 && (
                  <span className="text-[10px] bg-denon-surface text-denon-muted px-2 py-0.5 rounded-full">
                    {Object.keys(draft.overrides).length} active
                  </span>
                )}
                <svg
                  className={`w-4 h-4 text-denon-muted transition-transform ${overridesExpanded ? 'rotate-180' : ''}`}
                  viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </div>
            </button>

            {overridesExpanded && (
              <div className="border-t border-denon-border/50 px-4 py-3 space-y-3">
                {OVERRIDE_VARS.map(({ key, label, defaultFor }) => {
                  const effectiveValue = draft.overrides[key] ?? defaultFor(baseTheme)
                  const isOverridden = key in draft.overrides
                  return (
                    <div key={key} className="flex items-center gap-3">
                      <input
                        type="color"
                        value={effectiveValue}
                        onChange={e => handleOverride(key, e.target.value)}
                        className="w-8 h-8 rounded-lg border border-denon-border cursor-pointer bg-transparent"
                        title={label}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-denon-text">{label}</div>
                        <div className="text-[11px] text-denon-muted font-mono">{effectiveValue}</div>
                      </div>
                      {isOverridden && (
                        <button
                          onClick={() => handleClearOverride(key)}
                          className="w-6 h-6 flex items-center justify-center rounded-md text-denon-muted hover:text-denon-text hover:bg-denon-surface transition-all flex-shrink-0"
                          title="Reset to default"
                        >
                          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                            <path d="M18 6L6 18M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Error */}
          {error && (
            <p className="text-denon-red text-sm bg-denon-red/10 border border-denon-red/20 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-5 border-t border-denon-border/60">
          <button
            onClick={handleResetAll}
            disabled={Object.keys(draft.overrides).length === 0}
            className="text-sm text-denon-muted hover:text-denon-text disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            Reset overrides
          </button>
          <div className="flex gap-2">
            <button
              onClick={handleCancel}
              className="btn btn-ghost text-sm px-4 py-2"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="btn btn-primary text-sm px-4 py-2 disabled:opacity-60"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

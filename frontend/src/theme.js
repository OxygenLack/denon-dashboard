/**
 * Theme palette — sets CSS vars used throughout index.css and inline styles.
 * accent:    main highlight color (buttons, sliders, active states)
 * accentDim: darker variant (gradient end, thumb)
 */
export const THEMES = {
  gold:   { accent: '#C5A55A', accentDim: '#a08840' },
  blue:   { accent: '#3B82F6', accentDim: '#1d4ed8' },
  red:    { accent: '#EF4444', accentDim: '#b91c1c' },
  green:  { accent: '#22C55E', accentDim: '#15803d' },
  olive:  { accent: '#84CC16', accentDim: '#4d7c0f' },
  violet: { accent: '#8B5CF6', accentDim: '#6d28d9' },
  purple: { accent: '#A855F7', accentDim: '#7e22ce' },
  pink:   { accent: '#EC4899', accentDim: '#be185d' },
  orange: { accent: '#F97316', accentDim: '#c2410c' },
}

export function applyTheme(name) {
  const t = THEMES[name] ?? THEMES.gold
  const root = document.documentElement
  root.style.setProperty('--accent',     t.accent)
  root.style.setProperty('--accent-dim', t.accentDim)
}

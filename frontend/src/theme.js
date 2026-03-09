/**
 * Theme palette map — each theme defines the accent color triplet:
 *   accent:  main highlight (buttons, sliders, active states)
 *   accentDim: darker variant (gradient end, thumb)
 *   accentGlow: glow/shadow color (rgba)
 */
export const THEMES = {
  gold:   { accent: '#C5A55A', accentDim: '#a08840', accentGlow: 'rgba(197,165,90,' },
  blue:   { accent: '#3B82F6', accentDim: '#1d4ed8', accentGlow: 'rgba(59,130,246,' },
  red:    { accent: '#EF4444', accentDim: '#b91c1c', accentGlow: 'rgba(239,68,68,'  },
  green:  { accent: '#22C55E', accentDim: '#15803d', accentGlow: 'rgba(34,197,94,'  },
  olive:  { accent: '#84CC16', accentDim: '#4d7c0f', accentGlow: 'rgba(132,204,22,' },
  violet: { accent: '#8B5CF6', accentDim: '#6d28d9', accentGlow: 'rgba(139,92,246,' },
  purple: { accent: '#A855F7', accentDim: '#7e22ce', accentGlow: 'rgba(168,85,247,' },
  pink:   { accent: '#EC4899', accentDim: '#be185d', accentGlow: 'rgba(236,72,153,' },
  orange: { accent: '#F97316', accentDim: '#c2410c', accentGlow: 'rgba(249,115,22,' },
}

export function applyTheme(name) {
  const t = THEMES[name] ?? THEMES.gold
  const root = document.documentElement

  root.style.setProperty('--accent',      t.accent)
  root.style.setProperty('--accent-dim',  t.accentDim)
  root.style.setProperty('--accent-glow', t.accentGlow)
}

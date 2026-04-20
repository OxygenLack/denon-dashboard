import { useCallback } from 'react'

export function useApi() {
  const post = useCallback(async (path, body = {}) => {
    try {
      const res = await fetch(`/api/v1${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const text = await res.text().catch(() => res.statusText)
        console.warn(`API ${path} failed (${res.status}):`, text)
        return { ok: false, status: res.status, error: text }
      }
      return { ok: true }
    } catch (err) {
      console.warn(`API ${path} error:`, err)
      return { ok: false, status: 0, error: err.message }
    }
  }, [])

  return { post }
}

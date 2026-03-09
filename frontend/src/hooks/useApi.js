import { useCallback } from 'react'

export function useApi() {
  const post = useCallback(async (path, body = {}) => {
    try {
      const res = await fetch(`/api/v1${path}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      return res.ok
    } catch {
      return false
    }
  }, [])

  return { post }
}

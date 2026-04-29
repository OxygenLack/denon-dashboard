import { useEffect, useRef, useState, useCallback } from 'react'

const RECONNECT_DELAY = 3000

export function useWebSocket() {
  const [state, setState] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)
  const lastJsonRef = useRef(null) // track serialized state for diffing

  const connect = useCallback(() => {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${proto}//${window.location.host}/api/v1/ws`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setWsConnected(true)
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current)
        reconnectTimer.current = null
      }
    }

    ws.onmessage = (e) => {
      try {
        // Only trigger React re-render if the state payload actually changed.
        // Avoids unnecessary re-renders from identical WebSocket pushes
        // (e.g. heartbeat polls that return the same state).
        if (e.data !== lastJsonRef.current) {
          lastJsonRef.current = e.data
          setState(JSON.parse(e.data))
        }
      } catch {}
    }

    ws.onclose = () => {
      setWsConnected(false)
      wsRef.current = null
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [])

  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  const sendCommand = useCallback((command) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ command }))
    }
  }, [])

  return { state, wsConnected, sendCommand }
}

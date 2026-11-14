import { useEffect, useRef, useState } from 'react'
import PropTypes from 'prop-types'
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
import { getAuthToken } from '../utils/api'

/**
 * Terminal Component
 * 
 * Renders a browser-based terminal using xterm.js and establishes a WebSocket
 * connection to communicate with the backend container shell.
 * 
 * Requirements:
 * - 4.1: Display terminal interface using xterm.js
 * - 4.2: Connect to container via WebSocket within 2 seconds
 * - 4.3: Execute commands in container and return output within 200ms
 * - 4.4: Display real-time command output
 * - 4.5: Support standard terminal features (history, cursor navigation)
 * - 12.3: Use xterm.js for terminal rendering
 */

const Terminal = ({ sessionId, websocketUrl }) => {
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)
  const fitAddonRef = useRef(null)
  const socketRef = useRef(null)
  const [connectionStatus, setConnectionStatus] = useState('connecting')
  const [errorMessage, setErrorMessage] = useState(null)

  useEffect(() => {
    if (!sessionId || !websocketUrl) {
      return
    }

    // Initialize xterm.js terminal
    const terminal = new XTerm({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#ffffff',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      },
      allowTransparency: false,
      convertEol: true,
      scrollback: 1000,
      tabStopWidth: 4
    })

    // Initialize fit addon for responsive terminal sizing
    const fitAddon = new FitAddon()
    terminal.loadAddon(fitAddon)

    // Mount terminal to DOM
    if (terminalRef.current) {
      terminal.open(terminalRef.current)
      fitAddon.fit()
    }

    xtermRef.current = terminal
    fitAddonRef.current = fitAddon

    // Connect to WebSocket
    connectWebSocket(terminal)

    // Handle window resize
    const handleResize = () => {
      if (fitAddonRef.current) {
        fitAddonRef.current.fit()
      }
    }
    window.addEventListener('resize', handleResize)

    // Cleanup on unmount
    return () => {
      window.removeEventListener('resize', handleResize)
      if (socketRef.current) {
        socketRef.current.close()
      }
      if (xtermRef.current) {
        xtermRef.current.dispose()
      }
    }
  }, [sessionId, websocketUrl])

  /**
   * Establish WebSocket connection to backend terminal handler
   * @param {XTerm} terminal - xterm.js terminal instance
   */
  const connectWebSocket = (terminal) => {
    try {
      // Build WebSocket URL with authentication token
      const token = getAuthToken()
      const wsUrl = `${websocketUrl}?token=${token}`
      
      const socket = new WebSocket(wsUrl)
      socketRef.current = socket

      // WebSocket opened - connection established
      socket.onopen = () => {
        setConnectionStatus('connected')
        setErrorMessage(null)
        terminal.writeln('\x1b[32mConnected to container terminal\x1b[0m')
        
        // Send terminal size to backend
        socket.send(JSON.stringify({
          type: 'resize',
          cols: terminal.cols,
          rows: terminal.rows
        }))
      }

      // WebSocket message received - write to terminal
      socket.onmessage = (event) => {
        try {
          // Check if message is JSON (control message) or raw terminal data
          const data = event.data
          if (typeof data === 'string' && data.startsWith('{')) {
            const message = JSON.parse(data)
            if (message.type === 'error') {
              terminal.writeln(`\x1b[31mError: ${message.message}\x1b[0m`)
            }
          } else {
            // Raw terminal output - write directly
            terminal.write(data)
          }
        } catch (error) {
          // If not JSON, treat as raw terminal data
          terminal.write(event.data)
        }
      }

      // WebSocket closed - connection lost
      socket.onclose = () => {
        setConnectionStatus('disconnected')
        terminal.writeln('\x1b[33m\r\nConnection closed\x1b[0m')
      }

      // WebSocket error
      socket.onerror = (error) => {
        setConnectionStatus('error')
        setErrorMessage('Failed to connect to terminal')
        terminal.writeln('\x1b[31mConnection error\x1b[0m')
        console.error('WebSocket error:', error)
      }

      // Handle terminal input - send to WebSocket
      terminal.onData((data) => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(data)
        }
      })

      // Handle terminal resize - notify backend
      terminal.onResize(({ cols, rows }) => {
        if (socket.readyState === WebSocket.OPEN) {
          socket.send(JSON.stringify({
            type: 'resize',
            cols,
            rows
          }))
        }
      })

    } catch (error) {
      setConnectionStatus('error')
      setErrorMessage('Failed to initialize WebSocket connection')
      console.error('WebSocket connection error:', error)
    }
  }

  /**
   * Get status indicator color based on connection state
   */
  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'bg-green-500'
      case 'connecting':
        return 'bg-yellow-500'
      case 'disconnected':
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  /**
   * Get status text based on connection state
   */
  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'Connected'
      case 'connecting':
        return 'Connecting...'
      case 'disconnected':
        return 'Disconnected'
      case 'error':
        return 'Connection Error'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Connection status indicator */}
      <div className="flex items-center justify-between bg-gray-800 px-4 py-2 text-white text-sm">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`}></div>
          <span>{getStatusText()}</span>
        </div>
        {sessionId && (
          <span className="text-gray-400 text-xs">Session: {sessionId.substring(0, 8)}</span>
        )}
      </div>

      {/* Error message display */}
      {errorMessage && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 text-sm">
          {errorMessage}
        </div>
      )}

      {/* Terminal container */}
      <div 
        ref={terminalRef} 
        className="flex-1 bg-[#1e1e1e] overflow-hidden"
        style={{ minHeight: '400px' }}
      />

      {/* Terminal instructions */}
      <div className="bg-gray-100 px-4 py-2 text-xs text-gray-600 border-t border-gray-300">
        <p>
          <span className="font-semibold">Tip:</span> Use standard bash commands to debug the environment. 
          Type <code className="bg-gray-200 px-1 py-0.5 rounded">exit</code> to close the shell, 
          or use the &quot;End Session&quot; button above.
        </p>
      </div>
    </div>
  )
}

Terminal.propTypes = {
  sessionId: PropTypes.string.isRequired,
  websocketUrl: PropTypes.string.isRequired
}

export default Terminal

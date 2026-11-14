# Terminal Component - Technical Specification

## Overview

The Terminal component provides a full-featured browser-based terminal interface using xterm.js, enabling users to interact with Docker containers via WebSocket connections.

## Component Architecture

### Terminal.jsx

**Location:** `frontend/src/components/Terminal.jsx`

**Dependencies:**
```javascript
import { Terminal as XTerm } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import 'xterm/css/xterm.css'
```

**Props:**
```typescript
{
  sessionId: string    // Unique session identifier
  websocketUrl: string // Backend WebSocket endpoint URL
}
```

**State Management:**
```javascript
{
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error',
  errorMessage: string | null
}
```

**Refs:**
```javascript
{
  terminalRef: HTMLDivElement      // DOM mount point
  xtermRef: Terminal               // xterm.js instance
  fitAddonRef: FitAddon           // Resize addon
  socketRef: WebSocket            // WebSocket connection
}
```

## Terminal Configuration

### Visual Theme
```javascript
{
  background: '#1e1e1e',        // Dark background (VS Code style)
  foreground: '#d4d4d4',        // Light gray text
  cursor: '#ffffff',             // White cursor
  
  // ANSI colors
  black: '#000000',
  red: '#cd3131',
  green: '#0dbc79',
  yellow: '#e5e510',
  blue: '#2472c8',
  magenta: '#bc3fbc',
  cyan: '#11a8cd',
  white: '#e5e5e5',
  
  // Bright ANSI colors
  brightBlack: '#666666',
  brightRed: '#f14c4c',
  brightGreen: '#23d18b',
  brightYellow: '#f5f543',
  brightBlue: '#3b8eea',
  brightMagenta: '#d670d6',
  brightCyan: '#29b8db',
  brightWhite: '#e5e5e5'
}
```

### Terminal Settings
```javascript
{
  cursorBlink: true,                                           // Blinking cursor
  fontSize: 14,                                                // 14px font size
  fontFamily: 'Menlo, Monaco, "Courier New", monospace',     // Monospace fonts
  allowTransparency: false,                                    // Solid background
  convertEol: true,                                           // Convert line endings
  scrollback: 1000,                                           // 1000 lines history
  tabStopWidth: 4                                             // 4-space tabs
}
```

## WebSocket Protocol

### Connection URL Format
```
ws://localhost:8000/api/sessions/{sessionId}/terminal?token={jwt_token}
```

### Authentication Flow
1. Extract JWT token from localStorage
2. Append token as query parameter
3. Backend validates token and session ownership
4. Connection accepted or rejected with error code

### Error Codes
| Code | Reason | Description |
|------|--------|-------------|
| 4001 | Authentication required | No token provided |
| 4001 | Invalid authentication token | Token invalid or expired |
| 4003 | Access denied | User doesn't own session |
| 4004 | Session not found | Invalid session ID |
| 4003 | Session not active | Session terminated or timed out |
| 5000 | Internal error | Server-side error |

### Message Types

#### Control Messages (JSON)
```javascript
// Resize notification
{
  type: 'resize',
  cols: number,
  rows: number
}

// Error message
{
  type: 'error',
  message: string
}
```

#### Raw Terminal Data
- Plain text strings containing terminal output
- Binary data not currently supported
- UTF-8 encoding with error replacement

## Event Handlers

### WebSocket Events

#### onopen
```javascript
- Sets connectionStatus to 'connected'
- Clears error message
- Writes welcome message to terminal
- Sends initial terminal size
```

#### onmessage
```javascript
- Checks if message is JSON (control) or raw data
- JSON: Handles error messages
- Raw: Writes directly to terminal
```

#### onclose
```javascript
- Sets connectionStatus to 'disconnected'
- Writes disconnection message to terminal
```

#### onerror
```javascript
- Sets connectionStatus to 'error'
- Sets error message
- Writes error to terminal
```

### Terminal Events

#### onData
```javascript
- Receives user keyboard input
- Sends data to WebSocket if connected
- Handles all keypresses, special keys, and paste
```

#### onResize
```javascript
- Triggered when terminal dimensions change
- Sends resize notification to backend
- Backend adjusts PTY size accordingly
```

### Window Events

#### resize
```javascript
- Triggered on browser window resize
- Calls FitAddon.fit() to adjust terminal size
- Terminal automatically fills container
```

## Lifecycle Management

### Mount (useEffect)
```javascript
1. Validate props (sessionId, websocketUrl)
2. Initialize xterm.js Terminal instance
3. Initialize FitAddon for responsive sizing
4. Mount terminal to DOM element
5. Fit terminal to container
6. Connect WebSocket
7. Register window resize listener
```

### Unmount (cleanup)
```javascript
1. Remove window resize listener
2. Close WebSocket connection
3. Dispose xterm.js instance
4. Clean up refs
```

## Component Structure

```jsx
<div className="flex flex-col h-full">
  {/* Connection status bar */}
  <div className="status-bar">
    <status-indicator />
    <session-id-display />
  </div>

  {/* Error message */}
  {errorMessage && <error-banner />}

  {/* Terminal container */}
  <div ref={terminalRef} className="terminal-container" />

  {/* Instructions footer */}
  <div className="instructions-footer">
    <usage-tips />
  </div>
</div>
```

## Integration with ChallengeDetail

### Usage Example
```jsx
{session ? (
  <Terminal
    sessionId={session.session_id}
    websocketUrl={session.websocket_url}
  />
) : (
  <NoSessionPlaceholder />
)}
```

### Session Flow
1. User clicks "Start Challenge"
2. ChallengeDetail calls POST /api/sessions
3. Backend creates container, returns session data
4. ChallengeDetail renders Terminal component
5. Terminal connects via WebSocket
6. User interacts with container shell
7. User clicks "Check Solution" or "End Session"
8. Terminal disconnects, container terminated

## Performance Considerations

### Terminal Rendering
- xterm.js uses canvas rendering for optimal performance
- Handles thousands of lines without lag
- Automatic virtualization of scrollback buffer

### WebSocket Communication
- Minimal overhead for text-based protocol
- No buffering delays - real-time bidirectional relay
- 4KB read chunks from Docker exec socket
- 10ms polling interval for socket data

### Memory Management
- Terminal scrollback limited to 1000 lines
- Proper cleanup prevents memory leaks
- WebSocket and xterm instances disposed on unmount

## Browser Compatibility

### Supported Browsers
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Required Features
- WebSocket API
- ES6 Modules
- CSS Grid/Flexbox
- Canvas API

## Security Considerations

### Token Handling
- JWT token in query parameter (visible in network logs)
- Consider alternatives for production:
  - Custom WebSocket subprotocol with token
  - Short-lived session-specific tokens
  - Backend-initiated connections with session cookies

### Input Validation
- All user input goes through Docker exec (sandboxed)
- No direct command injection risk
- Container security constraints apply

### XSS Protection
- xterm.js escapes all output
- No HTML rendering in terminal
- ANSI escape sequences parsed safely

## Troubleshooting

### Terminal Not Connecting
1. Check browser console for WebSocket errors
2. Verify session ID is valid
3. Confirm backend WebSocket endpoint is running
4. Check authentication token is present and valid

### Terminal Output Garbled
1. Verify UTF-8 encoding
2. Check terminal size matches container PTY
3. Ensure TERM environment variable is set

### Commands Not Executing
1. Verify WebSocket readyState is OPEN
2. Check Docker exec process is running
3. Confirm container is active and not stopped

### Performance Issues
1. Reduce scrollback buffer size
2. Clear terminal periodically
3. Check Docker container resource limits

## Testing Strategy

### Unit Tests (Vitest)
```javascript
describe('Terminal Component', () => {
  test('renders without crashing', () => {})
  test('initializes xterm instance', () => {})
  test('connects WebSocket on mount', () => {})
  test('displays connection status', () => {})
  test('handles WebSocket messages', () => {})
  test('sends terminal input to WebSocket', () => {})
  test('cleans up on unmount', () => {})
})
```

### Integration Tests
```javascript
describe('Terminal Integration', () => {
  test('connects to live session', () => {})
  test('executes commands in container', () => {})
  test('receives real-time output', () => {})
  test('handles session termination', () => {})
})
```

### Manual Testing Checklist
- [ ] Terminal renders correctly
- [ ] Connects within 2 seconds
- [ ] Commands execute immediately
- [ ] Output displays in real-time
- [ ] Command history works (up/down arrows)
- [ ] Cursor navigation works (left/right arrows)
- [ ] Tab completion works
- [ ] Copy/paste works
- [ ] Terminal resizes with window
- [ ] Status indicator updates correctly
- [ ] Error messages display clearly
- [ ] Cleanup happens on unmount

## Future Enhancements

### Potential Improvements
1. **File Upload/Download**: Drag-and-drop files into terminal
2. **Terminal Recording**: Capture and replay sessions
3. **Multi-tab Support**: Multiple terminals per session
4. **Terminal Sharing**: Collaborative debugging
5. **Search**: Find text in terminal output
6. **Themes**: Customizable color schemes
7. **Font Size Control**: User-adjustable font size
8. **Full-screen Mode**: Maximize terminal
9. **Connection Retry**: Automatic reconnection logic
10. **Bandwidth Optimization**: Compress WebSocket data

### Additional Addons
- `xterm-addon-search`: Text search
- `xterm-addon-web-links`: Clickable URLs
- `xterm-addon-unicode11`: Extended Unicode support
- `xterm-addon-serialize`: Session serialization

## References

- [xterm.js Documentation](https://xtermjs.org/)
- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)

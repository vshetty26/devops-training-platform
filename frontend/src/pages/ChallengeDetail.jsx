import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Terminal from '../components/Terminal'
import { apiGet, apiPost, apiDelete } from '../utils/api'

/**
 * ChallengeDetail Component
 * 
 * Displays challenge information and provides session management with
 * integrated terminal interface.
 * 
 * Requirements:
 * - 2.4: Navigate to challenge detail page
 * - 3.1: Provision new Docker container when starting challenge
 * - 4.1: Display terminal interface for active sessions
 * - 5.5: Display remaining time during session
 * - 6.1: Provide check solution button
 * - 10.2: Build challenge detail with session controls
 */
const ChallengeDetail = () => {
  const { id } = useParams()
  const navigate = useNavigate()
  
  const [challenge, setChallenge] = useState(null)
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [creating, setCreating] = useState(false)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [timeRemaining, setTimeRemaining] = useState(null)

  // Fetch challenge details
  useEffect(() => {
    const fetchChallenge = async () => {
      try {
        setLoading(true)
        const data = await apiGet(`http://localhost:8000/api/challenges/${id}`)
        setChallenge(data)
        setError(null)
      } catch (err) {
        setError(`Failed to load challenge: ${err.message}`)
        console.error('Error fetching challenge:', err)
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchChallenge()
    }
  }, [id])

  // Countdown timer for session timeout
  useEffect(() => {
    if (!session) {
      setTimeRemaining(null)
      return
    }

    // Calculate time remaining based on session creation time and timeout
    const updateTimeRemaining = () => {
      const now = Date.now()
      const sessionStart = new Date(session.created_at || Date.now()).getTime()
      const timeoutMs = session.timeout_seconds * 1000
      const elapsed = now - sessionStart
      const remaining = Math.max(0, timeoutMs - elapsed)
      
      setTimeRemaining(remaining)

      // If time expired, clear session
      if (remaining === 0) {
        setSession(null)
        setError('Session timed out after 30 minutes')
      }
    }

    // Update immediately
    updateTimeRemaining()

    // Update every second
    const interval = setInterval(updateTimeRemaining, 1000)

    return () => clearInterval(interval)
  }, [session])

  /**
   * Start a new challenge session
   * Requirement 3.1: Provision Docker container within 10 seconds
   */
  const startSession = async () => {
    try {
      setCreating(true)
      setError(null)
      setValidationResult(null)
      
      const response = await apiPost('http://localhost:8000/api/sessions', {
        challenge_id: id
      })
      
      // Store session with creation time for countdown
      setSession({
        ...response,
        created_at: Date.now()
      })
      
    } catch (err) {
      setError(`Failed to start session: ${err.message}`)
      console.error('Error starting session:', err)
    } finally {
      setCreating(false)
    }
  }

  /**
   * Terminate active session
   * Requirement 5.2: Terminate container when requested
   */
  const endSession = useCallback(async () => {
    if (!session) return

    try {
      await apiDelete(`http://localhost:8000/api/sessions/${session.session_id}`)
      setSession(null)
      setValidationResult(null)
      setError(null)
    } catch (err) {
      setError(`Failed to end session: ${err.message}`)
      console.error('Error ending session:', err)
    }
  }, [session])

  /**
   * Validate user's solution
   * Requirement 6.1: Execute validation when user clicks check button
   */
  const validateSolution = async () => {
    if (!session) return

    try {
      setValidating(true)
      setValidationResult(null)
      
      const response = await apiPost(
        `http://localhost:8000/api/sessions/${session.session_id}/validate`,
        {}
      )
      
      setValidationResult(response)
      
      // If successful, end session after showing result
      if (response.success) {
        setTimeout(() => {
          endSession()
          // Optionally navigate to challenges or leaderboard
          // navigate('/challenges')
        }, 3000)
      }
      
    } catch (err) {
      setError(`Failed to validate solution: ${err.message}`)
      console.error('Error validating solution:', err)
    } finally {
      setValidating(false)
    }
  }

  /**
   * Format time remaining for display
   * Requirement 5.5: Display remaining time to user
   */
  const formatTimeRemaining = () => {
    if (timeRemaining === null) return ''
    
    const seconds = Math.floor(timeRemaining / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading challenge...</p>
        </div>
      </div>
    )
  }

  if (!challenge) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Challenge Not Found</h2>
          <p className="text-gray-600 mb-6">The requested challenge could not be found.</p>
          <button
            onClick={() => navigate('/challenges')}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            Back to Challenges
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/challenges')}
                className="text-blue-600 hover:text-blue-800"
              >
                ← Back to Challenges
              </button>
              <h1 className="text-2xl font-bold text-gray-800">{challenge.title}</h1>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                challenge.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                challenge.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {challenge.difficulty}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              {session && timeRemaining !== null && (
                <div className="text-sm">
                  <span className="text-gray-600">Time Remaining:</span>
                  <span className={`ml-2 font-mono font-bold ${
                    timeRemaining < 300000 ? 'text-red-600' : 'text-gray-800'
                  }`}>
                    {formatTimeRemaining()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left sidebar - Challenge info */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h2 className="text-xl font-bold text-gray-800 mb-4">Challenge Brief</h2>
              <p className="text-gray-700 mb-6 whitespace-pre-wrap">{challenge.brief}</p>

              {/* Session controls */}
              <div className="space-y-3">
                {!session ? (
                  <button
                    onClick={startSession}
                    disabled={creating}
                    className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {creating ? 'Starting Session...' : 'Start Challenge'}
                  </button>
                ) : (
                  <>
                    <button
                      onClick={validateSolution}
                      disabled={validating}
                      className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                    >
                      {validating ? 'Validating...' : 'Check Solution'}
                    </button>
                    <button
                      onClick={endSession}
                      className="w-full bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
                    >
                      End Session
                    </button>
                  </>
                )}
              </div>

              {/* Error display */}
              {error && (
                <div className="mt-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Validation result display */}
              {validationResult && (
                <div className={`mt-4 px-4 py-3 rounded border ${
                  validationResult.success
                    ? 'bg-green-100 border-green-400 text-green-700'
                    : 'bg-yellow-100 border-yellow-400 text-yellow-700'
                }`}>
                  <p className="font-semibold">
                    {validationResult.success ? '✓ Success!' : '✗ Not quite right'}
                  </p>
                  <p className="text-sm mt-1">{validationResult.message}</p>
                  {validationResult.hint && (
                    <p className="text-sm mt-2">
                      <span className="font-semibold">Hint:</span> {validationResult.hint}
                    </p>
                  )}
                </div>
              )}

              {/* Session info */}
              {session && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  <h3 className="text-sm font-semibold text-gray-600 mb-2">Session Info</h3>
                  <div className="text-xs text-gray-500 space-y-1">
                    <p>Session ID: {session.session_id.substring(0, 12)}...</p>
                    <p>Container: {session.container_id.substring(0, 12)}...</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right main area - Terminal */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: '600px' }}>
              {session ? (
                <Terminal
                  sessionId={session.session_id}
                  websocketUrl={session.websocket_url}
                />
              ) : (
                <div className="h-full flex items-center justify-center bg-gray-50">
                  <div className="text-center">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-24 h-24 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <p className="text-gray-600 text-lg font-semibold">No Active Session</p>
                    <p className="text-gray-500 mt-2">Start the challenge to access the terminal</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChallengeDetail

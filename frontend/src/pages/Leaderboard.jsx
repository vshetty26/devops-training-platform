import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiGet } from '../utils/api'

/**
 * Leaderboard Component
 * 
 * Displays user rankings with completion times for challenges.
 * Supports both global leaderboard (all challenges) and per-challenge views.
 * 
 * Requirements:
 * - 9.1: Platform SHALL display a leaderboard page with user rankings
 * - 9.2: Platform SHALL rank users by challenge completion, then by completion time
 * - 9.3: Platform SHALL display username and completion time for each entry
 * - 9.4: Leaderboard SHALL update within 5 seconds after challenge completion
 * - 9.5: Platform SHALL provide separate leaderboard views per challenge
 */
const Leaderboard = () => {
  const [leaderboardData, setLeaderboardData] = useState([])
  const [challenges, setChallenges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('global') // 'global' or 'challenge'
  const [selectedChallenge, setSelectedChallenge] = useState(null)
  const navigate = useNavigate()

  // Fetch challenges list on component mount
  useEffect(() => {
    const fetchChallenges = async () => {
      try {
        const data = await apiGet('http://localhost:8000/api/challenges')
        setChallenges(data)
        if (data.length > 0 && !selectedChallenge) {
          setSelectedChallenge(data[0].id)
        }
      } catch (err) {
        console.error('Failed to load challenges:', err)
      }
    }

    fetchChallenges()
  }, [])

  // Fetch leaderboard data based on current view mode and selected challenge
  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        setLoading(true)
        setError(null)
        
        let url = 'http://localhost:8000/api/leaderboard'
        if (viewMode === 'challenge' && selectedChallenge) {
          url = `http://localhost:8000/api/leaderboard/${selectedChallenge}`
        }
        
        const data = await apiGet(url)
        setLeaderboardData(data)
      } catch (err) {
        setError(err.message || 'Failed to load leaderboard')
      } finally {
        setLoading(false)
      }
    }

    if (viewMode === 'global' || (viewMode === 'challenge' && selectedChallenge)) {
      fetchLeaderboard()
    }
  }, [viewMode, selectedChallenge])

  /**
   * Format completion time in seconds to a human-readable string
   * Examples: "45s", "2m 35s", "1h 5m 30s"
   * 
   * @param {number} seconds - Completion time in seconds
   * @returns {string} Formatted time string
   */
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${seconds}s`
    }
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const remainingSeconds = seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${remainingSeconds}s`
    }
    
    return `${minutes}m ${remainingSeconds}s`
  }

  /**
   * Get medal emoji for top 3 ranks
   * 
   * @param {number} rank - User rank position
   * @returns {string|null} Medal emoji or null
   */
  const getMedalForRank = (rank) => {
    const medals = {
      1: '🥇',
      2: '🥈',
      3: '🥉'
    }
    return medals[rank] || null
  }

  /**
   * Get the selected challenge title
   * 
   * @returns {string} Challenge title or empty string
   */
  const getSelectedChallengeTitle = () => {
    if (!selectedChallenge) return ''
    const challenge = challenges.find(c => c.id === selectedChallenge)
    return challenge ? challenge.title : ''
  }

  if (loading && leaderboardData.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Leaderboard</h1>
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Leaderboard</h1>
          <p className="text-gray-600">
            Top performers ranked by completion time
          </p>
        </div>

        {/* View Mode Toggle */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Toggle Buttons */}
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('global')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  viewMode === 'global'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Global Rankings
              </button>
              <button
                onClick={() => setViewMode('challenge')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  viewMode === 'challenge'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Per Challenge
              </button>
            </div>

            {/* Challenge Selector (visible in challenge mode) */}
            {viewMode === 'challenge' && challenges.length > 0 && (
              <div className="flex-1 md:max-w-md">
                <label htmlFor="challenge-select" className="block text-sm font-medium text-gray-700 mb-2">
                  Select Challenge
                </label>
                <select
                  id="challenge-select"
                  value={selectedChallenge || ''}
                  onChange={(e) => setSelectedChallenge(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  {challenges.map((challenge) => (
                    <option key={challenge.id} value={challenge.id}>
                      {challenge.title}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">Error: {error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-2 text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        )}

        {/* Leaderboard Table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          {/* Table Header */}
          <div className="bg-gray-50 border-b border-gray-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-gray-900">
              {viewMode === 'global' 
                ? 'Top Fastest Completions' 
                : `${getSelectedChallengeTitle()} Rankings`}
            </h2>
          </div>

          {/* Table Content */}
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : leaderboardData.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No completions yet</p>
              <p className="text-gray-400 text-sm mt-2">
                Be the first to complete a challenge!
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Username
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Completion Time
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leaderboardData.map((entry) => (
                    <tr 
                      key={`${entry.user_id}-${entry.timestamp}`}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      {/* Rank Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">{getMedalForRank(entry.rank)}</span>
                          <span className="text-lg font-semibold text-gray-900">
                            #{entry.rank}
                          </span>
                        </div>
                      </td>

                      {/* Username Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {entry.username}
                        </div>
                      </td>

                      {/* Completion Time Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <svg 
                            className="w-4 h-4 text-gray-400 mr-2" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" 
                            />
                          </svg>
                          <span className="text-sm text-gray-900 font-mono">
                            {formatTime(entry.completion_time_seconds)}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Navigation Links */}
        <div className="mt-8 pt-6 border-t border-gray-200 flex gap-4">
          <button
            onClick={() => navigate('/challenges')}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            ← Back to Challenges
          </button>
        </div>
      </div>
    </div>
  )
}

export default Leaderboard

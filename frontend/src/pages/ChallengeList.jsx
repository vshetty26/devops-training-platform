import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiGet } from '../utils/api'

/**
 * ChallengeList Component
 * 
 * Displays all available challenges with difficulty indicators and completion status.
 * Users can click on a challenge to navigate to its detail page.
 * For completed challenges, shows the user's best completion time.
 * 
 * Requirements:
 * - 2.1: Platform SHALL display all available challenges on the challenge list page
 * - 2.2: Platform SHALL display difficulty level tags for each challenge
 * - 2.3: Platform SHALL display a short incident description for each challenge
 * - 2.4: Platform SHALL navigate to the challenge detail page when a user clicks a challenge
 * - 2.5: Platform SHALL indicate challenge completion status for the authenticated user
 * - 1.3: Platform SHALL associate all challenge attempts with the authenticated user identifier
 * - 12.2: Frontend SHALL use Tailwind CSS for styling
 */
const ChallengeList = () => {
  const [challenges, setChallenges] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  // Fetch challenges on component mount
  useEffect(() => {
    const fetchChallenges = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await apiGet('http://localhost:8000/api/challenges')
        setChallenges(data)
      } catch (err) {
        setError(err.message || 'Failed to load challenges')
      } finally {
        setLoading(false)
      }
    }

    fetchChallenges()
  }, [])

  // Navigate to challenge detail page
  const handleChallengeClick = (challengeId) => {
    navigate(`/challenges/${challengeId}`)
  }

  // Format completion time from seconds to readable format
  const formatCompletionTime = (seconds) => {
    if (!seconds) return ''
    
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    
    if (minutes === 0) {
      return `${remainingSeconds}s`
    }
    return `${minutes}m ${remainingSeconds}s`
  }

  // Get difficulty badge color based on difficulty level
  const getDifficultyColor = (difficulty) => {
    const colors = {
      easy: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      hard: 'bg-red-100 text-red-800'
    }
    return colors[difficulty.toLowerCase()] || 'bg-gray-100 text-gray-800'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Challenges</h1>
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Challenges</h1>
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800">Error: {error}</p>
            <button 
              onClick={() => window.location.reload()}
              className="mt-2 text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">DevOps Arena Challenges</h1>
          <p className="text-gray-600">
            Practice your troubleshooting skills with real-world DevOps scenarios
          </p>
        </div>

        {/* Challenge Grid */}
        {challenges.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">No challenges available</p>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {challenges.map((challenge) => (
              <div
                key={challenge.id}
                onClick={() => handleChallengeClick(challenge.id)}
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer overflow-hidden"
              >
                <div className="p-6">
                  {/* Title and Completion Status */}
                  <div className="flex items-start justify-between mb-3">
                    <h2 className="text-xl font-semibold text-gray-900 flex-1">
                      {challenge.title}
                    </h2>
                    {challenge.completed && (
                      <span className="ml-2 flex-shrink-0">
                        <svg 
                          className="w-6 h-6 text-green-500" 
                          fill="currentColor" 
                          viewBox="0 0 20 20"
                        >
                          <path 
                            fillRule="evenodd" 
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                      </span>
                    )}
                  </div>

                  {/* Difficulty Badge */}
                  <div className="mb-4">
                    <span 
                      className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getDifficultyColor(challenge.difficulty)}`}
                    >
                      {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
                    </span>
                  </div>

                  {/* Brief Description */}
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {challenge.brief}
                  </p>

                  {/* Completion Time */}
                  {challenge.completed && challenge.completion_time_seconds && (
                    <div className="mt-3">
                      <span className="inline-flex items-center text-sm text-green-700 font-medium">
                        <svg 
                          className="w-4 h-4 mr-1" 
                          fill="currentColor" 
                          viewBox="0 0 20 20"
                        >
                          <path 
                            fillRule="evenodd" 
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" 
                            clipRule="evenodd" 
                          />
                        </svg>
                        Best time: {formatCompletionTime(challenge.completion_time_seconds)}
                      </span>
                    </div>
                  )}

                  {/* Action Hint */}
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <span className="text-blue-600 text-sm font-medium hover:text-blue-700">
                      Start Challenge →
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Navigation Links */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={() => navigate('/leaderboard')}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            View Leaderboard →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChallengeList

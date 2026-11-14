import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import ChallengeList from './pages/ChallengeList'
import ChallengeDetail from './pages/ChallengeDetail'
import Leaderboard from './pages/Leaderboard'

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-100">
          <Routes>
            <Route path="/" element={<Login />} />
            <Route 
              path="/challenges" 
              element={
                <ProtectedRoute>
                  <ChallengeList />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/challenges/:id" 
              element={
                <ProtectedRoute>
                  <ChallengeDetail />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/leaderboard" 
              element={
                <ProtectedRoute>
                  <Leaderboard />
                </ProtectedRoute>
              } 
            />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App

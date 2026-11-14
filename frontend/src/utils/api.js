/**
 * API Utility Functions
 * 
 * Provides helper functions for making authenticated API requests.
 * Automatically includes JWT token from localStorage in request headers.
 * 
 * Requirements:
 * - 1.3: Associate all challenge attempts with authenticated user identifier
 */

/**
 * Get the authentication token from localStorage
 * @returns {string|null} JWT token or null if not found
 */
export const getAuthToken = () => {
  return localStorage.getItem('token')
}

/**
 * Create headers object with authentication token
 * @param {Object} additionalHeaders - Additional headers to include
 * @returns {Object} Headers object with Authorization header
 */
export const getAuthHeaders = (additionalHeaders = {}) => {
  const token = getAuthToken()
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...additionalHeaders
  }
}

/**
 * Make an authenticated API request
 * @param {string} url - API endpoint URL
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export const authenticatedFetch = async (url, options = {}) => {
  const headers = getAuthHeaders(options.headers)
  
  const response = await fetch(url, {
    ...options,
    headers
  })

  // If unauthorized, clear token and redirect to login
  if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/'
  }

  return response
}

/**
 * Make a GET request to the API
 * @param {string} url - API endpoint URL
 * @returns {Promise<any>} Parsed JSON response
 */
export const apiGet = async (url) => {
  const response = await authenticatedFetch(url)
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

/**
 * Make a POST request to the API
 * @param {string} url - API endpoint URL
 * @param {Object} data - Request body data
 * @returns {Promise<any>} Parsed JSON response
 */
export const apiPost = async (url, data) => {
  const response = await authenticatedFetch(url, {
    method: 'POST',
    body: JSON.stringify(data)
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

/**
 * Make a DELETE request to the API
 * @param {string} url - API endpoint URL
 * @returns {Promise<any>} Parsed JSON response
 */
export const apiDelete = async (url) => {
  const response = await authenticatedFetch(url, {
    method: 'DELETE'
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

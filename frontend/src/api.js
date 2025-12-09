const API_BASE_URL = 'http://localhost:8000/api'

// Helper function to get auth token
const getAuthToken = () => {
  return localStorage.getItem('authToken')
}

// Helper function to make authenticated requests
const apiRequest = async (url, options = {}) => {
  const token = getAuthToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  })
  
  if (response.status === 401) {
    // Token expired or invalid - clear auth and redirect to login
    localStorage.removeItem('authToken')
    localStorage.removeItem('authUser')
    localStorage.removeItem('refreshToken')
    window.location.href = '/'
    throw new Error('Unauthorized - please log in again')
  }
  
  return response
}

export const api = {
  // Locations
  getLocations: async () => {
    const response = await apiRequest('/locations/')
    if (!response.ok) {
      throw new Error('Failed to load locations')
    }
    return response.json()
  },

  createLocation: async (name) => {
    const response = await apiRequest('/locations/', {
      method: 'POST',
      body: JSON.stringify({ name }),
    })
    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch (e) {
        // If response is not JSON (e.g., HTML error page), use status text
        throw new Error(`Failed to create location: ${response.status} ${response.statusText}`)
      }
      throw new Error(error.name?.[0] || error.detail || 'Failed to create location')
    }
    return response.json()
  },

  updateLocation: async (id, name) => {
    const response = await apiRequest(`/locations/${id}/`, {
      method: 'PUT',
      body: JSON.stringify({ name }),
    })
    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch (e) {
        // If response is not JSON (e.g., HTML error page), use status text
        throw new Error(`Failed to update location: ${response.status} ${response.statusText}`)
      }
      throw new Error(error.name?.[0] || error.detail || 'Failed to update location')
    }
    return response.json()
  },

  deleteLocation: async (id, transferToId = null) => {
    const options = {
      method: 'DELETE',
    }
    
    if (transferToId) {
      options.body = JSON.stringify({ transfer_to_location_id: transferToId })
    }
    
    const response = await apiRequest(`/locations/${id}/`, options)
    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.error || error.detail || 'Failed to delete location')
    }
    return true
  },

  getInventoryByLocation: async (locationId) => {
    const response = await apiRequest(`/inventory/?location=${locationId}`)
    if (!response.ok) {
      throw new Error('Failed to load inventory')
    }
    return response.json()
  },

  // Items
  getItem: async (itemId) => {
    try {
      const response = await apiRequest(`/items/by-item-id/${itemId}/`)
      if (response.status === 404) {
        return null
      }
      if (!response.ok) {
        throw new Error('Failed to load item')
      }
      return response.json()
    } catch (err) {
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        throw new Error('Cannot connect to backend server. Make sure Django is running on http://localhost:8000')
      }
      throw err
    }
  },

  createItem: async (itemId) => {
    const response = await apiRequest('/items/', {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to create item')
    }
    return response.json()
  },

  updateItemImage: async (itemId, imageUrl) => {
    const response = await apiRequest(`/items/by-item-id/${itemId}/`, {
      method: 'PATCH',
      body: JSON.stringify({ image_url: imageUrl }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to update item image')
    }
    return response.json()
  },

  // Inventory
  getInventory: async (itemId) => {
    const response = await apiRequest(`/inventory/by-item-id/${itemId}/`)
    if (response.status === 404) {
      return []
    }
    if (!response.ok) {
      throw new Error('Failed to load inventory')
    }
    return response.json()
  },

  getAllInventory: async () => {
    const response = await apiRequest('/inventory/')
    if (!response.ok) {
      throw new Error('Failed to load inventory')
    }
    return response.json()
  },

  // Transactions
  receiveStock: async (itemId, locationId, quantity) => {
    const response = await apiRequest('/transactions/', {
      method: 'POST',
      body: JSON.stringify({
        item_id: itemId,
        location_id: locationId,
        transaction_type: 'RECEIVE',
        quantity: quantity,
      }),
    })
    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch (e) {
        // If response is not JSON (e.g., HTML error page), use status text
        throw new Error(`Failed to receive stock: ${response.status} ${response.statusText}`)
      }
      throw new Error(error.error || error.detail || 'Failed to receive stock')
    }
    return response.json()
  },

  shipStock: async (itemId, locationId, quantity) => {
    const response = await apiRequest('/transactions/', {
      method: 'POST',
      body: JSON.stringify({
        item_id: itemId,
        location_id: locationId,
        transaction_type: 'SHIP',
        quantity: quantity,
      }),
    })
    if (!response.ok) {
      let error
      try {
        error = await response.json()
      } catch (e) {
        // If response is not JSON (e.g., HTML error page), use status text
        throw new Error(`Failed to ship stock: ${response.status} ${response.statusText}`)
      }
      throw new Error(error.error || error.detail || 'Failed to ship stock')
    }
    return response.json()
  },

  // Journal
  getJournalEntries: async () => {
    const response = await apiRequest('/journal/')
    if (!response.ok) {
      throw new Error('Failed to load journal entries')
    }
    return response.json()
  },

  getJournalByItem: async (itemId) => {
    const response = await apiRequest(`/journal/by_item/?item_id=${itemId}`)
    if (!response.ok) {
      throw new Error('Failed to load journal entries')
    }
    return response.json()
  },

  getJournalByLocation: async (locationId) => {
    const response = await apiRequest(`/journal/by_location/?location_id=${locationId}`)
    if (!response.ok) {
      throw new Error('Failed to load journal entries')
    }
    return response.json()
  },
}

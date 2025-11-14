import { useState, useEffect } from 'react'
import './App.css'
import { api } from './api'

function App() {
  const [step, setStep] = useState('itemId') // 'itemId', 'receive', 'ship', 'inventory', 'journal', 'fullInventory', 'locations'
  const [itemId, setItemId] = useState('')
  const [item, setItem] = useState(null)
  const [inventory, setInventory] = useState([])
  const [fullInventory, setFullInventory] = useState([])
  const [locations, setLocations] = useState([])
  const [journalEntries, setJournalEntries] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showOnlyInStock, setShowOnlyInStock] = useState(false)
  
  // Transaction form state
  const [quantity, setQuantity] = useState('')
  const [selectedLocationId, setSelectedLocationId] = useState('')
  const [transactionType, setTransactionType] = useState('') // 'RECEIVE' or 'SHIP'
  const [selectedLocationName, setSelectedLocationName] = useState('')
  
  // Journal filter state
  const [journalFilter, setJournalFilter] = useState('all') // 'all', 'item', 'location'
  const [filterItemId, setFilterItemId] = useState('')
  const [filterLocationId, setFilterLocationId] = useState('')
  
  // Location management state
  const [editingLocation, setEditingLocation] = useState(null)
  const [newLocationName, setNewLocationName] = useState('')
  const [editLocationName, setEditLocationName] = useState('')
  const [deletingLocation, setDeletingLocation] = useState(null)
  const [transferToLocationId, setTransferToLocationId] = useState('')

  useEffect(() => {
    // Load locations on mount
    loadLocations()
  }, [])

  const loadLocations = async () => {
    try {
      const data = await api.getLocations()
      setLocations(data)
      setError('') // Clear any previous errors
    } catch (err) {
      console.error('Error loading locations:', err)
      // Show helpful error message
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError') || err.message.includes('Cannot connect')) {
        setError('⚠️ Cannot connect to backend server. Make sure Django is running on http://localhost:8000')
      } else {
        setError('Failed to load locations: ' + err.message)
      }
    }
  }

  const loadInventory = async (itemId, currentItem = null) => {
    try {
      const inventoryData = await api.getInventory(itemId)
      
      // Create a map of location_id -> inventory for quick lookup
      const inventoryMap = new Map()
      inventoryData.forEach(inv => {
        inventoryMap.set(inv.location.id, inv)
      })
      
      // Merge with all locations, showing 0 for locations without inventory
      const mergedInventory = locations.map(location => {
        const existingInv = inventoryMap.get(location.id)
        if (existingInv) {
          return existingInv
        } else {
          // Create a placeholder inventory entry with 0 quantity
          return {
            id: null,
            item: currentItem || item,
            location: location,
            quantity: 0,
            created_at: null,
            updated_at: null
          }
        }
      })
      
      setInventory(mergedInventory)
      return mergedInventory
    } catch (err) {
      // If no inventory exists, return locations with 0 quantity
      const emptyInventory = locations.map(location => ({
        id: null,
        item: currentItem || item,
        location: location,
        quantity: 0,
        created_at: null,
        updated_at: null
      }))
      setInventory(emptyInventory)
      return emptyInventory
    }
  }

  const handleItemIdSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      // Try to get existing item
      let itemData = await api.getItem(itemId)
      
      // If item doesn't exist, create it
      if (!itemData) {
        itemData = await api.createItem(itemId)
      }
      
      setItem(itemData)
      
      // Check inventory (pass itemData so it's available in loadInventory)
      const inventoryData = await loadInventory(itemId, itemData)
      
      // Check if all locations have 0 quantity
      const hasAnyStock = inventoryData.some(inv => inv.quantity > 0)
      
      if (!hasAnyStock) {
        // No inventory at any location - show receive form
        setStep('receive')
        setTransactionType('RECEIVE')
      } else {
        // Has inventory at some location - show inventory table
        setStep('inventory')
      }
    } catch (err) {
      setError(err.message || 'Failed to process item ID')
    } finally {
      setLoading(false)
    }
  }

  const handleTransaction = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (!quantity || !selectedLocationId) {
      setError('Please fill in all fields')
      setLoading(false)
      return
    }

    const qty = parseInt(quantity)
    if (qty <= 0) {
      setError('Quantity must be greater than 0')
      setLoading(false)
      return
    }

    try {
      if (transactionType === 'RECEIVE') {
        await api.receiveStock(itemId, parseInt(selectedLocationId), qty)
        setSuccess(`Successfully received ${quantity} units at ${selectedLocationName}`)
      } else if (transactionType === 'SHIP') {
        await api.shipStock(itemId, parseInt(selectedLocationId), qty)
        setSuccess(`Successfully shipped ${quantity} units from ${selectedLocationName}`)
      }
      
      // Reload inventory
      await loadInventory(itemId, item)
      
      // Reset form and go back to inventory view
      setQuantity('')
      setSelectedLocationId('')
      setStep('inventory')
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess('')
      }, 3000)
    } catch (err) {
      setError(err.message || `Failed to ${transactionType.toLowerCase()} stock`)
    } finally {
      setLoading(false)
    }
  }

  const handleReceiveClick = (locationId, locationName) => {
    setSelectedLocationId(locationId)
    setSelectedLocationName(locationName)
    setTransactionType('RECEIVE')
    setQuantity('')
    setStep('receive')
  }

  const handleShipClick = (locationId, locationName) => {
    setSelectedLocationId(locationId)
    setSelectedLocationName(locationName)
    setTransactionType('SHIP')
    setQuantity('')
    setStep('ship')
  }

  const handleReset = () => {
    setStep('itemId')
    setItemId('')
    setItem(null)
    setInventory([])
    setQuantity('')
    setSelectedLocationId('')
    setSelectedLocationName('')
    setTransactionType('')
    setError('')
    setSuccess('')
  }

  const handleItemIdClick = async (clickedItemId) => {
    setItemId(clickedItemId)
    setError('')
    setSuccess('')
    setLoading(true)
    setStep('itemId')

    try {
      // Try to get existing item
      let itemData = await api.getItem(clickedItemId)
      
      // If item doesn't exist, create it
      if (!itemData) {
        itemData = await api.createItem(clickedItemId)
      }
      
      setItem(itemData)
      
      // Check inventory
      const inventoryData = await loadInventory(clickedItemId, itemData)
      
      // Check if all locations have 0 quantity
      const hasAnyStock = inventoryData.some(inv => inv.quantity > 0)
      
      if (!hasAnyStock) {
        // No inventory at any location - show receive form
        setStep('receive')
        setTransactionType('RECEIVE')
      } else {
        // Has inventory at some location - show inventory table
        setStep('inventory')
      }
    } catch (err) {
      setError(err.message || 'Failed to process item ID')
    } finally {
      setLoading(false)
    }
  }

  const getLocationQuantity = (locationId) => {
    const inv = inventory.find(inv => inv.location.id === locationId)
    return inv ? inv.quantity : 0
  }

  const loadJournalEntries = async () => {
    setLoading(true)
    setError('')
    try {
      let data
      if (journalFilter === 'item' && filterItemId) {
        data = await api.getJournalByItem(filterItemId)
      } else if (journalFilter === 'location' && filterLocationId) {
        data = await api.getJournalByLocation(filterLocationId)
      } else {
        data = await api.getJournalEntries()
      }
      setJournalEntries(data)
    } catch (err) {
      setError(err.message || 'Failed to load journal entries')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (step === 'journal') {
      loadJournalEntries()
    } else if (step === 'fullInventory') {
      loadFullInventory()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, journalFilter, filterItemId, filterLocationId])

  const loadFullInventory = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await api.getAllInventory()
      setFullInventory(data)
    } catch (err) {
      setError(err.message || 'Failed to load full inventory')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const handleCreateLocation = async (e) => {
    e.preventDefault()
    if (!newLocationName.trim()) {
      setError('Location name is required')
      return
    }
    
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      await api.createLocation(newLocationName.trim())
      setSuccess(`Location "${newLocationName.trim()}" created successfully`)
      setNewLocationName('')
      await loadLocations()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.message || 'Failed to create location')
    } finally {
      setLoading(false)
    }
  }

  const handleEditLocation = (location) => {
    setEditingLocation(location)
    setEditLocationName(location.name)
    setError('')
    setSuccess('')
  }

  const handleUpdateLocation = async (e) => {
    e.preventDefault()
    if (!editLocationName.trim()) {
      setError('Location name is required')
      return
    }
    
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      await api.updateLocation(editingLocation.id, editLocationName.trim())
      setSuccess(`Location updated successfully`)
      setEditingLocation(null)
      setEditLocationName('')
      await loadLocations()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      setError(err.message || 'Failed to update location')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteLocation = async (locationId, locationName) => {
    // Check if location has inventory first
    try {
      const locationInventory = await api.getInventoryByLocation(locationId)
      const hasStock = locationInventory.some(inv => inv.quantity > 0)
      
      if (hasStock) {
        // Show transfer dialog
        setDeletingLocation({ id: locationId, name: locationName })
        setTransferToLocationId('')
        return
      }
    } catch (err) {
      // If check fails, proceed with normal deletion attempt
      console.error('Error checking inventory:', err)
    }
    
    // No inventory, proceed with normal deletion
    if (!window.confirm(`Are you sure you want to delete location "${locationName}"? This action cannot be undone.`)) {
      return
    }
    
    await performDeleteLocation(locationId, locationName)
  }

  const performDeleteLocation = async (locationId, locationName, transferToId = null) => {
    setLoading(true)
    setError('')
    setSuccess('')
    
    try {
      await api.deleteLocation(locationId, transferToId)
      setSuccess(`Location "${locationName}" deleted successfully${transferToId ? ' (inventory transferred)' : ''}`)
      setDeletingLocation(null)
      setTransferToLocationId('')
      await loadLocations()
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      const errorData = err.message
      // Check if error contains inventory info
      try {
        const errorResponse = JSON.parse(errorData)
        if (errorResponse.has_inventory) {
          setDeletingLocation({ id: locationId, name: locationName })
          setTransferToLocationId('')
          setError(errorResponse.message || errorResponse.error)
        } else {
          setError(errorData)
        }
      } catch {
        setError(errorData || 'Failed to delete location')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmDeleteWithTransfer = async () => {
    if (!transferToLocationId) {
      setError('Please select a location to transfer inventory to')
      return
    }
    
    if (transferToLocationId === deletingLocation.id.toString()) {
      setError('Cannot transfer inventory to the same location')
      return
    }
    
    await performDeleteLocation(deletingLocation.id, deletingLocation.name, parseInt(transferToLocationId))
  }

  const cancelEdit = () => {
    setEditingLocation(null)
    setEditLocationName('')
    setError('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>MyStock - LEGO Inventory Management</h1>
        <nav className="main-nav">
          <button 
            onClick={() => {
              setStep('itemId')
              handleReset()
            }}
            className={`nav-btn ${step === 'itemId' || step === 'receive' || step === 'ship' || step === 'inventory' ? 'active' : ''}`}
          >
            Item Lookup
          </button>
          <button 
            onClick={() => setStep('fullInventory')}
            className={`nav-btn ${step === 'fullInventory' ? 'active' : ''}`}
          >
            Full Inventory
          </button>
          <button 
            onClick={() => setStep('journal')}
            className={`nav-btn ${step === 'journal' ? 'active' : ''}`}
          >
            Transaction Log
          </button>
          <button 
            onClick={() => setStep('locations')}
            className={`nav-btn ${step === 'locations' ? 'active' : ''}`}
          >
            Locations
          </button>
        </nav>
      </header>

      <main className="app-main">
        {step === 'itemId' && (
          <div className="card">
            <h2>Enter Item ID</h2>
            <form onSubmit={handleItemIdSubmit}>
              <div className="form-group">
                <label htmlFor="itemId">Item ID:</label>
                <input
                  id="itemId"
                  type="text"
                  value={itemId}
                  onChange={(e) => setItemId(e.target.value)}
                  placeholder="Enter LEGO set item ID"
                  required
                  disabled={loading}
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary">
                {loading ? 'Processing...' : 'Continue'}
              </button>
            </form>
          </div>
        )}

        {step === 'receive' && item && (
          <div className="card">
            <h2>Receive Stock - {item.item_id}</h2>
            {item.image_url && (
              <div className="product-image-container">
                <img src={item.image_url} alt={item.name || item.item_id} className="product-image" />
              </div>
            )}
            {item.name && <p className="item-name">{item.name}</p>}
            <form onSubmit={handleTransaction}>
              <div className="form-group">
                <label htmlFor="quantity">Quantity:</label>
                <input
                  id="quantity"
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="Enter quantity"
                  min="1"
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-group">
                <label htmlFor="location">Location:</label>
                <select
                  id="location"
                  value={selectedLocationId}
                  onChange={(e) => {
                    const locId = e.target.value
                    setSelectedLocationId(locId)
                    const loc = locations.find(l => l.id === parseInt(locId))
                    setSelectedLocationName(loc ? loc.name : '')
                  }}
                  required
                  disabled={loading}
                >
                  <option value="">Select a location</option>
                  {locations.map(location => (
                    <option key={location.id} value={location.id}>
                      {location.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-actions">
                <button type="submit" disabled={loading} className="btn-primary">
                  {loading ? 'Processing...' : 'Receive Stock'}
                </button>
                <button 
                  type="button" 
                  onClick={() => {
                    if (inventory.length > 0) {
                      setStep('inventory')
                    } else {
                      handleReset()
                    }
                  }}
                  className="btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 'ship' && item && (
          <div className="card">
            <h2>Ship Stock - {item.item_id}</h2>
            {item.image_url && (
              <div className="product-image-container">
                <img src={item.image_url} alt={item.name || item.item_id} className="product-image" />
              </div>
            )}
            {item.name && <p className="item-name">{item.name}</p>}
            <p className="location-info">Location: <strong>{selectedLocationName}</strong></p>
            <p className="current-stock">Current Stock: <strong>{getLocationQuantity(parseInt(selectedLocationId))}</strong></p>
            <form onSubmit={handleTransaction}>
              <div className="form-group">
                <label htmlFor="quantity">Quantity to Ship:</label>
                <input
                  id="quantity"
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(e.target.value)}
                  placeholder="Enter quantity"
                  min="1"
                  max={getLocationQuantity(parseInt(selectedLocationId))}
                  required
                  disabled={loading}
                />
              </div>
              <div className="form-actions">
                <button type="submit" disabled={loading} className="btn-primary">
                  {loading ? 'Processing...' : 'Ship Stock'}
                </button>
                <button 
                  type="button" 
                  onClick={() => setStep('inventory')}
                  className="btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 'inventory' && item && (
          <div className="card">
            <div className="item-header">
              {item.image_url && (
                <div className="product-image-container">
                  <img src={item.image_url} alt={item.name || item.item_id} className="product-image" />
                </div>
              )}
              <div className="item-header-text">
                <h2>Inventory - {item.item_id}</h2>
                {item.name && <p className="item-name">{item.name}</p>}
              </div>
            </div>
            
            {inventory.length === 0 || !locations.length ? (
              <div className="no-inventory">
                <p>Loading locations...</p>
              </div>
            ) : (
              <div className="inventory-table-container">
                <table className="inventory-table">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Quantity</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inventory.map((inv, index) => (
                      <tr key={inv.id || `location-${inv.location.id}`}>
                        <td>{inv.location.name}</td>
                        <td className={`quantity-cell ${inv.quantity === 0 ? 'zero-quantity' : ''}`}>
                          {inv.quantity}
                        </td>
                        <td className="actions-cell">
                          <button
                            onClick={() => handleReceiveClick(inv.location.id, inv.location.name)}
                            className="btn-link btn-receive"
                          >
                            Receive
                          </button>
                          <span className="separator">|</span>
                          <button
                            onClick={() => handleShipClick(inv.location.id, inv.location.name)}
                            className="btn-link btn-ship"
                            disabled={inv.quantity === 0}
                            title={inv.quantity === 0 ? 'No stock available to ship' : ''}
                          >
                            Ship
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            
            <div className="card-actions">
              <button onClick={handleReset} className="btn-link">
                Enter Different Item ID
              </button>
            </div>
          </div>
        )}

        {step === 'journal' && (
          <div className="card">
            <h2>Transaction Journal</h2>
            
            <div className="journal-filters">
              <div className="filter-group">
                <label>
                  <input
                    type="radio"
                    value="all"
                    checked={journalFilter === 'all'}
                    onChange={(e) => {
                      setJournalFilter(e.target.value)
                      setFilterItemId('')
                      setFilterLocationId('')
                    }}
                  />
                  All Transactions
                </label>
                <label>
                  <input
                    type="radio"
                    value="item"
                    checked={journalFilter === 'item'}
                    onChange={(e) => setJournalFilter(e.target.value)}
                  />
                  Filter by Item
                </label>
                <label>
                  <input
                    type="radio"
                    value="location"
                    checked={journalFilter === 'location'}
                    onChange={(e) => setJournalFilter(e.target.value)}
                  />
                  Filter by Location
                </label>
              </div>
              
              {journalFilter === 'item' && (
                <div className="form-group">
                  <input
                    type="text"
                    placeholder="Enter Item ID"
                    value={filterItemId}
                    onChange={(e) => setFilterItemId(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        loadJournalEntries()
                      }
                    }}
                  />
                  <button onClick={loadJournalEntries} className="btn-primary" style={{ marginLeft: '10px' }}>
                    Filter
                  </button>
                </div>
              )}
              
              {journalFilter === 'location' && (
                <div className="form-group">
                  <select
                    value={filterLocationId}
                    onChange={(e) => setFilterLocationId(e.target.value)}
                  >
                    <option value="">Select Location</option>
                    {locations.map(loc => (
                      <option key={loc.id} value={loc.id}>{loc.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {loading ? (
              <div className="loading">Loading journal entries...</div>
            ) : journalEntries.length === 0 ? (
              <div className="no-inventory">
                <p>No journal entries found.</p>
              </div>
            ) : (
              <div className="journal-table-container">
                <table className="journal-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Item ID</th>
                      <th>Item Name</th>
                      <th>Location</th>
                      <th>Type</th>
                      <th>Quantity</th>
                      <th>Before</th>
                      <th>After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {journalEntries.map(entry => (
                      <tr key={entry.id}>
                        <td className="date-cell">{formatDate(entry.created_at)}</td>
                        <td>{entry.item_id || (entry.item?.item_id) || '-'}</td>
                        <td>{entry.item_name || (entry.item?.name) || '-'}</td>
                        <td>{entry.location_name || (entry.location?.name) || '-'}</td>
                        <td>
                          <span className={`transaction-badge ${entry.transaction_type.toLowerCase()}`}>
                            {entry.transaction_type}
                          </span>
                        </td>
                        <td className={`quantity-cell ${entry.quantity_after < entry.quantity_before ? 'negative-quantity' : ''}`}>
                          {entry.quantity_after < entry.quantity_before ? '-' : ''}{entry.quantity}
                        </td>
                        <td className="quantity-cell">{entry.quantity_before}</td>
                        <td className="quantity-cell">{entry.quantity_after}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {step === 'fullInventory' && (
          <div className="card">
            <h2>Full Inventory</h2>
            <p className="subtitle">Complete inventory of all products across all locations</p>
            
            <div className="inventory-controls">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showOnlyInStock}
                  onChange={(e) => setShowOnlyInStock(e.target.checked)}
                />
                Show only items in stock (quantity &gt; 0)
              </label>
            </div>

            {loading ? (
              <div className="loading">Loading inventory...</div>
            ) : fullInventory.length === 0 ? (
              <div className="no-inventory">
                <p>No inventory found.</p>
              </div>
            ) : (() => {
              // Transform inventory data: group by item_id
              const inventoryByItem = {}
              
              fullInventory.forEach(inv => {
                const itemId = inv.item.item_id
                if (!inventoryByItem[itemId]) {
                  inventoryByItem[itemId] = {
                    item: inv.item,
                    locations: {},
                    totalQuantity: 0,
                    lastUpdated: inv.updated_at
                  }
                }
                inventoryByItem[itemId].locations[inv.location.name] = inv.quantity
                inventoryByItem[itemId].totalQuantity += inv.quantity
                // Keep the most recent updated_at
                if (new Date(inv.updated_at) > new Date(inventoryByItem[itemId].lastUpdated)) {
                  inventoryByItem[itemId].lastUpdated = inv.updated_at
                }
              })
              
              // Convert to array and filter
              let items = Object.values(inventoryByItem)
              
              if (showOnlyInStock) {
                items = items.filter(item => item.totalQuantity > 0)
              }
              
              // Sort by item_id
              items.sort((a, b) => a.item.item_id.localeCompare(b.item.item_id))
              
              // Get all unique locations (sorted)
              const allLocations = [...new Set(locations.map(loc => loc.name))].sort()
              
              return (
                <div className="full-inventory-table-container">
                  <table className="full-inventory-table">
                    <thead>
                      <tr>
                        <th>Item ID</th>
                        <th>Item Name</th>
                        {allLocations.map(locName => (
                          <th key={locName}>{locName}</th>
                        ))}
                        <th>Total</th>
                        <th>Last Updated</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((itemData, idx) => (
                        <tr key={itemData.item.item_id || idx}>
                          <td className="item-id-cell">
                            <button
                              onClick={() => handleItemIdClick(itemData.item.item_id)}
                              className="item-id-link"
                              type="button"
                            >
                              {itemData.item.item_id}
                            </button>
                          </td>
                          <td className="item-name-cell">
                            {itemData.item.image_url && (
                              <img 
                                src={itemData.item.image_url} 
                                alt={itemData.item.name || itemData.item.item_id}
                                className="item-thumbnail"
                              />
                            )}
                            <span>{itemData.item.name || '-'}</span>
                          </td>
                          {allLocations.map(locName => {
                            const qty = itemData.locations[locName] || 0
                            return (
                              <td 
                                key={locName}
                                className={`quantity-cell ${qty === 0 ? 'zero-quantity' : ''}`}
                              >
                                {qty}
                              </td>
                            )
                          })}
                          <td className="quantity-cell total-cell">
                            {itemData.totalQuantity}
                          </td>
                          <td className="date-cell">{formatDate(itemData.lastUpdated)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  {showOnlyInStock && (
                    <div className="inventory-summary">
                      <p>
                        Showing {items.length} of {Object.keys(inventoryByItem).length} items with stock
                      </p>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        )}

        {step === 'locations' && (
          <div className="card">
            <h2>Location Management</h2>
            <p className="subtitle">Manage warehouse locations</p>

            {/* Create Location Form */}
            <div className="location-form-section">
              <h3>Add New Location</h3>
              <form onSubmit={handleCreateLocation}>
                <div className="form-group" style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <label htmlFor="newLocationName">Location Name:</label>
                    <input
                      id="newLocationName"
                      type="text"
                      value={newLocationName}
                      onChange={(e) => setNewLocationName(e.target.value)}
                      placeholder="Enter location name"
                      required
                      disabled={loading}
                      maxLength={100}
                    />
                  </div>
                  <button type="submit" disabled={loading || !newLocationName.trim()} className="btn-primary">
                    {loading ? 'Adding...' : 'Add Location'}
                  </button>
                </div>
              </form>
            </div>

            {/* Locations List */}
            <div className="locations-list-section">
              <h3>Existing Locations</h3>
              {loading && locations.length === 0 ? (
                <div className="loading">Loading locations...</div>
              ) : locations.length === 0 ? (
                <div className="no-inventory">
                  <p>No locations found. Add your first location above.</p>
                </div>
              ) : (
                <div className="locations-table-container">
                  <table className="locations-table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Created</th>
                        <th>Last Updated</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {locations.map(location => (
                        <tr key={location.id}>
                          {editingLocation && editingLocation.id === location.id ? (
                            <>
                              <td colSpan="3">
                                <form onSubmit={handleUpdateLocation} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                  <input
                                    type="text"
                                    value={editLocationName}
                                    onChange={(e) => setEditLocationName(e.target.value)}
                                    required
                                    disabled={loading}
                                    maxLength={100}
                                    style={{ flex: 1 }}
                                  />
                                  <button type="submit" disabled={loading} className="btn-primary" style={{ padding: '6px 12px' }}>
                                    Save
                                  </button>
                                  <button type="button" onClick={cancelEdit} disabled={loading} className="btn-secondary" style={{ padding: '6px 12px' }}>
                                    Cancel
                                  </button>
                                </form>
                              </td>
                              <td></td>
                            </>
                          ) : (
                            <>
                              <td className="location-name-cell">{location.name}</td>
                              <td className="date-cell">{formatDate(location.created_at)}</td>
                              <td className="date-cell">{formatDate(location.updated_at)}</td>
                              <td className="actions-cell">
                                <button
                                  onClick={() => handleEditLocation(location)}
                                  className="btn-link btn-edit"
                                  disabled={loading}
                                >
                                  Edit
                                </button>
                                <span className="separator">|</span>
                                <button
                                  onClick={() => handleDeleteLocation(location.id, location.name)}
                                  className="btn-link btn-delete"
                                  disabled={loading}
                                >
                                  Delete
                                </button>
                              </td>
                            </>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Delete Location with Transfer Dialog */}
            {deletingLocation && (
              <div className="card" style={{ marginTop: '20px', border: '2px solid #667eea', backgroundColor: '#fff9e6' }}>
                <h3>⚠️ Delete Location: {deletingLocation.name}</h3>
                <p style={{ color: '#d9534f', marginBottom: '20px', fontWeight: '600' }}>
                  This location has inventory in stock. You must transfer the inventory to another location before deleting.
                </p>
                
                <div className="form-group">
                  <label htmlFor="transferLocation">Transfer inventory to:</label>
                  <select
                    id="transferLocation"
                    value={transferToLocationId}
                    onChange={(e) => setTransferToLocationId(e.target.value)}
                    required
                    disabled={loading}
                  >
                    <option value="">Select a location</option>
                    {locations
                      .filter(loc => loc.id !== deletingLocation.id)
                      .map(loc => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name}
                        </option>
                      ))}
                  </select>
                </div>
                
                <div className="form-actions">
                  <button
                    onClick={handleConfirmDeleteWithTransfer}
                    disabled={loading || !transferToLocationId}
                    className="btn-primary"
                  >
                    {loading ? 'Deleting...' : 'Delete & Transfer Inventory'}
                  </button>
                  <button
                    onClick={() => {
                      setDeletingLocation(null)
                      setTransferToLocationId('')
                      setError('')
                    }}
                    disabled={loading}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="alert alert-error">
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{error}</pre>
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}
      </main>
    </div>
  )
}

export default App

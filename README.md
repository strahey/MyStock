# MyStock - LEGO Inventory Management System

A full-stack web application for managing LEGO set inventory across multiple warehouse locations.

## Features

- **Item Lookup**: Enter LEGO set item IDs to view and manage inventory
- **Stock Management**: Receive and ship stock across multiple locations
- **Full Inventory View**: See all items with quantities by location
- **Transaction Journal**: Complete audit log of all stock movements
- **Location Management**: Create, edit, and manage warehouse locations
- **Web Scraping**: Automatically fetch product names and images from LEGO websites
- **Denormalized History**: Transaction history preserved even after items/locations are deleted

## Tech Stack

### Backend
- **Django 5.2.8** - Web framework
- **Django REST Framework 3.16.1** - API framework
- **SQLite** - Database
- **Beautiful Soup 4** - Web scraping
- **django-cors-headers** - CORS handling

### Frontend
- **React 19** - UI framework
- **Vite 7** - Build tool and dev server
- **Vanilla CSS** - Styling

## Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **Node.js 20.19+ or 22.12+** (see `frontend/.nvmrc` for exact version)
- **npm** or **yarn**
- **Git** (for cloning the repository)

## Quick Start

If you're setting up for the first time, follow these steps in order:

1. **Clone the repository** and navigate to the project directory
2. **Set up the backend**: Create virtual environment, install dependencies, run migrations
3. **Set up the frontend**: Install Node.js version (if using nvm), install npm dependencies
4. **Start the application**: Use the launch script or start both servers manually

See the detailed setup instructions below.

## Local Development Setup

### 1. Clone the Repository

```bash
# Clone the repository (replace with your actual repository URL)
git clone git@github.com:strahey/MyStock.git
cd mystock
```

If you already have the repository locally, navigate to the project directory:

```bash
cd mystock
```

### 2. Backend Setup

#### Create and Activate Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

#### Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### Run Database Migrations

```bash
python manage.py migrate
```

#### Seed Initial Data (Optional)

```bash
# Add initial locations (Tull and Duck)
python manage.py seed_locations
```

#### Create Superuser (Optional - for Django admin)

```bash
python manage.py createsuperuser
```

### 3. Frontend Setup

#### Install Node.js Version (Recommended)

If you're using `nvm` (Node Version Manager), the project includes a `.nvmrc` file:

```bash
cd frontend
nvm use  # or nvm install if version not installed
cd ..
```

#### Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Verify Setup

Verify that everything is set up correctly:

```bash
# Check Python version
python --version  # Should be 3.8+

# Check Node.js version
node --version  # Should be 18+

# Verify Django is installed
source venv/bin/activate
python -c "import django; print(django.get_version())"  # Should show 5.2.8

# Verify React/Vite is installed
cd frontend
npm list react vite  # Should show installed versions
cd ..
```

## Running the Application

You have two options to start the application:

### Option 1: Manual Start (Two Terminals)

#### Terminal 1 - Start Backend

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start Django development server
python manage.py runserver
```

Backend will be available at: **http://localhost:8000**

#### Terminal 2 - Start Frontend

```bash
cd frontend
npm run dev
```

Frontend will be available at: **http://localhost:5173**

### Option 2: Using Launch Script

```bash
# Make the script executable (first time only)
chmod +x launch.sh

# Run the launch script
./launch.sh
```

The script will start both backend and frontend servers automatically.

## Stopping the Application

### If Using Launch Script

Simply press **Ctrl+C** in the terminal where the launch script is running. The script will automatically stop both the backend and frontend servers gracefully.

### If Running Manually (Two Terminals)

Press **Ctrl+C** in each terminal window:
1. Stop the backend: Press **Ctrl+C** in the terminal running `python manage.py runserver`
2. Stop the frontend: Press **Ctrl+C** in the terminal running `npm run dev`

### Force Stop (If Needed)

If servers don't stop properly, you can force kill them:

```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 5173)
lsof -ti:5173 | xargs kill -9

# Or kill both at once
lsof -ti:8000,5173 | xargs kill -9
```

## Useful Commands

These commands require the virtual environment to be activated:

```bash
source venv/bin/activate
```

### Clear All Data from Database (Start Fresh)

⚠️ **Warning**: This will delete ALL data including items, locations, inventory, and transaction history.

```bash
python manage.py clear_all_data
```

The command will prompt for confirmation. To skip the confirmation prompt:

```bash
python manage.py clear_all_data --confirm
```

### Delete a Specific Item from Database

Delete an item by its `item_id`:

```bash
python manage.py delete_item <ITEM_ID>
```

Example:
```bash
python manage.py delete_item 75192
```

**Note**: Deleting an item will also delete all related inventory records, stock transactions, and journal entries (though journal entries preserve denormalized data).

### Delete All Items with Zero Stock in All Locations

Delete all items that have zero quantity at all locations (or no inventory records at all):

```bash
python manage.py delete_zero_stock_items
```

The command will prompt for confirmation. To skip the confirmation prompt:

```bash
python manage.py delete_zero_stock_items --confirm
```

## Accessing the Application

Once both servers are running:

1. Open your browser and navigate to: **http://localhost:5173**
2. You should see the MyStock application with the main navigation
3. Backend API is available at: **http://localhost:8000/api/**

## API Endpoints

- `GET /api/locations/` - List all locations
- `POST /api/locations/` - Create a new location
- `GET /api/items/by_item_id/<item_id>/` - Get item by ID
- `GET /api/inventory/by_item/<item_id>/` - Get inventory for an item
- `GET /api/inventory/` - Get all inventory
- `POST /api/transactions/` - Create a transaction (receive or ship stock)
- `GET /api/journal/` - Get all transaction journal entries
- `GET /api/journal/by_item/<item_id>/` - Get journal entries for an item
- `GET /api/journal/by_location/<location_id>/` - Get journal entries for a location

## Project Structure

```
mystock/
├── backend/                 # Django project settings
│   ├── settings.py         # Main settings
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI configuration
├── inventory/              # Main Django app
│   ├── models.py           # Database models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views
│   ├── urls.py             # App URL configuration
│   ├── admin.py            # Django admin configuration
│   ├── scraper.py          # Web scraping logic
│   └── management/         # Management commands
│       └── commands/
│           └── seed_locations.py
├── frontend/               # React application
│   ├── src/
│   │   ├── App.jsx         # Main React component
│   │   ├── App.css         # Application styles
│   │   ├── api.js          # API client
│   │   ├── main.jsx        # React entry point
│   │   └── index.css       # Base styles
│   ├── package.json        # Node dependencies
│   └── vite.config.js      # Vite configuration
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── launch.sh               # Launch script
└── README.md               # This file
```

## Database Schema

### Models

- **Location**: Warehouse locations (name, timestamps)
- **Item**: LEGO set items (item_id, name, description, image_url)
- **StockTransaction**: Individual transactions (item, location, type, quantity)
- **Inventory**: Current inventory levels (item, location, quantity)
- **TransactionJournal**: Denormalized audit log of all transactions

## Features Overview

### Item Lookup
- Enter any LEGO set item ID
- Automatically scrapes product name and image from Brickset.com or LEGO.com
- Shows current inventory across all locations

### Receive Stock
- Add stock to any location
- Automatically updates inventory
- Records transaction in journal

### Ship Stock
- Remove stock from locations
- Validates sufficient quantity available
- Automatically updates inventory

### Full Inventory
- View all items and quantities across all locations
- Pivot table format: one row per item, one column per location
- Filter to show only items in stock
- Clickable item IDs to navigate to item details

### Transaction Journal
- Complete audit log of all stock movements
- Filter by item ID or location
- Shows before/after quantities
- Preserves historical data even after items/locations deleted

### Location Management
- Create new warehouse locations
- Edit location names
- Delete locations with inventory transfer
- Prevents data loss during deletion

## Development Notes

### CORS Configuration
The backend is configured to allow requests from:
- http://localhost:5173 (Vite default)
- http://localhost:3000 (Alternative React port)
- http://127.0.0.1:5173
- http://127.0.0.1:3000

### Web Scraping
The application attempts to scrape product information from:
1. Brickset.com (primary)
2. LEGO.com (fallback)

Note: Web scraping may fail if these sites change their HTML structure.

### Database
SQLite is used for simplicity. For production, consider PostgreSQL or MySQL.

## Troubleshooting

### Backend won't start
- Make sure virtual environment is activated: `source venv/bin/activate`
- Check if port 8000 is already in use: `lsof -ti:8000`
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Frontend won't start
- Check if port 5173 is already in use: `lsof -ti:5173`
- Verify Node.js version: `node --version` (should be 18+)
  - If using `nvm`, run `cd frontend && nvm use` to use the version specified in `.nvmrc`
- Reinstall dependencies: `cd frontend && rm -rf node_modules && npm install`
- Check for JSX syntax errors in the browser console or terminal output

### CORS errors
- Make sure backend is running on port 8000
- Check `backend/settings.py` CORS configuration
- Try restarting the Django server after changing CORS settings

### White screen or styling issues
- Clear browser cache
- Check browser console for errors
- Verify `frontend/src/index.css` doesn't have conflicting styles

## Future Enhancements

- User authentication and authorization
- Barcode scanning support
- Export inventory to CSV/Excel
- Email notifications for low stock
- Multi-warehouse support with inter-warehouse transfers
- Mobile responsive improvements
- Real-time updates with WebSockets
- Advanced search and filtering
- Bulk import/export
- Reports and analytics

## License

This project is for internal use.

## Contributing

For questions or issues, please contact the development team.


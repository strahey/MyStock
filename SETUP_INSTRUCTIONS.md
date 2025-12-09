# Google Login Integration - Setup Instructions

## Prerequisites

1. Python 3.8+ with virtual environment activated
2. Node.js 20.19+ or 22.12+
3. Google Cloud Console account

## Step 1: Install Backend Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install new packages
pip install -r requirements.txt
```

## Step 2: Set Up Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API (or Google Identity API)
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure the OAuth consent screen:
   - User type: External
   - App name: MyStock
   - Authorized domains: your domain (or localhost for development)
   - Scopes: email, profile
6. Create OAuth client:
   - Application type: Web application
   - Authorized JavaScript origins: 
     - `http://localhost:5173` (for development)
     - Your production domain (for production)
   - Authorized redirect URIs:
     - `http://localhost:8000/api/auth/google/callback/` (for development)
     - Your production callback URL (for production)
7. Copy the Client ID and Client Secret

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Django Secret Key (generate a new one for production)
DJANGO_SECRET_KEY=o-&7jy*szuwvxk*8-k2oxfz2mcgnxiufp&8k-j^1p#vs6snxi6

# Google OAuth 2.0 Credentials
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

**Important**: The `.env` file is already in `.gitignore` - do not commit it!

## Step 4: Configure Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```bash
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

Or set it when running:
```bash
VITE_GOOGLE_CLIENT_ID=your-client-id npm run dev
```

## Step 5: Run Database Migrations

**⚠️ WARNING**: This will modify your database schema. If you have existing data, you may need to migrate it or start fresh.

```bash
# Create migrations
python manage.py makemigrations inventory

# Apply migrations
python manage.py migrate

# Create a superuser (optional, for Django admin)
python manage.py createsuperuser
```

### Handling Existing Data

If you have existing data, you have two options:

**Option A: Start Fresh (Recommended for development)**
```bash
# Backup existing database
cp db.sqlite3 db.sqlite3.backup

# Clear all data
python manage.py clear_all_data --confirm

# Run migrations
python manage.py migrate
```

**Option B: Migrate Existing Data**
- Create a data migration script to assign existing data to a default user
- This is more complex and may require custom migration code

## Step 6: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Step 7: Start the Application

### Terminal 1 - Backend
```bash
source venv/bin/activate
python manage.py runserver
```

### Terminal 2 - Frontend
```bash
cd frontend
npm run dev
```

Or use the launch script:
```bash
./launch.sh
```

## Step 8: Test Authentication

1. Open http://localhost:5173 in your browser
2. You should see the login screen
3. Click "Sign in with Google"
4. Select your Google account
5. You should be redirected back and logged in
6. Your user email should appear in the header

## Troubleshooting

### "Google OAuth not configured" error
- Check that `GOOGLE_OAUTH2_CLIENT_ID` and `GOOGLE_OAUTH2_CLIENT_SECRET` are set in `.env`
- Restart the Django server after adding environment variables

### "VITE_GOOGLE_CLIENT_ID not set" error
- Set the environment variable in `frontend/.env` or when running `npm run dev`
- Restart the frontend dev server

### "Unauthorized" errors on API calls
- Make sure you're logged in
- Check that the JWT token is being sent in the Authorization header
- Try logging out and logging back in

### Migration errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check that you're using the correct Python version
- Try running `python manage.py migrate --run-syncdb` if needed

### CORS errors
- Make sure the frontend URL is in `CORS_ALLOWED_ORIGINS` in `backend/settings.py`
- Check that both servers are running

## Next Steps

- All locations, inventory, and transactions are now user-specific
- Each user will have their own isolated data
- Items (LEGO sets) are shared across users (same item_id = same product)

## Production Deployment

Before deploying to production:

1. Generate a new `SECRET_KEY` for Django
2. Set `DEBUG = False` in `settings.py`
3. Update `ALLOWED_HOSTS` with your domain
4. Update Google OAuth redirect URIs for production
5. Use environment variables for all secrets
6. Use HTTPS (required for OAuth)
7. Consider using PostgreSQL instead of SQLite for production


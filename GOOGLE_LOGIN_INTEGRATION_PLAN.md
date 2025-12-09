# Google Login Integration Plan

## Overview

This plan outlines the integration of Google OAuth authentication into the MyStock application, ensuring that locations, stock inventory, and transactions are unique for each individual user.

## Current State

- **No user authentication**: All data is currently shared globally
- **Open API endpoints**: All endpoints use `AllowAny` permissions
- **Models**: Location, Item, StockTransaction, Inventory, TransactionJournal
- **No user association**: None of the models currently have user foreign keys

## Goals

1. Integrate Google OAuth 2.0 authentication
2. Associate all user data (locations, inventory, transactions) with individual users
3. Implement user isolation at the API level
4. Update frontend to handle authentication state
5. Maintain backward compatibility during migration

---

## Phase 1: Backend Setup

### 1.1 Install Required Packages

Add to `requirements.txt`:
```
django-allauth==0.57.0
djangorestframework-simplejwt==5.3.1
```

### 1.2 Update Django Settings

**File**: `backend/settings.py`

**Changes needed**:
1. Add `allauth` and `allauth.account` to `INSTALLED_APPS`
2. Add authentication backends
3. Configure Google OAuth credentials
4. Update REST Framework authentication classes
5. Add JWT token authentication

**Key settings to add**:
```python
INSTALLED_APPS = [
    # ... existing apps ...
    'rest_framework',
    'rest_framework_simplejwt',
    'django.contrib.sites',  # Required for allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# Google OAuth Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
    }
}

# REST Framework JWT Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Allow unauthenticated access to auth endpoints
REST_FRAMEWORK_AUTH_EXCEPTIONS = [
    '/api/auth/google/',
    '/api/auth/login/',
    '/api/auth/refresh/',
]

# JWT Settings
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

### 1.3 Environment Variables

Create `.env` file (add to `.gitignore`):
```
GOOGLE_OAUTH2_CLIENT_ID=your_client_id_here
GOOGLE_OAUTH2_CLIENT_SECRET=your_client_secret_here
DJANGO_SECRET_KEY=your_secret_key_here
```

Update `settings.py` to load from `.env`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_OAUTH2_CLIENT_ID = os.getenv('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH2_CLIENT_SECRET')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', SECRET_KEY)
```

---

## Phase 2: Database Schema Changes

### 2.1 Update Models

**File**: `inventory/models.py`

**Changes needed**:
1. Add `user` ForeignKey to Location model
2. Add `user` ForeignKey to Item model (optional - items can be shared but inventory is user-specific)
3. Add `user` ForeignKey to StockTransaction model
4. Add `user` ForeignKey to Inventory model
5. Add `user` ForeignKey to TransactionJournal model
6. Update unique constraints to include user

**Model Updates**:

```python
from django.contrib.auth.models import User

class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['user', 'name']  # Location names unique per user

class Item(models.Model):
    # Items can be shared across users (same LEGO set), but inventory is user-specific
    item_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image_url = models.URLField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # No user field - items are shared

class StockTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='transactions')
    # ... rest of fields

class Inventory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='inventory')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='inventory')
    quantity = models.IntegerField(default=0)
    # ... rest of fields

    class Meta:
        unique_together = ['user', 'item', 'location']  # Unique per user

class TransactionJournal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    # ... rest of fields
```

### 2.2 Create Migration

```bash
python manage.py makemigrations inventory
python manage.py migrate
```

### 2.3 Data Migration Strategy

**Option A: Assign existing data to a default user**
- Create a migration that assigns all existing data to a default "system" user
- Users can then migrate their data manually

**Option B: Clean slate**
- Clear all existing data before deploying
- Users start fresh with their own accounts

**Recommended**: Option B (clean slate) for simplicity, with a backup script for existing data.

---

## Phase 3: Authentication API Endpoints

### 3.1 Create Authentication Views

**File**: `inventory/views.py` (or create `inventory/auth_views.py`)

**Endpoints needed**:
1. `POST /api/auth/google/` - Initiate Google OAuth flow
2. `POST /api/auth/google/callback/` - Handle Google OAuth callback
3. `POST /api/auth/login/` - Exchange Google token for JWT
4. `POST /api/auth/refresh/` - Refresh JWT token
5. `GET /api/auth/me/` - Get current user info
6. `POST /api/auth/logout/` - Logout (optional, client-side token removal)

**Implementation approach**:
- Use `django-allauth` for Google OAuth flow
- Use `djangorestframework-simplejwt` for JWT token generation
- Create custom views to bridge OAuth and JWT

### 3.2 URL Configuration

**File**: `inventory/urls.py`

Add authentication routes:
```python
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from . import auth_views

urlpatterns = [
    # ... existing patterns ...
    path('auth/google/', auth_views.GoogleLoginView.as_view(), name='google_login'),
    path('auth/google/callback/', auth_views.GoogleCallbackView.as_view(), name='google_callback'),
    path('auth/login/', auth_views.GoogleTokenLoginView.as_view(), name='token_login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', auth_views.UserProfileView.as_view(), name='user_profile'),
]
```

---

## Phase 4: Update API Views for User Isolation

### 4.1 Filter Querysets by User

**File**: `inventory/views.py`

**Changes needed**:
- Override `get_queryset()` in all ViewSets to filter by `request.user`
- Ensure `create()` methods associate new objects with `request.user`
- Update `destroy()` methods to verify user ownership

**Example for LocationViewSet**:
```python
class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    
    def get_queryset(self):
        return Location.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

**Apply similar changes to**:
- `ItemViewSet` - Filter transactions/inventory by user, but items remain shared
- `StockTransactionViewSet` - Filter by user
- `InventoryViewSet` - Filter by user
- `TransactionJournalViewSet` - Filter by user

### 4.2 Update Serializers

**File**: `inventory/serializers.py`

- Remove `user` field from serializers (set automatically)
- Ensure serializers don't expose user information unnecessarily

---

## Phase 5: Frontend Authentication

### 5.1 Install Dependencies

**File**: `frontend/package.json`

Add:
```json
{
  "dependencies": {
    "@react-oauth/google": "^0.12.1",
    "axios": "^1.6.0"
  }
}
```

### 5.2 Create Authentication Context

**File**: `frontend/src/AuthContext.jsx`

Create React context for:
- User state
- Login/logout functions
- Token management
- API request interceptors

### 5.3 Update API Client

**File**: `frontend/src/api.js`

**Changes needed**:
1. Add token to all requests
2. Handle 401 errors (redirect to login)
3. Add token refresh logic
4. Create auth-specific API functions

**Example**:
```javascript
let authToken = null;

export const setAuthToken = (token) => {
  authToken = token;
  localStorage.setItem('authToken', token);
};

export const getAuthToken = () => {
  if (!authToken) {
    authToken = localStorage.getItem('authToken');
  }
  return authToken;
};

const apiRequest = async (url, options = {}) => {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });
  
  if (response.status === 401) {
    // Handle unauthorized - redirect to login
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  
  return response;
};
```

### 5.4 Create Login Component

**File**: `frontend/src/Login.jsx`

- Google Sign-In button using `@react-oauth/google`
- Handle OAuth callback
- Store JWT token
- Redirect to main app

### 5.5 Update App Component

**File**: `frontend/src/App.jsx`

**Changes needed**:
1. Wrap app with `AuthProvider`
2. Add route protection
3. Show login screen if not authenticated
4. Display user info in header

---

## Phase 6: Google Cloud Console Setup

### 6.1 Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure consent screen:
   - User type: External
   - App name: MyStock
   - Authorized domains: your domain
   - Scopes: email, profile
6. Create OAuth client:
   - Application type: Web application
   - Authorized JavaScript origins: `http://localhost:5173` (dev), your production domain
   - Authorized redirect URIs: `http://localhost:8000/api/auth/google/callback/` (dev), production callback URL
7. Copy Client ID and Client Secret to `.env` file

---

## Phase 7: Testing Strategy

### 7.1 Backend Tests

- Test authentication endpoints
- Test user isolation (user A can't see user B's data)
- Test JWT token generation and validation
- Test permission checks

### 7.2 Frontend Tests

- Test login flow
- Test token storage and retrieval
- Test API calls with authentication
- Test logout functionality

### 7.3 Integration Tests

- Test full OAuth flow
- Test data isolation between users
- Test concurrent user access

---

## Phase 8: Migration Checklist

### Pre-Deployment
- [ ] Set up Google Cloud Console project
- [ ] Add OAuth credentials to `.env`
- [ ] Install new dependencies (`pip install`, `npm install`)
- [ ] Run database migrations
- [ ] Backup existing database (if keeping data)
- [ ] Test OAuth flow locally

### Deployment Steps
1. Update `requirements.txt` and `package.json`
2. Run migrations: `python manage.py migrate`
3. Update environment variables on server
4. Update CORS settings for production domain
5. Update Google OAuth redirect URIs for production
6. Deploy backend
7. Deploy frontend
8. Test authentication flow

### Post-Deployment
- [ ] Verify users can log in
- [ ] Verify data isolation works
- [ ] Monitor error logs
- [ ] Test token refresh functionality

---

## Phase 9: Security Considerations

### 9.1 Backend Security
- Use HTTPS in production
- Validate JWT tokens on every request
- Implement rate limiting on auth endpoints
- Use secure cookie settings for sessions (if using)
- Validate OAuth state parameter to prevent CSRF

### 9.2 Frontend Security
- Store tokens in localStorage (consider httpOnly cookies for production)
- Implement token refresh before expiration
- Clear tokens on logout
- Validate token expiration client-side

### 9.3 Data Security
- Ensure all queries filter by user
- Add database-level constraints where possible
- Audit logs for user actions
- Regular security updates

---

## Phase 10: Rollback Plan

If issues arise:
1. Revert database migrations (if possible)
2. Revert code changes
3. Restore previous database backup
4. Update environment variables to previous state

---

## Implementation Order

1. **Phase 1**: Backend setup (packages, settings)
2. **Phase 2**: Database schema changes (models, migrations)
3. **Phase 3**: Authentication API endpoints
4. **Phase 4**: Update API views for user isolation
5. **Phase 6**: Google Cloud Console setup (can be done in parallel)
6. **Phase 5**: Frontend authentication
7. **Phase 7**: Testing
8. **Phase 8**: Deployment

---

## Estimated Timeline

- **Backend setup**: 2-3 hours
- **Database changes**: 1-2 hours
- **Auth endpoints**: 3-4 hours
- **API view updates**: 2-3 hours
- **Frontend auth**: 4-5 hours
- **Google Console setup**: 30 minutes
- **Testing**: 2-3 hours
- **Total**: ~15-20 hours

---

## Notes

- Items (LEGO sets) remain shared across users (same item_id = same LEGO set)
- Inventory, locations, and transactions are user-specific
- Consider adding user profile management later
- Consider adding user-to-user sharing features in future
- Consider adding admin user role for system management

---

## Questions to Consider

1. Should items be user-specific or shared? (Plan assumes shared)
2. Should there be a way to transfer data between users?
3. Should there be admin users who can see all data?
4. How to handle existing data? (Clean slate vs. migration)
5. Should there be a way to export/import user data?

---

## Next Steps

1. Review and approve this plan
2. Set up Google Cloud Console project
3. Begin Phase 1 implementation
4. Test incrementally after each phase
5. Deploy to staging environment first
6. Deploy to production after thorough testing


# MyStock Free Hosting Plan - Render + Netlify + Supabase + Cloudflare

## 🎯 Overview

**Complete deployment guide** for MyStock using **Render (backend) + Netlify (frontend) + Supabase (database) + Cloudflare (DNS/CDN)** with **automatic GitHub deployments**.

## 🏗️ Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Netlify    │─────▶│   Render     │─────▶│   Supabase   │
│  (Frontend)  │      │  (Django)    │      │ (PostgreSQL) │
│  React/Vite  │      │   Gunicorn   │      │   Database   │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                      │                      │
┌──────▼───────┐      ┌──────▼───────┐      ┌──────▼───────┐
│  Cloudflare  │      │  Cloudflare  │      │  Cloudflare  │
│     CDN      │      │   Firewall   │      │   DNS        │
│   Caching    │      │   Security   │      │  SSL/TLS     │
└──────────────┘      └──────────────┘      └──────────────┘
```

## 🌐 Cloudflare Setup

### DNS Records for mystock.trahey.net
```bash
# In Cloudflare DNS dashboard:
# Type: CNAME, Name: mystock, Content: your-app.netlify.app, Proxy: ON
# Type: CNAME, Name: api.mystock, Content: your-app.onrender.com, Proxy: ON
```

### SSL/TLS Configuration
- **Mode**: Full (Strict)
- **Always Use HTTPS**: Enabled
- **Automatic HTTPS Rewrites**: Enabled

### Performance Optimization
- **Auto Minify**: JavaScript, CSS, HTML
- **Brotli Compression**: Enabled
- **Browser Cache TTL**: 1 year for static assets

## 🚀 Step-by-Step Deployment

### 1. Backend (Render.com)

#### Create Render Account & Project
1. Sign up at [https://render.com](https://render.com)
2. Click "New" → "Web Service"
3. Connect GitHub repository

#### Environment Variables
```
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@db.host:5432/postgres
ALLOWED_HOSTS=mystock.trahey.net,api.mystock.trahey.net
DJANGO_SETTINGS_MODULE=backend.settings_production
FRONTEND_URL=https://mystock.trahey.net
GOOGLE_OAUTH2_CLIENT_ID=your-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
```

#### Build & Start Commands
```bash
# Build Command:
pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput

# Start Command:
gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

### 2. Frontend (Netlify)

#### Create Netlify Account & Project
1. Sign up at [https://netlify.com](https://netlify.com)
2. Click "Add new site" → "Import from Git"
3. Select GitHub repository
4. Set base directory: `frontend`

#### Build Settings
```bash
# Build command:
npm install && npm run build

# Publish directory:
dist
```

#### Environment Variables
```
VITE_API_URL=https://api.mystock.trahey.net
```

### 3. Database (Supabase)

#### Create Supabase Project
1. Sign up at [https://supabase.com](https://supabase.com)
2. Create new project
3. Go to Project Settings → Database
4. Copy connection string

#### Database Configuration
```python
# backend/settings_production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'your-password',
        'HOST': 'db.your-project.supabase.co',
        'PORT': '5432',
    }
}
```

### 4. GitHub Actions (Automatic Deployment)

#### Create Workflow File
```yaml
# .github/workflows/deploy.yml
name: Deploy MyStock

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Deploy backend to Render
      - name: Deploy backend
        uses: renderinc/action-deploy@v1
        with:
          service-id: ${{ secrets.RENDER_SERVICE_ID }}
          api-key: ${{ secrets.RENDER_API_KEY }}

      # Deploy frontend to Netlify
      - name: Deploy frontend
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: './frontend/dist'
          production-branch: main
          github-token: ${{ secrets.GITHUB_TOKEN }}
          deploy-message: "Deploy from GitHub Actions"
          enable-pull-request-comment: false
          enable-commit-comment: true
          overwrites-pull-request-comment: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
        timeout-minutes: 1
```

### 5. Production Django Settings

```python
# backend/settings_production.py
from .settings import *
import os

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# CORS
CORS_ALLOWED_ORIGINS = [
    "https://mystock.trahey.net",
    "https://api.mystock.trahey.net",
]

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

### 6. Frontend API Configuration

```javascript
// frontend/src/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_BASE_URL,
  // ... existing API methods
};
```

## 📋 Deployment Checklist

- [ ] Set up Cloudflare DNS records for mystock.trahey.net
- [ ] Create Render.com account and project
- [ ] Create Netlify account and project
- [ ] Create Supabase database
- [ ] Configure environment variables in all services
- [ ] Set up GitHub Actions workflow
- [ ] Test Google OAuth with new domain
- [ ] Verify user isolation works
- [ ] Test all API endpoints
- [ ] Monitor free tier usage

## 🔧 Troubleshooting

### Cloudflare Issues
- **DNS not resolving**: Check proxy status (should be orange)
- **SSL errors**: Verify Full (Strict) mode and valid certificates
- **Cache issues**: Purge cache in Cloudflare dashboard

### Render Issues
- **Build failures**: Check build logs in Render dashboard
- **Database connection**: Verify environment variables
- **Timeouts**: Check service logs

### Netlify Issues
- **Build errors**: Check npm dependencies
- **Deployment failures**: Verify build settings
- **API connection**: Check CORS and environment variables

### Authentication Issues
- **Google OAuth**: Ensure domain is in authorized domains
- **CORS**: Verify CORS_ALLOWED_ORIGINS includes frontend domain
- **JWT**: Check token expiration and refresh

## 💰 Cost Analysis

**All services are 100% free** within these limits:

- **Cloudflare**: Free for all features
- **Render**: 750 hours/month (enough for 24/7)
- **Netlify**: 100GB bandwidth, 300 build minutes
- **Supabase**: 500MB database, 2GB bandwidth
- **Domain**: trahey.net already owned

## 🚀 Next Steps

1. **Set up Cloudflare DNS** for mystock.trahey.net
2. **Create accounts** on Render, Netlify, Supabase
3. **Configure environment variables**
4. **Set up GitHub Actions** for automatic deployment
5. **Deploy and test** thoroughly
6. **Monitor usage** to stay within free tiers

## 📚 Resources

- [Render Documentation](https://render.com/docs)
- [Netlify Documentation](https://docs.netlify.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Cloudflare Documentation](https://developers.cloudflare.com/)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.2/howto/deployment/)

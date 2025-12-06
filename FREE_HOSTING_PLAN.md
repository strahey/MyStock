# MyStock Free Hosting Plan - Internet Deployment

## Overview

This document outlines multiple strategies for hosting the MyStock application on the internet using free services. Each approach has different trade-offs in terms of ease of setup, performance, and limitations.

## Architecture Options

### Option 1: Railway (Backend) + Vercel (Frontend) + Supabase (Database)
**Best for**: Modern, easy deployment with good performance

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Vercel     │─────▶│   Railway    │─────▶│   Supabase   │
│  (Frontend)  │      │  (Django)    │      │ (PostgreSQL) │
│  React/Vite  │      │   Gunicorn   │      │   Database   │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Option 2: Render (Backend) + Netlify (Frontend) + Render PostgreSQL
**Best for**: All-in-one platform familiarity

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Netlify    │─────▶│   Render     │─────▶│   Render     │
│  (Frontend)  │      │  (Django)     │      │ (PostgreSQL) │
│  React/Vite  │      │   Gunicorn   │      │   Database   │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Option 3: PythonAnywhere (Backend) + GitHub Pages (Frontend) + SQLite
**Best for**: Simplest setup, minimal configuration

```
┌──────────────┐      ┌──────────────┐
│ GitHub Pages │─────▶│PythonAnywhere│
│  (Frontend)  │      │  (Django)    │
│  React/Vite  │      │   SQLite    │
└──────────────┘      └──────────────┘
```

### Option 4: Fly.io (All-in-One)
**Best for**: Single platform, container-based deployment

```
┌──────────────┐
│   Fly.io     │
│  (Django +   │
│   Frontend)  │
│   SQLite/    │
│  PostgreSQL  │
└──────────────┘
```

---

## Option 1: Railway + Vercel + Supabase (Recommended)

### Why This Combination?
- **Railway**: Easy Django deployment, automatic HTTPS, Git integration
- **Vercel**: Excellent React/Vite support, global CDN, instant deployments
- **Supabase**: Free PostgreSQL with generous limits, easy setup

### Free Tier Limits

**Railway**:
- $5 free credit monthly (usually enough for small apps)
- Automatic HTTPS
- Custom domains
- Git-based deployments

**Vercel**:
- Unlimited deployments
- 100GB bandwidth/month
- Automatic SSL
- Global CDN

**Supabase**:
- 500MB database
- 2GB bandwidth
- Unlimited API requests

### Step-by-Step Setup

#### 1. Prepare Repository

Ensure your repository is on GitHub:

```bash
git remote add origin git@github.com:strahey/MyStock.git
git push -u origin main
```

#### 2. Set Up Supabase Database

1. **Create Supabase Account**
   - Go to https://supabase.com
   - Sign up with GitHub
   - Create a new project

2. **Get Database Connection String**
   - Go to Project Settings → Database
   - Copy the connection string (URI format)
   - Example: `postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres`

3. **Update Django Settings**

Create `backend/settings_production.py`:

```python
from .settings import *
import os
from urllib.parse import urlparse

# Security
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database - Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    db_config = dj_database_url.parse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_config['NAME'],
            'USER': db_config['USER'],
            'PASSWORD': db_config['PASSWORD'],
            'HOST': db_config['HOST'],
            'PORT': db_config['PORT'],
        }
    }

# Static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# CORS - Allow Vercel domain
CORS_ALLOWED_ORIGINS = [
    os.environ.get('FRONTEND_URL', 'https://your-app.vercel.app'),
]

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Update `requirements.txt`:

```txt
Django==5.2.8
djangorestframework==3.16.1
django-cors-headers==4.9.0
requests==2.32.5
beautifulsoup4==4.14.2
lxml==6.0.2
gunicorn==21.2.0
psycopg2-binary==2.9.9
dj-database-url==2.1.0
whitenoise==6.6.0
```

#### 3. Deploy Backend to Railway

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your MyStock repository

3. **Configure Service**
   - Railway will auto-detect Django
   - Add environment variables:
     ```
     SECRET_KEY=your-secret-key-here
     DATABASE_URL=postgresql://postgres:password@host:5432/dbname
     ALLOWED_HOSTS=your-app.railway.app,yourdomain.com
     DJANGO_SETTINGS_MODULE=backend.settings_production
     FRONTEND_URL=https://your-app.vercel.app
     ```

4. **Add PostgreSQL Service (Optional)**
   - Or use Supabase connection string in DATABASE_URL
   - Railway can provision PostgreSQL if preferred

5. **Configure Build Settings**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT`

6. **Run Migrations**
   - Add a one-time command: `python manage.py migrate`
   - Or use Railway's CLI: `railway run python manage.py migrate`

7. **Get Backend URL**
   - Railway provides: `https://your-app.railway.app`
   - Note this URL for frontend configuration

#### 4. Deploy Frontend to Vercel

1. **Create Vercel Account**
   - Go to https://vercel.com
   - Sign up with GitHub

2. **Import Project**
   - Click "Add New Project"
   - Import your GitHub repository
   - Select the `frontend` folder as root directory

3. **Configure Build Settings**
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

4. **Add Environment Variables**
   ```
   VITE_API_URL=https://your-app.railway.app
   ```

5. **Update Frontend API Configuration**

Update `frontend/src/api.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_BASE_URL,
  // ... rest of your API code
};
```

6. **Deploy**
   - Vercel will automatically deploy on every push to main branch
   - Get your frontend URL: `https://your-app.vercel.app`

#### 5. Update CORS Settings

Update Railway environment variable:
```
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
```

#### 6. Custom Domain (Optional)

**Railway**:
- Go to project settings
- Add custom domain
- Update DNS records

**Vercel**:
- Go to project settings → Domains
- Add custom domain
- Update DNS records

---

## Option 2: Render + Netlify + Render PostgreSQL

### Why This Combination?
- **Render**: Reliable free tier, easy Django deployment
- **Netlify**: Great for static sites, excellent CDN
- **Render PostgreSQL**: Integrated database service

### Free Tier Limits

**Render**:
- 750 hours/month (enough for 24/7)
- 512MB RAM
- Automatic SSL
- Sleeps after 15 minutes of inactivity (free tier)

**Netlify**:
- 100GB bandwidth/month
- 300 build minutes/month
- Automatic SSL

### Step-by-Step Setup

#### 1. Deploy Backend to Render

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create Web Service**
   - New → Web Service
   - Connect GitHub repository
   - Settings:
     - Name: `mystock-backend`
     - Environment: Python 3
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT`

3. **Create PostgreSQL Database**
   - New → PostgreSQL
   - Name: `mystock-db`
   - Copy the Internal Database URL

4. **Add Environment Variables**
   ```
   SECRET_KEY=your-secret-key
   DATABASE_URL=<from PostgreSQL service>
   ALLOWED_HOSTS=your-app.onrender.com
   DJANGO_SETTINGS_MODULE=backend.settings_production
   FRONTEND_URL=https://your-app.netlify.app
   ```

5. **Run Migrations**
   - Use Render Shell: `python manage.py migrate`
   - Or add to build command: `pip install -r requirements.txt && python manage.py migrate`

#### 2. Deploy Frontend to Netlify

1. **Create Netlify Account**
   - Go to https://netlify.com
   - Sign up with GitHub

2. **Add New Site**
   - Import from Git
   - Select repository
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `dist`

3. **Add Environment Variables**
   ```
   VITE_API_URL=https://your-app.onrender.com
   ```

4. **Deploy**
   - Netlify auto-deploys on git push

---

## Option 3: PythonAnywhere + GitHub Pages

### Why This Combination?
- **PythonAnywhere**: Simplest Django hosting, no configuration needed
- **GitHub Pages**: Free static hosting, perfect for React builds
- **SQLite**: No database setup needed

### Free Tier Limits

**PythonAnywhere**:
- 1 web app
- 512MB disk space
- Limited CPU time
- Custom domain support

**GitHub Pages**:
- Unlimited bandwidth
- 1GB storage
- Free SSL

### Step-by-Step Setup

#### 1. Deploy Backend to PythonAnywhere

1. **Create Account**
   - Go to https://www.pythonanywhere.com
   - Sign up (free account)

2. **Upload Code**
   - Go to Files tab
   - Upload your project or clone from GitHub:
     ```bash
     git clone https://github.com/strahey/MyStock.git
     ```

3. **Create Virtual Environment**
   ```bash
   cd MyStock
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Go to Web tab
   - Click "Add a new web app"
   - Select "Manual configuration"
   - Python version: 3.10
   - Click Next

5. **Configure WSGI File**
   - Edit `/var/www/yourusername_pythonanywhere_com_wsgi.py`:
     ```python
     import os
     import sys

     path = '/home/yourusername/MyStock'
     if path not in sys.path:
         sys.path.insert(0, path)

     os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'

     from django.core.wsgi import get_wsgi_application
     application = get_wsgi_application()
     ```

6. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

7. **Reload Web App**
   - Click "Reload" button in Web tab

#### 2. Deploy Frontend to GitHub Pages

1. **Build Frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Configure Vite for GitHub Pages**

Update `vite.config.js`:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/MyStock/', // Your repository name
})
```

3. **Deploy Script**

Create `deploy.sh`:

```bash
#!/bin/bash
npm run build
cd dist
git init
git add -A
git commit -m 'deploy'
git push -f git@github.com:strahey/MyStock.git main:gh-pages
cd ..
```

4. **Enable GitHub Pages**
   - Go to repository Settings → Pages
   - Source: Deploy from branch
   - Branch: `gh-pages` / `root`

---

## Option 4: Fly.io (All-in-One)

### Why This Option?
- Single platform for everything
- Container-based (Docker)
- Good free tier
- Global edge deployment

### Free Tier Limits

**Fly.io**:
- 3 shared-cpu VMs
- 3GB persistent volume storage
- 160GB outbound data transfer

### Step-by-Step Setup

#### 1. Install Fly CLI

```bash
curl -L https://fly.io/install.sh | sh
```

#### 2. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run migrations and start server
CMD python manage.py migrate && gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

#### 3. Create fly.toml

```toml
app = "mystock-app"
primary_region = "iad"

[build]

[env]
  PORT = "8000"
  DJANGO_SETTINGS_MODULE = "backend.settings_production"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

#### 4. Deploy

```bash
fly auth login
fly launch
fly deploy
```

---

## Configuration Changes Needed

### 1. Update Django Settings for Production

Create `backend/settings_production.py` (see Option 1 for full example):

Key changes:
- `DEBUG = False`
- Set `SECRET_KEY` from environment
- Configure `ALLOWED_HOSTS`
- Update database configuration
- Configure CORS for frontend domain
- Set up static files serving

### 2. Update Frontend API Configuration

Update `frontend/src/api.js`:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  baseURL: API_BASE_URL,
  // ... existing code
};
```

### 3. Add Environment Variables

Each platform needs:
- `SECRET_KEY`: Django secret key
- `DATABASE_URL`: Database connection (if using PostgreSQL)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `FRONTEND_URL`: Frontend domain for CORS
- `VITE_API_URL`: Backend API URL (frontend)

### 4. Update requirements.txt

Add production dependencies:

```txt
gunicorn==21.2.0
psycopg2-binary==2.9.9  # For PostgreSQL
dj-database-url==2.1.0  # For DATABASE_URL parsing
whitenoise==6.6.0       # For static files (if not using CDN)
```

---

## Comparison Table

| Feature | Railway+Vercel | Render+Netlify | PythonAnywhere+GitHub | Fly.io |
|---------|---------------|----------------|----------------------|--------|
| **Ease of Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Free Tier Limits** | Generous | Moderate | Limited | Good |
| **Custom Domain** | ✅ | ✅ | ✅ | ✅ |
| **Auto Deploy** | ✅ | ✅ | Manual | ✅ |
| **Database Options** | PostgreSQL | PostgreSQL | SQLite | SQLite/PostgreSQL |
| **Best For** | Modern apps | Balanced | Simple apps | Container apps |

---

## Recommended Approach

**For Most Users**: **Option 1 (Railway + Vercel + Supabase)**
- Easiest setup
- Best performance
- Most reliable free tiers
- Excellent documentation

**For Simplicity**: **Option 3 (PythonAnywhere + GitHub Pages)**
- Minimal configuration
- No database setup
- Good for learning

**For Control**: **Option 4 (Fly.io)**
- Full container control
- Single platform
- More technical setup

---

## Post-Deployment Checklist

- [ ] Update `ALLOWED_HOSTS` with production domain
- [ ] Set strong `SECRET_KEY`
- [ ] Configure CORS for frontend domain
- [ ] Run database migrations
- [ ] Set up custom domain (optional)
- [ ] Configure SSL/HTTPS (usually automatic)
- [ ] Test all API endpoints
- [ ] Test frontend-backend communication
- [ ] Set up monitoring/alerts (optional)
- [ ] Document deployment process

---

## Troubleshooting

### Backend Issues

**Database Connection Errors**:
- Verify `DATABASE_URL` is correct
- Check database is accessible from hosting platform
- Ensure migrations have run

**Static Files Not Loading**:
- Run `python manage.py collectstatic`
- Configure `STATIC_ROOT` and `STATIC_URL`
- Use WhiteNoise or CDN for serving

**CORS Errors**:
- Verify `CORS_ALLOWED_ORIGINS` includes frontend URL
- Check `ALLOWED_HOSTS` includes backend domain

### Frontend Issues

**API Connection Errors**:
- Verify `VITE_API_URL` environment variable
- Check backend is accessible
- Verify CORS configuration

**Build Errors**:
- Check Node.js version matches `.nvmrc`
- Verify all dependencies installed
- Check build logs for specific errors

---

## Cost Considerations

All options listed are **free** but have limitations:

1. **Free tiers may sleep** (Render free tier sleeps after inactivity)
2. **Resource limits** (CPU, RAM, bandwidth)
3. **Build time limits** (Netlify: 300 min/month)
4. **Database size limits** (Supabase: 500MB)

**When to Upgrade**:
- High traffic
- Need 24/7 uptime (no sleeping)
- Need more resources
- Need support

---

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [Vercel Documentation](https://vercel.com/docs)
- [Render Documentation](https://render.com/docs)
- [Netlify Documentation](https://docs.netlify.com/)
- [PythonAnywhere Help](https://help.pythonanywhere.com/)
- [Fly.io Documentation](https://fly.io/docs/)
- [Supabase Documentation](https://supabase.com/docs)

---

## Next Steps

1. **Choose an option** based on your needs
2. **Prepare your code** (update settings, add production configs)
3. **Set up accounts** on chosen platforms
4. **Deploy backend** first
5. **Deploy frontend** and configure API URL
6. **Test thoroughly**
7. **Set up custom domain** (optional)
8. **Monitor usage** to stay within free tier limits



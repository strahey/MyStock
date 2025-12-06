# MyStock Deployment Plan - Proxmox LXC Containers

## Overview

This document outlines a comprehensive plan for deploying the MyStock application on a local Proxmox server using LXC containers. The architecture uses separate containers for each service component, providing isolation, scalability, and easier maintenance.

## Architecture

### Container Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Proxmox Host                          │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Nginx      │  │   Django     │  │   React      │ │
│  │   Reverse    │  │   Backend    │  │   Frontend   │ │
│  │   Proxy      │  │   (Gunicorn) │  │   (Static)   │ │
│  │              │  │              │  │              │ │
│  │  Port: 80    │  │  Port: 8000  │  │  Port: N/A   │ │
│  │  Port: 443   │  │  (internal)  │  │  (static)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┴──────────────────┘         │
│                          │                               │
│                  ┌───────▼────────┐                      │
│                  │   SQLite DB    │                      │
│                  │  (in backend)  │                      │
│                  └────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### Alternative: Separate Database Container (Optional)

For better scalability, consider a PostgreSQL container:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Nginx      │  │   Django     │  │   React      │  │  PostgreSQL  │
│   Reverse    │  │   Backend    │  │   Frontend   │  │   Database   │
│   Proxy      │  │   (Gunicorn) │  │   (Static)   │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                  │                  │                │
       └──────────────────┴──────────────────┴──────────────┘
```

## Container Specifications

### 1. Nginx Reverse Proxy Container
- **Template**: `ubuntu-22.04-standard` or `debian-12-standard`
- **Resources**:
  - CPU: 1 core
  - RAM: 512MB
  - Disk: 2GB
  - Network: Bridge (vmbr0) with static IP
- **Purpose**: 
  - SSL/TLS termination
  - Reverse proxy for backend API
  - Serve static frontend files
  - Load balancing (if multiple backend instances)

### 2. Django Backend Container
- **Template**: `ubuntu-22.04-standard` or `debian-12-standard`
- **Resources**:
  - CPU: 2 cores
  - RAM: 1GB (adjust based on usage)
  - Disk: 10GB (for database and application files)
  - Network: Bridge (vmbr0) with static IP
- **Purpose**:
  - Run Django application with Gunicorn
  - Host SQLite database (or connect to PostgreSQL)
  - Serve API endpoints

### 3. React Frontend Container (Optional - Static Files)
- **Template**: `ubuntu-22.04-standard` or `debian-12-standard`
- **Resources**:
  - CPU: 1 core
  - RAM: 512MB
  - Disk: 2GB
  - Network: Bridge (vmbr0) with static IP
- **Purpose**:
  - Build React application
  - Serve static files (can be served by Nginx instead)
- **Note**: Frontend can be built and served directly by Nginx, making this container optional

### 4. PostgreSQL Container (Optional - Recommended for Production)
- **Template**: `ubuntu-22.04-standard` or `debian-12-standard`
- **Resources**:
  - CPU: 1 core
  - RAM: 512MB
  - Disk: 10GB (for database files)
  - Network: Bridge (vmbr0) with static IP
- **Purpose**:
  - Replace SQLite for better performance and scalability
  - Database backups

## Network Configuration

### IP Address Scheme (Example)

```
Nginx Container:     192.168.1.100
Django Container:    192.168.1.101
Frontend Container:  192.168.1.102 (optional)
PostgreSQL:         192.168.1.103 (optional)
```

### Firewall Rules

- **Nginx**: Allow ports 80 (HTTP) and 443 (HTTPS) from LAN
- **Django**: Allow port 8000 only from Nginx container (internal)
- **Frontend**: No external access needed (served by Nginx)
- **PostgreSQL**: Allow port 5432 only from Django container (internal)

## Step-by-Step Deployment

### Phase 1: Container Creation

#### 1.1 Create Nginx Container

```bash
# Via Proxmox Web UI or CLI
pct create 100 \
  local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname nginx-mystock \
  --memory 512 \
  --cores 1 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1 \
  --rootfs local-lvm:2 \
  --storage local-lvm \
  --unprivileged 1 \
  --start
```

#### 1.2 Create Django Backend Container

```bash
pct create 101 \
  local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname django-mystock \
  --memory 1024 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.101/24,gw=192.168.1.1 \
  --rootfs local-lvm:10 \
  --storage local-lvm \
  --unprivileged 1 \
  --start
```

#### 1.3 Create Frontend Container (Optional)

```bash
pct create 102 \
  local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname frontend-mystock \
  --memory 512 \
  --cores 1 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.102/24,gw=192.168.1.1 \
  --rootfs local-lvm:2 \
  --storage local-lvm \
  --unprivileged 1 \
  --start
```

### Phase 2: Container Setup

#### 2.1 Nginx Container Setup

```bash
# Enter container
pct enter 100

# Update system
apt update && apt upgrade -y

# Install Nginx
apt install -y nginx

# Create directories
mkdir -p /var/www/mystock
mkdir -p /etc/nginx/ssl

# Exit container
exit
```

#### 2.2 Django Backend Container Setup

```bash
# Enter container
pct enter 101

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git sqlite3

# Create application user
useradd -m -s /bin/bash mystock
su - mystock

# Create application directory
mkdir -p /home/mystock/app
cd /home/mystock/app

# Clone repository (or copy files)
git clone git@github.com:strahey/MyStock.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Install Gunicorn for production
pip install gunicorn

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Seed initial data (optional)
python manage.py seed_locations

# Exit
exit
exit
```

#### 2.3 Frontend Container Setup (If Using Separate Container)

```bash
# Enter container
pct enter 102

# Update system
apt update && apt upgrade -y

# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Create application user
useradd -m -s /bin/bash mystock
su - mystock

# Create application directory
mkdir -p /home/mystock/app
cd /home/mystock/app

# Clone repository
git clone git@github.com:strahey/MyStock.git .

# Install dependencies
cd frontend
npm install

# Build production version
npm run build

# Exit
exit
exit
```

### Phase 3: Application Configuration

#### 3.1 Django Production Settings

Create `backend/settings_production.py`:

```python
from .settings import *
import os

# Security settings
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
ALLOWED_HOSTS = ['192.168.1.101', 'mystock.local', 'your-domain.com']

# Database (keep SQLite or switch to PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    "https://mystock.local",
    "https://your-domain.com",
]

# Security headers
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

#### 3.2 Gunicorn Configuration

Create `/home/mystock/app/gunicorn_config.py`:

```python
bind = "0.0.0.0:8000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
```

#### 3.3 Systemd Service for Django

Create `/etc/systemd/system/mystock.service`:

```ini
[Unit]
Description=MyStock Django Application
After=network.target

[Service]
User=mystock
Group=mystock
WorkingDirectory=/home/mystock/app
Environment="PATH=/home/mystock/app/venv/bin"
ExecStart=/home/mystock/app/venv/bin/gunicorn \
    --config /home/mystock/app/gunicorn_config.py \
    backend.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
systemctl daemon-reload
systemctl enable mystock
systemctl start mystock
```

#### 3.4 Nginx Configuration

Create `/etc/nginx/sites-available/mystock`:

```nginx
# Upstream backend
upstream django_backend {
    server 192.168.1.101:8000;
}

# HTTP server (redirect to HTTPS)
server {
    listen 80;
    server_name mystock.local your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name mystock.local your-domain.com;

    # SSL certificates (use Let's Encrypt or self-signed)
    ssl_certificate /etc/nginx/ssl/mystock.crt;
    ssl_certificate_key /etc/nginx/ssl/mystock.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Logging
    access_log /var/log/nginx/mystock_access.log;
    error_log /var/log/nginx/mystock_error.log;

    # Frontend static files
    location / {
        root /var/www/mystock;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "public, max-age=3600";
    }

    # Backend API
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Django admin
    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files (Django)
    location /static/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
    }

    # Media files (if any)
    location /media/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
    }
}
```

Enable site:

```bash
ln -s /etc/nginx/sites-available/mystock /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

#### 3.5 Copy Frontend Build to Nginx

If using separate frontend container:

```bash
# From frontend container, copy build files
pct enter 102
tar czf /tmp/frontend-build.tar.gz -C /home/mystock/app/frontend/dist .
exit

# Copy to Nginx container
pct push 100 /tmp/frontend-build.tar.gz /tmp/
pct enter 100
tar xzf /tmp/frontend-build.tar.gz -C /var/www/mystock
chown -R www-data:www-data /var/www/mystock
exit
```

Or build directly on Nginx container:

```bash
pct enter 100
apt install -y nodejs npm
# ... build process ...
```

### Phase 4: SSL/TLS Setup

#### Option 1: Self-Signed Certificate (Development)

```bash
pct enter 100
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/mystock.key \
  -out /etc/nginx/ssl/mystock.crt \
  -subj "/CN=mystock.local"
exit
```

#### Option 2: Let's Encrypt (Production)

```bash
pct enter 100
apt install -y certbot python3-certbot-nginx
certbot --nginx -d mystock.local -d your-domain.com
# Follow prompts
exit
```

### Phase 5: Firewall Configuration

On Proxmox host or router:

```bash
# Allow HTTP and HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Block direct access to Django (only allow from Nginx)
iptables -A INPUT -s 192.168.1.100 -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

## Production Checklist

### Security

- [ ] Change Django `SECRET_KEY` to a secure random value
- [ ] Set `DEBUG = False` in production settings
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable SSL/TLS with valid certificates
- [ ] Set up firewall rules
- [ ] Disable root login on containers
- [ ] Use strong passwords for database and admin
- [ ] Enable fail2ban for SSH protection
- [ ] Regular security updates: `apt update && apt upgrade`

### Performance

- [ ] Configure Gunicorn workers based on CPU cores
- [ ] Enable Nginx caching for static files
- [ ] Set up database connection pooling (if using PostgreSQL)
- [ ] Monitor resource usage
- [ ] Configure log rotation

### Backup

- [ ] Set up automated database backups
- [ ] Backup application files
- [ ] Test restore procedures
- [ ] Store backups off-container

### Monitoring

- [ ] Set up log aggregation
- [ ] Monitor container resource usage
- [ ] Set up alerts for service failures
- [ ] Monitor disk space

## Backup Strategy

### Database Backup Script

Create `/home/mystock/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/mystock/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp /home/mystock/app/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sqlite3" -mtime +30 -delete

# Optional: Copy to external location
# scp $BACKUP_DIR/db_$DATE.sqlite3 user@backup-server:/backups/
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /home/mystock/backup.sh
```

### Container Backup

Use Proxmox backup:

```bash
# Backup container
vzdump 101 --storage local --compress gzip

# Restore container
vzdump --restore 101 /path/to/backup.tar.gz
```

## Maintenance Procedures

### Updating the Application

```bash
# Enter Django container
pct enter 101
su - mystock
cd /home/mystock/app

# Pull latest changes
git pull

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart service
exit
systemctl restart mystock
```

### Updating Frontend

```bash
# If using separate container
pct enter 102
su - mystock
cd /home/mystock/app/frontend
git pull
npm install
npm run build

# Copy to Nginx
# ... (copy process)
```

### Log Monitoring

```bash
# Django logs
journalctl -u mystock -f

# Nginx logs
tail -f /var/log/nginx/mystock_access.log
tail -f /var/log/nginx/mystock_error.log
```

## Troubleshooting

### Container Won't Start
- Check container status: `pct status 101`
- Check logs: `pct enter 101` then `journalctl -xe`
- Verify network configuration

### Application Not Accessible
- Check Nginx status: `systemctl status nginx`
- Check Django service: `systemctl status mystock`
- Verify firewall rules
- Check Nginx error logs

### Database Issues
- Check file permissions on SQLite database
- Verify disk space: `df -h`
- Check database integrity: `sqlite3 db.sqlite3 "PRAGMA integrity_check;"`

## Alternative: Simplified Single Container

For smaller deployments, you can run everything in one container:

```bash
# Single container with all services
pct create 100 \
  local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname mystock \
  --memory 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.100/24,gw=192.168.1.1 \
  --rootfs local-lvm:20 \
  --storage local-lvm \
  --unprivileged 1 \
  --start
```

Install all services in one container and configure Nginx to serve everything locally.

## Next Steps

1. **Review and customize** IP addresses and domain names
2. **Set up DNS** or use `/etc/hosts` for local domain resolution
3. **Create containers** following Phase 1
4. **Configure services** following Phases 2-4
5. **Test deployment** thoroughly
6. **Set up backups** and monitoring
7. **Document** any custom configurations

## Additional Resources

- [Proxmox LXC Documentation](https://pve.proxmox.com/pve-docs/chapter-pct.html)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Documentation](https://nginx.org/en/docs/)



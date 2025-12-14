# Dockerfile for Django Backend (Development)
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy only the essential files (rest comes from bind mount in dev)
COPY backend /app/backend
COPY manage.py /app/

# Expose the port
EXPOSE 8000

# Set environment variables for development
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=backend.settings

# Entrypoint (override in docker-compose for hot reload)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

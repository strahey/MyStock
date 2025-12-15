# Use official slim Python image
FROM python:3.14-slim

# Set working directory
WORKDIR /app

# Install required system dependencies for psycopg/PostgreSQL and general builds
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy dependencies file
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy rest of the backend code
COPY backend /app/backend
COPY manage.py /app/
# (add any other files needed by your backend here, such as settings, wsgi, etc.)

# Set environment variables for production
ENV PYTHONUNBUFFERED=1

# Expose the backend port
EXPOSE 8000

# Default command for production (can be overridden in compose for dev)
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]

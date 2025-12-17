FROM python:3.11-slim

WORKDIR /app

# System dependencies for psycopg (PostgreSQL)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the ENTIRE project root into container's /app (which will bring in backend/, inventory/, manage.py, etc.)
COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
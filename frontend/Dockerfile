# Dockerfile for React Frontend (Development)
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

# Copy the rest of the frontend source
COPY frontend ./frontend

# Expose Vite's dev port (5173)
EXPOSE 5173

# Start the dev server
CMD ["npm", "run", "dev", "--", "--host"]

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    NODE_ENV=production

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install uvicorn gunicorn

# Copy frontend files first to optimize build caching
COPY frontend/package*.json frontend/

# Install frontend dependencies
WORKDIR /app/frontend
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build the frontend
RUN npm run build

# Return to app directory
WORKDIR /app

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/app/static /app/app/database

# Ensure excel_db.py is in the correct locations
COPY excel_db.py /app/
COPY excel_db.py /app/app/database/

# If Database.xlsx exists, copy it to the database directory
COPY Database.xlsx /app/app/database/ || echo "Database.xlsx not found (will be mounted at runtime)"

# Copy the built frontend files to the static directory
RUN cp -R /app/frontend/dist/* /app/app/static/ || echo "No frontend build files found"

# Make port 8080 available to the world outside this container
# This matches the port specified in your Digital Ocean app spec
EXPOSE 8080

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Starting OnTrack application..."\n\
echo "Environment: $NODE_ENV"\n\
echo "Port: $PORT"\n\
python main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run the application with the correct port
CMD ["sh", "-c", "python main.py"]

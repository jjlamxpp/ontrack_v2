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

# Copy the entire project
COPY . .

# List files to debug
RUN ls -la && ls -la app && ls -la app/database || echo "Database directory not found"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install frontend dependencies and build
WORKDIR /app/frontend
RUN npm install && npm run build

# Return to app directory
WORKDIR /app

# Create necessary directories if they don't exist
RUN mkdir -p app/static app/database

# Copy the excel_db.py file to the database directory if it's not already there
RUN if [ -f "excel_db.py" ] && [ ! -f "app/database/excel_db.py" ]; then \
        cp excel_db.py app/database/; \
        echo "Copied excel_db.py to app/database/"; \
    elif [ -f "app/database/excel_db.py" ]; then \
        echo "excel_db.py already in app/database/"; \
    else \
        echo "Warning: excel_db.py not found"; \
        find . -name "excel_db.py"; \
    fi

# Copy the frontend build to the static directory
RUN if [ -d "frontend/dist" ]; then \
        cp -R frontend/dist/* app/static/ || echo "No files to copy from frontend/dist"; \
        echo "Copied frontend build to app/static/"; \
    else \
        echo "Warning: frontend/dist directory not found"; \
        ls -la frontend; \
    fi

# Make port 8080 available
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]

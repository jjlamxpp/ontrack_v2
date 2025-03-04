# Use a slim Python base image
FROM python:3.9-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y curl gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory for the application
WORKDIR /app

# Copy Python dependency file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application (backend and frontend code)
COPY . .

# Build the frontend assets
WORKDIR /app/frontend
RUN npm install && npm run build

# Copy the built frontend files (assumed to be in the "dist" folder) to the backend's static directory.
# Adjust the destination directory to where your backend serves static files.
RUN mkdir -p /app/app/static && cp -R dist/* /app/app/static/

# Return to the app root directory
WORKDIR /app

# Expose the port your backend listens on (should match your DigitalOcean app spec's http_port)
EXPOSE 8080

# Start the Python application
CMD ["python", "main.py"]

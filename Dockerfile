# Use a base image that supports Python; we'll add Node.js manually
FROM python:3.9-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Set the working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire repository
COPY . .

# Build the frontend assets
WORKDIR /app/frontend
RUN npm install && npm run build

# Return to the app root (assuming your backend expects built assets in a known location)
WORKDIR /app

# Expose the port (should match http_port: 8080 in your spec)
EXPOSE 8080

# Start your Python application
CMD ["python", "main.py"]

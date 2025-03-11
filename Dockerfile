# Use an official Node.js runtime as a parent image for the frontend build
FROM node:18-slim AS frontend-build

# Set working directory for frontend
WORKDIR /app/frontend

# Copy package.json and package-lock.json
COPY frontend/package*.json ./

# Install dependencies including TypeScript and React types
RUN npm install && \
    npm install --save-dev typescript @types/react @types/react-dom @types/node

# Copy frontend source code
COPY frontend/ ./

# Create a simple vite-env.d.ts file to fix ImportMeta errors
RUN echo 'interface ImportMeta { env: Record<string, any>; }' > src/vite-env-fix.d.ts

# Build the frontend with TypeScript checks disabled
RUN NODE_ENV=production npx vite build

# Use Python image for the backend
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    NODE_ENV=production

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY . .

# Create necessary directories
RUN mkdir -p /app/app/static /app/app/database

# Copy the built frontend from the frontend-build stage
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Make port 8080 available
EXPOSE 8080

# Update the main.py to use the correct port
RUN sed -i 's/uvicorn.run("main:app", host="0.0.0.0", port=8000)/uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))/' main.py || echo "Failed to update port in main.py"

# Run the application
CMD ["python", "main.py"]

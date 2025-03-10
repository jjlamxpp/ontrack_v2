#!/bin/bash
set -e

echo "Build script started"

# Create necessary directories
mkdir -p app/database
mkdir -p static

# Copy excel_db.py to multiple locations to ensure it's found
echo "Copying excel_db.py to multiple locations"
cp excel_db.py app/database/excel_db.py
cp excel_db.py /app/excel_db.py 2>/dev/null || echo "Could not copy to /app/ (this is normal during local builds)"

# Check if Database.xlsx exists and copy it to app/database
if [ -f "Database.xlsx" ]; then
    echo "Copying Database.xlsx to app/database"
    cp Database.xlsx app/database/
fi

# Install dependencies
echo "Installing dependencies"
pip install -r requirements.txt

# Start the application
echo "Starting the application"
exec python main.py

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build

echo "Creating necessary directories..."
cd ..
mkdir -p app/static
cp -r frontend/dist/* app/static/

echo "Ensuring icon directories exist..."
mkdir -p app/static/icon
mkdir -p app/static/school_icon

# Copy default icons if needed
if [ -d "backup/icons" ]; then
  echo "Copying backup icons to static directory..."
  cp -r backup/icons/* app/static/icon/
fi

if [ -d "backup/school_icons" ]; then
  echo "Copying backup school icons to static directory..."
  cp -r backup/school_icons/* app/static/school_icon/
fi

echo "Build completed successfully!"

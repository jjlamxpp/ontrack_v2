#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build

echo "Creating necessary directories..."
cd ..
mkdir -p app/static
cp -r frontend/dist/* app/static/

echo "Ensuring database directory exists..."
mkdir -p app/database
if [ -f "Database.xlsx" ]; then
    cp Database.xlsx app/database/
fi

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

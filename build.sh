#!/bin/bash
set -e

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Installing frontend dependencies..."
cd frontend
npm install

echo "Building frontend..."
npm run build

echo "Creating frontend directory at project root..."
cd ..
mkdir -p frontend
echo "Copying frontend build to frontend directory..."
cp -r frontend/dist/* frontend/

echo "Build completed successfully!"

#!/bin/bash
echo "Starting build process..."

# Create static directories if they don't exist
mkdir -p app/static/icon
mkdir -p app/static/school_icon

# Copy default images if they exist in source
if [ -f "app/static/source/default.png" ]; then
    cp app/static/source/default.png app/static/icon/
    cp app/static/source/default.png app/static/school_icon/
fi

echo "Static directories created"
echo "Build completed successfully"

#!/bin/bash
set -e

# Print Python version and location to verify environment
which python3
python3 --version

# Ensure dependencies are installed
echo "Installing dependencies..."
pip install -r requirements.txt

# Start the application
echo "Starting application..."
python3 standalone.py

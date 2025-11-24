#!/bin/bash

# Run Python backend in development mode (without rebuilding binary)

echo "🚀 Starting Pointer backend in DEV mode..."

# Activate virtual environment
source src-python/.venv/bin/activate

# Run the backend directly with Python
cd src-python
python main.py

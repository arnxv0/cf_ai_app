#!/bin/bash

# Quick start script for Pointer with Arrow backend

echo "🚀 Pointer + Arrow Backend Setup"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the pointer project root"
    exit 1
fi

# Step 1: Check for .env file
echo "📝 Step 1: Checking environment configuration..."
if [ ! -f "src-python/.env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp src-python/.env.example src-python/.env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit src-python/.env and add your GOOGLE_API_KEY"
    echo "   Get your key from: https://aistudio.google.com/apikey"
    echo ""
    read -p "Press Enter after you've added your API key to continue..."
else
    echo "✅ .env file exists"
fi

# Step 2: Install Python dependencies
echo ""
echo "📦 Step 2: Installing Python dependencies..."
cd src-python

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt

cd ..

echo "✅ Python dependencies installed"

# Step 3: Install Node dependencies
echo ""
echo "📦 Step 3: Installing Node dependencies..."
npm install

echo "✅ Node dependencies installed"

# Step 4: Ready to run
echo ""
echo "✅ Setup complete!"
echo ""
echo "To start Pointer with Arrow backend:"
echo "  npm run tauri:dev"
echo ""
echo "The app will:"
echo "  1. Start the Vite dev server (frontend)"
echo "  2. Build and run the Tauri app (Rust)"
echo "  3. Auto-start the Python backend with Arrow agent"
echo ""
echo "Press your hotkey (Option+Space) to trigger the overlay!"
echo ""

#!/bin/bash

echo "🔨 Building Pointer Backend..."
echo "================================"

# Navigate to Python source directory
cd src-python

# Detect platform
PLATFORM=$(uname -m)
if [ "$PLATFORM" = "arm64" ]; then
    ARCH="aarch64-apple-darwin"
elif [ "$PLATFORM" = "x86_64" ]; then
    ARCH="x86_64-apple-darwin"
else
    echo "❌ Unsupported architecture: $PLATFORM"
    exit 1
fi

echo "📍 Platform: $ARCH"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "🐍 Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate Python virtual environment
echo "🐍 Activating Python virtual environment..."
source .venv/bin/activate

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt -q
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install requirements"
        exit 1
    fi
    echo "✅ Dependencies installed"
else
    echo "⚠️  No requirements.txt found"
fi

# Verify PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller -q
fi

# Build with PyInstaller
echo "🔧 Running PyInstaller..."
pyinstaller pointer-backend.spec --clean --noconfirm

# Check if build was successful
if [ ! -f "dist/pointer-backend" ]; then
    echo "❌ Build failed: dist/pointer-backend not found"
    exit 1
fi

# Create binaries directory if it doesn't exist
cd ..
mkdir -p src-tauri/binaries

# Copy the binary with architecture suffix
BINARY_NAME="pointer-backend-${ARCH}"
echo "📋 Copying binary to src-tauri/binaries/${BINARY_NAME}..."
cp src-python/dist/pointer-backend "src-tauri/binaries/${BINARY_NAME}"

# Make it executable
chmod +x "src-tauri/binaries/${BINARY_NAME}"

echo ""
echo "✅ Backend build complete!"
echo "📦 Binary: src-tauri/binaries/${BINARY_NAME}"
echo "================================"

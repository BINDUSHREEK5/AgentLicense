#!/bin/bash

set -e

echo "============================================"
echo "  AgentLicense Setup for Mac/Linux"
echo "============================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3.9+ is required but not found."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

echo "[✓] Python found: $(python3 --version)"
echo

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js 16+ is required but not found."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

echo "[✓] Node.js found: $(node --version)"
echo

# Create virtual environment
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[✓] Virtual environment created"
else
    echo "[✓] Virtual environment already exists"
fi
echo

# Activate virtual environment
source venv/bin/activate
echo "[✓] Virtual environment activated"
echo

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -q -r requirements.txt
echo "[✓] Backend dependencies installed"
cd ..
echo

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install --silent
echo "[✓] Frontend dependencies installed"
cd ..
echo

echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo
echo "Next steps:"
echo
echo "  TERMINAL 1 - Start Backend:"
echo "  ============================================"
echo "  source venv/bin/activate"
echo "  cd backend"
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo
echo "  TERMINAL 2 - Start Frontend:"
echo "  ============================================"
echo "  cd frontend"
echo "  npm run dev"
echo
echo "  Then open your browser to:"
echo "  http://localhost:3000"
echo
echo "============================================"
echo
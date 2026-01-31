#!/bin/bash
# Startup script for CamareraI POC

echo "=========================================="
echo "CamareraI - Voice Agent POC"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q dashscope flask python-dotenv requests pydub

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env with: DASHSCOPE_API_KEY=your-key-here"
    exit 1
fi

# Run quick test
echo ""
echo "Running DashScope connection test..."
python3 quick_test.py

# Check if test passed
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "Starting Flask application..."
    echo "=========================================="
    echo ""
    echo "Open your browser to: http://localhost:5000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    python3 poc_voice_agent.py
else
    echo ""
    echo "❌ Tests failed. Please fix the issues above before starting the application."
    exit 1
fi

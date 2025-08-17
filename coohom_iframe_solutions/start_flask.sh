#!/bin/bash

echo "🚀 Starting Coohom Iframe Integration Flask App..."
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if requirements are installed
if ! python3 -c "import flask" &> /dev/null; then
    echo "📦 Installing requirements..."
    pip3 install -r requirements.txt
fi

# Check if credential.txt exists
if [ ! -f "../credential.txt" ]; then
    echo "❌ credential.txt not found in parent directory"
    echo "Please ensure your Coohom API credentials are in ../credential.txt"
    exit 1
fi

echo "✅ All requirements met"
echo "🌐 Starting Flask server..."
echo "📱 Open your browser and go to: http://localhost:5000"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start Flask app
python3 flask_app.py

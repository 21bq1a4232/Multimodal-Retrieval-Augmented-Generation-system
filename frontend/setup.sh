#!/bin/bash

# Multimodal RAG System Frontend Setup Script

echo "🚀 Setting up Multimodal RAG System Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ npm version: $(npm -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
REACT_APP_API_URL=http://localhost:8000
EOF
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo "✅ Backend is running and accessible"
else
    echo "⚠️  Backend is not running or not accessible at http://localhost:8000"
    echo "   Please start the backend first, or update REACT_APP_API_URL in .env"
fi

echo ""
echo "🎉 Frontend setup completed!"
echo ""
echo "To start the development server:"
echo "  npm start"
echo ""
echo "The application will be available at:"
echo "  http://localhost:3000"
echo ""
echo "Make sure your backend API is running at:"
echo "  http://localhost:8000"
echo "" 
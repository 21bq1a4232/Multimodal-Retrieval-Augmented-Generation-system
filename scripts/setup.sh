#!/bin/bash

# Multimodal RAG System Setup Script
# This script helps set up the complete system

set -e

echo "🚀 Multimodal RAG System Setup"
echo "==============================="

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "✅ Running on macOS"
else
    echo "⚠️  This script is optimized for macOS. Please adapt for your system."
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
echo "🔍 Checking system requirements..."

# Check Docker
if command_exists docker; then
    echo "✅ Docker is installed"
    docker --version
else
    echo "❌ Docker not found. Please install Docker Desktop"
    exit 1
fi

# Check Docker Compose
if command_exists docker-compose; then
    echo "✅ Docker Compose is installed"
    docker-compose --version
else
    echo "❌ Docker Compose not found. Please install Docker Compose"
    exit 1
fi

# Check Ollama
if command_exists ollama; then
    echo "✅ Ollama is installed"
    ollama --version
else
    echo "📦 Installing Ollama..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            brew install ollama
        else
            echo "❌ Homebrew not found. Please install Ollama manually from https://ollama.ai"
            exit 1
        fi
    else
        echo "❌ Please install Ollama manually from https://ollama.ai"
        exit 1
    fi
fi

# Check Python (for development)
if command_exists python3; then
    echo "✅ Python 3 is installed"
    python3 --version
else
    echo "⚠️  Python 3 not found. Install for development purposes."
fi

# Check Node.js (for frontend development)
if command_exists node; then
    echo "✅ Node.js is installed"
    node --version
else
    echo "⚠️  Node.js not found. Install for frontend development."
fi

echo ""
echo "🛠️  Setting up environment..."

# Create environment file
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Multimodal RAG System Environment Configuration

# Application Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/multimodal_rag

# Vector Database Configuration
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_TYPE=chromadb
EMBEDDING_DIM=384

# Embedding Model Configuration
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120

# File Upload Configuration
MAX_FILE_SIZE=52428800
ALLOWED_EXTENSIONS=.pdf
UPLOAD_DIRECTORY=./data/uploads

# Processing Configuration
CHUNK_SIZE=512
CHUNK_OVERLAP=50
MAX_CHUNKS_PER_QUERY=5

# Retrieval Configuration
RETRIEVAL_K=10
RERANK_K=5
SIMILARITY_THRESHOLD=0.7

# Scoring Weights
SEMANTIC_WEIGHT=0.6
LEXICAL_WEIGHT=0.3
TABLE_BOOST=1.2

# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Logging Configuration
LOG_LEVEL=INFO

# Evaluation Configuration
EVALUATION_DATASET_PATH=./data/evaluation/test_queries.json
TARGET_ACCURACY=0.98
EOL
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/uploads
mkdir -p data/vector_db
mkdir -p data/evaluation
mkdir -p logs

echo "✅ Data directories created"

# Start Ollama service
echo "🦙 Starting Ollama service..."
if pgrep -f "ollama serve" > /dev/null; then
    echo "✅ Ollama service is already running"
else
    echo "🚀 Starting Ollama service in background..."
    ollama serve &
    sleep 3
fi

# Download recommended models
echo "📥 Downloading recommended models..."
echo "This may take a while depending on your internet connection..."

# Download LLM model
if ollama list | grep -q "llama2"; then
    echo "✅ llama2 model already downloaded"
else
    echo "📥 Downloading llama2 model..."
    ollama pull llama2
fi

# Optional: Download a smaller model for testing
if ollama list | grep -q "phi"; then
    echo "✅ phi model already downloaded"
else
    echo "📥 Downloading phi model (smaller, for testing)..."
    ollama pull phi
fi

echo ""
echo "🐳 Setting up Docker containers..."

# Build and start containers
echo "🔨 Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo "✅ Backend service is healthy"
        break
    else
        echo "⏳ Waiting for backend service... (attempt $i/30)"
        sleep 2
    fi
done

# Test basic functionality
echo "🧪 Testing basic functionality..."
if curl -s -X POST "http://localhost:8000/api/query" \
   -H "Content-Type: application/json" \
   -H "Authorization: Bearer demo-token" \
   -d '{"query": "test"}' > /dev/null; then
    echo "✅ API is responding"
else
    echo "⚠️  API test failed - check logs with: docker-compose logs backend"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "🌐 Access Points:"
echo "  • Frontend:     http://localhost:3000"
echo "  • API Docs:     http://localhost:8000/api/docs"
echo "  • Monitoring:   http://localhost:3001 (admin/admin)"
echo ""
echo "🔑 Authentication:"
echo "  • Demo Token:   demo-token"
echo ""
echo "📋 Next Steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Upload a PDF document"
echo "  3. Ask questions about your documents"
echo ""
echo "🛠️  Development:"
echo "  • View logs:    docker-compose logs -f"
echo "  • Stop system:  docker-compose down"
echo "  • Restart:      docker-compose restart"
echo ""
echo "📖 Documentation:"
echo "  • README.md for detailed information"
echo "  • API docs at http://localhost:8000/api/docs"
echo ""
echo "Happy querying! 🎯" 
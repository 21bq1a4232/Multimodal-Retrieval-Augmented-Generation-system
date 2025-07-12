# Multimodal Retrieval-Augmented Generation (RAG) System

A production-grade, fully self-hosted Multimodal RAG system that ingests and processes PDF documents containing text, tables, and images, providing accurate, explainable answers with citations. Built entirely with open-source tools and designed for high accuracy (targeting 98% retrieval precision).

## 🚀 Features

### Core Capabilities
- **Multimodal Document Processing**: Extract and process text, tables, and images from PDFs
- **Advanced OCR**: Extract text from images using multiple OCR engines (EasyOCR, Tesseract)
- **Table Extraction**: Intelligent table detection and structured data extraction
- **Hybrid Retrieval**: Combines semantic and lexical search with custom ranking
- **Citation Support**: Provides accurate citations with page numbers and content types
- **Real-time Processing**: Background document processing with status tracking
- **High Accuracy**: Custom scoring algorithms targeting 98% retrieval precision

### Technical Features
- **Vector Database**: ChromaDB or FAISS for efficient similarity search
- **Embedding Models**: State-of-the-art sentence transformers for semantic search
- **LLM Integration**: Ollama for local, privacy-preserving answer generation
- **RESTful API**: FastAPI backend with automatic OpenAPI documentation
- **Modern Frontend**: React/Next.js with responsive design
- **Authentication**: Token-based authentication with user isolation
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Containerized**: Full Docker deployment with production-ready configuration

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Databases     │
│   (React/Next)  │◄───│   (FastAPI)     │◄───│   PostgreSQL    │
│                 │    │                 │    │   ChromaDB/FAISS│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Services      │
                       │   • PDF Parser  │
                       │   • OCR Engine  │
                       │   • Embeddings  │
                       │   • Retrieval   │
                       │   • Ollama LLM  │
                       └─────────────────┘
```

## 📋 System Requirements

### Hardware Requirements
- **CPU**: 4+ cores recommended
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 50GB+ available space
- **GPU**: Optional but recommended for faster processing

### Software Requirements
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Ollama**: Latest version
- **Python**: 3.11+ (for development)
- **Node.js**: 18+ (for frontend development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/multimodal-rag-system.git
cd multimodal-rag-system
```

### 2. Set Up Environment
```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

### 3. Install Ollama and Download Models
```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Download recommended model
ollama pull llama2
```

### 4. Start the System
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 5. Access the System
- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **Monitoring**: http://localhost:3001 (Grafana)

## 🔧 Configuration

### Environment Variables

```bash
# Application Settings
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/multimodal_rag

# Vector Database Configuration
VECTOR_DB_PATH=./data/vector_db
VECTOR_DB_TYPE=chromadb  # or faiss
EMBEDDING_DIM=384

# Embedding Model Configuration
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
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
```

### Retrieval Optimization

The system uses a hybrid retrieval approach with multiple scoring factors:

1. **Semantic Similarity**: Vector-based similarity using sentence transformers
2. **Lexical Matching**: BM25-based keyword matching
3. **Content Type Boosting**: Enhanced scoring for tables when queries contain numeric keywords
4. **Length Normalization**: Preference for moderately-sized chunks
5. **Position Scoring**: Slight boost for content appearing earlier in documents

## 📖 Usage Guide

### Document Upload

1. **Via Web Interface**:
   - Navigate to the Upload tab
   - Drag and drop PDF files or click to select
   - Monitor processing status in real-time

2. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/documents/upload" \
     -H "Authorization: Bearer demo-token" \
     -F "file=@document.pdf"
   ```

### Querying Documents

1. **Via Web Interface**:
   - Go to the Query tab
   - Enter your question
   - View answers with citations
   - Rate the helpfulness

2. **Via API**:
   ```bash
   curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer demo-token" \
     -d '{
       "query": "What are the main findings?",
       "filters": {"content_types": ["text", "table"]}
     }'
   ```

### Query Examples

- **General Questions**: "What is the main conclusion of this study?"
- **Specific Data**: "What were the sales figures for Q3?"
- **Table Data**: "Show me the performance metrics table"
- **Image Content**: "What does the diagram show?"

## 🔍 API Documentation

### Authentication
```bash
# All API endpoints require authentication
Authorization: Bearer your-token-here
```

### Key Endpoints

#### Document Management
- `POST /api/documents/upload` - Upload PDF documents
- `GET /api/documents/{id}/status` - Check processing status
- `GET /api/documents` - List user documents
- `DELETE /api/documents/{id}` - Delete document

#### Query & Answer
- `POST /api/query` - Submit questions and get answers
- `POST /api/feedback` - Submit feedback on answers

#### System
- `GET /api/health` - System health check
- `GET /api/stats` - Usage statistics

### Response Format
```json
{
  "answer": "The main findings indicate...",
  "confidence": 0.85,
  "citations": [
    {
      "reference_id": "1",
      "content": "Relevant excerpt...",
      "page_number": 15,
      "content_type": "text"
    }
  ],
  "metadata": {
    "total_time_ms": 1250,
    "chunks_used": 3,
    "model_used": "llama2"
  }
}
```

## 📊 Monitoring & Evaluation

### System Metrics
- **Retrieval Accuracy**: Precision, recall, and F1 scores
- **Response Time**: Query processing and answer generation latency
- **System Health**: Database connections, service status
- **Usage Statistics**: Documents processed, queries handled

### Accuracy Evaluation
```bash
# Run evaluation script
python scripts/evaluate_accuracy.py \
  --dataset ./data/evaluation/test_queries.json \
  --output ./reports/accuracy_report.json
```

### Performance Tuning
1. **Adjust Retrieval Parameters**: Modify `RETRIEVAL_K`, `RERANK_K`, `SIMILARITY_THRESHOLD`
2. **Optimize Scoring Weights**: Tune `SEMANTIC_WEIGHT`, `LEXICAL_WEIGHT`, `TABLE_BOOST`
3. **Chunk Size Optimization**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP`
4. **Model Selection**: Try different embedding models for your domain

## 🛠️ Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
pytest backend/tests/ -v --cov=backend

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
black backend/
isort backend/

# Type checking
mypy backend/

# Linting
flake8 backend/
```

## 🔒 Security

### Data Protection
- **User Isolation**: Documents are isolated per user
- **Encrypted Storage**: Database encryption at rest
- **Secure Authentication**: JWT token-based authentication
- **Input Validation**: Comprehensive file and input validation

### Security Best Practices
1. **Change Default Passwords**: Update all default credentials
2. **Use HTTPS**: Configure SSL certificates for production
3. **Regular Updates**: Keep all dependencies up to date
4. **Monitor Access**: Enable audit logging and monitoring
5. **Backup Strategy**: Implement regular database backups

## 🚀 Deployment

### Production Deployment

1. **Update Configuration**:
   ```bash
   # Production environment variables
   DEBUG=false
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=postgresql://user:pass@prod-db:5432/db
   ```

2. **Deploy with Docker**:
   ```bash
   # Build and deploy
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure Reverse Proxy**:
   - Set up SSL certificates
   - Configure domain routing
   - Enable security headers

### Scaling Considerations
- **Horizontal Scaling**: Deploy multiple backend instances
- **Database Optimization**: Use connection pooling and read replicas
- **Caching**: Implement Redis caching for frequent queries
- **Load Balancing**: Use nginx or cloud load balancers

## 🔧 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**:
   ```bash
   # Check Ollama service
   ollama list
   ollama serve
   ```

2. **Vector Database Issues**:
   ```bash
   # Reset vector database
   rm -rf ./data/vector_db
   docker-compose restart backend
   ```

3. **High Memory Usage**:
   - Reduce batch sizes in configuration
   - Use smaller embedding models
   - Implement memory monitoring

4. **Slow Processing**:
   - Enable GPU acceleration
   - Optimize chunk sizes
   - Use faster embedding models

### Debug Mode
```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG

# View detailed logs
docker-compose logs -f backend
```

## 📚 Model Information

### Embedding Models
- **Default**: `sentence-transformers/all-MiniLM-L6-v2`
- **Alternatives**: 
  - `sentence-transformers/all-mpnet-base-v2` (better quality)
  - `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` (QA optimized)

### LLM Models (Ollama)
- **Default**: `llama2`
- **Alternatives**:
  - `codellama` (code understanding)
  - `mistral` (efficient performance)
  - `llama2:13b` (better accuracy)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript for frontend components
- Write comprehensive tests
- Update documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Open Source Libraries**: FastAPI, React, ChromaDB, Sentence Transformers
- **OCR Engines**: EasyOCR, Tesseract
- **PDF Processing**: PyMuPDF, pdfplumber, tabula-py
- **LLM Integration**: Ollama community

## 📞 Support

- **Documentation**: Check this README and API docs
- **Issues**: Report bugs via GitHub Issues
- **Discussions**: Join community discussions
- **Email**: contact@multimodal-rag.com

---

Built with ❤️ for the open-source community. Star ⭐ this repository if you find it useful!
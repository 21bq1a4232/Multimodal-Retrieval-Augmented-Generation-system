#!/usr/bin/env python3
"""
Simple script to run the Multimodal RAG backend locally for development
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for local development
os.environ['DATABASE_URL'] = 'postgresql://postgres:password@localhost:5433/multimodal_rag'
os.environ['REDIS_URL'] = 'redis://localhost:6379'
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
os.environ['VECTOR_DB_PATH'] = './data/vector_db'
os.environ['UPLOAD_DIRECTORY'] = './data/uploads'
os.environ['DEBUG'] = 'true'
os.environ['LOG_LEVEL'] = 'INFO'

# Create data directories
os.makedirs('./data/uploads', exist_ok=True)
os.makedirs('./data/vector_db', exist_ok=True)
os.makedirs('./logs', exist_ok=True)

def check_dependencies():
    """Check if required services are running"""
    print("🔍 Checking dependencies...")
    
    # Check Ollama
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is running")
            if 'llama2' in result.stdout:
                print("✅ llama2 model is available")
            else:
                print("⚠️  llama2 model not found, but continuing...")
        else:
            print("❌ Ollama is not running. Please start with: ollama serve")
            return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        return False
    
    # Check PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            database='multimodal_rag',
            user='postgres',
            password='password'
        )
        conn.close()
        print("✅ PostgreSQL is accessible")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is accessible")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    return True

def install_basic_requirements():
    """Install basic requirements for running the server"""
    print("📦 Installing basic requirements...")
    
    basic_requirements = [
        'fastapi==0.104.1',
        'uvicorn[standard]==0.24.0',
        'pydantic==2.5.0',
        'pydantic-settings==2.1.0',
        'httpx==0.25.2',
        'python-dotenv==1.0.0',
        'psycopg2-binary==2.9.9',
        'redis==5.0.1'
    ]
    
    for req in basic_requirements:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', req], 
                         check=True, capture_output=True)
            print(f"✅ Installed {req}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {req}: {e}")
            return False
    
    return True

def run_server():
    """Run the FastAPI server"""
    print("🚀 Starting the Multimodal RAG backend...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/api/docs")
    print("")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Run with uvicorn
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'backend.api.main:app',
            '--host', '0.0.0.0',
            '--port', '8000',
            '--reload',
            '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error running server: {e}")

def main():
    """Main function"""
    print("🚀 Multimodal RAG System - Development Server")
    print("=" * 50)
    
    # Check and install basic requirements
    if not install_basic_requirements():
        print("❌ Failed to install requirements")
        return 1
    
    # Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        print("\n💡 Quick setup commands:")
        print("  - Start Ollama: ollama serve")
        print("  - Start PostgreSQL: docker-compose -f docker-compose.dev.yml up -d postgres")
        print("  - Redis should already be running")
        return 1
    
    # Run the server
    run_server()
    return 0

if __name__ == '__main__':
    sys.exit(main()) 
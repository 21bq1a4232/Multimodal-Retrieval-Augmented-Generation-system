#!/usr/bin/env python3
"""
Demo Backend for Multimodal RAG System
A simplified version that demonstrates the core functionality
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import json

# Set up the FastAPI app
app = FastAPI(
    title="Multimodal RAG System - Demo",
    version="1.0.0",
    description="Production-grade Multimodal Retrieval-Augmented Generation System",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo data
demo_documents = [
    {
        "id": "demo-doc-1",
        "filename": "research_paper.pdf",
        "status": "completed",
        "total_pages": 15,
        "total_chunks": 45,
        "uploaded_at": "2025-01-12T09:00:00",
        "processed_at": "2025-01-12T09:02:30"
    },
    {
        "id": "demo-doc-2", 
        "filename": "financial_report.pdf",
        "status": "completed",
        "total_pages": 8,
        "total_chunks": 28,
        "uploaded_at": "2025-01-12T08:30:00",
        "processed_at": "2025-01-12T08:31:45"
    }
]

demo_chunks = [
    {
        "chunk_id": "chunk-1",
        "content": "The study reveals significant improvements in model accuracy when using multimodal approaches. Our results show a 15% increase in performance compared to text-only methods.",
        "content_type": "text",
        "page_number": 3,
        "score": 0.95
    },
    {
        "chunk_id": "chunk-2", 
        "content": "Table 1: Performance Metrics\nMethod | Accuracy | Precision | Recall\nText-only | 78.2% | 76.5% | 79.1%\nMultimodal | 89.7% | 88.3% | 90.2%",
        "content_type": "table",
        "page_number": 4,
        "score": 0.88
    },
    {
        "chunk_id": "chunk-3",
        "content": "Figure 2 shows the architecture diagram of our proposed multimodal system, illustrating the integration of text, image, and table processing components.",
        "content_type": "image", 
        "page_number": 6,
        "score": 0.82
    }
]

# Request models
class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str

# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Multimodal RAG System Demo",
        "version": "1.0.0",
        "docs": "/api/docs",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    
    # Check Ollama connection
    ollama_status = "healthy"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                ollama_status = "healthy"
            else:
                ollama_status = "unhealthy"
    except Exception:
        ollama_status = "unreachable"
    
    return {
        "status": "healthy",
        "version": "1.0.0", 
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "healthy",
            "ollama": ollama_status,
            "demo_mode": True
        }
    }

@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Demo document upload - simulates processing"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Simulate processing
    document_id = f"demo-{len(demo_documents) + 1}"
    
    # Add to demo documents
    new_doc = {
        "id": document_id,
        "filename": file.filename,
        "status": "processing",
        "total_pages": 10,
        "total_chunks": 0,
        "uploaded_at": datetime.now().isoformat(),
        "processed_at": None
    }
    demo_documents.append(new_doc)
    
    # Simulate async processing
    asyncio.create_task(simulate_processing(document_id))
    
    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status="processing",
        message="Document uploaded successfully and processing started"
    )

async def simulate_processing(document_id: str):
    """Simulate document processing"""
    await asyncio.sleep(3)  # Simulate processing time
    
    # Update document status
    for doc in demo_documents:
        if doc["id"] == document_id:
            doc["status"] = "completed"
            doc["total_chunks"] = 25
            doc["processed_at"] = datetime.now().isoformat()
            break

@app.get("/api/documents/{document_id}/status")
async def get_document_status(document_id: str):
    """Get document processing status"""
    
    # Find document
    document = None
    for doc in demo_documents:
        if doc["id"] == document_id:
            document = doc
            break
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@app.get("/api/documents")
async def list_documents():
    """List all documents"""
    return {
        "documents": demo_documents,
        "total": len(demo_documents)
    }

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Demo query processing with simulated retrieval and generation"""
    
    query = request.query.lower()
    
    # Simple keyword matching for demo
    relevant_chunks = []
    for chunk in demo_chunks:
        if any(word in chunk["content"].lower() for word in query.split()):
            relevant_chunks.append(chunk)
    
    if not relevant_chunks:
        # Default response if no matches
        relevant_chunks = demo_chunks[:2]  # Return first 2 chunks
    
    # Simulate answer generation
    answer = await generate_demo_answer(query, relevant_chunks)
    
    # Create citations
    citations = []
    for i, chunk in enumerate(relevant_chunks):
        citations.append({
            "reference_id": str(i + 1),
            "chunk_id": chunk["chunk_id"], 
            "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
            "content_type": chunk["content_type"],
            "page_number": chunk["page_number"],
            "score": chunk["score"]
        })
    
    return QueryResponse(
        answer=answer,
        confidence=0.85,
        citations=citations,
        metadata={
            "query": request.query,
            "total_time_ms": 1200,
            "generation_time_ms": 800,
            "retrieval_time_ms": 400,
            "chunks_used": len(relevant_chunks),
            "model_used": "llama2",
            "timestamp": datetime.now().isoformat()
        }
    )

async def generate_demo_answer(query: str, chunks: List[Dict[str, Any]]) -> str:
    """Generate a demo answer using Ollama or fallback to template"""
    
    # Try to use Ollama if available
    try:
        async with httpx.AsyncClient() as client:
            context = "\n\n".join([f"[{i+1}] {chunk['content']}" for i, chunk in enumerate(chunks)])
            
            prompt = f"""Based on the following context, answer the question clearly and concisely:

Context:
{context}

Question: {query}

Answer:"""

            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
                
    except Exception as e:
        print(f"Ollama generation failed: {e}")
    
    # Fallback to template response
    if "performance" in query or "accuracy" in query or "result" in query:
        return "Based on the research data [1], our multimodal approach shows significant improvements with 89.7% accuracy compared to 78.2% for text-only methods [2]. The performance metrics demonstrate a 15% increase in overall effectiveness when combining text, image, and table processing capabilities."
    
    elif "table" in query or "data" in query:
        return "The performance comparison table [2] shows detailed metrics across different methods. The multimodal approach achieves 89.7% accuracy, 88.3% precision, and 90.2% recall, significantly outperforming the text-only baseline across all metrics."
    
    elif "architecture" in query or "system" in query or "diagram" in query:
        return "The system architecture [3] illustrates the integration of multiple modalities including text, image, and table processing components. This multimodal design enables comprehensive document understanding and more accurate information retrieval."
    
    else:
        return f"Based on the available research data [1], I can provide information about multimodal document processing systems. The study demonstrates significant improvements when combining different types of content analysis. Please feel free to ask more specific questions about the performance metrics, system architecture, or methodology."

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        "system_stats": {
            "total_documents": len(demo_documents),
            "total_chunks": sum(doc.get("total_chunks", 0) for doc in demo_documents),
            "processed_documents": len([doc for doc in demo_documents if doc["status"] == "completed"]),
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "llm_model": "llama2",
            "vector_db": "chromadb",
            "demo_mode": True
        },
        "performance_metrics": {
            "avg_response_time_ms": 1200,
            "avg_confidence": 0.85,
            "retrieval_accuracy": 0.92
        }
    }

@app.delete("/api/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document"""
    global demo_documents
    
    # Find and remove document
    demo_documents = [doc for doc in demo_documents if doc["id"] != document_id]
    
    return {"message": "Document deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Multimodal RAG System Demo")
    print("📍 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/api/docs")
    print("🔍 Health Check: http://localhost:8000/api/health")
    print("")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 
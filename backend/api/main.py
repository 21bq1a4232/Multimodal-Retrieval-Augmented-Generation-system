"""
FastAPI Backend for Multimodal RAG System
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Import services
from backend.core.config import settings
from backend.core.database import get_async_session, create_tables
from backend.services.pdf_ingestion import PDFIngestionService
from backend.services.embedding_service import embedding_service
from backend.services.retrieval_service import retrieval_service
from backend.services.answer_generation_service import answer_generation_service
from backend.models.document import Document, QueryLog


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade Multimodal RAG System API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Initialize services
pdf_ingestion_service = PDFIngestionService()


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    citations: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class FeedbackRequest(BaseModel):
    query_id: str
    rating: Optional[int] = None
    helpful: Optional[bool] = None
    comment: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    total_pages: Optional[int] = None
    total_chunks: Optional[int] = None
    error_message: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, Any]


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple token-based authentication"""
    # In production, implement proper JWT validation
    if credentials.credentials == "demo-token":
        return {"user_id": "demo-user", "username": "demo"}
    raise HTTPException(status_code=401, detail="Invalid authentication credentials")


# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Multimodal RAG System API",
        "version": settings.app_version,
        "docs": "/api/docs"
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        async with get_async_session() as session:
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Check services
    try:
        embedding_stats = await embedding_service.get_embedding_stats()
        embedding_status = "healthy"
    except Exception as e:
        embedding_status = f"unhealthy: {str(e)}"
        embedding_stats = {}
    
    try:
        retrieval_stats = await retrieval_service.get_retrieval_stats()
        retrieval_status = "healthy"
    except Exception as e:
        retrieval_status = f"unhealthy: {str(e)}"
        retrieval_stats = {}
    
    try:
        ollama_health = await answer_generation_service.check_ollama_health()
        ollama_status = ollama_health.get('status', 'unknown')
    except Exception as e:
        ollama_status = f"unhealthy: {str(e)}"
        ollama_health = {}
    
    overall_status = "healthy" if all([
        "healthy" in db_status,
        "healthy" in embedding_status,
        "healthy" in retrieval_status,
        "healthy" in ollama_status
    ]) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.now(),
        services={
            "database": db_status,
            "embedding": embedding_status,
            "retrieval": retrieval_status,
            "ollama": ollama_status,
            "embedding_stats": embedding_stats,
            "retrieval_stats": retrieval_stats,
            "ollama_health": ollama_health
        }
    )


@app.post("/api/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    user: dict = Depends(get_current_user)
):
    """Upload and process a PDF document"""
    try:
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        if file.size > settings.max_file_size:
            raise HTTPException(status_code=400, detail="File too large")
        
        # Generate unique filename
        document_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix
        safe_filename = f"{document_id}{file_extension}"
        file_path = Path(settings.upload_directory) / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create document record
        async with get_async_session() as session:
            document = Document(
                id=document_id,
                filename=safe_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                file_size=file.size,
                mime_type=file.content_type,
                user_id=user_id or user["user_id"],
                status="pending"
            )
            session.add(document)
            await session.commit()
        
        # Start background processing
        try:
            processing_result = await pdf_ingestion_service.process_pdf(
                file_path=str(file_path),
                filename=file.filename,
                user_id=user_id or user["user_id"]
            )
            
            # Update document status
            async with get_async_session() as session:
                document.status = "processing"
                document.total_pages = processing_result.get('total_pages', 0)
                document.total_chunks = processing_result.get('total_chunks', 0)
                document.processed_at = datetime.now()
                await session.commit()
            
            # Generate embeddings
            if processing_result.get('chunks'):
                embeddings = await embedding_service.generate_embeddings(processing_result['chunks'])
                
                # Update retrieval corpus
                await retrieval_service.update_corpus(processing_result['chunks'])
                
                # Update document status to completed
                async with get_async_session() as session:
                    document.status = "completed"
                    await session.commit()
                
                logger.info(f"Document {document_id} processed successfully")
                
                return DocumentUploadResponse(
                    document_id=document_id,
                    filename=file.filename,
                    status="completed",
                    message="Document processed successfully"
                )
        
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Update document status to failed
            async with get_async_session() as session:
                document.status = "failed"
                document.error_message = str(e)
                await session.commit()
            
            return DocumentUploadResponse(
                document_id=document_id,
                filename=file.filename,
                status="failed",
                message=f"Document processing failed: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """Get document processing status"""
    try:
        async with get_async_session() as session:
            document = await session.get(Document, document_id)
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Check user access
            if document.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            return DocumentStatusResponse(
                document_id=document.id,
                filename=document.original_filename,
                status=document.status,
                total_pages=document.total_pages,
                total_chunks=document.total_chunks,
                error_message=document.error_message,
                uploaded_at=document.uploaded_at,
                processed_at=document.processed_at
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents")
async def list_documents(
    user: dict = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List user's documents"""
    try:
        async with get_async_session() as session:
            # In a real implementation, you'd use proper async query
            # This is a simplified version
            documents = []  # Would fetch from database
            
            return {
                "documents": documents,
                "total": len(documents),
                "skip": skip,
                "limit": limit
            }
    
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    user: dict = Depends(get_current_user)
):
    """Query documents and generate answer"""
    try:
        logger.info(f"Received query: {request.query}")
        
        # Generate answer
        result = await answer_generation_service.generate_answer(
            query=request.query,
            filters=request.filters,
            user_id=request.user_id or user["user_id"]
        )
        
        # Log query
        async with get_async_session() as session:
            query_log = QueryLog(
                query_text=request.query,
                user_id=request.user_id or user["user_id"],
                generated_answer=result["answer"],
                answer_confidence=result["confidence"],
                citations=result["citations"],
                retrieval_time_ms=result["metadata"]["retrieval_time_ms"],
                generation_time_ms=result["metadata"]["generation_time_ms"],
                total_time_ms=result["metadata"]["total_time_ms"],
                total_retrieved=result["metadata"]["chunks_used"]
            )
            session.add(query_log)
            await session.commit()
        
        return QueryResponse(
            answer=result["answer"],
            confidence=result["confidence"],
            citations=result["citations"],
            metadata=result["metadata"]
        )
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
async def submit_feedback(
    feedback: FeedbackRequest,
    user: dict = Depends(get_current_user)
):
    """Submit feedback for a query"""
    try:
        async with get_async_session() as session:
            # Find the query log
            query_log = await session.get(QueryLog, feedback.query_id)
            
            if not query_log:
                raise HTTPException(status_code=404, detail="Query not found")
            
            # Check user access
            if query_log.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Update feedback
            query_log.feedback_rating = feedback.rating
            query_log.feedback_helpful = feedback.helpful
            query_log.feedback_comment = feedback.comment
            query_log.feedback_at = datetime.now()
            
            await session.commit()
        
        return {"message": "Feedback submitted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_system_stats(user: dict = Depends(get_current_user)):
    """Get system statistics"""
    try:
        embedding_stats = await embedding_service.get_embedding_stats()
        retrieval_stats = await retrieval_service.get_retrieval_stats()
        
        # Get user-specific stats
        async with get_async_session() as session:
            # This would be implemented with proper async queries
            user_stats = {
                "documents_uploaded": 0,
                "queries_made": 0,
                "avg_confidence": 0.0
            }
        
        return {
            "user_stats": user_stats,
            "system_stats": {
                "embedding_stats": embedding_stats,
                "retrieval_stats": retrieval_stats
            }
        }
    
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/documents/{document_id}")
async def delete_document(
    document_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a document"""
    try:
        async with get_async_session() as session:
            document = await session.get(Document, document_id)
            
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Check user access
            if document.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
            
            # Delete file
            try:
                os.remove(document.file_path)
            except FileNotFoundError:
                pass
            
            # Delete from database
            await session.delete(document)
            await session.commit()
        
        return {"message": "Document deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Multimodal RAG System API")
    
    # Create database tables
    await create_tables()
    
    logger.info("API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Multimodal RAG System API")
    
    # Close services
    await embedding_service.close()
    await retrieval_service.close()
    await answer_generation_service.close()
    
    logger.info("API shut down successfully")


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.now().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )


# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "backend.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 
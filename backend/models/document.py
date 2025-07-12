"""
Database models for document storage and metadata
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Dict, Any, Optional, List
from backend.core.database import Base


class Document(Base):
    """Document model for storing PDF metadata"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Metadata
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)
    creator = Column(String(255), nullable=True)
    producer = Column(String(255), nullable=True)
    creation_date = Column(DateTime, nullable=True)
    modification_date = Column(DateTime, nullable=True)
    
    # Processing metadata
    total_pages = Column(Integer, nullable=True)
    total_chunks = Column(Integer, default=0)
    total_images = Column(Integer, default=0)
    total_tables = Column(Integer, default=0)
    
    # Timestamps
    uploaded_at = Column(DateTime, default=func.now())
    processed_at = Column(DateTime, nullable=True)
    
    # User context (for multi-tenancy)
    user_id = Column(String(255), nullable=True)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"


class DocumentChunk(Base):
    """Chunk model for storing processed document segments"""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    
    # Chunk identification
    chunk_id = Column(String(255), unique=True, nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # text, table, image, ocr
    cleaned_content = Column(Text, nullable=True)  # Cleaned for embeddings
    
    # Positioning
    page_number = Column(Integer, nullable=False)
    bbox = Column(JSON, nullable=True)  # Bounding box coordinates
    
    # Hierarchy and structure
    heading_level = Column(Integer, nullable=True)
    parent_heading = Column(String(500), nullable=True)
    section_title = Column(String(500), nullable=True)
    
    # Table-specific metadata
    table_metadata = Column(JSON, nullable=True)  # Headers, structure, etc.
    
    # Image-specific metadata
    image_metadata = Column(JSON, nullable=True)  # Size, format, OCR confidence
    
    # Processing metadata
    word_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("ChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, chunk_id='{self.chunk_id}', type='{self.content_type}')>"


class ChunkEmbedding(Base):
    """Embedding model for storing vector embeddings"""
    __tablename__ = "chunk_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("document_chunks.id"), nullable=False)
    
    # Embedding metadata
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(100), nullable=True)
    embedding_dim = Column(Integer, nullable=False)
    
    # Vector storage reference (actual vectors stored in vector DB)
    vector_db_id = Column(String(255), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    chunk = relationship("DocumentChunk", back_populates="embeddings")
    
    def __repr__(self):
        return f"<ChunkEmbedding(id={self.id}, model='{self.model_name}')>"


class QueryLog(Base):
    """Query log model for tracking user queries and responses"""
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query details
    query_text = Column(Text, nullable=False)
    query_embedding_id = Column(String(255), nullable=True)
    
    # User context
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    
    # Retrieval results
    retrieved_chunks = Column(JSON, nullable=True)  # List of chunk IDs and scores
    total_retrieved = Column(Integer, default=0)
    
    # Answer generation
    generated_answer = Column(Text, nullable=True)
    answer_confidence = Column(Float, nullable=True)
    citations = Column(JSON, nullable=True)  # List of citations with metadata
    
    # Performance metrics
    retrieval_time_ms = Column(Float, nullable=True)
    generation_time_ms = Column(Float, nullable=True)
    total_time_ms = Column(Float, nullable=True)
    
    # User feedback
    feedback_rating = Column(Integer, nullable=True)  # 1-5 rating
    feedback_helpful = Column(Boolean, nullable=True)
    feedback_comment = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    feedback_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<QueryLog(id={self.id}, query='{self.query_text[:50]}...')>"


class SystemMetrics(Base):
    """System metrics model for monitoring and evaluation"""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_type = Column(String(100), nullable=False)  # accuracy, precision, recall, etc.
    metric_value = Column(Float, nullable=False)
    metric_metadata = Column(JSON, nullable=True)
    
    # Context
    evaluation_dataset = Column(String(255), nullable=True)
    model_version = Column(String(100), nullable=True)
    configuration = Column(JSON, nullable=True)
    
    # Timestamp
    recorded_at = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, type='{self.metric_type}', value={self.metric_value})>"


class UserSession(Base):
    """User session model for authentication and context"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Session details
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id='{self.user_id}', active={self.is_active})>" 
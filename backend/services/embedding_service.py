"""
Embedding Generation and Vector Storage Service
"""
import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings as ChromaSettings
import faiss
import pickle
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from backend.core.config import settings, VECTOR_DB_CONFIG
from backend.models.document import DocumentChunk, ChunkEmbedding


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        self.model = None
        self.vector_db = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Initialize embedding model
        self._initialize_embedding_model()
        
        # Initialize vector database
        self._initialize_vector_db()
    
    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        try:
            logger.info(f"Loading embedding model: {settings.embedding_model_name}")
            self.model = SentenceTransformer(settings.embedding_model_name)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def _initialize_vector_db(self):
        """Initialize vector database"""
        try:
            if VECTOR_DB_CONFIG['type'] == 'chromadb':
                self._initialize_chromadb()
            elif VECTOR_DB_CONFIG['type'] == 'faiss':
                self._initialize_faiss()
            else:
                raise ValueError(f"Unsupported vector database type: {VECTOR_DB_CONFIG['type']}")
            
            logger.info(f"Vector database initialized: {VECTOR_DB_CONFIG['type']}")
        except Exception as e:
            logger.error(f"Failed to initialize vector database: {str(e)}")
            raise
    
    def _initialize_chromadb(self):
        """Initialize ChromaDB"""
        db_path = Path(VECTOR_DB_CONFIG['path'])
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(db_path),
            settings=ChromaSettings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )
        
        # Create or get collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="document_chunks",
            metadata={"hnsw:space": "cosine"}
        )
    
    def _initialize_faiss(self):
        """Initialize FAISS index"""
        self.faiss_index = None
        self.faiss_metadata = {}
        self.faiss_path = Path(VECTOR_DB_CONFIG['path'])
        self.faiss_path.mkdir(parents=True, exist_ok=True)
        
        # Try to load existing index
        index_file = self.faiss_path / "faiss_index.bin"
        metadata_file = self.faiss_path / "faiss_metadata.pkl"
        
        if index_file.exists() and metadata_file.exists():
            try:
                self.faiss_index = faiss.read_index(str(index_file))
                with open(metadata_file, 'rb') as f:
                    self.faiss_metadata = pickle.load(f)
                logger.info("Loaded existing FAISS index")
            except Exception as e:
                logger.warning(f"Failed to load existing FAISS index: {str(e)}")
                self._create_new_faiss_index()
        else:
            self._create_new_faiss_index()
    
    def _create_new_faiss_index(self):
        """Create a new FAISS index"""
        # Create HNSW index for better performance
        self.faiss_index = faiss.IndexHNSWFlat(
            VECTOR_DB_CONFIG['embedding_dim'],
            32  # number of connections
        )
        self.faiss_index.hnsw.efConstruction = 200
        self.faiss_index.hnsw.efSearch = 50
        self.faiss_metadata = {}
        logger.info("Created new FAISS index")
    
    async def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for document chunks
        
        Args:
            chunks: List of document chunks
            
        Returns:
            List of chunks with embedding metadata
        """
        try:
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            
            # Prepare texts for embedding
            texts = []
            chunk_embeddings = []
            
            for chunk in chunks:
                # Use cleaned content for embedding or fallback to original
                text = chunk.get('cleaned_content', chunk.get('content', ''))
                
                # Apply content-type specific preprocessing
                if chunk.get('content_type') == 'table':
                    text = self._preprocess_table_for_embedding(text, chunk)
                elif chunk.get('content_type') == 'image':
                    text = self._preprocess_image_for_embedding(text, chunk)
                
                texts.append(text)
            
            # Generate embeddings in batches
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                self.executor, self._generate_embeddings_batch, texts
            )
            
            # Process embeddings and store in vector database
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = await self._store_embedding(
                    chunk['chunk_id'], 
                    embedding, 
                    chunk
                )
                
                chunk_embeddings.append({
                    'chunk_id': chunk['chunk_id'],
                    'vector_id': vector_id,
                    'embedding_model': settings.embedding_model_name,
                    'embedding_dim': len(embedding)
                })
            
            logger.info(f"Generated and stored {len(chunk_embeddings)} embeddings")
            return chunk_embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def _generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings for a batch of texts"""
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=32,
                show_progress_bar=True,
                convert_to_numpy=True
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error in batch embedding generation: {str(e)}")
            raise
    
    def _preprocess_table_for_embedding(self, text: str, chunk: Dict[str, Any]) -> str:
        """Preprocess table content for better embedding"""
        # Add table-specific context
        table_metadata = chunk.get('table_metadata', {})
        
        # Create enhanced text with table structure information
        enhanced_text = f"Table with {table_metadata.get('rows', 0)} rows and {table_metadata.get('columns', 0)} columns. "
        
        # Add header information
        headers = table_metadata.get('headers', [])
        if headers:
            enhanced_text += f"Headers: {', '.join(headers)}. "
        
        # Add original table content
        enhanced_text += text
        
        return enhanced_text
    
    def _preprocess_image_for_embedding(self, text: str, chunk: Dict[str, Any]) -> str:
        """Preprocess image OCR content for better embedding"""
        # Add image-specific context
        image_metadata = chunk.get('image_metadata', {})
        
        # Create enhanced text with image context
        enhanced_text = f"Image content extracted via OCR (confidence: {image_metadata.get('ocr_confidence', 0):.2f}). "
        enhanced_text += text
        
        return enhanced_text
    
    async def _store_embedding(self, chunk_id: str, embedding: np.ndarray, chunk: Dict[str, Any]) -> str:
        """Store embedding in vector database"""
        try:
            if VECTOR_DB_CONFIG['type'] == 'chromadb':
                return await self._store_in_chromadb(chunk_id, embedding, chunk)
            elif VECTOR_DB_CONFIG['type'] == 'faiss':
                return await self._store_in_faiss(chunk_id, embedding, chunk)
            else:
                raise ValueError(f"Unsupported vector database type: {VECTOR_DB_CONFIG['type']}")
        except Exception as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise
    
    async def _store_in_chromadb(self, chunk_id: str, embedding: np.ndarray, chunk: Dict[str, Any]) -> str:
        """Store embedding in ChromaDB"""
        try:
            # Prepare metadata
            metadata = {
                'chunk_id': chunk_id,
                'content_type': chunk.get('content_type', 'text'),
                'page_number': chunk.get('page_number', 1),
                'word_count': chunk.get('word_count', 0),
                'char_count': chunk.get('char_count', 0)
            }
            
            # Add type-specific metadata
            if chunk.get('content_type') == 'table':
                table_meta = chunk.get('table_metadata', {})
                metadata.update({
                    'table_rows': table_meta.get('rows', 0),
                    'table_columns': table_meta.get('columns', 0)
                })
            elif chunk.get('content_type') == 'image':
                img_meta = chunk.get('image_metadata', {})
                metadata.update({
                    'ocr_confidence': img_meta.get('ocr_confidence', 0),
                    'ocr_engine': img_meta.get('ocr_engine', 'unknown')
                })
            
            # Store in ChromaDB
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding.tolist()],
                metadatas=[metadata],
                documents=[chunk.get('content', '')]
            )
            
            return chunk_id
            
        except Exception as e:
            logger.error(f"Error storing embedding in ChromaDB: {str(e)}")
            raise
    
    async def _store_in_faiss(self, chunk_id: str, embedding: np.ndarray, chunk: Dict[str, Any]) -> str:
        """Store embedding in FAISS"""
        try:
            # Add to FAISS index
            embedding_normalized = embedding.reshape(1, -1)
            faiss.normalize_L2(embedding_normalized)
            
            index = self.faiss_index.ntotal
            self.faiss_index.add(embedding_normalized)
            
            # Store metadata
            self.faiss_metadata[index] = {
                'chunk_id': chunk_id,
                'content_type': chunk.get('content_type', 'text'),
                'page_number': chunk.get('page_number', 1),
                'word_count': chunk.get('word_count', 0),
                'char_count': chunk.get('char_count', 0),
                'content': chunk.get('content', '')
            }
            
            # Save index and metadata
            await self._save_faiss_index()
            
            return str(index)
            
        except Exception as e:
            logger.error(f"Error storing embedding in FAISS: {str(e)}")
            raise
    
    async def _save_faiss_index(self):
        """Save FAISS index and metadata to disk"""
        try:
            index_file = self.faiss_path / "faiss_index.bin"
            metadata_file = self.faiss_path / "faiss_metadata.pkl"
            
            # Save index
            faiss.write_index(self.faiss_index, str(index_file))
            
            # Save metadata
            with open(metadata_file, 'wb') as f:
                pickle.dump(self.faiss_metadata, f)
                
        except Exception as e:
            logger.error(f"Error saving FAISS index: {str(e)}")
            raise
    
    async def search_similar(self, query: str, k: int = 10, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for similar chunks based on query
        
        Args:
            query: Search query
            k: Number of results to return
            filters: Optional filters for search
            
        Returns:
            List of similar chunks with scores
        """
        try:
            logger.info(f"Searching for similar chunks: {query[:50]}...")
            
            # Generate query embedding
            loop = asyncio.get_event_loop()
            query_embedding = await loop.run_in_executor(
                self.executor, self._generate_query_embedding, query
            )
            
            # Search in vector database
            if VECTOR_DB_CONFIG['type'] == 'chromadb':
                results = await self._search_chromadb(query_embedding, k, filters)
            elif VECTOR_DB_CONFIG['type'] == 'faiss':
                results = await self._search_faiss(query_embedding, k, filters)
            else:
                raise ValueError(f"Unsupported vector database type: {VECTOR_DB_CONFIG['type']}")
            
            logger.info(f"Found {len(results)} similar chunks")
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar chunks: {str(e)}")
            raise
    
    def _generate_query_embedding(self, query: str) -> np.ndarray:
        """Generate embedding for search query"""
        try:
            embedding = self.model.encode([query], convert_to_numpy=True)
            return embedding[0]
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            raise
    
    async def _search_chromadb(self, query_embedding: np.ndarray, k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search in ChromaDB"""
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if filters:
                if 'content_type' in filters:
                    where_clause['content_type'] = filters['content_type']
                if 'page_number' in filters:
                    where_clause['page_number'] = filters['page_number']
            
            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=k,
                where=where_clause if where_clause else None
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'chunk_id': results['ids'][0][i],
                    'score': 1 - results['distances'][0][i],  # Convert distance to similarity
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            raise
    
    async def _search_faiss(self, query_embedding: np.ndarray, k: int, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search in FAISS"""
        try:
            # Normalize query embedding
            query_normalized = query_embedding.reshape(1, -1)
            faiss.normalize_L2(query_normalized)
            
            # Search in FAISS
            scores, indices = self.faiss_index.search(query_normalized, k)
            
            # Format results
            formatted_results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx in self.faiss_metadata:
                    metadata = self.faiss_metadata[idx]
                    
                    # Apply filters if provided
                    if filters:
                        if 'content_type' in filters and metadata.get('content_type') != filters['content_type']:
                            continue
                        if 'page_number' in filters and metadata.get('page_number') != filters['page_number']:
                            continue
                    
                    formatted_results.append({
                        'chunk_id': metadata['chunk_id'],
                        'score': float(score),
                        'content': metadata['content'],
                        'metadata': metadata
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching FAISS: {str(e)}")
            raise
    
    async def update_embeddings(self, chunk_ids: List[str], new_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update embeddings for existing chunks
        
        Args:
            chunk_ids: List of chunk IDs to update
            new_chunks: List of updated chunk data
            
        Returns:
            List of updated embedding metadata
        """
        try:
            logger.info(f"Updating embeddings for {len(chunk_ids)} chunks")
            
            # Remove old embeddings
            await self._remove_embeddings(chunk_ids)
            
            # Generate new embeddings
            updated_embeddings = await self.generate_embeddings(new_chunks)
            
            logger.info(f"Updated {len(updated_embeddings)} embeddings")
            return updated_embeddings
            
        except Exception as e:
            logger.error(f"Error updating embeddings: {str(e)}")
            raise
    
    async def _remove_embeddings(self, chunk_ids: List[str]):
        """Remove embeddings from vector database"""
        try:
            if VECTOR_DB_CONFIG['type'] == 'chromadb':
                self.collection.delete(ids=chunk_ids)
            elif VECTOR_DB_CONFIG['type'] == 'faiss':
                # FAISS doesn't support deletion easily, so we'll recreate the index
                # This is a simplification - in production, you might want to implement
                # a more sophisticated deletion strategy
                logger.warning("FAISS deletion not implemented - consider using ChromaDB for frequent updates")
            
        except Exception as e:
            logger.error(f"Error removing embeddings: {str(e)}")
            raise
    
    async def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings"""
        try:
            if VECTOR_DB_CONFIG['type'] == 'chromadb':
                count = self.collection.count()
                return {
                    'total_embeddings': count,
                    'database_type': 'chromadb',
                    'embedding_model': settings.embedding_model_name,
                    'embedding_dim': VECTOR_DB_CONFIG['embedding_dim']
                }
            elif VECTOR_DB_CONFIG['type'] == 'faiss':
                return {
                    'total_embeddings': self.faiss_index.ntotal,
                    'database_type': 'faiss',
                    'embedding_model': settings.embedding_model_name,
                    'embedding_dim': VECTOR_DB_CONFIG['embedding_dim']
                }
            
        except Exception as e:
            logger.error(f"Error getting embedding stats: {str(e)}")
            return {}
    
    async def close(self):
        """Close connections and clean up resources"""
        try:
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)
            
            if VECTOR_DB_CONFIG['type'] == 'faiss':
                await self._save_faiss_index()
            
            logger.info("Embedding service closed")
            
        except Exception as e:
            logger.error(f"Error closing embedding service: {str(e)}")


# Global embedding service instance
embedding_service = EmbeddingService() 
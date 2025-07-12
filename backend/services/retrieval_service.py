"""
Hybrid Retrieval and Ranking Service
"""
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import re
from collections import Counter

from backend.core.config import settings, RETRIEVAL_CONFIG
from backend.services.embedding_service import embedding_service


logger = logging.getLogger(__name__)


class HybridRetrievalService:
    """Service for hybrid retrieval and ranking with custom scoring"""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.bm25_index = None
        self.document_corpus = []
        self.chunk_metadata = {}
        
    async def search_and_rank(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform hybrid search and ranking
        
        Args:
            query: Search query
            filters: Optional filters for search
            
        Returns:
            Dict containing ranked results and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting hybrid search for query: {query[:50]}...")
            
            # Step 1: Semantic search using embeddings
            semantic_results = await self._semantic_search(query, filters)
            
            # Step 2: Lexical search using BM25
            lexical_results = await self._lexical_search(query, filters)
            
            # Step 3: Hybrid scoring and ranking
            hybrid_results = await self._hybrid_ranking(
                query, semantic_results, lexical_results
            )
            
            # Step 4: Apply final filters and limits
            final_results = await self._apply_final_filters(
                hybrid_results, filters
            )
            
            retrieval_time = (time.time() - start_time) * 1000
            
            search_metadata = {
                'query': query,
                'total_results': len(final_results),
                'retrieval_time_ms': retrieval_time,
                'semantic_results': len(semantic_results),
                'lexical_results': len(lexical_results),
                'hybrid_results': len(hybrid_results),
                'filters_applied': filters or {},
                'retrieval_config': RETRIEVAL_CONFIG
            }
            
            logger.info(f"Hybrid search completed: {len(final_results)} results in {retrieval_time:.2f}ms")
            
            return {
                'results': final_results,
                'metadata': search_metadata
            }
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}")
            raise
    
    async def _semantic_search(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        try:
            # Use embedding service for semantic search
            results = await self.embedding_service.search_similar(
                query=query,
                k=RETRIEVAL_CONFIG['k'],
                filters=filters
            )
            
            # Enhance results with semantic scores
            for result in results:
                result['semantic_score'] = result.get('score', 0.0)
                result['search_type'] = 'semantic'
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return []
    
    async def _lexical_search(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Perform lexical search using BM25"""
        try:
            # Initialize BM25 if not already done
            if self.bm25_index is None:
                await self._initialize_bm25_index()
            
            # Tokenize query
            query_tokens = self._tokenize_text(query)
            
            # Get BM25 scores
            bm25_scores = self.bm25_index.get_scores(query_tokens)
            
            # Convert to results format
            results = []
            for i, score in enumerate(bm25_scores):
                if score > 0 and i < len(self.document_corpus):
                    chunk_id = self.document_corpus[i].get('chunk_id')
                    if chunk_id:
                        result = {
                            'chunk_id': chunk_id,
                            'score': float(score),
                            'lexical_score': float(score),
                            'content': self.document_corpus[i].get('content', ''),
                            'metadata': self.document_corpus[i].get('metadata', {}),
                            'search_type': 'lexical'
                        }
                        results.append(result)
            
            # Sort by score and take top k
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:RETRIEVAL_CONFIG['k']]
            
            return results
            
        except Exception as e:
            logger.error(f"Error in lexical search: {str(e)}")
            return []
    
    async def _initialize_bm25_index(self):
        """Initialize BM25 index from document corpus"""
        try:
            # Get all documents from embedding service
            # This is a simplified approach - in production, you'd want to
            # maintain a separate index for BM25
            
            # For now, we'll create a dummy corpus
            # In a real implementation, you'd load this from the database
            self.document_corpus = []
            
            # Get document texts for BM25 indexing
            tokenized_corpus = []
            for doc in self.document_corpus:
                tokens = self._tokenize_text(doc.get('content', ''))
                tokenized_corpus.append(tokens)
            
            if tokenized_corpus:
                self.bm25_index = BM25Okapi(tokenized_corpus)
                logger.info(f"Initialized BM25 index with {len(tokenized_corpus)} documents")
            else:
                logger.warning("No documents available for BM25 indexing")
                
        except Exception as e:
            logger.error(f"Error initializing BM25 index: {str(e)}")
            raise
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25 indexing"""
        # Simple tokenization - can be enhanced
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        return [token for token in tokens if len(token) > 1]
    
    async def _hybrid_ranking(self, query: str, semantic_results: List[Dict[str, Any]], 
                            lexical_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Combine semantic and lexical results with hybrid scoring
        """
        try:
            # Create a combined results dict
            combined_results = {}
            
            # Add semantic results
            for result in semantic_results:
                chunk_id = result['chunk_id']
                combined_results[chunk_id] = result.copy()
                combined_results[chunk_id]['semantic_score'] = result.get('semantic_score', 0.0)
                combined_results[chunk_id]['lexical_score'] = 0.0
            
            # Add lexical results
            for result in lexical_results:
                chunk_id = result['chunk_id']
                if chunk_id in combined_results:
                    combined_results[chunk_id]['lexical_score'] = result.get('lexical_score', 0.0)
                else:
                    combined_results[chunk_id] = result.copy()
                    combined_results[chunk_id]['semantic_score'] = 0.0
                    combined_results[chunk_id]['lexical_score'] = result.get('lexical_score', 0.0)
            
            # Apply hybrid scoring
            hybrid_results = []
            for chunk_id, result in combined_results.items():
                # Get enhanced scores
                enhanced_scores = await self._calculate_enhanced_scores(query, result)
                
                # Calculate final hybrid score
                final_score = self._calculate_hybrid_score(result, enhanced_scores)
                
                result.update({
                    'hybrid_score': final_score,
                    'enhanced_scores': enhanced_scores,
                    'final_score': final_score
                })
                
                hybrid_results.append(result)
            
            # Sort by hybrid score
            hybrid_results.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            return hybrid_results
            
        except Exception as e:
            logger.error(f"Error in hybrid ranking: {str(e)}")
            return []
    
    async def _calculate_enhanced_scores(self, query: str, result: Dict[str, Any]) -> Dict[str, float]:
        """Calculate enhanced scores for better ranking"""
        try:
            scores = {}
            
            # 1. Lexical overlap score
            scores['lexical_overlap'] = self._calculate_lexical_overlap(query, result['content'])
            
            # 2. Content type boost
            scores['content_type_boost'] = self._calculate_content_type_boost(query, result)
            
            # 3. Length normalization
            scores['length_normalization'] = self._calculate_length_normalization(result)
            
            # 4. Position score (if available)
            scores['position_score'] = self._calculate_position_score(result)
            
            # 5. Freshness score (if available)
            scores['freshness_score'] = self._calculate_freshness_score(result)
            
            return scores
            
        except Exception as e:
            logger.error(f"Error calculating enhanced scores: {str(e)}")
            return {}
    
    def _calculate_lexical_overlap(self, query: str, content: str) -> float:
        """Calculate lexical overlap between query and content"""
        try:
            query_tokens = set(self._tokenize_text(query))
            content_tokens = set(self._tokenize_text(content))
            
            if not query_tokens or not content_tokens:
                return 0.0
            
            overlap = len(query_tokens.intersection(content_tokens))
            return overlap / len(query_tokens)
            
        except Exception as e:
            logger.error(f"Error calculating lexical overlap: {str(e)}")
            return 0.0
    
    def _calculate_content_type_boost(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate content type boost based on query characteristics"""
        try:
            content_type = result.get('metadata', {}).get('content_type', 'text')
            
            # Check if query contains numeric keywords (boost tables)
            numeric_keywords = ['number', 'count', 'amount', 'total', 'sum', 'average', 'data']
            has_numeric = any(keyword in query.lower() for keyword in numeric_keywords)
            
            if content_type == 'table' and has_numeric:
                return RETRIEVAL_CONFIG['table_boost']
            elif content_type == 'image':
                # Check if query is about visual content
                visual_keywords = ['image', 'figure', 'diagram', 'chart', 'graph']
                has_visual = any(keyword in query.lower() for keyword in visual_keywords)
                if has_visual:
                    return 1.1
            
            return 1.0
            
        except Exception as e:
            logger.error(f"Error calculating content type boost: {str(e)}")
            return 1.0
    
    def _calculate_length_normalization(self, result: Dict[str, Any]) -> float:
        """Calculate length normalization score"""
        try:
            word_count = result.get('metadata', {}).get('word_count', 0)
            
            # Prefer chunks with moderate length
            if word_count < 20:
                return 0.7  # Too short
            elif word_count > 300:
                return 0.8  # Too long
            else:
                return 1.0  # Good length
                
        except Exception as e:
            logger.error(f"Error calculating length normalization: {str(e)}")
            return 1.0
    
    def _calculate_position_score(self, result: Dict[str, Any]) -> float:
        """Calculate position score (prefer earlier content)"""
        try:
            page_number = result.get('metadata', {}).get('page_number', 1)
            
            # Give slight boost to earlier pages
            if page_number <= 3:
                return 1.1
            elif page_number <= 10:
                return 1.0
            else:
                return 0.9
                
        except Exception as e:
            logger.error(f"Error calculating position score: {str(e)}")
            return 1.0
    
    def _calculate_freshness_score(self, result: Dict[str, Any]) -> float:
        """Calculate freshness score (if temporal information available)"""
        # This is a placeholder - in a real system, you might have
        # document creation dates or modification dates
        return 1.0
    
    def _calculate_hybrid_score(self, result: Dict[str, Any], enhanced_scores: Dict[str, float]) -> float:
        """Calculate final hybrid score"""
        try:
            # Base scores
            semantic_score = result.get('semantic_score', 0.0)
            lexical_score = result.get('lexical_score', 0.0)
            
            # Normalize scores to [0, 1] range
            semantic_score = max(0, min(1, semantic_score))
            lexical_score = max(0, min(1, lexical_score / 10.0))  # BM25 can have high values
            
            # Weighted combination
            base_score = (
                RETRIEVAL_CONFIG['semantic_weight'] * semantic_score +
                RETRIEVAL_CONFIG['lexical_weight'] * lexical_score
            )
            
            # Apply enhanced scores
            enhanced_score = base_score
            enhanced_score *= enhanced_scores.get('content_type_boost', 1.0)
            enhanced_score *= enhanced_scores.get('length_normalization', 1.0)
            enhanced_score *= enhanced_scores.get('position_score', 1.0)
            enhanced_score *= enhanced_scores.get('freshness_score', 1.0)
            
            # Add lexical overlap bonus
            enhanced_score += 0.1 * enhanced_scores.get('lexical_overlap', 0.0)
            
            return enhanced_score
            
        except Exception as e:
            logger.error(f"Error calculating hybrid score: {str(e)}")
            return 0.0
    
    async def _apply_final_filters(self, results: List[Dict[str, Any]], 
                                 filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Apply final filters and limits"""
        try:
            # Apply similarity threshold
            threshold = RETRIEVAL_CONFIG['similarity_threshold']
            filtered_results = [
                result for result in results 
                if result.get('hybrid_score', 0.0) >= threshold
            ]
            
            # Apply reranking limit
            rerank_k = RETRIEVAL_CONFIG['rerank_k']
            filtered_results = filtered_results[:rerank_k]
            
            # Apply content-specific filters
            if filters:
                if 'min_word_count' in filters:
                    min_words = filters['min_word_count']
                    filtered_results = [
                        result for result in filtered_results
                        if result.get('metadata', {}).get('word_count', 0) >= min_words
                    ]
                
                if 'content_types' in filters:
                    allowed_types = filters['content_types']
                    filtered_results = [
                        result for result in filtered_results
                        if result.get('metadata', {}).get('content_type') in allowed_types
                    ]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"Error applying final filters: {str(e)}")
            return results
    
    async def update_corpus(self, new_chunks: List[Dict[str, Any]]):
        """Update the document corpus for BM25 indexing"""
        try:
            # Add new chunks to corpus
            for chunk in new_chunks:
                self.document_corpus.append(chunk)
                self.chunk_metadata[chunk['chunk_id']] = chunk
            
            # Reinitialize BM25 index
            await self._initialize_bm25_index()
            
            logger.info(f"Updated corpus with {len(new_chunks)} new chunks")
            
        except Exception as e:
            logger.error(f"Error updating corpus: {str(e)}")
            raise
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics"""
        try:
            embedding_stats = await self.embedding_service.get_embedding_stats()
            
            return {
                'total_documents': len(self.document_corpus),
                'bm25_initialized': self.bm25_index is not None,
                'embedding_stats': embedding_stats,
                'retrieval_config': RETRIEVAL_CONFIG
            }
            
        except Exception as e:
            logger.error(f"Error getting retrieval stats: {str(e)}")
            return {}
    
    async def close(self):
        """Close connections and clean up resources"""
        try:
            await self.embedding_service.close()
            logger.info("Retrieval service closed")
            
        except Exception as e:
            logger.error(f"Error closing retrieval service: {str(e)}")


# Global retrieval service instance
retrieval_service = HybridRetrievalService() 
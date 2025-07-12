"""
Answer Generation Service with Ollama Integration
"""
import asyncio
import logging
import time
import json
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

from backend.core.config import settings, OLLAMA_CONFIG
from backend.services.retrieval_service import retrieval_service


logger = logging.getLogger(__name__)


class AnswerGenerationService:
    """Service for generating answers using Ollama LLM"""
    
    def __init__(self):
        self.retrieval_service = retrieval_service
        self.ollama_client = httpx.AsyncClient(
            base_url=OLLAMA_CONFIG['base_url'],
            timeout=OLLAMA_CONFIG['timeout']
        )
        self.model_name = OLLAMA_CONFIG['model']
        
    async def generate_answer(self, query: str, filters: Dict[str, Any] = None, 
                            user_id: str = None) -> Dict[str, Any]:
        """
        Generate answer for a given query
        
        Args:
            query: User query
            filters: Optional filters for retrieval
            user_id: User ID for context
            
        Returns:
            Dict containing answer, citations, and metadata
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating answer for query: {query[:50]}...")
            
            # Step 1: Retrieve relevant chunks
            retrieval_results = await self.retrieval_service.search_and_rank(
                query=query,
                filters=filters
            )
            
            if not retrieval_results['results']:
                return self._create_no_results_response(query)
            
            # Step 2: Prepare context and prompt
            context_data = self._prepare_context(retrieval_results['results'])
            prompt = self._create_prompt(query, context_data)
            
            # Step 3: Generate answer using Ollama
            generation_start = time.time()
            answer_response = await self._generate_with_ollama(prompt)
            generation_time = (time.time() - generation_start) * 1000
            
            # Step 4: Process and format response
            processed_answer = self._process_answer(answer_response, context_data)
            
            # Step 5: Create citations
            citations = self._create_citations(
                processed_answer, 
                retrieval_results['results']
            )
            
            total_time = (time.time() - start_time) * 1000
            
            # Create response
            response = {
                'answer': processed_answer['text'],
                'confidence': processed_answer['confidence'],
                'citations': citations,
                'metadata': {
                    'query': query,
                    'total_time_ms': total_time,
                    'generation_time_ms': generation_time,
                    'retrieval_time_ms': retrieval_results['metadata']['retrieval_time_ms'],
                    'chunks_used': len(retrieval_results['results']),
                    'model_used': self.model_name,
                    'timestamp': datetime.now().isoformat(),
                    'user_id': user_id
                }
            }
            
            logger.info(f"Answer generated in {total_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return self._create_error_response(query, str(e))
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare context data from retrieved chunks"""
        try:
            context_parts = []
            chunk_references = {}
            
            for i, chunk in enumerate(chunks):
                chunk_id = chunk['chunk_id']
                content = chunk['content']
                metadata = chunk.get('metadata', {})
                
                # Create reference ID
                ref_id = f"[{i+1}]"
                chunk_references[ref_id] = {
                    'chunk_id': chunk_id,
                    'content': content,
                    'content_type': metadata.get('content_type', 'text'),
                    'page_number': metadata.get('page_number', 1),
                    'score': chunk.get('hybrid_score', 0.0)
                }
                
                # Format content with reference
                formatted_content = f"{ref_id} {content}"
                context_parts.append(formatted_content)
            
            return {
                'context_text': '\n\n'.join(context_parts),
                'references': chunk_references,
                'total_chunks': len(chunks)
            }
            
        except Exception as e:
            logger.error(f"Error preparing context: {str(e)}")
            return {
                'context_text': '',
                'references': {},
                'total_chunks': 0
            }
    
    def _create_prompt(self, query: str, context_data: Dict[str, Any]) -> str:
        """Create structured prompt for the LLM"""
        try:
            prompt = f"""You are an expert assistant helping users find accurate information from documents. Your task is to provide a comprehensive, well-structured answer based on the provided context.

CONTEXT:
{context_data['context_text']}

USER QUERY: {query}

INSTRUCTIONS:
1. Provide a clear, concise answer based ONLY on the information provided in the context above
2. If you reference information from the context, include the reference number (e.g., [1], [2]) in your answer
3. If the context doesn't contain enough information to fully answer the query, clearly state this limitation
4. Structure your answer with clear paragraphs and logical flow
5. Be precise and avoid speculation beyond what's provided in the context
6. If you find conflicting information in the context, acknowledge this and present both perspectives

CONFIDENCE ASSESSMENT:
Rate your confidence in the answer on a scale of 0.0 to 1.0, where:
- 0.0-0.3: Low confidence (insufficient or unclear information)
- 0.4-0.6: Medium confidence (some relevant information but gaps remain)
- 0.7-0.9: High confidence (comprehensive information available)
- 1.0: Complete confidence (definitive answer with strong supporting evidence)

RESPONSE FORMAT:
Please structure your response as follows:

ANSWER:
[Your detailed answer here, including reference numbers where appropriate]

CONFIDENCE: [Your confidence score between 0.0 and 1.0]

LIMITATIONS:
[Any limitations or gaps in the available information, if applicable]"""

            return prompt
            
        except Exception as e:
            logger.error(f"Error creating prompt: {str(e)}")
            return f"Answer the following query based on the provided context: {query}"
    
    async def _generate_with_ollama(self, prompt: str) -> Dict[str, Any]:
        """Generate response using Ollama"""
        try:
            # Prepare request payload
            payload = {
                'model': self.model_name,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.1,  # Low temperature for more factual responses
                    'top_p': 0.9,
                    'max_tokens': 1000,
                    'stop': ['USER:', 'CONTEXT:']
                }
            }
            
            # Make request to Ollama
            response = await self.ollama_client.post('/api/generate', json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('response'):
                return {
                    'text': result['response'],
                    'success': True,
                    'model': self.model_name,
                    'total_duration': result.get('total_duration', 0),
                    'prompt_eval_count': result.get('prompt_eval_count', 0),
                    'eval_count': result.get('eval_count', 0)
                }
            else:
                logger.error(f"No response from Ollama: {result}")
                return {
                    'text': '',
                    'success': False,
                    'error': 'No response from model'
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from Ollama: {e}")
            return {
                'text': '',
                'success': False,
                'error': f'HTTP error: {e.response.status_code}'
            }
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            return {
                'text': '',
                'success': False,
                'error': str(e)
            }
    
    def _process_answer(self, answer_response: Dict[str, Any], 
                       context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure the generated answer"""
        try:
            if not answer_response.get('success'):
                return {
                    'text': f"I apologize, but I encountered an error while generating the answer: {answer_response.get('error', 'Unknown error')}",
                    'confidence': 0.0,
                    'limitations': 'Technical error prevented answer generation'
                }
            
            raw_text = answer_response.get('text', '')
            
            # Parse structured response
            answer_parts = self._parse_structured_response(raw_text)
            
            # Extract confidence if provided
            confidence = self._extract_confidence(answer_parts)
            
            # Clean and format the answer text
            answer_text = self._clean_answer_text(answer_parts.get('answer', raw_text))
            
            return {
                'text': answer_text,
                'confidence': confidence,
                'limitations': answer_parts.get('limitations', ''),
                'raw_response': raw_text
            }
            
        except Exception as e:
            logger.error(f"Error processing answer: {str(e)}")
            return {
                'text': answer_response.get('text', 'Error processing response'),
                'confidence': 0.0,
                'limitations': 'Error in response processing'
            }
    
    def _parse_structured_response(self, text: str) -> Dict[str, str]:
        """Parse structured response from LLM"""
        try:
            parts = {}
            current_section = None
            current_content = []
            
            lines = text.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('ANSWER:'):
                    if current_section:
                        parts[current_section] = '\n'.join(current_content).strip()
                    current_section = 'answer'
                    current_content = []
                elif line.startswith('CONFIDENCE:'):
                    if current_section:
                        parts[current_section] = '\n'.join(current_content).strip()
                    current_section = 'confidence'
                    current_content = [line.replace('CONFIDENCE:', '').strip()]
                elif line.startswith('LIMITATIONS:'):
                    if current_section:
                        parts[current_section] = '\n'.join(current_content).strip()
                    current_section = 'limitations'
                    current_content = []
                elif current_section:
                    current_content.append(line)
            
            # Add final section
            if current_section:
                parts[current_section] = '\n'.join(current_content).strip()
            
            return parts
            
        except Exception as e:
            logger.error(f"Error parsing structured response: {str(e)}")
            return {'answer': text}
    
    def _extract_confidence(self, answer_parts: Dict[str, str]) -> float:
        """Extract confidence score from answer"""
        try:
            confidence_text = answer_parts.get('confidence', '')
            
            # Try to extract numeric confidence
            import re
            confidence_match = re.search(r'(\d+\.?\d*)', confidence_text)
            
            if confidence_match:
                confidence = float(confidence_match.group(1))
                
                # Normalize to 0-1 range if needed
                if confidence > 1.0:
                    confidence = confidence / 100.0
                
                return max(0.0, min(1.0, confidence))
            
            # Fallback: estimate confidence based on answer quality
            answer_text = answer_parts.get('answer', '')
            
            if 'insufficient information' in answer_text.lower() or 'cannot answer' in answer_text.lower():
                return 0.2
            elif 'limited information' in answer_text.lower():
                return 0.4
            elif 'based on the provided context' in answer_text.lower():
                return 0.7
            else:
                return 0.6
                
        except Exception as e:
            logger.error(f"Error extracting confidence: {str(e)}")
            return 0.5
    
    def _clean_answer_text(self, text: str) -> str:
        """Clean and format answer text"""
        try:
            # Remove extra whitespace
            text = ' '.join(text.split())
            
            # Remove any remaining section headers
            text = text.replace('ANSWER:', '').replace('CONFIDENCE:', '').replace('LIMITATIONS:', '')
            
            # Clean up formatting
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning answer text: {str(e)}")
            return text
    
    def _create_citations(self, processed_answer: Dict[str, Any], 
                         chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create citations from referenced chunks"""
        try:
            citations = []
            answer_text = processed_answer.get('text', '')
            
            # Find reference patterns in the answer
            import re
            references = re.findall(r'\[(\d+)\]', answer_text)
            
            # Create citations for referenced chunks
            for ref_num in references:
                try:
                    chunk_index = int(ref_num) - 1
                    if 0 <= chunk_index < len(chunks):
                        chunk = chunks[chunk_index]
                        metadata = chunk.get('metadata', {})
                        
                        citation = {
                            'reference_id': ref_num,
                            'chunk_id': chunk['chunk_id'],
                            'content': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                            'content_type': metadata.get('content_type', 'text'),
                            'page_number': metadata.get('page_number', 1),
                            'score': chunk.get('hybrid_score', 0.0),
                            'source': {
                                'type': metadata.get('content_type', 'text'),
                                'page': metadata.get('page_number', 1),
                                'confidence': metadata.get('ocr_confidence') if metadata.get('content_type') == 'image' else None
                            }
                        }
                        
                        citations.append(citation)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Invalid reference number {ref_num}: {str(e)}")
                    continue
            
            # If no references found, create citations for top chunks
            if not citations and chunks:
                for i, chunk in enumerate(chunks[:3]):  # Top 3 chunks
                    metadata = chunk.get('metadata', {})
                    citation = {
                        'reference_id': str(i + 1),
                        'chunk_id': chunk['chunk_id'],
                        'content': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content'],
                        'content_type': metadata.get('content_type', 'text'),
                        'page_number': metadata.get('page_number', 1),
                        'score': chunk.get('hybrid_score', 0.0),
                        'source': {
                            'type': metadata.get('content_type', 'text'),
                            'page': metadata.get('page_number', 1),
                            'confidence': metadata.get('ocr_confidence') if metadata.get('content_type') == 'image' else None
                        }
                    }
                    citations.append(citation)
            
            return citations
            
        except Exception as e:
            logger.error(f"Error creating citations: {str(e)}")
            return []
    
    def _create_no_results_response(self, query: str) -> Dict[str, Any]:
        """Create response when no relevant results found"""
        return {
            'answer': "I apologize, but I couldn't find relevant information in the available documents to answer your query. Please try rephrasing your question or check if the topic is covered in the uploaded documents.",
            'confidence': 0.0,
            'citations': [],
            'metadata': {
                'query': query,
                'total_time_ms': 0,
                'generation_time_ms': 0,
                'retrieval_time_ms': 0,
                'chunks_used': 0,
                'model_used': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'error': 'No relevant results found'
            }
        }
    
    def _create_error_response(self, query: str, error_msg: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'answer': "I apologize, but I encountered an error while processing your query. Please try again or contact support if the issue persists.",
            'confidence': 0.0,
            'citations': [],
            'metadata': {
                'query': query,
                'total_time_ms': 0,
                'generation_time_ms': 0,
                'retrieval_time_ms': 0,
                'chunks_used': 0,
                'model_used': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'error': error_msg
            }
        }
    
    async def check_ollama_health(self) -> Dict[str, Any]:
        """Check Ollama service health"""
        try:
            response = await self.ollama_client.get('/api/tags')
            response.raise_for_status()
            
            models = response.json()
            
            return {
                'status': 'healthy',
                'available_models': [model['name'] for model in models.get('models', [])],
                'current_model': self.model_name,
                'base_url': OLLAMA_CONFIG['base_url']
            }
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'base_url': OLLAMA_CONFIG['base_url']
            }
    
    async def close(self):
        """Close connections and clean up resources"""
        try:
            await self.ollama_client.aclose()
            await self.retrieval_service.close()
            logger.info("Answer generation service closed")
            
        except Exception as e:
            logger.error(f"Error closing answer generation service: {str(e)}")


# Global answer generation service instance
answer_generation_service = AnswerGenerationService() 
"""
PDF Ingestion Service for Multimodal Document Processing
"""
import os
import uuid
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# PDF processing imports
import PyPDF2
import pdfplumber
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import pymupdf as fitz
        PYMUPDF_AVAILABLE = True
    except ImportError:
        PYMUPDF_AVAILABLE = False
        logger.warning("PyMuPDF not available for image extraction")

from PIL import Image
import pandas as pd

# OCR imports
import pytesseract
import easyocr
import cv2
import numpy as np

from backend.core.config import settings
from backend.models.document import Document, DocumentChunk

# Table extraction imports
import tabula
# Make camelot import optional due to version compatibility issues
try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False
    logger.warning("Camelot not available for table extraction. Using tabula and pdfplumber only.")

# Text processing
import re
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer


class PDFIngestionService:
    """Service for ingesting and processing PDF documents"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_directory)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OCR engines
        self.easyocr_reader = easyocr.Reader(['en'])
        
        # Initialize text processing
        self.tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
        
        # Thread pool for CPU-intensive tasks
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_pdf(self, file_path: str, filename: str, user_id: str = None) -> Dict[str, Any]:
        """
        Process a PDF file and extract multimodal content
        
        Args:
            file_path: Path to the PDF file
            filename: Original filename
            user_id: User ID for multi-tenancy
            
        Returns:
            Dict containing processing results and metadata
        """
        try:
            logger.info(f"Starting PDF processing for {filename}")
            
            # Extract basic metadata
            metadata = await self._extract_metadata(file_path)
            
            # Process document content
            content_data = await self._extract_content(file_path)
            
            # Create document chunks
            chunks = await self._create_chunks(content_data, metadata)
            
            # Generate processing summary
            summary = {
                'filename': filename,
                'total_pages': metadata.get('total_pages', 0),
                'total_chunks': len(chunks),
                'total_images': sum(1 for chunk in chunks if chunk['content_type'] == 'image'),
                'total_tables': sum(1 for chunk in chunks if chunk['content_type'] == 'table'),
                'processing_time': datetime.now().isoformat(),
                'chunks': chunks
            }
            
            logger.info(f"PDF processing completed for {filename}")
            return summary
            
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}")
            raise
    
    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata or {}
                
                return {
                    'total_pages': len(pdf_reader.pages),
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'producer': metadata.get('/Producer', ''),
                    'creation_date': metadata.get('/CreationDate', ''),
                    'modification_date': metadata.get('/ModDate', '')
                }
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {'total_pages': 0}
    
    async def _extract_content(self, file_path: str) -> Dict[str, Any]:
        """Extract multimodal content from PDF"""
        content_data = {
            'text_chunks': [],
            'table_chunks': [],
            'image_chunks': []
        }
        
        # Use asyncio to run CPU-intensive tasks in thread pool
        loop = asyncio.get_event_loop()
        
        # Extract text content
        text_chunks = await loop.run_in_executor(
            self.executor, self._extract_text_content, file_path
        )
        content_data['text_chunks'] = text_chunks
        
        # Extract table content
        table_chunks = await loop.run_in_executor(
            self.executor, self._extract_table_content, file_path
        )
        content_data['table_chunks'] = table_chunks
        
        # Extract image content
        image_chunks = await loop.run_in_executor(
            self.executor, self._extract_image_content, file_path
        )
        content_data['image_chunks'] = image_chunks
        
        return content_data
    
    def _extract_text_content(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract structured text content with hierarchy"""
        text_chunks = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text with formatting
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # Split text into paragraphs and detect headings
                    paragraphs = self._split_into_paragraphs(text)
                    
                    for para_idx, paragraph in enumerate(paragraphs):
                        if len(paragraph.strip()) < 20:  # Skip very short paragraphs
                            continue
                        
                        # Detect heading level
                        heading_level = self._detect_heading_level(paragraph)
                        
                        chunk = {
                            'content': paragraph,
                            'content_type': 'text',
                            'page_number': page_num,
                            'sequence_number': para_idx,
                            'heading_level': heading_level,
                            'word_count': len(paragraph.split()),
                            'char_count': len(paragraph),
                            'bbox': None  # Could extract bounding boxes if needed
                        }
                        
                        text_chunks.append(chunk)
                        
        except Exception as e:
            logger.error(f"Error extracting text content: {str(e)}")
        
        return text_chunks
    
    def _extract_table_content(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract and structure table content"""
        table_chunks = []
        
        # First try pdfplumber for table extraction (more reliable)
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table or len(table) < 2:  # Skip empty or single-row tables
                            continue
                        
                        # Convert table to DataFrame
                        table_df = pd.DataFrame(table[1:], columns=table[0])
                        
                        # Create readable text representation
                        table_text = self._table_to_text(table_df)
                        
                        chunk = {
                            'content': table_text,
                            'content_type': 'table',
                            'page_number': page_num,
                            'sequence_number': table_idx,
                            'table_metadata': {
                                'headers': table_df.columns.tolist(),
                                'rows': len(table_df),
                                'columns': len(table_df.columns),
                                'structured_data': table_df.to_dict('records'),
                                'extraction_method': 'pdfplumber'
                            },
                            'word_count': len(table_text.split()),
                            'char_count': len(table_text)
                        }
                        
                        table_chunks.append(chunk)
                        
        except Exception as e:
            logger.error(f"Error extracting tables with pdfplumber: {str(e)}")
        
        # Fallback to tabula-py if pdfplumber didn't find tables
        if not table_chunks:
            try:
                # Use tabula-py for table extraction
                tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                
                for table_idx, table in enumerate(tables):
                    if table.empty:
                        continue
                    
                    # Convert table to structured format
                    table_dict = table.to_dict('records')
                    
                    # Create readable text representation
                    table_text = self._table_to_text(table)
                    
                    chunk = {
                        'content': table_text,
                        'content_type': 'table',
                        'page_number': 1,  # tabula doesn't provide page info easily
                        'sequence_number': table_idx,
                        'table_metadata': {
                            'headers': table.columns.tolist(),
                            'rows': len(table),
                            'columns': len(table.columns),
                            'structured_data': table_dict,
                            'extraction_method': 'tabula'
                        },
                        'word_count': len(table_text.split()),
                        'char_count': len(table_text)
                    }
                    
                    table_chunks.append(chunk)
                    
            except Exception as e:
                logger.error(f"Error extracting table content with tabula: {str(e)}")
                
                # Final fallback to camelot for table extraction if available
                if CAMELOT_AVAILABLE:
                    try:
                        tables = camelot.read_pdf(file_path, pages='all')
                        
                        for table_idx, table in enumerate(tables):
                            table_df = table.df
                            if table_df.empty:
                                continue
                            
                            table_text = self._table_to_text(table_df)
                            
                            chunk = {
                                'content': table_text,
                                'content_type': 'table',
                                'page_number': table.page,
                                'sequence_number': table_idx,
                                'table_metadata': {
                                    'headers': table_df.columns.tolist(),
                                    'rows': len(table_df),
                                    'columns': len(table_df.columns),
                                    'structured_data': table_df.to_dict('records'),
                                    'accuracy': table.accuracy,
                                    'extraction_method': 'camelot'
                                },
                                'word_count': len(table_text.split()),
                                'char_count': len(table_text)
                            }
                            
                            table_chunks.append(chunk)
                            
                    except Exception as e2:
                        logger.error(f"Error with camelot table extraction: {str(e2)}")
        
        return table_chunks
    
    def _extract_image_content(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract and process images with OCR"""
        image_chunks = []
        
        if not PYMUPDF_AVAILABLE:
            logger.warning("PyMuPDF not available, skipping image extraction")
            return image_chunks
        
        try:
            pdf_document = fitz.open(file_path)
            
            for page_num, page in enumerate(pdf_document, 1):
                image_list = page.get_images()
                
                for img_index, img in enumerate(image_list):
                    # Extract image
                    xref = img[0]
                    pix = fitz.Pixmap(pdf_document, xref)
                    
                    if pix.n - pix.alpha < 4:  # Skip non-RGB images
                        img_data = pix.tobytes("png")
                        
                        # Convert to PIL Image
                        img_pil = Image.open(io.BytesIO(img_data))
                        
                        # Perform OCR
                        ocr_results = self._perform_ocr(img_pil)
                        
                        if ocr_results['text'].strip():
                            chunk = {
                                'content': ocr_results['text'],
                                'content_type': 'image',
                                'page_number': page_num,
                                'sequence_number': img_index,
                                'image_metadata': {
                                    'width': pix.width,
                                    'height': pix.height,
                                    'format': 'png',
                                    'ocr_confidence': ocr_results['confidence'],
                                    'ocr_engine': ocr_results['engine']
                                },
                                'word_count': len(ocr_results['text'].split()),
                                'char_count': len(ocr_results['text'])
                            }
                            
                            image_chunks.append(chunk)
                    
                    pix = None
            
            pdf_document.close()
            
        except Exception as e:
            logger.error(f"Error extracting image content: {str(e)}")
        
        return image_chunks
    
    def _perform_ocr(self, image: Image.Image) -> Dict[str, Any]:
        """Perform OCR on image using multiple engines"""
        try:
            # Try EasyOCR first
            img_array = np.array(image)
            easyocr_results = self.easyocr_reader.readtext(img_array)
            
            if easyocr_results:
                text = ' '.join([result[1] for result in easyocr_results])
                confidence = np.mean([result[2] for result in easyocr_results])
                
                return {
                    'text': text,
                    'confidence': confidence,
                    'engine': 'easyocr'
                }
        except Exception as e:
            logger.error(f"EasyOCR failed: {str(e)}")
        
        try:
            # Fallback to Tesseract
            text = pytesseract.image_to_string(image)
            confidence = 0.8  # Default confidence for tesseract
            
            return {
                'text': text,
                'confidence': confidence,
                'engine': 'tesseract'
            }
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {str(e)}")
            return {
                'text': '',
                'confidence': 0.0,
                'engine': 'none'
            }
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs while preserving structure"""
        # Split by double newlines first
        paragraphs = text.split('\n\n')
        
        # Further split by single newlines if paragraphs are too long
        refined_paragraphs = []
        for para in paragraphs:
            if len(para) > settings.chunk_size * 2:
                # Split long paragraphs by sentences
                sentences = re.split(r'[.!?]+', para)
                current_chunk = ""
                
                for sentence in sentences:
                    if len(current_chunk + sentence) < settings.chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            refined_paragraphs.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    refined_paragraphs.append(current_chunk.strip())
            else:
                refined_paragraphs.append(para)
        
        return [p.strip() for p in refined_paragraphs if p.strip()]
    
    def _detect_heading_level(self, text: str) -> Optional[int]:
        """Detect heading level based on text patterns"""
        # Simple heuristic for heading detection
        if re.match(r'^\d+\.?\s+[A-Z]', text):  # "1. TITLE" or "1 TITLE"
            return 1
        elif re.match(r'^\d+\.\d+\.?\s+[A-Z]', text):  # "1.1. TITLE"
            return 2
        elif re.match(r'^\d+\.\d+\.\d+\.?\s+[A-Z]', text):  # "1.1.1. TITLE"
            return 3
        elif text.isupper() and len(text) < 100:  # Short uppercase text
            return 1
        elif text.istitle() and len(text) < 100:  # Title case short text
            return 2
        
        return None
    
    def _table_to_text(self, table: pd.DataFrame) -> str:
        """Convert DataFrame to readable text"""
        # Create a text representation of the table
        text_parts = []
        
        # Add headers
        headers = " | ".join(str(col) for col in table.columns)
        text_parts.append(f"Table Headers: {headers}")
        
        # Add rows
        for idx, row in table.iterrows():
            row_text = " | ".join(str(val) for val in row.values)
            text_parts.append(f"Row {idx + 1}: {row_text}")
        
        return "\n".join(text_parts)
    
    async def _create_chunks(self, content_data: Dict[str, Any], metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create final document chunks with metadata"""
        all_chunks = []
        
        # Process text chunks
        for chunk in content_data['text_chunks']:
            chunk_id = str(uuid.uuid4())
            chunk['chunk_id'] = chunk_id
            chunk['cleaned_content'] = self._clean_text_for_embedding(chunk['content'])
            all_chunks.append(chunk)
        
        # Process table chunks
        for chunk in content_data['table_chunks']:
            chunk_id = str(uuid.uuid4())
            chunk['chunk_id'] = chunk_id
            chunk['cleaned_content'] = self._clean_text_for_embedding(chunk['content'])
            all_chunks.append(chunk)
        
        # Process image chunks
        for chunk in content_data['image_chunks']:
            chunk_id = str(uuid.uuid4())
            chunk['chunk_id'] = chunk_id
            chunk['cleaned_content'] = self._clean_text_for_embedding(chunk['content'])
            all_chunks.append(chunk)
        
        return all_chunks
    
    def _clean_text_for_embedding(self, text: str) -> str:
        """Clean text for embedding generation"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        # Remove very short words (less than 2 characters)
        words = text.split()
        words = [word for word in words if len(word) >= 2 or word in '.,!?;:-']
        
        return ' '.join(words).strip()


# Import for image processing
import io
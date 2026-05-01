"""
File Parser Agent for parsing complex documents, images, and multimedia files
Uses Pydantic AI with vision capabilities for intelligent document extraction
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent, DocumentUrl, ImageUrl
import asyncio
import logging

from model import select_model
from configs.config import config

logger = logging.getLogger(__name__)


class DocumentAnalysis(BaseModel, extra="allow"):
    """Output model for document analysis"""
    document_type: str
    description: str
    extracted_text: str


class FileParserAgent:
    """
    AI agent for parsing and analyzing medical documents, images, and audio files
    Uses vision models for image and complex document parsing
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize File Parser Agent
        
        Args:
            model_name: Model name (defaults to vision-capable model)
            api_key: API key
            provider: "google" or "openai"
        """
        
        # Use vision-capable model
        model_name = model_name or "gemini-2.5-flash-lite"
        model, _ = select_model(model_name, api_key or config.GOOGLE_API_KEY)
        
        self.system_prompt = """
        You are a document parsing specialist for medical/healthcare/clinical education. Your role is to:
        
        1. Parse and extract information from documents including images, PDFs, and presentations
        2. Extract all text content accurately, preserving structure and context
        3. Identify key medical concepts, findings, and information
        4. For images: Describe visual content, extract text from images (OCR), identify and describe medical diagrams/charts
        5. For complex documents: Extract text from all pages/slides, handle tables and structured data
        6. Provide confidence scores for extraction quality
        
        Be thorough and accurate. Preserve medical terminology and context.
        """
        
        self.agent = Agent(
            model,
            system_prompt=self.system_prompt,
            output_type=DocumentAnalysis
        )
    
    async def parse_document_from_url(
        self, 
        user_id: str, 
        document_url: str
    ) -> Optional[DocumentAnalysis]:
        """
        Parse document from URL using Pydantic AI
        
        Args:
            user_id: User ID (for logging)
            document_url: URL of the document
            
        Returns:
            DocumentAnalysis object or None if failed
        """
        try:
            # Determine content type from URL
            if document_url.lower().endswith(('.pdf', '.doc', '.docx')):
                # Handle document files
                result = await self.agent.run([
                    'Analyze this document and extract all text content, key information, and structure.',
                    DocumentUrl(url=document_url),
                ])
            elif document_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                # Handle image files
                result = await self.agent.run([
                    'Analyze this image. Extract all visible text (OCR), describe visual content, '
                    'identify medical diagrams, charts, or relevant information.',
                    ImageUrl(url=document_url),
                ])
            else:
                # Try as generic document
                result = await self.agent.run([
                    'Analyze this document content and Extract all visible text (OCR), describe visual content, '
                    'identify medical diagrams, charts, or relevant information.',
                    DocumentUrl(url=document_url),
                ])
            
            return result.output
            
        except Exception as e:
            logger.error(f"Error parsing document from URL {document_url}: {e}")
            return None
    
    async def parse_binary_content(
        self, 
        content_data: bytes, 
        media_type: str,
        filename: str, 
        content_hint: str = ""
    ) -> DocumentAnalysis:
        """
        Parse binary content using Pydantic AI with parallel processing for multiple pages/images
        
        Args:
            content_data: Binary file content
            media_type: MIME type
            filename: File name
            content_hint: Optional context hint
            
        Returns:
            DocumentAnalysis object
        """
        try:
            # For images, use vision model directly
            if media_type.startswith("image/"):
                result = await self.agent.run([
                    f'Analyze this medical image. Extract all text (OCR), describe visual content, '
                    f'identify medical diagrams, charts, findings. Context: {content_hint}',
                    BinaryContent(data=content_data, media_type=media_type),
                ])
                
                result = result.output
                return result
            
            # For documents, parse with context
            result = await self.agent.run([
                f'Analyze this document content. Extract all text, preserve structure, describe visual content, graphs and tables concisely, '
                f'identify key medical concepts and findings. Context: {content_hint}',
                BinaryContent(data=content_data, media_type=media_type),
            ])
            
            result = result.output
            
            return result
                
        except Exception as e:
            logger.error(f"Error parsing binary content {filename}: {e}")
            return DocumentAnalysis(
                document_type=media_type,
                description="Error processing file",
                extracted_text=f"Error processing file: {str(e)}. Please try reuploading.",
            )
    
    async def parse_multiple_files_parallel(
        self,
        files: List[Dict[str, Any]]
    ) -> List[DocumentAnalysis]:
        """
        Parse multiple files in parallel for efficiency

        Args:
            files: List of dicts with 'content', 'media_type', 'filename', 'hint'
            
        Returns:
            List of DocumentAnalysis objects
        """
        tasks = [
            self.parse_binary_content(
                content_data=file['content'],
                media_type=file['media_type'],
                filename=file['filename'],
                content_hint=file.get('hint', '')
            )
            for file in files
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        parsed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error parsing file {files[i]['filename']}: {result}")
                parsed_results.append(DocumentAnalysis(
                    document_type=files[i]['media_type'],
                    description="Error processing file",
                    extracted_text=f"Error: {str(result)}",
                ))
            else:
                parsed_results.append(result)
        
        return parsed_results


# Global instance
_file_parser_agent: Optional[FileParserAgent] = None


def get_file_parser_agent(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    provider: str = "google"
) -> FileParserAgent:
    """Get or create global File Parser Agent instance"""
    global _file_parser_agent
    if _file_parser_agent is None:
        _file_parser_agent = FileParserAgent(model_name, api_key, provider)
    return _file_parser_agent

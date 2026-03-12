"""
Document Processing Service with RAG using Pinecone
Handles document upload, chunking, embedding, and vector storage
"""
import os
import uuid
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from pinecone import PineconeAsyncio, ServerlessSpec
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic import BaseModel

import PyPDF2
from docx import Document as DocxDocument
from io import BytesIO

from config import config
from supabase import create_client, Client


class DocumentChunk(BaseModel):
    """Represents a chunk of a document"""
    chunk_index: int
    content: str
    metadata: Dict[str, Any]


class DocumentProcessor:
    """
    Handles document processing, chunking, embedding, and RAG operations
    """
    
    def __init__(self):
        """Initialize document processor with Pinecone and OpenAI clients"""
        # Initialize Pinecone
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY environment variable is required")
        
        self.pinecone = PineconeAsyncio(api_key=self.pinecone_api_key)
        
        # Initialize OpenAI for embeddings
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or config.OPENAI_API_KEY
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Initialize Gemini for embeddings (fallback)
        self.gemini_api_key = config.GOOGLE_API_KEY
        self.gemini_model = GeminiModel(
            "gemini-2.5-flash-preview-05-20",
            provider=GoogleGLAProvider(api_key=self.gemini_api_key)
        ) if self.gemini_api_key else None
        
        # Initialize Supabase
        self.supabase: Client = create_client(
            config.SUPABASE_URL,
            config.SUPABASE_SERVICE_ROLE_KEY
        )
        
        # Default expiration time (2 hours for temporary storage)
        self.default_expiration_hours = int(os.getenv("PINECONE_INDEX_EXPIRATION_HOURS", "2"))
        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small dimension
    
    async def process_document(
        self,
        file_content: bytes,
        file_name: str,
        file_type: str,
        user_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded document: extract text, chunk, embed, and store in Pinecone.
        
        Args:
            file_content: Raw file bytes
            file_name: Original file name
            file_type: MIME type of the file
            user_id: ID of the user uploading the document
            document_id: Optional document ID (generated if not provided)
            
        Returns:
            Dictionary with processing results
        """
        document_id = document_id or str(uuid.uuid4())
        
        # Extract text from document
        text_content = await self._extract_text(file_content, file_type)
        
        if not text_content:
            raise ValueError(f"Could not extract text from {file_type} file")
        
        # Chunk the document
        chunks = self._chunk_document(text_content, chunk_size=1000, overlap=200)
        
        # Create Pinecone index for this document
        index_name = f"doc-{document_id}-{int(datetime.now().timestamp())}"
        await self._create_pinecone_index(index_name)
        
        # Generate embeddings and upsert to Pinecone
        vectors = []
        for i, chunk in enumerate(chunks):
            embedding = await self._generate_embedding(chunk.content)
            vectors.append({
                "id": f"{document_id}-chunk-{i}",
                "values": embedding,
                "metadata": {
                    "document_id": document_id,
                    "chunk_index": i,
                    "content": chunk.content[:500],  # Store preview
                    "file_name": file_name
                }
            })
        
        # Upsert vectors in batches
        index = await self.pinecone.get_index(index_name)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            await index.upsert(vectors=batch)
        
        # Calculate expiration time
        expires_at = datetime.now() + timedelta(hours=self.default_expiration_hours)
        
        # Save document metadata to Supabase
        self.supabase.table("documents").insert({
            "id": document_id,
            "user_id": user_id,
            "name": file_name,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": len(file_content),
            "content": text_content[:10000],  # Store first 10k chars for preview
            "processed": True,
            "processing_status": "completed",
            "pinecone_index_name": index_name,
            "pinecone_index_created_at": datetime.now().isoformat(),
            "pinecone_index_expires_at": expires_at.isoformat(),
            "chunk_count": len(chunks),
            "uploaded_at": datetime.now().isoformat(),
            "processed_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "document_id": document_id,
            "index_name": index_name,
            "chunk_count": len(chunks),
            "expires_at": expires_at.isoformat(),
            "status": "processed"
        }
    
    async def _extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from various file types"""
        if file_type == "application/pdf":
            return self._extract_pdf_text(file_content)
        elif file_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
            return self._extract_docx_text(file_content)
        elif file_type == "text/plain":
            return file_content.decode('utf-8', errors='ignore')
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def _extract_pdf_text(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            pdf_file = BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        except Exception as e:
            raise ValueError(f"Error extracting PDF text: {str(e)}")
        return text
    
    def _extract_docx_text(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            docx_file = BytesIO(file_content)
            doc = DocxDocument(docx_file)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            raise ValueError(f"Error extracting DOCX text: {str(e)}")
        return text
    
    def _chunk_document(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """Split document into overlapping chunks"""
        chunks = []
        words = text.split()
        
        i = 0
        chunk_index = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunks.append(DocumentChunk(
                chunk_index=chunk_index,
                content=chunk_text,
                metadata={"start_word": i, "end_word": min(i + chunk_size, len(words))}
            ))
            
            i += chunk_size - overlap
            chunk_index += 1
        
        return chunks
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI or Gemini"""
        if self.openai_client:
            try:
                response = await self.openai_client.embeddings.create(
                    input=text,
                    model="text-embedding-3-small"
                )
                return response.data[0].embedding
            except Exception:
                pass
        
        # Fallback to Gemini (if available)
        # Note: Gemini doesn't have a direct embedding API in pydantic-ai
        # You might need to use a different approach or library
        # For now, raise an error if OpenAI is not available
        raise ValueError("Embedding generation requires OpenAI API key")
    
    async def _create_pinecone_index(self, index_name: str):
        """Create a Pinecone index for document storage"""
        try:
            # Check if index exists
            if index_name in await self.pinecone.list_indexes():
                return
            
            # Create index
            await self.pinecone.create_index(
                name=index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=os.getenv("PINECONE_REGION", "us-east-1")
                ),
                deletion_protection="disabled"  # Allow deletion after expiration
            )
        except Exception as e:
            # Index might already exist or creation failed
            print(f"Index creation note: {str(e)}")
    
    async def search_documents(
        self,
        query: str,
        document_id: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search documents using RAG.
        
        Args:
            query: Search query
            document_id: Optional document ID to search within
            top_k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        # Generate query embedding
        query_embedding = await self._generate_embedding(query)
        
        # Get index name from document_id if provided
        if document_id:
            doc_result = self.supabase.table("documents").select("pinecone_index_name").eq("id", document_id).execute()
            if doc_result.data:
                index_name = doc_result.data[0]["pinecone_index_name"]
            else:
                raise ValueError(f"Document {document_id} not found")
        else:
            # Search across all user's documents (would need to implement multi-index search)
            raise ValueError("document_id is required for search")
        
        # Query Pinecone
        index = await self.pinecone.get_index(index_name)
        results = await index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"document_id": document_id} if document_id else None
        )
        
        return [
            {
                "content": match.metadata.get("content", ""),
                "chunk_index": match.metadata.get("chunk_index", 0),
                "score": match.score
            }
            for match in results.matches
        ]
    
    async def cleanup_expired_indexes(self):
        """Clean up expired Pinecone indexes"""
        # Get all documents with expired indexes
        expired_docs = self.supabase.table("documents").select("pinecone_index_name").lt(
            "pinecone_index_expires_at",
            datetime.now().isoformat()
        ).execute()
        
        for doc in expired_docs.data:
            index_name = doc.get("pinecone_index_name")
            if index_name:
                try:
                    await self.pinecone.delete_index(index_name)
                    # Update document record
                    self.supabase.table("documents").update({
                        "pinecone_index_name": None,
                        "pinecone_index_expires_at": None
                    }).eq("id", doc["id"]).execute()
                except Exception as e:
                    print(f"Error deleting index {index_name}: {str(e)}")


# Global instance
_document_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> DocumentProcessor:
    """Get or create global DocumentProcessor instance"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor


"""
RAG Agent for document-based question answering
Uses Pinecone for vector search and pydantic-ai for response generation
"""
from dataclasses import dataclass
from typing import List, Optional
from pydantic_ai import Agent, RunContext
from openai import AsyncOpenAI
import os

from config import config
from agents.base_agent import BaseAgent
from agents.agents import get_rag_model
from service.document_processor import get_document_processor
from models.states import RAGResponse


@dataclass
class RAGDependencies:
    """Dependencies for RAG agent"""
    openai_client: AsyncOpenAI
    document_processor: any  # DocumentProcessor instance
    document_id: str


class RAGAgent(BaseAgent):
    """
    RAG Agent for answering questions based on document content
    """
    
    def __init__(self, model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google"):
        """
        Initialize RAG agent
        
        Args:
            model_name: AI model name (defaults to config)
            api_key: API key (defaults to config)
            provider: "google" or "openai"
        """
        super().__init__(model_name, api_key, provider)
        
        # Initialize OpenAI for embeddings
        self.openai_api_key = config.OPENAI_API_KEY
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        
        # Initialize agent using the pattern from agents.py
        model = get_rag_model(model_name, api_key)
        self.agent = Agent(
            model,
            deps_type=RAGDependencies,
            system_prompt="""
            You are an AI tutor helping a medical student learn from their study materials.
            Use the retrieve tool to find relevant information from the uploaded document.
            Answer questions accurately based on the retrieved content, provide explanations,
            and help the student understand complex medical concepts.
            Be educational, clear, and encouraging. Always cite your sources.
            """,
            output_type=RAGResponse
        )
        
        # Register retrieval tool
        self._register_retrieve_tool()
    
    def _register_retrieve_tool(self):
        """Register the retrieve tool with the agent"""
        
        @self.agent.tool
        async def retrieve(context: RunContext[RAGDependencies], search_query: str) -> str:
            """
            Retrieve relevant documentation sections based on a search query.
            
            Args:
                context: The call context with dependencies
                search_query: The search query
            
            Returns:
                Retrieved document content
            """
            doc_processor = context.deps.document_processor
            document_id = context.deps.document_id
            
            # Search for relevant chunks
            results = await doc_processor.search_documents(
                query=search_query,
                document_id=document_id,
                top_k=5
            )
            
            # Combine results
            retrieved_content = "\n\n".join([
                f"[Chunk {r['chunk_index']}] {r['content']}"
                for r in results
            ])
            
            return retrieved_content if retrieved_content else "No relevant content found."
    
    def _reinitialize_model(self, model_name: Optional[str] = None, api_key: Optional[str] = None):
        """Reinitialize the model"""
        super()._reinitialize_model(model_name, api_key)
        model = get_rag_model(self.model_name, self.api_key)
        self.agent = Agent(
            model,
            deps_type=RAGDependencies,
            system_prompt="""
            You are an AI tutor helping a medical student learn from their study materials.
            Use the retrieve tool to find relevant information from the uploaded document.
            Answer questions accurately based on the retrieved content, provide explanations,
            and help the student understand complex medical concepts.
            Be educational, clear, and encouraging. Always cite your sources.
            """,
            output_type=RAGResponse
        )
        self._register_retrieve_tool()
    
    async def answer_question(
        self,
        question: str,
        document_id: str,
        chat_history: Optional[List[dict]] = None
    ) -> dict:
        """
        Answer a question using RAG
        
        Args:
            question: User's question
            document_id: ID of the document to search
            chat_history: Previous conversation history
            
        Returns:
            Dictionary with answer and sources
        """
        # Get document processor
        doc_processor = get_document_processor()
        
        # Create dependencies
        deps = RAGDependencies(
            openai_client=self.openai_client,
            document_processor=doc_processor,
            document_id=document_id
        )
        
        # Build context with chat history
        context_parts = [question]
        if chat_history:
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in chat_history[-5:]  # Last 5 messages
            ])
            context_parts.insert(0, f"Previous conversation:\n{history_text}\n\nCurrent question:")
        
        # Run agent
        result = await self.agent.run("\n".join(context_parts), deps=deps)
        
        # Extract response
        rag_response = result.output
        
        # Return as dict for compatibility
        return {
            "answer": rag_response.response if isinstance(rag_response, RAGResponse) else str(rag_response),
            "sources": rag_response.sources if isinstance(rag_response, RAGResponse) else [],
            "usage": result.usage().dict() if hasattr(result, 'usage') else {}
        }


# Global instance
_rag_agent: Optional[RAGAgent] = None


def get_rag_agent(model_name: Optional[str] = None, api_key: Optional[str] = None, provider: str = "google") -> RAGAgent:
    """Get or create global RAG agent instance"""
    global _rag_agent
    if _rag_agent is None:
        _rag_agent = RAGAgent(model_name, api_key, provider)
    return _rag_agent

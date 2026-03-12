# Learning Mode Workflow

## Overview

Learning Mode enables users to upload documents and interact with them through an AI-powered chat interface. The system uses RAG (Retrieval-Augmented Generation) to provide context-aware responses based on document content. Documents are temporarily stored and automatically cleaned up after 2 hours.

## Architecture Components

### Services
- **Document Processor** - Handles document parsing, chunking, and embedding
- **RAG Agent** - Provides document-based question answering

### Storage
- **Supabase** - Document metadata and chat history
- **Pinecone/pgvector** - Vector embeddings for semantic search
- **Redis** - Chat session caching

## Workflow: Document Upload

### 1. User Request
```
POST /api/learning/upload
Form Data:
  - file: [PDF/DOCX/PPT/TXT/Image file]
  - document_id: "uuid"
  - user_id: "user_uuid"
```

### 2. Backend Processing

**Step 1: Validate File**
- Check file type (PDF, DOCX, PPT, TXT, Images)
- Validate file size limits
- Generate document ID if not provided

**Step 2: Read File Content**
```python
content = await file.read()
file_name = file.filename
file_type = file.content_type
```

**Step 3: Process Document**
```python
doc_processor = get_document_processor()
result = await doc_processor.process_document(
    file_content=content,
    file_name=file_name,
    file_type=file_type,
    user_id=user_id,
    document_id=document_id
)
```

**Document Processing Steps**:
1. **Extract Text**:
   - PDF: PyPDF2 extraction
   - DOCX: python-docx extraction
   - PPT: python-pptx extraction
   - Images: OCR processing (if available)

2. **Chunk Text**:
   - Split into manageable chunks (500-1000 tokens)
   - Preserve context across chunks
   - Add metadata (chunk index, source, etc.)

3. **Generate Embeddings**:
   - Use OpenAI embeddings (text-embedding-3-small)
   - Create vector embeddings for each chunk
   - Store in Pinecone or pgvector

4. **Create Pinecone Index** (if using Pinecone):
   - Generate unique index name
   - Set expiry time (2 hours from now)
   - Store embeddings with metadata

**Step 4: Save Document Metadata**
```python
db_service.create_document(
    user_id=user_id,
    name=file_name,
    file_name=file_name,
    file_type=file_type,
    file_size=len(content),
    content=text_content[:10000],  # First 10k chars for preview
    pinecone_index_name=index_name,
    expires_at=datetime.now() + timedelta(hours=2)
)
```

**Step 5: Mark as Processed**
```python
db_service.mark_document_processed(
    document_id=document_id,
    chunk_count=len(chunks),
    pinecone_index_name=index_name
)
```

**Step 6: Cache Processing Status**
```python
await redis_service.cache_document_processing(
    document_id=document_id,
    status="completed",
    progress=1.0,
    metadata={"chunk_count": len(chunks)}
)
```

### 3. Response
```json
{
  "success": true,
  "document_id": "uuid",
  "status": "completed",
  "chunk_count": 45,
  "expires_at": "2024-03-10T20:26:00Z"
}
```

## Workflow: Document Chat

### 1. User Request
```
POST /api/learning/chat
{
  "document_id": "uuid",
  "user_id": "user_uuid",
  "message": "What are the key points about hypertension?",
  "model_name": "gemini-2.5-flash",
  "api_key": "user_api_key",
  "provider": "google"
}
```

### 2. Backend Processing

**Step 1: Validate Request**
- Check document exists
- Verify document not expired
- Get user ID from JWT token

**Step 2: Get Chat History**
```python
# Try Redis first
chat_history = await redis_service.get_chat_session(
    user_id=user_id,
    document_id=document_id
)

# Fallback to database
if not chat_history:
    chat_history = db_service.get_chat_history(
        user_id=user_id,
        document_id=document_id,
        limit=50
    )
```

**Step 3: Initialize RAG Agent**
```python
rag_agent = get_rag_agent(
    model_name=model_name,
    api_key=api_key,
    provider=provider
)
```

**Step 4: Generate Response (Streaming)**
```python
async def generate_response():
    # RAG Agent processes:
    # 1. Receives user question
    # 2. Calls retrieve() tool with search query
    # 3. Retrieve tool searches document chunks:
    #    - Uses vector similarity search
    #    - Returns top 5 relevant chunks
    # 4. Agent generates response using retrieved context
    # 5. Includes source citations
    
    result = await rag_agent.answer_question(
        question=message,
        document_id=document_id,
        chat_history=chat_history[-5:]  # Last 5 messages
    )
    
    # Stream response word-by-word
    words = result["answer"].split()
    for word in words:
        yield f"data: {json.dumps({'content': word + ' '})}\n\n"
        await asyncio.sleep(0.03)
```

**RAG Agent Internal Flow**:
1. **Question Analysis**: Understands user's question
2. **Retrieval**: Calls `retrieve(search_query)` tool
   ```python
   @rag_agent.tool
   async def retrieve(context, search_query: str) -> str:
       # Search document chunks using vector similarity
       results = await doc_processor.search_documents(
           query=search_query,
           document_id=document_id,
           top_k=5
       )
       # Return relevant chunks
       return "\n\n".join([r['content'] for r in results])
   ```
3. **Context Building**: Combines retrieved chunks with chat history
4. **Response Generation**: Generates answer using retrieved context
5. **Source Extraction**: Identifies which chunks were used

**Step 5: Save Chat Messages**
```python
# Save user message
db_service.create_chat_message(
    user_id=user_id,
    document_id=document_id,
    role="user",
    content=message
)

# Save assistant response
db_service.create_chat_message(
    user_id=user_id,
    document_id=document_id,
    role="assistant",
    content=result["answer"],
    sources=result["sources"]
)
```

**Step 6: Update Chat Session Cache**
```python
# Append to chat history
chat_history.append({"role": "user", "content": message})
chat_history.append({"role": "assistant", "content": result["answer"]})

# Cache in Redis
await redis_service.set_chat_session(
    user_id=user_id,
    document_id=document_id,
    chat_history=chat_history[-20:],  # Last 20 messages
    ttl=3600
)
```

### 3. Response (Streaming)
```
data: {"content": "Hypertension "}
data: {"content": "is "}
data: {"content": "characterized "}
...
data: {"content": "pressure.", "complete": true, "sources": ["chunk_12", "chunk_15"]}
```

## Workflow: Create Quiz from Document

### 1. User Request
```
POST /api/learning/create-quiz
{
  "document_id": "uuid",
  "user_id": "user_uuid",
  "num_questions": 10,
  "quiz_type": "general",
  "model_name": "...",
  "api_key": "..."
}
```

### 2. Backend Processing

**Step 1: Get Document Content**
```python
document = db_service.get_document(document_id)
# Get full content or use chunks
context = document.get("content", "")
```

**Step 2: Generate Quiz**
```python
quiz = await generate_quiz(
    quiz_type=quiz_type,
    num_questions=num_questions,
    time_limit=600,
    context=context,  # Document content as context
    source="document",
    document_id=document_id,
    model_name=model_name,
    api_key=api_key
)
```

**Step 3: Save Quiz**
```python
db_service.create_quiz(
    user_id=user_id,
    title=f"Quiz from {document['name']}",
    questions=quiz.questions,
    quiz_type="mixed",
    time_limit=600,
    total_questions=num_questions,
    source="document",
    document_id=document_id
)
```

### 3. Response
```json
{
  "success": true,
  "quiz": {
    "id": "quiz_uuid",
    "title": "Quiz from Document.pdf",
    "questions": [...],
    "source": "document"
  }
}
```

## Workflow: Create Mediquest from Document

### 1. User Request
```
POST /api/learning/create-quest
{
  "document_id": "uuid",
  "user_id": "user_uuid",
  "game_config": {...},
  "model_name": "...",
  "api_key": "..."
}
```

### 2. Backend Processing

**Step 1: Get Document Content**
```python
document = db_service.get_document(document_id)
document_content = document.get("content", "")
```

**Step 2: Initialize Game with Document**
```python
game_master = get_game_master_agent(model_name, api_key, provider)
game_state = await game_master.initialize_game(
    game_config=game_config,
    user_id=user_id,
    from_document=True,
    document_content=document_content
)
```

**Step 3: Save Game State**
```python
db_service.create_game_state(
    user_id=user_id,
    case_id=game_state.case_id,
    state=game_state.model_dump(),
    scenario_type="document_based",
    document_id=document_id
)
```

### 3. Response
```json
{
  "success": true,
  "game_state": {...}
}
```

## Workflow: Document Cleanup

### Automatic Cleanup (Scheduled)

**Process**:
1. Cron job runs every hour
2. Find expired documents:
   ```sql
   SELECT * FROM documents
   WHERE pinecone_index_expires_at < NOW() - INTERVAL '2 hours'
   ```
3. For each expired document:
   - Delete Pinecone index (if exists)
   - Delete document chunks from database
   - Delete document record
   - Clear Redis cache
4. Log cleanup statistics

**Manual Cleanup Endpoint**:
```
POST /api/cleanup/expired-documents
```

## Data Flow Diagram

```
Document Upload
    ↓
File Validation
    ↓
Text Extraction
    ↓
Chunking
    ↓
Embedding Generation
    ↓
Vector Storage (Pinecone/pgvector)
    ↓
Save Metadata (Supabase)
    ↓
Cache Status (Redis)
    ↓
Return Success

Chat Request
    ↓
Get Chat History (Redis → Database)
    ↓
RAG Agent Processes
    ↓
[Retrieve Tool] Vector Search
    ↓
Get Relevant Chunks
    ↓
Generate Response (AI Model)
    ↓
Stream Response
    ↓
Save Messages (Database)
    ↓
Update Cache (Redis)
    ↓
Return Response
```

## Vector Search Process

### 1. Query Embedding
```python
query_embedding = openai_client.embeddings.create(
    model="text-embedding-3-small",
    input=search_query
).data[0].embedding
```

### 2. Similarity Search
```python
# Pinecone
results = pinecone_index.query(
    vector=query_embedding,
    top_k=5,
    filter={"document_id": document_id}
)

# pgvector
results = await db.query("""
    SELECT chunk_index, content, metadata
    FROM document_chunks
    WHERE document_id = $1
    ORDER BY embedding <=> $2::vector
    LIMIT 5
""", document_id, query_embedding)
```

### 3. Retrieve Chunks
- Return top 5 most similar chunks
- Include chunk index and metadata
- Combine into context string

## Error Handling

- **Invalid File Type**: Return 400 Bad Request
- **File Too Large**: Return 413 Payload Too Large
- **Processing Error**: Return 500 with error details
- **Document Expired**: Return 410 Gone
- **Vector Search Error**: Fallback to keyword search
- **Rate Limiting**: Return 429 Too Many Requests

## Performance Optimizations

- Redis caching for chat sessions (1 hour TTL)
- Batch embedding generation
- Async document processing
- Connection pooling for database
- Lazy loading of document content
- Streaming responses for chat

## Security Considerations

- File type validation
- File size limits
- User ID verification from JWT
- Document ownership verification
- Automatic cleanup of expired documents
- Input sanitization for chat messages
- Rate limiting per user

## Temporary Storage Strategy

- **Documents**: 2-hour expiry from upload time
- **Pinecone Indexes**: Auto-deleted after expiry
- **Chat Sessions**: 1-hour TTL in Redis
- **Processing Status**: 2-hour TTL in Redis
- **Cleanup**: Automatic via scheduled jobs

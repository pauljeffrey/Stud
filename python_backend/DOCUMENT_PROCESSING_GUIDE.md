# Document Processing Guide

## Overview

This document explains how document processing works in Stud, including file storage, vector DB management, and cleanup processes.

## Document Processing Flow

### 1. Upload & Processing

When a user uploads a document:

1. **File Size Validation**: Files are validated against size limits:
   - Regular files: 10MB max (configurable via `MAX_FILE_SIZE`)
   - Images: 5MB max (configurable via `MAX_IMAGE_SIZE`)

2. **S3 Storage** (if enabled):
   - File is saved to S3 bucket for persistent storage
   - S3 key is stored in database for re-ingestion
   - Files remain in S3 even after vector DB expiration

3. **Text Extraction**:
   - **PDF**: Uses PyPDF2 for text extraction
   - **DOCX**: Uses python-docx for text extraction
   - **PPTX**: Uses python-pptx for slide text extraction
   - **Images**: Uses FileParserAgent with vision model for OCR and content extraction
   - **Text**: Direct UTF-8 decoding

4. **Nonsensical Text Detection**:
   - For PDF/DOCX files, extracted text is checked for quality
   - If text appears nonsensical (OCR errors, corrupted extraction), FileParserAgent is used
   - FileParserAgent uses vision models for better extraction

5. **Chunking** (Memory Efficient):
   - Uses streaming generator to avoid loading entire document in memory
   - Chunks are 1000 words with 200 word overlap
   - Yields chunks one at a time instead of storing all in memory

6. **Embedding Generation**:
   - Embeddings generated in parallel batches (50 chunks at a time)
   - Uses OpenAI `text-embedding-3-small` model
   - Parallel processing for efficiency

7. **Vector DB Storage**:
   - Chunks stored in Pinecone with metadata
   - Each document gets its own Pinecone index
   - Index name format: `doc-{document_id}-{timestamp}`

8. **Database Storage**:
   - Document metadata saved to Supabase `documents` table
   - Includes: file info, Pinecone index name, expiration time, S3 key
   - First 10k characters stored for preview

### 2. Document Expiration

**Vector DB (Pinecone)**:
- Documents expire after **2 hours** (configurable via `PINECONE_INDEX_EXPIRATION_HOURS`)
- After expiration, Pinecone index is deleted
- Document metadata remains in database with `pinecone_index_name = NULL`

**S3 Storage**:
- Files remain in S3 indefinitely (if S3 is enabled)
- Allows re-ingestion after vector DB expiration
- S3 key stored in database for retrieval

### 3. Re-ingestion

When a document has expired from vector DB:

1. User tries to search/chat with expired document
2. System checks if S3 key exists in database
3. If S3 enabled and file exists:
   - Downloads file from S3
   - Re-processes document (extract, chunk, embed)
   - Creates new Pinecone index
   - Updates database with new index name
4. If S3 not enabled or file missing:
   - Returns error: "Document has expired and cannot be re-ingested"

### 4. Cleanup Service

**When it runs**:
- Automatically started as background task on server startup
- Runs every **1 hour** (3600 seconds)
- Can also be manually triggered via `/api/cleanup/documents` endpoint

**What it does**:
1. Finds documents expired more than 2 hours ago
2. Deletes Pinecone indexes for expired documents
3. Updates database: sets `pinecone_index_name = NULL`, `processing_status = "expired"`
4. **Does NOT delete S3 files** (keeps them for re-ingestion)
5. **Does NOT delete database records** (preserves metadata)

**Cleanup Service Location**:
- Background task: `python_backend/service/cleanup_service.py::run_cleanup_task()`
- Started in: `python_backend/main.py::lifespan()` function
- API endpoint: `python_backend/api/cleanup.py`

## File Storage Architecture

### S3 Service (`python_backend/service/s3_service.py`)

**Purpose**: Persistent file storage for re-ingestion capability

**Features**:
- Upload files to S3 bucket
- Download files from S3
- Delete files from S3
- Generate presigned URLs for file access
- Check file existence

**Environment Variables** (add to `.env`, don't set values yet):
```env
# S3 Configuration (optional)
S3_ENABLED=false
S3_BUCKET_NAME=
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

**Usage**:
- If `S3_ENABLED=true` and credentials provided: files saved to S3
- If `S3_ENABLED=false` or missing credentials: S3 operations skipped (no errors)

### Database Service (`python_backend/service/database.py`)

**Purpose**: Centralized database operations

**Document Operations**:
- `create_document()`: Create document record with metadata
- `get_document()`: Retrieve document by ID
- `get_user_documents()`: Get all documents for a user
- `update_document()`: Update document metadata
- `mark_document_processed()`: Mark document as processed

**Why use database service instead of direct Supabase**:
- Single source of truth for database operations
- Consistent error handling
- Easier to test and mock
- Cleaner separation of concerns

## Memory Efficiency

### Streaming Chunking

Instead of:
```python
chunks = []  # Stores all chunks in memory
for chunk in process_chunks():
    chunks.append(chunk)  # Memory grows with document size
```

We use:
```python
def _chunk_document_streaming():
    # Yields chunks one at a time
    yield DocumentChunk(...)  # Memory efficient
```

### Parallel Embedding Generation

- Embeddings generated in batches of 50 (configurable)
- Uses `asyncio.gather()` for parallel API calls
- Reduces total processing time

### Batch Upsert

- Vectors upserted to Pinecone in batches of 100
- Prevents memory overflow for large documents

## File Size Limits

**Frontend** (should be implemented):
- Add file size validation before upload
- Show error if file exceeds limits
- Recommended: 10MB for documents, 5MB for images

**Backend**:
- Validated in `DocumentProcessor.validate_file_size()`
- Throws `ValueError` if file too large
- Limits configurable via environment variables

## Answer to Your Questions

### Q: Why are we saving to Supabase in document_processor (lines 132-149)?

**A**: We're now using `database_service.create_document()` instead of direct Supabase calls. This provides:
- Consistent database interface
- Better error handling
- Easier testing
- Single source of truth

### Q: How does our app handle processing of uploaded documents?

**A**: 
1. File uploaded → validated for size
2. Saved to S3 (if enabled)
3. Text extracted based on file type
4. Nonsensical text checked → FileParserAgent used if needed
5. Document chunked (streaming, memory efficient)
6. Embeddings generated (parallel batches)
7. Stored in Pinecone vector DB
8. Metadata saved to database

### Q: Are processed files stored in vector DB forever?

**A**: **No**. Files expire from vector DB after **2 hours**. However:
- Files remain in **S3** (if enabled) for re-ingestion
- Database metadata is preserved
- Can be re-ingested from S3 when needed

### Q: When does cleanup_service run?

**A**: 
- **Automatically**: Every hour as background task (started in `main.py`)
- **Manually**: Via `/api/cleanup/documents` endpoint
- **On startup**: Background task starts when FastAPI app starts

## Environment Variables Summary

Add these to your `.env` file (don't set values yet - just document them):

```env
# S3 Storage (Optional - for re-ingestion capability)
S3_ENABLED=false
S3_BUCKET_NAME=
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# File Size Limits
MAX_FILE_SIZE=10485760  # 10MB default
MAX_IMAGE_SIZE=5242880  # 5MB default

# Vector DB Expiration
PINECONE_INDEX_EXPIRATION_HOURS=2  # Default 2 hours
```

## Best Practices

1. **Always use database service** instead of direct Supabase calls
2. **Enable S3** for production to allow re-ingestion
3. **Set appropriate file size limits** based on your tier
4. **Monitor cleanup service** logs for expired document cleanup
5. **Use streaming chunking** for large files to avoid memory issues
6. **Implement frontend file size validation** before upload

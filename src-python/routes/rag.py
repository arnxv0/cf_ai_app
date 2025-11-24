from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import logging
import os

logger = logging.getLogger("pointer.routes.rag")

router = APIRouter(prefix="/api/rag", tags=["rag"])


class AddDocumentRequest(BaseModel):
    text: str
    source: str = "manual"
    filename: Optional[str] = None


class QueryRequest(BaseModel):
    query: str
    k: int = 5


@router.get("/stats")
async def get_stats():
    """Get knowledge base statistics."""
    try:
        from tools.rag import get_store, EMBEDDING_DIM
        store = get_store()
        
        # Count by source
        sources = {}
        dimension_issues = 0
        for doc in store.docs:
            sources[doc.source] = sources.get(doc.source, 0) + 1
            if len(doc.vec) != EMBEDDING_DIM:
                dimension_issues += 1
        
        return {
            "total_documents": len(store.docs),
            "by_source": sources,
            "database_path": store.db_path,
            "embedding_dimension": EMBEDDING_DIM,
            "dimension_issues": dimension_issues,
            "sample_docs": [
                {
                    "id": doc.id[:8] + "...",
                    "filename": doc.filename,
                    "source": doc.source,
                    "vec_dim": len(doc.vec),
                    "preview": doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
                }
                for doc in store.docs[:5]  # Show first 5 docs
            ]
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add")
async def add_document(request: AddDocumentRequest):
    """Add a document to the knowledge base."""
    try:
        from tools.rag import get_store, embed
        import uuid
        
        store = get_store()
        doc_id = str(uuid.uuid4())
        
        # Embed and add
        vec = embed(request.text)
        store.add(doc_id, request.text, vec, source=request.source, filename=request.filename)
        
        return {
            "success": True,
            "id": doc_id,
            "total_documents": len(store.docs)
        }
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to the knowledge base."""
    try:
        from tools.rag import get_store, embed
        import uuid
        
        # Read file content
        content = await file.read()
        
        # Handle PDF files
        if file.filename and (file.filename.endswith('.pdf') or file.content_type == 'application/pdf'):
            try:
                from pypdf import PdfReader
                from io import BytesIO
                
                # Extract text from PDF
                pdf_reader = PdfReader(BytesIO(content))
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                text = "\n\n".join(text_parts)
                
                if not text.strip():
                    raise HTTPException(status_code=400, detail="Could not extract text from PDF")
                    
            except Exception as e:
                logger.error(f"Error extracting PDF text: {e}")
                raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")
        else:
            # Handle text files
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text or PDF")
        
        store = get_store()
        doc_id = str(uuid.uuid4())
        
        # Embed and add
        vec = embed(text)
        store.add(doc_id, text, vec, source="file", filename=file.filename)
        
        return {
            "success": True,
            "id": doc_id,
            "filename": file.filename,
            "total_documents": len(store.docs)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def query_documents(request: QueryRequest):
    """Query the knowledge base."""
    try:
        from tools.rag import get_store, embed
        
        store = get_store()
        query_vec = embed(request.query)
        results = store.search(query_vec, k=request.k)
        
        return {
            "success": True,
            "query": request.query,
            "matches": [{
                "id": doc.id,
                "score": float(score),
                "text": doc.text,
                "source": doc.source,
                "filename": doc.filename,
                "created_at": doc.created_at,
                "preview": doc.text[:200] + "..." if len(doc.text) > 200 else doc.text
            } for doc, score in results]
        }
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(skip: int = 0, limit: int = 50):
    """List all documents in the knowledge base."""
    try:
        from tools.rag import get_store
        
        store = get_store()
        docs = store.docs[skip:skip + limit]
        
        return {
            "success": True,
            "total": len(store.docs),
            "skip": skip,
            "limit": limit,
            "documents": [{
                "id": doc.id,
                "text": doc.text,
                "source": doc.source,
                "filename": doc.filename,
                "created_at": doc.created_at,
                "preview": doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
            } for doc in docs]
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from the knowledge base."""
    try:
        from tools.rag import get_store
        
        store = get_store()
        
        # Use the delete method which handles DB updates
        deleted = store.delete(doc_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "success": True,
            "id": doc_id,
            "total_documents": len(store.docs)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base():
    """Clear all documents from the knowledge base."""
    try:
        from tools.rag import get_store
        
        store = get_store()
        count = len(store.docs)
        
        # Use the clear method which handles DB updates
        store.clear()
        
        return {
            "success": True,
            "deleted_count": count,
            "message": "Knowledge base cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))

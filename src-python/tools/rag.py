from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass, asdict
from tool_adapter import FunctionTool
import sqlite3
import json
import uuid
from datetime import datetime
import os
from pathlib import Path

# Constants
EMBEDDING_DIM = 100  # Fixed dimension for all embeddings

# Enhanced document with metadata
@dataclass
class Doc:
    id: str
    text: str
    vec: np.ndarray
    source: str = "manual"  # manual, file, selection
    filename: Optional[str] = None
    created_at: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if self.metadata is None:
            self.metadata = {}


def _get_data_dir() -> Path:
    """Get the application data directory, creating it if needed."""
    # Use user's home directory for data storage
    if os.name == 'nt':  # Windows
        data_dir = Path(os.environ.get('APPDATA', Path.home())) / 'Pointer'
    elif os.name == 'posix':  # macOS/Linux
        if 'darwin' in os.sys.platform:  # macOS
            data_dir = Path.home() / 'Library' / 'Application Support' / 'Pointer'
        else:  # Linux
            data_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share')) / 'Pointer'
    else:
        data_dir = Path.home() / '.pointer'
    
    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class TinyStore:
    def __init__(self, db_path: str = None):
        self.docs: List[Doc] = []
        # Use default path in app data directory if not specified
        if db_path is None:
            db_path = str(_get_data_dir() / "knowledge_base.db")
        self.db_path = db_path
        self._init_db()
        self._load_from_db()

    def _init_db(self):
        """Initialize SQLite database for persistent storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                vec BLOB NOT NULL,
                source TEXT NOT NULL,
                filename TEXT,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _load_from_db(self):
        """Load all documents from database into memory"""
        import logging
        logger = logging.getLogger("arrow.tools.rag")
        
        logger.info(f"📖 Loading documents from database: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, text, vec, source, filename, created_at, metadata FROM documents")
            rows = cursor.fetchall()
            
            logger.info(f"📖 Found {len(rows)} documents in database")
            
            needs_reembedding = []
            
            for row in rows:
                doc_id, text, vec_blob, source, filename, created_at, metadata_json = row
                vec = np.frombuffer(vec_blob, dtype=float)
                metadata = json.loads(metadata_json) if metadata_json else {}
                
                # Check if vector has correct dimension
                if len(vec) != EMBEDDING_DIM:
                    logger.warning(f"⚠️  Document {doc_id[:8]}... has wrong dimension ({len(vec)} vs {EMBEDDING_DIM}), will re-embed")
                    needs_reembedding.append((doc_id, text, source, filename, created_at, metadata))
                    continue
                
                self.docs.append(Doc(
                    id=doc_id,
                    text=text,
                    vec=vec,
                    source=source,
                    filename=filename,
                    created_at=created_at,
                    metadata=metadata
                ))
                logger.info(f"✅ Loaded document: {filename or doc_id[:8]}... (source: {source})")
            
            # Re-embed documents with wrong dimensions
            if needs_reembedding:
                logger.info(f"🔄 Re-embedding {len(needs_reembedding)} documents with new embeddings...")
                for doc_id, text, source, filename, created_at, metadata in needs_reembedding:
                    new_vec = embed(text)
                    self.docs.append(Doc(
                        id=doc_id,
                        text=text,
                        vec=new_vec,
                        source=source,
                        filename=filename,
                        created_at=created_at,
                        metadata=metadata
                    ))
                    # Update in database
                    cursor.execute("""
                        UPDATE documents SET vec = ? WHERE id = ?
                    """, (new_vec.tobytes(), doc_id))
                    logger.info(f"✅ Re-embedded document: {filename or doc_id[:8]}...")
                
                conn.commit()
                logger.info(f"✅ Updated {len(needs_reembedding)} documents with new embeddings")
            
            conn.close()
            logger.info(f"📖 Loaded {len(self.docs)} documents into memory")
        except Exception as e:
            logger.error(f"❌ Error loading from database: {e}")
            import traceback
            traceback.print_exc()

    def add(self, id: str, text: str, vec: np.ndarray, source: str = "manual", 
            filename: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        """Add document to both memory and database"""
        doc = Doc(
            id=id,
            text=text,
            vec=vec,
            source=source,
            filename=filename,
            metadata=metadata or {}
        )
        self.docs.append(doc)
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, text, vec, source, filename, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            doc.id,
            doc.text,
            vec.tobytes(),
            doc.source,
            doc.filename,
            doc.created_at,
            json.dumps(doc.metadata)
        ))
        conn.commit()
        conn.close()

    def delete(self, doc_id: str) -> bool:
        """Delete document from both memory and database"""
        # Remove from memory
        self.docs = [d for d in self.docs if d.id != doc_id]
        
        # Remove from database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted

    def get_all(self) -> List[Dict[str, Any]]:
        """Get all documents with metadata"""
        return [{
            "id": d.id,
            "text": d.text,
            "source": d.source,
            "filename": d.filename,
            "created_at": d.created_at,
            "metadata": d.metadata,
            "preview": d.text[:200] + "..." if len(d.text) > 200 else d.text
        } for d in self.docs]

    def search(self, qvec: np.ndarray, k: int = 5):
        if not self.docs:
            return []
        
        # All vectors now have same dimension (EMBEDDING_DIM)
        sims = []
        for d in self.docs:
            q_norm = np.linalg.norm(qvec)
            d_norm = np.linalg.norm(d.vec)
            
            if q_norm == 0 or d_norm == 0:
                sims.append(0.0)
            else:
                # Cosine similarity
                sim = float(qvec @ d.vec / (q_norm * d_norm))
                sims.append(sim)
        
        topk = np.argsort(sims)[::-1][:k]
        return [(self.docs[i], sims[i]) for i in topk]

    def clear(self):
        """Clear all documents"""
        self.docs = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documents")
        conn.commit()
        conn.close()


STORE = TinyStore()


# Embeddings: simple bag-of-words with fixed dimensions to avoid mismatches
# (Already defined at top of file)

def embed(text: str) -> np.ndarray:
    """Create a simple fixed-dimension embedding from text using hash-based features"""
    tokens = text.lower().split()
    
    # Create a fixed-size vector using hash-based feature mapping
    vec = np.zeros(EMBEDDING_DIM, dtype=float)
    
    for token in tokens:
        # Use hash to map token to a position in the fixed vector
        idx = hash(token) % EMBEDDING_DIM
        vec[idx] += 1.0
    
    # Normalize the vector
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    
    return vec


# API functions for the agent
async def rag_add(id: str, text: str, source: str = "manual", 
                  filename: Optional[str] = None) -> Dict[str, Any]:
    """Add a document to the knowledge base"""
    if not id:
        id = str(uuid.uuid4())
    STORE.add(id, text, embed(text), source=source, filename=filename)
    return {"status": "ok", "id": id, "count": len(STORE.docs)}


async def rag_query(query: str, k: int = 5) -> Dict[str, Any]:
    """Query the knowledge base"""
    import logging
    logger = logging.getLogger("arrow.tools.rag")
    
    logger.info(f"🔍 RAG Query: '{query}' (searching {len(STORE.docs)} documents)")
    
    results = STORE.search(embed(query), k=k)
    
    logger.info(f"📊 Found {len(results)} results")
    for i, (d, score) in enumerate(results[:3]):  # Log top 3
        logger.info(f"   {i+1}. {d.filename or d.id[:8]}... (score: {score:.3f})")
    
    return {
        "matches": [{
            "id": d.id,
            "score": s,
            "text": d.text,
            "source": d.source,
            "filename": d.filename,
            "preview": d.text[:200] + "..." if len(d.text) > 200 else d.text
        } for d, s in results]
    }


# Export store for direct access
def get_store() -> TinyStore:
    """Get the global store instance"""
    return STORE


RagAddTool = FunctionTool(func=rag_add)
RagQueryTool = FunctionTool(func=rag_query)
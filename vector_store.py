"""
Vector Store Module
Handles embeddings and similarity search using ChromaDB
"""

import logging
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from knowledge_base import get_document_chunks

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, embedding_model_name="all-MiniLM-L6-v2", persist_dir="./chroma_db"):
        """
        Initialize vector store with embedding model and ChromaDB
        
        Args:
            embedding_model_name: Name of sentence-transformer model
            persist_dir: Directory to persist ChromaDB
        """
        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        # Disable telemetry to avoid errors
        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("knowledge_base")
            logger.info(f"Loaded existing collection with {self.collection.count()} documents")
        except:
            self.collection = self.client.create_collection("knowledge_base")
            logger.info("Created new collection")
            self._initialize_collection()
    
    def _initialize_collection(self):
        """Load documents into vector store"""
        chunks = get_document_chunks()
        
        if len(chunks) == 0:
            logger.warning("No documents to load")
            return
        
        logger.info(f"Embedding {len(chunks)} documents...")
        
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        
        # Add to collection
        self.collection.add(
            documents=texts,
            embeddings=embeddings.tolist(),
            ids=[chunk["id"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks]
        )
        
        logger.info(f"✓ Successfully loaded {len(chunks)} documents into vector store")
    
    def search(self, query: str, k: int = 3):
        """
        Search for relevant documents
        
        Args:
            query: Search query string
            k: Number of results to return
            
        Returns:
            List of dictionaries with text, metadata, and distance
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results['documents'][0])):
            formatted_results.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i] if 'distances' in results else 0,
                'source': results['metadatas'][0][i].get('source', 'unknown')
            })
        
        return formatted_results
    
    def get_stats(self):
        """Get collection statistics"""
        return {
            'total_documents': self.collection.count(),
            'embedding_model': self.embedding_model.get_sentence_embedding_dimension()
        }
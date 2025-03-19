from typing import List, Dict, Union, Optional
import chromadb
from chromadb.config import Settings
import numpy as np
import logging
from datetime import datetime

from src.config import settings

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        """Initialize the vector store with ChromaDB."""
        self.client = chromadb.HttpClient(
            host=settings.VECTOR_STORE_HOST,
            port=settings.VECTOR_STORE_PORT,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        self.collection_name = "documents"
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if it doesn't."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except chromadb.errors.InvalidCollectionException:
            # Create the collection if it doesn't exist
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}  # or "l2" depending on your needs
            )

    def store_embeddings(
        self,
        embeddings: List[Dict],
        document_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """Store embeddings with their metadata in the vector store."""
        try:
            # Prepare data for storage
            ids = []
            vectors = []
            metadatas = []
            texts = []

            for i, embedding_data in enumerate(embeddings):
                # Generate unique ID for each chunk
                chunk_id = f"{document_id}_chunk_{i}"
                
                # Prepare metadata
                chunk_metadata = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'timestamp': datetime.utcnow().isoformat(),
                    **(metadata or {}),
                    **{k: v for k, v in embedding_data.items() if k not in ['text', 'embedding']}
                }
                
                ids.append(chunk_id)
                vectors.append(embedding_data['embedding'].tolist())
                metadatas.append(chunk_metadata)
                texts.append(embedding_data['text'])

            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=vectors,
                metadatas=metadatas,
                documents=texts
            )
            
            logger.info(f"Successfully stored {len(embeddings)} embeddings for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing embeddings: {str(e)}")
            raise

    def search_similar(
        self,
        query_embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar embeddings in the vector store."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            raise

    def get_document_chunks(
        self,
        document_id: str,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """Retrieve all chunks for a specific document."""
        try:
            where_clause = {
                'document_id': document_id,
                **(where or {})
            }
            
            results = self.collection.get(
                where=where_clause
            )
            
            formatted_results = []
            for i in range(len(results['ids'])):
                formatted_results.append({
                    'id': results['ids'][i],
                    'text': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'embedding': results['embeddings'][i]
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error retrieving document chunks: {str(e)}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks associated with a document."""
        try:
            self.collection.delete(
                where={'document_id': document_id}
            )
            logger.info(f"Successfully deleted document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    def update_metadata(
        self,
        document_id: str,
        metadata: Dict,
        where: Optional[Dict] = None
    ) -> bool:
        """Update metadata for document chunks."""
        try:
            where_clause = {
                'document_id': document_id,
                **(where or {})
            }
            
            self.collection.update(
                where=where_clause,
                metadatas=[metadata]
            )
            logger.info(f"Successfully updated metadata for document {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict:
        """Get statistics about the vector store collection."""
        try:
            return {
                'name': self.collection_name,
                'count': self.collection.count(),
                'metadata': self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def reset_collection(self) -> bool:
        """Reset the collection (delete all data)."""
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            logger.info(f"Successfully reset collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise 
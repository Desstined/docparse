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
            port=settings.VECTOR_STORE_PORT
        )
        self.collection_name = "documents"
        self.collection = None
        self._initialize_collection()

    def _initialize_collection(self):
        try:
            # First try to get the existing collection
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Retrieved existing collection: {self.collection_name}")
        except Exception as e:
            try:
                # Only create if it doesn't exist
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                # Initialize with empty metadata to establish the collection
                self.collection.add(
                    documents=["initialization"],
                    metadatas=[{"type": "system", "status": "initialized"}],
                    ids=["system_init"]
                )
            except chromadb.errors.UniqueConstraintError:
                # If we get here, the collection exists but get_collection failed for some reason
                # Try getting it one more time
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Retrieved collection after creation attempt: {self.collection_name}")
            except Exception as create_error:
                logger.error(f"Error creating collection: {create_error}")
                raise

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
            self._initialize_collection()
            logger.info(f"Successfully reset collection {self.collection_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise

    def get_documents(self):
        if not self.collection:
            self._initialize_collection()
        
        try:
            results = self.collection.get()
            # Filter out the initialization document
            if results and results.get('ids'):
                indices = [i for i, id in enumerate(results['ids']) if id != "system_init"]
                if not indices:  # If only initialization document exists
                    return {
                        'ids': [],
                        'embeddings': [],
                        'metadatas': [],
                        'documents': []
                    }
                return {
                    'ids': [results['ids'][i] for i in indices],
                    'embeddings': [results['embeddings'][i] for i in indices] if results.get('embeddings') else [],
                    'metadatas': [results['metadatas'][i] for i in indices] if results.get('metadatas') else [],
                    'documents': [results['documents'][i] for i in indices] if results.get('documents') else []
                }
            return {
                'ids': [],
                'embeddings': [],
                'metadatas': [],
                'documents': []
            }
        except Exception as e:
            logger.error(f"Error getting documents from vector store: {e}")
            return {
                'ids': [],
                'embeddings': [],
                'metadatas': [],
                'documents': []
            }

    def add_document(self, document_id: str, content: str, metadata: dict):
        try:
            if not self.collection:
                self._initialize_collection()
            
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[document_id]
            )
            logger.info(f"Added document {document_id} to collection")
        except Exception as e:
            logger.error(f"Error adding document to vector store: {e}")
            raise

    def search(
        self, 
        query_text: str, 
        n_results: int = 10, 
        where: dict | None = None,
        score_threshold: float = 0.0
    ) -> dict:
        try:
            if not self.collection:
                self._initialize_collection()

            # Get collection count
            collection_info = self.collection.count()
            if collection_info == 0:
                # Return empty results if collection is empty
                return {
                    'ids': [],
                    'distances': [],
                    'metadatas': [],
                    'documents': []
                }
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, collection_info),  # Don't request more results than documents
                where=where
            )
            
            # Format results to match expected structure
            return {
                'ids': results['ids'][0] if results.get('ids') else [],
                'distances': results['distances'][0] if results.get('distances') else [],
                'metadatas': results['metadatas'][0] if results.get('metadatas') else [],
                'documents': results['documents'][0] if results.get('documents') else []
            }
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            # Return empty results on error
            return {
                'ids': [],
                'distances': [],
                'metadatas': [],
                'documents': []
            }

    def update_document(self, document_id: str, content: str, metadata: dict):
        try:
            if not self.collection:
                self._initialize_collection()
            
            # Get existing metadata
            existing = self.collection.get(ids=[document_id])
            if existing and existing['metadatas']:
                # Merge existing metadata with updates
                metadata = {**existing['metadatas'][0], **metadata}
            
            self.collection.update(
                ids=[document_id],
                documents=[content] if content else None,
                metadatas=[metadata] if metadata else None
            )
            logger.info(f"Updated document {document_id}")
        except Exception as e:
            logger.error(f"Error updating document in vector store: {e}")
            raise

    def get_document(self, document_id: str) -> dict:
        try:
            if not self.collection:
                self._initialize_collection()
            
            result = self.collection.get(
                ids=[document_id],
                include=['metadatas', 'documents']
            )
            
            if not result or not result.get('ids'):
                raise ValueError(f"Document {document_id} not found")
            
            return result
        except Exception as e:
            logger.error(f"Error getting document from vector store: {e}")
            raise 
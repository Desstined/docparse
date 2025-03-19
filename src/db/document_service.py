from typing import List, Dict, Optional, Union
import uuid
import logging
from datetime import datetime

from src.vectorizer.processor import Vectorizer
from src.text_processor.processor import TextProcessor
from src.pdf_processor.processor import PDFProcessor
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self):
        """Initialize the document service with required processors."""
        self.vectorizer = Vectorizer()
        self.text_processor = TextProcessor()
        self.pdf_processor = PDFProcessor()
        self.vector_store = VectorStore()

    def process_document(
        self,
        file_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """Process a document: extract text, generate embeddings, and store in vector DB."""
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Extract text from PDF
            text = self.pdf_processor.extract_text(file_path)
            
            # Process text into chunks
            chunks = self.text_processor.chunk_text(text)
            
            # Generate embeddings for chunks
            embeddings = self.vectorizer.get_embeddings_with_metadata(
                texts=chunks,
                metadata=[{
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'source_file': file_path
                } for i in range(len(chunks))]
            )
            
            # Store embeddings in vector store
            self.vector_store.store_embeddings(
                embeddings=embeddings,
                document_id=document_id,
                metadata={
                    'source_file': file_path,
                    'processed_at': datetime.utcnow().isoformat(),
                    'total_chunks': len(chunks),
                    **(metadata or {})
                }
            )
            
            return {
                'document_id': document_id,
                'total_chunks': len(chunks),
                'metadata': metadata
            }
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

    def search_documents(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
        where_document: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar documents using a text query."""
        try:
            # Generate embedding for query
            query_embedding = self.vectorizer.get_embedding(query)
            
            # Search in vector store
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            return results
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    def get_document(
        self,
        document_id: str,
        include_embeddings: bool = False
    ) -> Dict:
        """Retrieve a document and its chunks from the vector store."""
        try:
            # Get document chunks
            chunks = self.vector_store.get_document_chunks(document_id)
            
            if not chunks:
                raise ValueError(f"Document {document_id} not found")
            
            # Get document metadata from first chunk
            document_metadata = {
                k: v for k, v in chunks[0]['metadata'].items()
                if k not in ['chunk_index', 'total_chunks']
            }
            
            # Prepare response
            response = {
                'document_id': document_id,
                'metadata': document_metadata,
                'chunks': [
                    {
                        'text': chunk['text'],
                        'metadata': {
                            k: v for k, v in chunk['metadata'].items()
                            if k in ['chunk_index', 'total_chunks']
                        }
                    }
                    for chunk in chunks
                ]
            }
            
            if include_embeddings:
                response['embeddings'] = [
                    chunk['embedding'] for chunk in chunks
                ]
            
            return response
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its chunks from the vector store."""
        try:
            return self.vector_store.delete_document(document_id)
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    def update_document_metadata(
        self,
        document_id: str,
        metadata: Dict
    ) -> bool:
        """Update metadata for a document."""
        try:
            return self.vector_store.update_metadata(
                document_id=document_id,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error updating document metadata: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict:
        """Get statistics about the document collection."""
        try:
            return self.vector_store.get_collection_stats()
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise

    def reset_collection(self) -> bool:
        """Reset the document collection."""
        try:
            return self.vector_store.reset_collection()
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise 
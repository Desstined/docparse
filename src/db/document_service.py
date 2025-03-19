from typing import List, Dict, Optional, Union
import uuid
import logging
from datetime import datetime
import os
from fastapi import UploadFile, status, HTTPException, BackgroundTasks
import PyPDF2
import io

from src.vectorizer.processor import Vectorizer
from src.text_processor.processor import TextProcessor
from src.pdf_processor.processor import PDFProcessor
from .vector_store import VectorStore
from src.api.models import CollectionStats, DocumentResponse, SearchQuery, SearchResponse, SearchResult
from .session import get_db
from sqlalchemy.orm import Session

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

    def get_collection_stats(self) -> CollectionStats:
        """Get statistics about the document collection."""
        try:
            # Get documents from vector store - don't raise exceptions
            try:
                results = self.vector_store.get_documents()
            except Exception as e:
                logger.error(f"Error getting documents from vector store: {e}")
                results = {'ids': [], 'documents': [], 'metadatas': []}

            # Always return a valid stats object
            doc_count = len(results.get('ids', []))
            chunk_count = len(results.get('documents', []))

            return CollectionStats(
                total_documents=doc_count,
                total_pages=0,  # This would come from metadata
                total_chunks=chunk_count,
                average_pages=0,  # This would come from metadata
                processing_documents=0,
                failed_documents=0,
                average_chunks_per_document=chunk_count / doc_count if doc_count > 0 else 0,
                documents_by_status={
                    "completed": doc_count,
                    "processing": 0,
                    "failed": 0
                }
            )
        except Exception as e:
            logger.error(f"Error calculating collection stats: {e}")
            # Always return a valid stats object, even on error
            return CollectionStats(
                total_documents=0,
                total_pages=0,
                total_chunks=0,
                average_pages=0,
                processing_documents=0,
                failed_documents=0,
                average_chunks_per_document=0,
                documents_by_status={
                    "completed": 0,
                    "processing": 0,
                    "failed": 0
                }
            )

    def reset_collection(self) -> bool:
        """Reset the document collection."""
        try:
            return self.vector_store.reset_collection()
        except Exception as e:
            logger.error(f"Error resetting collection: {str(e)}")
            raise

    async def upload_document(self, file: UploadFile, background_tasks: BackgroundTasks) -> DocumentResponse:
        try:
            content = await file.read()
            document_id = str(uuid.uuid4())
            
            # Save initial document state
            self.vector_store.add_document(
                document_id=document_id,
                content="",  # Empty content initially
                metadata={
                    "filename": file.filename,
                    "upload_date": datetime.utcnow().isoformat(),
                    "status": "processing"
                }
            )

            # Add processing task to background
            background_tasks.add_task(
                self._process_document,
                document_id,
                content
            )

            return DocumentResponse(
                id=document_id,
                filename=file.filename,
                upload_date=datetime.utcnow().isoformat(),
                status="processing"
            )

        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error uploading document: {str(e)}"
            )

    def _process_document(self, document_id: str, content: bytes):
        try:
            # Extract text from PDF
            pdf_text = self._extract_text_from_pdf(content)
            
            # Update document in vector store with processed content
            self.vector_store.update_document(
                document_id=document_id,
                content=pdf_text,
                metadata={
                    "status": "completed",
                    "processed_at": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            # Update document status to failed
            self.vector_store.update_document(
                document_id=document_id,
                content="",
                metadata={
                    "status": "failed",
                    "error": str(e)
                }
            )

    def _extract_text_from_pdf(self, content: bytes) -> str:
        try:
            # Create a PDF reader object
            pdf_file = io.BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Extract text from all pages
            text = []
            for page in pdf_reader.pages:
                text.append(page.extract_text())
            
            return "\n".join(text)
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing PDF file"
            )

    async def search_documents(self, query: SearchQuery) -> SearchResponse:
        try:
            # Get vector store results
            vector_results = self.vector_store.search(
                query_text=query.query,
                n_results=10,
                where={"status": "completed"} if not query.include_processing else None,
                score_threshold=query.similarity_threshold
            )
            
            # If no results, return empty response
            if not vector_results['ids']:
                return SearchResponse(
                    results=[],
                    total_results=0
                )

            # Get document details from database
            document_ids = vector_results['ids']
            documents = self.db.query(DBDocument).filter(DBDocument.id.in_(document_ids)).all()
            doc_map = {doc.id: doc for doc in documents}
            
            results = []
            for i, doc_id in enumerate(document_ids):
                if doc_id in doc_map:
                    doc = doc_map[doc_id]
                    results.append(SearchResult(
                        document_id=doc_id,
                        filename=doc.filename,
                        content=vector_results['documents'][i] if vector_results.get('documents') else "",
                        similarity_score=float(vector_results['distances'][i]),
                        upload_date=doc.upload_date.isoformat(),
                        status=doc.status,
                        matching_text=vector_results['documents'][i] if vector_results.get('documents') else None
                    ))
            
            return SearchResponse(
                results=results,
                total_results=len(results)
            )
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            # Return empty results instead of raising an error
            return SearchResponse(
                results=[],
                total_results=0
            )

    async def get_document(self, document_id: str) -> DocumentResponse:
        try:
            result = self.vector_store.get_document(document_id)
            if not result or not result.get('ids'):
                raise ValueError(f"Document {document_id} not found")
            
            metadata = result['metadatas'][0]
            return DocumentResponse(
                id=document_id,
                filename=metadata.get('filename', ''),
                upload_date=metadata.get('upload_date', ''),
                status=metadata.get('status', 'unknown')
            )
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            raise 
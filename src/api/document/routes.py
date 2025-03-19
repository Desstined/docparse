from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
from sqlalchemy.orm import Session
import logging

from src.db.document_service import DocumentService
from src.api.auth.utils import get_current_active_user
from src.db.session import get_db
from src.api.models import (
    DocumentResponse,
    SearchQuery,
    SearchResponse,
    CollectionStats,
    ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Dependency to get document service
def get_document_service():
    return DocumentService()

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all documents."""
    try:
        documents = document_service.list_documents(skip=skip, limit=limit)
        return documents
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[dict] = None,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and process a new document."""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )
        
        content = await file.read()
        document = document_service.process_document(content, metadata)
        return document
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific document by ID."""
    try:
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        return document
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a specific document by ID."""
    try:
        success = document_service.delete_document(document_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        return {"status": "success", "message": f"Document {document_id} deleted"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def get_empty_stats() -> CollectionStats:
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

@router.get("/stats")
async def get_collection_stats(
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user)
):
    try:
        stats = document_service.get_collection_stats()
        return stats if stats else get_empty_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        if "Document stats not found" in str(e):
            return get_empty_stats()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
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

@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    }
)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user)
):
    """Upload a new document."""
    return await document_service.upload_document(file, background_tasks)

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user)
):
    """Get a specific document by ID."""
    try:
        return await document_service.get_document(document_id)
    except Exception as e:
        logger.error(f"Error getting document: {str(e)}")
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
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

@router.get(
    "/stats",
    response_model=CollectionStats,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_collection_stats(
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user)
):
    """Get statistics about the document collection."""
    try:
        return document_service.get_collection_stats()
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        # Return empty stats instead of error
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

@router.post(
    "/search",
    response_model=SearchResponse,
    responses={
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def search_documents(
    query: SearchQuery,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(get_current_active_user)
):
    """Search documents using semantic search."""
    try:
        return await document_service.search_documents(query)
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        # Return empty results instead of error
        return SearchResponse(
            results=[],
            total_results=0
        ) 
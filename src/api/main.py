from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from typing import Optional
import logging
import tempfile
import os

from src.db.document_service import DocumentService
from src.api.auth.routes import router as auth_router
from src.api.auth.utils import get_current_active_user, check_permissions
from .models import (
    DocumentResponse,
    SearchQuery,
    SearchResponse,
    CollectionStats,
    ErrorResponse
)
from src.api.document.routes import router as document_router
from src.db.init_db import init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Processing API",
    description="""
    A powerful API for processing PDF documents and performing semantic search.
    
    ## Features
    * PDF document processing with OCR support
    * Text extraction and chunking
    * Semantic search using vector embeddings
    * Document metadata management
    * User authentication and authorization
    
    ## Authentication
    All endpoints except `/health` and `/auth/token` require authentication.
    Use the `/auth/token` endpoint to obtain a JWT token.
    
    ## Rate Limiting
    API requests are limited to prevent abuse.
    """,
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:80"],  # Add frontend service URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include authentication router
app.include_router(auth_router)
app.include_router(document_router)

# Dependency to get document service
def get_document_service():
    return DocumentService()

def custom_openapi():
    """Customize OpenAPI documentation."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    
    # Add security requirement to all endpoints
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            if "security" not in operation:
                operation["security"] = [{"Bearer": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized successfully")

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}

@app.post(
    "/documents",
    response_model=DocumentResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def process_document(
    file: UploadFile = File(...),
    metadata: Optional[dict] = None,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["documents:write"]))
):
    """
    Process a PDF document and store it in the vector database.
    
    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text and metadata
    3. Generates embeddings
    4. Stores the document in the vector database
    
    Requires the `documents:write` permission.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )

        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # Process the document
            result = document_service.process_document(
                file_path=temp_path,
                metadata=metadata
            )
            
            # Get the processed document
            document = document_service.get_document(
                document_id=result['document_id'],
                include_embeddings=True
            )
            
            return document
        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post(
    "/search",
    response_model=SearchResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def search_documents(
    query: SearchQuery,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["documents:read"]))
):
    """
    Search for similar documents using semantic search.
    
    This endpoint:
    1. Generates embeddings for the search query
    2. Performs similarity search in the vector database
    3. Returns matching documents with similarity scores
    
    Requires the `documents:read` permission.
    """
    try:
        results = document_service.search_documents(
            query=query.query,
            n_results=query.n_results,
            where=query.where,
            where_document=query.where_document
        )
        
        return SearchResponse(
            results=results,
            query=query.query,
            total_results=len(results)
        )
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_document(
    document_id: str,
    include_embeddings: bool = False,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["documents:read"]))
):
    """
    Retrieve a processed document by ID.
    
    This endpoint:
    1. Retrieves the document from the vector database
    2. Optionally includes embeddings in the response
    
    Requires the `documents:read` permission.
    """
    try:
        document = document_service.get_document(
            document_id=document_id,
            include_embeddings=include_embeddings
        )
        return document
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.delete(
    "/documents/{document_id}",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def delete_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["documents:delete"]))
):
    """
    Delete a document from the vector database.
    
    This endpoint:
    1. Removes the document and its embeddings
    2. Returns a success message
    
    Requires the `documents:delete` permission.
    """
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

@app.get(
    "/stats",
    response_model=CollectionStats,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_collection_stats(
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["admin"]))
):
    """
    Get statistics about the document collection.
    
    This endpoint:
    1. Retrieves collection statistics
    2. Returns metadata about the collection
    
    Requires the `admin` permission.
    """
    try:
        return document_service.get_collection_stats()
    except Exception as e:
        logger.error(f"Error getting collection stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.post(
    "/reset",
    response_model=dict,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def reset_collection(
    document_service: DocumentService = Depends(get_document_service),
    current_user = Depends(check_permissions(["admin"]))
):
    """
    Reset the document collection (delete all documents).
    
    This endpoint:
    1. Deletes all documents and their embeddings
    2. Returns a success message
    
    Requires the `admin` permission.
    """
    try:
        success = document_service.reset_collection()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset collection"
            )
        return {"status": "success", "message": "Collection reset successfully"}
    except Exception as e:
        logger.error(f"Error resetting collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 
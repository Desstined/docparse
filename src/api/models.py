from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Model for document metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    custom: Optional[Dict[str, Any]] = Field(default_factory=dict)

class DocumentChunk(BaseModel):
    """Model for document chunks."""
    id: str
    text: str
    metadata: Optional[DocumentMetadata] = None
    embedding: Optional[List[float]] = None

class DocumentResponse(BaseModel):
    """Model for document response."""
    id: str
    filename: str
    upload_date: str
    status: str

class SearchQuery(BaseModel):
    """Model for search query."""
    query: str
    similarity_threshold: float = 0.0
    include_processing: bool = False

class SearchResult(BaseModel):
    """Model for search result."""
    document_id: str
    filename: str
    content: str
    similarity_score: float
    upload_date: str
    status: str
    matching_text: str | None = None

class SearchResponse(BaseModel):
    """Model for search response."""
    results: list[SearchResult]
    total_results: int

class CollectionStats(BaseModel):
    """Model for collection statistics."""
    total_documents: int
    total_pages: int
    total_chunks: int
    average_pages: float
    processing_documents: int
    failed_documents: int
    average_chunks_per_document: float
    documents_by_status: dict[str, int]

class ErrorResponse(BaseModel):
    """Model for error response."""
    detail: str

class User(BaseModel):
    id: int
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool = False
    scopes: list[str] = [] 
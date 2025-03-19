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
    chunks: List[DocumentChunk]
    metadata: Optional[DocumentMetadata] = None
    created_at: datetime
    updated_at: datetime

class SearchQuery(BaseModel):
    """Model for search query."""
    query: str
    n_results: int = Field(default=10, gt=0, le=100)
    where: Optional[Dict[str, Any]] = None
    where_document: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    """Model for search result."""
    document_id: str
    chunk_id: str
    text: str
    metadata: Optional[DocumentMetadata] = None
    score: float

class SearchResponse(BaseModel):
    """Model for search response."""
    results: List[SearchResult]
    query: str
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
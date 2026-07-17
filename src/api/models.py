"""
models.py

Pydantic request and response models for the entitlement filtering demo API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for POST /api/search"""
    userId: str = Field(..., description="User identifier (e.g. user.alpha.north@example.com)")
    query: str = Field(..., description="Natural language search query", min_length=1)
    searchMode: str = Field(
        default="hybrid",
        description="Search mode: 'keyword', 'vector', or 'hybrid'"
    )
    topK: int = Field(default=5, ge=1, le=20, description="Maximum number of results to return")


class ChatRequest(BaseModel):
    """Request body for POST /api/chat"""
    userId: str = Field(..., description="User identifier")
    query: str = Field(..., description="User's question", min_length=1)
    searchMode: str = Field(default="hybrid", description="Search mode for retrieval")
    topK: int = Field(default=5, ge=1, le=20, description="Number of retrieval chunks for context")


class ChunkCitation(BaseModel):
    """Citation metadata for a retrieved document chunk."""
    title: str
    sourceFile: str
    sourcePage: Optional[int] = None
    partnerId: Optional[str] = None
    clientId: Optional[str] = None
    productLine: Optional[str] = None
    region: Optional[str] = None
    classification: Optional[str] = None
    score: Optional[float] = None


class SearchResult(BaseModel):
    """A single search result chunk."""
    chunkId: Optional[str] = None
    content: str
    citation: ChunkCitation


class SearchResponse(BaseModel):
    """Response body for POST /api/search"""
    userId: str
    query: str
    filter: str = Field(description="The OData filter applied to this query (for demo transparency)")
    results: List[SearchResult]
    resultCount: int
    message: Optional[str] = None


class ChatResponse(BaseModel):
    """Response body for POST /api/chat"""
    userId: str
    query: str
    filter: str
    answer: Optional[str] = None
    sources: List[SearchResult]
    message: Optional[str] = None


class EntitlementProfile(BaseModel):
    """A user's entitlement profile from the mock entitlement service."""
    userId: str
    displayName: str
    partnerId: str
    allowedClients: List[str]
    allowedProductLines: List[str]
    allowedRegions: List[str]
    canReadGlobalReferences: bool


class UserSummary(BaseModel):
    """Summary of a demo user for the users list endpoint."""
    userId: str
    displayName: str
    partnerId: str

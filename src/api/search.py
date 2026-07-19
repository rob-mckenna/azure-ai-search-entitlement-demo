"""
search.py

Azure AI Search query execution for the entitlement filtering demo.

This module handles the actual search requests to Azure AI Search.
Every query MUST include the entitlement filter — there is no code
path that runs an unfiltered search for user queries.

Supported search modes:
- keyword: Full-text search only (always available)
- vector: Vector similarity search (requires Azure OpenAI embeddings)
- hybrid: Combined keyword + vector search (requires Azure OpenAI embeddings)
"""

import os
import logging
import sys
from pathlib import Path
from typing import List, Optional

from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

# Allow importing the index schema consistently from src/ingestion/.
sys.path.insert(0, str(Path(__file__).parent.parent / "ingestion"))

from models import SearchResult, ChunkCitation
from index_schema import INDEX_NAME

logger = logging.getLogger(__name__)


def get_search_client() -> SearchClient:
    """
    Create and return an Azure AI Search client.

    Uses API key authentication if AZURE_SEARCH_API_KEY is set,
    otherwise falls back to DefaultAzureCredential (managed identity).
    """
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    if not endpoint:
        raise ValueError("AZURE_SEARCH_ENDPOINT environment variable is not set.")

    api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
    if api_key:
        credential = AzureKeyCredential(api_key)
    else:
        credential = DefaultAzureCredential()

    index_name = os.getenv("AZURE_SEARCH_INDEX", INDEX_NAME)
    return SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)


def get_query_embedding(query: str) -> Optional[List[float]]:
    """
    Generate a vector embedding for the search query.

    Returns None if Azure OpenAI is not configured (falls back to keyword search).
    """
    enable_llm = os.getenv("ENABLE_LLM", "false").lower() == "true"
    if not enable_llm:
        return None

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
    if not endpoint or not deployment:
        return None

    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if api_key:
            client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version="2024-02-01")
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-02-01"
            )

        response = client.embeddings.create(input=query, model=deployment)
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Failed to generate query embedding: {e}. Falling back to keyword search.")
        return None


def execute_search(
    query: str,
    entitlement_filter: str,
    search_mode: str = "hybrid",
    top_k: int = 5
) -> List[SearchResult]:
    """
    Execute an Azure AI Search query with the entitlement filter applied.

    IMPORTANT: The entitlement_filter is ALWAYS applied. There is no code
    path in this function that runs an unfiltered search.

    Args:
        query: The user's search query text.
        entitlement_filter: OData filter string from the entitlement filter builder.
                            This MUST be a non-empty string — pass DENY_ALL_FILTER if
                            the user has no entitlements.
        search_mode: 'keyword', 'vector', or 'hybrid'.
        top_k: Maximum number of results to return.

    Returns:
        List of SearchResult objects containing content and citation metadata.
    """
    if not entitlement_filter:
        raise ValueError(
            "entitlement_filter must not be empty. "
            "Use filters.DENY_ALL_FILTER for users with no entitlements."
        )

    search_client = get_search_client()

    # Determine if vector search is available
    query_vector = None
    if search_mode in ("vector", "hybrid"):
        query_vector = get_query_embedding(query)
        if query_vector is None and search_mode == "vector":
            logger.info("Vector search requested but embeddings unavailable — falling back to keyword.")
            search_mode = "keyword"
        elif query_vector is None and search_mode == "hybrid":
            logger.info("Hybrid search requested but embeddings unavailable — falling back to keyword.")
            search_mode = "keyword"

    # Build vector query parameters
    vector_queries = None
    if query_vector is not None:
        vector_queries = [
            VectorizedQuery(
                vector=query_vector,
                k_nearest_neighbors=top_k,
                fields="contentVector"
            )
        ]

    # Execute the search
    # The filter parameter enforces entitlement restrictions on EVERY query.
    try:
        if search_mode == "keyword":
            results = search_client.search(
                search_text=query,
                filter=entitlement_filter,  # Entitlement filter applied here
                select=[
                    "id", "chunkId", "content", "title", "sourceFile",
                    "sourcePage", "partnerId", "clientId", "productLine",
                    "region", "classification"
                ],
                top=top_k
            )
        else:
            # vector or hybrid
            results = search_client.search(
                search_text=query if search_mode == "hybrid" else None,
                filter=entitlement_filter,  # Entitlement filter applied here
                vector_queries=vector_queries,
                select=[
                    "id", "chunkId", "content", "title", "sourceFile",
                    "sourcePage", "partnerId", "clientId", "productLine",
                    "region", "classification"
                ],
                top=top_k
            )

        search_results = []
        for result in results:
            citation = ChunkCitation(
                title=result.get("title", ""),
                sourceFile=result.get("sourceFile", ""),
                sourcePage=result.get("sourcePage"),
                partnerId=result.get("partnerId"),
                clientId=result.get("clientId"),
                productLine=result.get("productLine"),
                region=result.get("region"),
                classification=result.get("classification"),
                score=result.get("@search.score")
            )
            search_results.append(SearchResult(
                chunkId=result.get("chunkId"),
                content=result.get("content", ""),
                citation=citation
            ))

        return search_results

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise

"""
main.py

FastAPI application for the Azure AI Search entitlement filtering demo.

Endpoints:
    GET  /                              - Health check
    GET  /api/users                     - List all demo users
    GET  /api/entitlements/{userId}     - Get entitlement profile for a user
    POST /api/search                    - Entitlement-filtered document search
    POST /api/chat                      - Entitlement-filtered RAG chat (requires Azure OpenAI)

Security model:
    - All search and chat requests require a userId.
    - The entitlement service looks up the user's authorization context.
    - The filter builder converts entitlements to an OData filter.
    - The search layer applies the filter to EVERY query — no exceptions.
    - Unknown users receive deny-by-default (empty results).
    - The LLM only receives chunks returned by the filtered search.

Usage:
    python src/api/main.py
    # API available at http://localhost:8000
    # Interactive docs at http://localhost:8000/docs
"""

import os
import logging
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Allow importing from src/api/ and src/ingestion/
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "ingestion"))

from models import (
    SearchRequest, SearchResponse,
    ChatRequest, ChatResponse,
    SearchResult
)
from entitlements import get_all_users, get_entitlements
from filters import build_entitlement_filter
from search import execute_search

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Azure AI Search Entitlement Filtering Demo",
    description=(
        "Demonstrates metadata-based entitlement filtering in Azure AI Search. "
        "Users only retrieve document chunks they are explicitly authorized to access. "
        "All data is synthetic and for demonstration purposes only."
    ),
    version="1.0.0"
)

# CORS — allow requests from the React frontend during local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Azure AI Search Entitlement Filtering Demo",
        "note": "All data is synthetic. No real users or documents are present."
    }


@app.get("/api/users")
async def list_users():
    """
    List all demo users available in the mock entitlement service.

    Used by the frontend to populate the user selector dropdown.
    """
    users = get_all_users()
    return {"users": [u.model_dump() for u in users]}


@app.get("/api/entitlements/{user_id}")
async def get_user_entitlements(user_id: str):
    """
    Get the full entitlement profile for a specific user.

    Returns 404 if the user is not found (deny-by-default).
    """
    profile = get_entitlements(user_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"User '{user_id}' not found in entitlement service. No access granted."
        )
    return profile.model_dump()


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Execute an entitlement-filtered document search.

    Process:
    1. Look up user entitlements (deny-by-default if not found)
    2. Build OData filter from entitlements
    3. Execute filtered search against Azure AI Search
    4. Return only authorized document chunks

    The generated filter is included in the response for demo transparency.
    """
    logger.info(
        "Search request received (mode=%s, topK=%s, queryLength=%s).",
        request.searchMode,
        request.topK,
        len(request.query or "")
    )

    # Step 1: Look up user entitlements
    entitlements = get_entitlements(request.userId)
    if entitlements is None:
        logger.warning("Unknown user supplied for search request — applying deny-by-default filter.")

    # Step 2: Build entitlement filter (DENY_ALL_FILTER if user is unknown)
    entitlement_filter = build_entitlement_filter(entitlements)

    # Step 3: Check if Azure Search is configured
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    if not endpoint:
        return SearchResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            results=[],
            resultCount=0,
            message=(
                "Azure AI Search is not configured. "
                "Set AZURE_SEARCH_ENDPOINT in your .env file. "
                f"Filter that would be applied: {entitlement_filter}"
            )
        )

    # Step 4: Execute filtered search
    try:
        results = execute_search(
            query=request.query,
            entitlement_filter=entitlement_filter,
            search_mode=request.searchMode,
            top_k=request.topK
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    message = None
    if entitlements is None:
        message = (
            f"User '{request.userId}' was not found in the entitlement service. "
            "No content returned (deny-by-default)."
        )
    elif not results:
        message = (
            "No results found. This may mean the query matched no documents within "
            "your entitlement scope, or the index is empty."
        )

    logger.info("Search completed with %s results.", len(results))

    return SearchResponse(
        userId=request.userId,
        query=request.query,
        filter=entitlement_filter,
        results=results,
        resultCount=len(results),
        message=message
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Entitlement-filtered RAG chat endpoint.

    Process:
    1. Look up user entitlements (deny-by-default if not found)
    2. Build OData filter from entitlements
    3. Execute filtered search to retrieve authorized context chunks
    4. Pass ONLY the filtered chunks to Azure OpenAI for answer generation
    5. Return the answer with source citations

    The LLM only receives content that passed the entitlement filter.
    Unauthorized documents are never sent to the LLM.

    If Azure OpenAI is not configured, returns retrieval results only.
    """
    logger.info(
        "Chat request received (mode=%s, topK=%s, queryLength=%s).",
        request.searchMode,
        request.topK,
        len(request.query or "")
    )

    # Step 1: Look up entitlements
    entitlements = get_entitlements(request.userId)
    if entitlements is None:
        logger.warning("Unknown user supplied for chat request — applying deny-by-default filter.")

    # Step 2: Build entitlement filter
    entitlement_filter = build_entitlement_filter(entitlements)

    # Step 3: Check if Azure Search is configured
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    if not endpoint:
        return ChatResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            answer=None,
            sources=[],
            message="Azure AI Search is not configured. Set AZURE_SEARCH_ENDPOINT in your .env file."
        )

    # Step 4: Execute filtered retrieval
    try:
        sources = execute_search(
            query=request.query,
            entitlement_filter=entitlement_filter,
            search_mode=request.searchMode,
            top_k=request.topK
        )
    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")

    if entitlements is None:
        return ChatResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            answer=None,
            sources=[],
            message=(
                f"User '{request.userId}' was not found in the entitlement service. "
                "No content returned (deny-by-default)."
            )
        )

    if not sources:
        return ChatResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            answer=None,
            sources=[],
            message="No documents found within your entitlement scope for this query."
        )

    # Step 5: Generate answer with Azure OpenAI (if configured)
    enable_llm = os.getenv("ENABLE_LLM", "false").lower() == "true"
    openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "")

    if not enable_llm or not openai_endpoint or not chat_deployment:
        return ChatResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            answer=None,
            sources=sources,
            message=(
                "Answer generation is disabled because Azure OpenAI is not configured. "
                "Retrieval results are shown below."
            )
        )

    # Build context from ONLY the filtered chunks
    # Unauthorized documents never reach this point
    context_parts = []
    for i, source in enumerate(sources, start=1):
        context_parts.append(
            f"[Document {i}: {source.citation.title} — {source.citation.sourceFile}]\n"
            f"{source.content}"
        )
    context = "\n\n---\n\n".join(context_parts)

    system_prompt = (
        "You are a helpful assistant. Answer the user's question using ONLY the provided "
        "document context. Do not use any information outside of the provided context. "
        "If the context does not contain enough information to answer, say so clearly. "
        "Cite document titles when referring to specific information. "
        "All data is synthetic and for demonstration purposes only."
    )

    user_message = f"Context:\n{context}\n\nQuestion: {request.query}"

    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if api_key:
            llm_client = AzureOpenAI(
                azure_endpoint=openai_endpoint,
                api_key=api_key,
                api_version="2024-02-01"
            )
        else:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            llm_client = AzureOpenAI(
                azure_endpoint=openai_endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-02-01"
            )

        completion = llm_client.chat.completions.create(
            model=chat_deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=1000,
            temperature=0.3
        )
        answer = completion.choices[0].message.content

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        answer = None
        return ChatResponse(
            userId=request.userId,
            query=request.query,
            filter=entitlement_filter,
            answer=None,
            sources=sources,
            message=f"Answer generation failed: {str(e)}. Retrieval results are shown below."
        )

    return ChatResponse(
        userId=request.userId,
        query=request.query,
        filter=entitlement_filter,
        answer=answer,
        sources=sources
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("main:app", host=host, port=port, reload=True)

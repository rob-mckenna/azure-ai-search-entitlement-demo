"""
embeddings.py

Generates text embeddings using Azure OpenAI.
Embeddings are used for vector and hybrid search in Azure AI Search.

If Azure OpenAI is not configured (ENABLE_LLM=false or missing endpoint),
this module returns None for all embeddings. The ingestion pipeline
will skip the contentVector field in that case, and the index will
operate in keyword-only mode.
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def get_embedding_client():
    """
    Create an Azure OpenAI client for embedding generation.

    Returns None if Azure OpenAI is not configured.
    """
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
    enable_llm = os.getenv("ENABLE_LLM", "false").lower() == "true"

    if not enable_llm or not endpoint or not deployment:
        logger.info("Azure OpenAI not configured — embeddings disabled, using keyword search only.")
        return None

    try:
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        # Prefer API key authentication if provided, otherwise use managed identity
        api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        if api_key:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version="2024-02-01"
            )
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
        return client
    except Exception as e:
        logger.warning(f"Failed to create Azure OpenAI client: {e}. Embeddings disabled.")
        return None


def generate_embedding(text: str, client=None, deployment: str = None) -> Optional[List[float]]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: The text to embed.
        client: An AzureOpenAI client instance (from get_embedding_client()).
        deployment: The embedding model deployment name.

    Returns:
        A list of floats representing the embedding, or None if not available.
    """
    if client is None:
        return None

    if not deployment:
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

    if not deployment:
        return None

    try:
        # Truncate very long text to avoid token limit errors
        truncated = text[:8000] if len(text) > 8000 else text
        response = client.embeddings.create(input=truncated, model=deployment)
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None


def generate_embeddings_batch(
    texts: List[str],
    client=None,
    deployment: str = None,
    batch_size: int = 16
) -> List[Optional[List[float]]]:
    """
    Generate embeddings for a list of texts in batches.

    Args:
        texts: List of text strings to embed.
        client: An AzureOpenAI client instance.
        deployment: The embedding model deployment name.
        batch_size: Number of texts to embed per API call.

    Returns:
        List of embedding vectors (or None for each text if embeddings unavailable).
    """
    if client is None:
        return [None] * len(texts)

    if not deployment:
        deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")

    results = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            truncated_batch = [t[:8000] if len(t) > 8000 else t for t in batch]
            response = client.embeddings.create(input=truncated_batch, model=deployment)
            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            results.extend([item.embedding for item in sorted_data])
        except Exception as e:
            logger.warning(f"Failed to generate batch embeddings: {e}. Using None for this batch.")
            results.extend([None] * len(batch))

    return results

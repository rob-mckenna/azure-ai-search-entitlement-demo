"""
ingest_documents.py

Main ingestion pipeline for the entitlement filtering demo.

Pipeline steps:
1. Load document metadata from src/ingestion/metadata.json
2. Extract text from PDFs in sample-docs/
3. Chunk documents using the chunking module
4. Attach entitlement metadata to every chunk
5. Generate embeddings (if Azure OpenAI is configured)
6. Create the Azure AI Search index if it doesn't exist
7. Upload chunks to Azure AI Search

Usage:
    python src/ingestion/ingest_documents.py

Environment variables required:
    AZURE_SEARCH_ENDPOINT  - Azure AI Search endpoint URL
    AZURE_SEARCH_API_KEY   - API key (or use managed identity via DefaultAzureCredential)

Optional:
    AZURE_OPENAI_ENDPOINT           - Azure OpenAI endpoint (for vector embeddings)
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT - Embedding model deployment name
    ENABLE_LLM=true                 - Enable embedding generation
"""

import os
import sys
import json
import hashlib
import logging
from pathlib import Path

# Allow running from repository root or from src/ingestion/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient

from chunking import chunk_pages
from embeddings import get_embedding_client, generate_embeddings_batch
from index_schema import build_index_schema, INDEX_NAME

# Load .env file if present
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent
SAMPLE_DOCS_DIR = REPO_ROOT / "sample-docs"
METADATA_FILE = Path(__file__).parent / "metadata.json"


def get_search_credential():
    """Return an Azure AI Search credential (API key or managed identity)."""
    api_key = os.getenv("AZURE_SEARCH_API_KEY", "")
    if api_key:
        return AzureKeyCredential(api_key)
    logger.info("No API key found — using DefaultAzureCredential (managed identity).")
    return DefaultAzureCredential()


def ensure_index_exists(index_client: SearchIndexClient, recreate: bool = False):
    """Create the search index if it doesn't already exist.

    Args:
        recreate: If True, delete and recreate the index even if it already exists.
                  Use this when the index schema has changed (e.g. vector dimensions).
    """
    existing = [idx.name for idx in index_client.list_indexes()]
    if INDEX_NAME in existing:
        if not recreate:
            logger.info(f"Index '{INDEX_NAME}' already exists.")
            return
        logger.info(f"Deleting existing index '{INDEX_NAME}' for recreation...")
        index_client.delete_index(INDEX_NAME)
        logger.info(f"Index '{INDEX_NAME}' deleted.")

    logger.info(f"Creating index '{INDEX_NAME}'...")
    index = build_index_schema()
    index_client.create_index(index)
    logger.info(f"Index '{INDEX_NAME}' created successfully.")


def extract_text_from_pdf(pdf_path: Path) -> list[str]:
    """
    Extract text from a PDF file, returning one string per page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of page text strings (one per page).
    """
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(pdf_path))
        pages = []
        for page in reader.pages:
            text = page.extract_text() or ""
            pages.append(text.strip())
        return pages
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return []


def make_chunk_id(document_id: str, chunk_index: int) -> str:
    """Generate a stable, unique chunk ID."""
    raw = f"{document_id}-chunk-{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def build_search_documents(
    metadata_entry: dict,
    pages: list[str],
    embeddings: list
) -> list[dict]:
    """
    Build Azure AI Search document objects from a PDF's pages and metadata.

    Each chunk gets:
    - All entitlement metadata fields (partnerId, clientId, etc.)
    - The content text
    - An embedding vector (if available)
    - A stable unique ID

    Args:
        metadata_entry: Document metadata from metadata.json
        pages: List of page text strings from the PDF
        embeddings: List of embedding vectors (or None values)

    Returns:
        List of dicts ready to upload to Azure AI Search
    """
    document_id = metadata_entry["documentId"]
    chunks = chunk_pages(pages)

    search_docs = []
    for i, chunk_data in enumerate(chunks):
        chunk_id = make_chunk_id(document_id, i)

        doc = {
            "id": chunk_id,
            "documentId": document_id,
            "chunkId": f"chunk-{i}",
            "title": metadata_entry["title"],
            "content": chunk_data["text"],
            "sourceFile": metadata_entry["sourceFile"],
            "sourcePage": chunk_data["page"],
            "partnerId": metadata_entry["partnerId"],
            "clientId": metadata_entry["clientId"],
            "productLine": metadata_entry["productLine"],
            "region": metadata_entry["region"],
            "classification": metadata_entry["classification"],
            "allowedEntitlements": metadata_entry["allowedEntitlements"],
        }

        # Add embedding vector if available
        if i < len(embeddings) and embeddings[i] is not None:
            doc["contentVector"] = embeddings[i]

        search_docs.append(doc)

    return search_docs


def ingest_all_documents(recreate_index: bool = False):
    """Main ingestion function — processes all documents in metadata.json."""
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    if not endpoint:
        logger.error("AZURE_SEARCH_ENDPOINT is not set. Please configure your .env file.")
        sys.exit(1)

    credential = get_search_credential()
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    search_client = SearchClient(
        endpoint=endpoint,
        index_name=INDEX_NAME,
        credential=credential
    )

    # Step 1: Ensure the index exists (optionally recreate it)
    ensure_index_exists(index_client, recreate=recreate_index)

    # Step 2: Load document metadata
    if not METADATA_FILE.exists():
        logger.error(f"Metadata file not found: {METADATA_FILE}")
        sys.exit(1)

    with open(METADATA_FILE, "r") as f:
        metadata_list = json.load(f)

    logger.info(f"Loaded metadata for {len(metadata_list)} documents.")

    # Step 3: Initialize embedding client (None if Azure OpenAI not configured)
    embedding_client = get_embedding_client()
    if embedding_client:
        logger.info("Azure OpenAI configured — embeddings will be generated.")
    else:
        logger.info("Azure OpenAI not configured — running in keyword-only mode.")

    total_chunks = 0
    failed_docs = []

    for metadata_entry in metadata_list:
        source_file = metadata_entry["sourceFile"]
        pdf_path = SAMPLE_DOCS_DIR / source_file

        if not pdf_path.exists():
            logger.warning(
                f"PDF not found: {pdf_path}. "
                f"Run 'python src/ingestion/generate_sample_pdfs.py' first."
            )
            failed_docs.append(source_file)
            continue

        logger.info(f"Processing: {source_file}")

        # Step 4: Extract text from PDF
        pages = extract_text_from_pdf(pdf_path)
        if not pages:
            logger.warning(f"No text extracted from {source_file}. Skipping.")
            failed_docs.append(source_file)
            continue

        # Step 5: Chunk the pages
        chunks = chunk_pages(pages)
        chunk_texts = [c["text"] for c in chunks]
        logger.info(f"  → {len(chunk_texts)} chunks from {len(pages)} pages")

        # Step 6: Generate embeddings (if configured)
        embeddings = generate_embeddings_batch(chunk_texts, client=embedding_client)

        # Step 7: Build search documents
        search_docs = build_search_documents(metadata_entry, pages, embeddings)

        # Step 8: Upload to Azure AI Search in batches
        batch_size = 50
        for i in range(0, len(search_docs), batch_size):
            batch = search_docs[i:i + batch_size]
            try:
                results = search_client.upload_documents(documents=batch)
                succeeded = sum(1 for r in results if r.succeeded)
                failed = len(results) - succeeded
                if failed > 0:
                    logger.warning(f"  → {failed} chunks failed to upload for {source_file}")
                logger.info(f"  → Uploaded {succeeded}/{len(batch)} chunks")
            except Exception as e:
                logger.error(f"  → Failed to upload batch for {source_file}: {e}")
                failed_docs.append(source_file)
                break

        total_chunks += len(search_docs)

    logger.info(f"\n{'='*60}")
    logger.info(f"Ingestion complete.")
    logger.info(f"Total chunks uploaded: {total_chunks}")
    if failed_docs:
        logger.warning(f"Failed documents: {failed_docs}")
    else:
        logger.info("All documents ingested successfully.")
    logger.info(f"Index: {INDEX_NAME}")
    logger.info(f"{'='*60}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest documents into Azure AI Search.")
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Delete and recreate the search index before ingesting (use when schema has changed).",
    )
    args = parser.parse_args()
    ingest_all_documents(recreate_index=args.recreate_index)

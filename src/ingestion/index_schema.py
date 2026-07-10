"""
index_schema.py

Defines the Azure AI Search index schema for the entitlement filtering demo.

Index name: entitlement-demo-index

Key design decisions:
- content is searchable (full-text) and retrievable
- partnerId, clientId, productLine, region, classification, allowedEntitlements are filterable
- contentVector supports vector search when embeddings are configured
- All metadata fields are retrievable for citation and debugging
"""

from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
)

INDEX_NAME = "entitlement-demo-index"
VECTOR_DIMENSIONS = 1536  # text-embedding-3-small dimensions


def build_index_schema() -> SearchIndex:
    """
    Build the Azure AI Search index definition.

    This index is designed to support:
    - Full-text (keyword) search on the content field
    - Vector search on the contentVector field (when embeddings are available)
    - Hybrid search combining both
    - Metadata filtering by entitlement fields at query time
    """

    fields = [
        # Primary key — unique per document chunk
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
            retrievable=True
        ),

        # Document-level identifier
        SimpleField(
            name="documentId",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Chunk identifier within the document
        SimpleField(
            name="chunkId",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Document title — used for citations
        SimpleField(
            name="title",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Main content field — full-text searchable
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            retrievable=True,
            analyzer_name="en.lucene"
        ),

        # Source file name — used for citations
        SimpleField(
            name="sourceFile",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Source page number — used for citations
        SimpleField(
            name="sourcePage",
            type=SearchFieldDataType.Int32,
            filterable=True,
            retrievable=True
        ),

        # --- Entitlement metadata fields (filterable) ---

        # Partner identifier — e.g. PartnerAlpha, PartnerBeta
        SimpleField(
            name="partnerId",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Client identifier — e.g. ClientNorth, ClientSouth, ClientEast
        SimpleField(
            name="clientId",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Product line identifier — e.g. ProductLineA, ProductLineB
        SimpleField(
            name="productLine",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Region identifier — e.g. RegionOne, RegionTwo
        SimpleField(
            name="region",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Classification — e.g. RestrictedDemo, PublicDemoReference
        SimpleField(
            name="classification",
            type=SearchFieldDataType.String,
            filterable=True,
            retrievable=True
        ),

        # Collection of all entitlement tags on this document
        # This field supports search.in() filter expressions
        SearchField(
            name="allowedEntitlements",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            retrievable=True
        ),

        # --- Vector search field ---
        # Populated by the embeddings pipeline when Azure OpenAI is configured
        SearchField(
            name="contentVector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            retrievable=False,  # Don't return raw vectors to clients
            vector_search_dimensions=VECTOR_DIMENSIONS,
            vector_search_profile_name="entitlement-vector-profile"
        ),
    ]

    # Vector search configuration using HNSW algorithm
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="entitlement-hnsw")
        ],
        profiles=[
            VectorSearchProfile(
                name="entitlement-vector-profile",
                algorithm_configuration_name="entitlement-hnsw"
            )
        ]
    )

    # Semantic search configuration for better ranking
    semantic_config = SemanticConfiguration(
        name="entitlement-semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="content")],
            keywords_fields=[
                SemanticField(field_name="title"),
                SemanticField(field_name="partnerId"),
                SemanticField(field_name="clientId"),
            ]
        )
    )
    semantic_search = SemanticSearch(configurations=[semantic_config])

    return SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )

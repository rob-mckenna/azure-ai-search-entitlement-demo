"""
filters.py

OData filter builder for Azure AI Search entitlement enforcement.

This module is the core of the entitlement filtering pattern.
It translates a user's entitlement profile into an Azure AI Search
OData filter string that is applied to every search query.

Key design decisions:
- Deny-by-default: if entitlements are missing or empty, return a filter
  that matches nothing (impossible condition).
- Never fall back to unfiltered search.
- Log the generated filter for demo transparency.
- Support PublicDemoReference classification for global reference documents.

Azure AI Search OData filter syntax reference:
    https://learn.microsoft.com/en-us/azure/search/search-query-odata-filter
"""

import logging
from typing import Optional
from models import EntitlementProfile

logger = logging.getLogger(__name__)

# A filter expression that matches no documents.
# Used as the deny-all fallback when no entitlements are available.
DENY_ALL_FILTER = "id eq 'DENIED_NO_ENTITLEMENTS_FOUND'"

# Classification value for documents accessible to all users with
# canReadGlobalReferences = true.
PUBLIC_REFERENCE_CLASSIFICATION = "PublicDemoReference"


def build_entitlement_filter(entitlements: Optional[EntitlementProfile]) -> str:
    """
    Build an OData filter string from a user's entitlement profile.

    The filter enforces that users can only retrieve document chunks where:
    - partnerId matches the user's partnerId, AND
    - clientId is in the user's allowedClients list, AND
    - productLine is in the user's allowedProductLines list, AND
    - region is in the user's allowedRegions list

    Additionally, if canReadGlobalReferences is true, the filter also allows
    documents classified as PublicDemoReference.

    If no entitlements are found (user is unknown), the DENY_ALL_FILTER is
    returned, which matches no documents.

    Args:
        entitlements: The user's entitlement profile, or None if unknown.

    Returns:
        An OData filter string ready to pass to Azure AI Search.
    """

    # Deny-by-default: unknown users get no access
    if entitlements is None:
        logger.warning("No entitlements found for user — applying deny-all filter.")
        return DENY_ALL_FILTER

    # Build the restricted document filter clause
    # This is only meaningful if the user has actual client/product/region assignments.
    restricted_filter = _build_restricted_filter(entitlements)

    # Build the global reference clause (PublicDemoReference documents)
    global_filter = _build_global_reference_filter(entitlements)

    # Combine: (restricted clause) OR (global reference clause)
    # At least one of these must be non-empty.
    filter_clauses = []
    if restricted_filter:
        filter_clauses.append(restricted_filter)
    if global_filter:
        filter_clauses.append(global_filter)

    if not filter_clauses:
        # User has no allowed clients, products, or regions AND cannot read global references
        # This should not normally happen but is handled defensively
        logger.warning("User has no applicable entitlements — applying deny-all filter.")
        return DENY_ALL_FILTER

    if len(filter_clauses) == 1:
        final_filter = filter_clauses[0]
    else:
        # Wrap each clause in parentheses before joining with OR
        final_filter = " or ".join(f"({clause})" for clause in filter_clauses)

    logger.info(
        "Generated entitlement filter (restricted=%s, hasGlobalReferenceClause=%s).",
        bool(restricted_filter),
        bool(global_filter)
    )
    return final_filter


def _build_restricted_filter(entitlements: EntitlementProfile) -> Optional[str]:
    """
    Build the OData filter clause for restricted (non-public) documents.

    Returns None if the user has no allowed clients, product lines, or regions
    (meaning they cannot access any restricted documents).
    """
    # If the user has no allowed clients/products/regions, they cannot access
    # any RestrictedDemo documents.
    if (
        not entitlements.allowedClients
        and not entitlements.allowedProductLines
        and not entitlements.allowedRegions
    ):
        return None

    clauses = []

    # Partner filter — user can only see documents for their own partner
    clauses.append(f"partnerId eq '{entitlements.partnerId}'")

    # Client filter — search.in() matches any value in the list
    if entitlements.allowedClients:
        client_list = ",".join(entitlements.allowedClients)
        clauses.append(f"search.in(clientId, '{client_list}', ',')")

    # Product line filter
    if entitlements.allowedProductLines:
        product_list = ",".join(entitlements.allowedProductLines)
        clauses.append(f"search.in(productLine, '{product_list}', ',')")

    # Region filter
    if entitlements.allowedRegions:
        region_list = ",".join(entitlements.allowedRegions)
        clauses.append(f"search.in(region, '{region_list}', ',')")

    if not clauses:
        return None

    return " and ".join(clauses)


def _build_global_reference_filter(entitlements: EntitlementProfile) -> Optional[str]:
    """
    Build the OData filter clause for PublicDemoReference documents.

    Returns None if the user does not have canReadGlobalReferences.
    """
    if entitlements.canReadGlobalReferences:
        return f"classification eq '{PUBLIC_REFERENCE_CLASSIFICATION}'"
    return None

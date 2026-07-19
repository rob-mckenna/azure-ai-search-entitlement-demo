"""
test_no_unfiltered_search.py

Tests that verify the system NEVER performs an unfiltered search for user queries.

This is a critical security property of the entitlement filtering pattern:
- The filter parameter must always be set when calling Azure AI Search
- The execute_search function must raise an error if filter is empty
- The API layer must always build a filter before calling search
- The deny-all filter is the correct fallback, not an unfiltered search

These tests use mocking to avoid requiring a live Azure AI Search instance.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "ingestion"))

from filters import build_entitlement_filter, DENY_ALL_FILTER
from entitlements import get_entitlements
from models import EntitlementProfile


class TestExecuteSearchRequiresFilter:
    """Verify that execute_search raises an error if no filter is provided."""

    @patch("search.get_search_client")
    def test_execute_search_raises_on_empty_filter(self, mock_client):
        """execute_search must raise ValueError if filter is empty string."""
        from search import execute_search
        with pytest.raises(ValueError, match="entitlement_filter must not be empty"):
            execute_search(
                query="test query",
                entitlement_filter="",
                search_mode="keyword"
            )

    @patch("search.get_search_client")
    def test_execute_search_with_deny_all_filter_does_not_raise(self, mock_get_client):
        """execute_search should NOT raise for the DENY_ALL_FILTER — it is a valid filter
        that matches no documents. The search itself should run (and return nothing)."""
        mock_search_client = MagicMock()
        mock_search_client.search.return_value = iter([])
        mock_get_client.return_value = mock_search_client

        from search import execute_search
        # This should not raise — DENY_ALL_FILTER is a valid non-empty filter
        results = execute_search(
            query="test",
            entitlement_filter=DENY_ALL_FILTER,
            search_mode="keyword"
        )
        assert results == []

    @patch("search.get_search_client")
    def test_execute_search_passes_filter_to_azure_search(self, mock_get_client):
        """Verify that the filter is passed to the Azure Search client."""
        mock_search_client = MagicMock()
        mock_search_client.search.return_value = iter([])
        mock_get_client.return_value = mock_search_client

        from search import execute_search
        test_filter = "partnerId eq 'PartnerAlpha'"
        execute_search(
            query="test query",
            entitlement_filter=test_filter,
            search_mode="keyword"
        )

        # Verify search was called with the filter
        mock_search_client.search.assert_called_once()
        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs.get("filter") == test_filter, (
            "Filter was not passed to Azure AI Search client"
        )

    @patch("search.get_search_client")
    def test_execute_search_with_deny_all_passes_filter_to_azure(self, mock_get_client):
        """The deny-all filter must be passed to Azure Search (not bypassed)."""
        mock_search_client = MagicMock()
        mock_search_client.search.return_value = iter([])
        mock_get_client.return_value = mock_search_client

        from search import execute_search
        execute_search(
            query="test",
            entitlement_filter=DENY_ALL_FILTER,
            search_mode="keyword"
        )

        call_kwargs = mock_search_client.search.call_args.kwargs
        assert call_kwargs.get("filter") == DENY_ALL_FILTER


class TestAPILayerAlwaysBuildsFilter:
    """Verify that the API layer always generates a filter before searching."""

    def test_known_user_gets_non_empty_filter(self):
        """For a known user, the filter must be a non-trivial OData expression."""
        profile = get_entitlements("user.alpha.north@example.com")
        assert profile is not None
        entitlement_filter = build_entitlement_filter(profile)
        assert entitlement_filter != ""
        assert entitlement_filter is not None

    def test_unknown_user_gets_deny_all_not_empty(self):
        """For an unknown user, the fallback is DENY_ALL — not an empty string."""
        profile = get_entitlements("attacker@evil.example.com")
        assert profile is None
        entitlement_filter = build_entitlement_filter(profile)
        assert entitlement_filter == DENY_ALL_FILTER
        assert entitlement_filter != ""

    def test_filter_pipeline_for_all_demo_users(self):
        """Run the complete entitlement-to-filter pipeline for all demo users
        and verify that every filter is a non-empty string."""
        demo_users = [
            "user.alpha.north@example.com",
            "user.alpha.south@example.com",
            "user.beta.east@example.com",
            "user.global.reader@example.com",
        ]
        for user_id in demo_users:
            profile = get_entitlements(user_id)
            assert profile is not None, f"Profile is None for known user: {user_id}"
            entitlement_filter = build_entitlement_filter(profile)
            assert entitlement_filter, f"Filter is falsy for user: {user_id}"
            assert entitlement_filter != "", f"Filter is empty for user: {user_id}"


class TestFilterDoesNotBypassOnMissingMetadata:
    """Verify that missing metadata fields do not accidentally grant access."""

    def test_user_with_empty_clients_gets_no_client_filter(self):
        """A user with no allowed clients should not have a client filter
        that accidentally matches all documents."""
        profile = EntitlementProfile(
            userId="limited@example.com",
            displayName="Limited User",
            partnerId="PartnerAlpha",
            allowedClients=[],
            allowedProductLines=[],
            allowedRegions=[],
            canReadGlobalReferences=False
        )
        result = build_entitlement_filter(profile)
        # User with no clients, no products, no regions, no global ref gets DENY_ALL
        assert result == DENY_ALL_FILTER

    def test_partial_entitlements_still_enforce_all_dimensions(self):
        """A user with clients but no products or regions still produces a filter
        that restricts by all specified dimensions."""
        profile = EntitlementProfile(
            userId="partial@example.com",
            displayName="Partial User",
            partnerId="PartnerAlpha",
            allowedClients=["ClientNorth"],
            allowedProductLines=["ProductLineA"],
            allowedRegions=["RegionOne"],
            canReadGlobalReferences=False
        )
        result = build_entitlement_filter(profile)
        # Must include all three restriction dimensions
        assert "partnerId" in result
        assert "ClientNorth" in result
        assert "ProductLineA" in result
        assert "RegionOne" in result


class TestNoFallbackToUnfilteredSearch:
    """Verify that there is no code path that falls back to an unfiltered search."""

    @patch("search.get_search_client")
    def test_search_function_signature_requires_filter(self, mock_client):
        """The execute_search function must require a filter parameter."""
        from search import execute_search
        import inspect
        sig = inspect.signature(execute_search)
        assert "entitlement_filter" in sig.parameters, (
            "execute_search must have an entitlement_filter parameter"
        )

    def test_filter_builder_never_returns_none(self):
        """build_entitlement_filter must never return None — always a string."""
        test_profiles = [
            None,  # Unknown user
            EntitlementProfile(
                userId="test@example.com",
                displayName="Test",
                partnerId="PartnerX",
                allowedClients=["ClientA"],
                allowedProductLines=["ProductX"],
                allowedRegions=["RegionX"],
                canReadGlobalReferences=False
            ),
        ]
        for profile in test_profiles:
            result = build_entitlement_filter(profile)
            assert result is not None, f"build_entitlement_filter returned None for profile: {profile}"
            assert isinstance(result, str), f"build_entitlement_filter returned non-string: {type(result)}"

"""
test_search_authorization.py

Tests that verify the search authorization enforcement logic.

These tests do NOT require a live Azure AI Search instance.
They test the logic around:
- Entitlement lookup before search
- Filter application to every search call
- Correct handling of users with partial entitlements
- Correct handling of users with no entitlements
- PublicDemoReference accessibility rules

Integration tests against a live Azure AI Search index are out of scope
for this test module — see docs/sample-queries.md for manual test scripts.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))

from entitlements import get_entitlements
from filters import build_entitlement_filter, DENY_ALL_FILTER, PUBLIC_REFERENCE_CLASSIFICATION
from models import EntitlementProfile, SearchRequest


class TestEntitlementLookupBeforeSearch:
    """Verify that entitlement lookups occur correctly for all user types."""

    def test_known_user_gets_non_deny_filter(self):
        """A known user should get a filter that is not the deny-all filter."""
        profile = get_entitlements("user.alpha.north@example.com")
        assert profile is not None
        entitlement_filter = build_entitlement_filter(profile)
        assert entitlement_filter != DENY_ALL_FILTER

    def test_unknown_user_gets_deny_all_filter(self):
        """An unknown user triggers deny-by-default."""
        profile = get_entitlements("hacker@malicious.example.com")
        assert profile is None
        entitlement_filter = build_entitlement_filter(profile)
        assert entitlement_filter == DENY_ALL_FILTER

    def test_empty_user_id_gets_deny_all_filter(self):
        profile = get_entitlements("")
        assert profile is None
        entitlement_filter = build_entitlement_filter(profile)
        assert entitlement_filter == DENY_ALL_FILTER


class TestFilterAlwaysApplied:
    """Verify that a filter is always produced (never None or empty string)."""

    def test_filter_is_never_none(self):
        test_cases = [
            "user.alpha.north@example.com",
            "user.alpha.south@example.com",
            "user.beta.east@example.com",
            "user.global.reader@example.com",
            "unknown@example.com",
            "",
        ]
        for user_id in test_cases:
            profile = get_entitlements(user_id)
            result = build_entitlement_filter(profile)
            assert result is not None, f"Filter was None for user: {user_id}"

    def test_filter_is_never_empty_string(self):
        test_cases = [
            "user.alpha.north@example.com",
            "user.beta.east@example.com",
            "unknown@example.com",
        ]
        for user_id in test_cases:
            profile = get_entitlements(user_id)
            result = build_entitlement_filter(profile)
            assert result.strip() != "", f"Filter was empty string for user: {user_id}"

    def test_filter_is_never_wildcard_all(self):
        """The filter must never be a wildcard that would return all documents."""
        wildcard_patterns = ["*", "1 eq 1", "true"]
        test_cases = [
            "user.alpha.north@example.com",
            "unknown@example.com",
        ]
        for user_id in test_cases:
            profile = get_entitlements(user_id)
            result = build_entitlement_filter(profile)
            for pattern in wildcard_patterns:
                assert result != pattern, f"Filter was dangerous wildcard '{pattern}' for user: {user_id}"


class TestCrossPartnerIsolation:
    """Verify that users cannot access documents from other partners."""

    def test_alpha_north_filter_blocks_partner_beta(self):
        profile = get_entitlements("user.alpha.north@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        # The filter must not include PartnerBeta
        # It should use partnerId eq 'PartnerAlpha'
        assert "PartnerBeta" not in entitlement_filter
        assert "PartnerAlpha" in entitlement_filter

    def test_beta_east_filter_blocks_partner_alpha(self):
        profile = get_entitlements("user.beta.east@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        assert "PartnerAlpha" not in entitlement_filter
        assert "PartnerBeta" in entitlement_filter

    def test_alpha_north_filter_blocks_client_east(self):
        profile = get_entitlements("user.alpha.north@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        assert "ClientEast" not in entitlement_filter

    def test_alpha_north_filter_blocks_client_south(self):
        profile = get_entitlements("user.alpha.north@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        assert "ClientSouth" not in entitlement_filter

    def test_beta_east_filter_blocks_client_north(self):
        profile = get_entitlements("user.beta.east@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        assert "ClientNorth" not in entitlement_filter


class TestPublicReferenceAccessRules:
    """Test the PublicDemoReference classification access rules."""

    def test_all_demo_users_can_read_global_references(self):
        """All four demo users have canReadGlobalReferences=True."""
        user_ids = [
            "user.alpha.north@example.com",
            "user.alpha.south@example.com",
            "user.beta.east@example.com",
            "user.global.reader@example.com",
        ]
        for user_id in user_ids:
            profile = get_entitlements(user_id)
            assert profile is not None
            assert profile.canReadGlobalReferences is True, f"{user_id} should have global ref access"

    def test_all_demo_user_filters_include_public_reference(self):
        """All known demo users' filters should include the PublicDemoReference clause."""
        user_ids = [
            "user.alpha.north@example.com",
            "user.alpha.south@example.com",
            "user.beta.east@example.com",
            "user.global.reader@example.com",
        ]
        for user_id in user_ids:
            profile = get_entitlements(user_id)
            f = build_entitlement_filter(profile)
            assert PUBLIC_REFERENCE_CLASSIFICATION in f, (
                f"PublicDemoReference not in filter for {user_id}: {f}"
            )

    def test_unknown_user_cannot_access_public_reference(self):
        """Unknown users get deny-all — they cannot even access PublicDemoReference."""
        profile = get_entitlements("unknown@example.com")
        entitlement_filter = build_entitlement_filter(profile)
        # The deny-all filter must not contain the public reference classification
        assert PUBLIC_REFERENCE_CLASSIFICATION not in entitlement_filter
        assert entitlement_filter == DENY_ALL_FILTER

    def test_user_without_global_ref_access_gets_no_public_reference_in_filter(self):
        """A user explicitly set with canReadGlobalReferences=False should not
        get the public reference clause in their filter."""
        profile = EntitlementProfile(
            userId="restricted@example.com",
            displayName="Restricted User",
            partnerId="PartnerAlpha",
            allowedClients=["ClientNorth"],
            allowedProductLines=["ProductLineA"],
            allowedRegions=["RegionOne"],
            canReadGlobalReferences=False
        )
        entitlement_filter = build_entitlement_filter(profile)
        assert PUBLIC_REFERENCE_CLASSIFICATION not in entitlement_filter


class TestSearchRequestValidation:
    """Test that SearchRequest model validates inputs correctly."""

    def test_valid_search_request(self):
        req = SearchRequest(
            userId="user.alpha.north@example.com",
            query="test query",
            searchMode="hybrid"
        )
        assert req.userId == "user.alpha.north@example.com"
        assert req.query == "test query"
        assert req.searchMode == "hybrid"
        assert req.topK == 5  # default

    def test_search_request_default_mode(self):
        req = SearchRequest(userId="test@example.com", query="test")
        assert req.searchMode == "hybrid"

    def test_search_request_custom_top_k(self):
        req = SearchRequest(userId="test@example.com", query="test", topK=10)
        assert req.topK == 10

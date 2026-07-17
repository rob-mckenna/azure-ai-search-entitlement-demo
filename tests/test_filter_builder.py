"""
test_filter_builder.py

Tests for the OData filter builder (src/api/filters.py).

Verifies:
- Correct OData filter strings are generated for known users
- Unknown users get the deny-all filter
- Global reference filter is included when canReadGlobalReferences is True
- Users with no allowed clients/products/regions get deny-all or global-only filter
- Filter syntax is valid OData
- search.in() expressions are constructed correctly
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))

from filters import build_entitlement_filter, DENY_ALL_FILTER, PUBLIC_REFERENCE_CLASSIFICATION
from models import EntitlementProfile


def make_profile(**kwargs) -> EntitlementProfile:
    """Helper to create a test EntitlementProfile with default values."""
    defaults = {
        "userId": "test@example.com",
        "displayName": "Test User",
        "partnerId": "PartnerTest",
        "allowedClients": ["ClientTest"],
        "allowedProductLines": ["ProductLineTest"],
        "allowedRegions": ["RegionTest"],
        "canReadGlobalReferences": False,
    }
    defaults.update(kwargs)
    return EntitlementProfile(**defaults)


class TestDenyAllFilter:
    """Tests for deny-by-default behavior."""

    def test_none_entitlements_returns_deny_all(self):
        """Unknown users (None entitlement) get the deny-all filter."""
        result = build_entitlement_filter(None)
        assert result == DENY_ALL_FILTER

    def test_deny_all_filter_format(self):
        """The deny-all filter must be a valid non-empty string."""
        assert isinstance(DENY_ALL_FILTER, str)
        assert len(DENY_ALL_FILTER) > 0

    def test_global_reader_with_no_restricted_access_gets_global_filter(self):
        """A user with no clients/products/regions but canReadGlobalReferences=True
        gets a filter for PublicDemoReference only (not deny-all)."""
        profile = make_profile(
            allowedClients=[],
            allowedProductLines=[],
            allowedRegions=[],
            canReadGlobalReferences=True
        )
        result = build_entitlement_filter(profile)
        assert result != DENY_ALL_FILTER
        assert PUBLIC_REFERENCE_CLASSIFICATION in result

    def test_user_with_no_entitlements_and_no_global_access_gets_deny_all(self):
        """A user with no clients, no products, no regions, and no global reference access
        should get the deny-all filter."""
        profile = make_profile(
            allowedClients=[],
            allowedProductLines=[],
            allowedRegions=[],
            canReadGlobalReferences=False
        )
        result = build_entitlement_filter(profile)
        assert result == DENY_ALL_FILTER


class TestPartnerFilter:
    """Tests for partner ID filtering."""

    def test_partner_id_included_in_filter(self):
        profile = make_profile(partnerId="PartnerAlpha")
        result = build_entitlement_filter(profile)
        assert "partnerId eq 'PartnerAlpha'" in result

    def test_different_partner_id_in_filter(self):
        profile = make_profile(partnerId="PartnerBeta")
        result = build_entitlement_filter(profile)
        assert "partnerId eq 'PartnerBeta'" in result
        assert "PartnerAlpha" not in result


class TestClientFilter:
    """Tests for client ID filtering using search.in()."""

    def test_single_client_in_filter(self):
        profile = make_profile(allowedClients=["ClientNorth"])
        result = build_entitlement_filter(profile)
        assert "ClientNorth" in result
        assert "search.in(clientId," in result

    def test_multiple_clients_in_filter(self):
        profile = make_profile(allowedClients=["ClientNorth", "ClientSouth"])
        result = build_entitlement_filter(profile)
        assert "ClientNorth" in result
        assert "ClientSouth" in result
        assert "search.in(clientId," in result

    def test_client_filter_uses_search_in_syntax(self):
        """search.in() is the correct OData syntax for multi-value matching."""
        profile = make_profile(allowedClients=["ClientA", "ClientB"])
        result = build_entitlement_filter(profile)
        # Should use search.in format, not multiple eq conditions
        assert "search.in(clientId," in result


class TestProductLineFilter:
    """Tests for product line filtering."""

    def test_single_product_line_in_filter(self):
        profile = make_profile(allowedProductLines=["ProductLineA"])
        result = build_entitlement_filter(profile)
        assert "ProductLineA" in result

    def test_multiple_product_lines_in_filter(self):
        profile = make_profile(allowedProductLines=["ProductLineA", "ProductLineB"])
        result = build_entitlement_filter(profile)
        assert "ProductLineA" in result
        assert "ProductLineB" in result


class TestRegionFilter:
    """Tests for region filtering."""

    def test_single_region_in_filter(self):
        profile = make_profile(allowedRegions=["RegionOne"])
        result = build_entitlement_filter(profile)
        assert "RegionOne" in result

    def test_multiple_regions_in_filter(self):
        profile = make_profile(allowedRegions=["RegionOne", "RegionTwo"])
        result = build_entitlement_filter(profile)
        assert "RegionOne" in result
        assert "RegionTwo" in result


class TestGlobalReferenceFilter:
    """Tests for PublicDemoReference classification filter."""

    def test_can_read_global_references_adds_classification_filter(self):
        profile = make_profile(canReadGlobalReferences=True)
        result = build_entitlement_filter(profile)
        assert PUBLIC_REFERENCE_CLASSIFICATION in result
        assert "classification eq" in result

    def test_cannot_read_global_references_excludes_classification_filter(self):
        profile = make_profile(canReadGlobalReferences=False)
        result = build_entitlement_filter(profile)
        assert PUBLIC_REFERENCE_CLASSIFICATION not in result

    def test_global_reader_filter_format(self):
        """Global reference filter should use classification eq expression."""
        profile = make_profile(
            allowedClients=[],
            allowedProductLines=[],
            allowedRegions=[],
            canReadGlobalReferences=True
        )
        result = build_entitlement_filter(profile)
        assert f"classification eq '{PUBLIC_REFERENCE_CLASSIFICATION}'" in result


class TestFilterCombination:
    """Tests for the OR combination of restricted and global filters."""

    def test_filter_uses_or_to_combine_restricted_and_global(self):
        """When both restricted and global filters apply, they should be combined with OR."""
        profile = make_profile(
            allowedClients=["ClientNorth"],
            canReadGlobalReferences=True
        )
        result = build_entitlement_filter(profile)
        # Must contain 'or' to combine restricted and global clauses
        assert " or " in result

    def test_filter_does_not_expose_unrelated_partner(self):
        """A filter for PartnerAlpha must not allow PartnerBeta documents."""
        profile = make_profile(partnerId="PartnerAlpha", allowedClients=["ClientNorth"])
        result = build_entitlement_filter(profile)
        assert "PartnerBeta" not in result

    def test_filter_does_not_expose_unrelated_client(self):
        """A filter for ClientNorth must not allow ClientEast documents."""
        profile = make_profile(
            partnerId="PartnerAlpha",
            allowedClients=["ClientNorth"],
            canReadGlobalReferences=False
        )
        result = build_entitlement_filter(profile)
        assert "ClientEast" not in result
        assert "ClientSouth" not in result


class TestRealDemoUsers:
    """Tests using real demo user entitlements from entitlements.py."""

    def _get_filter_for_user(self, user_id):
        from entitlements import get_entitlements
        profile = get_entitlements(user_id)
        return build_entitlement_filter(profile)

    def test_alpha_north_filter_contains_partner_alpha(self):
        result = self._get_filter_for_user("user.alpha.north@example.com")
        assert "PartnerAlpha" in result

    def test_alpha_north_filter_contains_client_north(self):
        result = self._get_filter_for_user("user.alpha.north@example.com")
        assert "ClientNorth" in result

    def test_alpha_north_filter_excludes_client_east(self):
        result = self._get_filter_for_user("user.alpha.north@example.com")
        assert "ClientEast" not in result

    def test_beta_east_filter_contains_partner_beta(self):
        result = self._get_filter_for_user("user.beta.east@example.com")
        assert "PartnerBeta" in result

    def test_beta_east_filter_excludes_partner_alpha(self):
        result = self._get_filter_for_user("user.beta.east@example.com")
        assert "PartnerAlpha" not in result

    def test_unknown_user_gets_deny_all(self):
        from entitlements import get_entitlements
        profile = get_entitlements("unknown@example.com")
        result = build_entitlement_filter(profile)
        assert result == DENY_ALL_FILTER

    def test_global_reader_gets_only_public_reference_filter(self):
        result = self._get_filter_for_user("user.global.reader@example.com")
        assert PUBLIC_REFERENCE_CLASSIFICATION in result
        # Should NOT contain partner-specific filters since global reader has no clients
        assert "PartnerAlpha" not in result
        assert "PartnerBeta" not in result

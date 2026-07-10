"""
test_entitlements.py

Tests for the mock entitlement service (src/api/entitlements.py).

Verifies:
- All demo users load correctly with the expected fields
- Known users return full entitlement profiles
- Unknown users return None (triggering deny-by-default)
- Entitlement fields have the expected values for each demo persona
"""

import sys
import os
from pathlib import Path

# Add src/api to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))

from entitlements import get_all_users, get_entitlements
from models import EntitlementProfile, UserSummary


class TestGetAllUsers:
    """Tests for get_all_users()"""

    def test_returns_list(self):
        users = get_all_users()
        assert isinstance(users, list)

    def test_returns_four_demo_users(self):
        users = get_all_users()
        assert len(users) == 4

    def test_all_users_are_user_summary_type(self):
        users = get_all_users()
        for user in users:
            assert isinstance(user, UserSummary)

    def test_user_ids_are_present(self):
        users = get_all_users()
        user_ids = {u.userId for u in users}
        assert "user.alpha.north@example.com" in user_ids
        assert "user.alpha.south@example.com" in user_ids
        assert "user.beta.east@example.com" in user_ids
        assert "user.global.reader@example.com" in user_ids

    def test_partner_ids_are_present(self):
        users = get_all_users()
        partner_map = {u.userId: u.partnerId for u in users}
        assert partner_map["user.alpha.north@example.com"] == "PartnerAlpha"
        assert partner_map["user.alpha.south@example.com"] == "PartnerAlpha"
        assert partner_map["user.beta.east@example.com"] == "PartnerBeta"
        assert partner_map["user.global.reader@example.com"] == "Global"

    def test_display_names_are_set(self):
        users = get_all_users()
        for user in users:
            assert user.displayName and len(user.displayName) > 0


class TestGetEntitlements:
    """Tests for get_entitlements()"""

    def test_unknown_user_returns_none(self):
        result = get_entitlements("unknown@example.com")
        assert result is None

    def test_empty_string_returns_none(self):
        result = get_entitlements("")
        assert result is None

    def test_known_user_returns_profile(self):
        result = get_entitlements("user.alpha.north@example.com")
        assert result is not None
        assert isinstance(result, EntitlementProfile)

    def test_user_alpha_north_entitlements(self):
        profile = get_entitlements("user.alpha.north@example.com")
        assert profile is not None
        assert profile.userId == "user.alpha.north@example.com"
        assert profile.displayName == "User Alpha North"
        assert profile.partnerId == "PartnerAlpha"
        assert profile.allowedClients == ["ClientNorth"]
        assert profile.allowedProductLines == ["ProductLineA"]
        assert profile.allowedRegions == ["RegionOne"]
        assert profile.canReadGlobalReferences is True

    def test_user_alpha_south_entitlements(self):
        profile = get_entitlements("user.alpha.south@example.com")
        assert profile is not None
        assert profile.partnerId == "PartnerAlpha"
        assert "ClientSouth" in profile.allowedClients
        assert "ProductLineA" in profile.allowedProductLines
        assert "ProductLineB" in profile.allowedProductLines
        assert "RegionOne" in profile.allowedRegions
        assert "RegionTwo" in profile.allowedRegions
        assert profile.canReadGlobalReferences is True

    def test_user_beta_east_entitlements(self):
        profile = get_entitlements("user.beta.east@example.com")
        assert profile is not None
        assert profile.partnerId == "PartnerBeta"
        assert profile.allowedClients == ["ClientEast"]
        assert profile.allowedProductLines == ["ProductLineB"]
        assert profile.allowedRegions == ["RegionTwo"]
        assert profile.canReadGlobalReferences is True

    def test_global_reader_has_no_restricted_access(self):
        profile = get_entitlements("user.global.reader@example.com")
        assert profile is not None
        assert profile.partnerId == "Global"
        assert profile.allowedClients == []
        assert profile.allowedProductLines == []
        assert profile.allowedRegions == []
        assert profile.canReadGlobalReferences is True

    def test_alpha_north_cannot_access_client_east(self):
        """User Alpha North's allowed clients should not include ClientEast."""
        profile = get_entitlements("user.alpha.north@example.com")
        assert profile is not None
        assert "ClientEast" not in profile.allowedClients

    def test_alpha_north_cannot_access_client_south(self):
        """User Alpha North's allowed clients should not include ClientSouth."""
        profile = get_entitlements("user.alpha.north@example.com")
        assert profile is not None
        assert "ClientSouth" not in profile.allowedClients

    def test_beta_east_cannot_access_partner_alpha(self):
        """User Beta East belongs to PartnerBeta, not PartnerAlpha."""
        profile = get_entitlements("user.beta.east@example.com")
        assert profile is not None
        assert profile.partnerId != "PartnerAlpha"

    def test_case_sensitive_user_lookup(self):
        """User IDs are case-sensitive — uppercase variant should not be found."""
        result = get_entitlements("USER.ALPHA.NORTH@EXAMPLE.COM")
        assert result is None

    def test_all_profiles_have_required_fields(self):
        """All demo users must have all required entitlement fields."""
        user_ids = [
            "user.alpha.north@example.com",
            "user.alpha.south@example.com",
            "user.beta.east@example.com",
            "user.global.reader@example.com",
        ]
        for uid in user_ids:
            profile = get_entitlements(uid)
            assert profile is not None, f"Profile missing for {uid}"
            assert profile.userId == uid
            assert profile.displayName is not None and len(profile.displayName) > 0
            assert profile.partnerId is not None and len(profile.partnerId) > 0
            assert isinstance(profile.allowedClients, list)
            assert isinstance(profile.allowedProductLines, list)
            assert isinstance(profile.allowedRegions, list)
            assert isinstance(profile.canReadGlobalReferences, bool)

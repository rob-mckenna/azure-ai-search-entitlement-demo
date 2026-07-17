"""
entitlements.py

Mock entitlement service for the Azure AI Search entitlement filtering demo.

In a real system, this module would:
- Call your IAM system (Azure AD, Okta, custom portal API)
- Look up group memberships or role assignments
- Return the user's authorization context

This demo uses a hardcoded list of fictional users to simulate the
authorization lookup. All user identities are synthetic.

Key principle: The entitlement service determines WHAT a user can access.
This is separate from authentication (WHO the user is).

Endpoints exposed via FastAPI:
    GET /api/users                     — List all demo users
    GET /api/entitlements/{userId}     — Get entitlements for a specific user
"""

from typing import List, Optional
from models import EntitlementProfile, UserSummary

# -------------------------------------------------------------------
# Synthetic demo users.
# All identities, names, and affiliations are fictional.
# Do not use real names, real email addresses, or real organizations.
# -------------------------------------------------------------------
_DEMO_USERS: List[dict] = [
    {
        "userId": "user.alpha.north@example.com",
        "displayName": "User Alpha North",
        "partnerId": "PartnerAlpha",
        "allowedClients": ["ClientNorth"],
        "allowedProductLines": ["ProductLineA"],
        "allowedRegions": ["RegionOne"],
        "canReadGlobalReferences": True
    },
    {
        "userId": "user.alpha.south@example.com",
        "displayName": "User Alpha South",
        "partnerId": "PartnerAlpha",
        "allowedClients": ["ClientSouth"],
        "allowedProductLines": ["ProductLineA", "ProductLineB"],
        "allowedRegions": ["RegionOne", "RegionTwo"],
        "canReadGlobalReferences": True
    },
    {
        "userId": "user.beta.east@example.com",
        "displayName": "User Beta East",
        "partnerId": "PartnerBeta",
        "allowedClients": ["ClientEast"],
        "allowedProductLines": ["ProductLineB"],
        "allowedRegions": ["RegionTwo"],
        "canReadGlobalReferences": True
    },
    {
        "userId": "user.global.reader@example.com",
        "displayName": "Global Reference Reader",
        "partnerId": "Global",
        "allowedClients": [],
        "allowedProductLines": [],
        "allowedRegions": [],
        "canReadGlobalReferences": True
    },
]

# Build a lookup dict for O(1) access by userId
_USER_INDEX: dict = {u["userId"]: u for u in _DEMO_USERS}


def get_all_users() -> List[UserSummary]:
    """
    Return a summary list of all demo users.

    Used by GET /api/users to populate the user selector in the frontend.
    """
    return [
        UserSummary(
            userId=u["userId"],
            displayName=u["displayName"],
            partnerId=u["partnerId"]
        )
        for u in _DEMO_USERS
    ]


def get_entitlements(user_id: str) -> Optional[EntitlementProfile]:
    """
    Look up the entitlement profile for a given user ID.

    In a real system, this would call your IAM or authorization service.
    Here it looks up the user in the hardcoded demo user list.

    Args:
        user_id: The user's identifier (e.g. user.alpha.north@example.com)

    Returns:
        EntitlementProfile if the user exists, None otherwise.
        Returning None triggers deny-by-default behavior in the search layer.
    """
    user_data = _USER_INDEX.get(user_id)
    if user_data is None:
        return None

    return EntitlementProfile(**user_data)

# Security Model

## Overview

This document describes the security model used in the Azure AI Search Entitlement Filtering Demo. Understanding this model is essential before adapting the pattern to a production system.

> **Important:** This demo shows a *pattern*, not a complete production security implementation. It is designed to be instructive, not exhaustive.

---

## Core Principles

### 1. Azure AI Search Does Not Authenticate End Users

Azure AI Search is a backend service. In this demo, the application layer (the FastAPI API) is responsible for:
- Receiving the user's identity (the `userId` parameter)
- Looking up their authorization context
- Building and enforcing the query-time filter

Azure AI Search applies the filter provided by the application. It does not independently verify user identity.

### 2. The Application Must Authenticate the User

In a real system, before calling `/api/search` or `/api/chat`, the user must be authenticated by your identity provider (Azure AD, Okta, Auth0, etc.). The `userId` must come from a verified JWT claim or session token — not from an untrusted user-supplied parameter.

In this demo, the `userId` is passed as a plain string for simplicity. **This is a demo pattern only.** In production, always extract the user identity from a validated, signed token.

### 3. The Authorization Service Determines Entitlements

Authentication answers "who is this user?" Authorization answers "what are they allowed to access?"

These are separate concerns:

```
Authentication: WHO is the user?
    → Identity Provider (Azure AD, Okta, etc.)
    → Result: Verified user identity

Authorization: WHAT can the user access?
    → Entitlement Service (IAM, custom portal DB, Azure AD groups, etc.)
    → Result: Entitlement context (partnerId, allowedClients, etc.)
```

In this demo, the entitlement service is a hardcoded mock (`src/api/entitlements.py`). In production, replace this with calls to your real authorization system.

### 4. The Retrieval Service Enforces Filters

The retrieval API (`src/api/main.py` and `src/api/search.py`) is the enforcement point. Every search query includes an OData filter derived from the user's entitlement context.

The filter is constructed by `src/api/filters.py` and passed to every Azure AI Search query. There is no code path that executes an unfiltered search for user queries.

### 5. The System Must Be Deny-by-Default

If a user's identity cannot be resolved to an entitlement profile, the filter builder returns:

```
id eq 'DENIED_NO_ENTITLEMENTS_FOUND'
```

This expression matches no documents. The user receives an empty result set.

**Never default to returning all documents** if entitlements are missing or ambiguous.

### 6. Entitlement Metadata Must Be Attached at Ingestion Time

Entitlement enforcement only works if every document chunk in the index has accurate entitlement metadata fields (partnerId, clientId, productLine, region, classification).

If a chunk is missing these fields, the filter may not match it — which could result in either:
- Accidental exclusion (the chunk is never returned to anyone), or
- Accidental inclusion (if the filter logic treats missing values as permissive)

The schema and filter logic in this demo treats missing values as exclusive. However, you should validate metadata completeness during ingestion.

### 7. Revocation Depends on Entitlement Source and Query-Time Filtering

This pattern enforces access at **query time** — not at storage time. This means:

- If a user's entitlements are revoked in the entitlement service, the change takes effect on their next query.
- There is no need to physically remove documents from the index to revoke access (unlike ACL-based systems).
- However, if the entitlement service has caching or latency, there may be a short window where the old filter is still applied.

For document-level revocation (e.g., a specific document should no longer be accessible by any user), the document chunks must be deleted from the index or their metadata must be updated to remove the relevant entitlement tags.

### 8. If Document Permissions Change, Metadata Must Be Updated

If a document's classification or allowed entitlements change after ingestion:
- Re-ingest the document with updated metadata to update the chunks in the index, or
- Use the Azure AI Search merge/upload API to update the metadata fields on existing chunks.

The demo ingestion pipeline uses `upload_documents` with merge-or-upload semantics, so re-running the ingestion pipeline with updated metadata will update existing chunks.

### 9. This Demo Is Not a Replacement for Native Source-System ACLs

This pattern is designed for systems where **business authorization lives outside the document repository** — for example:
- A custom partner portal that controls which partners can see which documents
- An application-tier entitlement service based on business rules
- A system where documents don't have native ACLs (e.g., plain file storage)

For systems where the document source already has native ACLs (e.g., SharePoint, Azure Data Lake with POSIX ACLs), you should evaluate using those native ACLs *in addition to* this pattern, not instead of them.

### 10. This Demo Shows a Pattern for Systems Where Business Authorization Lives Outside the Document Repository

The key use case for this pattern is:
- Documents are stored in a central index (Azure AI Search)
- Authorization is governed by an external business system (CRM, ERP, partner portal, IAM)
- The document index has no knowledge of user identity or permissions
- The application layer bridges authentication (identity) and authorization (entitlements) at query time

### 11. Frontend Messaging Should Reflect Authorization Outcomes Without Leaking Internal Attributes

User-facing messaging should clearly distinguish:

- **No access granted**: deny-by-default was applied (unknown or unresolved user identity).
- **Limited access with results**: content is visible, but only within authorized scope.
- **No matches in scope**: user is authorized, but no documents matched the query in that scope.

UI copy should explain enforcement behavior in plain language and avoid exposing raw entitlement attributes (for example, full internal filters or entitlement payloads) unless explicitly needed for demo troubleshooting.

---

## Threat Model

### What This Pattern Protects Against

| Threat | Protection |
|---|---|
| User queries for documents outside their partner/client scope | OData filter excludes those documents from results |
| Unknown user queries the API | Deny-by-default returns empty results |
| User tries to enumerate restricted document IDs | Filter prevents direct ID-based retrieval of unauthorized docs |
| LLM hallucination using unauthorized context | LLM only receives filtered chunks — unauthorized content never reaches the LLM |

### What This Pattern Does NOT Protect Against

| Risk | Mitigation Required |
|---|---|
| Compromised API key to Azure AI Search | Rotate keys, use managed identity, restrict network access |
| API called with a forged userId | Validate userId from signed JWT in production |
| Metadata incorrectly applied at ingestion | Validate metadata completeness in ingestion pipeline |
| Azure AI Search service-level access | Use network restrictions, private endpoints, RBAC |
| Bulk data export via repeated API calls | Implement rate limiting and audit logging |
| Insider threat by application developers | Standard least-privilege access controls on Azure resources |

---

## Production Hardening Checklist

Before adapting this pattern to production:

- [ ] Replace mock entitlement service with calls to your real IAM/authorization system
- [ ] Extract `userId` from a validated, signed JWT token — never trust a user-supplied string
- [ ] Use managed identity for all Azure resource authentication (no API keys in code)
- [ ] Enable Azure AI Search network restrictions or private endpoints
- [ ] Implement audit logging for every entitlement lookup and filter application
- [ ] Validate entitlement metadata completeness during the ingestion pipeline
- [ ] Implement rate limiting on the search API
- [ ] Set up alerting for deny-by-default events (potential unauthorized access attempts)
- [ ] Review and test the deny-all filter expression against your Azure AI Search version
- [ ] Consider adding row-level security at the Azure Storage layer for the source documents
- [ ] Test revocation scenarios: ensure entitlement changes propagate correctly

---

## About This Demo

This demo intentionally does not use real users, real customers, real documents, or real business data. It demonstrates a reusable pattern where an external application or portal owns authorization and passes entitlement context into Azure AI Search as query-time filters.

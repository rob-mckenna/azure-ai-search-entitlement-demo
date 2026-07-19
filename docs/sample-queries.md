# Sample Queries — Demo Script

This document contains sample queries demonstrating the entitlement filtering behavior.
Use these to run demos or verify that the system is working correctly.

All users, documents, and data are **entirely synthetic**. No real business data is present.

---

## Compare Workflow Checklist

Use this manual checklist to validate the compare workflow:

1. Start the API and frontend.
2. Open the app in two browser tabs, or use the API directly.
3. Run the same query for two different users.
4. Confirm the filters, result counts, and document titles differ where expected.
5. Confirm `PublicDemoReference` content remains available to known demo users.
6. Confirm unknown users still receive the deny-by-default filter and no results.

**Open UI gap:** the current frontend has no dedicated side-by-side compare pane.
Comparison is manual today: use the user selector, query history, and/or separate
tabs.

**Regressions to guard with tests:**
- Search calls must always include the entitlement filter.
- Unknown users must stay deny-by-default.
- Switching users must not reuse a previous user's results or filter.
- PublicDemoReference access must remain explicitly gated.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"userId":"user.alpha.north@example.com","query":"Summarize Product Line A implementation notes","searchMode":"hybrid"}'

curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"userId":"user.beta.east@example.com","query":"Summarize Product Line A implementation notes","searchMode":"hybrid"}'
```

---

## Prerequisites

1. Deploy the infrastructure: `azd up`
2. Generate synthetic PDFs: `python src/ingestion/generate_sample_pdfs.py`
3. Ingest documents: `python src/ingestion/ingest_documents.py`
4. Start the API: `python src/api/main.py`

---

## Using the API Directly

Replace `http://localhost:8000` with your deployed API URL if using Azure.

---

## Sample Query 1: User Alpha North — Authorized Access

**Scenario:** User Alpha North queries for Product Line A information.

**Expected:** Results from PartnerAlpha, ClientNorth, ProductLineA, RegionOne only — plus any PublicDemoReference documents.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.alpha.north@example.com",
    "query": "Summarize Product Line A implementation notes",
    "searchMode": "hybrid"
  }'
```

**Expected filter:**
```
(partnerId eq 'PartnerAlpha' and search.in(clientId, 'ClientNorth', ',') and search.in(productLine, 'ProductLineA', ',') and search.in(region, 'RegionOne', ',')) or (classification eq 'PublicDemoReference')
```

**Expected results:**
- partner-alpha-client-north-overview.pdf
- restricted-client-north-financial-summary.pdf
- shared-global-reference-guide.pdf (PublicDemoReference)

---

## Sample Query 2: User Alpha South — Operational Risks

**Scenario:** User Alpha South queries for operational information.

**Expected:** Results from PartnerAlpha, ClientSouth only. ClientNorth content is NOT returned even though both share PartnerAlpha.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.alpha.south@example.com",
    "query": "What are the operational risks?",
    "searchMode": "hybrid"
  }'
```

**Expected filter:**
```
(partnerId eq 'PartnerAlpha' and search.in(clientId, 'ClientSouth', ',') and search.in(productLine, 'ProductLineA,ProductLineB', ',') and search.in(region, 'RegionOne,RegionTwo', ',')) or (classification eq 'PublicDemoReference')
```

**Expected results:**
- partner-alpha-client-south-product-line-a-summary.pdf
- shared-global-reference-guide.pdf (PublicDemoReference)
- NOT: partner-alpha-client-north-overview.pdf (different client)

---

## Sample Query 3: User Beta East — Implementation Details

**Scenario:** User Beta East queries for ClientEast implementation details.

**Expected:** Results from PartnerBeta, ClientEast only.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.beta.east@example.com",
    "query": "Show implementation details for ClientEast",
    "searchMode": "keyword"
  }'
```

**Expected filter:**
```
(partnerId eq 'PartnerBeta' and search.in(clientId, 'ClientEast', ',') and search.in(productLine, 'ProductLineB', ',') and search.in(region, 'RegionTwo', ',')) or (classification eq 'PublicDemoReference')
```

**Expected results:**
- partner-beta-client-east-operational-review.pdf
- restricted-client-east-implementation-notes.pdf
- shared-global-reference-guide.pdf (PublicDemoReference)
- NOT: Any PartnerAlpha documents

---

## Sample Query 4: User Alpha North — Cross-Partner Attempt (Blocked)

**Scenario:** User Alpha North tries to access ClientEast implementation notes. This is a different partner and client — the filter should block it.

**Expected:** No ClientEast content returned. The entitlement filter prevents access.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.alpha.north@example.com",
    "query": "Summarize ClientEast implementation notes",
    "searchMode": "hybrid"
  }'
```

**Expected results:**
- Zero results from PartnerBeta or ClientEast
- May return PublicDemoReference documents if query matches
- The filter enforces: `partnerId eq 'PartnerAlpha'` — PartnerBeta documents are excluded

---

## Sample Query 5: Global Reference Reader — Reference Content Only

**Scenario:** The Global Reference Reader has no client-specific entitlements. They can only access PublicDemoReference documents.

**Expected:** Only the shared global reference guide is returned.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.global.reader@example.com",
    "query": "What reference guidance is available?",
    "searchMode": "keyword"
  }'
```

**Expected filter:**
```
(classification eq 'PublicDemoReference')
```

**Expected results:**
- shared-global-reference-guide.pdf ONLY
- NO restricted partner/client documents

---

## Sample Query 6: Unknown User — Deny-by-Default

**Scenario:** An unknown user submits a query. The entitlement service returns no profile. The deny-by-default behavior returns empty results.

**Expected:** Zero results and a message explaining deny-by-default.

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "unknown@example.com",
    "query": "Summarize all restricted documents",
    "searchMode": "keyword"
  }'
```

**Expected filter:**
```
id eq 'DENIED_NO_ENTITLEMENTS_FOUND'
```

**Expected response:**
```json
{
  "userId": "unknown@example.com",
  "query": "Summarize all restricted documents",
  "filter": "id eq 'DENIED_NO_ENTITLEMENTS_FOUND'",
  "results": [],
  "resultCount": 0,
  "message": "User 'unknown@example.com' was not found in the entitlement service. No content returned (deny-by-default)."
}
```

---

## Sample Query 7: Chat Mode (RAG) — if Azure OpenAI is configured

**Scenario:** User Alpha North asks a question and wants an AI-generated answer.

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user.alpha.north@example.com",
    "query": "What is the current implementation status for Product Line A?",
    "searchMode": "hybrid"
  }'
```

**Without Azure OpenAI configured:**
```json
{
  "message": "Answer generation is disabled because Azure OpenAI is not configured. Retrieval results are shown below.",
  "sources": [...]
}
```

**With Azure OpenAI configured (ENABLE_LLM=true):**
Returns an AI-generated answer synthesized from ONLY the filtered chunks.
The LLM never receives unauthorized content.

---

## Entitlement Lookup Endpoint

Check a user's entitlement profile:

```bash
curl http://localhost:8000/api/entitlements/user.alpha.north@example.com
```

Response:
```json
{
  "userId": "user.alpha.north@example.com",
  "displayName": "User Alpha North",
  "partnerId": "PartnerAlpha",
  "allowedClients": ["ClientNorth"],
  "allowedProductLines": ["ProductLineA"],
  "allowedRegions": ["RegionOne"],
  "canReadGlobalReferences": true
}
```

Unknown user:
```bash
curl http://localhost:8000/api/entitlements/unknown@example.com
# Returns: 404 Not Found
```

---

## Key Demonstration Points

When running this demo, highlight these observations:

1. **Same query, different users, different results** — Run Query 1 (Alpha North) and Query 3 (Beta East) with the same query text. The results are completely different.

2. **Cross-partner blocking** — Query 4 shows that even with a highly relevant query about ClientEast content, User Alpha North sees nothing from PartnerBeta.

3. **Filter transparency** — The API always returns the generated OData filter. Show this to explain how the filtering works mechanically.

4. **Deny-by-default** — Query 6 demonstrates that unknown users get nothing, not everything.

5. **Global reference access** — Query 5 shows that the Global Reference Reader gets access only to PublicDemoReference documents.

6. **LLM protection** — If Azure OpenAI is configured, demonstrate that the LLM answer only references documents the user is authorized to see.

7. **Compare workflow gap** — There is no dedicated compare UI yet, so use the checklist above and compare query history / response payloads manually.

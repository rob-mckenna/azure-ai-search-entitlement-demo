# Squad Decisions

## Active Decisions

### 2026-07-18: Retrieval entitlement enforcement baseline
**By:** Morpheus
**What:**
- **Entitlement contract (Portal/AuthZ → API):** The caller (portal or authorization service) is responsible for authenticated identity and authoritative entitlement context. The API consumes `userId`, resolves entitlements from the authorization source, and converts them into a mandatory Azure AI Search OData filter applied to every retrieval call.
- **Deny-by-default:** If entitlement lookup is unknown, missing, or yields no usable scope, the API must return no content by applying a deny-all filter (`search.in(id, '___NO_MATCH___', ',')`). Never broaden access on ambiguity.
- **Azure OpenAI fallback:** When Azure OpenAI is unavailable/disabled, the system remains retrieval-only. Entitlement-filtered search responses continue; generative answer synthesis is skipped with an explicit message that answer generation is disabled.
**Why:**
- Locks a single security baseline for all retrieval paths before adding features.
- Prevents accidental authorization bypass from null/empty entitlement states.
- Preserves least-privilege behavior while keeping demo functionality usable without Azure OpenAI.

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
